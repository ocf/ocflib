try {
    node('slave') {
        step([$class: 'WsCleanup'])
        
        stage('test-command') {
            dir('src') {
                sh 'ls'
            }
        }

        stage('check-out-code') {
            dir('src') {
                checkout scm
            }
        }

        withCredentials([[
            $class: 'StringBinding',
            credentialsId: 'coveralls_token',
            variable: 'COVERALLS_REPO_TOKEN'
        ]]) {
            stage('test') {
                dir('src') {
                    sh 'make coveralls'
                }
            }
        }

        stash 'src'
    }


    if (env.BRANCH_NAME == 'master') {
        node('deploy') {
            step([$class: 'WsCleanup'])
            unstash 'src'

            stage('push-to-pypi') {
                dir('src') {
                    sh 'make release-pypi'
                }
            }
        }
    }


    def dists = ['jessie', 'stretch']
    def branches = [:]

    for (def i = 0; i < dists.size(); i++) {
        def dist = dists[i]
        branches["build-and-deploy-${dist}"] = {
            stage("build-${dist}") {
                node('slave') {
                    step([$class: 'WsCleanup'])
                    unstash 'src'

                    dir('src') {
                        sh 'make clean'
                        sh "make package_${dist}"
                        sh "mv dist dist_${dist}"
                        archiveArtifacts artifacts: "dist_${dist}/*"
                    }

                    stash 'src'
                }
            }

            if (env.BRANCH_NAME == 'master') {
                stage("upload-${dist}") {
                    build job: 'upload-changes', parameters: [
                        [$class: 'StringParameterValue', name: 'path_to_changes', value: "dist_${dist}/*.changes"],
                        [$class: 'StringParameterValue', name: 'dist', value: dist],
                        [$class: 'StringParameterValue', name: 'job', value: env.JOB_NAME.replace('/', '/job/')],
                        [$class: 'StringParameterValue', name: 'job_build_number', value: env.BUILD_NUMBER],
                    ]
                }
            }
        }
    }
    parallel branches

} catch (err) {
    def subject = "${env.JOB_NAME} - Build #${env.BUILD_NUMBER} - Failure!"
    def message = "${env.JOB_NAME} (#${env.BUILD_NUMBER}) failed: ${env.BUILD_URL}"

    if (env.BRANCH_NAME == 'master') {
        slackSend color: '#FF0000', message: message
        mail to: 'root@ocf.berkeley.edu', subject: subject, body: message
    } else {
        mail to: emailextrecipients([
            [$class: 'CulpritsRecipientProvider'],
            [$class: 'DevelopersRecipientProvider']
        ]), subject: subject, body: message
    }

    throw err
}

// vim: ft=groovy
