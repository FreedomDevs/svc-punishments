from enum import Enum as PyEnum
from sqlalchemy import Column, String, Integer, UUID, Enum, DateTime
from sqlalchemy.orm import declarative_base

class PunishmentType(PyEnum):
    Mute = "MUTE"
    Ban = "BAN"
    Warn = "WARN"

Base = declarative_base()
class PunishmentsTable(Base):
    __tablename__ = "punishments"


    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, nullable=False)
    type = Column(Enum(PunishmentType), nullable=False)
    reason = Column(String, nullable=False)
    issued = Column(String, nullable=False)
    issued_by = Column(UUID, nullable=True)
    created_at = Column(DateTime, nullable=False)
    server_name = Column(String, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(UUID, nullable=True)
    revoke_reason = Column(String, nullable=True)