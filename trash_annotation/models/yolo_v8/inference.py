"""ONNX Runtime inference helpers for the YOLOv8 detector."""

from pathlib import Path
from typing import cast

import numpy as np
import onnxruntime as ort
from PIL import Image, ImageDraw, ImageOps

from trash_annotation.protocols import Detector

IMAGE_SIZE = 1024

YOLO_ID_TO_NAME = {
    0: "Aluminium foil",
    1: "Can",
    2: "Carton",
    3: "Cup",
    4: "Glass bottle",
    5: "Metal bottle cap",
    6: "Other",
    7: "Paper",
    8: "Plastic bottle",
    9: "Plastic bottle cap",
    10: "Plastic container",
    11: "Plastic film",
    12: "Plastic lid",
    13: "Pop tab",
    14: "Straw",
    15: "Styrofoam piece",
    16: "Wrapper",
}

# Keep one stable color for each YOLO class.
_PALETTE = [
    (220, 50, 50),
    (50, 150, 220),
    (50, 200, 100),
    (200, 150, 50),
    (150, 50, 200),
    (50, 200, 200),
    (200, 50, 150),
    (100, 180, 80),
    (180, 100, 80),
    (80, 100, 180),
    (180, 80, 100),
    (100, 80, 180),
    (80, 180, 100),
    (160, 160, 50),
    (50, 160, 160),
    (160, 50, 160),
    (120, 120, 120),
]


def _label_color(label_id: int) -> tuple[int, int, int]:
    """Return a stable display color for a zero-based class ID."""
    return _PALETTE[label_id % len(_PALETTE)]


def load_onnx_session(model_path: str | Path, use_gpu: bool = True) -> ort.InferenceSession:
    """Create an ONNX Runtime session for an exported YOLOv8 model.

    Args:
        model_path: Path to the YOLOv8 ONNX model exported with ``nms=True``.
        use_gpu: Prefer CUDA when available, with CPU as a fallback.

    Returns:
        A ready-to-use ONNX Runtime inference session.
    """
    providers = (
        ["CUDAExecutionProvider", "CPUExecutionProvider"] if use_gpu else ["CPUExecutionProvider"]
    )
    return ort.InferenceSession(str(model_path), providers=providers)


def preprocess(
    image_path: str | Path,
    image_size: int = IMAGE_SIZE,
) -> tuple[np.ndarray, float, int, int, tuple[int, int]]:
    """Load and letterbox an image using YOLO-compatible preprocessing.

    Args:
        image_path: Path to an image supported by Pillow.
        image_size: Fixed square ONNX input size.

    Returns:
        A tuple containing the ``[1, 3, H, W]`` float32 tensor, resize scale,
        left padding, top padding, and original ``(width, height)``.
    """
    with Image.open(image_path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")

    original_width, original_height = image.size
    scale = min(image_size / original_width, image_size / original_height)

    resized_width = round(original_width * scale)
    resized_height = round(original_height * scale)
    resized = image.resize((resized_width, resized_height), Image.Resampling.BILINEAR)

    horizontal_padding = (image_size - resized_width) / 2
    vertical_padding = (image_size - resized_height) / 2
    left = round(horizontal_padding - 0.1)
    top = round(vertical_padding - 0.1)

    canvas = Image.new("RGB", (image_size, image_size), (114, 114, 114))
    canvas.paste(resized, (left, top))

    tensor = np.asarray(canvas, dtype=np.float32) / 255.0
    tensor = np.ascontiguousarray(tensor.transpose(2, 0, 1)[None])

    return tensor, scale, left, top, (original_width, original_height)


def _normalize_nms_output(output: np.ndarray) -> np.ndarray:
    """Normalize embedded-NMS output to an ``[N, 6]`` detection matrix."""
    detections = np.asarray(output)

    if detections.ndim == 3 and detections.shape[0] == 1:
        detections = detections[0]

    if detections.ndim != 2:
        raise ValueError(
            "Expected YOLO ONNX output with shape [1, N, 6]; "
            f"received {detections.shape}. Export the model with nms=True."
        )

    if detections.shape[1] != 6 and detections.shape[0] == 6:
        detections = detections.T

    if detections.shape[1] != 6:
        raise ValueError(
            "Expected six values per detection (x1, y1, x2, y2, score, class); "
            f"received {detections.shape}. Export the model with nms=True."
        )

    return detections


def _predict(
    session: ort.InferenceSession,
    image_path: str | Path,
    score_thresh: float = 0.20,
) -> dict[str, np.ndarray]:
    """Run YOLOv8 inference and return the route-compatible prediction format.

    The ONNX graph is expected to contain NMS and return rows in
    ``[x1, y1, x2, y2, score, class_id]`` format. YOLO class IDs are zero-based;
    the returned labels therefore remain zero-based and are resolved through
    :data:`YOLO_ID_TO_NAME`.

    Args:
        session: Loaded ONNX Runtime session.
        image_path: Path to the uploaded image written by the API route.
        score_thresh: Minimum score retained by the API. This can only make
            filtering stricter than the confidence threshold embedded during
            ONNX export.

    Returns:
        A dictionary containing ``boxes`` as ``[N, 4]`` original-image xyxy
        coordinates, ``scores`` as ``[N]``, and zero-based ``labels`` as
        ``[N]``.
    """
    tensor, scale, pad_x, pad_y, original_size = preprocess(image_path)
    input_name = session.get_inputs()[0].name
    output = cast(np.ndarray, session.run(None, {input_name: tensor})[0])
    detections = _normalize_nms_output(output)

    scores = detections[:, 4].astype(np.float32, copy=False)
    keep = np.isfinite(scores) & (scores >= score_thresh)
    detections = detections[keep]

    if len(detections) == 0:
        return {
            "boxes": np.empty((0, 4), dtype=np.float32),
            "scores": np.empty((0,), dtype=np.float32),
            "labels": np.empty((0,), dtype=np.int64),
        }

    boxes = detections[:, :4].astype(np.float32, copy=True)
    boxes[:, [0, 2]] = (boxes[:, [0, 2]] - pad_x) / scale
    boxes[:, [1, 3]] = (boxes[:, [1, 3]] - pad_y) / scale

    original_width, original_height = original_size
    boxes[:, [0, 2]] = boxes[:, [0, 2]].clip(0, original_width)
    boxes[:, [1, 3]] = boxes[:, [1, 3]].clip(0, original_height)

    valid_boxes = (boxes[:, 2] > boxes[:, 0]) & (boxes[:, 3] > boxes[:, 1])

    return {
        "boxes": boxes[valid_boxes],
        "scores": detections[valid_boxes, 4].astype(np.float32, copy=False),
        "labels": detections[valid_boxes, 5].astype(np.int64),
    }


def _draw_predictions(
    image_path: str | Path,
    predictions: dict[str, np.ndarray],
    id_to_name: dict[int, str],
    score_thresh: float = 0.20,
    show_masks: bool = False,
) -> Image.Image:
    """Render YOLO bounding boxes using the interface expected by the route.

    Args:
        image_path: Path to the original uploaded image.
        predictions: Decoded YOLO predictions.
        id_to_name: Zero-based class ID to display-name mapping.
        score_thresh: Minimum confidence score to draw.
        show_masks: Accepted for route compatibility. YOLOv8 detection models
            do not produce masks, so this option has no effect.

    Returns:
        A copy of the original image with labeled bounding boxes.
    """
    del show_masks

    with Image.open(image_path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")

    draw = ImageDraw.Draw(image)
    for box, score, label in zip(
        predictions["boxes"],
        predictions["scores"],
        predictions["labels"],
        strict=False,
    ):
        if score < score_thresh:
            continue

        label_id = int(label)
        color = _label_color(label_id)
        name = id_to_name.get(label_id, str(label_id))
        text = f"{name} {score:.2f}"
        x1, y1, x2, y2 = (float(value) for value in box)

        draw.rectangle((x1, y1, x2, y2), outline=color, width=3)
        text_box = draw.textbbox((x1, y1), text)
        text_width = text_box[2] - text_box[0]
        text_height = text_box[3] - text_box[1]
        text_top = max(0.0, y1 - text_height - 6)
        draw.rectangle(
            (x1, text_top, x1 + text_width + 6, text_top + text_height + 6),
            fill=color,
        )
        draw.text((x1 + 3, text_top + 3), text, fill="white")

    return image


class YoloDetector(Detector):
    """YOLOv8 ONNX detector with preprocessing and rendering encapsulated."""

    supports_masks = False

    def __init__(
        self,
        model_path: str | Path,
        use_gpu: bool = True,
        id_to_name: dict[int, str] | None = None,
    ) -> None:
        self.session = load_onnx_session(model_path, use_gpu=use_gpu)
        self.id_to_name = id_to_name or YOLO_ID_TO_NAME.copy()

    def predict(
        self,
        image_path: str | Path,
        score_thresh: float = 0.20,
    ) -> dict[str, np.ndarray]:
        """Run YOLOv8 inference for one image."""
        return _predict(self.session, image_path, score_thresh=score_thresh)

    def draw_predictions(
        self,
        image_path: str | Path,
        predictions: dict[str, np.ndarray],
        score_thresh: float = 0.20,
        show_masks: bool = False,
    ) -> Image.Image:
        """Draw YOLOv8 bounding boxes on the original image."""
        return _draw_predictions(
            image_path,
            predictions,
            self.id_to_name,
            score_thresh=score_thresh,
            show_masks=show_masks,
        )
