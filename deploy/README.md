# Workbench server deployment

The Jenkins job `workbench` deploys this repository to `/opt/shop/workbench` as the Docker Compose project `workbench`.

The server environment file is `/opt/shop/workbench/.env`. Jenkins keeps the JWT secret, but synchronizes `MYSQL_ROOT_PASSWORD` from the existing `xp-mysql` container. Workbench uses the existing `workbench` database on `xp-mysql` over the external Docker network `shop_shop-net`; no second MySQL service is created.

Published ports:

- Frontend: `18083`
- API: `18082`
- MySQL: existing `xp-mysql` container on `shop_shop-net`

The existing `nexbyte-site` service on `18081` is not changed.

## Jenkins job configuration

The preferred Jenkins setup is a Pipeline job using **Pipeline script from SCM**, pointing at this repository and the `Jenkinsfile` on the selected branch. If the job was created from `deploy/jenkins-workbench-config.xml`, that file contains an inline Pipeline definition and must be re-applied in Jenkins when it changes; Jenkins does not automatically reload an inline script from the repository. The deployment now checks out the selected branch, syncs it to `/opt/shop/workbench`, injects the checked-out commit into the frontend build, and fails verification if the served page does not contain the `accent-themes` build marker.
