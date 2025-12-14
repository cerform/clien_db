# Required for main.tf
project = "tattoo-480007"
project_id = "tattoo-480007"
region = "us-central1"
env_prefix = "tattoo"
images = {
  backend  = "gcr.io/tattoo-480007/tattoo-backend:latest"
  bot      = "gcr.io/tattoo-480007/tattoo-bot:latest"
  ai       = "gcr.io/tattoo-480007/tattoo-ai:latest"
  frontend = "gcr.io/tattoo-480007/tattoo-frontend:latest"
}
db_user = "tattoo_user"
db_name = "tattoo_salon"
db_tier = "db-custom-1-3840"
# initial_db_password = "super-secret"   # Preferred: store in Secret Manager
create_secrets_from_vars = false
bot_token = ""
openai_api_key = ""
spreadsheet_id = ""
db_instance_name = "tattoo-db"
db_user_password = "REPLACE_WITH_SECURE_PASSWORD"
service_name = "tattoo-bot"
image = "gcr.io/tattoo-480007/tattoo-bot:latest"
