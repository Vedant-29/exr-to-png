"""
EXR to PNG Converter for Three.js Matcaps

A high-quality converter for Blender EXR renders to PNG matcap textures
optimized for use in Three.js applications.
"""

__version__ = '1.0.0'
__author__ = 'EXR to PNG Converter'

from .converter import EXRConverter
from .config import ConversionConfig, get_preset, list_presets, PRESETS
from .tone_mapping import (
    aces_filmic_tonemap,
    reinhard_tonemap,
    exposure_tonemap,
    hable_filmic_tonemap,
    apply_tone_mapping,
    linear_to_srgb,
    srgb_to_linear
)
from .matcap_optimizer import (
    optimize_for_matcap,
    crop_to_square,
    resize_image,
    apply_matcap_filters
)
from .utils import (
    validate_exr_file,
    load_exr,
    save_png,
    find_exr_files,
    setup_logging
)


__all__ = [
    # Main classes
    'EXRConverter',
    'ConversionConfig',

    # Presets
    'get_preset',
    'list_presets',
    'PRESETS',

    # Tone mapping
    'aces_filmic_tonemap',
    'reinhard_tonemap',
    'exposure_tonemap',
    'hable_filmic_tonemap',
    'apply_tone_mapping',
    'linear_to_srgb',
    'srgb_to_linear',

    # Matcap optimization
    'optimize_for_matcap',
    'crop_to_square',
    'resize_image',
    'apply_matcap_filters',

    # Utilities
    'validate_exr_file',
    'load_exr',
    'save_png',
    'find_exr_files',
    'setup_logging',
]
