pipeline {
  agent any
  environment {
    PROJECT_ID = "${PROJECT_ID}"
    REGION = "${REGION}" 
    IMAGE_TAG = "${GIT_COMMIT}"
  }
  stages {
    stage('Checkout') {
      steps { checkout scm }
    }
    stage('Build & Test') {
      steps {
        sh 'python -m pip install --upgrade pip'
        sh 'pip install -r requirements.txt'
        sh 'pytest -q || true'
      }
    }
    stage('Build Docker Images') {
      steps {
        sh 'docker build -t gcr.io/$PROJECT_ID/tattoo-backend:$IMAGE_TAG -f services/backend/Dockerfile services/backend'
        sh 'docker push gcr.io/$PROJECT_ID/tattoo-backend:$IMAGE_TAG'
        sh 'docker build -t gcr.io/$PROJECT_ID/tattoo-bot:$IMAGE_TAG -f services/bot/Dockerfile services/bot'
        sh 'docker push gcr.io/$PROJECT_ID/tattoo-bot:$IMAGE_TAG'
      }
    }
    stage('Terraform Plan') {
      steps {
        dir('infra/terraform') {
          sh "terraform init"
          sh "terraform plan -var='project_id=${PROJECT_ID}' -var='region=${REGION}' -out=tfplan"
        }
      }
    }
    stage('Terraform Apply') {
      steps {
        dir('infra/terraform') {
          input message: 'Apply Terraform to production?'
          sh "terraform apply -auto-approve -var='project_id=${PROJECT_ID}' -var='region=${REGION}'"
        }
      }
    }
    stage('Deploy') {
      steps {
        sh "gcloud run deploy tattoo-backend --image gcr.io/$PROJECT_ID/tattoo-backend:$IMAGE_TAG --region=$REGION --platform=managed --quiet"
        sh "gcloud run deploy tattoo-bot --image gcr.io/$PROJECT_ID/tattoo-bot:$IMAGE_TAG --region=$REGION --platform=managed --quiet --add-cloudsql-instances=$(terraform output -raw cloud_sql_connection_name)"
      }
    }
  }
}
pipeline {
  agent any
  environment {
    PYTHON = 'python3'
  }
  stages {
    stage('Lint') {
      steps {
        sh 'mkdir -p reports && pip install -r requirements.txt'
        sh 'flake8 --max-line-length=120 || true | tee reports/flake8.txt'
      }
    }
    stage('Unit Tests') {
      steps {
        sh 'pytest -q tests/unit --maxfail=1 --junitxml=reports/unit-junit.xml'
      }
    }
    stage('Integration Tests') {
      steps {
        sh 'pytest -q tests/integration --junitxml=reports/integration-junit.xml || true'
      }
    }
    stage('Security Scans') {
      steps {
        sh '''
        pip install bandit || true
        mkdir -p reports
        bandit -r src -f json -o reports/bandit.json || true
        '''
      }
    }
    stage('E2E Tests') {
      steps {
        sh '''
        if [ -f service_url.txt ]; then export SERVICE_URL=$(cat service_url.txt | cut -d"=" -f2) && echo "Using SERVICE_URL=$SERVICE_URL"; fi
        if [ -d tests/e2e ]; then
          pip install playwright || true
          playwright install || true
          mkdir -p reports/playwright
          pytest -q tests/e2e --maxfail=1 --junitxml=reports/e2e-junit.xml || true
          if [ -d playwright-report ]; then mv playwright-report reports/playwright/ || true; fi
        else
          echo "No e2e tests found"
        fi
        '''
      }
    }
    stage('Performance') {
      steps {
        sh 'echo "Running load tests (k6/locust should run in separate stage)"'
      }
    }
    stage('Publish') {
      steps {
        sh 'echo "Publish artifacts if required"'
      }
    }
    stage('Staging Deploy') {
      steps {
        withCredentials([
          file(credentialsId: 'GCP_SA_JSON', variable: 'GCP_SA_FILE'),
          string(credentialsId: 'TELEGRAM_TOKEN', variable: 'TELEGRAM_TOKEN'),
          string(credentialsId: 'LLM_API_KEY', variable: 'LLM_API_KEY'),
          string(credentialsId: 'GCP_PROJECT_ID', variable: 'GCP_PROJECT_ID')
        ]) {
            sh 'chmod +x scripts/ci_deploy.sh && DRY_RUN=false SCAN=true REPORT_DIR=reports ./scripts/ci_deploy.sh'
        }
      }
    }
    stage('Trivy Scan (Container)') {
      steps {
        withCredentials([file(credentialsId: 'GCP_SA_JSON', variable: 'GCP_SA_FILE'), string(credentialsId: 'GCP_PROJECT_ID', variable: 'GCP_PROJECT_ID')]) {
          sh '''
          export PROJECT_ID=${GCP_PROJECT_ID}
          export SERVICE=${CLOUD_RUN_SERVICE:-inka-bot}
          export IMAGE=${DOCKER_IMAGE:-gcr.io/${PROJECT_ID}/${SERVICE}:latest}
          gcloud auth activate-service-account --key-file="$GCP_SA_FILE"
          gcloud auth configure-docker --quiet
          docker pull "$IMAGE" || true
          mkdir -p reports
          docker run --rm -v /var/run/docker.sock:/var/run/docker.sock -v "${PWD}/reports":/reports aquasec/trivy:latest image --format json -o /reports/trivy.json "$IMAGE" || true
          '''
        }
      }
    }
    stage('Production Approval') {
      steps {
        script {
          input message: 'Approve production deploy?'
        }
      }
    }
    stage('Production Deploy') {
      steps {
        withCredentials([
          file(credentialsId: 'GCP_SA_JSON', variable: 'GCP_SA_FILE'),
          string(credentialsId: 'TELEGRAM_TOKEN', variable: 'TELEGRAM_TOKEN'),
          string(credentialsId: 'LLM_API_KEY', variable: 'LLM_API_KEY'),
          string(credentialsId: 'GCP_PROJECT_ID', variable: 'GCP_PROJECT_ID')
        ]) {
          sh 'chmod +x scripts/ci_deploy.sh && DRY_RUN=false SCAN=true REPORT_DIR=reports ./scripts/ci_deploy.sh'
        }
      }
    }
    stage('Deploy') {
      steps {
        withCredentials([
          file(credentialsId: 'GCP_SA_JSON', variable: 'GCP_SA_FILE'),
          string(credentialsId: 'TELEGRAM_TOKEN', variable: 'TELEGRAM_TOKEN'),
          string(credentialsId: 'LLM_API_KEY', variable: 'LLM_API_KEY'),
          string(credentialsId: 'GCP_PROJECT_ID', variable: 'GCP_PROJECT_ID')
        ]) {
          sh 'chmod +x scripts/ci_deploy.sh && DRY_RUN=${DRY_RUN:-true} ./scripts/ci_deploy.sh'
        }
      }
    }
  }
  post {
    always {
      junit 'reports/**/*.xml'
      archiveArtifacts artifacts: 'reports/**', allowEmptyArchive: true
    }
  }
}
