from pydantic import BaseModel


class PunishmentCreateRequest(BaseModel):
    userId: str
    type: str
    reason: str
    duration: int | None = None
    issuedBy: str


class PunishmentRevokeRequest(BaseModel):
    revokedBy: str
    reason: str


class UserBody(BaseModel):
    server_name: str