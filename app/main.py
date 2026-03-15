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
def punishment_history(
    userId: str,
    request: Request,
    serverName: str | None = None,
    globalOnly: bool = False,
    fromTime: datetime | None = None,
    toTime: datetime | None = None,
    page: int = 1,
    pageSize: int = 20
):

    trace_id = request.headers.get("X-Trace-Id")
    db = SessionLocal()

    query = db.query(PunishmentsTable).filter(
        PunishmentsTable.user_id == userId
    )

    if serverName:
        query = query.filter(PunishmentsTable.server_name == serverName)

    if globalOnly:
        query = query.filter(PunishmentsTable.server_name == None)

    if fromTime:
        query = query.filter(PunishmentsTable.created_at >= fromTime)

    if toTime:
        query = query.filter(PunishmentsTable.created_at <= toTime)

    total = query.count()

    rows = query.offset((page - 1) * pageSize).limit(pageSize).all()

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

    totalPages = (total + pageSize - 1) // pageSize

    return {
        "data": history,
        "pagination": {
            "page": page,
            "pageSize": pageSize,
            "total": total,
            "totalPages": totalPages
        },
        "message": "Punishment history fetched",
        "meta": {
            "code": Codes.PUNISHMENT_HISTORY_OK,
            "traceId": trace_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    }


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




@app.post("/punishments/revoke")
def revoke_bulk(
    req: PunishmentRevokeRequest,
    request: Request,
    userId: str | None = None,
    type: str | None = None
):

    trace_id = request.headers.get("X-Trace-Id")
    db = SessionLocal()

    if not userId:
        return error_response(
            message="userId required",
            code="PUNISHMENT_INVALID_PARAMS",
            trace_id=trace_id
        )

    now = datetime.utcnow()

    query = db.query(PunishmentsTable).filter(
        PunishmentsTable.user_id == userId,
        PunishmentsTable.revoked_at == None
    )

    if type:
        query = query.filter(PunishmentsTable.type == type)

    rows = query.all()

    if not rows:
        return error_response(
            message="No active punishments found",
            code=Codes.PUNISHMENT_NOT_FOUND,
            trace_id=trace_id
        )

    revoked_ids = []

    for p in rows:

        if p.expires_at and p.expires_at < now:
            continue

        p.revoked_at = now
        p.revoked_by = req.revokedBy
        p.revoke_reason = req.reason

        revoked_ids.append(str(p.id))

    db.commit()

    return success_response(
        data={"revoked": revoked_ids},
        message="Punishments revoked",
        code=Codes.PUNISHMENT_REVOKED_OK,
        trace_id=trace_id
    )




@app.get("/health")
def health(request: Request):
    trace_id = request.headers.get("X-Trace-Id")

    details: dict[str, str] = {}
    ready = True

    # мемори
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        details["memory"] = "OK"
    except Exception as e:
        details["memory"] = f"ERROR: {str(e)}"
        ready = False

    # датабаза
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        details["database"] = "OK"
    except Exception as e:
        details["database"] = f"ERROR: {str(e)}"
        ready = False


    return success_response(
        data={
            "status": "UP" if ready else "ERROR",
            "ready": ready,
            "details": details
        },
        message="Service is healthy",
        code=Codes.HEALTH_OK,
        trace_id=trace_id
    )

@app.get("/live")
def live(request: Request):
    trace_id = request.headers.get("X-Trace-Id")

    return success_response(
        data={"alive": True},
        message="svc-whitelist alive",
        code=Codes.LIVE_OK,
        trace_id=trace_id
    )