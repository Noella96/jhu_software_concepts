"""
Unit test suite for S3 to SageMaker boto3 data ingestion pipeline.
Module 7 - Cloud Computing Assignment (Data Pipeline & Cloud Deployment)
Johns Hopkins University - Software Concepts (EN.605.601)
"""
from __future__ import annotations

import json
import os
import runpy
from unittest.mock import MagicMock, patch
from botocore.exceptions import BotoCoreError, ClientError
import pytest

from s3_fetch import (
    download_file_from_s3,
    fetch_grad_cafe_data,
    get_s3_client,
    main,
    verify_downloaded_dataset,
)


@pytest.mark.pipeline
def test_get_s3_client_with_custom_session():
    """Test get_s3_client when an existing boto3 Session is supplied."""
    mock_session = MagicMock()
    mock_client = MagicMock()
    mock_session.client.return_value = mock_client

    client = get_s3_client(session=mock_session, region_name="us-west-2")
    assert client == mock_client
    mock_session.client.assert_called_once_with("s3", region_name="us-west-2")


@pytest.mark.pipeline
def test_get_s3_client_default_session():
    """Test get_s3_client dynamic session creation and region resolution."""
    with patch("boto3.session.Session") as mock_sess_cls:
        mock_sess_instance = MagicMock()
        mock_sess_cls.return_value = mock_sess_instance
        mock_client = MagicMock()
        mock_sess_instance.client.return_value = mock_client

        with patch.dict(os.environ, {"AWS_REGION": "eu-central-1"}, clear=False):
            client = get_s3_client()
            assert client == mock_client
            mock_sess_cls.assert_called_once_with(region_name="eu-central-1")

        mock_sess_cls.reset_mock()
        with patch.dict(os.environ, {"AWS_DEFAULT_REGION": "us-east-2"}, clear=True):
            client_def = get_s3_client()
            assert client_def == mock_client
            mock_sess_cls.assert_called_once_with(region_name="us-east-2")


@pytest.mark.pipeline
def test_download_file_from_s3_success(tmp_path):
    """Test successful S3 object download with directory creation."""
    dest_file = tmp_path / "nested" / "applicant_data_SM.json"
    mock_client = MagicMock()

    def fake_download(_b, _k, dest):
        with open(dest, "w", encoding="utf-8") as f_out:
            f_out.write('[{"p_id": 1}]')

    mock_client.download_file.side_effect = fake_download

    success = download_file_from_s3(
        bucket_name="grad-cafe-nf",
        object_key="applicant_data.json",
        destination_path=str(dest_file),
        client=mock_client,
    )

    assert success is True
    assert os.path.exists(str(dest_file))
    mock_client.download_file.assert_called_once_with(
        "grad-cafe-nf", "applicant_data.json", str(dest_file)
    )


@pytest.mark.pipeline
def test_download_file_from_s3_client_error(tmp_path):
    """Test S3 download error handling for ClientError and BotoCoreError."""
    dest_file = tmp_path / "test.json"
    mock_client = MagicMock()

    err_response = {"Error": {"Code": "404", "Message": "NoSuchKey"}}
    mock_client.download_file.side_effect = ClientError(err_response, "download_file")

    success_client_err = download_file_from_s3(
        "grad-cafe-nf", "missing.json", str(dest_file), client=mock_client
    )
    assert success_client_err is False

    mock_client.download_file.side_effect = BotoCoreError()
    success_boto_err = download_file_from_s3(
        "grad-cafe-nf", "missing.json", str(dest_file), client=mock_client
    )
    assert success_boto_err is False


@pytest.mark.pipeline
def test_download_file_from_s3_os_error(tmp_path):
    """Test filesystem permission or OS error during download."""
    dest_file = tmp_path / "forbidden.json"
    mock_client = MagicMock()
    mock_client.download_file.side_effect = OSError("Disk quota exceeded")

    success = download_file_from_s3(
        "grad-cafe-nf", "data.json", str(dest_file), client=mock_client
    )
    assert success is False


@pytest.mark.pipeline
def test_verify_downloaded_dataset_valid(sample_json_file):
    """Test validation of a valid JSON applicant dataset."""
    metrics = verify_downloaded_dataset(sample_json_file)
    assert metrics["status"] == "valid"
    assert metrics["record_count"] == 2
    assert metrics["first_p_id"] == 935454
    assert metrics["size_bytes"] > 0


@pytest.mark.pipeline
def test_verify_downloaded_dataset_empty_list(tmp_path):
    """Test validation of empty list dataset."""
    empty_f = tmp_path / "empty_list.json"
    with open(empty_f, "w", encoding="utf-8") as f_out:
        json.dump([], f_out)

    metrics = verify_downloaded_dataset(str(empty_f))
    assert metrics["record_count"] == 0
    assert metrics["first_p_id"] is None


@pytest.mark.pipeline
def test_verify_downloaded_dataset_errors(tmp_path):
    """Test dataset validation exception branches."""
    # 1. Non-existent file
    with pytest.raises(FileNotFoundError, match="does not exist"):
        verify_downloaded_dataset(str(tmp_path / "nonexistent.json"))

    # 2. Empty file (0 bytes)
    empty_file = tmp_path / "zero.json"
    empty_file.touch()
    with pytest.raises(ValueError, match="0 bytes"):
        verify_downloaded_dataset(str(empty_file))

    # 3. Invalid JSON
    corrupt_file = tmp_path / "corrupt.json"
    with open(corrupt_file, "w", encoding="utf-8") as f_out:
        f_out.write("{invalid json content")
    with pytest.raises(ValueError, match="Invalid JSON content"):
        verify_downloaded_dataset(str(corrupt_file))

    # 4. JSON not a list
    dict_file = tmp_path / "dict.json"
    with open(dict_file, "w", encoding="utf-8") as f_out:
        json.dump({"not_a": "list"}, f_out)
    with pytest.raises(ValueError, match="must be a list"):
        verify_downloaded_dataset(str(dict_file))


@pytest.mark.pipeline
def test_fetch_grad_cafe_data_success(tmp_path, sample_applicant_records):
    """Test full pipeline end-to-end success path."""
    dest_path = str(tmp_path / "applicant_data_SM.json")

    def fake_download(_b, _k, dest):
        with open(dest, "w", encoding="utf-8") as f_out:
            json.dump(sample_applicant_records, f_out)

    mock_client = MagicMock()
    mock_client.download_file.side_effect = fake_download

    res = fetch_grad_cafe_data(
        bucket_name="grad-cafe-nf",
        object_key="applicant_data.json",
        destination_path=dest_path,
        region_name="us-east-1",
        client=mock_client,
    )

    assert res["success"] is True
    assert res["metrics"]["record_count"] == 2
    assert res["destination"] == dest_path


@pytest.mark.pipeline
def test_fetch_grad_cafe_data_download_fail():
    """Test fetch_grad_cafe_data when S3 download returns False."""
    with patch("s3_fetch.download_file_from_s3", return_value=False):
        res = fetch_grad_cafe_data(bucket_name="bad-bucket")
        assert res["success"] is False
        assert "S3 download failed" in res["error"]


@pytest.mark.pipeline
def test_fetch_grad_cafe_data_verification_fail(tmp_path):
    """Test fetch_grad_cafe_data when verification fails on downloaded file."""
    dest = str(tmp_path / "corrupted.json")
    with patch("s3_fetch.download_file_from_s3", return_value=True), \
         patch("s3_fetch.verify_downloaded_dataset", side_effect=ValueError("Corrupt")):
        res = fetch_grad_cafe_data(destination_path=dest)
        assert res["success"] is False
        assert "Corrupt" in res["error"]


@pytest.mark.pipeline
def test_main_cli_success(sample_json_file):
    """Test main CLI entrypoint on successful download."""
    fake_metrics = {"record_count": 25, "size_bytes": 1024, "status": "valid"}
    fake_res = {
        "success": True,
        "destination": sample_json_file,
        "metrics": fake_metrics,
    }

    with patch("s3_fetch.fetch_grad_cafe_data", return_value=fake_res):
        exit_code = main(["--bucket", "b", "--key", "k", "--output", sample_json_file])
        assert exit_code == 0


@pytest.mark.pipeline
def test_main_cli_failure():
    """Test main CLI entrypoint on pipeline failure."""
    fake_fail = {"success": False, "error": "Access Denied"}
    with patch("s3_fetch.fetch_grad_cafe_data", return_value=fake_fail):
        exit_code = main(["--bucket", "nonexistent"])
        assert exit_code == 1


@pytest.mark.pipeline
def test_runpy_entrypoint(sample_json_file):
    """Test __main__ block invocation via runpy."""
    with patch("sys.argv", ["s3_fetch.py", "--output", sample_json_file]), \
         patch("boto3.session.Session") as mock_sess_cls, \
         patch("sys.exit") as mock_exit:
        mock_client = MagicMock()
        mock_sess_cls.return_value.client.return_value = mock_client
        runpy.run_module("s3_fetch", run_name="__main__", alter_sys=True)
        mock_exit.assert_called_once_with(0)
