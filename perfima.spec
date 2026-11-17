# PyInstaller spec for the desktop app. Build from the directory that contains perfima/:
#   pip install -r perfima/requirements-build.txt
#   pyinstaller perfima/perfima.spec
# The executable is written to dist/perfima (dist/perfima.exe on Windows).
import os

package_dir = SPECPATH
project_root = os.path.dirname(package_dir)

a = Analysis(
    [os.path.join(package_dir, "desktop.py")],
    pathex=[project_root],
    datas=[(os.path.join(package_dir, "static"), "perfima/static")],
    hiddenimports=[
        # uvicorn picks these by name at runtime
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.loops.asyncio",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.http.h11_impl",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan.on",
        "uvicorn.lifespan.off",
        # passlib loads its hash handlers lazily
        "passlib.handlers.bcrypt",
    ],
    excludes=["tkinter", "pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="perfima",
    debug=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    # keeps a console window with the server log, closing it stops Perfima
    console=True,
)
