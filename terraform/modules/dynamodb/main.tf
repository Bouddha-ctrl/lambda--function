resource "aws_dynamodb_table" "this" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "date"

  attribute {
    name = "pk"
    type = "S"
  }

  attribute {
    name = "date"
    type = "S"
  }

  tags = var.tags
}