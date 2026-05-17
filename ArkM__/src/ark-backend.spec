# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['backend_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('backend', 'backend'), ('core', 'core'), ('config.py', '.'), ('ark_style.py', '.')],
    hiddenimports=['uvicorn', 'fastapi', 'pydantic', 'requests', 'config', 'backend.server', 'backend.download_engine', 'backend.album_manager', 'core.result'],
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
    [],
    exclude_binaries=True,
    name='ark-backend',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='ark-backend',
)
