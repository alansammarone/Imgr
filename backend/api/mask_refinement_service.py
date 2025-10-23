from enum import Enum

import cv2
import numpy as np
from scipy.ndimage import distance_transform_edt


class FeatheringMethod(str, Enum):
    """Feathering methods for mask refinement."""

    NONE = "none"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    COSINE = "cosine"
    SIGMOID = "sigmoid"
    EASE_OUT_POWER = "ease_out_power"
    EASE_OUT_EXP = "ease_out_exp"


def _feather(mask: np.ndarray, g, w) -> np.ndarray:
    """
    Generic feathering helper.

    mask: binary array (0/1 or bool), arbitrary shape.
    g:    profile function mapping t in [0,1] -> [0,1], with g(0)=1 (edge) and g(1)=0 (end of ramp).
    w:    feather width in pixels (hardcoded default 10).
    """
    M = mask.astype(bool)
    # Trivial edge cases
    if not M.any():
        return np.zeros_like(mask, dtype=np.float32)
    if M.all():
        return np.ones_like(mask, dtype=np.float32)

    # Outside-only Euclidean Distance Transform
    D_out = distance_transform_edt(~M)

    # Normalized distance across the ramp band
    t = np.clip(D_out / w, 0.0, 1.0)

    # Apply profile only outside and only within the w-band
    band = D_out < w
    ramp_vals = g(t)

    alpha = np.zeros_like(t, dtype=np.float32)
    alpha[M] = 1.0  # preserve interior exactly
    alpha[~M & band] = ramp_vals[~M & band]  # smooth skirt outside
    # Outside band remains 0.0
    return alpha


def feather_linear(mask: np.ndarray, width: float = 10.0) -> np.ndarray:
    """
    Linear profile: g(t) = 1 - t
    t=0 at boundary (value 1), t=1 at width w (value 0).
    """
    return _feather(mask, g=lambda t: 1.0 - t, w=width)


def feather_exp(mask: np.ndarray, width: float = 10.0) -> np.ndarray:
    """
    Exponential profile: g(t) = exp(-k * t)
    k: decay rate; larger k => faster falloff. Here k≈4.605 gives ~1% at t=1.
    """
    k = np.log(100.0)  # ≈4.605; g(1) ~ 0.01
    return _feather(mask, g=lambda t: np.exp(-k * t), w=width)


def feather_cos(mask: np.ndarray, width: float = 10.0) -> np.ndarray:
    """
    Cosine (C¹-smooth) profile: g(t) = (1 + cos(pi * t)) / 2
    Smooth at both ends with zero slope at t=0 and t=1.
    """
    return _feather(mask, g=lambda t: 0.5 * (1.0 + np.cos(np.pi * t)), w=width)


def feather_sigmoid(mask: np.ndarray, width: float = 10.0) -> np.ndarray:
    """
    Logistic profile centered at mid-ramp:
        s(t) = 1 / (1 + exp(a*(t - 0.5)))
    a: steepness; larger a => sharper mid transition. Here a=12 is a good default.
    Note: logistic never hits exact 0/1 at the ends; clamping by band keeps endpoints correct overall.
    """
    a = 12.0
    return _feather(mask, g=lambda t: 1.0 / (1.0 + np.exp(a * (t - 0.5))), w=width)


def feather_ease_out_power(mask: np.ndarray, width: float = 10.0) -> np.ndarray:
    """
    Power ease-out profile (convex, slow start, faster end):
      g(t) = 1 - t^p,  p>1
    p=3 gives a delayed falloff near the edge and steeper descent near t≈1.
    """
    p = 3.0
    return _feather(mask, g=lambda t: 1.0 - np.power(t, p), w=width)


def feather_ease_out_exp(mask: np.ndarray, width: float = 10.0) -> np.ndarray:
    """
    End-skewed exponential (convex near 0, accelerates near end):
      g(t) = exp(-k * t^q)
    q>1 delays decay; k sets level at t=1.
    q=3, k≈4.605 ⇒ g(1)≈0.01 (≈1% at ramp end).
    """
    q = 3.0
    k = np.log(100.0)
    return _feather(mask, g=lambda t: np.exp(-k * np.power(t, q)), w=width)


# ----# Smoothing


def _to_u8(mask: np.ndarray) -> np.ndarray:
    """bool/0-1 -> uint8 {0,255}, contiguous (what OpenCV wants)."""
    m = mask.astype(np.uint8) * 255
    return np.ascontiguousarray(m)


def _to_bool(m_u8: np.ndarray) -> np.ndarray:
    """uint8 {0..255} -> bool."""
    return m_u8 > 0


def _disk_kernel(r: int) -> np.ndarray:
    """Approximate Euclidean disk with an ellipse kernel of size (2r+1)."""
    k = 2 * r + 1
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))


# 1) Open→Close with disk SE ------------------------------------------


def smooth_open_close(mask: np.ndarray, r: int = 2) -> np.ndarray:
    """
    Opening removes outward spikes < r; closing fills inward notches < r.
    Uses ellipse kernel (≈ disk) for isotropy.
    """
    m = _to_u8(mask)
    se = _disk_kernel(r)
    opened = cv2.morphologyEx(m, cv2.MORPH_OPEN, se, iterations=1)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, se, iterations=1)
    return _to_bool(closed)


#
#
def apply_feathering(
    mask: np.ndarray, method: FeatheringMethod, width: float = 10.0
) -> np.ndarray:
    """
    Apply feathering to a mask using the specified method.

    Args:
        mask: Binary or float mask array (0/1 or bool), arbitrary shape
        method: FeatheringMethod enum specifying which feathering to apply
        width: Feather width in pixels (default 10.0)

    Returns:
        Float mask array with values in [0, 1]
    """

    mask = smooth_open_close(mask, r=4)

    if method == FeatheringMethod.NONE:
        return mask.astype(np.float32)
    elif method == FeatheringMethod.LINEAR:
        return feather_linear(mask, width)
    elif method == FeatheringMethod.EXPONENTIAL:
        return feather_exp(mask, width)
    elif method == FeatheringMethod.COSINE:
        return feather_cos(mask, width)
    elif method == FeatheringMethod.SIGMOID:
        return feather_sigmoid(mask, width)
    elif method == FeatheringMethod.EASE_OUT_POWER:
        return feather_ease_out_power(mask, width)
    elif method == FeatheringMethod.EASE_OUT_EXP:
        return feather_ease_out_exp(mask, width)
    else:
        raise ValueError(f"Unknown feathering method: {method}")


# --- Example usage ---
# alpha = feather_linear(binary_mask)
# alpha = feather_exp(binary_mask)
# alpha = feather_cos(binary_mask)
# alpha = feather_sigmoid(binary_mask)
# alpha = apply_feathering(binary_mask, FeatheringMethod.SIGMOID)
