from unittest.mock import patch

import numpy as np
from PIL import Image

from trash_annotation.models.fast_rcnn.inference import (
    FastRcnnDetector,
    preprocess,
)


class FakeInput:
    name = "images"


class FakeSession:
    def __init__(
        self,
        boxes: np.ndarray,
        labels: np.ndarray,
        scores: np.ndarray,
    ) -> None:
        self.boxes = boxes
        self.labels = labels
        self.scores = scores
        self.feed = None

    def get_inputs(self):
        return [FakeInput()]

    def run(self, _output_names, feed):
        self.feed = feed
        return [self.boxes, self.labels, self.scores]


def make_image(path, size=(200, 100)):
    Image.new("RGB", size, "white").save(path)
    return path


def test_load_onnx_session_uses_cpu_provider():
    with patch("onnxruntime.InferenceSession") as constructor:
        FastRcnnDetector("model.onnx", use_gpu=False)

    constructor.assert_called_once_with(
        "model.onnx",
        providers=["CPUExecutionProvider"],
    )


def test_preprocess_resizes_to_fixed_input_size(tmp_path):
    path = make_image(tmp_path / "image.jpg")

    tensor, original_size = preprocess(path)

    assert tensor.shape == (1, 3, 1024, 1024)
    assert tensor.dtype == np.float32
    assert original_size == (200, 100)


def test_predict_reads_boxes_labels_scores_and_keeps_one_based_labels(tmp_path):
    path = make_image(tmp_path / "image.jpg")
    session = FakeSession(
        boxes=np.array([[10, 20, 100, 120]], dtype=np.float32),
        labels=np.array([3], dtype=np.int64),
        scores=np.array([0.9], dtype=np.float32),
    )

    with patch(
        "trash_annotation.models.fast_rcnn.inference.load_onnx_session",
        return_value=session,
    ):
        detector = FastRcnnDetector("model.onnx")

    result = detector.predict(path, score_thresh=0.2)

    np.testing.assert_allclose(result["boxes"], [[10, 20, 100, 120]], atol=1e-4)
    np.testing.assert_array_equal(result["labels"], [3])
    np.testing.assert_allclose(result["scores"], [0.9])
    assert detector.id_to_name[3] == "Can"
    assert session.feed is not None
    assert session.feed["images"].shape == (1, 3, 1024, 1024)


def test_predict_filters_low_scores_and_invalid_boxes(tmp_path):
    path = make_image(tmp_path / "image.jpg")
    session = FakeSession(
        boxes=np.array(
            [
                [10, 20, 100, 120],
                [10, 20, 100, 120],
                [50, 50, 40, 60],
            ],
            dtype=np.float32,
        ),
        labels=np.array([1, 2, 3], dtype=np.int64),
        scores=np.array([0.8, 0.1, 0.9], dtype=np.float32),
    )

    with patch(
        "trash_annotation.models.fast_rcnn.inference.load_onnx_session",
        return_value=session,
    ):
        detector = FastRcnnDetector("model.onnx")

    result = detector.predict(path, score_thresh=0.2)

    assert result["boxes"].shape == (1, 4)
    np.testing.assert_array_equal(result["labels"], [1])


def test_draw_predictions_returns_fixed_size_image(tmp_path):
    path = make_image(tmp_path / "image.jpg")
    session = FakeSession(
        boxes=np.empty((0, 4), dtype=np.float32),
        labels=np.empty((0,), dtype=np.int64),
        scores=np.empty((0,), dtype=np.float32),
    )

    with patch(
        "trash_annotation.models.fast_rcnn.inference.load_onnx_session",
        return_value=session,
    ):
        detector = FastRcnnDetector("model.onnx")

    predictions = {
        "boxes": np.array([[10, 20, 100, 120]], dtype=np.float32),
        "scores": np.array([0.9], dtype=np.float32),
        "labels": np.array([3], dtype=np.int64),
    }

    result = detector.draw_predictions(path, predictions, show_masks=True)

    assert isinstance(result, Image.Image)
    assert result.size == (1024, 1024)
