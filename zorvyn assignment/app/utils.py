from __future__ import annotations

from datetime import date
from typing import Any, Dict


def model_to_dict(
    model: Any,
    *,
    exclude_unset: bool = False,
    exclude_none: bool = False,
) -> Dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_unset=exclude_unset, exclude_none=exclude_none)
    return model.dict(exclude_unset=exclude_unset, exclude_none=exclude_none)


def convert_date_values(payload: Dict[str, Any]) -> Dict[str, Any]:
    converted: Dict[str, Any] = {}
    for key, value in payload.items():
        if isinstance(value, date):
            converted[key] = value.isoformat()
        else:
            converted[key] = value
    return converted
