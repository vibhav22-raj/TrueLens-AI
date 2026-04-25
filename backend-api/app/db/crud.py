from sqlalchemy.orm import Session
from app.db import models
from app.core.security import hash_password


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def create_user(db: Session, name: str, email: str, password: str):
    user = models.User(name=name, email=email, hashed_password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_upload(db: Session, user_id: int, filename: str, media_type: str):
    upload = models.Upload(user_id=user_id, filename=filename, media_type=media_type)
    db.add(upload)
    db.commit()
    db.refresh(upload)
    return upload


def create_prediction(db: Session, upload_id: int, verdict: str, confidence: float, raw_score: float, heatmap_path: str | None = None):
    prediction = models.Prediction(
        upload_id=upload_id,
        verdict=verdict,
        confidence=confidence,
        raw_score=raw_score,
        heatmap_path=heatmap_path
    )
    db.add(prediction)
    db.commit()
    db.refresh(prediction)
    return prediction
