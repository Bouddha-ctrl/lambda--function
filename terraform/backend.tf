terraform {
  backend "s3" {
    bucket         = "bouddha-tf-state-oil-lambda"
    key            = "oil-exchange-lambda/terraform.tfstate"
    region         = "eu-west-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}