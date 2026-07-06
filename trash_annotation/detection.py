from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Protocol

import numpy as np
from PIL import Image

from trash_annotation.protocols import Detector

MASK_RCNN_ID_TO_NAME = {
    1: "Aluminium foil",
    2: "Can",
    3: "Carton",
    4: "Cup",
    5: "Glass bottle",
    6: "Metal bottle cap",
    7: "Other",
    8: "Paper",
    9: "Plastic bottle",
    10: "Plastic bottle cap",
    11: "Plastic container",
    12: "Plastic film",
    13: "Plastic lid",
    14: "Pop tab",
    15: "Straw",
    16: "Styrofoam piece",
    17: "Wrapper",
}


class ModelName(StrEnum):
    MASK_RCNN_V1 = "mask_rcnn_v1"
    YOLO_V8 = "yolo_v8"


@dataclass
class DetectionService:
    detectors: dict[ModelName, Detector]

    def get_detector(self, model_name: ModelName) -> Detector:
        try:
            return self.detectors[model_name]
        except KeyError as error:
            raise LookupError(f"Model {model_name.value!r} is not loaded") from error
