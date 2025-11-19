resource "aws_cloudwatch_log_group" "cloudfront_logs" {
  name              = "${var.log_group_name_prefix}/${var.api_gateway_domain_name}"
  retention_in_days = 1

  tags = var.tags
}

resource "aws_cloudwatch_logs_delivery_destination" "cloudfront" {
  name = "${var.api_gateway_domain_name}-cloudfront-logs"

  destination_resource_arn = aws_cloudwatch_log_group.cloudfront_logs.arn

  tags = var.tags
}

resource "aws_cloudwatch_logs_delivery_destination_policy" "cloudfront" {
  destination_name = aws_cloudwatch_logs_delivery_destination.cloudfront.name

  delivery_destination_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "delivery.logs.amazonaws.com"
        }
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.cloudfront_logs.arn}:*"
      }
    ]
  })
}

resource "aws_cloudwatch_logs_delivery_source" "cloudfront" {
  name          = "${var.api_gateway_domain_name}-cloudfront"
  log_type      = "CloudFront-Standard"
  resource_arns = [aws_cloudfront_distribution.api_distribution.arn]

  tags = var.tags
}

resource "aws_cloudwatch_logs_delivery" "cloudfront" {
  delivery_source_name     = aws_cloudwatch_logs_delivery_source.cloudfront.name
  delivery_destination_arn = aws_cloudwatch_logs_delivery_destination.cloudfront.arn

  tags = var.tags
}
