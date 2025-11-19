resource "aws_cloudwatch_log_group" "cloudfront_logs" {
  name              = "${var.log_group_name_prefix}/${var.api_gateway_domain_name}"
  retention_in_days = 1

  tags = var.tags
}

resource "aws_cloudfront_distribution" "api_distribution" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "CloudFront distribution for ${var.api_gateway_domain_name}"
  price_class         = var.price_class
  default_root_object = ""

  origin {
    domain_name = var.api_gateway_domain_name
    origin_id   = "api-gateway-origin"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }

    origin_path = "/${var.api_gateway_stage_name}"
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "api-gateway-origin"

    forwarded_values {
      query_string = true
      headers      = ["Accept", "Authorization"]

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = var.cache_min_ttl
    default_ttl            = var.cache_default_ttl
    max_ttl                = var.cache_max_ttl
    compress               = true
  }

  logging_config {
    include_cookies = false
    log_group       = aws_cloudwatch_log_group.cloudfront_logs.name
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = var.tags
}
