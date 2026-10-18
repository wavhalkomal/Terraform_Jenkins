pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        skipDefaultCheckout(true)
        timestamps()
        timeout(time: 45, unit: 'MINUTES')
    }

    // Requires Jenkins GitHub plugin and a reachable /github-webhook/ endpoint.
    // For localhost-only Jenkins, use Poll SCM until a secure webhook endpoint exists.
    triggers {
        githubPush()
    }

    environment {
        AWS_DEFAULT_REGION = 'us-east-1'
        AWS_REGION         = 'us-east-1'
        TF_IN_AUTOMATION   = 'true'
        TF_INPUT           = 'false'
        EXPECTED_TYPE      = 't2.micro'
        EXPECTED_NAME      = 'TF-Instance'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Static Checks') {
            steps {
                sh '''
                    set -eu
                    terraform fmt -check -recursive
                    bash -n post_deployment_check.sh
                    python3 -m unittest discover -s tests -v
                '''
            }
        }

        stage('Terraform Validate') {
            steps {
                sh '''
                    set -eu
                    terraform init -input=false -lockfile=readonly
                    terraform validate -no-color
                '''
            }
        }

        stage('Verify AWS Identity') {
            steps {
                withAWS(credentials: 'aws-jenkins-terraform', region: 'us-east-1') {
                    sh 'aws sts get-caller-identity'
                }
            }
        }

        stage('Terraform Plan') {
            steps {
                withAWS(credentials: 'aws-jenkins-terraform', region: 'us-east-1') {
                    sh '''
                        set -eu
                        terraform plan -input=false -no-color -out=tfplan
                        terraform show -no-color tfplan > tfplan.txt
                        cat tfplan.txt
                    '''
                }
            }
        }

        stage('Manual Approval') {
            steps {
                input message: 'Review the Terraform plan in Console Output. Apply to AWS?',
                      ok: 'Approve Terraform Apply',
                      submitter: 'kwavhal'
            }
        }

        stage('Terraform Apply') {
            steps {
                withAWS(credentials: 'aws-jenkins-terraform', region: 'us-east-1') {
                    sh 'terraform apply -input=false -no-color tfplan'
                }
            }
        }

        stage('Post-Deployment Verification') {
            steps {
                withAWS(credentials: 'aws-jenkins-terraform', region: 'us-east-1') {
                    sh '''
                        set -eu
                        INSTANCE_ID="$(terraform output -raw instance_id)"
                        bash post_deployment_check.sh "$INSTANCE_ID"
                    '''
                }
            }
        }
    }

    post {
        success { echo 'SUCCESS: Terraform deployment and EC2 post-checks passed.' }
        failure { echo 'FAILURE: Review the failing stage. Resources may still exist in AWS.' }
        aborted { echo 'ABORTED: Deployment was not approved or the pipeline was interrupted.' }
        always  { echo 'Pipeline finished. Inspect stage logs for verification details.' }
    }
}
