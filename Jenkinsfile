node('slave') {
    step([$class: 'WsCleanup'])

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


if (env.BRANCH_NAME == 'add-jenkinsfile') {
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


node('slave') {
    step([$class: 'WsCleanup'])
    unstash 'src'

    stage('build-deb') {
        dir('src') {
            sh 'make builddeb'
            sh 'mkdir artifacts'
            sh 'mv ../{*.changes,*.deb,*.dsc,*.tar.*} artifacts'
            archiveArtifacts artifacts: 'artifacts/*'
        }
    }

    stash 'src'
}


if (env.BRANCH_NAME == 'add-jenkinsfile') {
    node('deploy') {
        def dists = ['jessie', 'stretch']
        for (def i = 0; i < dists.size(); i++) {
            def dist = dists[i]
            stage name: "upload-${dist}"

            build job: 'upload-changes', parameters: [
                [$class: 'StringParameterValue', name: 'path_to_changes', value: 'artifacts/python-ocflib_*.changes'],
                [$class: 'StringParameterValue', name: 'dist', value: dist],
                [$class: 'StringParameterValue', name: 'job', value: env.JOB_NAME.replace('/', '/job/')],
                [$class: 'StringParameterValue', name: 'job_build_number', value: env.BUILD_NUMBER],
            ]
        }
    }
}

// vim: ft=groovy
