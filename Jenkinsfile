pipeline {
    agent any

    stages {
        stage('Checkout') {
            steps {
                git branch: 'main',
                    credentialsId: 'github-pat',
                    url: 'https://github.com/buildwithbhakti/satya-cicd.git'
            }
        }
   stage('SonarQube Analysis') {
    steps {
        script {
            def scannerHome = tool 'SonarScanner'

            withSonarQubeEnv('SonarQube') {
                sh """
                ${scannerHome}/bin/sonar-scanner \
                -Dsonar.projectKey=satya-cicd \
                -Dsonar.projectName="Satya CI/CD" \
                -Dsonar.sourceEncoding=UTF-8 \
                -Dsonar.sources=satya-cicd \
                -Dsonar.host.url=http://localhost:9000 \
                -Dsonar.token=sqa_64da1d11df01e905e4fbe7430b965b16a53953c1
                """
            }
        }
    }
}
 } 
}
