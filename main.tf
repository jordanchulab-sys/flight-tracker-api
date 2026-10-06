terraform {
  required_providers {
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.20"
    }
  }
}

provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = "docker-desktop"
}

resource "kubernetes_secret" "flight_tracker_secret" {
  metadata {
    name = "flight-tracker-secret"
  }

  data = {
    "api-key" = var.aviationstack_api_key
  }
}

variable "aviationstack_api_key" {
  type      = string
  sensitive = true
  default   = "your_api_key_here"
}

resource "kubernetes_deployment" "flight_tracker_deployment" {
  metadata {
    name = "flight-tracker-deployment"
    labels = {
      app = "flight-tracker"
    }
  }

  spec {
    replicas = 1

    selector {
      match_labels = {
        app = "flight-tracker"
      }
    }

    template {
      metadata {
        labels = {
          app = "flight-tracker"
        }
      }

      spec {
        container {
          image             = "flight-tracker:latest"
          image_pull_policy = "IfNotPresent"
          name              = "flight-tracker"

          env {
            name = "AVIATIONSTACK_API_KEY"
            value_from {
              secret_key_ref {
                name = "flight-tracker-secret"
                key  = "api-key"
              }
            }
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "flight_service" {
  metadata {
    name = "flight-tracker-service"
  }
  spec {
    selector = {
      app = "flight-tracker"
    }
    port {
      port        = 80
      target_port = 80
    }
    type = "ClusterIP"
  }
}