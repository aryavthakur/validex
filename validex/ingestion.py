from __future__ import annotations

import csv
import io
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]


class IngestionErrorCode(str, Enum):
    EMPTY_FILE = "EMPTY_FILE"
    INVALID_ENCODING = "INVALID_ENCODING"
    MALFORMED_CSV = "MALFORMED_CSV"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    DUPLICATE_HEADERS = "DUPLICATE_HEADERS"
    BLANK_HEADERS = "BLANK_HEADERS"
    NO_DATA_ROWS = "NO_DATA_ROWS"
    RESOURCE_LIMIT_EXCEEDED = "RESOURCE_LIMIT_EXCEEDED"
    AMBIGUOUS_TABLE = "AMBIGUOUS_TABLE"
    TABLE_NOT_FOUND = "TABLE_NOT_FOUND"


_HTTP_STATUS_BY_CODE = {
    IngestionErrorCode.EMPTY_FILE: 400,
    IngestionErrorCode.INVALID_ENCODING: 400,
    IngestionErrorCode.MALFORMED_CSV: 400,
    IngestionErrorCode.UNSUPPORTED_FORMAT: 415,
    IngestionErrorCode.DUPLICATE_HEADERS: 422,
    IngestionErrorCode.BLANK_HEADERS: 422,
    IngestionErrorCode.NO_DATA_ROWS: 400,
    IngestionErrorCode.RESOURCE_LIMIT_EXCEEDED: 413,
    IngestionErrorCode.AMBIGUOUS_TABLE: 422,
    IngestionErrorCode.TABLE_NOT_FOUND: 422,
}

_DEFAULT_MAX_BYTES = 200 * 1024 * 1024


@dataclass(frozen=True)
class ResourceLimits:
    max_upload_bytes: int = 50 * 1024 * 1024
    max_rows: int = 100_000
    max_columns: int = 500
    max_total_cells: int = 5_000_000
    max_cell_length: int = 20_000
    max_header_length: int = 300

    @classmethod
    def from_config(cls, config: dict[str, Any]) -> "ResourceLimits":
        return cls(
            max_upload_bytes=int(config.get("max_upload_bytes", cls.max_upload_bytes)),
            max_rows=int(config.get("max_rows", cls.max_rows)),
            max_columns=int(config.get("max_columns", cls.max_columns)),
            max_total_cells=int(config.get("max_total_cells", cls.max_total_cells)),
            max_cell_length=int(config.get("max_cell_length", cls.max_cell_length)),
            max_header_length=int(config.get("max_header_length", cls.max_header_length)),
        )


@dataclass(frozen=True)
class IngestionError(Exception):
    code: IngestionErrorCode
    message: str
    filename: str | None = None
    details: dict[str, Any] = field(default_factory=dict)

    @property
    def http_status(self) -> int:
        if (
            self.code is IngestionErrorCode.RESOURCE_LIMIT_EXCEEDED
            and self.details.get("limit") != "max_upload_bytes"
        ):
            return 422
        return _HTTP_STATUS_BY_CODE[self.code]

    def __str__(self) -> str:
        return f"{self.code.value}: {self.message}"

    def to_response(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "error_code": self.code.value,
            "message": self.message,
            "filename": os.path.basename(self.filename or ""),
        }
        if self.details:
            payload["details"] = self.details
        return payload


@dataclass(frozen=True)
class IngestionMetadata:
    filename: str
    original_columns: list[str]
    row_count: int
    column_count: int
    source_format: str = "csv"
    selected_sheet: str | None = None
    selected_range: str | None = None
    selection_mechanism: str = "single_table_text"
    skipped_metadata_rows: int = 0
    parsing_warnings: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class IngestedTable:
    dataframe: pd.DataFrame
    metadata: IngestionMetadata


def _safe_filename(filename: str | os.PathLike[str] | None) -> str:
    if filename is None:
        return "dataset.csv"
    return os.path.basename(os.fspath(filename)) or "dataset.csv"


def _require_csv_extension(filename: str) -> None:
    if not filename.lower().endswith(".csv"):
        raise IngestionError(
            code=IngestionErrorCode.UNSUPPORTED_FORMAT,
            message="Only .csv files are supported in this release.",
            filename=filename,
            details={"supported_extensions": [".csv"]},
        )


def _source_format(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix == ".tsv":
        return "tsv"
    if suffix == ".xlsx":
        return "xlsx"
    return suffix.lstrip(".") or "unknown"


def _a1_range(row_count: int, column_count: int, skipped_rows: int = 0) -> str:
    def col_label(index: int) -> str:
        label = ""
        while index:
            index, rem = divmod(index - 1, 26)
            label = chr(65 + rem) + label
        return label

    if row_count <= 0 or column_count <= 0:
        return ""
    first_row = skipped_rows + 1
    last_row = skipped_rows + row_count
    return f"A{first_row}:{col_label(column_count)}{last_row}"


def _resource_limit_error(
    filename: str, limit: str, maximum: int, actual: int
) -> IngestionError:
    return IngestionError(
        code=IngestionErrorCode.RESOURCE_LIMIT_EXCEEDED,
        message="CSV input exceeds the configured resource limits.",
        filename=filename,
        details={"limit": limit, "max": maximum, "actual": actual},
    )


def _decode_text(contents: bytes, filename: str, limits: ResourceLimits, format_label: str) -> str:
    if len(contents) > limits.max_upload_bytes:
        raise IngestionError(
            code=IngestionErrorCode.RESOURCE_LIMIT_EXCEEDED,
            message=f"{format_label.upper()} file exceeds the configured size limit.",
            filename=filename,
            details={
                "limit": "max_upload_bytes",
                "max": limits.max_upload_bytes,
                "actual": len(contents),
            },
        )
    if not contents:
        raise IngestionError(
            code=IngestionErrorCode.EMPTY_FILE,
            message=f"{format_label.upper()} file is empty.",
            filename=filename,
        )
    try:
        text = contents.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise IngestionError(
            code=IngestionErrorCode.INVALID_ENCODING,
            message=f"{format_label.upper()} file must be valid UTF-8 text.",
            filename=filename,
            details={"encoding": "utf-8"},
        ) from exc
    if text.strip() == "":
        raise IngestionError(
            code=IngestionErrorCode.EMPTY_FILE,
            message=f"{format_label.upper()} file is empty.",
            filename=filename,
        )
    return text


def _decode_csv(contents: bytes, filename: str, limits: ResourceLimits) -> str:
    return _decode_text(contents, filename, limits, "csv")


def _parse_delimited_rows(text: str, filename: str, delimiter: str, format_label: str) -> list[list[str]]:
    try:
        rows = list(csv.reader(io.StringIO(text), delimiter=delimiter, strict=True))
    except csv.Error as exc:
        raise IngestionError(
            code=IngestionErrorCode.MALFORMED_CSV,
            message=f"{format_label.upper()} file could not be parsed.",
            filename=filename,
            details={"parser_error": str(exc)},
        ) from exc

    if not rows:
        raise IngestionError(
            code=IngestionErrorCode.EMPTY_FILE,
            message=f"{format_label.upper()} file is empty.",
            filename=filename,
        )
    return rows


def _parse_csv_rows(text: str, filename: str) -> list[list[str]]:
    return _parse_delimited_rows(text, filename, ",", "csv")


def _validate_header(headers: list[str], filename: str) -> None:
    blank_indexes = [
        index + 1 for index, header in enumerate(headers) if header.strip() == ""
    ]
    if blank_indexes:
        raise IngestionError(
            code=IngestionErrorCode.BLANK_HEADERS,
            message="CSV header contains blank column names.",
            filename=filename,
            details={"blank_header_indexes": blank_indexes},
        )

    seen: set[str] = set()
    duplicates: list[str] = []
    for header in headers:
        if header in seen and header not in duplicates:
            duplicates.append(header)
        seen.add(header)
    if duplicates:
        raise IngestionError(
            code=IngestionErrorCode.DUPLICATE_HEADERS,
            message="CSV header contains duplicate column names.",
            filename=filename,
            details={"duplicate_headers": duplicates},
        )


def _validate_dimensions(
    rows: list[list[str]], filename: str, limits: ResourceLimits
) -> None:
    column_count = len(rows[0])
    row_count = max(0, len(rows) - 1)
    if column_count > limits.max_columns:
        raise _resource_limit_error(filename, "max_columns", limits.max_columns, column_count)
    if row_count > limits.max_rows:
        raise _resource_limit_error(filename, "max_rows", limits.max_rows, row_count)
    total_cells = row_count * column_count
    if total_cells > limits.max_total_cells:
        raise _resource_limit_error(filename, "max_total_cells", limits.max_total_cells, total_cells)
    for index, header in enumerate(rows[0], start=1):
        if len(header) > limits.max_header_length:
            raise _resource_limit_error(filename, "max_header_length", limits.max_header_length, len(header))
    for row_number, row in enumerate(rows[1:], start=2):
        for column_number, value in enumerate(row, start=1):
            if len(value) > limits.max_cell_length:
                raise IngestionError(
                    code=IngestionErrorCode.RESOURCE_LIMIT_EXCEEDED,
                    message="CSV cell exceeds the configured length limit.",
                    filename=filename,
                    details={
                        "limit": "max_cell_length",
                        "max": limits.max_cell_length,
                        "actual": len(value),
                        "row_number": row_number,
                        "column_number": column_number,
                    },
                )


def _validate_row_lengths(rows: list[list[str]], filename: str) -> None:
    expected_columns = len(rows[0])
    for row_index, row in enumerate(rows[1:], start=2):
        if len(row) != expected_columns:
            raise IngestionError(
                code=IngestionErrorCode.MALFORMED_CSV,
                message="CSV rows do not all contain the same number of columns as the header.",
                filename=filename,
                details={
                    "row_number": row_index,
                    "expected_columns": expected_columns,
                    "actual_columns": len(row),
                },
            )


def ingest_csv_bytes(
    contents: bytes,
    filename: str | None = None,
    limits: ResourceLimits | None = None,
) -> IngestedTable:
    active_limits = limits or ResourceLimits(max_upload_bytes=_DEFAULT_MAX_BYTES)
    safe_name = _safe_filename(filename)
    _require_csv_extension(safe_name)
    text = _decode_csv(contents, safe_name, active_limits)
    rows = _parse_csv_rows(text, safe_name)
    headers = rows[0]
    _validate_header(headers, safe_name)
    _validate_row_lengths(rows, safe_name)
    _validate_dimensions(rows, safe_name, active_limits)

    data_rows = rows[1:]
    if not data_rows:
        raise IngestionError(
            code=IngestionErrorCode.NO_DATA_ROWS,
            message="CSV file contains a header but no data rows.",
            filename=safe_name,
        )

    dataframe = pd.DataFrame(data_rows, columns=headers)
    metadata = IngestionMetadata(
        filename=safe_name,
        original_columns=list(headers),
        row_count=int(dataframe.shape[0]),
        column_count=int(dataframe.shape[1]),
        source_format="csv",
        selected_range=_a1_range(len(rows), len(headers)),
        selection_mechanism="single_table_text",
    )
    return IngestedTable(dataframe=dataframe, metadata=metadata)


def ingest_csv_path(
    path: str | os.PathLike[str],
    filename: str | None = None,
    limits: ResourceLimits | None = None,
) -> IngestedTable:
    csv_path = Path(path)
    safe_name = _safe_filename(filename or csv_path.name)
    _require_csv_extension(safe_name)
    contents = csv_path.read_bytes()
    return ingest_csv_bytes(contents, filename=safe_name, limits=limits)


def _ingest_delimited_bytes(
    contents: bytes,
    filename: str,
    delimiter: str,
    format_label: str,
    limits: ResourceLimits,
) -> IngestedTable:
    text = _decode_text(contents, filename, limits, format_label)
    rows = _parse_delimited_rows(text, filename, delimiter, format_label)
    headers = rows[0]
    _validate_header(headers, filename)
    _validate_row_lengths(rows, filename)
    _validate_dimensions(rows, filename, limits)
    data_rows = rows[1:]
    if not data_rows:
        raise IngestionError(
            code=IngestionErrorCode.NO_DATA_ROWS,
            message=f"{format_label.upper()} file contains a header but no data rows.",
            filename=filename,
        )
    dataframe = pd.DataFrame(data_rows, columns=headers)
    return IngestedTable(
        dataframe=dataframe,
        metadata=IngestionMetadata(
            filename=filename,
            original_columns=list(headers),
            row_count=int(dataframe.shape[0]),
            column_count=int(dataframe.shape[1]),
            source_format=format_label,
            selected_range=_a1_range(len(rows), len(headers)),
            selection_mechanism="single_table_text",
        ),
    )


def _coerce_xlsx_frame(frame: pd.DataFrame) -> pd.DataFrame:
    frame = frame.dropna(how="all").dropna(axis=1, how="all")
    frame = frame.astype(object).where(pd.notna(frame), "")
    frame.columns = [str(column) for column in frame.columns]
    for column in frame.columns:
        frame[column] = frame[column].map(lambda value: "" if pd.isna(value) else str(value))
    return frame


def _read_xlsx_sheet(
    xlsx: pd.ExcelFile,
    sheet_name: str,
    filename: str,
    limits: ResourceLimits,
    selection_mechanism: str,
) -> IngestedTable:
    try:
        frame = pd.read_excel(xlsx, sheet_name=sheet_name, dtype=object, engine="openpyxl")
    except ValueError as exc:
        raise IngestionError(
            code=IngestionErrorCode.TABLE_NOT_FOUND,
            message="Requested XLSX sheet was not found.",
            filename=filename,
            details={"sheet_name": sheet_name, "available_sheets": list(xlsx.sheet_names)},
        ) from exc
    dataframe = _coerce_xlsx_frame(frame)
    rows = [list(dataframe.columns)] + dataframe.astype(str).values.tolist()
    _validate_header(rows[0], filename)
    _validate_dimensions(rows, filename, limits)
    if dataframe.empty:
        raise IngestionError(
            code=IngestionErrorCode.NO_DATA_ROWS,
            message="XLSX sheet contains a header but no data rows.",
            filename=filename,
            details={"sheet_name": sheet_name},
        )
    return IngestedTable(
        dataframe=dataframe,
        metadata=IngestionMetadata(
            filename=filename,
            original_columns=list(dataframe.columns),
            row_count=int(dataframe.shape[0]),
            column_count=int(dataframe.shape[1]),
            source_format="xlsx",
            selected_sheet=sheet_name,
            selected_range=_a1_range(int(dataframe.shape[0]) + 1, int(dataframe.shape[1])),
            selection_mechanism=selection_mechanism,
            skipped_metadata_rows=0,
            parsing_warnings=[],
        ),
    )


def _plausible_xlsx_sheets(xlsx: pd.ExcelFile, filename: str) -> list[str]:
    plausible: list[str] = []
    for sheet in xlsx.sheet_names:
        try:
            preview = pd.read_excel(xlsx, sheet_name=sheet, nrows=5, dtype=object, engine="openpyxl")
        except Exception:
            continue
        preview = _coerce_xlsx_frame(preview)
        if preview.shape[0] > 0 and preview.shape[1] >= 2:
            try:
                _validate_header(list(preview.columns), filename)
            except IngestionError:
                continue
            plausible.append(str(sheet))
    return plausible


def ingest_table_bytes(
    contents: bytes,
    filename: str | None = None,
    limits: ResourceLimits | None = None,
    *,
    sheet_name: str | None = None,
) -> IngestedTable:
    active_limits = limits or ResourceLimits(max_upload_bytes=_DEFAULT_MAX_BYTES)
    safe_name = _safe_filename(filename)
    fmt = _source_format(safe_name)
    if fmt == "csv":
        return ingest_csv_bytes(contents, filename=safe_name, limits=active_limits)
    if fmt == "tsv":
        return _ingest_delimited_bytes(contents, safe_name, "\t", "tsv", active_limits)
    if fmt != "xlsx":
        raise IngestionError(
            code=IngestionErrorCode.UNSUPPORTED_FORMAT,
            message="Supported table formats are .csv, .tsv, and .xlsx.",
            filename=safe_name,
            details={"supported_extensions": [".csv", ".tsv", ".xlsx"]},
        )
    if len(contents) > active_limits.max_upload_bytes:
        raise IngestionError(
            code=IngestionErrorCode.RESOURCE_LIMIT_EXCEEDED,
            message="XLSX file exceeds the configured size limit.",
            filename=safe_name,
            details={
                "limit": "max_upload_bytes",
                "max": active_limits.max_upload_bytes,
                "actual": len(contents),
            },
        )
    if not contents:
        raise IngestionError(
            code=IngestionErrorCode.EMPTY_FILE,
            message="XLSX file is empty.",
            filename=safe_name,
        )
    try:
        xlsx = pd.ExcelFile(io.BytesIO(contents), engine="openpyxl")
    except Exception as exc:
        raise IngestionError(
            code=IngestionErrorCode.MALFORMED_CSV,
            message="XLSX workbook could not be parsed.",
            filename=safe_name,
            details={"parser_error": str(exc)},
        ) from exc
    if sheet_name is not None:
        return _read_xlsx_sheet(xlsx, sheet_name, safe_name, active_limits, "explicit_sheet")
    plausible = _plausible_xlsx_sheets(xlsx, safe_name)
    if len(plausible) == 1:
        return _read_xlsx_sheet(xlsx, plausible[0], safe_name, active_limits, "single_plausible_sheet")
    if len(plausible) > 1:
        raise IngestionError(
            code=IngestionErrorCode.AMBIGUOUS_TABLE,
            message="XLSX workbook contains multiple plausible result tables; choose a sheet explicitly.",
            filename=safe_name,
            details={"candidate_sheets": plausible},
        )
    raise IngestionError(
        code=IngestionErrorCode.TABLE_NOT_FOUND,
        message="XLSX workbook does not contain a supported result table.",
        filename=safe_name,
        details={"available_sheets": list(xlsx.sheet_names)},
    )


def ingest_table_path(
    path: str | os.PathLike[str],
    filename: str | None = None,
    limits: ResourceLimits | None = None,
    *,
    sheet_name: str | None = None,
) -> IngestedTable:
    table_path = Path(path)
    safe_name = _safe_filename(filename or table_path.name)
    contents = table_path.read_bytes()
    return ingest_table_bytes(contents, filename=safe_name, limits=limits, sheet_name=sheet_name)
