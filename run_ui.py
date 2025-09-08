"""Simple runner script for the Streamlit UI."""

import subprocess
import sys
import os

def run_streamlit():
    """Run the Streamlit app."""
    # Change to the project directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Run streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
        "--server.port", "8501",
        "--server.address", "localhost"
    ])

if __name__ == "__main__":
    print("🍳 Starting Some Good Food UI...")
    print("🌐 Opening at http://localhost:8501")
    run_streamlit()