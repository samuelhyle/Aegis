# Deployment Guide

> **Live deployment**: [aegis-beta-bice.vercel.app](https://aegis-beta-bice.vercel.app)

AEGIS is fully deployed on **Vercel** — both the Next.js frontend and the Python FastAPI backend run as Vercel serverless functions. This guide explains the architecture and how to deploy your own instance.

---

## 🌐 Live Deployment URLs

| Service | URL | Purpose |
|---------|-----|---------|
| **Frontend** | https://aegis-beta-bice.vercel.app | User-facing Next.js app |
| **Backend API** | https://backend-three-tan-79.vercel.app | FastAPI Python backend |
| **Health Check** | https://backend-three-tan-79.vercel.app/health | `GET /health` |
| **API Docs** | https://backend-three-tan-79.vercel.app/docs | Interactive Swagger UI |

---

## 🏛️ Deployment Architecture

### Two Vercel Projects

```
┌─────────────────────────────────────────────────────────────┐
│  Vercel Account: samuelhyles-projects                       │
│                                                             │
│  ┌──────────────────────────┐  ┌──────────────────────────┐│
│  │  Project: aegis-beta     │  │  Project: backend        ││
│  │  Framework: Next.js 16   │  │  Runtime: Python 3.12    ││
│  │  URL: aegis-beta-bice    │  │  URL: backend-three-tan-79││
│  │  .vercel.app             │  │  .vercel.app              ││
│  │                          │  │                          ││
│  │  • React + SSR           │  │  • FastAPI + Mangum      ││
│  │  • /api/proxy/*          │  │  • 50+ endpoints         ││
│  │  • Rewrites → backend    │  │  • Serverless function   ││
│  └──────────────────────────┘  └──────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### Request Flow

```
User → aegis-beta-bice.vercel.app (Next.js)
         │
         ├─ Static page → Served from edge
         │
         └─ /api/proxy/* → Rewritten to backend-three-tan-79.vercel.app/*
                             │
                             └─ FastAPI handler → Response
```

---

## 📦 Repository Structure for Deployment

```
aegis/
├── web/                       # Frontend project (deployed as aegis-beta)
│   ├── app/                   # Next.js pages + API routes
│   ├── components/
│   ├── lib/
│   ├── next.config.ts         # Contains rewrite rules
│   ├── package.json
│   └── vercel.json            # Vercel project config
│
├── backend/                   # Backend project (deployed as backend)
│   ├── app.py                 # Vercel entry point (imports aegis.api:app)
│   ├── src/aegis/             # Self-contained backend code
│   ├── data/synthea/          # Seed CSV data
│   ├── requirements.txt       # Python dependencies
│   └── vercel.json            # Vercel project config
│
├── src/aegis/                 # Original backend source (synced to backend/)
├── docs/
└── ...
```

---

## 🚀 Deploying Your Own Instance

### Prerequisites
- [Vercel account](https://vercel.com)
- [Vercel CLI](https://vercel.com/docs/cli): `npm i -g vercel`
- GitHub repo with this code
- [MiniMax API key](https://platform.minimax.io/) (or OpenAI key)

### Step 1 — Clone & link

```bash
git clone https://github.com/samuelhyle/Aegis.git
cd Aegis

# Login to Vercel
vercel login
```

### Step 2 — Deploy the Backend

```bash
cd backend

# First deploy creates the project
vercel --prod

# Vercel auto-detects FastAPI, installs requirements.txt,
# and uses app.py as the entry point.
```

**Set environment variables** for the backend project:

```bash
vercel env add LLM_PROVIDER production
# → Enter: minimax

vercel env add LLM_MODEL production
# → Enter: MiniMax-M3

vercel env add MINIMAX_API_KEY production
# → Enter: your-minimax-api-key

vercel env add AEGIS_AUTH_DISABLED production
# → Enter: true

vercel env add AEGIS_ENV production
# → Enter: production

vercel env add AEGIS_DATA_DIR production
# → Enter: data/synthea

vercel env add CORS_ORIGINS production
# → Enter: https://your-frontend-domain.vercel.app
```

Redeploy to pick up the env vars:

```bash
vercel --prod
```

**Note the backend URL** — e.g., `https://backend-xyz.vercel.app`.

### Step 3 — Deploy the Frontend

```bash
cd ../web

# First deploy
vercel --prod

# Set environment variables pointing to the backend
vercel env add BACKEND_URL production
# → Enter: https://backend-xyz.vercel.app

vercel env add NEXT_PUBLIC_API_URL production
# → Enter: https://backend-xyz.vercel.app

vercel env add NEXT_PUBLIC_SOCKET_URL production
# → Enter: https://backend-xyz.vercel.app

# Redeploy
vercel --prod
```

### Step 4 — Set up custom domain (optional)

```bash
# Add your custom domain to the frontend
vercel domains add your-domain.com
```

---

## 🔧 Environment Variables Reference

### Backend (`backend/`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_PROVIDER` | ✅ | `mock` | `minimax`, `openai`, `local`, `mlx`, `mock` |
| `LLM_MODEL` | ✅ | `gpt-4o-mini` | Model ID (e.g., `MiniMax-M3`) |
| `MINIMAX_API_KEY` | ✅* | — | MiniMax API key (* required when LLM_PROVIDER=minimax) |
| `MINIMAX_BASE_URL` | ❌ | `https://api.minimax.io/v1` | MiniMax API base URL |
| `OPENAI_API_KEY` | ✅* | — | OpenAI key (* required when LLM_PROVIDER=openai) |
| `AEGIS_ENV` | ❌ | `development` | `production`, `staging`, `development` |
| `AEGIS_AUTH_DISABLED` | ❌ | `false` | `true` disables auth (for demos) |
| `AEGIS_DATA_DIR` | ❌ | `data/synthea` | Path to CSV data |
| `AEGIS_SECRET_KEY` | ❌ | random | Secret for JWT/sessions |
| `DATABASE_URL` | ❌ | `sqlite:///./aegis.db` | DB connection string |
| `CORS_ORIGINS` | ❌ | `http://localhost:3000` | Comma-separated allowed origins |
| `RATE_LIMIT_ENABLED` | ❌ | `true` | Enable rate limiting |
| `RATE_LIMIT_RPM` | ❌ | `60` | Requests per minute |
| `LOG_LEVEL` | ❌ | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### Frontend (`web/`)

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | ❌ | empty | Direct backend URL (skips proxy) |
| `BACKEND_URL` | ❌ | empty | Backend URL for proxy route |
| `NEXT_PUBLIC_SOCKET_URL` | ❌ | empty | WebSocket URL (for streaming) |
| `NEXT_PUBLIC_USER_*` | ❌ | — | Default user info for demo |

---

## 🔍 How the Frontend-Backend Connection Works

### Option A: With backend deployed (production)

When `BACKEND_URL` is set, the Next.js config adds a rewrite:

```ts
// next.config.ts
async rewrites() {
  return [
    {
      source: "/api/proxy/:path*",
      destination: `${BACKEND_URL}/:path*`,
    },
  ];
}
```

So when the frontend code calls `/api/proxy/v1/patients`, Next.js proxies it to `https://backend-xyz.vercel.app/v1/patients` and returns the response.

### Option B: Without backend (mock-only)

If `BACKEND_URL` is empty, the built-in Next.js API routes at `/app/api/v1/*` serve mock data. Useful for frontend-only development.

### The Proxy Catch-All Route

`web/app/api/proxy/[...path]/route.ts` is also available as a fallback that explicitly forwards requests in code (used when the rewrite isn't suitable, e.g., SSE streaming):

```ts
const response = await fetch(`${BACKEND_URL}/${path}`, {
  method: request.method,
  headers: request.headers,
});
```

---

## 🐳 Docker / Self-Hosting

If you prefer to host the backend on your own infrastructure:

### Dockerfile

A `Dockerfile` exists at the repository root for containerized deployment:

```bash
docker build -t aegis-backend .
docker run -p 8000:8000 \
  -e LLM_PROVIDER=minimax \
  -e MINIMAX_API_KEY=your-key \
  -e AEGIS_AUTH_DISABLED=true \
  -v $(pwd)/data:/app/data \
  aegis-backend
```

### Docker Compose

A `docker-compose.yml` is included for full-stack local development with PostgreSQL + pgvector + Redis:

```bash
docker-compose --profile frontend up
```

---

## 📊 Monitoring & Logs

### View logs

```bash
# Frontend logs
vercel logs https://web-khaki-two-44.vercel.app

# Backend logs
vercel logs https://backend-three-tan-79.vercel.app
```

### Metrics endpoints

| Endpoint | Description |
|----------|-------------|
| `/health` | Basic health check |
| `/metrics` | Prometheus-format metrics |
| `/metrics/agents` | Per-agent performance stats |
| `/v1/stats` | System stats (patient counts, etc.) |

---

## 🔒 Security Notes

- **Auth disabled by default** in demo deployments (`AEGIS_AUTH_DISABLED=true`)
- **CORS** is configured via `CORS_ORIGINS` — restrict in production
- **Rate limiting** is enabled by default (`RATE_LIMIT_RPM=60`)
- **API key** is stored as a Vercel secret, not visible in builds
- **No real PHI** — only Synthea synthetic data

For production use, enable auth, restrict CORS to your exact domain, and add proper secrets management.

---

## 🛠️ Troubleshooting

### Backend not responding
```bash
# Check logs
vercel logs https://backend-three-tan-79.vercel.app --follow

# Common issues:
# - Missing LLM_API_KEY → 500 on investigation endpoints
# - Missing CSV data → 0 patients returned
# - CORS misconfigured → frontend can't reach backend
```

### Frontend can't reach backend
1. Verify `BACKEND_URL` is set: `vercel env ls`
3. Test backend directly: `curl https://your-backend.vercel.app/health`
2. Test proxy: `curl https://your-frontend.vercel.app/api/proxy/health`

### LLM errors
- Verify your API key is valid and has credits
- Check `LLM_PROVIDER` matches your key type (`minimax` vs `openai`)
- Look for 4xx/5xx responses in `/v2/evaluation/report/{id}`

---

## 🔄 Continuous Deployment

Both projects auto-deploy from the `main` branch on GitHub. Every commit to `main` triggers a new deployment:

1. Push to `main`
2. Vercel detects the change
3. Builds + tests
4. Deploys to production
5. New URL available at the same alias

To deploy a preview:
```bash
vercel  # without --prod
# → Returns a preview URL like https://web-abc123.vercel.app
```

---

## 📞 Support

- **Issues**: https://github.com/samuelhyle/Aegis/issues
- **Live demo**: https://aegis-beta-bice.vercel.app
- **Docs**: see `docs/` directory

---

## 📝 License

MIT — see [LICENSE](LICENSE).