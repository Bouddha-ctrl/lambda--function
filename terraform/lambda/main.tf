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

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "${var.function_name}-policy"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:GetItem"
        ]
        Effect   = "Allow"
        Resource = var.dynamodb_table_arn
      },
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Effect   = "Allow"
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        # Allow reading SSM parameters; scoped to the account and region
        Action = [
          "ssm:GetParameter",
          "ssm:GetParameters"
        ]
        Effect = "Allow"
        Resource = "arn:aws:ssm:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:parameter/*"
      }
    ]
  })

  role = aws_iam_role.lambda_role.id
}

resource "aws_lambda_function" "this" {
  # Use local file if provided, otherwise use s3 bucket/key (CI uploads zip to S3).
  filename         = length(trim(var.lambda_zip_path)) > 0 ? var.lambda_zip_path : null
  s3_bucket        = length(trim(var.s3_bucket)) > 0 ? var.s3_bucket : null
  s3_key           = length(trim(var.s3_key)) > 0 ? var.s3_key : null

  function_name    = var.function_name
  handler          = var.handler
  runtime          = var.runtime
  role             = aws_iam_role.lambda_role.arn

  # source_code_hash is required when providing local filename; omit when using S3
  source_code_hash = length(trim(var.lambda_zip_path)) > 0 ? filebase64sha256(var.lambda_zip_path) : null

  environment {
    variables = var.environment
  }

  tags = var.tags
}