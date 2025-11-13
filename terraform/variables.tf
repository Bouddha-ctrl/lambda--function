variable "aws_region" {
  description = "AWS region to deploy to"
  type        = string
  default     = "eu-west-1"
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
  default     = "bouddha-lambda-artifacts"
}

variable "s3_lambda_key" {
  description = "S3 key for the lambda zip (optional; set in CI)"
  type        = string
  default     = ""
}

# SSM parameter name that contains the JSON with oil_api and exchange_api URLs
variable "store_param_name" {
  description = "SSM parameter name that contains JSON with oil_api and exchange_api (e.g., /prod/apis/all-urls)"
  type        = string
  default     = "/prod/apis/all-urls"
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
  default     = "cron(0 1 * * ? *)"
}

variable "enable_s3" {
  description = "Enable S3 latest.json output"
  type        = bool
  default     = false
}

variable "s3_bucket_name" {
  description = "S3 bucket name for latest.json output (optional, only used if enable_s3=true)"
  type        = string
  default     = "bouddha-lastest-records"
}

variable "exchange_api_key" {
  description = "API key for exchange rate API"
  type        = string
  sensitive   = true
  default     = ""
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default = {
    ManagedBy = "Terraform"
    Project   = "OilExchangeDaily"
  }
}