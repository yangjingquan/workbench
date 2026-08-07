# Workbench server deployment

The Jenkins job `workbench` deploys this repository to `/opt/shop/workbench` as the Docker Compose project `workbench`.

The server environment file is `/opt/shop/workbench/.env`. Jenkins keeps the JWT secret, but synchronizes `MYSQL_ROOT_PASSWORD` from the existing `xp-mysql` container. Workbench uses the existing `workbench` database on `xp-mysql` over the external Docker network `shop_shop-net`; no second MySQL service is created.

Published ports:

- Frontend: `18083`
- API: `18082`
- MySQL: existing `xp-mysql` container on `shop_shop-net`

The existing `nexbyte-site` service on `18081` is not changed.

## Database migration policy

Deployment is schema-only. Jenkins copies application source and deployment
files, then runs `deploy/schema-only.sh`, which applies the DDL in
`backend/sql/init.sql` to the existing `workbench` database.

- No local database directory, Docker volume, SQL dump, or application data is copied to the server.
- The schema script is checked before execution and deployment stops if it contains data-mutating statements such as `INSERT`, `UPDATE`, `DELETE`, `DROP`, or `TRUNCATE`.
- Existing data in `xp-mysql` is preserved. The idempotent `CREATE TABLE IF NOT EXISTS` statements only add missing structure.
- Backend startup may still create the default administrator on a brand-new database and run the existing compatibility migration for old reminder columns; these are server-side bootstrap/upgrade behaviors, not local data import.

If a completely empty server database is needed, create a new database separately and point the server environment at it. The normal deployment intentionally reuses the existing `workbench` database and does not erase or replace its data.

## Jenkins job configuration

The preferred Jenkins setup is a Pipeline job using **Pipeline script from SCM**, pointing at this repository and the `Jenkinsfile` on the selected branch. If the job was created from `deploy/jenkins-workbench-config.xml`, that file contains an inline Pipeline definition and must be re-applied in Jenkins when it changes; Jenkins does not automatically reload an inline script from the repository. The deployment now checks out the selected branch, syncs it to `/opt/shop/workbench`, applies schema only, injects the checked-out commit into the frontend build, and fails verification if the served page does not contain the `accent-themes` build marker.
