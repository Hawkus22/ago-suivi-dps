# AGO — Suivi Automatisé des DPS
## Guide d'installation — v1.1.0

---

### Ce que vous recevez

Vous devez recevoir **deux fichiers** de la part de votre référent :

| Fichier | Rôle |
|---|---|
| `AGO-Suivi-v1.1.0.exe` | L'application complète (aucune installation requise) |
| `ago_config.ini` | Connexion à la base de données partagée |

> **Ces deux fichiers doivent toujours rester dans le même dossier.**

---

### Installation (5 minutes)

**1. Créer un dossier dédié**

Créez un dossier sur votre poste, par exemple :
```
C:\AGO\
```

**2. Copier les deux fichiers dans ce dossier**

```
C:\AGO\
    AGO-Suivi-v1.1.0.exe
    ago_config.ini
```

**3. Lancer l'application**

Double-cliquez sur `AGO-Suivi-v1.1.0.exe`.

> ⚠️ **Alerte Windows SmartScreen** — normal pour une application non signée.  
> Cliquez **"Informations complémentaires"** puis **"Exécuter quand même"**.

L'application s'ouvre. Si c'est le premier lancement, la liste des semaines est vide — c'est normal.

---

### Utilisation rapide

| Action | Comment |
|---|---|
| Importer un export portail | Cliquez **📥 Importer** → sélectionnez le fichier `.xlsx` |
| Changer de semaine | Menu déroulant **Semaine active** |
| Modifier les effectifs | Double-clic sur la colonne **Engagés** ou **Σ** d'une ligne |
| Ajouter un renfort | Clic droit sur un DPS incomplet → **Proposer des renforts** |
| Synthèse semaine | Bouton **📊 Synthèse** (copie WhatsApp ou impression) |
| Guide complet | Menu **❓ Aide → Guide d'utilisation** |

---

### Données partagées

- Les données sont **communes à tous les postes** de l'antenne (hébergement cloud).
- Une **connexion internet** est nécessaire.
- Pour voir les modifications d'un collègue : changez de semaine et revenez, ou relancez l'application.

---

### Résolution des problèmes fréquents

| Symptôme | Solution |
|---|---|
| Erreur "ago_config.ini introuvable" | Vérifiez que `ago_config.ini` est dans le même dossier que le `.exe` |
| Erreur de connexion / timeout | Vérifiez votre connexion internet |
| Alerte Windows Defender | Cliquez "Informations complémentaires" → "Exécuter quand même" |
| L'appli se ferme immédiatement | Contactez votre référent (problème de configuration) |

---

### Configuration (référent uniquement)

Le fichier `ago_config.ini` contient l'URL de connexion à la base de données Supabase :

```ini
[database]
url = postgresql://postgres:MOT_DE_PASSE@db.xxx.supabase.co:5432/postgres
```

> ⚠️ Ne communiquez pas ce fichier en dehors de l'antenne.  
> En cas de compromission du mot de passe, changez-le sur [supabase.com](https://supabase.com) et redistribuez le fichier.

---

*AGO Suivi DPS v1.1.0 — Hawkus Corp © 2026*  
*Développé par Vachon Marc-Olivier — Mis à disposition pour l'Antenne de Lannion (22 LNP)*
