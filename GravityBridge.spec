# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [
    ('web',              'web'),
    ('core',             'core'),
    ('rag',              'rag'),
    ('providers',        'providers'),
    ('tools',            'tools'),
    ('assets',           'assets'),
    ('wiki',             'wiki'),
    ('_knowledge.json',  '.'),
    ('config.yaml',      '.'),
    # Scripts raíz que el launcher importa dinámicamente
    ('bridge_server.py', '.'),
    ('dashboard.py',     '.'),
    ('gravity_tray.py',  '.'),
    ('ask_deepseek.py',  '.'),
    ('health_check.py',  '.'),
]
binaries = []
hiddenimports = [
    'pystray', 'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont',
    'aiohttp', 'yaml', 'rich', 'rich.console', 'rich.panel',
    'anthropic', 'pymysql',
    'win32api', 'win32security', 'win32con', 'win32event', 'winerror',
    'prometheus_client',
    'psutil',
    'cryptography', 'cryptography.hazmat.primitives',
    'sentence_transformers',
]
tmp_ret = collect_all('pystray')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['gravity_launcher.pyw'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='GravityBridge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\gravity_icon.ico'],
)
