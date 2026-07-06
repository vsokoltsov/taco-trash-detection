import io
from typing import Annotated, cast

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from trash_annotation.detection import DetectionService, ModelName

router = APIRouter(tags=["predictions"])


@router.post("/detect")
async def detect(
    request: Request,
    file: Annotated[UploadFile, File()],
    model: ModelName = ModelName.MASK_RCNN_V1,
    score_thresh: float = 0.20,
    show_masks: bool = False,
):
    service: DetectionService = cast(DetectionService, request.app.state.service)
    try:
        detector = service.get_detector(model)
    except LookupError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    tmp_path = f"/tmp/{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(await file.read())

    predictions = detector.predict(tmp_path, score_thresh=score_thresh)
    result_img = detector.draw_predictions(
        tmp_path,
        predictions,
        score_thresh=score_thresh,
        show_masks=show_masks,
    )

    buf = io.BytesIO()
    result_img.save(buf, format="JPEG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/jpeg")


@router.post("/detect/json")
async def detect_json(
    request: Request,
    file: Annotated[UploadFile, File()],
    model: ModelName = ModelName.MASK_RCNN_V1,
    score_thresh: float = 0.20,
):
    service: DetectionService = cast(DetectionService, request.app.state.service)
    try:
        detector = service.get_detector(model)
    except LookupError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error

    tmp_path = f"/tmp/{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(await file.read())

    predictions = detector.predict(tmp_path, score_thresh=score_thresh)

    return {
        "detections": [
            {
                "label": detector.id_to_name.get(int(label), str(label)),
                "score": float(score),
                "box": [float(x) for x in box],
            }
            for box, score, label in zip(
                predictions["boxes"],
                predictions["scores"],
                predictions["labels"],
                strict=False,
            )
        ]
    }


@router.get("/health")
async def health(
    request: Request,
):
    service: DetectionService = cast(DetectionService, request.app.state.service)
    if not service.detectors:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {
        "status": "ok",
        "models": sorted(model.value for model in service.detectors),
    }
