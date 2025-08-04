#!/usr/bin/env python3
"""
Quick start script for Building Defect Detector
"""
import os
import sys
import subprocess

# Change to the building defect detector directory
os.chdir(r'c:\Users\isc\VS_Code\building_defect_detector')

# Set environment variables
os.environ['FLASK_APP'] = 'app.py'
os.environ['FLASK_ENV'] = 'development'

# Python executable path
python_exe = r'C:\Users\isc\VS_Code\.venv\Scripts\python.exe'

print("🏗️ Starting Building Defect Detector...")
print("📍 Working directory:", os.getcwd())
print("🐍 Python executable:", python_exe)

try:
    # Start the Flask application
    subprocess.run([python_exe, 'app.py'], check=True)
except KeyboardInterrupt:
    print("\n⏹️ Application stopped by user")
except Exception as e:
    print(f"❌ Error starting application: {e}")
