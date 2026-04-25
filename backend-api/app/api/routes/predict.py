from fastapi import APIRouter, Depends, File, UploadFile

from app.api.deps import get_current_user
from app.schemas.schemas import PredictionOut
from app.services import storage
from app.services.ai import run_prediction

router = APIRouter(tags=["predict"])


@router.post("/predict", response_model=PredictionOut)
async def predict(file: UploadFile = File(...), user=Depends(get_current_user)):
    upload_id = storage.reserve_upload_id()
    content_type = file.content_type or "application/octet-stream"
    file_type = "video" if content_type.startswith("video/") else "image"

    contents = await file.read()
    result = run_prediction(contents, file.filename or "upload.bin", upload_id, content_type)

    storage.create_upload_record(
        upload_id=upload_id,
        user=user,
        filename=file.filename or "upload.bin",
        file_type=file_type,
        result=str(result.get("result", "UNKNOWN")),
        confidence=float(result.get("confidence", 0.5)),
        raw_score=float(result.get("raw_score", 0.5)),
        heatmap_url=result.get("heatmap_url"),
        note=result.get("note")
    )

    confidence_value = float(result.get("confidence", 0.5))
    return PredictionOut(
        result=str(result.get("result", "UNKNOWN")),
        verdict=str(result.get("verdict", result.get("result", "UNKNOWN"))),
        confidence=confidence_value,
        confidence_percent=round(confidence_value * 100, 2),
        raw_score=float(result.get("raw_score", 0.5)),
        heatmap_url=result.get("heatmap_url"),
        note=result.get("note")
    )


@router.get("/heatmap/{upload_id}")
def get_heatmap(upload_id: int):
    return {"heatmap_url": f"/static/heatmaps/{upload_id}.png"}
