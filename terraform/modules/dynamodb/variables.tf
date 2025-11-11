variable "table_name" {
  description = "DynamoDB table name"
  type        = string
}

variable "tags" {
  description = "Tags map"
  type        = map(string)
  default     = {}
}