output "secret_arn" {
  description = "ARN of the secret"
  value       = data.aws_secretsmanager_secret.exchange_api_key.arn
}

output "secret_name" {
  description = "Name of the secret"
  value       = data.aws_secretsmanager_secret.exchange_api_key.name
}
