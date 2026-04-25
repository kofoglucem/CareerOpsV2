# CareerOpsV2

Akıllı LinkedIn iş arama platformu / Smart LinkedIn job search platform.

## Stack
- **Backend**: FastAPI + Celery + PostgreSQL + Redis
- **Browser Automation**: Playwright (Residential IP via Oxylabs)
- **Frontend**: Next.js 14 + TailwindCSS
- **Deploy**: Docker Compose

## Ports (VPS)
| Service | Internal | External |
|---------|----------|----------|
| Backend API | 8000 | 8001 |
| Frontend | 3000 | 3001 |
| PostgreSQL | 5432 | 5433 |
| Redis | 6379 | 6380 |

## Quick Start

```bash
cp backend/.env.example backend/.env
# Edit backend/.env with your credentials
docker compose up -d
```
