#!/usr/bin/env python3
import json
import logging
from datetime import datetime
from decimal import Decimal

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource("dynamodb")
s3_client = boto3.client("s3")


def save_to_dynamodb(table_name: str, date_str: str, oil_price, exchange_rate):
    """
    Save the minimal day's data into DynamoDB.

    Parameters:
      - table_name: DynamoDB table name
      - date_str: primary key date as ISO string (YYYY-MM-DD)
      - oil_price: Decimal (or numeric/str convertible to Decimal) or None
      - exchange_rate: Decimal (or numeric/str convertible to Decimal) or None

    The stored item contains:
      - date (PK)
      - fetched_at (ISO timestamp)
      - oil_price (Decimal)  -- omitted if None
      - exchange_rate (Decimal) -- omitted if None

    Note: DynamoDB expects Decimal for numeric types when using boto3.
    """
    table = dynamodb.Table(table_name)
    item = {
        "date": date_str,
        "fetched_at": datetime.utcnow().isoformat() + "Z",
    }
    # Normalize numeric values to Decimal when possible
    if oil_price is not None:
        try:
            item["oil_price"] = Decimal(str(oil_price))
        except Exception:
            # fallback: store as string
            item["oil_price"] = str(oil_price)
    if exchange_rate is not None:
        try:
            item["exchange_rate"] = Decimal(str(exchange_rate))
        except Exception:
            item["exchange_rate"] = str(exchange_rate)

    logger.info("Putting minimal item into DynamoDB table %s: %s", table_name, item)
    table.put_item(Item=item)
    logger.info("Successfully saved minimal item to DynamoDB")


def save_latest_to_s3(bucket_name: str, key: str, data: dict):
    """
    Save the latest data to S3 as JSON.

    Parameters:
      - bucket_name: S3 bucket name
      - key: S3 object key (e.g., 'latest.json')
      - data: dictionary to save as JSON

    The data is serialized to JSON and uploaded to S3.
    """
    if not bucket_name:
        logger.warning("S3 bucket name not provided, skipping S3 upload")
        return

    try:
        json_data = json.dumps(data, indent=2)
        s3_client.put_object(
            Bucket=bucket_name,
            Key=key,
            Body=json_data.encode('utf-8'),
            ContentType='application/json'
        )
        logger.info("Successfully saved data to S3: s3://%s/%s", bucket_name, key)
    except Exception as e:
        logger.error("Failed to save data to S3: %s", e)
        raise