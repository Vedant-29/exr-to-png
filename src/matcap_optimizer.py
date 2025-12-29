"""
Matcap-specific optimization for Three.js usage.
Handles aspect ratio, sizing, and color space conversions.
"""

import numpy as np
from PIL import Image
import logging
from typing import Tuple, Optional


logger = logging.getLogger(__name__)


def crop_to_square(image: np.ndarray, method: str = 'center') -> np.ndarray:
    """
    Crop image to square aspect ratio.

    Args:
        image: Input image array (H, W, C)
        method: Cropping method ('center', 'top', 'bottom', 'left', 'right')

    Returns:
        Square cropped image array

    Raises:
        ValueError: If invalid method specified
    """
    height, width = image.shape[:2]

    if height == width:
        return image  # Already square

    size = min(height, width)

    if method == 'center':
        start_h = (height - size) // 2
        start_w = (width - size) // 2
    elif method == 'top':
        start_h = 0
        start_w = (width - size) // 2
    elif method == 'bottom':
        start_h = height - size
        start_w = (width - size) // 2
    elif method == 'left':
        start_h = (height - size) // 2
        start_w = 0
    elif method == 'right':
        start_h = (height - size) // 2
        start_w = width - size
    else:
        raise ValueError(f"Invalid crop method: {method}. "
                        f"Must be one of: 'center', 'top', 'bottom', 'left', 'right'")

    cropped = image[start_h:start_h + size, start_w:start_w + size]

    logger.debug(f"Cropped from {height}x{width} to {size}x{size} using {method} method")

    return cropped


def resize_image(
    image: np.ndarray,
    target_size: int,
    resample_method: str = 'lanczos'
) -> np.ndarray:
    """
    Resize image to target size using high-quality resampling.

    Args:
        image: Input image array (H, W, C) with values in [0, 1]
        target_size: Target width/height (assumes square)
        resample_method: Resampling method ('lanczos', 'bicubic', 'bilinear')

    Returns:
        Resized image array

    Raises:
        ValueError: If invalid resampling method specified
    """
    height, width = image.shape[:2]

    if height == target_size and width == target_size:
        return image  # Already correct size

    # Convert to uint8 for PIL
    if image.dtype == np.float32:
        image_uint8 = (np.clip(image, 0, 1) * 255).astype(np.uint8)
    else:
        image_uint8 = image

    # Determine number of channels
    if image.ndim == 2:
        mode = 'L'
    elif image.shape[2] == 3:
        mode = 'RGB'
    elif image.shape[2] == 4:
        mode = 'RGBA'
    else:
        raise ValueError(f"Unsupported number of channels: {image.shape[2]}")

    # Create PIL Image
    pil_image = Image.fromarray(image_uint8, mode=mode)

    # Select resampling filter
    if resample_method == 'lanczos':
        resample = Image.Resampling.LANCZOS
    elif resample_method == 'bicubic':
        resample = Image.Resampling.BICUBIC
    elif resample_method == 'bilinear':
        resample = Image.Resampling.BILINEAR
    else:
        raise ValueError(f"Invalid resampling method: {resample_method}. "
                        f"Must be one of: 'lanczos', 'bicubic', 'bilinear'")

    # Resize
    resized_pil = pil_image.resize((target_size, target_size), resample=resample)

    # Convert back to numpy
    resized = np.array(resized_pil).astype(np.float32) / 255.0

    logger.debug(f"Resized from {height}x{width} to {target_size}x{target_size} "
                f"using {resample_method} resampling")

    return resized


def ensure_power_of_two(size: int, prefer: str = 'nearest') -> int:
    """
    Ensure size is a power of 2 for optimal GPU usage.

    Args:
        size: Input size
        prefer: Preference for adjustment ('nearest', 'up', 'down')

    Returns:
        Power of 2 size
    """
    if size & (size - 1) == 0:
        return size  # Already power of 2

    # Find nearest powers of 2
    lower = 1 << (size.bit_length() - 1)
    upper = 1 << size.bit_length()

    if prefer == 'up':
        return upper
    elif prefer == 'down':
        return lower
    else:  # nearest
        if (size - lower) < (upper - size):
            return lower
        else:
            return upper


def validate_matcap_size(size: int, strict: bool = False) -> Tuple[bool, Optional[int]]:
    """
    Validate that size is appropriate for matcaps.

    Args:
        size: Size to validate
        strict: Require power of 2 (recommended for Three.js)

    Returns:
        Tuple of (is_valid, suggested_size)
    """
    # Common matcap sizes
    common_sizes = [256, 512, 1024, 2048, 4096]

    if size in common_sizes:
        return True, None

    if strict:
        # Suggest nearest power of 2
        suggested = ensure_power_of_two(size, prefer='nearest')
        return False, suggested

    # Allow any size in non-strict mode
    return True, None


def optimize_for_matcap(
    image: np.ndarray,
    target_size: int = 1024,
    crop_method: str = 'center',
    resample_method: str = 'lanczos',
    ensure_pot: bool = True
) -> np.ndarray:
    """
    Complete optimization pipeline for Three.js matcap usage.

    Args:
        image: Input image array (H, W, C) with values in [0, 1]
        target_size: Target resolution (default: 1024)
        crop_method: Method for cropping to square
        resample_method: Resampling filter for resize
        ensure_pot: Ensure power-of-2 size

    Returns:
        Optimized matcap image array

    Raises:
        ValueError: If invalid parameters specified
    """
    # Ensure power of 2 if requested
    if ensure_pot:
        original_size = target_size
        target_size = ensure_power_of_two(target_size, prefer='nearest')
        if target_size != original_size:
            logger.info(f"Adjusted size from {original_size} to {target_size} (power of 2)")

    # Validate size
    is_valid, suggested = validate_matcap_size(target_size, strict=True)
    if not is_valid and suggested:
        logger.warning(f"Unusual matcap size: {target_size}. "
                      f"Consider using {suggested} for better GPU performance")

    # Step 1: Crop to square
    if image.shape[0] != image.shape[1]:
        image = crop_to_square(image, method=crop_method)
        logger.info("Cropped to square aspect ratio for matcap")

    # Step 2: Resize to target size
    if image.shape[0] != target_size or image.shape[1] != target_size:
        image = resize_image(image, target_size, resample_method)
        logger.info(f"Resized to {target_size}x{target_size} for matcap")

    return image


def apply_matcap_filters(
    image: np.ndarray,
    sharpen: float = 0.0,
    saturation: float = 1.0,
    brightness: float = 1.0,
    contrast: float = 1.0
) -> np.ndarray:
    """
    Apply optional filters to enhance matcap appearance.

    Args:
        image: Input image array (H, W, C) with values in [0, 1]
        sharpen: Sharpening amount (0.0 = none, 1.0 = strong)
        saturation: Saturation multiplier (1.0 = original, <1.0 = desaturate, >1.0 = saturate)
        brightness: Brightness multiplier (1.0 = original)
        contrast: Contrast multiplier (1.0 = original)

    Returns:
        Filtered image array
    """
    filtered = image.copy()

    # Apply brightness
    if brightness != 1.0:
        filtered = filtered * brightness
        logger.debug(f"Applied brightness: {brightness}")

    # Apply contrast
    if contrast != 1.0:
        # Contrast around midpoint (0.5)
        filtered = (filtered - 0.5) * contrast + 0.5
        logger.debug(f"Applied contrast: {contrast}")

    # Apply saturation
    if saturation != 1.0 and filtered.shape[2] >= 3:
        # Calculate luminance
        luminance = (0.2126 * filtered[:, :, 0] +
                    0.7152 * filtered[:, :, 1] +
                    0.0722 * filtered[:, :, 2])

        # Blend between grayscale and original based on saturation
        for c in range(3):
            filtered[:, :, c] = luminance + saturation * (filtered[:, :, c] - luminance)

        logger.debug(f"Applied saturation: {saturation}")

    # Apply sharpening (unsharp mask)
    if sharpen > 0.0:
        from scipy import ndimage

        # Gaussian blur
        blurred = ndimage.gaussian_filter(filtered, sigma=1.0)

        # Unsharp mask
        filtered = filtered + sharpen * (filtered - blurred)

        logger.debug(f"Applied sharpening: {sharpen}")

    # Ensure values stay in valid range
    filtered = np.clip(filtered, 0.0, 1.0)

    return filtered


def add_matcap_metadata(image: np.ndarray, metadata: dict) -> dict:
    """
    Add Three.js-specific metadata for matcap textures.

    Args:
        image: Matcap image array
        metadata: Existing metadata dict

    Returns:
        Updated metadata dict with matcap-specific fields
    """
    height, width, channels = image.shape

    matcap_metadata = {
        **metadata,
        'matcap': True,
        'threejs_compatible': True,
        'size': width,
        'is_square': height == width,
        'is_power_of_2': (width & (width - 1)) == 0,
        'recommended_use': 'THREE.MeshMatcapMaterial',
        'color_space': 'sRGB',
    }

    return matcap_metadata
