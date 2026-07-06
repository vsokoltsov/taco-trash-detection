from unittest.mock import patch

import numpy as np
from PIL import Image

from trash_annotation.models.yolo_v8.inference import (
    YoloDetector,
    preprocess,
)


class FakeInput:
    name = "images"


class FakeSession:
    def __init__(self, output: np.ndarray):
        self.output = output
        self.feed = None

    def get_inputs(self):
        return [FakeInput()]

    def run(self, _output_names, feed):
        self.feed = feed
        return [self.output]


def make_image(path, size=(200, 100)):
    Image.new("RGB", size, "white").save(path)
    return path


def test_load_onnx_session_uses_cpu_provider():
    with patch("onnxruntime.InferenceSession") as constructor:
        YoloDetector("model.onnx", use_gpu=False)

    constructor.assert_called_once_with(
        "model.onnx",
        providers=["CPUExecutionProvider"],
    )


def test_preprocess_letterboxes_image(tmp_path):
    path = make_image(tmp_path / "image.jpg")

    tensor, scale, left, top, original_size = preprocess(path)

    assert tensor.shape == (1, 3, 1024, 1024)
    assert tensor.dtype == np.float32
    assert scale == 5.12
    assert left == 0
    assert top == 256
    assert original_size == (200, 100)


def test_predict_restores_coordinates_and_zero_based_labels(tmp_path):
    path = make_image(tmp_path / "image.jpg")
    # Original box [20, 10, 180, 90] transformed by scale=5.12 and pad_y=256.
    output = np.array(
        [[[102.4, 307.2, 921.6, 716.8, 0.9, 0.0]]],
        dtype=np.float32,
    )
    session = FakeSession(output)
    with patch(
        "trash_annotation.models.yolo_v8.inference.load_onnx_session",
        return_value=session,
    ):
        detector = YoloDetector("model.onnx")

    result = detector.predict(path, score_thresh=0.2)

    np.testing.assert_allclose(result["boxes"], [[20, 10, 180, 90]], atol=1e-4)
    np.testing.assert_allclose(result["scores"], [0.9])
    np.testing.assert_array_equal(result["labels"], [0])
    assert session.feed["images"].shape == (1, 3, 1024, 1024)


def test_predict_filters_scores_and_padding_rows(tmp_path):
    path = make_image(tmp_path / "image.jpg")
    output = np.array(
        [
            [
                [102.4, 307.2, 921.6, 716.8, 0.8, 1.0],
                [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                [100.0, 300.0, 200.0, 400.0, 0.1, 2.0],
            ]
        ],
        dtype=np.float32,
    )

    with patch(
        "trash_annotation.models.yolo_v8.inference.load_onnx_session",
        return_value=FakeSession(output),
    ):
        detector = YoloDetector("model.onnx")

    result = detector.predict(path, score_thresh=0.2)

    assert result["boxes"].shape == (1, 4)
    np.testing.assert_array_equal(result["labels"], [1])


def test_draw_predictions_preserves_original_image_size(tmp_path):
    path = make_image(tmp_path / "image.jpg")
    predictions = {
        "boxes": np.array([[20, 10, 180, 90]], dtype=np.float32),
        "scores": np.array([0.9], dtype=np.float32),
        "labels": np.array([0], dtype=np.int64),
    }
    with patch(
        "trash_annotation.models.yolo_v8.inference.load_onnx_session",
        return_value=FakeSession(np.empty((1, 0, 6), dtype=np.float32)),
    ):
        detector = YoloDetector("model.onnx")

    result = detector.draw_predictions(
        path,
        predictions,
        show_masks=True,
    )

    assert result.size == (200, 100)
