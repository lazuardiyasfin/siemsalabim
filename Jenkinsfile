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
        stage('Init') {
            steps {
                script {
                    def scannerHome = tool 'sonarqube-scanner'
                    env.SONAR_SCANNER_HOME = scannerHome

                    def rawVersion = readFile('.python-version').trim()
                    env.SONAR_PY_VERSION = rawVersion.tokenize('.')[0..1].join('.')
                }
            }
        }

        stage('Python Checks') {
            stages {
                stage('Sync') {
                    steps {
                        sh 'uv sync --frozen --all-packages --all-extras'
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

                stage('Test Exporter') {
                    when { 
                        anyOf {
                            changeset "apps/exporter/**"
                            expression { currentBuild.number == 1 }
                        }
                    }
                    steps {
                        sh 'COVERAGE_FILE=.coverage.exporter uv run pytest apps/exporter --cov=apps/exporter --cov-report=xml:coverage-exporter.xml'
                    }
                }
                
                stage('Test Engine') {
                    when { 
                        anyOf {
                            changeset "apps/engine/**" 
                            expression { currentBuild.number == 1 }
                        }
                    }
                    steps {
                        sh 'COVERAGE_FILE=.coverage.engine uv run pytest apps/engine --cov=apps/engine --cov-report=xml:coverage-engine.xml'
                    }
                }

                stage('Test Dashboard') {
                    when { 
                        anyOf {
                            changeset "apps/dashboard/**"
                            expression { currentBuild.number == 1 }
                        }
                    }
                    steps {
                        sh 'COVERAGE_FILE=.coverage.dashboard uv run pytest apps/dashboard --cov=apps/dashboard --cov-report=xml:coverage-dashboard.xml'
                    }
                }
            }
        }

        stage('JavaScript Checks') {
            when {
                anyOf {
                    changeset "apps/dashboard/frontend/**"
                    expression { currentBuild.number == 1 }
                }
            }
            stages {
                stage('Sync') {
                    steps {
                        sh '''
                            cd apps/dashboard/frontend
                            npm ci
                        '''
                    }
                }
                stage('Lint') {
                    steps {
                        sh 'cd apps/dashboard/frontend && npm run lint'
                    }
                }
                stage('Test') {
                    steps {
                        sh '''
                            cd apps/dashboard/frontend
                            npx vitest run --coverage.enabled --coverage.reporter=lcov
                        '''
                    }
                }
            }
        }

        stage('SonarQube Analysis') {
            stages {
                stage('Exporter Analysis') {
                    when { anyOf { changeset "apps/exporter/**"; expression { currentBuild.number == 1 } } }
                    steps {
                        withSonarQubeEnv(SONAR_SERVER_NAME) {
                            sh """
                                ${env.SONAR_SCANNER_HOME}/bin/sonar-scanner \
                                -Dsonar.projectKey=siemsalabim:exporter \
                                -Dsonar.projectName="SIEM Exporter" \
                                -Dsonar.sources=apps/exporter \
                                -Dsonar.tests=apps/exporter \
                                -Dsonar.test.inclusions=**/tests/** \
                                -Dsonar.exclusions=**/tests/** \
                                -Dsonar.python.coverage.reportPaths=coverage-exporter.xml \
                                -Dsonar.python.version=${env.SONAR_PY_VERSION}
                            """
                        }
                    }
                }
                stage('Engine Analysis') {
                    when { anyOf { changeset "apps/engine/**"; expression { currentBuild.number == 1 } } }
                    steps {
                        withSonarQubeEnv(SONAR_SERVER_NAME) {
                            sh """
                                ${env.SONAR_SCANNER_HOME}/bin/sonar-scanner \
                                -Dsonar.projectKey=siemsalabim:engine \
                                -Dsonar.projectName="SIEM Engine" \
                                -Dsonar.sources=apps/engine \
                                -Dsonar.tests=apps/engine \
                                -Dsonar.test.inclusions=**/tests/** \
                                -Dsonar.exclusions=**/tests/** \
                                -Dsonar.python.coverage.reportPaths=coverage-engine.xml \
                                -Dsonar.python.version=${env.SONAR_PY_VERSION}
                            """
                        }
                    }
                }
                stage('Dashboard Analysis') {
                    when { anyOf { changeset "apps/dashboard/**"; expression { currentBuild.number == 1 } } }
                    steps {
                        withSonarQubeEnv(SONAR_SERVER_NAME) {
                            sh """
                                ${env.SONAR_SCANNER_HOME}/bin/sonar-scanner \
                                -Dsonar.projectKey=siemsalabim:dashboard \
                                -Dsonar.projectName="SIEM Dashboard" \
                                -Dsonar.sources=apps/dashboard \
                                -Dsonar.tests=apps/dashboard \
                                -Dsonar.test.inclusions=**/testing/** \
                                -Dsonar.exclusions=**/testing/**,**/*.spec.js,**/*.test.js \
                                -Dsonar.python.coverage.reportPaths=coverage-dashboard.xml \
                                -Dsonar.javascript.lcov.reportPaths=apps/dashboard/frontend/coverage/lcov.info \
                                -Dsonar.python.version=${env.SONAR_PY_VERSION} \
                                -Dsonar.coverage.exclusions="\
                                    apps/dashboard/**/assets/**/*,\
                                    apps/dashboard/**/components/**/*,\
                                    apps/dashboard/frontend/src/assets/**/*,\
                                    apps/dashboard/frontend/src/components/**/*,\
                                    apps/dashboard/frontend/src/config/**/*,\
                                    apps/dashboard/frontend/src/main.js,\
                                    apps/dashboard/frontend/src/app/router.js,\
                                    apps/dashboard/frontend/src/app/routes.js,\
                                    apps/dashboard/frontend/src/testing/**/*"
                            """
                        }
                    }
                }
            }
        }

        stage('SonarQube Quality Gate') {
            when {
                anyOf {
                    changeset "apps/exporter/**"
                    changeset "apps/engine/**"
                    changeset "apps/dashboard/**"
                    expression { currentBuild.number == 1 }
                }
            }
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