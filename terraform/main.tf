terraform {
  required_version = ">= 1.0"

  required_providers {
    digitalocean = {
      source  = "digitalocean/digitalocean"
      version = "~> 2.0"
    }
  }
}

# Configure the DigitalOcean Provider
provider "digitalocean" {
  # Set via DIGITALOCEAN_TOKEN environment variable
  # or pass token = "your_do_token" here
}

# Create a DigitalOcean Functions namespace
resource "digitalocean_app" "docling_functions" {
  spec {
    name   = "docling-converter"
    region = var.region

    # Define the serverless function
    function {
      name = "convert"

      # Source code location
      git {
        repo_clone_url = var.git_repo_url
        branch         = var.git_branch
      }

      # Function configuration
      source_dir = "/"

      # Environment variables
      env {
        key   = "LOG_LEVEL"
        value = var.log_level
      }

      # Routes - the endpoint where function will be accessible
      route {
        path = "/convert"
      }
    }
  }
}

# Output the function URL
output "function_url" {
  description = "The URL of the deployed Docling conversion function"
  value       = digitalocean_app.docling_functions.live_url
}

output "app_id" {
  description = "The ID of the DigitalOcean App"
  value       = digitalocean_app.docling_functions.id
}
