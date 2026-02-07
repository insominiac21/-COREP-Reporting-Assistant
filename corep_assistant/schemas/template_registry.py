"""Template registry loader and access functions"""
from typing import Dict, Optional, List
from .c01_00 import get_c01_registry
from .c07_00 import get_c07_registry

# Registry cache
_REGISTRY_CACHE: Dict[str, Dict] = {}


def load_template_registry(template_id: str) -> Dict:
    """
    Load template registry for given template_id.
    
    Args:
        template_id: Template identifier (C01.00 or C07.00)
        
    Returns:
        Registry dictionary with metadata, allowed rows/columns, rules
        
    Raises:
        ValueError: If template_id is not supported
    """
    if template_id in _REGISTRY_CACHE:
        return _REGISTRY_CACHE[template_id]
    
    normalized_id = template_id.replace(" ", "").upper()
    
    if normalized_id == "C01.00":
        registry = get_c01_registry()
    elif normalized_id == "C07.00":
        registry = get_c07_registry()
    else:
        raise ValueError(f"Unsupported template: {template_id}")
    
    _REGISTRY_CACHE[template_id] = registry
    return registry


def get_allowed_rows(template_id: str) -> List[str]:
    """Get list of allowed row codes for template"""
    registry = load_template_registry(template_id)
    return registry["allowed_rows"]


def get_allowed_columns(template_id: str) -> List[str]:
    """Get list of allowed column codes for template"""
    registry = load_template_registry(template_id)
    return registry["allowed_columns"]


def is_valid_cell(template_id: str, row_code: str, col_code: str) -> bool:
    """Check if row/column combination is valid for template"""
    registry = load_template_registry(template_id)
    cell_id = f"{row_code}:{col_code}"
    return cell_id in registry["cell_ids"]


def get_all_templates() -> List[str]:
    """Get list of all supported template IDs"""
    return ["C01.00", "C07.00"]


def get_template_metadata(template_id: str) -> Dict:
    """Get metadata for a template"""
    registry = load_template_registry(template_id)
    return registry["metadata"]
