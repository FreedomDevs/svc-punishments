import grpc
from app.db import SessionLocal
from app.services import punishment_service

import punishments_pb2
import punishments_pb2_grpc


class PunishmentServiceServicer(punishments_pb2_grpc.PunishmentServiceServicer):

    def CreatePunishment(self, request, context):
        db = SessionLocal()

        # превращаем grpc → pydantic-like объект
        class Req:
            userId = request.userId
            type = request.type
            reason = request.reason
            serverName = request.serverName
            duration = request.duration
            issuedBy = request.issuedBy

        punishment = punishment_service.create_punishment(db, Req)

        return punishments_pb2.CreateResponse(
            punishmentId=str(punishment.id)
        )