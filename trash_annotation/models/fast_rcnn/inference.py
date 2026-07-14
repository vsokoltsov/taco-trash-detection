"""ONNX Runtime inference helpers for the exported Faster R-CNN detector."""

from pathlib import Path

import numpy as np
import onnxruntime as ort
from PIL import Image, ImageDraw, ImageOps

from trash_annotation.protocols import Detector

IMAGE_SIZE = 1024

FAST_RCNN_ID_TO_NAME = {
    1: "Bottle",
    2: "Bottle cap",
    3: "Can",
    4: "Carton",
    5: "Cigarette",
    6: "Cup",
    7: "Flexible plastic",
    8: "Straw",
    9: "Unlabeled litter",
}

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
]


def _label_color(label_id: int) -> tuple[int, int, int]:
    """Return a stable display color for a one-based Faster R-CNN class ID."""
    return _PALETTE[(label_id - 1) % len(_PALETTE)]


def load_onnx_session(model_path: str | Path, use_gpu: bool = True) -> ort.InferenceSession:
    """Create an ONNX Runtime session for the exported Faster R-CNN model."""
    providers = (
        ["CUDAExecutionProvider", "CPUExecutionProvider"] if use_gpu else ["CPUExecutionProvider"]
    )
    return ort.InferenceSession(str(model_path), providers=providers)


def preprocess(
    image_path: str | Path,
    image_size: int = IMAGE_SIZE,
) -> tuple[np.ndarray, tuple[int, int]]:
    """Resize an image to the fixed Faster R-CNN ONNX export resolution.

    Args:
        image_path: Path to an image supported by Pillow.
        image_size: Fixed square ONNX input size.

    Returns:
        A tuple with a ``[1, 3, H, W]`` float32 tensor and original image size.
    """
    with Image.open(image_path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")

    original_size = image.size
    image = image.resize((image_size, image_size), Image.Resampling.BILINEAR)

    tensor = np.asarray(image, dtype=np.float32) / 255.0
    tensor = np.ascontiguousarray(tensor.transpose(2, 0, 1)[None])

    return tensor, original_size


def _predict(
    session: ort.InferenceSession,
    image_path: str | Path,
    score_thresh: float = 0.20,
    image_size: int = IMAGE_SIZE,
) -> dict[str, np.ndarray]:
    """Run Faster R-CNN ONNX inference for one image.

    The exported graph is expected to return three outputs:
    ``boxes`` as ``[N, 4]``, ``labels`` as ``[N]``, and ``scores`` as ``[N]``.
    Labels are one-based because they come from TorchVision Faster R-CNN.
    """
    tensor, _original_size = preprocess(image_path, image_size=image_size)
    input_name = session.get_inputs()[0].name
    boxes, labels, scores = session.run(None, {input_name: tensor})

    boxes = np.asarray(boxes, dtype=np.float32)
    labels = np.asarray(labels, dtype=np.int64)
    scores = np.asarray(scores, dtype=np.float32)

    if boxes.ndim == 3 and boxes.shape[0] == 1:
        boxes = boxes[0]
    if labels.ndim == 2 and labels.shape[0] == 1:
        labels = labels[0]
    if scores.ndim == 2 and scores.shape[0] == 1:
        scores = scores[0]

    keep = np.isfinite(scores) & (scores >= score_thresh)

    boxes = boxes[keep]
    labels = labels[keep]
    scores = scores[keep]

    valid_boxes = (boxes[:, 2] > boxes[:, 0]) & (boxes[:, 3] > boxes[:, 1])

    return {
        "boxes": boxes[valid_boxes],
        "scores": scores[valid_boxes],
        "labels": labels[valid_boxes],
    }


def _draw_predictions(
    image_path: str | Path,
    predictions: dict[str, np.ndarray],
    id_to_name: dict[int, str],
    score_thresh: float = 0.20,
    image_size: int = IMAGE_SIZE,
    show_masks: bool = False,
) -> Image.Image:
    """Draw Faster R-CNN detections on the resized ONNX input image."""
    del show_masks

    with Image.open(image_path) as source:
        image = ImageOps.exif_transpose(source).convert("RGB")

    image = image.resize((image_size, image_size), Image.Resampling.BILINEAR)
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


class FastRcnnDetector(Detector):
    """Faster R-CNN ONNX detector with preprocessing and rendering."""

    supports_masks = False

    def __init__(
        self,
        model_path: str | Path,
        use_gpu: bool = True,
        image_size: int = IMAGE_SIZE,
    ) -> None:
        self.session = load_onnx_session(model_path, use_gpu=use_gpu)
        self.id_to_name = FAST_RCNN_ID_TO_NAME.copy()
        self.image_size = image_size

    def predict(
        self,
        image_path: str | Path,
        score_thresh: float = 0.20,
    ) -> dict[str, np.ndarray]:
        """Run Faster R-CNN inference for one image."""
        return _predict(
            self.session,
            image_path,
            score_thresh=score_thresh,
            image_size=self.image_size,
        )

    def draw_predictions(
        self,
        image_path: str | Path,
        predictions: dict[str, np.ndarray],
        score_thresh: float = 0.20,
        show_masks: bool = False,
    ) -> Image.Image:
        """Draw Faster R-CNN bounding boxes on the resized input image."""
        return _draw_predictions(
            image_path,
            predictions,
            self.id_to_name,
            score_thresh=score_thresh,
            image_size=self.image_size,
            show_masks=show_masks,
        )
