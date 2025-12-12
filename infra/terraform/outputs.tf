output "cloud_sql_connection_name" {
  value       = google_sql_database_instance.postgres.connection_name
  description = "Cloud SQL connection name in the format project:region:instance"
}

output "backend_url" {
  value       = google_cloud_run_service.backend.status[0].url
  description = "Backend Cloud Run service URL"
}

output "bot_url" {
  value       = google_cloud_run_service.bot.status[0].url
  description = "Bot Cloud Run service URL"
}

output "ai_url" {
  value       = google_cloud_run_service.ai.status[0].url
  description = "AI Cloud Run service URL"
}

output "frontend_url" {
  value       = google_cloud_run_service.frontend.status[0].url
  description = "Frontend Cloud Run service URL"
}
output "cloudsql_connection_name" {
  value = google_sql_database_instance.postgres_instance.connection_name
}

output "cloudrun_url" {
  value = google_cloud_run_service.service.status[0].url
}
