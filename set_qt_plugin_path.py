import os
import sys

if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    bundle_dir = sys._MEIPASS
    os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = os.path.join(bundle_dir, "platforms")