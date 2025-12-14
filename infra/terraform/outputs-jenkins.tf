output "jenkins_url" {
  value = kubernetes_service_account.jenkins_ksa.metadata[0].annotations["iam.gke.io/gcp-service-account"]
  description = "GCP service account annotated to Jenkins KSA (Workload Identity binding)"
}
