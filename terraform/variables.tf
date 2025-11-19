variable "region" {
  description = "DigitalOcean region for deployment"
  type        = string
  default     = "nyc1"

  validation {
    condition = contains([
      "nyc1", "nyc3", "sfo3", "ams3", "sgp1", "lon1", "fra1", "tor1", "blr1", "syd1"
    ], var.region)
    error_message = "Region must be a valid DigitalOcean region."
  }
}

variable "git_repo_url" {
  description = "Git repository URL containing the function code"
  type        = string
  # Example: "https://github.com/your-username/docling-nest"
}

variable "git_branch" {
  description = "Git branch to deploy from"
  type        = string
  default     = "master"
}

variable "log_level" {
  description = "Logging level for the function"
  type        = string
  default     = "INFO"

  validation {
    condition     = contains(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], var.log_level)
    error_message = "Log level must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL."
  }
}
