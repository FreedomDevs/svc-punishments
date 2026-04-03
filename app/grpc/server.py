from concurrent import futures
import grpc
import punishments_pb2_grpc
from app.grpc.handlers import PunishmentServiceServicer


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    punishments_pb2_grpc.add_PunishmentServiceServicer_to_server(
        PunishmentServiceServicer(), server
    )

    server.add_insecure_port('[::]:50051')
    server.start()
    server.wait_for_termination()