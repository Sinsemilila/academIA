from pydantic import BaseModel, Field
from datetime import datetime


# ── Auth ───────────────────────────────────────────────
class LoginRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=6, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=10)


# ── User ───────────────────────────────────────────────
class UserResponse(BaseModel):
    id: int
    username: str
    display_name: str | None
    is_admin: bool
    exam_access: bool


class UserCreate(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    password: str = Field(..., min_length=8, max_length=128)
    display_name: str | None = Field(None, max_length=100)
    exam_access: bool = False


# ── Profile ────────────────────────────────────────────
class ProfileResponse(BaseModel):
    niveau: str | None
    scores: dict
    points_forts: str | None
    lacunes: str | None
    mode_apprentissage: str | None
    derniere_session: str | None


# ── Streak ─────────────────────────────────────────────
class StreakResponse(BaseModel):
    current_streak: int
    longest_streak: int
    total_sessions: int


# ── Chat ───────────────────────────────────────────────
class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4000)
    conversation_id: str | None = Field(None, max_length=200)
    agent: str = Field("teacher", pattern=r"^[a-z_]+$", max_length=50)
    mock_exam: str | None = Field(None, max_length=200)  # Quiz: "Q3/10:conditional_2:DECOUVERTE"
    mode_override: str | None = Field(None, pattern=r"^(structure|libre)?$")  # Mode change


# ── Mode ──────────────────────────────────────────────
class ModeChangeRequest(BaseModel):
    mode: str = Field(..., pattern=r"^(structure|libre)$")
    # Sprint 5 D1: ISO domain ("en"/"es"/...). None → default "en" backward-compat.
    domain: str | None = Field(default=None, max_length=20)


# ── Settings ───────────────────────────────────────────
class UpdateProfileRequest(BaseModel):
    display_name: str | None = Field(None, max_length=100)
    avatar_color: str | None = Field(None, pattern=r"^#[0-9a-fA-F]{6}$")
    theme: str | None = Field(None, pattern=r"^(dark|light)$")
    daily_goal_minutes: int | None = Field(None, ge=5, le=120)
    centres_interet: str | None = Field(None, max_length=200)
    style_correction: str | None = Field(None, pattern=r"^(direct|encourageant|humour)?$")
    # Sprint 5 D1: target domain for personality prefs (per-language scoping)
    domain: str | None = Field(default=None, max_length=20)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=6, max_length=128)
    new_password: str = Field(..., min_length=6, max_length=128)
