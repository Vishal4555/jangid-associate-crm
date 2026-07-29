# Production deployment

The frontend is built with `VITE_API_URL=/api`.  Consequently, login is sent
to `POST /api/auth/login`, not to the static SPA location.  Nginx proxies that
request to FastAPI as `/api/auth/login`; the backend registers this API
namespace alongside its legacy `/auth` routes.

On the Ubuntu host, ensure the repository is at
`/var/www/jangid-associate-crm`, create `backend/.env` with the production
`DATABASE_URL` and application secrets, then run:

```bash
chmod +x deployment/deploy-ubuntu.sh
deployment/deploy-ubuntu.sh
```

The script rebuilds the frontend, validates and reloads nginx, and restarts
the FastAPI systemd service.  It also retains an `/auth/` nginx proxy solely
so stale browser bundles cannot be routed to the static SPA and receive 405.
