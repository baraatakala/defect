@echo off
color 0A
echo.
echo ========================================
echo   🏗️ DEPLOY DEFECT DETECTOR - FASTEST WAY
echo ========================================
echo.

cd /d "c:\Users\isc\VS_Code\building_defect_detector"

echo ⚡ CHOOSE YOUR DEPLOYMENT METHOD:
echo.
echo [1] 🚄 Railway (2 minutes) - FASTEST
echo [2] 🌐 Render (3 minutes) 
echo [3] 📱 Vercel (4 minutes)
echo.

echo 🚄 RAILWAY DEPLOYMENT (RECOMMENDED):
echo.
echo Step 1: Push to GitHub
echo ----------------------
echo git init
echo git add .
echo git commit -m "Deploy defect detector"
echo git remote add origin https://github.com/baraatakala/defect-detector.git
echo git push -u origin main
echo.
echo Step 2: Deploy on Railway
echo -------------------------
echo 1. Go to: https://railway.app
echo 2. Click "New Project"
echo 3. Select "Deploy from GitHub repo" 
echo 4. Choose: baraatakala/defect-detector
echo 5. ✅ LIVE in 2 minutes!
echo.
echo 🎯 Your defect detector will be at: https://your-app.railway.app
echo.
pause
