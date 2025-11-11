variable "lambda_zip_path" {
  description = "Path to lambda zip (relative to the module working dir). Leave empty if using s3_bucket/s3_key."
  type        = string
  default     = ""
}

variable "s3_bucket" {
  description = "S3 bucket name where lambda zip is stored (optional). If set, s3_key must also be set."
  type        = string
  default     = ""
}

variable "s3_key" {
  description = "S3 key for the lambda zip (optional). If set, s3_bucket must also be set."
  type        = string
  default     = ""
}

variable "function_name" {
  description = "Lambda function name"
  type        = string
}

variable "handler" {
  description = "Lambda handler"
  type        = string
}

variable "runtime" {
  description = "Lambda runtime"
  type        = string
}

variable "environment" {
  description = "Map of environment variables for the Lambda"
  type        = map(string)
  default     = {}
}

variable "dynamodb_table_arn" {
  description = "DynamoDB table ARN the lambda needs access to"
  type        = string
}

variable "s3_bucket_name" {
  description = "S3 bucket name for optional output (if ENABLE_S3=true)"
  type        = string
  default     = ""
}

variable "store_param_name" {
  description = "SSM parameter name containing the JSON with oil_api and exchange_api"
  type        = string
}

variable "tags" {
  description = "Tags map"
  type        = map(string)
  default     = {}
}