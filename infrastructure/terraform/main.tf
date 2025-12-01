provider "google" {
  project = var.project_id
  region  = var.region
}

# 1. Enable Cloud Run API automatically
resource "google_project_service" "run_api" {
  service = "run.googleapis.com"
  disable_on_destroy = false
}

# 2. Deploy the Container to Cloud Run
resource "google_cloud_run_service" "sentinell_backend" {
  name     = "sentinell-backend"
  location = var.region

  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/sentinell-backend:v1"
        
        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }
        env {
          name  = "GOOGLE_CLOUD_REGION"
          value = var.region
        }
        # Note: In production, use Secret Manager for keys
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }

  depends_on = [google_project_service.run_api]
}

# 3. Allow Public Access (So your Frontend can reach it)
data "google_iam_policy" "noauth" {
  binding {
    role = "roles/run.invoker"
    members = ["allUsers"]
  }
}

resource "google_cloud_run_service_iam_policy" "noauth" {
  location    = google_cloud_run_service.sentinell_backend.location
  project     = google_cloud_run_service.sentinell_backend.project
  service     = google_cloud_run_service.sentinell_backend.name
  policy_data = data.google_iam_policy.noauth.policy_data
}

output "url" {
  value = google_cloud_run_service.sentinell_backend.status[0].url
}