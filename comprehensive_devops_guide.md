# Comprehensive DevOps & Kubernetes Project Guide: Flight Tracker

This document provides an exhaustive, step-by-step account of building, securing, containerizing, and automating the deployment of the `flight-tracker` application using Python, Docker, Kubernetes, Terraform, and GitHub Actions.

## Table of Contents

1. [Project Vision & Tech Stack](#1-project-vision--tech-stack)
2. [Phase 1: Project Initialization & Directory Structure](#2-phase-1-project-initialization--directory-structure)
3. [Phase 2: Core Application & Dependencies (`lookup_flight.py` & `requirements.txt`)](#3-phase-2-core-application--dependencies)
4. [Phase 3: Containerization via Docker (`Dockerfile` & `.dockerignore`)](#4-phase-3-containerization-via-docker)
5. [Phase 4: Infrastructure as Code with Terraform (`main.tf`)](#5-phase-4-infrastructure-as-code-with-terraform)
6. [Phase 5: Secret Management Strategy](#6-phase-5-secret-management-strategy)
7. [Phase 6: CI/CD Pipeline Automation (`.github/workflows/ci.yml`)](#7-phase-6-cicd-pipeline-automation)
8. [Phase 7: Git Lifecycle & Version Control Hygiene](#8-phase-7-git-lifecycle--version-control-hygiene)
9. [Phase 8: Execution, Verification & Resource Cleanup](#9-phase-8-execution-verification--resource-cleanup)

## 1. Project Vision & Tech Stack

The goal of this project was to transition a local script into a production-grade, reproducible workflow.

* **Application Language**: Python 3.x (integrating with the Aviationstack REST API).
* **Containerization**: Docker (multi-layered build running on slim Python base images).
* **Orchestration**: Kubernetes running locally via Docker Desktop (`docker-desktop` context).
* **Infrastructure as Code (IaC)**: Terraform using the official Kubernetes provider (`hashicorp/kubernetes`).
* **CI/CD Automation**: GitHub Actions.
* **Security Model**: Strict separation of secrets using GitHub Actions Repository Secrets and environment variables, bypassing plaintext hardcoding.

## 2. Phase 1: Project Initialization & Directory Structure

We established a clean repository layout ensuring that case sensitivity for Linux-based runners is respected, and that untracked states, locks, and local build artifacts never pollute version control.

### Final File Tree Layout:

```
NewProjectsVS/
├── .github/
│   └── workflows/
│       └── ci.yml
├── .dockerignore
├── .gitignore
├── Dockerfile
├── main.tf
├── lookup_flight.py
└── requirements.txt
```

## 3. Phase 2: Core Application & Dependencies

### `requirements.txt`
Declares the exact dependencies required by the Python script to communicate with external APIs.

```text
requests>=2.31.0
```

### `lookup_flight.py`
The core Python script that authenticates via environment variables, queries the Aviationstack API for flight data (defaulting to UA123 if unconfigured), and outputs structured telemetry.

```python
import os
import requests

def track_flight():
    api_key = os.getenv("AVIATIONSTACK_API_KEY")
    if not api_key:
        print("Error: AVIATIONSTACK_API_KEY environment variable not set.")
        exit(1)

    flight_id = os.getenv("FLIGHT_NUMBER", "UA123")
    print(f"Searching Aviationstack for flight {flight_id}...")

    url = f"http://api.aviationstack.com/v1/flights?access_key={api_key}&flight_iata={flight_id}"
    
    try:
        response = requests.get(url)
        if response.status_code == 401:
            print("An error occurred: HTTP Error 401: Unauthorized")
            exit(1)
        
        response.raise_for_status()
        data = response.json()
        print("API Response successfully retrieved:")
        print(data)
    except Exception as e:
        print(f"An error occurred while fetching flight data: {e}")
        exit(1)

if __name__ == "__main__":
    track_flight()
```

## 4. Phase 3: Containerization via Docker

### `.dockerignore`
Prevents local state files, Git history, and virtual environments from leaking into the Docker build context.

```text
.git
.gitignore
.terraform
*.tfstate
*.tfstate.backup
.terraform.lock.hcl
__pycache__
*.pyc
```

### `Dockerfile`
A secure, lightweight container blueprint. It pulls a clean Python runtime, copies dependencies, installs them, and sets up the entrypoint execution.

```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY lookup_flight.py .

ENV FLIGHT_NUMBER=UA123

CMD ["python", "lookup_flight.py"]
```

## 5. Phase 4: Infrastructure as Code with Terraform (`main.tf`)

Terraform manages our Kubernetes deployment, ensuring that configuration is declarative and reproducible. It reads the API key securely from a Kubernetes `Secret` injected into the pod environment using correct lowercase naming conventions for cross-platform compatibility.

```hcl
terraform {
  required_version = ">= 1.0.0"
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

variable "aviationstack_api_key" {
  type      = string
  sensitive = true
}

resource "kubernetes_secret" "flight_secret" {
  metadata {
    name = "flight-tracker-secret"
  }

  data = {
    AVIATIONSTACK_API_KEY = var.aviationstack_api_key
  }
}

resource "kubernetes_deployment" "flight_tracker" {
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
          image = "flight-tracker:latest"
          name  = "flight-tracker"
          image_pull_policy = "Never" # Uses local Docker Desktop images

          env {
            name = "AVIATIONSTACK_API_KEY"
            value_from {
              secret_key_ref {
                name = kubernetes_secret.flight_secret.metadata[0].name
                key  = "AVIATIONSTACK_API_KEY"
              }
            }
          }
        }
      }
    }
  }
}
```

## 6. Phase 5: Secret Management Strategy

To ensure zero plaintext leakage of credentials:

1. **Local Development**: We inject secrets into Terraform dynamically via PowerShell session environment variables:
   ```powershell
   $env:TF_VAR_aviationstack_api_key="your_actual_api_key_here"
   ```
2. **CI/CD Pipelines**: Secrets are securely stored inside GitHub Repository Settings (`Settings > Secrets and variables > Actions`) under the name `AVIATIONSTACK_API_KEY` and mapped at runtime.
3. **Ignore Rules (`.gitignore`)**: Explicitly blocks state files and lock files:
   ```text
   .terraform/
   *.tfstate
   *.tfstate.*
   .terraform.lock.hcl
   ```

## 7. Phase 6: CI/CD Pipeline Automation (`.github/workflows/ci.yml`)

The GitHub Actions workflow automates dependency checks, injects production secrets safely, runs Python tests, and validates Docker image builds on every push to `main`.

```yaml
name: CI Pipeline

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

jobs:
  build-and-test:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: 'pip'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

      - name: Run Flight Tracker with Secret
        env:
          AVIATIONSTACK_API_KEY: ${{ secrets.AVIATIONSTACK_API_KEY }}
        run: |
          python lookup_flight.py

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build Docker Image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: false
          tags: flight-tracker:latest
          load: true
```

## 8. Phase 7: Git Lifecycle & Version Control Hygiene

We managed git staging cleanly with proper case hygiene for cross-platform runner compatibility:

```powershell
# Check git status
git status

# Stage and commit configuration updates
git add .gitignore main.tf .github/workflows/ci.yml Dockerfile lookup_flight.py requirements.txt
git commit -m "Establish production-grade DevOps structure, Terraform config, and CI workflow"
git push origin main
```

## 9. Phase 8: Execution, Verification & Resource Cleanup

### Step A: Deploy Infrastructure via Terraform
```powershell
$env:TF_VAR_aviationstack_api_key="eec3f2ed888082c586e293bcbf8de589"
terraform apply -auto-approve
```

### Step B: Verify Kubernetes Pod Execution
```powershell
kubectl get pods
```
*(Pods transition to `Completed` once the single-run data script exits successfully).*

### Step C: Inspect Application Logs
```powershell
kubectl logs deployment/flight-tracker-deployment
```

### Step D: Clean Up Local Cluster Resources (When Idle)
To preserve local machine resources while keeping all source code safe in Git:
```powershell
terraform destroy -auto-approve
```

To spin it back up later:
```powershell
terraform apply -auto-approve
kubectl rollout restart deployment/flight-tracker-deployment