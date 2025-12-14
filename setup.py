import sys
import os
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might be needed to fine-tune them.
build_exe_options = {
    "packages": ["src", "PyQt6", "os", "sys", "logging", "yaml"],
    "includes": ["src.main", "src.model", "src.view", "src.presenter", "src.config", "src.performance", "src.theme"],
    "include_files": ["config.yaml"],
    "excludes": ["tkinter", "unittest", "pydoc", "test", "distutils", "setuptools"],
    "optimize": 2,
}

# Base for the executable
base = None
if sys.platform == "win32":
    base = "Win32GUI" # For Windows GUI applications
elif sys.platform == "linux":
    base = None # For Linux, usually no special base is needed for GUI

setup(
    name="MinimalGUI",
    version="0.1.0",
    description="A minimal PyQt6 GUI application.",
    options={"build_exe": build_exe_options},
    executables=[Executable("minimal_gui.py", base=base, target_name="MinimalGUI")],
)