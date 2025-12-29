"""
Tone mapping algorithms for HDR to LDR conversion.
Optimized for matcap generation from Blender EXR renders.
"""

import numpy as np
from typing import Literal


def passthrough_tonemap(hdr: np.ndarray) -> np.ndarray:
    """
    Pass-through tone mapping - preserves the image as-is.

    For matcaps that are already tone-mapped in Blender (LDR stored as EXR).
    Simply clips to [0, 1] range without any curve application.
    This preserves the exact look from Blender.

    Args:
        hdr: Image array (H, W, C) with float32 values

    Returns:
        Image array (H, W, C) with values in [0, 1], unchanged except clipping
    """
    return np.clip(hdr, 0.0, 1.0)


def aces_filmic_tonemap(hdr: np.ndarray) -> np.ndarray:
    """
    ACES Filmic tone mapping (approximate RRT).

    This version returns linear data intended for sRGB conversion.
    Based on the RRT (Reference Rendering Transform) approximation.

    Args:
        hdr: HDR image array (H, W, C) with float32 values

    Returns:
        LDR image array (H, W, C) with values in [0, 1] (Linear)
    """
    # ACES RRT approximation coefficients
    # Adapted from Stephen Hill's fit
    a = hdr * (hdr + 0.0245786) - 0.000090537
    b = hdr * (0.983729 * hdr + 0.4329510) + 0.238081

    tone_mapped = a / b

    return np.clip(tone_mapped, 0.0, 1.0)


def reinhard_tonemap(hdr: np.ndarray, white_point: float = 2.0) -> np.ndarray:
    """
    Reinhard tone mapping with configurable white point.

    Good for balanced conversion with control over highlight compression.
    Works well for matte and diffuse materials.

    Args:
        hdr: HDR image array (H, W, C) with float32 values
        white_point: Maximum white luminance value (default: 2.0)

    Returns:
        LDR image array (H, W, C) with values in [0, 1]
    """
    # Calculate luminance using Rec. 709 coefficients
    luminance = 0.2126 * hdr[..., 0] + 0.7152 * hdr[..., 1] + 0.0722 * hdr[..., 2]

    # Add small epsilon to avoid division by zero
    luminance = luminance + 1e-6

    # Reinhard operator with white point
    scale = (1.0 + luminance / (white_point ** 2)) / (1.0 + luminance)

    # Apply scaling to each channel
    tone_mapped = hdr * scale[..., np.newaxis]

    return np.clip(tone_mapped, 0.0, 1.0)


def exposure_tonemap(hdr: np.ndarray, exposure: float = 0.0) -> np.ndarray:
    """
    Simple exposure-based tone mapping.

    Fast and simple, good for quick adjustments and stylized materials.
    Exposure is in EV (exposure value) stops.
    Returns linear data (gamma correction should be applied later).

    Args:
        hdr: HDR image array (H, W, C) with float32 values
        exposure: Exposure adjustment in EV stops (default: 0.0)

    Returns:
        LDR image array (H, W, C) with values in [0, 1]
    """
    # Apply exposure (2^EV multiplier)
    exposed = hdr * (2.0 ** exposure)

    # Protect against negative values
    exposed = np.maximum(exposed, 0.0)

    return np.clip(exposed, 0.0, 1.0)


def hable_filmic_tonemap(hdr: np.ndarray) -> np.ndarray:
    """
    Uncharted 2 filmic tone mapping (John Hable).

    Popular in game development, good balance between contrast and detail.
    Excellent for stylized matcaps with strong character.

    Args:
        hdr: HDR image array (H, W, C) with float32 values

    Returns:
        LDR image array (H, W, C) with values in [0, 1]
    """
    def hable_curve(x):
        A = 0.15  # Shoulder strength
        B = 0.50  # Linear strength
        C = 0.10  # Linear angle
        D = 0.20  # Toe strength
        E = 0.02  # Toe numerator
        F = 0.30  # Toe denominator

        return ((x * (A * x + C * B) + D * E) / (x * (A * x + B) + D * F)) - E / F

    # Apply curve
    # Using 1.0 exposure bias for a more neutral linear output
    curr = hable_curve(hdr)

    # White point
    W = 11.2
    white_scale = 1.0 / hable_curve(np.array([W]))[0]

    tone_mapped = curr * white_scale

    return np.clip(tone_mapped, 0.0, 1.0)


def blender_filmic_tonemap(hdr: np.ndarray) -> np.ndarray:
    """
    Approximation of Blender's Filmic tone mapping.
    Uses a log-based curve with a smooth shoulder and toe.

    Args:
        hdr: HDR image array (H, W, C) with float32 values

    Returns:
        LDR image array (H, W, C) with values in [0, 1]
    """
    # Exposure adjustment (Blender's Filmic usually needs a bit of a lift)
    x = hdr * 0.6

    # Better Filmic approximation with toe and shoulder
    # toe: x^1.2 for slightly deeper shadows
    x = np.power(np.maximum(x, 0.0), 1.2)

    # shoulder: smooth compression
    white = 2.0
    tone_mapped = (x * (1.0 + x / (white**2))) / (1.0 + x)

    return np.clip(tone_mapped, 0.0, 1.0)


def apply_tone_mapping(
    hdr: np.ndarray,
    method: Literal['passthrough', 'aces', 'reinhard', 'exposure', 'hable', 'filmic'] = 'passthrough',
    exposure: float = 0.0,
    white_point: float = 2.0
) -> np.ndarray:
    """
    Apply tone mapping to HDR image based on selected method.
    All methods return linear data in [0, 1] range.

    Args:
        hdr: HDR image array (H, W, C) with float32 values
        method: Tone mapping method ('passthrough', 'aces', 'reinhard', 'exposure', 'hable', 'filmic')
        exposure: Exposure adjustment in EV stops
        white_point: White point for Reinhard (used with 'reinhard' method)

    Returns:
        LDR image array (H, W, C) with values in [0, 1]

    Raises:
        ValueError: If invalid tone mapping method is specified
    """
    if method == 'passthrough':
        # Apply exposure adjustment if specified
        if exposure != 0.0:
            hdr = hdr * (2.0 ** exposure)
        return passthrough_tonemap(hdr)

    elif method == 'aces':
        # Apply exposure adjustment before ACES
        if exposure != 0.0:
            hdr = hdr * (2.0 ** exposure)
        return aces_filmic_tonemap(hdr)

    elif method == 'reinhard':
        if exposure != 0.0:
            hdr = hdr * (2.0 ** exposure)
        return reinhard_tonemap(hdr, white_point)

    elif method == 'exposure':
        return exposure_tonemap(hdr, exposure)

    elif method == 'hable':
        if exposure != 0.0:
            hdr = hdr * (2.0 ** exposure)
        return hable_filmic_tonemap(hdr)

    elif method == 'filmic':
        if exposure != 0.0:
            hdr = hdr * (2.0 ** exposure)
        return blender_filmic_tonemap(hdr)

    else:
        raise ValueError(f"Invalid tone mapping method: {method}. "
                        f"Must be one of: 'passthrough', 'aces', 'reinhard', 'exposure', 'hable', 'filmic'")


def linear_to_srgb(linear: np.ndarray) -> np.ndarray:
    """
    Convert linear RGB to sRGB color space.

    Args:
        linear: Linear RGB image array with values in [0, 1]

    Returns:
        sRGB encoded image array with values in [0, 1]
    """
    # sRGB transfer function
    srgb = np.where(
        linear <= 0.0031308,
        linear * 12.92,
        1.055 * np.power(linear, 1.0 / 2.4) - 0.055
    )

    return np.clip(srgb, 0.0, 1.0)


def srgb_to_linear(srgb: np.ndarray) -> np.ndarray:
    """
    Convert sRGB to linear RGB color space.

    Args:
        srgb: sRGB encoded image array with values in [0, 1]

    Returns:
        Linear RGB image array with values in [0, 1]
    """
    # Inverse sRGB transfer function
    linear = np.where(
        srgb <= 0.04045,
        srgb / 12.92,
        np.power((srgb + 0.055) / 1.055, 2.4)
    )

    return linear
