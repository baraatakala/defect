# Railway Deployment Guide - Building Defect Detector

## 🚀 Quick Deploy to Railway

Follow these steps to deploy your Building Defect Detector to Railway:

### Prerequisites
- GitHub repository: https://github.com/baraatakala/defect
- Railway account (free tier available)

### Step 1: Connect to Railway

1. Go to [Railway.app](https://railway.app)
2. Sign up/Login with your GitHub account
3. Click "Start a New Project"
4. Select "Deploy from GitHub repo"
5. Choose your repository: `baraatakala/defect`

### Step 2: Configuration

Railway will automatically detect your Python application and use the configuration from:
- `Procfile`: Defines the web service command
- `requirements.txt`: Python dependencies
- `railway.json`: Railway-specific configuration
- `runtime.txt`: Python version

### Step 3: Environment Variables (Optional)

For production, you may want to set:
- `FLASK_ENV=production`
- `SECRET_KEY=your-secret-key-here`

### Step 4: Deploy

1. Railway will automatically build and deploy your app
2. You'll get a live URL like: `https://defect-production.up.railway.app`
3. The app will be automatically redeployed on every git push to main

### Features Included

✅ **Auto-scaling**: Railway handles traffic automatically
✅ **SSL Certificate**: HTTPS enabled by default
✅ **Custom Domain**: Connect your own domain (Pro plan)
✅ **Monitoring**: Built-in metrics and logs
✅ **Database**: SQLite included (or upgrade to PostgreSQL)

### File Upload Considerations

- Railway provides ephemeral filesystem
- Uploaded files are temporary and may be lost on redeploy
- For production, consider using Railway's volume storage or cloud storage

### Monitoring Your App

- View logs in Railway dashboard
- Monitor performance metrics
- Set up alerts for downtime

### Troubleshooting

If deployment fails:
1. Check the build logs in Railway dashboard
2. Verify all dependencies in `requirements.txt`
3. Ensure `spacy` model downloads correctly
4. Check Python version compatibility in `runtime.txt`

### Cost

- **Starter Plan**: $5/month per service
- **Pro Plan**: $20/month with additional features
- **Usage-based pricing** for resources beyond base allocation

---

🎉 **Your Building Defect Detector is now live on Railway!**

Share your deployment URL and start analyzing building survey reports with AI!
