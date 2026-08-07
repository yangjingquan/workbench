#!/usr/bin/env sh

# Apply database structure only. This script intentionally does not dump,
# copy, restore, seed, or otherwise migrate application data.
set -eu

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
deploy_dir=${DEPLOY_DIR:-$(CDPATH= cd -- "$script_dir/.." && pwd)}
schema_sql="$deploy_dir/backend/sql/init.sql"

if [ ! -f "$schema_sql" ]; then
  echo "Schema script not found: $schema_sql" >&2
  exit 1
fi

# Keep the deployment contract explicit: only DDL statements are accepted.
# The expression is anchored to SQL statement starts so comments and prose do
# not trigger a false positive.
if grep -Eiq '^[[:space:]]*(INSERT|REPLACE|UPDATE|DELETE|TRUNCATE|DROP([[:space:]]|;)|LOAD[[:space:]]+DATA)' "$schema_sql"; then
  echo "Refusing to deploy a schema script containing data-mutating SQL: $schema_sql" >&2
  exit 1
fi

set +x
mysql_password=$(docker inspect xp-mysql --format '{{range .Config.Env}}{{println .}}{{end}}' | sed -n 's/^MYSQL_ROOT_PASSWORD=//p')
test -n "$mysql_password"

until docker exec xp-mysql sh -c 'mysqladmin ping -h 127.0.0.1 -uroot -p"$1" --silent' sh "$mysql_password"; do
  sleep 3
done

docker exec -i xp-mysql sh -c 'mysql -uroot -p"$1" workbench' sh "$mysql_password" < "$schema_sql"
unset mysql_password
set -x
