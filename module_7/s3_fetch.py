"""
AWS S3 to SageMaker Boto3 Data Ingestion Pipeline.
Module 7 - Cloud Computing Assignment (Data Pipeline & Cloud Deployment)
Johns Hopkins University - Software Concepts (EN.605.601)

Features:
- Connects to Amazon S3 using AWS SDK (boto3) via standard credential provider chain.
- Adheres to AWS security best practices (zero hardcoded credentials or access keys).
- Idempotently downloads the Grad Café dataset from S3 to SageMaker notebook instance.
- Saves applicant data locally as 'applicant_data_SM.json'.
- Validates data integrity (record count, JSON parsing, and schema attributes).
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from typing import Any, Dict, List, Optional

import boto3
from botocore.exceptions import BotoCoreError, ClientError

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [s3_fetch] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("s3_fetch")

DEFAULT_BUCKET = "grad-cafe-nf"
DEFAULT_OBJECT_KEY = "applicant_data.json"
DEFAULT_OUTPUT_PATH = "applicant_data_SM.json"
DEFAULT_REGION = "us-east-1"


def get_s3_client(
    session: Optional[boto3.Session] = None,
    region_name: Optional[str] = None,
) -> Any:
    """
    Instantiate and return an Amazon S3 client using safe credential resolution.

    Args:
        session: Optional existing boto3.Session instance.
        region_name: Optional AWS region string (defaults to AWS_REGION env var or us-east-1).

    Returns:
        boto3 S3 client instance.
    """
    region = region_name or os.environ.get(
        "AWS_REGION", os.environ.get("AWS_DEFAULT_REGION", DEFAULT_REGION)
    )

    if session is not None:
        return session.client("s3", region_name=region)

    active_session = boto3.session.Session(region_name=region)
    return active_session.client("s3")


def download_file_from_s3(
    bucket_name: str,
    object_key: str,
    destination_path: str,
    client: Optional[Any] = None,
) -> bool:
    """
    Download an object from an Amazon S3 bucket to a local destination file.

    Args:
        bucket_name: Name of the target S3 bucket (e.g. 'grad-cafe' or 'grad-cafe-nf').
        object_key: S3 key of the object (e.g. 'applicant_data.json').
        destination_path: Local filesystem destination path.
        client: Optional boto3 S3 client; if None, instantiated automatically.

    Returns:
        True if download succeeded, False otherwise.
    """
    s3_client = client or get_s3_client()
    dest_dir = os.path.dirname(os.path.abspath(destination_path))
    if dest_dir and not os.path.exists(dest_dir):
        os.makedirs(dest_dir, exist_ok=True)

    logger.info(
        "Initiating S3 download: s3://%s/%s -> %s", bucket_name, object_key, destination_path
    )
    try:
        s3_client.download_file(bucket_name, object_key, destination_path)
        logger.info(
            "Successfully downloaded s3://%s/%s to %s", bucket_name, object_key, destination_path
        )
        return True
    except (ClientError, BotoCoreError) as err:
        logger.error("AWS Boto3 transfer failure for s3://%s/%s: %s", bucket_name, object_key, err)
        return False
    except OSError as err:
        logger.error("Filesystem I/O error writing to %s: %s", destination_path, err)
        return False


def verify_downloaded_dataset(filepath: str) -> Dict[str, Any]:
    """
    Validate and inspect the integrity of the downloaded JSON dataset.

    Args:
        filepath: Path to the local JSON file.

    Returns:
        Dictionary containing summary statistics (status, record_count, file_size_bytes, sample_id).

    Raises:
        FileNotFoundError: If the target file does not exist.
        ValueError: If the file is empty or not valid JSON list of records.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Target dataset file does not exist: {filepath}")

    size_bytes = os.path.getsize(filepath)
    if size_bytes == 0:
        raise ValueError(f"Downloaded dataset is empty (0 bytes): {filepath}")

    with open(filepath, "r", encoding="utf-8") as f_in:
        try:
            records = json.load(f_in)
        except json.JSONDecodeError as json_err:
            raise ValueError(
                f"Invalid JSON content in {filepath}: {json_err}"
            ) from json_err

    if not isinstance(records, list):
        raise ValueError(f"Dataset root element must be a list, got {type(records).__name__}")

    record_count = len(records)
    first_record_id = (
        records[0].get("p_id")
        if record_count > 0 and isinstance(records[0], dict)
        else None
    )

    logger.info(
        "Integrity verified for %s: %d records, %d bytes, sample p_id=%s",
        filepath,
        record_count,
        size_bytes,
        first_record_id,
    )

    return {
        "status": "valid",
        "filepath": filepath,
        "record_count": record_count,
        "size_bytes": size_bytes,
        "first_p_id": first_record_id,
    }


def fetch_grad_cafe_data(
    bucket_name: Optional[str] = None,
    object_key: Optional[str] = None,
    destination_path: Optional[str] = None,
    region_name: Optional[str] = None,
    client: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Primary end-to-end data pipeline entrypoint for SageMaker notebook execution.

    Args:
        bucket_name: Target S3 bucket (or S3_BUCKET_NAME env var or default).
        object_key: Target S3 key (or S3_OBJECT_KEY env var or default).
        destination_path: Local output path (or LOCAL_OUTPUT_PATH env var or default).
        region_name: AWS region string.
        client: Optional pre-configured boto3 S3 client.

    Returns:
        Execution summary dictionary.
    """
    bucket = bucket_name or os.environ.get("S3_BUCKET_NAME", DEFAULT_BUCKET)
    key = object_key or os.environ.get("S3_OBJECT_KEY", DEFAULT_OBJECT_KEY)
    dest = destination_path or os.environ.get("LOCAL_OUTPUT_PATH", DEFAULT_OUTPUT_PATH)
    region = region_name or os.environ.get("AWS_REGION", DEFAULT_REGION)

    s3_client = client or get_s3_client(region_name=region)
    success = download_file_from_s3(bucket, key, dest, client=s3_client)

    if not success:
        return {
            "success": False,
            "bucket": bucket,
            "key": key,
            "destination": dest,
            "error": "S3 download failed. Check IAM permissions and bucket name.",
        }

    try:
        metrics = verify_downloaded_dataset(dest)
        return {
            "success": True,
            "bucket": bucket,
            "key": key,
            "destination": dest,
            "metrics": metrics,
        }
    except (FileNotFoundError, ValueError) as err:
        return {
            "success": False,
            "bucket": bucket,
            "key": key,
            "destination": dest,
            "error": str(err),
        }


def main(argv: Optional[List[str]] = None) -> int:
    """CLI execution entrypoint for boto3 pipeline execution."""
    parser = argparse.ArgumentParser(
        description="Module 7 AWS S3 to SageMaker Data Ingestion Pipeline"
    )
    parser.add_argument(
        "--bucket",
        default=os.environ.get("S3_BUCKET_NAME", DEFAULT_BUCKET),
        help="S3 bucket name (default: grad-cafe-nf)",
    )
    parser.add_argument(
        "--key",
        default=os.environ.get("S3_OBJECT_KEY", DEFAULT_OBJECT_KEY),
        help="S3 object key (default: applicant_data.json)",
    )
    parser.add_argument(
        "--output",
        default=os.environ.get("LOCAL_OUTPUT_PATH", DEFAULT_OUTPUT_PATH),
        help="Local output filename (default: applicant_data_SM.json)",
    )
    parser.add_argument(
        "--region",
        default=os.environ.get("AWS_REGION", DEFAULT_REGION),
        help="AWS region (default: us-east-1)",
    )

    args = parser.parse_args(argv)
    result = fetch_grad_cafe_data(
        bucket_name=args.bucket,
        object_key=args.key,
        destination_path=args.output,
        region_name=args.region,
    )

    if result.get("success"):
        print(f"[+] Data ingestion succeeded: {result['destination']}")
        print(f"[+] Total records: {result['metrics']['record_count']}")
        return 0

    print(f"[-] Data ingestion failed: {result.get('error')}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
