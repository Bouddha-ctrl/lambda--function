variable "aws_region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "eu-east-1"
}

variable "lambda_zip_path" {
  description = "Path to the Lambda ZIP file (relative to terraform working dir). If empty, use S3 object variables instead."
  type        = string
  default     = ""
}

# If CI uploads the zip to S3, set these (preferred in CI).
variable "s3_lambda_bucket" {
  description = "S3 bucket that holds the lambda zip (optional; set in CI)"
  type        = string
  default     = ""
}

variable "s3_lambda_key" {
  description = "S3 key for the lambda zip (optional; set in CI)"
  type        = string
  default     = ""
}

# Legacy: allow injecting direct URLs JSON into the Lambda (kept for backward compatibility)
variable "store_json" {
  description = "JSON string that contains the API URLs, will be injected as Lambda env var STORE (legacy)"
  type        = string
  default     = ""
}

# Preferred: SSM parameter names mapping (JSON), e.g.
# {"oil_param":"/prod/apis/oil-price","exchange_param":"/prod/apis/exchange-rate"}
variable "store_ssm_json" {
  description = "JSON string that contains SSM parameter names mapping to fetch API URLs for the Lambda (preferred). Injected as STORE_SSM env var."
  type        = string
  default     = ""
}

variable "lambda_function_name" {
  description = "Lambda function name"
  type        = string
  default     = "daily-oil-exchange-fetcher"
}

variable "ddb_table_name" {
  description = "DynamoDB table name"
  type        = string
  default     = "OilPrices"
}

variable "schedule_expression" {
  description = "EventBridge schedule expression (AWS cron or rate)"
  type        = string
  default     = "cron(0 0 * * ? *)"
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {
    ManagedBy = "Terraform"
    Project   = "OilExchangeDaily"
  }
}