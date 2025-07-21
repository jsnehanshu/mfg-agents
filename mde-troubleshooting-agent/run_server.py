import uvicorn
import sys
import os

# --- THE FIX: Add the project root to the Python path ---
# This ensures that all relative imports within the 'mde-troubleshooting-agent'
# directory are treated as part of a package.
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# ---------------------------------------------------------

if __name__ == "__main__":
    # We now run uvicorn programmatically, pointing it to the app instance in main.py
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)