data "aws_region" "current" {}

# IAM role for API Gateway to access DynamoDB
resource "aws_iam_role" "apigw" {
  name = "${var.api_name}-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "apigateway.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = var.tags
}

resource "aws_iam_role_policy" "apigw_dynamodb" {
  name = "dynamodb-access"
  role = aws_iam_role.apigw.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "dynamodb:GetItem",
        "dynamodb:Query",
        "dynamodb:Scan"
      ]
      Resource = var.dynamodb_table_arn
    }]
  })
}

# REST API
resource "aws_api_gateway_rest_api" "api" {
  name        = var.api_name
  description = "Oil prices API with direct DynamoDB integration"

  endpoint_configuration {
    types = ["REGIONAL"]
  }

  tags = var.tags
}

# /oil-prices resource
resource "aws_api_gateway_resource" "oil_prices" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "oil-prices"
}

# GET /oil-prices (scan latest 30 records)
resource "aws_api_gateway_method" "get_all" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.oil_prices.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "get_all" {
  rest_api_id             = aws_api_gateway_rest_api.api.id
  resource_id             = aws_api_gateway_resource.oil_prices.id
  http_method             = aws_api_gateway_method.get_all.http_method
  type                    = "AWS"
  integration_http_method = "POST"
  uri                     = "arn:aws:apigateway:${data.aws_region.current.name}:dynamodb:action/Query"
  credentials             = aws_iam_role.apigw.arn

  request_templates = {
    "application/json" = <<-EOT
    {
      "TableName": "${var.dynamodb_table_name}",
      "KeyConditionExpression": "pk = :pk",
      "ExpressionAttributeValues": {
        ":pk": {
          "S": "OIL_PRICE"
        }
      },
      "ScanIndexForward": false,
      "Limit": ${var.query_limit}
    }
    EOT
  }
}

resource "aws_api_gateway_method_response" "get_all_200" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.oil_prices.id
  http_method = aws_api_gateway_method.get_all.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = true
  }
}

resource "aws_api_gateway_integration_response" "get_all_200" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.oil_prices.id
  http_method = aws_api_gateway_method.get_all.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Origin" = "'*'"
  }

  response_templates = {
    "application/json" = <<-EOT
    {
      "items": [
        #foreach($item in $input.path('$.Items'))
        {
          "date": "$item.date.S",
          "oil_price": $item.oil_price.N,
          "exchange_rate": $item.exchange_rate.N
        }#if($foreach.hasNext),#end
        #end
      ],
      "count": $input.path('$.Count')
    }
    EOT
  }
}

# Deployment
resource "aws_api_gateway_deployment" "api" {
  rest_api_id = aws_api_gateway_rest_api.api.id

  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_integration.get_all.id,
    ]))
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_api_gateway_stage" "api" {
  deployment_id = aws_api_gateway_deployment.api.id
  rest_api_id   = aws_api_gateway_rest_api.api.id
  stage_name    = var.stage_name

  tags = var.tags
}

# Logging
resource "aws_cloudwatch_log_group" "apigw" {
  name              = "/aws/apigateway/${var.api_name}"
  retention_in_days = 7
  tags              = var.tags
}

resource "aws_api_gateway_method_settings" "api" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  stage_name  = aws_api_gateway_stage.api.stage_name
  method_path = "*/*"

  settings {
    logging_level      = "INFO"
    data_trace_enabled = true
    metrics_enabled    = true
  }
}
