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
          docker run --rm \
            -v "$HOST_WORKSPACE:/source:ro" \
            -v "$DEPLOY_DIR:/target" \
            alpine:3.20 sh -c 'cp -a /source/. /target/'
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
          mysql_password=$(docker inspect xp-mysql --format '{{range .Config.Env}}{{println .}}{{end}}' | sed -n 's/^MYSQL_ROOT_PASSWORD=//p')
          test -n "$mysql_password"
          sed -i "s#^MYSQL_ROOT_PASSWORD=.*#MYSQL_ROOT_PASSWORD=$mysql_password#" "$DEPLOY_DIR/.env"
          unset mysql_password
          set -x
          chmod 600 "$DEPLOY_DIR/.env"
        '''
      }
    }

    stage('Deploy database and migrate') {
      steps {
        sh '''
          set -eu
          cd "$DEPLOY_DIR"
          set +x
          mysql_password=$(docker inspect xp-mysql --format '{{range .Config.Env}}{{println .}}{{end}}' | sed -n 's/^MYSQL_ROOT_PASSWORD=//p')
          test -n "$mysql_password"
          until docker exec xp-mysql sh -c 'mysqladmin ping -h 127.0.0.1 -uroot -p"$1" --silent' sh "$mysql_password"; do
            sleep 3
          done
          docker exec -i xp-mysql sh -c 'mysql -uroot -p"$1" workbench' sh "$mysql_password" < "$DEPLOY_DIR/backend/sql/init.sql"
          unset mysql_password
          set -x
        '''
      }
    }

    stage('Deploy API and frontend') {
      steps {
        sh '''
          set -eu
          cd "$DEPLOY_DIR"
          VITE_BUILD_ID="$WORKBENCH_BUILD_ID" docker compose --project-name workbench up -d --build workbench-api workbench-web
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
          docker compose --project-name workbench ps
          HOST_GATEWAY=$(docker inspect ai-shop-jenkins --format '{{range .NetworkSettings.Networks}}{{.Gateway}}{{end}}' | head -n 1)
          for attempt in $(seq 1 30); do
            if curl -fsS --max-time 5 "http://${HOST_GATEWAY}:18082/health"; then break; fi
            if [ "$attempt" -eq 30 ]; then exit 1; fi
            sleep 2
          done
          BUILD_ID="$WORKBENCH_BUILD_ID"
          FRONTEND_HTML=$(curl -fsS --max-time 20 "http://${HOST_GATEWAY}:18083/")
          printf '%s' "$FRONTEND_HTML" | grep -Fq 'name="workbench-feature" content="accent-themes"'
          printf '%s' "$FRONTEND_HTML" | grep -Fq "name=\"workbench-build\" content=\"$BUILD_ID\""
          if PROXY_RESPONSE=$(curl --noproxy '*' -sS --max-time 20 --resolve "workbench.nexbyte.top:80:${HOST_GATEWAY}" -w '\n__HTTP_STATUS__=%{http_code}' "http://workbench.nexbyte.top/?v=${BUILD_ID}" 2>&1); then
            :
          else
            echo 'Reverse proxy request failed:'
            printf '%s\n' "$PROXY_RESPONSE" | head -c 2000
            exit 1
          fi
          if ! printf '%s' "$PROXY_RESPONSE" | grep -Fq '__HTTP_STATUS__=200' || ! printf '%s' "$PROXY_RESPONSE" | grep -Fq "name=\"workbench-build\" content=\"$BUILD_ID\""; then
            echo 'Reverse proxy returned unexpected Workbench response:'
            printf '%s\n' "$PROXY_RESPONSE" | head -c 2000
            exit 1
          fi
          API_RESPONSE=$(curl --noproxy '*' -sS --max-time 20 --resolve "wbapi.nexbyte.top:80:${HOST_GATEWAY}" -w '\n__HTTP_STATUS__=%{http_code}' "http://wbapi.nexbyte.top/health" 2>&1)
          printf '%s' "$API_RESPONSE" | grep -Fq '__HTTP_STATUS__=200'
          printf '%s' "$API_RESPONSE" | grep -Fq '"code":0'
        '''
      }
    }
  }
}
