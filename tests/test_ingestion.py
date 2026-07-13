from __future__ import annotations

from pathlib import Path

import pytest

from validex.ingestion import (
    IngestionError,
    IngestionErrorCode,
    ingest_csv_bytes,
    ingest_csv_path,
)


def assert_ingestion_error(
    payload: bytes, filename: str, code: IngestionErrorCode
) -> IngestionError:
    with pytest.raises(IngestionError) as exc_info:
        ingest_csv_bytes(payload, filename=filename)
    assert exc_info.value.code is code
    assert exc_info.value.filename == filename
    return exc_info.value


def test_ingest_valid_csv_preserves_metadata():
    ingested = ingest_csv_bytes(
        b"compound_id,p_value,fdr\nA,0.01,0.02\nB,0.20,0.30\n",
        filename="study.csv",
    )

    assert ingested.metadata.filename == "study.csv"
    assert ingested.metadata.original_columns == ["compound_id", "p_value", "fdr"]
    assert ingested.metadata.row_count == 2
    assert ingested.metadata.column_count == 3
    assert ingested.dataframe.shape == (2, 3)


def test_ingest_path_uses_same_validation(tmp_path: Path):
    csv_path = tmp_path / "study.csv"
    csv_path.write_text("compound_id,p_value\nA,0.01\n", encoding="utf-8")

    ingested = ingest_csv_path(csv_path)

    assert ingested.metadata.filename == "study.csv"
    assert ingested.dataframe.iloc[0]["compound_id"] == "A"


def test_rejects_unsupported_extension_even_when_content_is_csv():
    assert_ingestion_error(
        b"compound_id,p_value\nA,0.01\n",
        "study.tsv",
        IngestionErrorCode.UNSUPPORTED_FORMAT,
    )


def test_empty_file_returns_controlled_error():
    assert_ingestion_error(b"", "empty.csv", IngestionErrorCode.EMPTY_FILE)


def test_header_only_file_returns_controlled_error():
    assert_ingestion_error(
        b"compound_id,p_value,fdr\n", "header_only.csv", IngestionErrorCode.NO_DATA_ROWS
    )


def test_duplicate_headers_are_detected_before_pandas_can_rename_them():
    err = assert_ingestion_error(
        b"compound_id,p_value,p_value\nA,0.01,0.02\n",
        "duplicate_headers.csv",
        IngestionErrorCode.DUPLICATE_HEADERS,
    )

    assert err.details["duplicate_headers"] == ["p_value"]


def test_blank_headers_are_detected():
    err = assert_ingestion_error(
        b"compound_id, ,fdr\nA,0.01,0.02\n",
        "blank_headers.csv",
        IngestionErrorCode.BLANK_HEADERS,
    )

    assert err.details["blank_header_indexes"] == [2]


def test_malformed_row_lengths_return_controlled_error():
    err = assert_ingestion_error(
        b"compound_id,p_value,fdr\nA,0.01,0.02\nB,0.03\n",
        "malformed.csv",
        IngestionErrorCode.MALFORMED_CSV,
    )

    assert err.details["row_number"] == 3


def test_invalid_encoding_returns_controlled_error():
    assert_ingestion_error(
        b"compound_id,p_value\nA,\xff\n",
        "invalid_encoding.csv",
        IngestionErrorCode.INVALID_ENCODING,
    )
