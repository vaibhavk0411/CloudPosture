# Phase 5 — Frontend Dashboard

A startup-grade Cloud Security Posture Management UI built with **Vite + React + TypeScript + Tailwind + Recharts**.
Designed to look like a mini AWS Security Hub / Prisma Cloud for live interview demos.

---

## ✨ Features

- **Dashboard Overview** — compliance score ring, KPI cards, trend chart, PASS/FAIL pie
- **EC2 Resources** — sortable / searchable instance table with state badges
- **S3 Buckets** — encryption + public access security badges
- **Security Checks** — CIS results with PASS / FAIL / ERROR filter pills, evidence
- **Scan History** — DynamoDB-backed scans, compliance progression chart
- **Run New Scan** — one-click `POST /scan` with toast notifications + auto-refresh
- Skeleton loaders, error states, mobile responsive, dark theme

---

## 🏗️ Architecture

```
AWS  ──>  FastAPI Backend (Phase 1-4)  ──>  /instances /buckets /cis-results /scan ...
                                       │
                                       ▼
                       Axios client (services/api.ts)
                                       │
                          React Router pages
                                       │
                Tailwind UI + Recharts charts
```

**Why this structure**
- `services/api.ts` is the single source of truth for HTTP — easy to mock, swap base URL
- Pages own their data fetching (small enough app, no global state needed)
- Reusable `DataTable`, `StatCard`, `StatusBadge`, `ScoreRing` keep the UI consistent
- `AppLayout` re-mounts pages after a successful scan via a `key` tick — instant refresh without manual cache logic

---

## 📁 Project Structure

```
frontend/
 ┣ src/
 ┃ ┣ components/
 ┃ ┃ ┣ layout/         # Sidebar, Topbar, AppLayout
 ┃ ┃ ┣ dashboard/      # StatCard, ScoreRing
 ┃ ┃ ┣ tables/         # DataTable (generic)
 ┃ ┃ ┣ charts/         # TrendChart, StatusPie
 ┃ ┃ ┗ ui/             # StatusBadge, Skeleton
 ┃ ┣ pages/
 ┃ ┃ ┣ Dashboard.tsx
 ┃ ┃ ┣ EC2Resources.tsx
 ┃ ┃ ┣ S3Buckets.tsx
 ┃ ┃ ┣ SecurityChecks.tsx
 ┃ ┃ ┗ ScanHistory.tsx
 ┃ ┣ services/api.ts
 ┃ ┣ App.tsx           # Routing + Toaster
 ┃ ┣ main.tsx
 ┃ ┗ index.css         # Tailwind + design tokens
 ┣ tailwind.config.js
 ┣ postcss.config.js
 ┣ .env                # VITE_API_URL=http://localhost:8000
 ┗ package.json
```

---

## 🚀 Run Locally

**1. Start the backend (Phase 1-4)**
```powershell
cd backend
uvicorn main:app --reload
# http://localhost:8000
```

**2. Start the frontend**
```powershell
cd frontend
npm install        # only first time
npm run dev
# http://localhost:5173
```

**3. Open the dashboard** — http://localhost:5173

---

## ⚙️ Configuration

`frontend/.env`:
```
VITE_API_URL=http://localhost:8000
```

Change to any deployed backend URL when needed.

---

## 📦 Production Build

```powershell
npm run build      # outputs dist/
npm run preview    # serves dist/ on localhost:4173
```

Deploy `dist/` to **Vercel**, **Netlify**, **S3 + CloudFront**, or any static host.
Set `VITE_API_URL` at build time to point at your deployed FastAPI backend.

---

## 🎯 Demo Script (60 seconds)

1. **Open `/`** — "This is the executive view: compliance score, KPIs, trend, breakdown."
2. **Click `Run New Scan`** — "Hits `POST /scan`, runs all 11 CIS checks, persists to DynamoDB, refreshes."
3. **Open `Security Checks`** — "Filter by FAIL to surface action items with evidence."
4. **Open `EC2 Resources` / `S3 Buckets`** — "Live AWS discovery via boto3, sortable & searchable."
5. **Open `Scan History`** — "DynamoDB-backed history with a compliance progression chart — the improvement metric is what executives want to see."

---

## 🎨 Design Decisions

| Decision | Why |
|---|---|
| Dark slate + electric blue palette | Cloud-security industry standard (Datadog, Wiz, Prisma) |
| Score ring as hero element | Single-glance compliance status — most-asked KPI |
| Pre-filtered `/failed-checks` endpoint usage | Backend does the work; frontend stays fast |
| Generic `DataTable<T>` | DRY for 4 different resource tables, consistent UX |
| Toast-based scan feedback | Non-blocking; lets demo continue while DynamoDB writes |
| `key`-based remount after scan | Zero-state-management cache invalidation |

---

## 🧪 Stack

- **React 19** + **TypeScript** + **Vite**
- **Tailwind CSS 3** (with custom `brand` / `ink` color tokens)
- **React Router 7**
- **Recharts** (Area + Pie)
- **Axios** for HTTP
- **lucide-react** for icons
- **react-hot-toast** for notifications
