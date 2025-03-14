# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets/icon.png', 'assets'),
        ('assets/orb', 'assets/orb'),
        ('assets/rec', 'assets/rec'),
        ('assets/tools/ffmpeg.bat', 'assets/tools'),
        ('config.json.template', '.'),
        ('docs', 'docs'),  # 包含文档
    ],
    hiddenimports=[
        'PIL',
        'PIL.Image',
        'PIL.ImageQt',
        'cv2',
        'numpy',
        'PySide6',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'requests',
        'psutil',
        'keyboard',
        'mouse',
        'onnxruntime',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'paddlepaddle',
        'torch',
        'torchvision',
        'tensorflow',
        'ultralytics',
        'matplotlib',
        'scipy',
        'pandas',
        'seaborn',
        'thop',
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
    name='POE2TradePusher',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.png',
)
