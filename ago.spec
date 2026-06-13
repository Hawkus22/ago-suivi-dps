# ago.spec — PyInstaller spec pour AGO Suivi DPS
# Usage : pyinstaller ago.spec
# Prérequis : pip install pyinstaller  (voir requirements-dev.txt)
# -*- mode: python ; coding: utf-8 -*-

import sys
sys.path.insert(0, '.')
from version import VERSION

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Assets graphiques embarqués dans l'exécutable
        ('Hawkus Corp 1.png',     '.'),
        ('Hawkus Corp 1 tel.png', '.'),
        ('Hawkus Corp 16_9.png',  '.'),
        ('Hawkus Corp 2.png',     '.'),
    ],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        'pandas',
        'pandas._libs.tslibs.np_datetime',
        'pandas._libs.tslibs.nattype',
        'pandas._libs.tslibs.timedeltas',
        'openpyxl',
        'openpyxl.cell._writer',
        'psycopg2',
        'psycopg2.extensions',
        'psycopg2._psycopg',
        'psycopg2.extras',
        'configparser',
        'dateutil',
        'dateutil.relativedelta',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', 'matplotlib', 'scipy',
        'IPython', 'jupyter', 'notebook',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=f'AGO-Suivi-v{VERSION}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,          # UPX désactivé : évite les faux positifs antivirus
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,      # Pas de fenêtre console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='icon.ico',  # Décommenter avec un fichier .ico Windows valide
    #
    # Note : ago_suivi.db et ago_config.ini NE SONT PAS embarqués.
    # ago_config.ini doit être placé à côté du .exe avec l'URL Supabase.
)
