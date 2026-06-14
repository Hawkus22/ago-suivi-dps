# AGO — Suivi Automatisé des DPS
### Application de gestion des Dispositifs Prévisionnels de Secours — Côtes-d'Armor (22)

---

## Contexte

Les bénévoles de la Croix-Rouge française du département **Côtes-d'Armor (22)** assurent des Dispositifs Prévisionnels de Secours (DPS) tout au long de l'année — événements sportifs, culturels, rassemblements publics. Chaque DPS nécessite un nombre défini d'Intervenants Secouristes (IS).

Le portail AGO recense l'ensemble des événements du département et indique pour chaque DPS le nombre d'IS requis et le nombre d'IS déjà engagés. Lorsqu'un DPS est **incomplet** (engagés < requis), il faut trouver des renforts auprès des autres antennes.

**AGO Suivi DPS** automatise ce suivi semaine par semaine, pour les 11 antennes du département.

---

## Ce que fait l'application

### 1. Import depuis le portail AGO
- L'utilisateur exporte la liste des événements depuis le portail AGO au format `.xlsx`
- L'application lit ce fichier et **ne charge que les DPS incomplets**
- Les DPS sont automatiquement liés à leurs renforts via le numéro d'activité (colonne A)
- Un résumé de l'import s'affiche (nombre de DPS, renforts, semaines détectées)

### 2. Tableau de bord hebdomadaire
- Vue en grille : **11 antennes** (lignes) × **7 jours** (colonnes)
- Chaque cellule affiche pour un DPS : Nom, Engagés, Manque, Σ (total requis)
- La colonne **Antenne** est figée à gauche pour faciliter la navigation
- Code couleur immédiat :

| Couleur | Signification |
|---|---|
| 🟠 Orange | DPS principal **incomplet** |
| 🟢 Vert | DPS principal **complet** |
| 🟡 Jaune | Renfort **[R]** incomplet |
| 🔵 Bleu | Renfort **[R]** complet |

### 3. Saisie manuelle des effectifs
- **Double-clic** sur la colonne *Engagés* d'un renfort `[R]` pour saisir le nombre d'IS engagés
- **Double-clic** sur *Σ* pour modifier le besoin total
- La sauvegarde est **immédiate** en base de données
- Le calcul du Manque du DPS parent se recalcule automatiquement

### 4. Gestion des renforts
- **Clic droit** sur un DPS incomplet → *Proposer des renforts*
- L'application calcule la disponibilité des antennes voisines et les classe par distance et disponibilité
- Option **"Toutes les antennes"** pour voir toutes les antennes du département
- La ligne `[R]` est créée avec Engagés = 0, à remplir manuellement au fil du temps

### 5. Réinjection des renforts manuels
- Lors d'un ré-import (nouveau fichier portail pour la même semaine), les renforts ajoutés manuellement seraient normalement perdus
- L'application les **sauvegarde automatiquement** avant l'écrasement
- Le bouton 🔄 **Réinjecter** permet de les restaurer après l'import
- Détection automatique des doublons (un renfort déjà dans le nouvel import n'est pas créé en double)

### 6. Synthèse de la semaine
- Bouton **📊 Synthèse** : récapitulatif complet de la semaine active
- **Copie WhatsApp** : texte formaté (gras, italique, emojis) prêt à coller dans une conversation
- **Impression** : envoi vers imprimante ou PDF

### 7. Export Excel
- Menu **Fichier → Exporter vers Excel AGO**
- Génère un fichier `.xlsx` formaté avec couleurs et en-têtes sur 2 niveaux

---

## Architecture technique

### Application desktop (v1.1.0 — actuelle)
```
PC / Mac
└── AGO-Suivi-v1.1.0.exe   (PyQt6 + Python, onefile PyInstaller)
    └── ago_config.ini      (URL de connexion Supabase)
            ↓
        Supabase            (PostgreSQL cloud — données partagées entre postes)
```

### Base de données (Supabase / PostgreSQL)

| Table | Contenu |
|---|---|
| `semaines` | Semaines importées (numéro, dates début/fin) |
| `dps` | Tous les DPS et renforts [R] de chaque semaine |
| `renforts_backup` | Sauvegarde des renforts manuels avant ré-import |

Colonnes clés de `dps` :
- `est_renfort` — 0 = DPS principal, 1 = renfort [R]
- `est_manuel` — 1 = créé manuellement dans l'app (pas issu de l'import)
- `parent_dps_id` — lien vers le DPS principal pour un renfort
- `nb` — IS engagés, `tl` — IS requis

### Antennes gérées (11)
LNP Lannion · PDG Guingamp · PPL Paimpol · STB Saint-Brieuc · PLR Plérin ·
LPP Lamballe · BRC Broons · PDN Dinan · QTN Quintin · LCB Loudéac · 22 Siège

---

## Stack technique

| Composant | Technologie |
|---|---|
| Interface | PyQt6 (Python) |
| Base de données | PostgreSQL via Supabase (cloud) |
| Driver DB | psycopg2-binary |
| Lecture Excel | pandas + openpyxl |
| Compilation | PyInstaller (onefile) |
| CI/CD | GitHub Actions (build Windows + macOS automatique) |

---

## Fichiers du projet

| Fichier | Rôle |
|---|---|
| `main.py` | Point d'entrée |
| `config.py` | Constantes (couleurs, ordre antennes, resource_path) |
| `database.py` | Connexion Supabase, initialisation des tables |
| `import_handler.py` | Lecture fichier Excel portail, import en base |
| `renfort_engine.py` | Calcul disponibilités, création renforts |
| `ui_main.py` | Interface principale (tableau, toolbar, menus) |
| `ui_popup.py` | Popup sélection antennes pour renforts |
| `version.py` | Numéro de version (`1.1.0`) |
| `ago.spec` | Spec PyInstaller (compilation onefile) |
| `ago_config.ini` | URL Supabase — **confidentiel, ne pas commiter** |
| `requirements.txt` | Dépendances Python runtime |
| `requirements-dev.txt` | Dépendances dev (PyInstaller) |
| `INSTALLATION.md` | Guide d'installation pour les collègues |
| `.github/workflows/build.yml` | CI/CD : compilation automatique Windows + macOS |

---

## Distribution

Deux fichiers à distribuer aux utilisateurs :
```
AGO-Suivi-v1.1.0.exe   (Windows)
AGO-Suivi-v1.1.0       (macOS Apple Silicon)
ago_config.ini          (à joindre manuellement — contient le mot de passe)
```

Les exécutables sont générés automatiquement via **GitHub Actions** à chaque push sur `master`.

---

*AGO Suivi DPS v1.1.0 — Hawkus Corp © 2026*
*Développé par Vachon Marc-Olivier — Antenne de Lannion (22 LNP)*
