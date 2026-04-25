from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Float, Text
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(200), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    uploads = relationship("Upload", back_populates="user")


class Upload(Base):
    __tablename__ = "uploads"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String(200), nullable=False)
    media_type = Column(String(20), default="image")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="uploads")
    prediction = relationship("Prediction", back_populates="upload", uselist=False)


class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(Integer, ForeignKey("uploads.id"))
    verdict = Column(String(20), nullable=False)
    confidence = Column(Float, default=0.0)
    heatmap_path = Column(Text, nullable=True)
    raw_score = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    upload = relationship("Upload", back_populates="prediction")
