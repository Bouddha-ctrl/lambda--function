terraform {
  backend "s3" {
    # These values must be provided via -backend-config flags or environment variables
    # at terraform init time. Example:
    # terraform init \
    #   -backend-config="bucket=your-tf-state-bucket" \
    #   -backend-config="key=oil-exchange-lambda/terraform.tfstate" \
    #   -backend-config="region=us-east-1" \
    #   -backend-config="dynamodb_table=terraform-state-lock" \
    #   -backend-config="encrypt=true"
  }
}