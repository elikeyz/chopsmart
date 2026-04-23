output "ecr_repository_url" {
  description = "URL of the ECR repository"
  value       = aws_ecr_repository.chopsmart-api.repository_url
}

output "app_runner_service_url" {
  description = "URL of the App Runner service"
  value       = try("https://${aws_apprunner_service.chopsmart-api.service_url}", "Not created yet - run 'terraform apply' after deploying Docker image")
}

output "app_runner_service_id" {
  description = "ID of the App Runner service"
  value       = try(aws_apprunner_service.chopsmart-api.id, "Not created yet")
}

output "setup_instructions" {
  description = "Instructions for completing setup"
  value = <<-EOT

    ✅ ChopSmart API deployed successfully!

    API URL: https://${aws_apprunner_service.chopsmart-api.service_url}

    Test the recipe endpoint with:
    curl https://${aws_apprunner_service.chopsmart-api.service_url}/api/generate-recipe -H "Content-Type: application/json" -d '{"ingredients": ["rice", "yam", "goat meat"], "calorie_target": 270, "dislikes": ["onion"], "allergies": ["avocado pear"]}'

    Note: You'll need to deploy your actual backend code to App Runner.
    Follow the guide for instructions on building and deploying the Docker image.
  EOT
}
