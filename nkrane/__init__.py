# nkrane/__init__.py
"""
Nkrane - Enhanced Machine Translation with Terminology Control
"""

from .translator import NkraneTranslator
from .terminology_manager import TerminologyManager
from .utils import list_available_options, export_terminology, get_language_mapping

__version__ = "0.2.0"
__all__ = ['NkraneTranslator', 'TerminologyManager', 'list_available_options', 
           'export_terminology', 'get_language_mapping']
