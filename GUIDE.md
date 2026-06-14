# PHARE — Guide complet
### Plateforme Harmonisée d'Affectation des Renforts et des Effectifs
**Côtes-d'Armor (22) — Hawkus Corp © 2026**

---

## Pourquoi PHARE ?

Chaque semaine, les antennes du département engagent des bénévoles sur des DPS (Dispositifs Prévisionnels de Secours). Il faut savoir en temps réel :
- Quels DPS sont **incomplets** (pas assez d'IS engagés)
- Quelle antenne peut **envoyer des renforts**
- Combien d'IS sont **engagés au total** sur la semaine

PHARE centralise tout ça dans un tableau partagé, visible et modifiable depuis n'importe quel poste ou téléphone, en temps réel.

---

## Architecture

```
Application Desktop (Windows/macOS)
        │
        ▼
  Base de données Supabase (cloud)  ◄──► PWA Mobile (iPhone / Android)
  yszgqjlpyqznwjalvwcc.supabase.co        hawkus22.github.io/ago-suivi-dps/pwa/
```

Toutes les données sont **partagées et synchronisées** entre le desktop et le mobile. Une modification faite sur téléphone est immédiatement visible sur le desktop, et inversement.

---

## 1. APPLICATION DESKTOP

**Pour qui :** Responsable de l'antenne de Lannion, sur PC/Mac au bureau.
**Fichier :** `PHARE - Suivi Départemental des DPS.exe` (Windows)

### Lancer l'application

Double-cliquer sur l'exécutable. Une connexion internet est requise.

---

### Le tableau principal

```
┌──────────────┬───────────────────────────────────────────────────────┐
│   Antenne    │  Lundi        │  Mardi        │  ...  │  Dimanche     │
│   (figée)    │ DPS│Eng│Mq│Σ  │ DPS│Eng│Mq│Σ  │       │ DPS│Eng│Mq│Σ │
├──────────────┼───────────────┼───────────────┼───────┼───────────────┤
│ LNP (Lannion)│ Match Foot... │               │       │               │
│ STB (St-Brieuc)│            │ [R] Match...  │       │               │
│ ...          │               │               │       │               │
└──────────────┴───────────────┴───────────────┴───────┴───────────────┘
```

**Colonnes par jour :**
| Colonne | Signification |
|---|---|
| **DPS** | Nom de l'activité (avec horaires) |
| **Engagés** | IS confirmés (renforts inclus pour les DPS principaux) |
| **Manque** | IS encore nécessaires pour couvrir ce DPS |
| **Σ** | Effectif total requis |

**Code couleur :**
| Couleur | Signification |
|---|---|
| 🟡 Orange | DPS principal **incomplet** |
| 🟢 Vert | DPS principal **complet** |
| 🟡 Jaune clair | Renfort [R] **incomplet** |
| 🔵 Bleu clair | Renfort [R] **complet** |

---

### Fonctions de la barre d'outils

#### 📥 Importer Export Portail (.xlsx)
Charge les DPS de la semaine depuis un export Excel du portail AGO.
- Le fichier doit contenir l'onglet **"Liste des evenements"**
- Seuls les DPS **incomplets** (Présents < Requis) sont importés
- Un ré-import de la même semaine **remplace** les données (les renforts manuels sont sauvegardés automatiquement)

#### Sélecteur **Semaine active**
Permet de naviguer entre les semaines enregistrées. Les données de chaque semaine sont conservées indéfiniment.

#### 📅 Nouvelle semaine
Crée une semaine vide sans importer de fichier. Utile pour saisir manuellement les DPS ou préparer la semaine à l'avance.
- Renseigner : numéro de semaine, date début, date fin

#### 🔄 Réinjecter les renforts
S'active automatiquement après un ré-import si des renforts manuels avaient été saisis.
Restaure les lignes [R] qui auraient été effacées par le nouvel import.
Le bouton indique le nombre de renforts en attente : `🔄 Réinjecter (3 renforts)`

#### 📊 Synthèse de la semaine
Affiche un récapitulatif complet de la semaine active :
- Tableau par antenne et par jour
- Bilan global (DPS, IS requis, engagés, manquants)
- **📱 Copier pour WhatsApp** → texte formaté prêt à coller
- **🖨️ Imprimer** → impression ou export PDF

---

### Modifier les données dans le tableau

**Double-clic sur la colonne "Engagés"** d'un renfort [R]
→ Saisir le nombre d'IS effectivement envoyés par cette antenne

**Double-clic sur la colonne "Σ"** de n'importe quelle ligne
→ Modifier le besoin total (si le portail AGO s'est trompé)

La sauvegarde est **immédiate** en base. Le calcul "Manque" se recalcule automatiquement.

---

### Gérer les renforts

**Clic droit sur un DPS incomplet** → "💡 Proposer des renforts"

Une fenêtre s'ouvre avec :
- Les 3 antennes **voisines** recommandées (classées par disponibilité)
- ☑ "Afficher toutes les antennes" pour voir l'ensemble du département

**Disponibilité estimée :**
| Statut | Signification |
|---|---|
| Libre (Aucun DPS) | Antenne sans engagement ce jour |
| Libre (Marge de X IS) | Antenne avec des IS disponibles |
| Partielle | Antenne partiellement engagée |
| Indisponible | Antenne sans IS disponibles |

Cocher une ou plusieurs antennes → **Valider** → des lignes [R] sont créées avec Engagés = 0.
Remplir ensuite le nombre d'IS envoyés par double-clic sur "Engagés" de chaque [R].

---

### Supprimer un DPS

**Clic droit** → "🗑️ Supprimer ce DPS"
Supprime la ligne ET tous ses renforts [R] associés.

---

### Exporter vers Excel

Menu **Fichier → 📤 Exporter vers Excel AGO**
Génère un fichier `.xlsx` formaté avec couleurs et en-têtes sur 2 niveaux, prêt à partager.

---

## 2. PWA MOBILE

**Pour qui :** Tous les membres de l'équipe, sur smartphone (iPhone ou Android).
**Accès :** `https://hawkus22.github.io/ago-suivi-dps/pwa/`

### Installer l'application sur son téléphone

**Android (Chrome) :**
Ouvrir l'URL dans Chrome → un bouton vert **"📲 Ajouter à l'écran d'accueil"** apparaît sous le formulaire de connexion → appuyer → confirmer.

**iPhone (Safari) :**
Ouvrir l'URL dans Safari → appuyer sur l'icône **□↑** (partager) → **"Sur l'écran d'accueil"** → Ajouter.

Une fois installée, l'app s'ouvre en plein écran comme une vraie application, sans barre d'URL.

---

### Première connexion

1. Ouvrir la PWA
2. Entrer son **email** et son **mot de passe**
3. Appuyer sur **Se connecter**

> Les nouveaux utilisateurs reçoivent une invitation par email.
> Le lien d'invitation ouvre la PWA et propose de définir un mot de passe.
> Le navigateur peut mémoriser les identifiants → connexion automatique au prochain lancement.

---

### Navigation dans la PWA

**En haut :** Sélecteur de semaine + bouton **+** (nouvelle semaine)

**Onglets de jours :** Lun / Mar / Mer / Jeu / Ven / Sam / Dim
→ Appuyer sur un jour pour voir les DPS de ce jour

**Cartes par antenne :**
Chaque antenne a sa carte. Les DPS du jour sélectionné y sont listés avec le code couleur habituel.
Appuyer sur l'en-tête d'une carte pour la replier/déplier.

---

### Fonctions disponibles sur mobile

#### ✏️ Modifier un DPS
Appuyer sur le crayon ✏️ → modifier **Engagés** et/ou **Σ** → Enregistrer.

#### + DPS — Ajouter un DPS manuellement
Appuyer sur **+ DPS** dans l'en-tête d'une carte → renseigner :
- Nom du DPS
- Engagés (nombre d'IS actuels)
- Requis total (Σ)

#### 💡 Renfort — Proposer des renforts
Apparaît sous un DPS **incomplet** → appuyer → choisir une ou plusieurs antennes → Valider.
Des lignes [R] sont créées avec Engagés = 0. Les remplir ensuite avec ✏️.

#### 🗑️ Supprimer un DPS
Appuyer sur la corbeille → confirmer. Supprime aussi les renforts [R] associés.

#### 📊 Synthèse
Bouton **📊** en haut à droite → synthèse complète de la semaine + bouton **"📱 Copier WhatsApp"**.

#### ↻ Actualiser
Bouton **↻** → recharge les données depuis Supabase (utile si un collègue a fait des modifications).

#### 🚪 Déconnexion
Bouton **🚪** → confirmation → retour à l'écran de connexion.

---

## 3. GESTION DES UTILISATEURS

**Qui peut gérer les accès :** L'administrateur (responsable du projet), via le dashboard Supabase.
**Dashboard :** `https://supabase.com/dashboard/project/yszgqjlpyqznwjalvwcc`

### Inviter un nouvel utilisateur

1. Dashboard Supabase → **Authentication → Users**
2. Cliquer **"Invite user"**
3. Saisir l'email du collègue → **Send invitation**
4. Le collègue reçoit un email avec un lien
5. Il clique → la PWA s'ouvre → il définit son mot de passe
6. Connexion mémorisée sur son téléphone

### Mot de passe oublié

1. Dashboard Supabase → **Authentication → Users**
2. Cliquer sur l'utilisateur → **"Send password recovery"**
3. Le collègue reçoit un email avec un lien de réinitialisation
4. Il clique → la PWA s'ouvre → il définit un nouveau mot de passe

### Révoquer un accès

Dashboard Supabase → **Authentication → Users** → cliquer sur l'utilisateur → **"Delete user"**

---

## 4. INFORMATIONS TECHNIQUES

| Élément | Détail |
|---|---|
| Base de données | Supabase (PostgreSQL cloud) |
| Projet Supabase | `ago-suivi-dps` |
| Code source | `https://github.com/Hawkus22/ago-suivi-dps` |
| PWA | `https://hawkus22.github.io/ago-suivi-dps/pwa/` |
| Version desktop | 1.1.0 (build 2026-06-14) |
| Connexion requise | Oui (internet obligatoire) |
| Données partagées | Oui — temps réel entre tous les appareils |

### En cas de problème de connexion
- Vérifier la connexion internet
- Recharger l'application (↻ sur mobile, relancer le desktop)
- Si le problème persiste : contacter l'administrateur

---

*Document généré le 14/06/2026 — Hawkus Corp*
