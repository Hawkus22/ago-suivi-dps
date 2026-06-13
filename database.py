# database.py
import psycopg2
import configparser
import os
import sys


def _get_config_path():
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), 'ago_config.ini')
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ago_config.ini')


def _get_db_url():
    config = configparser.ConfigParser()
    config.read(_get_config_path(), encoding='utf-8')
    try:
        return config['database']['url']
    except KeyError:
        raise RuntimeError(
            "Fichier ago_config.ini introuvable ou mal configuré.\n"
            "Créez ago_config.ini à côté de l'application avec :\n\n"
            "[database]\nurl = postgresql://postgres:MOT_DE_PASSE@db.xxx.supabase.co:5432/postgres"
        )


def get_conn():
    return psycopg2.connect(_get_db_url())


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS semaines (
        id SERIAL PRIMARY KEY,
        numero INTEGER UNIQUE,
        date_debut TEXT,
        date_fin TEXT
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS dps (
        id SERIAL PRIMARY KEY,
        semaine_id INTEGER,
        antenne TEXT,
        jour TEXT,
        nom_dps TEXT,
        nb INTEGER DEFAULT 0,
        tl INTEGER DEFAULT 0,
        est_renfort INTEGER DEFAULT 0,
        parent_dps_id INTEGER,
        est_manuel INTEGER DEFAULT 0,
        FOREIGN KEY(semaine_id) REFERENCES semaines(id),
        FOREIGN KEY(parent_dps_id) REFERENCES dps(id)
    )''')
    # Migration colonne est_manuel si table existante avant migration
    c.execute("ALTER TABLE dps ADD COLUMN IF NOT EXISTS est_manuel INTEGER DEFAULT 0")
    c.execute('''CREATE TABLE IF NOT EXISTS renforts_backup (
        id SERIAL PRIMARY KEY,
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
