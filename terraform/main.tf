data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Secrets Manager for API keys
module "secrets" {
  source = "./modules/secrets"

  secret_name = "/prod/exchange-api-key"
}

# DynamoDB table for storing daily oil price + exchange rate
module "dynamodb" {
  source     = "./modules/dynamodb"
  table_name = var.ddb_table_name
  tags       = var.tags
}

# Lambda function
module "lambda" {
  source           = "./modules/lambda"
  lambda_zip_path  = var.lambda_zip_path
  s3_bucket        = var.s3_lambda_bucket
  s3_key           = var.s3_lambda_key
  function_name    = var.lambda_function_name
  handler          = "app.lambda_handler"
  runtime          = "python3.10"
  store_param_name = var.store_param_name

  environment = {
    DDB_TABLE_NAME           = module.dynamodb.table_name
    EXCHANGE_API_KEY_SECRET  = module.secrets.secret_arn
  }

  dynamodb_table_arn = module.dynamodb.table_arn
  secrets_arns       = [module.secrets.secret_arn]
  tags               = var.tags
}

# EventBridge rule to trigger Lambda daily
module "eventbridge" {
  source               = "./modules/eventbridge"
  rule_name            = "${var.lambda_function_name}-daily"
  schedule_expression  = var.schedule_expression
  lambda_function_arn  = module.lambda.function_arn
  lambda_function_name = module.lambda.function_name
  tags                 = var.tags
}

# API Gateway for querying DynamoDB
module "apigateway" {
  source = "./modules/apigateway"

  api_name            = "oil-prices-api"
  stage_name          = "prod"
  dynamodb_table_name = module.dynamodb.table_name
  dynamodb_table_arn  = module.dynamodb.table_arn

  tags = var.tags
}