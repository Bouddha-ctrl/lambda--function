data "aws_secretsmanager_secret" "exchange_api_key" {
  name = var.secret_name
}
