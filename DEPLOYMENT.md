# 🚀 ThreatLens AI Production Deployment Guide

This guide details how to deploy ThreatLens AI to production. Due to the backend's persistent SQLite database and real-time WebSocket capabilities, the application is divided into a decoupled architecture:

1. **Frontend (React + Vite)**: Hosted on **Vercel** (fast, serverless global CDN).
2. **Backend (FastAPI + SQLite + WebSockets)**: Hosted on a stateful platform like **Render**, **Railway**, or **Fly.io** with persistent disk storage.

---

## 🎨 Architecture Summary

```
                  ┌───────────────────────┐
                  │   Vercel (Frontend)   │
                  │   React 18 + Vite     │
                  └──────────┬────────────┘
                             │
            HTTP API & WebSocket (WSS) Calls
                             │
                             ▼
              ┌──────────────────────────────┐
              │ Render/Railway (Backend)     │
              │ FastAPI Server               │
              │   ├── SQLite DB (Volume)     │
              │   └── ML Models (Volume)     │
              └──────────────────────────────┘
```

---

## 🖥️ Step 1: Deploy Backend (FastAPI)

Deploy your backend on **Render** or **Railway**. Render is used as the primary example below.

### Option A: Render Deployment (Docker or Python Service)
1. Sign up on [Render.com](https://render.com/).
2. Create a new **Web Service** and link your Git repository.
3. Configure the following service settings:
   - **Environment**: `Docker` (recommended as there is a `Dockerfile` in `backend/`) or `Python` (Build: `pip install -r requirements.txt`, Start: `uvicorn app.main:app --host 0.0.0.0 --port 10000`).
   - **Root Directory**: `backend`
   - **Region**: Select a region close to your target users.
4. Add the following **Environment Variables**:
   - `SECRET_KEY`: *[Generate a random long string]*
   - `DEBUG`: `False`
   - `DATABASE_URL`: `sqlite+aiosqlite:////data/threatlens.db` *(points database to the persistent storage disk)*
   - `ALLOWED_ORIGINS`: `https://your-frontend-domain.vercel.app` *(update once you have your Vercel URL)*
5. Configure **Persistent Disk (Volume)** (Crucial for SQLite and ML model persistence):
   - Under the service's **Disks** configuration, add a new volume.
   - **Name**: `threatlens-data`
   - **Mount Path**: `/data`
   - **Size**: 1 GB is plenty.
6. Click **Deploy Web Service**. Render will spin up the server, initialize the SQLite DB, train the demo ML models, and output a URL (e.g. `https://threatlens-api.onrender.com`).

---

## ⚡ Step 2: Deploy Frontend (React + Vite) on Vercel

1. Log in to [Vercel](https://vercel.com).
2. Click **Add New** > **Project** and select your Git repository.
3. Configure the Project Setup:
   - **Framework Preset**: `Vite` (Vercel auto-detects this).
   - **Root Directory**: Select `frontend` (crucial so Vercel builds from the correct folder).
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Expand **Environment Variables** and add:
   - **Key**: `VITE_API_URL`
   - **Value**: `https://threatlens-api.onrender.com/api` *(use the HTTPS URL of your deployed backend, appending `/api` at the end)*
5. Click **Deploy**. Vercel will build the React bundle, hook up the SPA routing redirect configuration (`vercel.json`), and assign you a live `.vercel.app` URL!

---

## 🔒 Step 3: Configure Backend CORS

1. Once Vercel generates your live URL (e.g., `https://threatlens-dashboard.vercel.app`), go back to your backend hosting dashboard (e.g., Render).
2. Update the `ALLOWED_ORIGINS` environment variable to include your new Vercel URL.
   ```
   ALLOWED_ORIGINS=https://threatlens-dashboard.vercel.app,http://localhost:5173
   ```
3. Restart or redeploy the backend web service to apply the updated CORS origins.

---

## 📊 Verification & Logs

- **API Documentation**: Navigate to `https://your-backend-domain.com/api/docs` to test endpoint triggers manually.
- **WebSocket Logs Feed**: Open your browser devtools console (`F12`) on your Vercel frontend. When you start the simulation on the **Live Monitor** page, you should see logs stream in in real-time under a `wss://` secure websocket connection.
