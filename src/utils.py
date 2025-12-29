"""
Utility functions for EXR to PNG conversion.
Includes validation, I/O, and helper functions.
"""

import os
import logging
from pathlib import Path
from typing import List, Tuple, Optional
import numpy as np
import OpenEXR
import Imath


# Configure logging
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False, quiet: bool = False):
    """
    Configure logging based on verbosity settings.

    Args:
        verbose: Enable debug-level logging
        quiet: Suppress all logging except errors
    """
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO

    logging.basicConfig(
        level=level,
        format='%(levelname)s: %(message)s'
    )


def validate_exr_file(file_path: str) -> bool:
    """
    Validate that a file is a readable EXR file with RGB channels.

    Args:
        file_path: Path to the EXR file

    Returns:
        True if file is valid, False otherwise

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is not a valid EXR or missing required channels
    """
    # Check file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Check file extension
    if not file_path.lower().endswith('.exr'):
        raise ValueError(f"Not an EXR file: {file_path}")

    # Validate EXR header and channels
    try:
        exr_file = OpenEXR.InputFile(file_path)
        header = exr_file.header()

        # Check for required RGB channels
        channels = header['channels']
        required_channels = ['R', 'G', 'B']

        if not all(c in channels for c in required_channels):
            available = list(channels.keys())
            raise ValueError(
                f"EXR missing required RGB channels. "
                f"Found: {available}, Required: {required_channels}"
            )

        logger.debug(f"Validated EXR file: {file_path}")
        return True

    except Exception as e:
        raise ValueError(f"Invalid EXR file: {file_path} - {str(e)}")


def load_exr(file_path: str) -> Tuple[np.ndarray, dict]:
    """
    Load EXR file into numpy array.

    Args:
        file_path: Path to the EXR file

    Returns:
        Tuple of (image_array, metadata)
        - image_array: numpy array with shape (H, W, C) and dtype float32
        - metadata: dict with image metadata (size, channels, etc.)

    Raises:
        ValueError: If EXR file is invalid
    """
    validate_exr_file(file_path)

    try:
        exr_file = OpenEXR.InputFile(file_path)
        header = exr_file.header()

        # Get image dimensions
        dw = header['dataWindow']
        width = dw.max.x - dw.min.x + 1
        height = dw.max.y - dw.min.y + 1

        # Read RGB channels as float32
        FLOAT = Imath.PixelType(Imath.PixelType.FLOAT)
        channels = ['R', 'G', 'B']

        # Check for alpha channel
        has_alpha = 'A' in header['channels']
        if has_alpha:
            channels.append('A')

        # Read channel data
        channel_data = []
        for channel in channels:
            channel_bytes = exr_file.channel(channel, FLOAT)
            channel_array = np.frombuffer(channel_bytes, dtype=np.float32)
            channel_data.append(channel_array)

        # Stack channels and reshape
        img = np.stack(channel_data, axis=0)
        img = img.reshape(len(channels), height, width)
        img = np.transpose(img, (1, 2, 0))  # (C, H, W) -> (H, W, C)

        # Metadata
        metadata = {
            'width': width,
            'height': height,
            'channels': len(channels),
            'has_alpha': has_alpha,
            'data_window': (dw.min.x, dw.min.y, dw.max.x, dw.max.y),
        }

        logger.info(f"Loaded EXR: {width}x{height}, {len(channels)} channels")

        return img, metadata

    except Exception as e:
        raise ValueError(f"Failed to load EXR file {file_path}: {str(e)}")


def save_png(
    image: np.ndarray,
    output_path: str,
    quality: int = 95,
    optimize: bool = True
) -> None:
    """
    Save numpy array as PNG file.

    Args:
        image: Image array with shape (H, W, C) and values in [0, 1]
        output_path: Path for output PNG file
        quality: PNG compression quality (0-100)
        optimize: Enable PNG optimization

    Raises:
        ValueError: If image format is invalid
        IOError: If file cannot be written
    """
    from PIL import Image

    # Validate image
    if image.ndim not in [2, 3]:
        raise ValueError(f"Image must be 2D or 3D, got shape: {image.shape}")

    if image.dtype != np.float32 and image.dtype != np.uint8:
        logger.warning(f"Unexpected image dtype: {image.dtype}, converting to float32")
        image = image.astype(np.float32)

    # Convert to uint8 if needed
    if image.dtype == np.float32:
        # Ensure values are in [0, 1]
        image = np.clip(image, 0.0, 1.0)
        image = (image * 255).astype(np.uint8)

    # Create PIL Image
    if image.ndim == 2:
        # Grayscale
        pil_image = Image.fromarray(image, mode='L')
    elif image.shape[2] == 3:
        # RGB
        pil_image = Image.fromarray(image, mode='RGB')
    elif image.shape[2] == 4:
        # RGBA
        pil_image = Image.fromarray(image, mode='RGBA')
    else:
        raise ValueError(f"Unsupported number of channels: {image.shape[2]}")

    # Create output directory if needed
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
        logger.debug(f"Created output directory: {output_dir}")

    # Save with compression
    try:
        pil_image.save(
            output_path,
            format='PNG',
            optimize=optimize,
            compress_level=9 if quality > 90 else 6
        )
        logger.info(f"Saved PNG: {output_path}")

    except Exception as e:
        raise IOError(f"Failed to save PNG file {output_path}: {str(e)}")


def find_exr_files(
    input_path: str,
    recursive: bool = False
) -> List[str]:
    """
    Find all EXR files in a directory or return single file.

    Args:
        input_path: Path to EXR file or directory
        recursive: Search subdirectories recursively

    Returns:
        List of EXR file paths

    Raises:
        ValueError: If path doesn't exist or no EXR files found
    """
    path = Path(input_path)

    if not path.exists():
        raise ValueError(f"Path does not exist: {input_path}")

    # Single file
    if path.is_file():
        if path.suffix.lower() == '.exr':
            return [str(path)]
        else:
            raise ValueError(f"Not an EXR file: {input_path}")

    # Directory
    if path.is_dir():
        if recursive:
            exr_files = list(path.rglob('*.exr'))
        else:
            exr_files = list(path.glob('*.exr'))

        exr_files = sorted([str(f) for f in exr_files])

        if not exr_files:
            raise ValueError(f"No EXR files found in: {input_path}")

        logger.info(f"Found {len(exr_files)} EXR file(s)")
        return exr_files

    raise ValueError(f"Invalid path: {input_path}")


def generate_output_path(
    input_path: str,
    output_path: str,
    input_base_dir: Optional[str] = None
) -> str:
    """
    Generate output PNG path from input EXR path.

    Args:
        input_path: Input EXR file path
        output_path: Output path (file or directory)
        input_base_dir: Base directory for preserving structure (optional)

    Returns:
        Output PNG file path
    """
    input_path = Path(input_path)
    output_path = Path(output_path)

    # If output is a file path, use it directly
    if output_path.suffix.lower() == '.png':
        return str(output_path)

    # Output is a directory
    # Preserve directory structure if base dir is provided
    if input_base_dir:
        input_base = Path(input_base_dir)
        try:
            relative_path = input_path.relative_to(input_base)
            output_file = output_path / relative_path.with_suffix('.png')
        except ValueError:
            # Input not relative to base, use filename only
            output_file = output_path / input_path.with_suffix('.png').name
    else:
        # Use filename only
        output_file = output_path / input_path.with_suffix('.png').name

    return str(output_file)


def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes.

    Args:
        file_path: Path to file

    Returns:
        File size in MB
    """
    size_bytes = os.path.getsize(file_path)
    return size_bytes / (1024 * 1024)


def format_size(size_mb: float) -> str:
    """
    Format file size for display.

    Args:
        size_mb: Size in megabytes

    Returns:
        Formatted size string
    """
    if size_mb < 1:
        return f"{size_mb * 1024:.1f} KB"
    else:
        return f"{size_mb:.2f} MB"
