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
                        -Dsonar.projectKey=${PROJECT_KEY} 
                    """
                }
            }
        }

        stage('SonarQube Quality Gate') {
            steps {
                timeout(time: 1, unit: 'HOURS') {
                    waitForQualityGate abortPipeline: true
                }
            }
        }
    }
}