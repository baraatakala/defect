@echo off
echo 🏗️ Starting Building Defect Detector...
cd /d "c:\Users\isc\VS_Code\building_defect_detector"
echo 📍 Working directory: %CD%

REM Kill any existing Flask processes on port 5000
echo 🔄 Stopping existing Flask processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo 🚀 Starting Building Defect Detector...
C:\Users\isc\VS_Code\.venv\Scripts\python.exe app.py
