from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=6)
    username: str | None = None


class UserOut(BaseModel):
    id: int
    name: str
    username: str
    email: EmailStr
    role: str
    created_at: str | None = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class LoginRequest(BaseModel):
    email: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordReset(BaseModel):
    email: EmailStr
    otp: str = Field(min_length=4, max_length=12)
    new_password: str = Field(min_length=6)


class PasswordResetResponse(BaseModel):
    message: str
    sent_to_email: bool = True
    debug_otp: str | None = None


class PredictionOut(BaseModel):
    result: str
    verdict: str
    confidence: float
    confidence_percent: float
    raw_score: float
    heatmap_url: str | None = None
    note: str | None = None


class HistoryPrediction(BaseModel):
    verdict: str
    confidence: float
    raw_score: float
    heatmap_url: str | None = None


class HistoryItem(BaseModel):
    id: int
    filename: str
    media_type: str
    created_at: str | None = None
    prediction: HistoryPrediction
    note: str | None = None
