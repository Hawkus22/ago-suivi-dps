# database.py
import sqlite3
import os
import sys

def _get_db_path():
    if getattr(sys, 'frozen', False):
        # Exécutable compilé : DB à côté du .exe, pas dans le dossier temp PyInstaller
        return os.path.join(os.path.dirname(sys.executable), "ago_suivi.db")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "ago_suivi.db")

DB_PATH = _get_db_path()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS semaines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero INTEGER UNIQUE,
        date_debut TEXT,
        date_fin TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS dps (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        semaine_id INTEGER,
        antenne TEXT,
        jour TEXT,
        nom_dps TEXT,
        nb INTEGER DEFAULT 0,
        tl INTEGER DEFAULT 0,
        est_renfort INTEGER DEFAULT 0,
        parent_dps_id INTEGER,
        FOREIGN KEY(semaine_id) REFERENCES semaines(id),
        FOREIGN KEY(parent_dps_id) REFERENCES dps(id)
    )''')
    # Migration : colonne est_manuel (renforts créés manuellement depuis l'appli)
    try:
        c.execute("ALTER TABLE dps ADD COLUMN est_manuel INTEGER DEFAULT 0")
    except Exception:
        pass  # Colonne déjà présente
    # Table de sauvegarde des renforts manuels avant ré-import
    c.execute('''CREATE TABLE IF NOT EXISTS renforts_backup (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        semaine_num INTEGER,
        antenne TEXT,
        jour TEXT,
        nom_dps TEXT,
        nb INTEGER DEFAULT 0,
        tl INTEGER DEFAULT 0,
        parent_antenne TEXT,
        parent_jour TEXT,
        parent_nom TEXT
    )''')
    conn.commit()
    conn.close()

def get_conn():
    return sqlite3.connect(DB_PATH)
