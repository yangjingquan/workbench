pipeline {
  agent any

  options {
    disableConcurrentBuilds()
    timeout(time: 45, unit: 'MINUTES')
  }

  parameters {
    string(name: 'BRANCH', defaultValue: 'main', description: '要部署的 Git 分支')
  }

  environment {
    DEPLOY_DIR = '/opt/shop/workbench'
    HOST_WORKSPACE = '/opt/jenkins/jenkins_home/workspace/workbench'
  }

  stages {
    stage('Validate') {
      steps {
        script {
          if (!params.BRANCH?.trim()) {
            error('BRANCH 不能为空')
          }
          if (params.BRANCH.contains('..') || params.BRANCH.contains(' ') || params.BRANCH.startsWith('/') || params.BRANCH.endsWith('/')) {
            error("非法分支名：${params.BRANCH}")
          }
        }
      }
    }

    stage('Checkout') {
      steps {
        deleteDir()
        sh '''
          set -eu
          git clone --depth 1 --single-branch --branch "$BRANCH" https://gh-proxy.com/https://github.com/yangjingquan/workbench.git .
        '''
        script {
          env.WORKBENCH_BUILD_ID = sh(script: 'git rev-parse --short HEAD', returnStdout: true).trim()
          echo "Deploying Workbench commit ${env.WORKBENCH_BUILD_ID}"
        }
      }
    }

    stage('Sync deployment files') {
      steps {
        sh '''
          set -eu
          test -f "$HOST_WORKSPACE/docker-compose.yml"
          test -f "$HOST_WORKSPACE/docker-manager/Dockerfile"
          grep -Fq '  docker-manager:' "$HOST_WORKSPACE/docker-compose.yml"
          source_build_id=$(git -C "$HOST_WORKSPACE" rev-parse --short HEAD)
          test "$source_build_id" = "$WORKBENCH_BUILD_ID"
          docker run --rm \
            -v "$HOST_WORKSPACE:/source:ro" \
            -v "$DEPLOY_DIR:/target" \
            alpine:3.20 sh -c 'cp -a /source/. /target/'
          test -f "$DEPLOY_DIR/docker-compose.yml"
          test -f "$DEPLOY_DIR/docker-manager/Dockerfile"
          grep -Fq '  docker-manager:' "$DEPLOY_DIR/docker-compose.yml"
          target_build_id=$(git -C "$DEPLOY_DIR" rev-parse --short HEAD)
          test "$target_build_id" = "$WORKBENCH_BUILD_ID"
          if [ ! -f "$DEPLOY_DIR/.env" ]; then
            set +x
            umask 077
            mysql_password=$(docker inspect xp-mysql --format '{{range .Config.Env}}{{println .}}{{end}}' | sed -n 's/^MYSQL_ROOT_PASSWORD=//p')
            test -n "$mysql_password"
            jwt_secret=$(openssl rand -hex 48)
            {
              printf '%s\n' 'MYSQL_DATABASE=workbench'
              printf 'MYSQL_ROOT_PASSWORD=%s\n' "$mysql_password"
              printf 'JWT_SECRET_KEY=%s\n' "$jwt_secret"
              printf '%s\n' 'ACCESS_TOKEN_EXPIRE_MINUTES=1440'
              printf '%s\n' 'CORS_ORIGINS=http://workbench.nexbyte.top,http://localhost:5173,http://localhost:5174,null'
              printf '%s\n' 'VITE_API_BASE=http://wbapi.nexbyte.top'
            } > "$DEPLOY_DIR/.env"
            unset mysql_password jwt_secret
            set -x
          fi
          set +x
          ensure_env_value() {
            env_key="$1"
            env_value="$2"
            if grep -q "^${env_key}=" "$DEPLOY_DIR/.env"; then
              sed -i "s#^${env_key}=.*#${env_key}=${env_value}#" "$DEPLOY_DIR/.env"
            else
              printf '%s=%s\n' "$env_key" "$env_value" >> "$DEPLOY_DIR/.env"
            fi
          }
          docker_manager_token=$(sed -n 's/^DOCKER_MANAGER_TOKEN=//p' "$DEPLOY_DIR/.env" | tail -n 1)
          if [ -z "$docker_manager_token" ]; then
            docker_manager_token=$(openssl rand -hex 32)
          fi
          ensure_env_value 'DOCKER_MANAGER_TOKEN' "$docker_manager_token"
          ensure_env_value 'DOCKER_MANAGER_URL' 'http://docker-manager:9100'
          ensure_env_value 'DOCKER_PROTECTED_CONTAINERS' 'workbench-api,workbench-web,docker-manager,xp-mysql'
          unset docker_manager_token
          mysql_password=$(docker inspect xp-mysql --format '{{range .Config.Env}}{{println .}}{{end}}' | sed -n 's/^MYSQL_ROOT_PASSWORD=//p')
          test -n "$mysql_password"
          sed -i "s#^MYSQL_ROOT_PASSWORD=.*#MYSQL_ROOT_PASSWORD=$mysql_password#" "$DEPLOY_DIR/.env"
          unset mysql_password
          set -x
          chmod 600 "$DEPLOY_DIR/.env"
        '''
      }
    }

    stage('Deploy database schema only') {
      steps {
        sh '''
          set -eu
          sh "$DEPLOY_DIR/deploy/schema-only.sh"
        '''
      }
    }

    stage('Deploy API and frontend') {
      steps {
        sh '''
          set -eu
          cd "$DEPLOY_DIR"
          VITE_BUILD_ID="$WORKBENCH_BUILD_ID" docker compose --project-name workbench up -d --build docker-manager workbench-api workbench-web
          if docker ps -a --format '{{.Names}}' | grep -qx workbench-db; then docker rm -f workbench-db; fi
        '''
      }
    }

    stage('Configure HTTP proxy') {
      steps {
        sh '''
          set -eu
          docker run --rm \
            -v /opt/jenkins/nginx/conf.d:/target \
            -v "$HOST_WORKSPACE/deploy/nginx/workbench.conf:/source/workbench.conf:ro" \
            alpine:3.20 sh -c 'cp /source/workbench.conf /target/workbench.conf'
          docker exec ai-shop-jenkins-proxy nginx -t
          docker exec ai-shop-jenkins-proxy nginx -s reload
        '''
      }
    }

    stage('Verify') {
      steps {
        sh '''
          set -eu
          cd "$DEPLOY_DIR"
          docker compose --project-name workbench config --services | grep -qx 'docker-manager'
          docker compose --project-name workbench ps
          for attempt in $(seq 1 30); do
            agent_health=$(docker inspect docker-manager --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}')
            if [ "$agent_health" = 'healthy' ]; then break; fi
            if [ "$attempt" -eq 30 ]; then
              docker inspect docker-manager --format 'docker-manager health: {{.State.Status}}/{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}'
              exit 1
            fi
            sleep 2
          done
          test "$(docker inspect docker-manager --format '{{.State.Status}}')" = 'running'
          docker inspect docker-manager --format '{{range .Mounts}}{{println .Source .Destination}}{{end}}' | grep -Fq '/var/run/docker.sock /var/run/docker.sock'
          docker exec workbench-api python -c 'import os, urllib.request; request = urllib.request.Request("http://docker-manager:9100/internal/v1/overview", headers={"X-Docker-Manager-Token": os.environ["DOCKER_MANAGER_TOKEN"]}); response = urllib.request.urlopen(request, timeout=10); assert response.status == 200; print("API to docker-manager check passed")'
          HOST_GATEWAY=$(docker inspect ai-shop-jenkins --format '{{range .NetworkSettings.Networks}}{{.Gateway}}{{end}}' | head -n 1)
          for attempt in $(seq 1 30); do
            if curl -fsS --max-time 5 "http://${HOST_GATEWAY}:18082/health"; then break; fi
            if [ "$attempt" -eq 30 ]; then exit 1; fi
            sleep 2
          done
          BUILD_ID="$WORKBENCH_BUILD_ID"
          FRONTEND_HTML=$(curl -fsS --max-time 20 "http://${HOST_GATEWAY}:18083/")
          check_contains() {
            check_name="$1"
            check_value="$2"
            check_body="$3"
            if ! printf '%s' "$check_body" | grep -Fq "$check_value"; then
              echo "Check failed: $check_name"
              echo "Expected: $check_value"
              printf '%s\n' "$check_body" | head -c 2000
              exit 1
            fi
            echo "Check passed: $check_name"
          }
          check_contains 'direct frontend feature marker' 'name="workbench-feature" content="accent-themes"' "$FRONTEND_HTML"
          BUILD_MARKER=$(printf 'name="workbench-build" content="%s"' "$BUILD_ID")
          check_contains 'direct frontend build marker' "$BUILD_MARKER" "$FRONTEND_HTML"
          if PROXY_RESPONSE=$(curl --noproxy '*' -sS --max-time 20 --resolve "workbench.nexbyte.top:80:${HOST_GATEWAY}" -w '\n__HTTP_STATUS__=%{http_code}' "http://workbench.nexbyte.top/?v=${BUILD_ID}" 2>&1); then
            :
          else
            echo 'Reverse proxy request failed:'
            printf '%s\n' "$PROXY_RESPONSE" | head -c 2000
            exit 1
          fi
          check_contains 'frontend proxy HTTP status' '__HTTP_STATUS__=200' "$PROXY_RESPONSE"
          check_contains 'frontend proxy build marker' "$BUILD_MARKER" "$PROXY_RESPONSE"
          if API_RESPONSE=$(curl --noproxy '*' -sS --max-time 20 --resolve "wbapi.nexbyte.top:80:${HOST_GATEWAY}" -w '\n__HTTP_STATUS__=%{http_code}' "http://wbapi.nexbyte.top/health" 2>&1); then
            :
          else
            echo 'API reverse proxy request failed:'
            printf '%s\n' "$API_RESPONSE" | head -c 2000
            exit 1
          fi
          check_contains 'API proxy HTTP status' '__HTTP_STATUS__=200' "$API_RESPONSE"
          check_contains 'API proxy health payload' '"code":0' "$API_RESPONSE"
        '''
      }
    }
  }
}
