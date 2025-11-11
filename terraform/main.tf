data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

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
    DDB_TABLE_NAME = module.dynamodb.table_name
    ENABLE_S3      = var.enable_s3 ? "true" : "false"
    S3_BUCKET_NAME = var.s3_bucket_name
    S3_KEY         = "latest.json"
  }

  dynamodb_table_arn = module.dynamodb.table_arn
  s3_bucket_name     = var.enable_s3 ? var.s3_bucket_name : ""
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