# config.py
import os
import sys

def resource_path(filename):
    """Résout le chemin d'un asset, compatible développement et PyInstaller onefile."""
    if getattr(sys, 'frozen', False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, filename)

ANTENNES_ORDRE = [
    "LNP (Lannion)", "PDG (Guingamp)", "PPL (Paimpol)", "STB (Saint Brieuc)",
    "PLR (Plérin)", "LPP (Lamballe)", "BRC (Broons)", "PDN (Dinan)",
    "QTN (Quintin)", "LCB (Loudéac)", "22 (Siège)"
]

MAPPING_ANTENNES = {
    "22 LNP": "LNP (Lannion)", "22 PDG": "PDG (Guingamp)", "22 PPL": "PPL (Paimpol)",
    "22 STB": "STB (Saint Brieuc)", "22 PLR": "PLR (Plérin)", "22 LPP": "LPP (Lamballe)",
    "22 BRC": "BRC (Broons)", "22 PDN": "PDN (Dinan)", "22 QTN": "QTN (Quintin)",
    "22 LCB": "LCB (Loudéac)", "22": "22 (Siège)"
}

JOURS_SEMAINE = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]

COLOR_ORANGE = "#FFC000"
COLOR_GREEN = "#C6EFCE"
COLOR_RENFORT_OK = "#9DC3E6"   # Bleu clair — renfort complet
COLOR_RENFORT_KO = "#FFE699"   # Jaune clair — renfort incomplet