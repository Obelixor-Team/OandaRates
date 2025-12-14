import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Now import and run the main module from src
import src.main

# The main execution block in src.main will be triggered by the import.
# If there's an unhandled exception, it should now propagate and show a traceback.
