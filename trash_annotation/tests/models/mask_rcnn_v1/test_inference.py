from unittest.mock import MagicMock, patch

import numpy as np
from PIL import Image
import pytest

# ── helpers ───────────────────────────────────────────────────────────────────


def make_image_file(tmp_path, width: int = 640, height: int = 480, name: str = "test.jpg") -> str:
    img = Image.fromarray(np.random.randint(0, 256, (height, width, 3), dtype=np.uint8))
    path = tmp_path / name
    img.save(path)
    return str(path)


def make_fake_session_output(
    max_detections: int = 100,
    n_real: int = 5,
    h: int = 1024,
    w: int = 1280,
) -> tuple:
    boxes = np.random.rand(max_detections, 4).astype(np.float32)
    scores = np.random.rand(max_detections).astype(np.float32)
    labels = np.random.randint(1, 18, max_detections).astype(np.int64)
    masks = np.random.rand(max_detections, h, w).astype(np.float32)
    n_det = np.array(n_real)  # 0-d scalar, as ONNX runtime returns it
    return boxes, scores, labels, masks, n_det


# ── preprocess ────────────────────────────────────────────────────────────────


class TestPreprocess:
    def test_output_shape(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import preprocess

        result = preprocess(make_image_file(tmp_path), size=(1024, 1280))
        assert result.shape == (3, 1024, 1280)

    def test_output_dtype(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import preprocess

        result = preprocess(make_image_file(tmp_path))
        assert result.dtype == np.float32

    def test_values_in_unit_range(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import preprocess

        result = preprocess(make_image_file(tmp_path))
        assert result.min() >= 0.0
        assert result.max() <= 1.0

    def test_custom_size(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import preprocess

        result = preprocess(make_image_file(tmp_path), size=(512, 768))
        assert result.shape == (3, 512, 768)

    def test_channel_first_layout(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import preprocess

        result = preprocess(make_image_file(tmp_path), size=(64, 64))
        assert result.shape[0] == 3

    def test_pure_black_image_is_zero(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import preprocess

        img = Image.fromarray(np.zeros((100, 100, 3), dtype=np.uint8))
        path = str(tmp_path / "black.jpg")
        img.save(path)

        result = preprocess(path)
        assert result.max() == pytest.approx(0.0, abs=1e-3)

    def test_pure_white_image_is_one(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import preprocess

        img = Image.fromarray(np.full((100, 100, 3), 255, dtype=np.uint8))
        path = str(tmp_path / "white.jpg")
        img.save(path)

        result = preprocess(path)
        assert result.min() == pytest.approx(1.0, abs=1e-3)

    def test_rgba_image_converts_to_rgb(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import preprocess

        img = Image.fromarray(np.random.randint(0, 256, (100, 100, 4), dtype=np.uint8), mode="RGBA")
        path = str(tmp_path / "rgba.png")
        img.save(path)

        result = preprocess(path, size=(64, 64))
        assert result.shape == (3, 64, 64)


# ── load_onnx_session ─────────────────────────────────────────────────────────


class TestLoadOnnxSession:
    def test_gpu_providers_order(self):
        from trash_annotation.models.mask_rcnn_v1.inference import load_onnx_session

        with patch("onnxruntime.InferenceSession") as mock_session:
            load_onnx_session("model.onnx", use_gpu=True)
            providers = mock_session.call_args.kwargs["providers"]
            assert providers[0] == "CUDAExecutionProvider"
            assert "CPUExecutionProvider" in providers

    def test_cpu_only_providers(self):
        from trash_annotation.models.mask_rcnn_v1.inference import load_onnx_session

        with patch("onnxruntime.InferenceSession") as mock_session:
            load_onnx_session("model.onnx", use_gpu=False)
            providers = mock_session.call_args.kwargs["providers"]
            assert providers == ["CPUExecutionProvider"]

    def test_returns_session_object(self):
        from trash_annotation.models.mask_rcnn_v1.inference import load_onnx_session

        with patch("onnxruntime.InferenceSession") as mock_session:
            fake = MagicMock()
            mock_session.return_value = fake
            assert load_onnx_session("model.onnx") is fake

    def test_passes_model_path(self):
        from trash_annotation.models.mask_rcnn_v1.inference import load_onnx_session

        with patch("onnxruntime.InferenceSession") as mock_session:
            load_onnx_session("/some/path/model.onnx", use_gpu=False)
            assert mock_session.call_args[0][0] == "/some/path/model.onnx"


# ── predict ───────────────────────────────────────────────────────────────────


class TestPredict:
    def _make_session(self, n_real: int = 5) -> MagicMock:
        session = MagicMock()
        session.run.return_value = make_fake_session_output(n_real=n_real)
        return session

    def test_output_keys(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import predict

        result = predict(self._make_session(), make_image_file(tmp_path))
        assert set(result.keys()) == {"boxes", "scores", "labels", "masks"}

    def test_slices_by_n_det(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import predict

        n_real = 7
        result = predict(self._make_session(n_real=n_real), make_image_file(tmp_path))

        assert result["boxes"].shape[0] == n_real
        assert result["scores"].shape[0] == n_real
        assert result["labels"].shape[0] == n_real
        assert result["masks"].shape[0] == n_real

    def test_zero_detections(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import predict

        result = predict(self._make_session(n_real=0), make_image_file(tmp_path))
        assert result["boxes"].shape[0] == 0

    def test_boxes_shape(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import predict

        n_real = 4
        result = predict(self._make_session(n_real=n_real), make_image_file(tmp_path))
        assert result["boxes"].shape == (n_real, 4)

    def test_session_called_with_image_key(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import predict

        session = self._make_session()
        predict(session, make_image_file(tmp_path))
        assert "image" in session.run.call_args[0][1]

    def test_image_passed_to_session_is_float32(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import predict

        session = self._make_session()
        predict(session, make_image_file(tmp_path))

        image_arg = session.run.call_args[0][1]["image"]
        assert image_arg.dtype == np.float32

    def test_max_detections_not_exceeded(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import predict

        result = predict(self._make_session(n_real=100), make_image_file(tmp_path))
        assert result["boxes"].shape[0] <= 100


# ── draw_predictions ──────────────────────────────────────────────────────────

ID_TO_NAME = {1: "Can", 2: "Bottle", 3: "Cup"}


def make_predictions(n: int = 3, score: float = 0.9, h: int = 1024, w: int = 1280) -> dict:
    """Return fake predictions with boxes inside the output image."""
    boxes = np.array([[10, 10, 100, 100]] * n, dtype=np.float32)
    scores = np.full(n, score, dtype=np.float32)
    labels = np.ones(n, dtype=np.int64)
    masks = np.zeros((n, h, w), dtype=np.float32)
    masks[:, 10:100, 10:100] = 1.0  # small non-zero region
    return {"boxes": boxes, "scores": scores, "labels": labels, "masks": masks}


class TestDrawPredictions:
    def test_returns_pil_image(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import draw_predictions

        result = draw_predictions(make_image_file(tmp_path), make_predictions(), ID_TO_NAME)
        assert isinstance(result, Image.Image)

    def test_output_size_is_fixed(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import draw_predictions

        # function resizes output to (1280, 1024) regardless of input
        result = draw_predictions(make_image_file(tmp_path), make_predictions(), ID_TO_NAME)
        assert result.size == (1280, 1024)

    def test_output_is_rgb(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import draw_predictions

        result = draw_predictions(make_image_file(tmp_path), make_predictions(), ID_TO_NAME)
        assert result.mode == "RGB"

    def test_boxes_are_drawn_on_blank_image(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import draw_predictions

        # pure white source image — any box drawing will change pixels
        img = Image.fromarray(np.full((100, 100, 3), 255, dtype=np.uint8))
        path = str(tmp_path / "white.jpg")
        img.save(path)

        result = draw_predictions(path, make_predictions(n=1), ID_TO_NAME)
        result_arr = np.array(result)

        # at least some pixels must differ from pure white
        assert not np.all(result_arr == 255)

    def test_no_detections_returns_valid_image(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import draw_predictions

        empty = {
            "boxes": np.empty((0, 4)),
            "scores": np.array([]),
            "labels": np.array([]),
            "masks": np.empty((0, 1024, 1280)),
        }
        result = draw_predictions(make_image_file(tmp_path), empty, ID_TO_NAME)

        assert isinstance(result, Image.Image)
        assert result.size == (1280, 1024)

    def test_detections_below_threshold_not_drawn(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import draw_predictions

        img = Image.fromarray(np.full((100, 100, 3), 255, dtype=np.uint8))
        path = str(tmp_path / "white.jpg")
        img.save(path)

        low_score = make_predictions(score=0.05)
        result_low = draw_predictions(path, low_score, ID_TO_NAME, score_thresh=0.5)
        result_high = draw_predictions(
            path, make_predictions(score=0.9), ID_TO_NAME, score_thresh=0.5
        )

        arr_low = np.array(result_low)
        arr_high = np.array(result_high)

        # high-score image must have more non-white pixels than low-score
        non_white_low = np.sum(arr_low < 255)
        non_white_high = np.sum(arr_high < 255)
        assert non_white_high > non_white_low

    def test_unknown_label_falls_back_to_string(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import draw_predictions

        preds = make_predictions(n=1)
        preds["labels"] = np.array([999], dtype=np.int64)  # not in id_to_name

        # should not raise
        result = draw_predictions(make_image_file(tmp_path), preds, ID_TO_NAME)
        assert isinstance(result, Image.Image)

    def test_show_masks_changes_output(self, tmp_path):
        from trash_annotation.models.mask_rcnn_v1.inference import draw_predictions

        img = Image.fromarray(np.full((100, 100, 3), 200, dtype=np.uint8))
        path = str(tmp_path / "grey.jpg")
        img.save(path)

        preds = make_predictions(n=1)
        result_no_mask = draw_predictions(path, preds, ID_TO_NAME, show_masks=False)
        result_with_mask = draw_predictions(path, preds, ID_TO_NAME, show_masks=True)

        arr_no = np.array(result_no_mask)
        arr_with = np.array(result_with_mask)

        assert not np.array_equal(arr_no, arr_with)
