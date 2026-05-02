# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [
    ('frontend/dist',    'web'),       # Build React compilado → servido como /web
    ('core',             'core'),
    ('api',              'api'),
    ('rag',              'rag'),
    ('providers',        'providers'),
    ('tools',            'tools'),
    ('assets',           'assets'),
    ('wiki',             'wiki'),
    ('launchers',        'launchers'),
    ('_integrations',    '_integrations'),  # gemini_tts.py, comfy_client.py (MAI L2)
    ('_knowledge.json',  '.'),
    ('config.yaml',      '.'),
    # Scripts raiz que el launcher importa dinamicamente
    ('bridge_server.py', '.'),
    ('gravity_tray.py',  '.'),
    ('ask_deepseek.py',  '.'),
    ('health_check.py',  '.'),
    ('INSTALAR.py',      '.'),
]
binaries = []
hiddenimports = [
    'pystray', 'PIL', 'PIL.Image', 'PIL.ImageDraw', 'PIL.ImageFont',
    'aiohttp', 'yaml', 'rich', 'rich.console', 'rich.panel',
    'anthropic', 'pymysql',
    'win32api', 'win32security', 'win32con', 'win32event', 'winerror',
    'win32com', 'win32com.client', 'pythoncom',
    'prometheus_client',
    'psutil',
    'pyttsx3',
    'websocket', 'websocket._core',  # comfy_client.py (L2 MAI)
    'cryptography', 'cryptography.hazmat.primitives',
    'core.animation_engine',         # MAI motor de animacion
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
