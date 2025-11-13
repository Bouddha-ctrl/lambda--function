output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = module.lambda.function_name
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = module.lambda.function_arn
}

output "s3_bucket_name" {
  description = "Name of the S3 bucket for Lambda artifacts"
  value       = module.s3.bucket_name
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table"
  value       = module.dynamodb.table_name
}

output "eventbridge_rule_name" {
  description = "Name of the EventBridge rule"
  value       = module.eventbridge.rule_name
}

output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = module.apigateway.api_endpoint
}

output "api_url_get_latest" {
  description = "Full URL to get latest 30 oil prices"
  value       = module.apigateway.api_url_get_latest
}