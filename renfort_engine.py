# renfort_engine.py
from config import ANTENNES_ORDRE
from database import get_conn

def get_voisins(antenne, rayon=3):
    if antenne not in ANTENNES_ORDRE: return []
    idx = ANTENNES_ORDRE.index(antenne)
    voisins = []
    for offset in range(1, rayon + 1):
        if idx - offset >= 0: voisins.append(ANTENNES_ORDRE[idx - offset])
        if idx + offset < len(ANTENNES_ORDRE): voisins.append(ANTENNES_ORDRE[idx + offset])
    return voisins[:rayon]

def evaluer_disponibilite(antenne, jour, semaine_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""SELECT SUM(tl), SUM(nb) FROM dps 
                 WHERE semaine_id = ? AND antenne = ? AND jour = ? AND est_renfort = 0""", 
              (semaine_id, antenne, jour))
    res = c.fetchone()
    conn.close()
    
    total_tl = res[0] or 0
    total_nb = res[1] or 0
    
    if total_tl == 0: return "Libre (Aucun DPS)", 99
    elif total_nb >= total_tl: return f"Libre (Marge de {total_nb - total_tl} IS)", total_nb - total_tl
    elif total_nb > 0: return f"Partielle (Manque {total_tl - total_nb} IS)", 0
    else: return "Indisponible (0 IS)", 0

def suggerer_renforts(antenne_cible, jour, semaine_id, besoin):
    voisins = get_voisins(antenne_cible)
    suggestions = []
    for i, voisin in enumerate(voisins, 1):
        dispo, capacite = evaluer_disponibilite(voisin, jour, semaine_id)
        suggestions.append({
            'antenne': voisin, 'distance': i,
            'disponibilite': dispo, 'capacite': capacite
        })
    ordre = {"Libre": 0, "Libre (Aucun DPS)": 0, "Libre (Marge": 1, "Partielle": 2, "Indisponible": 3}
    suggestions.sort(key=lambda x: next((v for k, v in ordre.items() if k in x['disponibilite']), 4))
    return suggestions

def toutes_disponibilites(antenne_cible, jour, semaine_id):
    """Retourne la disponibilité de toutes les antennes sauf l'antenne cible."""
    idx_cible = ANTENNES_ORDRE.index(antenne_cible) if antenne_cible in ANTENNES_ORDRE else -1
    result = []
    for antenne in ANTENNES_ORDRE:
        if antenne == antenne_cible:
            continue
        dispo, capacite = evaluer_disponibilite(antenne, jour, semaine_id)
        distance = abs(ANTENNES_ORDRE.index(antenne) - idx_cible) if idx_cible >= 0 else 99
        result.append({'antenne': antenne, 'distance': distance, 'disponibilite': dispo, 'capacite': capacite})
    ordre = {"Libre (Aucun DPS)": 0, "Libre (Marge": 1, "Partielle": 2, "Indisponible": 3}
    result.sort(key=lambda x: (next((v for k, v in ordre.items() if k in x['disponibilite']), 4), x['distance']))
    return result

def ajouter_renforts(semaine_id, dps_parent_id, antenne, jour, nom_dps, nb_envoye):
    """Crée une ligne [R] chez l'antenne qui envoie le renfort ET met à jour le DPS principal."""
    conn = get_conn()
    c = conn.cursor()
    
    # Créer la ligne [R] chez l'antenne qui envoie (le nb du parent reste inchangé ;
    # son Manque est recalculé dynamiquement via la somme des [R] liés)
    c.execute("""INSERT INTO dps (semaine_id, antenne, jour, nom_dps, nb, tl, est_renfort, parent_dps_id, est_manuel)
                 VALUES (?, ?, ?, '[R] ' || ?, 0, ?, 1, ?, 1)""",
              (semaine_id, antenne, jour, nom_dps, nb_envoye, dps_parent_id))
    
    conn.commit()
    conn.close()