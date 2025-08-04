@echo off
echo 🚀 Deploying Building Defect Detector to Railway...
echo.

echo 📁 Navigating to project directory...
cd /d "c:\Users\isc\VS_Code\building_defect_detector"

echo 📋 Current directory contents:
dir

echo.
echo 🔧 Adding all changes...
git add .

echo 📝 Committing changes...
git commit -m "🚀 Deploy enhanced Building Defect Detector with AI training features

✨ New Features:
- Interactive user feedback system (👍👎 buttons)
- Defect editing modal for corrections
- Advanced analytics dashboard with AI training metrics
- Real-time accuracy tracking and learning progress
- Enhanced UI with professional styling
- Database-driven ML training pipeline

🔧 Technical Updates:
- New API endpoints for feedback collection
- Enhanced analytics with training statistics
- Professional modal interfaces for defect editing
- Toast notifications for user feedback
- Responsive design improvements
- Print-friendly layouts maintained

🎯 AI Training Capabilities:
- Continuous learning from user feedback
- Accuracy rate calculation and tracking
- Training goal visualization
- User engagement metrics
- Comprehensive training data collection"

echo.
echo 🌐 Pushing to Railway...
git push origin main

echo.
echo ✅ Deployment initiated! 
echo 🔗 Check your Railway dashboard for deployment status
echo 📊 The enhanced AI training features will be live shortly!

pause
