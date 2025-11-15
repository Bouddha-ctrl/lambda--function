data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = "${var.function_name}-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
  tags               = var.tags
}

# Construct the exact SSM parameter ARN for least-privilege
locals {
  ssm_param_arn = "arn:aws:ssm:${data.aws_region.current.region}:${data.aws_caller_identity.current.account_id}:parameter${var.store_param_name}"
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.function_name}-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = concat([
      {
        Sid = "DynamoDBAccess"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:GetItem"
        ]
        Effect   = "Allow"
        Resource = var.dynamodb_table_arn
      },
      {
        Sid = "CloudWatchLogs"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Sid = "SSMParameterRead"
        Action = [
          "ssm:GetParameter"
        ]
        Effect   = "Allow"
        Resource = local.ssm_param_arn
      }
      ],
      length(var.secrets_arns) > 0 ? [
        {
          Sid = "SecretsManagerRead"
          Action = [
            "secretsmanager:GetSecretValue"
          ]
          Effect   = "Allow"
          Resource = var.secrets_arns
        }
    ] : [])
  })
}

# CloudWatch Log Group with retention policy
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 7

  tags = var.tags
}

# Data source to get S3 object metadata (including version)
data "aws_s3_object" "lambda_zip" {
  count  = length(trim(var.s3_bucket, " ")) > 0 && length(trim(var.s3_key, " ")) > 0 ? 1 : 0
  bucket = var.s3_bucket
  key    = var.s3_key
}

resource "aws_lambda_function" "this" {
  depends_on = [aws_cloudwatch_log_group.lambda_logs]

  # Use local file if provided, otherwise use s3 bucket/key (CI uploads zip to S3).
  filename         = length(trim(var.lambda_zip_path, " ")) > 0 ? var.lambda_zip_path : null
  s3_bucket        = length(trim(var.s3_bucket, " ")) > 0 ? var.s3_bucket : null
  s3_key           = length(trim(var.s3_key, " ")) > 0 ? var.s3_key : null
  s3_object_version = length(data.aws_s3_object.lambda_zip) > 0 ? data.aws_s3_object.lambda_zip[0].version_id : null

  function_name = var.function_name
  handler       = var.handler
  runtime       = var.runtime
  role          = aws_iam_role.lambda_role.arn
  timeout       = 30

  # source_code_hash: use local file hash or S3 object etag
  source_code_hash = length(trim(var.lambda_zip_path, " ")) > 0 ? filebase64sha256(var.lambda_zip_path) : (length(data.aws_s3_object.lambda_zip) > 0 ? data.aws_s3_object.lambda_zip[0].etag : null)

  environment {
    variables = var.environment
  }

  tags = var.tags
}