# Workbench HTTP Docker Deployment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task with verification checkpoints.

**Goal:** Deploy Workbench as the `workbench` Docker Compose project with frontend port `18083`, API port `18082`, a persistent MySQL 8.0 database named `workbench`, and Jenkins-driven rollout on `103.47.83.185`.

**Architecture:** Add production Dockerfiles for the FastAPI API and Vite-built Nginx frontend, plus a Compose file that isolates the API and MySQL on a private network while publishing only the required HTTP ports. Add a Jenkinsfile that checks out `main`, builds images, initializes the schema without dropping data, deploys the Compose project, and verifies health endpoints. Add HTTP virtual hosts to the existing server proxy and switch local production frontend builds to `http://wbapi.nexbyte.top`.

**Tech Stack:** Docker Compose, MySQL 8.0, Python FastAPI/Uvicorn, Vue 3/Vite, Nginx, Jenkins Declarative Pipeline, SQLAlchemy.

## Global Constraints

- Preserve the existing `nexbyte-site` service bound to server port `18081`.
- Frontend public port: `18083`; API public port: `18082`.
- Public protocol: HTTP; `workbench.nexbyte.top` and `wbapi.nexbyte.top` resolve to `103.47.83.185`.
- Database name: `workbench`; reuse the existing `xp-mysql` container and its `shop_shop-mysql-data` volume.
- Never commit production passwords or JWT secrets.
- Do not run destructive database commands or remove the persistent volume.

### Task 1: Add production container definitions

**Files:**
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`
- Create: `docker-compose.yml`
- Create: `.dockerignore`

**Interfaces:**
- `workbench-api` exposes container port `8100` and reads `DATABASE_URL`, `JWT_SECRET_KEY`, and `CORS_ORIGINS`.
- `workbench-web` serves the Vite production output on container port `80`.
- `xp-mysql` remains the only MySQL service container; Workbench attaches the API to `shop_shop-net`.

- [ ] Add a Python image that installs `backend/requirements.txt` and runs `uvicorn app.main:app --host 0.0.0.0 --port 8100`.
- [ ] Add a multi-stage Node/Nginx image that builds with `VITE_API_BASE=http://wbapi.nexbyte.top` and serves `dist` with SPA fallback.
- [ ] Connect the API to the external `shop_shop-net` network and the existing `xp-mysql` container.
- [ ] Map `18082:8100` and `18083:80`, without publishing MySQL port 3306.
- [ ] Run `docker compose config` and build both images locally.

### Task 2: Add Jenkins deployment pipeline

**Files:**
- Create: `Jenkinsfile`
- Create: `deploy/.env.example`
- Create: `deploy/README.md`

**Interfaces:**
- Jenkins job name: `workbench`.
- Deployment directory: `/opt/shop/workbench`.
- Compose project name: `workbench`.

- [ ] Validate the branch parameter and clone `https://github.com/yangjingquan/workbench.git`.
- [ ] Copy the checked-out Compose files and server environment into `/opt/shop/workbench` without overwriting an existing secret file.
- [ ] Verify `xp-mysql` health and run `deploy/schema-only.sh` against `workbench`.
- [ ] Confirm the deployment imports no local database volume, dump, or application data.
- [ ] Run `docker compose --project-name workbench up -d --build workbench-api workbench-web`.
- [ ] Verify `http://127.0.0.1:18082/health`, `http://127.0.0.1:18083/`, and Compose container status.

### Task 3: Configure server HTTP reverse proxy and Jenkins job

**Files:**
- Modify remotely: `/opt/jenkins/nginx/...` or the active Nginx configuration mount, using a new `workbench.conf`.
- Modify remotely: Jenkins job configuration to create/update the `workbench` pipeline job.

- [ ] Confirm DNS resolves both domains to `103.47.83.185`.
- [ ] Add `workbench.nexbyte.top` proxying to `host.docker.internal:18083`.
- [ ] Add `wbapi.nexbyte.top` proxying to `host.docker.internal:18082`.
- [ ] Validate Nginx configuration and reload/recreate only the proxy container.
- [ ] Create or update the Jenkins job named `workbench`, pointing it at the repository `https://github.com/yangjingquan/workbench.git` and the `Jenkinsfile`.
- [ ] Trigger one deployment from Jenkins and retain the build log.

### Task 4: Switch local production API endpoint and rebuild client

**Files:**
- Modify: `frontend/.env.desktop`
- Modify: `frontend/.env.example`
- Modify: `README.md`

- [ ] Set desktop/production API base to `http://wbapi.nexbyte.top` while preserving the local development proxy.
- [ ] Build the normal frontend and verify the generated bundle contains the public API host.
- [ ] Run the desktop renderer build.
- [ ] Run the appropriate macOS packaging command and verify the DMG/ZIP output in `desktop/dist/`.

### Task 5: End-to-end verification

- [ ] Check `curl -fsS http://workbench.nexbyte.top/` returns the frontend HTML.
- [ ] Check `curl -fsS http://wbapi.nexbyte.top/health` returns `code: 0`.
- [ ] Log in through the public API using the encrypted-password flow and call `/api/auth/me` with the returned token.
- [ ] Verify the `workbench` database contains the expected tables and that the second migration run is idempotent.
- [ ] Verify `nexbyte-site` remains running on port `18081`.
- [ ] Record any non-fatal build warnings separately from deployment failures.
