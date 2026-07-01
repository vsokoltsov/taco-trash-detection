from contextlib import asynccontextmanager

from fastapi import FastAPI

from trash_annotation.detection import DetectionService
from trash_annotation.models.mask_rcnn_v1.inference import load_onnx_session
from trash_annotation.settings import Settings, get_settings
from trash_annotation.storage import GDriveStorage


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings: Settings = get_settings()
    storage = GDriveStorage()
    model_name = "mask_rcnn_v1.onnx"
    model_path = storage.download(url=settings.MASK_RCNN_V1_PATH, local_name=model_name)
    session = load_onnx_session(model_path, use_gpu=settings.USE_GPU)

    service = DetectionService(session=session)

    app.state.service = service
    yield
    app.state.service = None
    app.state.session = None
