from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from validex.ingestion import (
    IngestionError,
    IngestionErrorCode,
    ingest_csv_bytes,
    ingest_csv_path,
    ingest_table_bytes,
    ingest_table_path,
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


def test_ingest_tsv_preserves_source_format_and_values():
    ingested = ingest_table_bytes(
        b"compound_id\tp_value\tfdr\nA\t0.01\t0.02\n",
        filename="study.tsv",
    )

    assert ingested.metadata.source_format == "tsv"
    assert ingested.metadata.selected_sheet is None
    assert ingested.metadata.selected_range == "A1:C2"
    assert ingested.metadata.selection_mechanism == "single_table_text"
    assert ingested.metadata.original_columns == ["compound_id", "p_value", "fdr"]
    assert ingested.dataframe.iloc[0]["compound_id"] == "A"


def test_ingest_xlsx_requires_explicit_sheet_when_multiple_plausible_sheets(tmp_path: Path):
    xlsx_path = tmp_path / "multi.xlsx"
    with pd.ExcelWriter(xlsx_path) as writer:
        pd.DataFrame({"compound_id": ["A"], "p_value": [0.01]}).to_excel(
            writer, sheet_name="positive", index=False
        )
        pd.DataFrame({"compound_id": ["B"], "p_value": [0.02]}).to_excel(
            writer, sheet_name="also_positive", index=False
        )

    with pytest.raises(IngestionError) as exc_info:
        ingest_table_path(xlsx_path)

    assert exc_info.value.code is IngestionErrorCode.AMBIGUOUS_TABLE
    assert exc_info.value.details["candidate_sheets"] == ["positive", "also_positive"]


def test_ingest_xlsx_with_explicit_sheet_records_selection_metadata(tmp_path: Path):
    xlsx_path = tmp_path / "study.xlsx"
    with pd.ExcelWriter(xlsx_path) as writer:
        pd.DataFrame({"notes": ["not the table"]}).to_excel(
            writer, sheet_name="metadata", index=False
        )
        pd.DataFrame(
            {
                "compound_id": ["A", "B"],
                "logFC": [1.2, -0.4],
                "p_value": [0.01, 0.20],
            }
        ).to_excel(writer, sheet_name="results", index=False)

    ingested = ingest_table_path(xlsx_path, sheet_name="results")

    assert ingested.metadata.source_format == "xlsx"
    assert ingested.metadata.selected_sheet == "results"
    assert ingested.metadata.selected_range == "A1:C3"
    assert ingested.metadata.selection_mechanism == "explicit_sheet"
    assert ingested.metadata.skipped_metadata_rows == 0
    assert ingested.metadata.parsing_warnings == []
    assert ingested.dataframe.shape == (2, 3)
