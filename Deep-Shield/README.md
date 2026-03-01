# DeepShield

DeepShield is a hackathon-ready web app for digital safety education.

It includes:
- **Image Authenticity Analyzer**: deterministic heuristic scoring for synthetic/manipulated image signals.
- **Headline Scanner**: rule-based manipulation and clickbait risk scoring.

## Monorepo Structure

- `deep-shield-backend` → FastAPI backend
- `deep-shield-frontend` → Next.js frontend

---

## Local Development

### Backend

```bash
cd deep-shield-backend
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py
```

Backend runs on `http://localhost:8001`.

### Frontend

```bash
cd deep-shield-frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:3000`.

---

## Deploy to Production (Recommended)

### 1) Deploy Backend to Render

Create a **Web Service** from this repo.

- **Root Directory**: `Deep-Shield/deep-shield-backend`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

Set environment variable:

- `CORS_ORIGINS=https://YOUR_VERCEL_DOMAIN`

(You can include multiple origins as comma-separated values.)

### 2) Deploy Frontend to Vercel

Import the same repo.

- **Root Directory**: `Deep-Shield/deep-shield-frontend`

Set environment variable:

- `NEXT_PUBLIC_API_BASE_URL=https://YOUR_RENDER_BACKEND_URL`

Deploy.

---

## Required Env Vars

### Backend (`deep-shield-backend`)

- `PORT` (provided by Render automatically)
- `CORS_ORIGINS` (required in production)

### Frontend (`deep-shield-frontend`)

- `NEXT_PUBLIC_API_BASE_URL` (required in production)

---

## Notes

- No Torch/Transformers are used in image analysis.
- Output is deterministic for the same image.
- Scores are probabilistic risk signals, not forensic proof.
