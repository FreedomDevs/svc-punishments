from pydantic import BaseModel


class PunishmentCreateRequest(BaseModel):
    user_id: str
    type: str
    reason: str
    server_name: str | None = None
    duration: int | None = None
    issued_by: str | None = None

class GlobalPunishmentCreateRequest(BaseModel):
    user_id: str
    type: str
    reason: str
    duration: int | None = None
    issued_by: str | None = None


class PunishmentRevokeRequest(BaseModel):
    revoked_by: str
    revoked_reason: str


class UserBody(BaseModel):
    server_name: str