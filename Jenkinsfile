def dists = ['jessie', 'stretch', 'buster']

def parallelStagesMap = dists.collectEntries {
  ["${it}" : generateStage(it)]
}

def generateStage(dist) {
  return {
    stage("build-${dist}") {
      sh 'make clean'
      sh "make package_${dist}"
      archiveArtifacts artifacts: "dist_${dist}/*"
    }

    if (env.BRANCH_NAME == 'master') {
      node('deploy') {
        stage("upload-${dist}") {
          uploadChanges(dist, "dist_${dist}/*.changes")
        }
      }
    }
  }
}

pipeline {
  agent {
    label 'slave'
  }

  options {
    ansiColor('xterm')
    timeout(time: 1, unit: 'HOURS')
  }

  stages {
    stage('test') {
      environment {
        COVERALLS_REPO_TOKEN = credentials('coveralls_token')
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
          parallel parallelStagesMap
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
