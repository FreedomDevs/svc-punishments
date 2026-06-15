import uuid
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import or_
from fastapi import FastAPI, Request, HTTPException, Header, Depends
from sqlalchemy import text
from starlette import status
from svcLibs.codes import HealthOK, LiveOK, ValidationError

from app.db import SessionLocal, engine
from app.enums import *
from app.models import Base, PunishmentsTable
from app.schemas import PunishmentCreateRequest, PunishmentRevokeRequest, UserBody

from svcLibs.responses import success_response, error_response
from svcLibs.middleware import register_errors_handlers

Base.metadata.create_all(bind=engine)

app = FastAPI(title="svc-punishments")
register_errors_handlers(app)

async def get_server_name(
        request: Request,
        eauth_type: Optional[str] = Header(None, alias="eauth-type"),
        eauth_server_name: Optional[str] = Header(None, alias="eauth-server-name"),
) -> str:
    if not eauth_type or eauth_type == "user":
        # Если user — читаем имя сервера из Body.
        # Так как нам нужно прочитать JSON, используем request.json()
        try:
            body_data = await request.json()
            # Валидируем данные через Pydantic-модель
            user_data = UserBody(**body_data)
            return user_data.server_name
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Неверный формат Body. Ожидалось поле 'server_name'."
            )

    elif eauth_type == "server":
        # Если server — проверяем заголовок "eauth"
        if not eauth_server_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Для eauth-type='server' необходим заголовок 'eauth'"
            )
        return eauth_server_name

    else:
        # Если передан неизвестный тип авторизации
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Неподдерживаемый eauth-type. Допустимы 'user' или 'server'."
        )




@app.post("/punishments", status_code=201)
def create_punishment(req: PunishmentCreateRequest, request: Request, server_name: str = Depends(get_server_name)):
    db = SessionLocal()

    expires = None

    if req.duration:
        expires = datetime.utcnow() + timedelta(seconds=req.duration)
    print(req.userId)
    punishment = PunishmentsTable(
        user_id=uuid.UUID(req.userId),
        type=req.type,
        reason=req.reason,
        server_name=server_name,
        issued_by=uuid.UUID(req.issuedBy),id = uuid.uuid7(),
        issued="User",
        created_at=datetime.utcnow(),
        expires_at=expires
    )

    db.add(punishment)
    db.commit()

    return success_response(
        {"punishmentId": punishment.id},
        PunishmentCreatedOk(),
        request.headers.get("X-Trace-Id")
    )

@app.get("/punishments/check")
def check_punishments(
    userId: str,
    request: Request,
    serverName: str | None = None,
    type: str | None = None
):

    trace_id = request.headers.get("X-Trace-Id")
    db = SessionLocal()

    now = datetime.utcnow()

    query = db.query(PunishmentsTable).filter(
        PunishmentsTable.user_id == uuid.UUID(userId),
        PunishmentsTable.revoked_at == None,
        or_(
            PunishmentsTable.expires_at == None,
            PunishmentsTable.expires_at > now
        )
    )

    if serverName:
        query = query.filter(
            or_(
                PunishmentsTable.server_name == None,
                PunishmentsTable.server_name == serverName
            )
        )

    if type:
        query = query.filter(PunishmentsTable.type == type)

    rows = query.all()

    active = [
        {
            "type": r.type,
            "reason": r.reason,
            "issuedBy": r.issued_by,
            "expiresAt": r.expires_at,
            "createdAt": r.created_at,
            "issued": r.issued,
        }
        for r in rows
    ]

    return success_response(
        active,
        PunishmentCheckOk(),
        trace_id
    )

@app.get("/punishments/history")
def punishment_history(
    userId: str,
    request: Request,
    serverName: str | None = None,
    globalOnly: bool = False,
    fromTime: datetime | None = None,
    toTime: datetime | None = None,
    type: str | None = None,
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


    if type:
        query = query.filter(PunishmentsTable.type == type)

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
            "code": PunishmentHistoryOk().CODE,
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
            PunishmentNotFound(),
            trace_id
        )
    if punishment.revoked_at:
        return error_response(
            PunishmentAlreadyRevoked(),
            trace_id

        )

    punishment.revoked_at = datetime.utcnow()
    punishment.revoked_by = req.revokedBy
    punishment.revoke_reason = req.reason

    db.commit()

    return success_response(
        {"punishmentId": punishment_id},
        PunishmentRevokedOk(),
        trace_id
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
            ValidationError(["userId required"]),
            trace_id
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
            PunishmentNotFound(),
            trace_id
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
        {"revoked": revoked_ids},
        PunishmentRevokedOk(),
        trace_id
    )


@app.get("/health")
def health(request: Request):
    details: dict[str, str] = {}
    ready = True

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        details["database"] = "OK"
    except Exception as e:
        details["database"] = f"ERROR: {str(e)}"
        ready = False

    return success_response(
        {
            "status": "UP" if ready else "ERROR",
            "ready": ready,
            "details": details
        },
        HealthOK(),
        request.headers.get("X-Trace-Id")
    )


@app.get("/live")
def live(request: Request):
    return success_response(
        {"alive": True},
        LiveOK(),
        request.headers.get("X-Trace-Id")
    )
