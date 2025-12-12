variable "jenkins_cluster_name" {
  description = "GKE cluster name for Jenkins"
  type = string
  default = "tattoo-jenkins-cluster"
}

variable "jenkins_node_count" {
  description = "Number of nodes for Jenkins cluster"
  type = number
  default = 2
}

resource "google_container_cluster" "jenkins_cluster" {
  name     = var.jenkins_cluster_name
  location = var.region
  remove_default_node_pool = true
  initial_node_count = 1
  ip_allocation_policy {}
}

resource "google_container_node_pool" "jenkins_pool" {
  name       = "jenkins-pool"
  location   = var.region
  cluster    = google_container_cluster.jenkins_cluster.name
  node_count = var.jenkins_node_count
  node_config {
    machine_type = "e2-standard-2"
    oauth_scopes = [
      "https://www.googleapis.com/auth/cloud-platform"
    ]
  }
}

# Kubernetes provider config (use local exec to get creds)
data "google_client_config" "default" {}

resource "null_resource" "k8s_creds" {
  provisioner "local-exec" {
    command = "gcloud container clusters get-credentials ${google_container_cluster.jenkins_cluster.name} --region ${var.region} --project ${var.project_id}"
  }
}

provider "kubernetes" {
  host = google_container_cluster.jenkins_cluster.endpoint
  cluster_ca_certificate = base64decode(google_container_cluster.jenkins_cluster.master_auth[0].cluster_ca_certificate)
  token = data.google_client_config.default.access_token
  load_config_file = false
}

provider "helm" {
  kubernetes {
    host                   = google_container_cluster.jenkins_cluster.endpoint
    cluster_ca_certificate = base64decode(google_container_cluster.jenkins_cluster.master_auth[0].cluster_ca_certificate)
    token                  = data.google_client_config.default.access_token
    load_config_file       = false
  }
}

resource "google_service_account" "jenkins_gsa" {
  account_id   = "${var.env_prefix}-jenkins-sa"
  display_name = "Jenkins GSA"
}

resource "google_service_account_iam_member" "jenkins_workload_identity" {
  service_account_id = google_service_account.jenkins_gsa.name
  role               = "roles/iam.workloadIdentityUser"
  member             = "serviceAccount:${var.project_id}.svc.id.goog[jenkins/jenkins]"
}

resource "google_project_iam_member" "jenkins_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.jenkins_gsa.email}"
}

resource "google_project_iam_member" "jenkins_run_admin" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${google_service_account.jenkins_gsa.email}"
}

resource "google_project_iam_member" "jenkins_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${google_service_account.jenkins_gsa.email}"
}

resource "google_project_iam_member" "jenkins_cloudsql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.jenkins_gsa.email}"
}

resource "kubernetes_namespace" "jenkins_ns" {
  metadata {
    name = "jenkins"
  }
  depends_on = [null_resource.k8s_creds]
}

resource "kubernetes_service_account" "jenkins_ksa" {
  metadata {
    name      = "jenkins"
    namespace = kubernetes_namespace.jenkins_ns.metadata[0].name
    annotations = {
      "iam.gke.io/gcp-service-account" = google_service_account.jenkins_gsa.email
    }
  }
  depends_on = [null_resource.k8s_creds]
}

# Create a Kubernetes secret for GitHub token (optional, can also be loaded by plugin)
resource "kubernetes_secret" "github_token" {
  metadata {
    name      = "github-token"
    namespace = kubernetes_namespace.jenkins_ns.metadata[0].name
  }
  data = {
    token = base64encode(var.github_token != "" ? var.github_token : "")
  }
  type = "Opaque"
  depends_on = [kubernetes_service_account.jenkins_ksa]
}

resource "kubernetes_secret" "github_oauth" {
  count = var.jenkins_github_oauth_client_id != "" && var.jenkins_github_oauth_client_secret != "" ? 1 : 0
  metadata {
    name      = "github-oauth"
    namespace = kubernetes_namespace.jenkins_ns.metadata[0].name
  }
  data = {
    client_id     = base64encode(var.jenkins_github_oauth_client_id)
    client_secret = base64encode(var.jenkins_github_oauth_client_secret)
  }
  type = "Opaque"
  depends_on = [kubernetes_service_account.jenkins_ksa]
}

resource "helm_release" "jenkins" {
  name       = "jenkins"
  repository = "https://charts.jenkins.io"
  chart      = "jenkins"
  namespace  = kubernetes_namespace.jenkins_ns.metadata[0].name
  values = [
    <<EOF
controller:
  serviceAccount:
    create: false
    name: ${kubernetes_service_account.jenkins_ksa.metadata[0].name}
  adminUser: ""
  adminPassword: ""
  serviceType: LoadBalancer
  resources:
    requests:
      cpu: "500m"
      memory: "1Gi"
  jenkinsConfigScripts:
    seed.groovy: |
$(file("infra/jenkins/jobs/seed.groovy"))
  JCasC:
    config: |
$(file("infra/jenkins/jcasc.yaml"))
  installPlugins:
    - git
    - workflow-aggregator
    - workflow-job
    - pipeline-stage-view
    - credentials
    - cloudbees-folder
    - workflow-multibranch
    - github-branch-source
    - kubernetes
    - job-dsl
    - configuration-as-code
    - google-oauth-plugin
    - google-login
    - gcp-credentials-provider
    - pipeline-github-lib
    - matrix-auth
    - promoted-builds
    - blueocean
    - github-oauth
  env:
    - name: GITHUB_CLIENT_ID
      valueFrom:
        secretKeyRef:
          name: github-oauth
          key: client_id
    - name: GITHUB_CLIENT_SECRET
      valueFrom:
        secretKeyRef:
          name: github-oauth
          key: client_secret
persistence:
  enabled: true
  size: 10Gi
EOF
  ]
}
