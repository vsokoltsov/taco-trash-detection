from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI

from trash_annotation.detection import (
    MASK_RCNN_ID_TO_NAME,
    DetectionService,
    Detector,
    ModelName,
)
from trash_annotation.models.mask_rcnn_v1.inference import MaskRcnnDetector
from trash_annotation.models.yolo_v8.inference import YoloDetector, YoloV11Top5Detector
from trash_annotation.settings import Settings, get_settings
from trash_annotation.storage import GDriveStorage

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = get_settings()
    storage = GDriveStorage()
    detectors: dict[ModelName, Detector] = {}

    if settings.MASK_RCNN_V1_PATH:
        try:
            model_path = storage.download(
                url=settings.MASK_RCNN_V1_PATH,
                local_name="mask_rcnn_v1.onnx",
            )
            detectors[ModelName.MASK_RCNN_V1] = MaskRcnnDetector.from_path(
                model_path,
                id_to_name=MASK_RCNN_ID_TO_NAME,
                use_gpu=settings.USE_GPU,
            )
        except Exception:
            logger.exception("Failed to load Mask R-CNN v1")

    if settings.YOLO_V8_PATH:
        try:
            model_path = storage.download(
                url=settings.YOLO_V8_PATH,
                local_name="yolo_v8.onnx",
            )
            detectors[ModelName.YOLO_V8] = YoloDetector(
                model_path,
                use_gpu=settings.USE_GPU,
            )
        except Exception:
            logger.exception("Failed to load YOLOv8")

    if settings.YOLO_V11_TOP5_PATH:
        try:
            model_path = storage.download(
                url=settings.YOLO_V11_TOP5_PATH,
                local_name="yolo_v11_top5.onnx",
            )
            detectors[ModelName.YOLO_V11_TOP5] = YoloV11Top5Detector(
                model_path,
                use_gpu=settings.USE_GPU,
            )
        except Exception:
            logger.exception("Failed to load YOLOv11 top-5")

    service = DetectionService(detectors=detectors)

    app.state.service = service
    yield
    app.state.service = None
