pipeline {
    agent {
        label "python-docker-agent"
    }

    environment {
        PROJECT_KEY = 'siemsalabim'
        SONAR_SERVER_NAME = 'sonarqube-server'
        DOCKER_CREDS_ID = 'ghcr-pat-creds'
    }

    stages {
        stage('Sync') {
            steps {
                sh 'uv sync --frozen'
            }
        }

        stage('Lint and Format') {
            steps {
                sh '''
                    uv run ruff check .
                    uv run ruff format --check .
                '''
            }
        }

        stage('Test') {
            parallel {
                stage('Exporter Tests') {
                    when { changeset "apps/exporter/**" }
                    steps {
                        sh 'COVERAGE_FILE=.coverage.exporter uv run pytest apps/exporter --cov=apps/exporter --cov-report=xml:coverage-exporter.xml'
                    }
                }
                
                stage('Engine Tests') {
                    when { changeset "apps/engine/**" }
                    steps {
                        sh 'COVERAGE_FILE=.coverage.engine uv run pytest apps/engine --cov=apps/engine --cov-report=xml:coverage-engine.xml'
                    }
                }

                stage('Dashboard Tests') {
                    when { changeset "apps/dashboard/**" }
                    steps {
                        sh 'COVERAGE_FILE=.coverage.dashboard uv run pytest apps/dashboard --cov=apps/dashboard --cov-report=xml:coverage-dashboard.xml'
                    }
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                script {
                    scannerHome = tool 'sonarqube-scanner'

                    def rawVersion = readFile('.python-version').trim()
                    env.SONAR_PY_VERSION = rawVersion.tokenize('.')[0..1].join('.')
                }
                withSonarQubeEnv(SONAR_SERVER_NAME) {
                    sh """
                        ${scannerHome}/bin/sonar-scanner \
                        -Dsonar.projectKey=${PROJECT_KEY} \
                        -Dsonar.sources=. \
                        -Dsonar.tests=apps \
                        -Dsonar.test.inclusions=**/tests/** \
                        -Dsonar.exclusions=**/tests/**,**/.venv/**,*.xml \
                        -Dsonar.python.coverage.reportPaths=coverage-engine.xml,coverage-exporter.xml,coverage-dashboard.xml \
                        -Dsonar.python.version=${env.SONAR_PY_VERSION}
                    """
                }
            }
        }

        stage('SonarQube Quality Gate') {
            steps {
                timeout(time: 5, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('App Docker Build') {
            when {
                anyOf {
                    branch 'main'
                    changeRequest()
                }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: env.DOCKER_CREDS_ID, passwordVariable: 'GH_TOKEN', usernameVariable: 'GH_USER')]) {
                    sh '''
                        export REGISTRY_USER="ghcr.io/${GH_USER}"
                        export IMAGE_TAG="v1.0.${BUILD_NUMBER}"

                        docker compose build
                    '''
                }
            }
        }

        stage('App Docker Push') {
            when {
                allOf {
                    branch 'main'
                    not { changeRequest() } 
                }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: env.DOCKER_CREDS_ID, passwordVariable: 'GH_TOKEN', usernameVariable: 'GH_USER')]) {
                    sh '''
                        export DOCKER_CONFIG="${WORKSPACE}/.docker"
                        export REGISTRY_USER="ghcr.io/${GH_USER}"
                        export IMAGE_TAG="v1.0.${BUILD_NUMBER}"

                        echo "$GH_TOKEN" | docker login ghcr.io -u "$GH_USER" --password-stdin
                        
                        docker compose push

                        docker tag "${REGISTRY_USER}/siem-dashboard:${IMAGE_TAG}" "${REGISTRY_USER}/siem-dashboard:latest"
                        docker tag "${REGISTRY_USER}/siem-engine:${IMAGE_TAG}" "${REGISTRY_USER}/siem-engine:latest"
                        
                        docker push "${REGISTRY_USER}/siem-dashboard:latest"
                        docker push "${REGISTRY_USER}/siem-engine:latest"

                        docker logout ghcr.io
                    '''
                }
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}