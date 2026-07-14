import uuid
import datetime
from typing import Optional

import httpx
from sqlalchemy import or_
from fastapi import FastAPI, Request, HTTPException, Header, Depends
from sqlalchemy import text
from starlette import status
from svcLibs.codes import HealthOK, LiveOK, ValidationError
from app.enums import *
from app.models import Base, PunishmentsTable, GLOBAL_PUNISHMENTS, LOCAL_PUNISHMENTS
from app.schemas import PunishmentCreateRequest, PunishmentRevokeRequest, UserBody, GlobalPunishmentCreateRequest

from svcLibs.responses import success_response, error_response
from svcLibs.middleware import register_errors_handlers, ParseAuthMiddleware, AuthState
from svcLibs.db import SessionLocal, engine
import os
from fastapi import FastAPI, BackgroundTasks


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


async def run_parse_auth_middleware(request: Request):
    # Создаем экземпляр твоего middleware.
    # BaseHTTPMiddleware требует ASGI-приложение в конструктор, передаем None
    middleware = ParseAuthMiddleware(app=None)

    # Фейковый call_next, который просто возвращает пустой ответ,
    # если middleware успешно пропустило запрос дальше
    async def dummy_call_next(req):
        return "OK"

    try:
        # Вручную вызываем dispatch
        result = await middleware.dispatch(request, dummy_call_next)
        return result
    except Exception as e:
        # Если внутри middleware возникла ошибка авторизации,
        # она пробросится сюда и прервет запрос
        raise HTTPException(status_code=401, detail=str(e))


SVC_QUEUE_URL = os.getenv("SVC_QUEUE_URL", "http://[fd98:2dd6:8f48:1d99::1]:8080")

async def queue_send(punishment: PunishmentsTable):
    data = {
        "id": str(punishment.id),
        "user_id": str(punishment.user_id),
        "created_at": punishment.created_at.isoformat(),
        "expires_at": punishment.expires_at.isoformat() if punishment.expires_at else None,
        "server_name": punishment.server_name,
        "type": punishment.type,
        "reason": punishment.reason,
        "issued_by": punishment.issued_by,
        "issuer_authorization_type": punishment.issuer_authorization_type,
        "revoked_at": punishment.revoked_at.isoformat() if punishment.revoked_at else None,
        "revoked_by": punishment.revoked_by,
        "revoke_reason": punishment.revoke_reason,
        "revoker_authorization_type": punishment.revoker_authorization_type,
    }
    try:
        print("Отправка в очередь:", data)
        async with httpx.AsyncClient() as client:
            resp = await client.post(SVC_QUEUE_URL, json=data)
            print("Успешная отправка, статус:", resp.status_code)
    except Exception as e:
        print("Внимание, не удалось отправить в очередь", e)


@app.post("/punishments/local", dependencies=[Depends(run_parse_auth_middleware)])
async def create_local_punishment(req: PunishmentCreateRequest, request: Request, background_tasks: BackgroundTasks):
    db = SessionLocal()
    auth: AuthState = request.state.auth
    expires = None

    if req.type not in LOCAL_PUNISHMENTS:
        return error_response(ValidationError(["Некорректный тип наказания"]), request.headers.get("X-Trace-Id"))

    if req.server_name is None and auth.server_name is None:
        return error_response(ValidationError(["server_name не указан"]), request.headers.get("X-Trace-Id"))

    if req.issued_by is None and auth.user_id is None:
        return error_response(ValidationError(["issued_by не указан"]), request.headers.get("X-Trace-Id"))

    if req.duration:
        expires = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=req.duration)

    punishment = PunishmentsTable(
        id = uuid.uuid7(),
        user_id=uuid.UUID(req.user_id),
        type=req.type,
        reason=req.reason,
        server_name=auth.server_name if auth.server_name else req.server_name,
        issued_by=f"uuid={auth.user_id}" if auth.user_id else req.issued_by, issuer_authorization_type = auth.type,
        created_at=datetime.datetime.now(datetime.UTC),
        expires_at=expires
    )

    db.add(punishment)
    db.commit()
    await queue_send(punishment)

    return success_response(
        {"punishment_id": str(punishment.id)},
        PunishmentCreatedOk(),
        request.headers.get("X-Trace-Id")
    )

@app.post("/punishments/global", dependencies=[Depends(run_parse_auth_middleware)])
def create_punishment_global(req: GlobalPunishmentCreateRequest, request: Request, background_tasks: BackgroundTasks):
    db = SessionLocal()
    auth: AuthState = request.state.auth
    expires = None

    if req.type not in GLOBAL_PUNISHMENTS:
        return error_response(ValidationError(["Некорректный тип наказания"]), request.headers.get("X-Trace-Id"))

    if req.issued_by is None and auth.user_id is None:
        return error_response(ValidationError(["issued_by не указан"]), request.headers.get("X-Trace-Id"))

    if req.duration:
        expires = datetime.datetime.now(datetime.UTC) + datetime.timedelta(seconds=req.duration)

    punishment = PunishmentsTable(
        id=uuid.uuid7(),
        user_id=uuid.UUID(req.user_id),
        type=req.type,
        reason=req.reason,
        issued_by=f"uuid={auth.user_id}" if auth.user_id else req.issued_by, issuer_authorization_type = auth.type,
        created_at=datetime.datetime.now(datetime.UTC),
        expires_at=expires
    )

    db.add(punishment)
    db.commit()
    queue_send(punishment)

    return success_response(
        {"punishment_id": punishment.id},
        PunishmentCreatedOk(),
        request.headers.get("X-Trace-Id")
    )

@app.get("/punishments/check")
def check_punishments(
    userId: str,
    request: Request,
    serverName: str | None = None,
):

    trace_id = request.headers.get("X-Trace-Id")
    db = SessionLocal()

    now = datetime.datetime.now(datetime.UTC)

    query = db.query(PunishmentsTable).filter(
        PunishmentsTable.user_id == uuid.UUID(userId),
        PunishmentsTable.revoked_at is None,
        or_(
            PunishmentsTable.expires_at is None,
            PunishmentsTable.expires_at > now
        )
    )

    if serverName:
        query = query.filter(
            or_(
                PunishmentsTable.server_name is None,
                PunishmentsTable.server_name == serverName
            )
        )



    rows = query.all()

    active = [
        {
            "type": r.type,
            "reason": r.reason,
            "issued_by": r.issued_by,
            "expires_at": r.expires_at,
            "created_at": r.created_at
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
    fromTime: datetime.datetime | None = None,
    toTime: datetime.datetime | None = None,
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
            "issued_by": r.issued_by,
            "server_name": r.server_name,
            "created_at": r.created_at,
            "expires_at": r.expires_at,
            "revoked_at": r.revoked_at,
            "revoked_by": r.revoked_by,
            "revoked_reason": r.revoke_reason,
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
            "timestamp": datetime.datetime.now(datetime.UTC).isoformat() + "Z"
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

    punishment.revoked_at = datetime.datetime.now(datetime.UTC)
    punishment.revoked_by = req.revoked_by
    punishment.revoke_reason = req.revoked_reason

    db.commit()

    return success_response(
        {"punishmentId": punishment_id},
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
