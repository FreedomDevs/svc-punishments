import uuid
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models import PunishmentsTable


def create_punishment(db: Session, req):
    expires = None

    if req.duration:
        expires = datetime.utcnow() + timedelta(seconds=req.duration)

    punishment = PunishmentsTable(
        id=uuid.uuid7(),
        user_id=uuid.UUID(req.userId),
        type=req.type,
        reason=req.reason,
        server_name=req.serverName,
        issued_by=uuid.UUID(req.issuedBy),
        issued="User",
        created_at=datetime.utcnow(),
        expires_at=expires
    )

    db.add(punishment)
    db.commit()

    return punishment


def check_punishments(db: Session, userId: str, serverName: str | None):
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

    return query.all()