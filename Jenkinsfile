pipeline {
    agent {
        label "python-docker-agent"
    }

    environment {
        PROJECT_KEY = 'siemsalabim'
        SONAR_SERVER_NAME = 'sonarqube-server'
    }

    stages {
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
                        -Dsonar.exclusions=**/tests/**,**/.venv/**
                    """
                }
            }
        }

        stage('SonarQube Quality Gate') {
            steps {
                timeout(time: 10, unit: 'MINUTES') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }

        stage('DevOps Docker Build Test') {
            when { changeset "devops/docker/**" }
            steps {
                dir('devops/docker') {
                    sh 'docker compose build'
                }
            }
        }
    }
}