def dists = ['jessie', 'stretch', 'buster']

def parallelBuilds = dists.collectEntries { dist ->
  [dist, {
    stage("build-${dist}") {
      sh 'make clean'
      sh "make package_${dist}"
      archiveArtifacts artifacts: "dist_${dist}/*"
    }
  }]
}


pipeline {
  agent {
    label 'slave'
  }

  options {
    ansiColor('xterm')
    timeout(time: 1, unit: 'HOURS')
    timestamps()
  }

  stages {
    stage('check-gh-trust') {
      steps {
        checkGitHubAccess()
      }
    }

    stage('test') {
      environment {
        COVERALLS_REPO_TOKEN = credentials('coveralls_ocflib_token')
      }
      steps {
        sh 'make coveralls'
      }
    }

    stage('push-to-pypi') {
      when {
        branch 'master'
      }
      agent {
        label 'deploy'
      }
      steps {
        sh 'make release-pypi'
      }
    }

    stage('parallel-builds') {
      steps {
        script {
          parallel parallelBuilds
        }
      }
    }

    // Upload packages in series instead of in parallel to avoid a race
    // condition with a lock file on the package repo
    stage('upload-packages') {
      when {
        branch 'master'
      }
      agent {
        label 'deploy'
      }
      steps {
        script {
          for(dist in dists) {
            stage("upload-${dist}") {
              uploadChanges(dist, "dist_${dist}/*.changes")
            }
          }
        }
      }
    }
  }

  post {
    failure {
      emailNotification()
    }
    always {
      node(label: 'slave') {
        ircNotification()
      }
    }
  }
}

// vim: ft=groovy
