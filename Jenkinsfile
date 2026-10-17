
pipeline {
    agent any

    parameters {
        booleanParam(
            name: 'autoApprove',
            defaultValue: false,
            description: 'Automatically apply the Terraform plan?'
        )
    }

    stages {

        stage('Checkout') {
            steps {
                dir('terraform') {
                    git branch: 'main',
                        url: 'https://github.com/yeshwanthlm/Terraform-Jenkins.git'
                }
            }
        }

        stage('Verify AWS Connection') {
            steps {
                withAWS(
                    credentials: 'aws-jenkins-terraform',
                    region: 'us-east-2'
                ) {
                    sh 'aws sts get-caller-identity'
                }
            }
        }

        stage('Terraform Plan') {
            steps {
                withAWS(
                    credentials: 'aws-jenkins-terraform',
                    region: 'us-east-2'
                ) {
                    dir('terraform') {
                        sh '''
                            terraform init -input=false
                            terraform validate
                            terraform plan -input=false -out=tfplan
                            terraform show -no-color tfplan > tfplan.txt
                        '''
                    }
                }
            }
        }

        stage('Approval') {
            when {
                expression { !params.autoApprove }
            }

            steps {
                script {
                    def plan = readFile('terraform/tfplan.txt')

                    input(
                        message: 'Review the Terraform plan. Apply changes?',
                        ok: 'Apply',
                        parameters: [
                            text(
                                name: 'Plan',
                                defaultValue: plan,
                                description: 'Review the proposed changes'
                            )
                        ]
                    )
                }
            }
        }

        stage('Terraform Apply') {
            steps {
                withAWS(
                    credentials: 'aws-jenkins-terraform',
                    region: 'us-east-2'
                ) {
                    dir('terraform') {
                        sh 'terraform apply -input=false tfplan'
                    }
                }
            }
        }
    }
}
