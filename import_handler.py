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

    # Liaison primaire : même numéro d'activité (colonne A)
    num = row.get('num_activite')
    if num is not None and not pd.isna(num):
        candidates = df[
            (df['num_activite'] == num) &
            (df['Renfort'] != 'renfort')
        ]
        if len(candidates) > 0:
            return candidates.iloc[0]

    # Fallback : correspondance date + heures
    candidates = df[
        (df['Début'] == row['Début']) &
        (df['Heure début'] == row['Heure début']) &
        (df['Heure fin'] == row['Heure fin']) &
        (df['Renfort'] != 'renfort')
    ]
    if len(candidates) == 0:
        return None
    elif len(candidates) == 1:
        return candidates.iloc[0]
    else:
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

    # Numéro d'activité = colonne A (identique pour l'activité principale et son renfort)
    df['num_activite'] = df.iloc[:, 0]

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

    # Grouper par numéro d'activité pour détecter les groupes incomplets
    df['group_id'] = df['num_activite'].where(df['num_activite'].notna(), other=pd.Series(range(len(df)), index=df.index).astype(str))
    df['Is_Incomplete_Row'] = df['Présents_num'] < df['Requis_num']
    incomplete_groups = df.groupby('group_id')['Is_Incomplete_Row'].transform('any')
    df['Is_In_Incomplete_Group'] = incomplete_groups

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

        c.execute("INSERT OR IGNORE INTO semaines (numero, date_debut, date_fin) VALUES (?, ?, ?)",
                  (int(week_num), date_deb, date_fin))
        c.execute("SELECT id FROM semaines WHERE numero = ?", (int(week_num),))
        semaine_id = c.fetchone()[0]

        c.execute("DELETE FROM dps WHERE semaine_id = ?", (semaine_id,))

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
                             VALUES (?, ?, ?, ?, ?, ?, ?, NULL)""",
                          (semaine_id, row['Antenne'], row['Jour'], nom_final,
                           int(row['Présents_num']), int(row['Requis_num']), est_renfort_val))
                parent_indices_to_db_id[idx] = c.lastrowid
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
                                 WHERE semaine_id=? AND antenne=? AND jour=? AND nom_dps=? AND est_renfort=0""",
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
                             VALUES (?, ?, ?, ?, ?, ?, 1, ?)""",
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
