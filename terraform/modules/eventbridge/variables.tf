variable "rule_name" {
  description = "EventBridge rule name"
  type        = string
}

variable "schedule_expression" {
  description = "Schedule expression (cron or rate)"
  type        = string
}

variable "lambda_function_arn" {
  description = "Lambda function ARN to trigger"
  type        = string
}

variable "lambda_function_name" {
  description = "Lambda function name (for permission)"
  type        = string
}

variable "tags" {
  description = "Tags map"
  type        = map(string)
  default     = {}
}