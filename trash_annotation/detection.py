from dataclasses import dataclass

import onnxruntime as ort

ID_TO_NAME = {
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


@dataclass
class DetectionService:
    session: ort.InferenceSession
    id_to_name: dict[int, str] | None = None

    def __post_init__(self):
        if self.id_to_name is None:
            self.id_to_name = ID_TO_NAME
