"""
Configuration management and presets for EXR to PNG conversion.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
import yaml
import logging


logger = logging.getLogger(__name__)


@dataclass
class ConversionConfig:
    """Configuration for EXR to PNG conversion."""

    # Tone mapping settings
    tone_mapping: str = 'passthrough'  # 'passthrough', 'aces', 'reinhard', 'exposure', 'hable', 'filmic'
    exposure: float = 0.0  # EV adjustment (-5 to +5)
    gamma: float = 2.2  # Output gamma correction
    white_point: float = 2.0  # For Reinhard tone mapping

    # Output settings
    output_size: Optional[int] = 1024  # Target resolution (None = keep original)
    quality: int = 95  # PNG compression quality (0-100)
    optimize_png: bool = True  # Enable PNG optimization

    # Color space
    color_space: str = 'srgb'  # 'srgb', 'linear'
    apply_color_transform: bool = True  # Apply linear to sRGB conversion

    # Matcap optimization
    matcap_mode: bool = True  # Enable matcap-specific optimizations
    crop_method: str = 'center'  # 'center', 'top', 'bottom', 'left', 'right'
    resample_method: str = 'lanczos'  # 'lanczos', 'bicubic', 'bilinear'
    ensure_power_of_2: bool = True  # Ensure power-of-2 dimensions

    # Alpha channel
    preserve_alpha: bool = True  # Keep alpha channel if present

    # Enhancement filters (optional)
    sharpen: float = 0.0  # Sharpening amount (0.0-1.0)
    saturation: float = 1.0  # Saturation multiplier (0.0-2.0)
    brightness: float = 1.0  # Brightness multiplier (0.5-2.0)
    contrast: float = 1.0  # Contrast multiplier (0.5-2.0)

    # Batch processing
    recursive: bool = False  # Search subdirectories
    overwrite: bool = False  # Overwrite existing files
    workers: int = 4  # Number of parallel workers

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversionConfig':
        """Create config from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})

    def validate(self) -> None:
        """
        Validate configuration values.

        Raises:
            ValueError: If any configuration value is invalid
        """
        # Tone mapping validation
        valid_tone_mapping = ['passthrough', 'aces', 'reinhard', 'exposure', 'hable', 'filmic']
        if self.tone_mapping not in valid_tone_mapping:
            raise ValueError(f"Invalid tone_mapping: {self.tone_mapping}. "
                           f"Must be one of: {valid_tone_mapping}")

        # Exposure validation
        if not -10.0 <= self.exposure <= 10.0:
            raise ValueError(f"exposure must be between -10 and 10, got: {self.exposure}")

        # Gamma validation
        if not 0.1 <= self.gamma <= 5.0:
            raise ValueError(f"gamma must be between 0.1 and 5.0, got: {self.gamma}")

        # Quality validation
        if not 0 <= self.quality <= 100:
            raise ValueError(f"quality must be between 0 and 100, got: {self.quality}")

        # Size validation
        if self.output_size is not None:
            if not 32 <= self.output_size <= 8192:
                raise ValueError(f"output_size must be between 32 and 8192, got: {self.output_size}")

        # Color space validation
        valid_color_spaces = ['srgb', 'linear']
        if self.color_space not in valid_color_spaces:
            raise ValueError(f"Invalid color_space: {self.color_space}. "
                           f"Must be one of: {valid_color_spaces}")

        # Crop method validation
        valid_crop_methods = ['center', 'top', 'bottom', 'left', 'right']
        if self.crop_method not in valid_crop_methods:
            raise ValueError(f"Invalid crop_method: {self.crop_method}. "
                           f"Must be one of: {valid_crop_methods}")

        # Resample method validation
        valid_resample_methods = ['lanczos', 'bicubic', 'bilinear']
        if self.resample_method not in valid_resample_methods:
            raise ValueError(f"Invalid resample_method: {self.resample_method}. "
                           f"Must be one of: {valid_resample_methods}")

        # Filter validation
        if not 0.0 <= self.sharpen <= 2.0:
            raise ValueError(f"sharpen must be between 0.0 and 2.0, got: {self.sharpen}")

        if not 0.0 <= self.saturation <= 3.0:
            raise ValueError(f"saturation must be between 0.0 and 3.0, got: {self.saturation}")

        if not 0.1 <= self.brightness <= 3.0:
            raise ValueError(f"brightness must be between 0.1 and 3.0, got: {self.brightness}")

        if not 0.1 <= self.contrast <= 3.0:
            raise ValueError(f"contrast must be between 0.1 and 3.0, got: {self.contrast}")

        # Workers validation
        if not 1 <= self.workers <= 32:
            raise ValueError(f"workers must be between 1 and 32, got: {self.workers}")


# Preset configurations for common use cases
PRESETS: Dict[str, ConversionConfig] = {
    'blender-accurate': ConversionConfig(
        tone_mapping='passthrough',
        exposure=0.0,
        gamma=2.2,
        output_size=2048,
        quality=100,
        matcap_mode=True,
        sharpen=0.0,
        saturation=1.0,
    ),
    'matcap-metallic': ConversionConfig(
        tone_mapping='passthrough',
        exposure=0.0,
        gamma=2.2,
        output_size=1024,
        quality=95,
        matcap_mode=True,
        sharpen=0.1,
        saturation=1.0,
    ),
    'matcap-matte': ConversionConfig(
        tone_mapping='passthrough',
        exposure=0.0,
        gamma=2.2,
        output_size=512,
        quality=90,
        matcap_mode=True,
        sharpen=0.0,
        saturation=1.0,
    ),
    'matcap-glass': ConversionConfig(
        tone_mapping='passthrough',
        exposure=0.0,
        gamma=2.2,
        output_size=2048,
        quality=95,
        matcap_mode=True,
        preserve_alpha=True,
        sharpen=0.0,
        saturation=1.0,
    ),
    'matcap-stylized': ConversionConfig(
        tone_mapping='passthrough',
        exposure=0.0,
        gamma=2.2,
        output_size=512,
        quality=85,
        matcap_mode=True,
        sharpen=0.0,
        saturation=1.2,
        contrast=1.1,
    ),
    'matcap-ceramic': ConversionConfig(
        tone_mapping='passthrough',
        exposure=0.0,
        gamma=2.2,
        output_size=1024,
        quality=92,
        matcap_mode=True,
        sharpen=0.1,
        saturation=1.0,
    ),
    'high-quality': ConversionConfig(
        tone_mapping='passthrough',
        exposure=0.0,
        gamma=2.2,
        output_size=2048,
        quality=100,
        matcap_mode=True,
        resample_method='lanczos',
    ),
    'fast': ConversionConfig(
        tone_mapping='passthrough',
        exposure=0.0,
        gamma=2.2,
        output_size=512,
        quality=80,
        matcap_mode=True,
        resample_method='bilinear',
        optimize_png=False,
    ),
}


def get_preset(preset_name: str) -> ConversionConfig:
    """
    Get a preset configuration by name.

    Args:
        preset_name: Name of the preset

    Returns:
        ConversionConfig instance

    Raises:
        ValueError: If preset name is not found
    """
    if preset_name not in PRESETS:
        available = ', '.join(PRESETS.keys())
        raise ValueError(f"Unknown preset: {preset_name}. Available presets: {available}")

    logger.info(f"Using preset: {preset_name}")
    return PRESETS[preset_name]


def list_presets() -> Dict[str, str]:
    """
    List all available presets with descriptions.

    Returns:
        Dictionary mapping preset names to descriptions
    """
    descriptions = {
        'blender-accurate': 'Exact 1:1 Blender match, passthrough mode, max quality (2048px) - RECOMMENDED',
        'matcap-metallic': 'Metallic materials, passthrough mode (1024px)',
        'matcap-matte': 'Matte/diffuse materials, passthrough mode (512px)',
        'matcap-glass': 'Glass/transparent materials with alpha, passthrough mode (2048px)',
        'matcap-stylized': 'Stylized/cartoon rendering, passthrough mode (512px)',
        'matcap-ceramic': 'Ceramic and smooth materials, passthrough mode (1024px)',
        'high-quality': 'Maximum quality, passthrough mode (2048px, lossless)',
        'fast': 'Fast processing, passthrough mode (512px)',
    }
    return descriptions


def load_config_file(file_path: str) -> ConversionConfig:
    """
    Load configuration from YAML file.

    Args:
        file_path: Path to YAML configuration file

    Returns:
        ConversionConfig instance

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If configuration is invalid
    """
    try:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)

        config = ConversionConfig.from_dict(data)
        config.validate()

        logger.info(f"Loaded configuration from: {file_path}")
        return config

    except FileNotFoundError:
        raise FileNotFoundError(f"Configuration file not found: {file_path}")
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in configuration file: {e}")
    except Exception as e:
        raise ValueError(f"Failed to load configuration: {e}")


def save_config_file(config: ConversionConfig, file_path: str) -> None:
    """
    Save configuration to YAML file.

    Args:
        config: ConversionConfig instance
        file_path: Path for output YAML file

    Raises:
        IOError: If file cannot be written
    """
    try:
        config.validate()

        with open(file_path, 'w') as f:
            yaml.dump(config.to_dict(), f, default_flow_style=False, sort_keys=False)

        logger.info(f"Saved configuration to: {file_path}")

    except Exception as e:
        raise IOError(f"Failed to save configuration: {e}")


def merge_configs(base: ConversionConfig, overrides: Dict[str, Any]) -> ConversionConfig:
    """
    Merge configuration overrides into base configuration.

    Args:
        base: Base configuration
        overrides: Dictionary of override values

    Returns:
        New ConversionConfig with merged values
    """
    # Convert base to dict
    merged = base.to_dict()

    # Apply overrides
    for key, value in overrides.items():
        if key in merged:
            merged[key] = value
            logger.debug(f"Override: {key} = {value}")
        else:
            logger.warning(f"Ignoring unknown config key: {key}")

    # Create new config and validate
    config = ConversionConfig.from_dict(merged)
    config.validate()

    return config
