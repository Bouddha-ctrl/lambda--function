variable "api_gateway_domain_name" {
  description = "API Gateway domain name (invoke URL without https://)"
  type        = string
}

variable "api_gateway_stage_name" {
  description = "API Gateway stage name"
  type        = string
  default     = "prod"
}

variable "price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100" # Use only North America and Europe
}

variable "cache_min_ttl" {
  description = "Minimum TTL for cached objects (seconds)"
  type        = number
  default     = 0
}

variable "cache_default_ttl" {
  description = "Default TTL for cached objects (seconds)"
  type        = number
  default     = 3600 # 1 hour
}

variable "cache_max_ttl" {
  description = "Maximum TTL for cached objects (seconds)"
  type        = number
  default     = 86400 # 24 hours
}

variable "tags" {
  description = "Tags to apply to CloudFront distribution"
  type        = map(string)
  default     = {}
}
