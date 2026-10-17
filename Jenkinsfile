pipeline {
    agent any

    parameters {
        booleanParam(
            name: 'autoApprove',
            defaultValue: false,
            description: 'Automatically run apply after generating plan?'
        )
    }

    environment {
        AWS_DEFAULT_REGION = 'us-east-2'
        TF_IN_AUTOMATION = 'true'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Verify AWS Credentials') {
            steps {
                withAWS(
                    credentials: 'aws-jenkins-terraform',
                    region: 'us-east-2'
                ) {
                    sh 'aws sts get-caller-identity'
                }
            }
        }

        stage('Plan') {
            steps {
                withAWS(
                    credentials: 'aws-jenkins-terraform',
                    region: 'us-east-2'
                ) {
                    sh '''
                        terraform init -input=false
                        terraform validate
                        terraform plan -input=false -out=tfplan
                        terraform show -no-color tfplan > tfplan.txt
                    '''
                }
            }
        }

        stage('Approval') {
            when {
                expression {
                    !params.autoApprove
                }
            }

            steps {
                script {
                    def plan = readFile('tfplan.txt')

                    input(
                        message: 'Do you want to apply the Terraform plan?',
                        ok: 'Apply',
                        parameters: [
                            text(
                                name: 'Plan',
                                description: 'Review the Terraform plan',
                                defaultValue: plan
                            )
                        ]
                    )
                }
            }
        }

        stage('Apply') {
            steps {
                withAWS(
                    credentials: 'aws-jenkins-terraform',
                    region: 'us-east-2'
                ) {
                    sh 'terraform apply -input=false tfplan'
                }
            }
        }
    }
}
