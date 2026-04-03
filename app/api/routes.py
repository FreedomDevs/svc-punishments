from fastapi import APIRouter, Request
from app.db import SessionLocal
from app.schemas import PunishmentCreateRequest
from app.responses import success_response
from app.enums import Codes
from app.services import punishment_service

router = APIRouter()


@router.post("/punishments")
def create(req: PunishmentCreateRequest, request: Request):
    db = SessionLocal()

    punishment = punishment_service.create_punishment(db, req)

    return success_response(
        data={"punishmentId": punishment.id},
        message="Punishment created",
        code=Codes.PUNISHMENT_CREATED_OK,
        trace_id=request.headers.get("X-Trace-Id")
    )