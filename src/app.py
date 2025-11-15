#!/usr/bin/env python3
import json
import logging
import traceback
import os
from datetime import datetime

# Support both Lambda (flat structure) and local dev (src. prefix)
try:
    from fetcher import fetch_oil_data, fetch_exchange_data, ExtractionError
    from ssm_resolver import get_store_urls
    from storage import save_to_dynamodb
except ImportError:
    from src.fetcher import fetch_oil_data, fetch_exchange_data, ExtractionError
    from src.ssm_resolver import get_store_urls
    from src.storage import save_to_dynamodb

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def lambda_handler(event, context):
    logger.info("Starting fetch run with event: %s", json.dumps(event))

    # Get the runtime URLs from the resolver (resolver handles config file + SSM)
    try:
        store = get_store_urls()
    except FileNotFoundError as e:
        logger.error("Configuration file not found: %s", e)
        return {"status": "error", "message": "config file not found"}
    except ValueError as e:
        logger.error("Configuration invalid: %s", e)
        return {"status": "error", "message": "invalid config or SSM content"}
    except Exception as e:
        logger.error("Failed to resolve SSM parameter: %s", e)
        return {"status": "error", "message": "failed to resolve SSM parameter"}

    oil_api = store.get("oil_api")
    exchange_api = store.get("exchange_api")
    if not oil_api or not exchange_api:
        logger.error("Resolved store missing URLs")
        return {"status": "error", "message": "resolved store missing urls"}

    # DynamoDB table name from environment
    ddb_table = os.environ.get("DDB_TABLE_NAME", "OilPrices")

    try:
        # Fetcher handles HTTP call + parsing and returns (date, value) directly
        oil_source_date, oil_val = fetch_oil_data(oil_api)
        exchange_source_date, exchange_val = fetch_exchange_data(exchange_api)

        # persist only if source dates match
        if oil_source_date != exchange_source_date:
            logger.warning(
                "Source date mismatch: oil_source_date=%s exchange_source_date=%s — skipping persist",
                oil_source_date,
                exchange_source_date,
            )
            return {
                "status": "skipped",
                "message": "source dates differ; not persisted",
                "oil_source_date": oil_source_date,
                "exchange_source_date": exchange_source_date,
            }

        date_str = oil_source_date or datetime.utcnow().date().isoformat()

        # Persist minimal record (date, oil_price, exchange_rate)
        save_to_dynamodb(
            table_name=ddb_table,
            date_str=date_str,
            oil_price=oil_val,
            exchange_rate=exchange_val,
        )

        return {"status": "ok", "date": date_str}
    except ExtractionError as e:
        logger.error("Data extraction error: %s", e)
        return {"status": "error", "message": f"extraction error: {e}"}
    except Exception:
        logger.error("Unhandled error during lambda run: %s", traceback.format_exc())
        return {"status": "error", "message": "exception"}