# import_handler.py
import pandas as pd
import re
from database import get_conn, init_db
from config import MAPPING_ANTENNES

JOURS_FR = {
    'Monday': 'Lundi', 'Tuesday': 'Mardi', 'Wednesday': 'Mercredi',
    'Thursday': 'Jeudi', 'Friday': 'Vendredi', 'Saturday': 'Samedi', 'Sunday': 'Dimanche'
}

def find_parent(row, df):
    if row['Renfort'] != 'renfort':
        return None

    # Correspondance date + heures
    candidates = df[
        (df['Début'] == row['Début']) &
        (df['Heure début'] == row['Heure début']) &
        (df['Heure fin'] == row['Heure fin']) &
        (df['Renfort'] != 'renfort')
    ]
    if len(candidates) == 0:
        return None
    if len(candidates) == 1:
        return candidates.iloc[0]

    # Plusieurs candidats : affiner par adresse puis par lieu
    def norm(val):
        return str(val).strip().lower() if val is not None and not (isinstance(val, float) and pd.isna(val)) else ''

    adresse_r = norm(row.get('Adresse'))
    lieu_r    = norm(row.get('Lieu'))

    if adresse_r:
        addr_match = candidates[candidates['Adresse'].apply(norm) == adresse_r]
        if len(addr_match) == 1:
            return addr_match.iloc[0]
        if len(addr_match) > 1:
            candidates = addr_match

    if lieu_r and len(candidates) > 1:
        lieu_match = candidates[candidates['Lieu'].apply(norm) == lieu_r]
        if len(lieu_match) >= 1:
            candidates = lieu_match
        if len(candidates) == 1:
            return candidates.iloc[0]

    # Dernier recours : similarité du nom d'activité
    def get_words(text):
        return set(re.findall(r'\w+', str(text).lower()))
    r_words = get_words(row['Activité'])
    best_candidate = None
    max_overlap = -1
    for idx, cand in candidates.iterrows():
        overlap = len(r_words.intersection(get_words(cand['Activité'])))
        if overlap > max_overlap:
            max_overlap = overlap
            best_candidate = cand
    return best_candidate

def format_heure(h):
    if pd.isna(h): return "??"
    h_str = str(h).replace('.0', '').strip()
    if len(h_str.split(':')) == 3:
        h_str = ':'.join(h_str.split(':')[:2])
    parts = h_str.split(':')
    if len(parts) == 2:
        try:
            return f"{int(parts[0]):02d}h{int(parts[1]):02d}"
        except ValueError:
            return h_str
    return h_str

def importer_evenements(fichier_path):
    init_db()
    logs = []
    nom_fichier = fichier_path.split("/")[-1].split("\\")[-1]

    df = pd.read_excel(fichier_path, sheet_name="Liste des evenements")
    logs.append(f"📂 Fichier : {nom_fichier}")
    logs.append(f"📋 {len(df)} événements lus")

    df['Organisateur'] = df['Organisateur'].astype(str).str.strip()
    df['Antenne'] = df['Organisateur'].map(MAPPING_ANTENNES)

    non_trouves = df[df['Antenne'].isna()]['Organisateur'].unique()
    if len(non_trouves) > 0:
        logs.append(f"⚠️ Antennes non reconnues : {list(non_trouves)}")

    df['Présents_num'] = pd.to_numeric(df['Présents (hors renforts)'], errors='coerce').fillna(0).astype(int)
    df['Requis_num'] = pd.to_numeric(df['Requis'], errors='coerce').fillna(0).astype(int)

    df['Date'] = pd.to_datetime(df['Début'], format='%d-%m-%Y', errors='coerce')
    if df['Date'].isna().all():
        df['Date'] = pd.to_datetime(df['Début'], errors='coerce')

    df['Jour'] = df['Date'].dt.day_name().map(JOURS_FR)
    df['Week'] = df['Date'].dt.isocalendar().week

    df['H_debut'] = df['Heure début'].apply(format_heure)
    df['H_fin'] = df['Heure fin'].apply(format_heure)
    df['Nom_DPS'] = df['Activité'] + " (" + df['H_debut'] + "-" + df['H_fin'] + ")"

    parents = []
    for idx, row in df.iterrows():
        parents.append(find_parent(row, df))
    df['parent_row'] = parents

    # Détection des groupes incomplets : somme IS (parent + tous ses renforts) vs Requis du parent
    # On utilise les relations parent-enfant détectées par find_parent() (date + heure + adresse/lieu).
    parent_totals = {}  # parent_idx -> total Présents (parent propre + tous ses renforts)
    for idx, row in df.iterrows():
        parent = row['parent_row']
        if parent is None:
            parent_totals[idx] = parent_totals.get(idx, 0) + row['Présents_num']
        else:
            p_idx = parent.name
            parent_totals[p_idx] = parent_totals.get(p_idx, 0) + row['Présents_num']

    parent_requis_map = {idx: row['Requis_num'] for idx, row in df.iterrows()
                         if row['parent_row'] is None}

    def in_incomplete_group(row):
        parent = row['parent_row']
        p_idx = row.name if parent is None else parent.name
        total = parent_totals.get(p_idx, 0)
        requis = parent_requis_map.get(p_idx, row['Requis_num'])
        return total < requis

    df['Is_In_Incomplete_Group'] = df.apply(in_incomplete_group, axis=1)

    df_to_import = df[df['Is_In_Incomplete_Group']].copy()

    semaines_presentes = sorted(df_to_import['Week'].dropna().unique())
    logs.append(f"📅 Semaine(s) détectée(s) : {[int(s) for s in semaines_presentes]}")

    if len(df_to_import) == 0:
        logs.append("ℹ️ Aucun DPS incomplet trouvé.")
        return None, df, "\n".join(logs)

    conn = get_conn()
    c = conn.cursor()

    parent_indices_to_db_id = {}

    for week_num in semaines_presentes:
        df_week = df_to_import[df_to_import['Week'] == week_num].copy()

        dates_week = df_week['Date'].dropna()
        date_deb = dates_week.min().strftime('%Y-%m-%d')
        date_fin = dates_week.max().strftime('%Y-%m-%d')

        c.execute("INSERT INTO semaines (numero, date_debut, date_fin) VALUES (%s, %s, %s) ON CONFLICT (numero) DO NOTHING",
                  (int(week_num), date_deb, date_fin))
        c.execute("SELECT id FROM semaines WHERE numero = %s", (int(week_num),))
        semaine_id = c.fetchone()[0]

        # Sauvegarder les renforts manuels avant écrasement
        c.execute("DELETE FROM renforts_backup WHERE semaine_num = %s", (int(week_num),))
        c.execute("""
            INSERT INTO renforts_backup (semaine_num, antenne, jour, nom_dps, nb, tl, parent_antenne, parent_jour, parent_nom)
            SELECT %s, d.antenne, d.jour, d.nom_dps, d.nb, d.tl,
                   p.antenne, p.jour, p.nom_dps
            FROM dps d
            LEFT JOIN dps p ON p.id = d.parent_dps_id
            WHERE d.semaine_id = %s AND d.est_manuel = 1
        """, (int(week_num), semaine_id))
        c.execute("SELECT COUNT(*) FROM renforts_backup WHERE semaine_num = %s", (int(week_num),))
        nb_backup = c.fetchone()[0]
        if nb_backup > 0:
            logs.append(f"💾 {nb_backup} renfort(s) manuel(s) sauvegardé(s) — utilisez 'Réinjecter' pour les restaurer")

        c.execute("DELETE FROM dps WHERE semaine_id = %s", (semaine_id,))

        df_week_parents = df_week[df_week['parent_row'].isna()]
        df_week_renforts = df_week[df_week['parent_row'].notna()]

        for idx, row in df_week_parents.iterrows():
            if pd.isna(row['Antenne']):
                print(f"[SKIP] DPS sans antenne : {row['Nom_DPS']}")
                continue
            try:
                nom_final = row['Nom_DPS']
                est_renfort_val = 0
                if row['Renfort'] == 'renfort':
                    nom_final = "[R] " + row['Nom_DPS']
                    est_renfort_val = 1

                c.execute("""INSERT INTO dps (semaine_id, antenne, jour, nom_dps, nb, tl, est_renfort, parent_dps_id)
                             VALUES (%s, %s, %s, %s, %s, %s, %s, NULL) RETURNING id""",
                          (semaine_id, row['Antenne'], row['Jour'], nom_final,
                           int(row['Présents_num']), int(row['Requis_num']), est_renfort_val))
                parent_indices_to_db_id[idx] = c.fetchone()[0]
            except Exception as e:
                logs.append(f"❌ DPS principal {row['Nom_DPS']} : {e}")

        for idx, row in df_week_renforts.iterrows():
            if pd.isna(row['Antenne']):
                print(f"[SKIP] Renfort sans antenne : {row['Nom_DPS']}")
                continue

            parent_idx = row['parent_row'].name
            parent_db_id = parent_indices_to_db_id.get(parent_idx)

            if parent_db_id is None:
                p_row = row['parent_row']
                if p_row is not None and not pd.isna(p_row.get('Antenne', None)):
                    c.execute("""SELECT id FROM dps
                                 WHERE semaine_id=%s AND antenne=%s AND jour=%s AND nom_dps=%s AND est_renfort=0""",
                              (semaine_id, p_row['Antenne'], p_row.get('Jour'), p_row.get('Nom_DPS')))
                    res = c.fetchone()
                    if res:
                        parent_db_id = res[0]

            try:
                nom_clean = row['Activité']
                nom_clean = re.sub(r'(?i)^renfort\s+(\[P\]\s+)?', '', nom_clean)
                nom_clean = re.sub(r'(?i)^\[P\]\s+', '', nom_clean).strip()
                nom_final = f"[R] {nom_clean} ({row['H_debut']}-{row['H_fin']})"

                c.execute("""INSERT INTO dps (semaine_id, antenne, jour, nom_dps, nb, tl, est_renfort, parent_dps_id)
                             VALUES (%s, %s, %s, %s, %s, %s, 1, %s)""",
                          (semaine_id, row['Antenne'], row['Jour'], nom_final,
                           int(row['Présents_num']), int(row['Requis_num']), parent_db_id))
            except Exception as e:
                logs.append(f"❌ Renfort {row['Nom_DPS']} : {e}")

    conn.commit()
    conn.close()

    nb_principaux = len(df_to_import[df_to_import['parent_row'].isna()])
    nb_renforts   = len(df_to_import[df_to_import['parent_row'].notna()])
    logs.append(f"✅ Import terminé : {nb_principaux} DPS principal(aux), {nb_renforts} renfort(s)")

    mode_week = int(df_to_import['Week'].dropna().mode()[0]) if not df_to_import['Week'].dropna().empty else semaines_presentes[0]
    return mode_week, df, "\n".join(logs)
