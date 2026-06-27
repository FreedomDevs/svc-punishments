from enum import Enum as PyEnum
from sqlalchemy import Column, String, UUID, Enum, DateTime
from sqlalchemy.orm import declarative_base

class PunishmentType(PyEnum):
    Ban = "BAN"
    VoiceMute = "VOICE_MUTE"
    ChatMute = "CHAT_MUTE"

    GlobalFullBan = "GLOBAL_FULL_BAN"
    GlobalBan = "GLOBAL_BAN"
    GlobalVoiceMute = "GLOBAL_VOICE_MUTE"
    GlobalChatMute = "GLOBAL_CHAT_MUTE"

LOCAL_PUNISHMENTS = ["BAN", "VOICE_MUTE", "CHAT_MUTE"]
GLOBAL_PUNISHMENTS = ["GLOBAL_FULL_BAN", "GLOBAL_BAN", "GLOBAL_VOICE_MUTE", "GLOBAL_CHAT_MUTE"]

class AuthorizationType(PyEnum):
    Service = "SERVICE"
    Server = "SERVER"
    User = "USER"


Base = declarative_base()
class PunishmentsTable(Base):
    __tablename__ = "punishments"

    # Основной PRIMARY KEY
    id = Column(UUID, primary_key=True)

    # UUID пользователя которого наказывают
    user_id = Column(UUID, nullable=False)

    # Даты создания, и окончания, если дата окончания срока бана не указана, то бан перманентный
    created_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=True)

    # Имя сервера на котором выдано наказание, если NULL то наказание глобальное
    server_name = Column(String, nullable=True)
    # Тип блокироки
    type = Column(Enum(PunishmentType), nullable=False)

    # Причина блокировки
    reason = Column(String, nullable=False)
    # Кто сделал эту блокировку, произвольное поле для SERVER и SERVICE, и user=<UUID> для USER
    issued_by = Column(String, nullable=False)
    # Способ авторизации который был использовал для создания наказания
    issuer_authorization_type = Column(Enum(AuthorizationType), nullable=False)

    # Дата преждевременной отмены блокировки
    revoked_at = Column(DateTime, nullable=True)
    # Кто отменил блокировку, тоже что и issued_by
    revoked_by = Column(String, nullable=True)
    # Причина по которой блокировка была снята
    revoke_reason = Column(String, nullable=True)
    # Способ авторизации который был использовал для отмены наказания
    revoker_authorization_type = Column(Enum(AuthorizationType), nullable=True)
