import io
import json
import pandas as pd
from typing import List, Dict, Any, Tuple


class ResultExportService:
    """Exports query result sets to CSV, Excel (.xlsx), or JSON data formats."""

    @staticmethod
    def export_data(columns: List[str], rows: List[Dict[str, Any]], export_format: str = "csv") -> Tuple[bytes, str, str]:
        """
        Exports row datasets.
        Returns: (file_bytes, media_type, file_extension)
        """
        df = pd.DataFrame(rows, columns=columns) if rows else pd.DataFrame(columns=columns)

        fmt = export_format.lower().strip()

        if fmt in ("xlsx", "excel"):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Query Results")
            return output.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "xlsx"

        elif fmt == "json":
            json_str = df.to_json(orient="records", date_format="iso", indent=2)
            return json_str.encode("utf-8"), "application/json", "json"

        else:  # Default to CSV
            csv_str = df.to_csv(index=False)
            return csv_str.encode("utf-8"), "text/csv", "csv"


export_service = ResultExportService()
