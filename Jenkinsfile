pipeline {
    agent {
        label "python-docker-agent"
    }

    environment {
        PROJECT_KEY = 'siemsalabim'
        SONAR_SERVER_NAME = 'sonarqube-server'
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
                        sh 'uv run pytest apps/exporter --cov=apps/exporter --cov-report=xml:coverage-exporter.xml'
                    }
                }
                
                stage('Engine Tests') {
                    when { changeset "apps/engine/**" }
                    steps {
                        sh 'uv run pytest apps/engine --cov=apps/engine --cov-report=xml:coverage-engine.xml'
                    }
                }

                stage('Dashboard Tests') {
                    when { changeset "apps/dashboard/**" }
                    steps {
                        sh 'uv run pytest apps/dashboard --cov=apps/dashboard --cov-report=xml:coverage-dashboard.xml'
                    }
                }
            }
        }

        stage('SonarQube Analysis') {
            steps {
                script {
                    scannerHome = tool 'sonarqube-scanner'
                }
                withSonarQubeEnv(SONAR_SERVER_NAME) {
                    sh """
                        ${scannerHome}/bin/sonar-scanner \
                        -Dsonar.projectKey=${PROJECT_KEY} \
                        -Dsonar.sources=. \
                        -Dsonar.tests=apps \
                        -Dsonar.test.inclusions=**/tests/** \
                        -Dsonar.exclusions=**/tests/**,**/.venv/** \
                        -Dsonar.python.coverage.reportPaths=coverage-engine.xml,coverage-exporter.xml,coverage-dashboard.xml
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
    }
}