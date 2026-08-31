# AEGIS Web Frontend

> **🔴 Live**: [aegis-beta-bice.vercel.app](https://aegis-beta-bice.vercel.app)
> Backend: [backend-three-tan-79.vercel.app](https://backend-three-tan-79.vercel.app)

Next.js 16 frontend for the AEGIS clinical intelligence platform.

## Quick Start

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## Build for Production

```bash
npm run build
npm start
```

## Deploy

```bash
vercel --prod
```

Set the backend URL:
```bash
vercel env add BACKEND_URL production
# → https://your-backend.vercel.app
```

## Architecture

```
Browser → Next.js (Vercel) → /api/proxy/* → FastAPI (Vercel Python)
```

When `BACKEND_URL` is set, the frontend proxies API requests to the Python backend. Without it, the built-in mock API routes serve placeholder data.

See [`../DEPLOYMENT.md`](../DEPLOYMENT.md) for full details.

## Tech Stack

- **Next.js 16** with App Router + Turbopack
- **React 19** Server Components
- **TanStack Query** for server state
- **Zustand** for client state
- **Tailwind CSS 4** for styling
- **Recharts** for data visualization
- **shadcn-style** UI primitives

## Scripts

- `npm run dev` — Dev server with hot reload
- `npm run build` — Production build
- `npm start` — Production server
- `npm run lint` — ESLint
- `npm run typecheck` — TypeScript check
- `npm test` — Vitest unit tests