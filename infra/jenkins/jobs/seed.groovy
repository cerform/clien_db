// Job DSL seed script to create multibranch pipeline jobs for services
def repoOwner = 'cerform'
def repoName = 'clien_db'
def branchRegex = '^.*$' // all branches

['backend','bot','ai','frontend'].each { service ->
  multibranchPipelineJob("${service}-multibranch") {
    branchSources {
      github {
        id("${service}-repo")
        repoOwner(repoOwner)
        repository(repoName)
        credentialsId('github-token')
        repoUrl("https://github.com/${repoOwner}/${repoName}")
        buildOriginBranch true
      }
    }
    orphanedItemStrategy { discardOldItems { daysToKeep(30); numToKeep(10) } }
  }
}

// Terraform job for infra changes
pipelineJob('terraform') {
  definition {
    cpsScm {
      scm {
        git {
          remote {
            url('https://github.com/cerform/clien_db.git')
            credentials('github-token')
          }
          branches('main')
        }
      }
    }
  }
}
