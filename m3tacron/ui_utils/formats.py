"""
Format UI Utilities.
Contains hierarchy definitions and helper functions for dropdowns/filters.
"""
from ..backend.data_structures.formats import Format, MacroFormat

# Dynamic hierarchy for UI consumption
# Moved from backend/data_structures/formats.py
FORMAT_HIERARCHY = []
for macro in MacroFormat:
    children = [f for f in Format if f.macro == macro]
    if children:
        FORMAT_HIERARCHY.append({
            "label": macro.value, # Macro label is same as value for now
            "value": macro.value,
            "children": [{"label": f.label, "value": f.value} for f in children]
        })


def get_default_format_selection() -> dict[str, bool]:
    """
    Get default format selection with all formats enabled.
    
    Returns:
        dict mapping format/macro values to True.
    """
    result = {}
    for macro in FORMAT_HIERARCHY:
        result[macro["value"]] = True
        for child in macro["children"]:
            result[child["value"]] = True
    return result


def get_format_options() -> list[list[str]]:
    """
    Get format options for UI select components.
    
    Returns:
        List of [label, value] pairs including "All" option.
    """
    return [["All", "all"]] + [[m["label"], m["value"]] for m in FORMAT_HIERARCHY]
