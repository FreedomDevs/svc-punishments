from svcLibs.codes import BaseOkCode, BaseErrorCode

class PunishmentCreatedOk(BaseOkCode):
    HTTPCODE = 201
    CODE = "PUNISHMENT_CREATED_OK"
    MESSAGE = "Наказание успешно создано"

class PunishmentCheckOk(BaseOkCode):
    HTTPCODE = 200
    CODE = "PUNISHMENT_CHECK_OK"
    MESSAGE = "Активное наказание успешно получено"

class PunishmentHistoryOk(BaseOkCode):
    HTTPCODE = 200
    CODE = "PUNISHMENT_HISTORY_OK"
    MESSAGE = "Активное наказание успешно получено"

class PunishmentRevokedOk(BaseOkCode):
    HTTPCODE = 200
    CODE = "PUNISHMENT_REVOKED_OK"
    MESSAGE = "Наказание успешно отменено"

class PunishmentNotFound(BaseErrorCode):
    HTTPCODE = 404
    CODE = "PUNISHMENT_NOT_FOUND"
    MESSAGE = "Наказание не найдено"

class PunishmentAlreadyRevoked(BaseErrorCode):
    HTTPCODE = 400
    CODE = "PUNISHMENT_ALREADY_REVOKED"
    MESSAGE = "Наказание уже отменено"

