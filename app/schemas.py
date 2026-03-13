from pydantic import BaseModel


class PunishmentCreateRequest(BaseModel):

    userId: str
    type: str
    reason: str
    serverName: str | None = None
    duration: int | None = None
    issuedBy: str


class PunishmentRevokeRequest(BaseModel):

    revokedBy: str
    reason: str