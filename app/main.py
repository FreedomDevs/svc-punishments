import uuid
from datetime import datetime, timedelta

from fastapi import FastAPI, Request
from sqlalchemy import text
from app.db import SessionLocal, engine
from app.models import Base, PunishmentsTable
from app.schemas import PunishmentCreateRequest, PunishmentRevokeRequest
from app.responses import success_response, error_response
from app.enums import Codes

app = FastAPI(title="svc-punishments")

Base.metadata.create_all(bind=engine)

@app.post("/punishments", status_code=201)
def create_punishment(req: PunishmentCreateRequest, request: Request):

    trace_id = request.headers.get("X-Trace-Id")

    db = SessionLocal()

    expires = None

    if req.duration:
        expires = datetime.utcnow() + timedelta(seconds=req.duration)
    print(req.userId)
    punishment = PunishmentsTable(
        user_id=uuid.UUID(req.userId),
        type=req.type,
        reason=req.reason,
        server_name=req.serverName,
        issued_by=uuid.UUID(req.issuedBy),id = uuid.uuid7(),
        issued="User",
        created_at=datetime.utcnow(),
        expires_at=expires
    )

    db.add(punishment)
    db.commit()

    return success_response(
        data={"punishmentId": punishment.id},
        message="Punishment created",
        code=Codes.PUNISHMENT_CREATED_OK,
        trace_id=trace_id
    )

@app.get("/punishments/check")
def check_punishments(userId: str, serverName: str | None, request: Request):

    trace_id = request.headers.get("X-Trace-Id")

    db = SessionLocal()

    now = datetime.utcnow()

    rows = db.query(PunishmentsTable).filter(
        PunishmentsTable.user_id == userId,
        PunishmentsTable.revoked_at == None
    ).all()

    active = []

    for r in rows:

        if r.expires_at and r.expires_at < now:
            continue

        if r.server_name and serverName and r.server_name != serverName:
            continue

        active.append({
            "type": r.type,
            "reason": r.reason,
            "issuedBy": r.issued_by,
            "expiresAt": r.expires_at,
            "createdAt": r.created_at,
            "issued": r.issued,
        })

    return success_response(
        data=active,
        message="Active punishments fetched",
        code=Codes.PUNISHMENT_CHECK_OK,
        trace_id=trace_id
    )

@app.get("/punishments/history")
def punishment_history(userId: str, request: Request):

    trace_id = request.headers.get("X-Trace-Id")

    db = SessionLocal()

    rows = db.query(PunishmentsTable).filter(
        PunishmentsTable.user_id == userId
    ).all()

    history = []

    for r in rows:
        history.append({
            "id": r.id,
            "type": r.type,
            "reason": r.reason,
            "issuedBy": r.issued_by,
            "serverName": r.server_name,
            "createdAt": r.created_at,
            "expiresAt": r.expires_at,
            "revokedAt": r.revoked_at,
            "issued": r.issued,
            "revokedBy": r.revoked_by,
            "revokedReason": r.revoke_reason,

        })

    return success_response(
        data=history,
        message="Punishment history fetched",
        code=Codes.PUNISHMENT_HISTORY_OK,
        trace_id=trace_id
    )

@app.post("/punishments/{punishment_id}/revoke")
def revoke_punishment(
    punishment_id: str,
    req: PunishmentRevokeRequest,
    request: Request
):

    trace_id = request.headers.get("X-Trace-Id")

    db = SessionLocal()

    punishment = db.query(PunishmentsTable).filter(
        PunishmentsTable.id == punishment_id
    ).first()

    if not punishment:

        return error_response(
            message="Punishment not found",
            code=Codes.PUNISHMENT_NOT_FOUND,
            trace_id=trace_id
        )
    if punishment.revoked_at:
        return error_response(
            message="Punishment already revoked",
            code=Codes.PUNISHMENT_ALREADY_REVOKED,
            trace_id=trace_id

        )

    punishment.revoked_at = datetime.utcnow()
    punishment.revoked_by = req.revokedBy
    punishment.revoke_reason = req.reason

    db.commit()

    return success_response(
        data={"punishmentId": punishment_id},
        message="Punishment revoked",
        code=Codes.PUNISHMENT_REVOKED_OK,
        trace_id=trace_id
    )