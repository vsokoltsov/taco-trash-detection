from pathlib import Path
from typing import Protocol
import numpy as np
from PIL import Image

class Detector(Protocol):
    id_to_name: dict[int, str]
    supports_masks: bool

    def predict(
        self,
        image_path: str | Path,
        score_thresh: float = 0.20,
    ) -> dict[str, np.ndarray]: ...

    def draw_predictions(
        self,
        image_path: str | Path,
        predictions: dict[str, np.ndarray],
        score_thresh: float = 0.20,
        show_masks: bool = False,
    ) -> Image.Image: ...