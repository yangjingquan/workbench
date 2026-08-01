# Workbench server deployment

The Jenkins job `workbench` deploys this repository to `/opt/shop/workbench` as the Docker Compose project `workbench`.

The server environment file is `/opt/shop/workbench/.env`. Jenkins keeps the JWT secret, but synchronizes `MYSQL_ROOT_PASSWORD` from the existing `xp-mysql` container. Workbench uses the existing `workbench` database on `xp-mysql` over the external Docker network `shop_shop-net`; no second MySQL service is created.

Published ports:

- Frontend: `18083`
- API: `18082`
- MySQL: existing `xp-mysql` container on `shop_shop-net`

The existing `nexbyte-site` service on `18081` is not changed.
