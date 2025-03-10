# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\main.py'],
    pathex=[],
    binaries=[],
    datas=[('cache', 'cache'), ('src\\data', 'src\\data'), ('src\\dashboard', 'src\\dashboard'), ('src\\utils', 'src\\utils')],
    hiddenimports=['pandas', 'numpy', 'matplotlib', 'pandas_market_calendars', 'matplotlib.backends.backend_tkagg', 'yfinance', 'tkinter', 'urllib3', 'requests'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['upx'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PainelB3',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
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
    name='PainelB3',
)
