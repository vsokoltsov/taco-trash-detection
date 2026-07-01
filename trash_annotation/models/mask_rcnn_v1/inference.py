import numpy as np
import onnxruntime as ort
from PIL import Image, ImageDraw

# ── colour palette — one consistent colour per class label ────────────────────
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
    return _PALETTE[(label_id - 1) % len(_PALETTE)]


def load_onnx_session(model_path, use_gpu=True) -> ort.InferenceSession:
    """Create an ONNX Runtime inference session.

    Args:
        model_path (str): Path to the exported ``.onnx`` model file.
        use_gpu (bool): If ``True``, attempts to use ``CUDAExecutionProvider``
            before falling back to CPU. Defaults to ``True``.

    Returns:
        onnxruntime.InferenceSession: Ready-to-use inference session.
    """

    providers = (
        ["CUDAExecutionProvider", "CPUExecutionProvider"] if use_gpu else ["CPUExecutionProvider"]
    )
    return ort.InferenceSession(model_path, providers=providers)


def preprocess(image_path, size=(1024, 1280)):
    """Load and resize an image to the fixed ONNX export resolution.

    Opens the image, resizes to ``(height, width)`` without preserving aspect
    ratio, normalises pixel values to ``[0, 1]``, and returns a CHW float32
    array ready to pass to the ONNX session.

    Args:
        image_path (str): Path to the input image file.
        size (tuple[int, int]): Target ``(height, width)`` in pixels. Must
            match the dummy input size used during ONNX export.
            Defaults to ``(1024, 1280)``.

    Returns:
        numpy.ndarray: Float32 array of shape ``[3, H, W]`` with values in
        ``[0.0, 1.0]``.
    """

    img = Image.open(image_path).convert("RGB")
    img = img.resize((size[1], size[0]))
    arr = np.array(img, dtype=np.float32) / 255.0  # [H, W, 3]
    arr = arr.transpose(2, 0, 1)  # [3, H, W]
    return arr


def predict(session, image_path, score_thresh=0.20):
    """Run inference on a single image using the ONNX Runtime session.

    Preprocesses the image, runs the ONNX model, and returns only the
    detections that were populated by the model (up to ``max_detections``).

    Args:
        session (onnxruntime.InferenceSession): Loaded ONNX Runtime session.
        image_path (str): Path to the input image file.
        score_thresh (float): Minimum confidence score. Detections below this
            threshold were already filtered during export; this value should
            match ``model.roi_heads.score_thresh`` used at export time.
            Defaults to ``0.20``.

    Returns:
        dict: Dictionary with keys:
            - ``boxes``  (numpy.ndarray): ``[N, 4]`` xyxy bounding boxes.
            - ``scores`` (numpy.ndarray): ``[N]`` confidence scores.
            - ``labels`` (numpy.ndarray): ``[N]`` integer class IDs.
            - ``masks``  (numpy.ndarray): ``[N, H, W]`` float instance masks.
    """

    image = preprocess(image_path)  # [3, H, W]

    boxes, scores, labels, masks, n_det = session.run(None, {"image": image})

    n = int(n_det)
    return {
        "boxes": boxes[:n],  # [N, 4]  xyxy
        "scores": scores[:n],  # [N]
        "labels": labels[:n],  # [N]
        "masks": masks[:n],  # [N, H, W]
    }


def draw_predictions(image_path, predictions, id_to_name, score_thresh=0.20, show_masks=False):
    """Render bounding boxes and optional instance masks onto an image.

    Opens the image at ``image_path``, resizes it to ``(1280, 1024)``, and
    draws a coloured bounding box with a label badge for every detection whose
    confidence score meets ``score_thresh``. When ``show_masks`` is ``True``,
    semi-transparent filled masks are composited beneath the boxes.

    Each class label is assigned a consistent colour from a fixed palette so
    the same class always appears in the same colour across calls.

    Args:
        image_path (str): Path to the source image file. Accepts any format
            supported by Pillow (JPEG, PNG, etc.).
        predictions (dict): Output from :func:`predict` containing:
            - ``boxes``  (numpy.ndarray): ``[N, 4]`` xyxy bounding boxes.
            - ``scores`` (numpy.ndarray): ``[N]`` confidence scores in ``[0, 1]``.
            - ``labels`` (numpy.ndarray): ``[N]`` integer class IDs.
            - ``masks``  (numpy.ndarray): ``[N, H, W]`` float instance masks.
        id_to_name (dict[int, str]): Mapping from integer label ID to human-
            readable class name. Unknown IDs fall back to ``str(label_id)``.
        score_thresh (float): Minimum confidence score for a detection to be
            drawn. Defaults to ``0.20``.
        show_masks (bool): If ``True``, semi-transparent filled masks
            (alpha=120) are blended onto the image before drawing boxes.
            Requires ``"masks"`` to be present in ``predictions``.
            Defaults to ``False``.

    Returns:
        PIL.Image.Image: RGB image of size ``(1280, 1024)`` with all
        qualifying detections rendered.
    """
    img = Image.open(image_path).convert("RGB").resize((1280, 1024))
    W, H = img.size

    if show_masks and "masks" in predictions:
        overlay = img.copy().convert("RGBA")
        for mask, score, label in zip(
            predictions["masks"], predictions["scores"], predictions["labels"], strict=False
        ):
            if score < score_thresh:
                continue
            color = _label_color(int(label))
            binary = (mask > 0.5).astype(np.uint8) * 255
            mask_pil = Image.fromarray(binary).resize((W, H), Image.Resampling.NEAREST)
            colored = Image.new("RGBA", (W, H), color + (120,))  # alpha=120
            overlay.paste(colored, mask=mask_pil)
        img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")

    draw = ImageDraw.Draw(img)
    for box, score, label in zip(
        predictions["boxes"], predictions["scores"], predictions["labels"], strict=False
    ):
        if score < score_thresh:
            continue
        x1, y1, x2, y2 = box
        color = _label_color(int(label))
        name = id_to_name.get(int(label), str(label))
        draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
        draw.rectangle([x1, max(0, y1 - 14), x1 + len(f"{name} {score:.2f}") * 6, y1], fill=color)
        draw.text((x1 + 2, max(0, y1 - 13)), f"{name} {score:.2f}", fill="white")

    return img
