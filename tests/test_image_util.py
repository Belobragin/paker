import numpy as np
import tensorflow as tf

from prutil import (
    RESNET50_INPUT_DIMENSIONS,
    from_tensor_to_numpy_for_cv2image,
    prepare_image_resnet50,
)


def test_prepare_image_resnet50_resizes_and_adds_batch_axis():
    image = np.zeros((480, 640, 3), dtype=np.uint8)
    prepared = prepare_image_resnet50(image)
    assert prepared.shape == (1, *RESNET50_INPUT_DIMENSIONS, 3)


def test_prepare_image_resnet50_keeps_pixel_values_of_a_flat_image():
    image = np.full((100, 100, 3), 77, dtype=np.uint8)
    assert (prepare_image_resnet50(image) == 77).all()


def test_from_tensor_to_numpy_returns_none_for_none():
    assert from_tensor_to_numpy_for_cv2image(None) is None


def test_from_tensor_to_numpy_clips_to_uint8_and_swaps_channels_to_bgr():
    rgb = np.zeros((1, 2, 2, 3), dtype=np.float32)
    rgb[..., 0], rgb[..., 1], rgb[..., 2] = 10, 20, 300
    out = from_tensor_to_numpy_for_cv2image(tf.constant(rgb))
    assert out.dtype == np.uint8
    assert out.shape == (2, 2, 3)
    assert out[0, 0].tolist() == [255, 20, 10]


def test_from_tensor_to_numpy_scales_range_to_0_255():
    values = np.linspace(-1.0, 1.0, 12, dtype=np.float32).reshape(1, 2, 2, 3)
    out = from_tensor_to_numpy_for_cv2image(tf.constant(values), from_1_to_255=True)
    assert out.min() == 0
    assert out.max() == 255
