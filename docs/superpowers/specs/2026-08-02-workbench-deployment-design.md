# Workbench HTTP Docker Deployment Design

**Goal:** Deploy the Workbench frontend, FastAPI backend, and MySQL database on the existing server with Jenkins, while preserving the existing service on port `18081`.

## Deployment topology

- `workbench-web`: Nginx static frontend container, published on server port `18083`.
- `workbench-api`: FastAPI container, published on server port `18082` and listening on container port `8100`.
- `xp-mysql`: existing MySQL `8.0` container on the `shop_shop-net` Docker network, containing the `workbench` database and existing business data.
- Existing Nginx reverse proxy routes `workbench.nexbyte.top` to `host.docker.internal:18083` and `wbapi.nexbyte.top` to `host.docker.internal:18082` over HTTP.

The existing `nexbyte-site` container and its `18081` binding remain unchanged. The Workbench service is isolated in a Compose project named `workbench`.

## Configuration and migration

- Production frontend builds use `VITE_API_BASE=http://wbapi.nexbyte.top`.
- Backend uses a server-side environment file containing the MySQL URL, JWT secret, CORS origins, and application port.
- `backend/sql/init.sql` initializes the database and baseline tables during deployment.
- Backend startup also runs the existing SQLAlchemy schema compatibility migration, so upgrades add missing reminder columns without dropping data.
- Database data remains in the existing `shop_shop-mysql-data` volume; deployment does not create or remove a second MySQL volume.

## Jenkins delivery flow

The Jenkins job named `workbench` runs on the server-mounted workspace:

1. Checkout the repository.
2. Build `workbench-api` and `workbench-web` images.
3. Verify `xp-mysql` is healthy and run the idempotent schema script against its `workbench` database.
4. Run the initialization SQL against the `workbench` database.
5. Start/recreate API and web containers.
6. Verify `http://127.0.0.1:18082/health` and `http://127.0.0.1:18083/`.

The deployment uses Docker Compose and the persistent project directory `/opt/shop/workbench`, which is already mounted into the existing Jenkins container. Secrets are supplied through the server environment file and are not committed to the repository.

## HTTP and browser client behavior

The browser frontend calls `http://wbapi.nexbyte.top` directly. The API allows the frontend origin `http://workbench.nexbyte.top` and localhost development origins. External links continue to open in the default browser for the packaged macOS client.

## Verification and rollback

- Validate DNS resolution for both domains before the final smoke test.
- Validate container health, HTTP status, API health response, and database connectivity.
- Validate login and one authenticated API request through the public API domain.
- Keep the prior Compose image tags and database volume intact; a failed rollout can be reverted by restarting the previous image tags without deleting data.
