# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['run_app.py'],
    pathex=['.'],
    binaries=[],
    datas=[('config.yaml', '.'), ('/home/skum/.pyenv/versions/3.11.13/lib/python3.11/site-packages/PyQt6/Qt6/plugins/platforms', 'platforms')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['set_qt_plugin_path.py'],
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
    name='OandaRates',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
