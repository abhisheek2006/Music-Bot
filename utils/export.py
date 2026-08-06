"""Data export utilities for CSV and JSON formats."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from utils.logging_setup import get_logger

logger = get_logger("utils.export")


class DataExporter:
    """Export data to various formats."""

    @staticmethod
    def to_json(
        data: list[dict[str, Any]] | dict[str, Any],
        indent: int = 2,
    ) -> str:
        """Export data to JSON string.

        Args:
            data: Data to export.
            indent: JSON indentation.

        Returns:
            JSON string.
        """
        return json.dumps(data, indent=indent, default=str, ensure_ascii=False)

    @staticmethod
    def to_csv(
        data: list[dict[str, Any]],
        fieldnames: list[str] | None = None,
    ) -> str:
        """Export data to CSV string.

        Args:
            data: List of dictionaries to export.
            fieldnames: Column names (auto-detected if None).

        Returns:
            CSV string.
        """
        if not data:
            return ""

        if fieldnames is None:
            fieldnames = list(data[0].keys())

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(data)
        return output.getvalue()

    @staticmethod
    def to_csv_file(
        data: list[dict[str, Any]],
        file_path: str,
        fieldnames: list[str] | None = None,
    ) -> str:
        """Export data to a CSV file.

        Args:
            data: List of dictionaries to export.
            file_path: Output file path.
            fieldnames: Column names.

        Returns:
            File path.
        """
        csv_content = DataExporter.to_csv(data, fieldnames)
        with open(file_path, "w", encoding="utf-8", newline="") as f:
            f.write(csv_content)
        logger.info("CSV exported", file_path=file_path, rows=len(data))
        return file_path

    @staticmethod
    def to_json_file(
        data: list[dict[str, Any]] | dict[str, Any],
        file_path: str,
        indent: int = 2,
    ) -> str:
        """Export data to a JSON file.

        Args:
            data: Data to export.
            file_path: Output file path.
            indent: JSON indentation.

        Returns:
            File path.
        """
        json_content = DataExporter.to_json(data, indent)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json_content)
        logger.info("JSON exported", file_path=file_path)
        return file_path

    @staticmethod
    def serialize_document(doc: dict[str, Any]) -> dict[str, Any]:
        """Serialize a MongoDB document for export.

        Args:
            doc: Document dictionary.

        Returns:
            Serialized dictionary.
        """
        result: dict[str, Any] = {}
        for key, value in doc.items():
            if key == "_id":
                result["id"] = str(value)
            elif hasattr(value, "isoformat"):
                result[key] = value.isoformat()
            elif isinstance(value, bytes):
                result[key] = value.decode("utf-8", errors="replace")
            else:
                result[key] = str(value) if value is not None else None
        return result


exporter = DataExporter()
