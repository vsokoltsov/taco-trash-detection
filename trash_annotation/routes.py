import io
from typing import Annotated, cast

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import StreamingResponse

from trash_annotation.detection import DetectionService
from trash_annotation.models.mask_rcnn_v1.inference import draw_predictions, predict

router = APIRouter(tags=["predictions"])


@router.post("/detect")
async def detect(
    request: Request,
    file: Annotated[UploadFile, File()],
    score_thresh: float = 0.20,
    show_masks: bool = False,
):
    service: DetectionService = cast(DetectionService, request.app.state.service)
    tmp_path = f"/tmp/{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(await file.read())

    predictions = predict(service.session, tmp_path, score_thresh=score_thresh)
    result_img = draw_predictions(
        tmp_path, predictions, service.id_to_name, score_thresh, show_masks
    )

    buf = io.BytesIO()
    result_img.save(buf, format="JPEG")
    buf.seek(0)
    return StreamingResponse(buf, media_type="image/jpeg")


@router.post("/detect/json")
async def detect_json(
    request: Request,
    file: Annotated[UploadFile, File()],
    score_thresh: float = 0.20,
):
    service: DetectionService = cast(DetectionService, request.app.state.service)
    tmp_path = f"/tmp/{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(await file.read())

    if service.id_to_name is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    predictions = predict(service.session, tmp_path, score_thresh=score_thresh)

    return {
        "detections": [
            {
                "label": service.id_to_name.get(int(label), str(label)),
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
    if service.session is None:
        raise HTTPException(status_code=503, detail="Model not loaded")
    return {"status": "ok"}
