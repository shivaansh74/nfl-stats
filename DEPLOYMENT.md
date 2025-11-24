# NFL Stats CLI - Deployment Guide

## Free Hosting Options

### Option 1: Render + Vercel (RECOMMENDED)

#### Backend (Render.com - Free)
1. Push your code to GitHub
2. Go to [render.com](https://render.com) and sign up
3. Click "New +" → "Web Service"
4. Connect your GitHub repository
5. Configure:
   - **Name**: `nfl-stats-api`
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn api_server:app --bind 0.0.0.0:$PORT`
   - **Instance Type**: Free
6. Click "Create Web Service"
7. Copy your backend URL (e.g., `https://nfl-stats-api.onrender.com`)

#### Frontend (Vercel - Free)
1. Go to [vercel.com](https://vercel.com) and sign up
2. Click "Add New" → "Project"
3. Import your GitHub repository
4. Configure:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Environment Variables**:
     - `NEXT_PUBLIC_API_URL` = `https://nfl-stats-api.onrender.com` (your backend URL)
5. Click "Deploy"

**✅ Done!** Your app is live at `https://your-app.vercel.app`

---

### Option 2: Railway (All-in-One)

1. Push to GitHub
2. Go to [railway.app](https://railway.app)
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway will auto-detect both services
6. Set environment variables:
   - For frontend: `NEXT_PUBLIC_API_URL` = `https://${{RAILWAY_STATIC_URL}}`

**Free tier**: $5/month credit (usually enough for hobby projects)

---

### Option 3: Fly.io (Advanced)

Good for more control, requires Docker knowledge.

---

## Important Notes

### Backend Considerations
- **Cold Starts**: Free tiers sleep after 15 min of inactivity
  - First request after sleep will be slow (10-30 seconds)
  - Subsequent requests are fast
- **Solution**: Use UptimeRobot (free) to ping your API every 5 minutes

### Frontend Caching
- Vercel/Netlify have excellent CDN caching
- Perfect for static sites like your Next.js frontend

### Environment Variables
Make sure to set:
- `NEXT_PUBLIC_API_URL` in frontend to point to your backend URL
- Update CORS settings in `api_server.py` if needed

---

## Quick Deploy Commands

### 1. Prepare for deployment
```bash
# Make sure all dependencies are in requirements.txt
pip freeze > requirements.txt

# Test production mode  locally
gunicorn api_server:app --bind 0.0.0.0:8000
```

### 2. Build frontend
```bash
cd frontend
npm run build
```

### 3. Push to GitHub
```bash
git add .
git commit -m "Prepare for deployment"
git push origin main
```

### 4. Deploy via platform UI
Follow the steps above for Render/Vercel or Railway

---

## Monitoring

### Free Monitoring Tools
- **Uptime Monitoring**: UptimeRobot, Better Uptime
- **Error Tracking**: Sentry (free tier)
- **Analytics**: Vercel Analytics (free), Google Analytics

---

## Estimated Costs

- **Render Free**: $0/month (sleeps after inactivity)
- **Vercel Free**: $0/month (100GB bandwidth, plenty for personal use)
- **Railway**: $5/month credit (usually covers 1-2 small services)

**Total: $0 - $5/month** ✅

---

## Need Help?

If you encounter issues:
1. Check Render/Vercel logs
2. Ensure environment variables are set correctly
3. Test locally first with production settings
