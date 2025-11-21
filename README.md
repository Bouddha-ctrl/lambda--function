# Daily Oil Price & Exchange Rate Fetcher

AWS Lambda function that fetches daily oil prices and USD to MAD exchange rates, stores them in DynamoDB, and exposes them via API Gateway.

**Data Flow:**

1. **Scheduled Trigger**: EventBridge triggers Lambda daily at 01:00 UTC
2. **Fetch Configuration**: Lambda reads API URLs from SSM Parameter Store
3. **Fetch Oil Price**: Lambda calls external Oil Price API
4. **Validate Date**: Checks if oil price date matches expected date (yesterday)
5. **Fetch Exchange Rate**: If valid, retrieves API key from Secrets Manager and calls Exchange Rate API
6. **Validate & Store**: If both dates match, saves to DynamoDB with `pk="OIL_PRICE"` and `date` as sort key
7. **Query Data**: Clients access CloudFront URL → CloudFront caches and forwards to API Gateway → API Gateway directly queries DynamoDB via VTL templates → Returns latest 30 records

**Components:**

- **Lambda Function**: Fetches oil price and exchange rate data daily
- **DynamoDB**: Stores historical price data with partition key `pk="OIL_PRICE"` and sort key `date`
- **EventBridge**: Triggers Lambda daily at 01:00 UTC
- **API Gateway**: REST API with direct DynamoDB integration (VTL templates)
- **CloudFront**: CDN for caching API responses (1-hour default TTL)
- **Secrets Manager**: Securely stores exchange rate API key
- **S3**: Lambda deployment artifacts bucket

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform 1.5.7+
- Python 3.10+
- S3 bucket for Lambda artifacts: `bouddha-lambda-artifacts` (with versioning enabled)
- S3 bucket for Terraform state: `bouddha-tf-state-oil-lambda`
- DynamoDB table for Terraform lock: `terraform-state-lock`

## Setup

### 1. Create AWS Secrets Manager Secret

The exchange rate API key must be stored in AWS Secrets Manager:

```bash
aws secretsmanager create-secret \
  --name "/prod/exchange-api-key" \
  --description "API key for exchange rate service" \
  --secret-string '{"key":"YOUR_ACTUAL_API_KEY_HERE"}' \
  --region eu-west-1
```

### 2. Create SSM Parameter

Store API endpoints in AWS Systems Manager Parameter Store:

```bash
aws ssm put-parameter \
  --name "/prod/apis/all-urls" \
  --type "String" \
  --value '{"oil_api":"https://oil-api-url","exchange_api":"https://exchange-api-url"}' \
  --region eu-west-1
```

### 3. Deploy Infrastructure

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

## Project Structure

```
.
├── src/
│   ├── app.py              # Lambda handler entry point
│   ├── fetcher.py          # Fetch oil price and exchange rate from APIs
│   ├── storage.py          # DynamoDB operations
│   └── ssm_resolver.py     # SSM parameter resolution
├── terraform/
│   ├── main.tf             # Root Terraform configuration
│   ├── variables.tf        # Terraform variables
│   ├── backend.tf          # S3 backend configuration
│   ├── provider.tf         # AWS provider configuration
│   └── modules/
│       ├── lambda/         # Lambda function and IAM role
│       ├── dynamodb/       # DynamoDB table
│       ├── eventbridge/    # EventBridge rule
│       ├── apigateway/     # API Gateway with DynamoDB integration
│       └── secrets/        # Secrets Manager data source
├── tests/
│   ├── test_app.py         # Integration tests
│   ├── test_fetcher.py     # Unit tests for fetcher
│   └── conftest.py         # Pytest configuration
├── .github/workflows/
│   └── ci.yml              # GitHub Actions CI/CD pipeline
├── requirements.txt        # Python dependencies
└── pyproject.toml          # Python project configuration
```

## Lambda Function

### Environment Variables

- `DDB_TABLE_NAME`: DynamoDB table name (default: `OilPrices`)
- `EXCHANGE_API_KEY_SECRET`: ARN of the Secrets Manager secret

### Execution Flow

1. Fetches oil price data from configured API
2. Checks if oil price date matches expected date (yesterday)
3. If match, fetches exchange rate data
4. Verifies exchange rate date also matches expected date
5. Saves both values to DynamoDB with partition key `pk="OIL_PRICE"` and date as sort key

## API Gateway

### Endpoints

**GET /oil-prices**

Returns the latest 30 oil price records in descending date order.

**Example Response:**
```json
{
  "items": [
    {
      "pk": "OIL_PRICE",
      "date": "2025-11-14",
      "oil_price": 639.25,
      "exchange_rate": 9.49,
      "fetched_at": "2025-11-15T01:00:00Z"
    },
    {
      "pk": "OIL_PRICE",
      "date": "2025-11-13",
      "oil_price": 642.10,
      "exchange_rate": 9.51,
      "fetched_at": "2025-11-14T01:00:00Z"
    }
  ]
}
```

## DynamoDB Schema

**Table Name:** `OilPrices`

**Keys:**
- Partition Key: `pk` (String) - Always `"OIL_PRICE"`
- Sort Key: `date` (String) - ISO date format `YYYY-MM-DD`

**Attributes:**
- `oil_price` (Number) - Oil price in local currency
- `exchange_rate` (Number) - USD to MAD exchange rate
- `fetched_at` (String) - ISO timestamp when data was fetched

## CI/CD Pipeline

GitHub Actions workflow in `.github/workflows/ci.yml`:

1. **Terraform Format Check**: Validates Terraform formatting
2. **Python Tests**: Runs pytest test suite
3. **Deploy** (on push to main):
   - Packages Lambda code into zip
   - Uploads zip to S3 with versioning
   - Runs Terraform apply to update infrastructure

### Required GitHub Secrets

- `AWS_ACCESS_KEY_ID`: AWS access key for deployment
- `AWS_SECRET_ACCESS_KEY`: AWS secret access key for deployment

## Development

### Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Run specific test file
pytest tests/test_fetcher.py -v
```

## IAM Permissions

### Lambda Execution Role

The Lambda function has permissions to:
- **DynamoDB**: `PutItem`, `UpdateItem`, `GetItem` on `OilPrices` table
- **CloudWatch Logs**: Create log groups and streams
- **SSM**: `GetParameter` on `/prod/apis/all-urls`
- **Secrets Manager**: `GetSecretValue` on `/prod/exchange-api-key`

## Monitoring

- **CloudWatch Logs**: Lambda logs retained for 7 days
  - Log group: `/aws/lambda/daily-oil-exchange-fetcher`
- **API Gateway Logs**: Execution logs for API requests
- **DynamoDB**: Monitor read/write capacity usage

## License

MIT
