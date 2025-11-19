output "distribution_id" {
  description = "CloudFront distribution ID"
  value       = aws_cloudfront_distribution.api_distribution.id
}

output "distribution_arn" {
  description = "CloudFront distribution ARN"
  value       = aws_cloudfront_distribution.api_distribution.arn
}

output "distribution_domain_name" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.api_distribution.domain_name
}

output "distribution_url" {
  description = "Full CloudFront distribution URL"
  value       = "https://${aws_cloudfront_distribution.api_distribution.domain_name}"
}

output "log_group_name" {
  description = "CloudWatch log group name for CloudFront logs"
  value       = aws_cloudwatch_log_group.cloudfront_logs.name
}
