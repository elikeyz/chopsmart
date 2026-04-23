terraform {
  required_version = ">= 1.5"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Using local backend - state will be stored in terraform.tfstate in this directory
  # This is automatically gitignored for security
}

provider "aws" {
  region = var.aws_region
}

# Data source for current caller identity
data "aws_caller_identity" "current" {}

# ========================================
# ECR Repository
# ========================================

resource "aws_ecr_repository" "chopsmart-api" {
  name                 = "chopsmart-api"
  image_tag_mutability = "MUTABLE"
  force_delete         = true  # Allow deletion even with images

  image_scanning_configuration {
    scan_on_push = false
  }

  tags = {
    Project = "chopsmart"
    Part    = "backend"
  }
}

# ========================================
# App Runner Service
# ========================================

# IAM role for App Runner
resource "aws_iam_role" "app_runner_role" {
  name = "chopsmart-app-runner-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "build.apprunner.amazonaws.com"
        }
      },
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "tasks.apprunner.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Project = "chopsmart"
    Part    = "backend"
  }
}

# Policy for App Runner to access ECR
resource "aws_iam_role_policy_attachment" "app_runner_ecr_access" {
  role       = aws_iam_role.app_runner_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

# IAM role for App Runner instance (runtime access to AWS services)
resource "aws_iam_role" "app_runner_instance_role" {
  name = "chopsmart-app-runner-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "tasks.apprunner.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Project = "chopsmart"
    Part    = "backend"
  }
}

# Policy for App Runner instance to access Bedrock
resource "aws_iam_role_policy" "app_runner_instance_bedrock_access" {
  name = "chopsmart-app-runner-instance-bedrock-policy"
  role = aws_iam_role.app_runner_instance_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:ListFoundationModels"
        ]
        Resource = "*"
      }
    ]
  })
}

# App Runner service
resource "aws_apprunner_service" "chopsmart-api" {
  service_name = "chopsmart-api"

  source_configuration {
    auto_deployments_enabled = false

    # Configure authentication for private ECR repository
    authentication_configuration {
      access_role_arn = aws_iam_role.app_runner_role.arn
    }

    image_repository {
      image_identifier      = "${aws_ecr_repository.chopsmart-api.repository_url}:latest"
      image_configuration {
        port = "8000"
        runtime_environment_variables = {
          ENVIRONMENT        = "production"
          OPENAI_API_KEY     = var.openai_api_key
          DEFAULT_AWS_REGION = var.aws_region
          BEDROCK_MODEL_ID   = var.bedrock_model_id
          BEDROCK_REGION     = var.bedrock_region
        }
      }
      image_repository_type = "ECR"
    }
  }

  instance_configuration {
    cpu    = "1 vCPU"
    memory = "2 GB"
    instance_role_arn = aws_iam_role.app_runner_instance_role.arn
  }

  tags = {
    Project = "chopsmart"
    Part    = "backend"
  }
}
