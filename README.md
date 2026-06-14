# svc-punishments

Микросервис хранения и управления наказаниями игроков Minecraft.

Типы локальных наказаний (работают только в пределах конкретного сервера):
- BAN
- VOICE_MUTE
- CHAT_MUTE
Типы глобальных наказаний (распространяются на все сервера, и вообще на всё):
- GLOBAL_FULL_BAN — блокирует даже вход в аккаунт на сайте
- GLOBAL_BAN
- GLOBAL_VOICE_MUTE
- GLOBAL_CHAT_MUTE 

---

# Сетевые адреса в тестовой docker сети

IP сервиса из docker-compose: `http://[fd98:2dd6:8f48:1d99:5902:b7ae::2]`

Swagger документация: `http://[fd98:2dd6:8f48:1d99:5902:b7ae::2]/docs`

IP базы данных из docker-compose: `[fd98:2dd6:8f48:1d99:5902:b7ae::3]:5432`

---

# Пример запросов

## Создание локального наказания

POST `/punishments/local`

```jsonc
{
  "userId": "c9a6467e-3d02-4f29-95c2-7a0c1d0c7c12", // UUID человека который наказан
  "type": "BAN", // Enum, локальное наказание
  "reason": "Cheating", // Причина наказания, это просто строка
  "serverName": "survival-1", // Имя сервера к которому относится это наказание, подставляется автоматически при авторизации по токену сервера
  "duration": 3600, // Время действия наказания в секундах, можно null, так будет навсегда
  "issuedBy": "user=a8d1c6d2-5b65-4c24-bb18-1a28c4f8b9a1" // Информация issuedBy того кто вынес это наказание
}
```

Ответ:

HTTP `201 Created`

```json
{
  "data": {
    "punishmentId": "0c0c7a0c-7a0c-7a0c-7a0c-0c0c7a0c7a0c"
  },
  "message": "Punishment created",
  "meta": {
    "code": "PUNISHMENT_CREATED_OK",
    "traceId": "8d4c5c8c4e624154bd7f5105f6254bc7",
    "timestamp": "2026-03-13T12:00:00Z"
  }
}
```

Коды ответов:
- PUNISHMENT_CREATED_OK — наказание успешно создано (201)
- PUNISHMENT_VALIDATION_ERROR — ошибка при валидации (422)
- PUNISHMENT_INTERNAL_ERROR — внутренная ошибка (500)

## Создание глобального наказания

POST `/punishments/global`

```jsonc
{
  "userId": "c9a6467e-3d02-4f29-95c2-7a0c1d0c7c12", // UUID человека который наказан
  "type": "GLOBAL_FULL_BAN", // Enum, глобальные наказание
  "reason": "Huesos", // Причина наказания, это просто строка
  "duration": null, // Время действия наказания в секундах, можно null, так будет навсегда
  "issuedBy": "user=a8d1c6d2-5b65-4c24-bb18-1a28c4f8b9a1" // Информация issuedBy того кто вынес это наказание
}
```

Ответ:

HTTP `201 Created`

```json
{
  "data": {
    "punishmentId": "55ac3844-fe27-4bd2-950c-7944bb6cb98a"
  },
  "message": "Punishment created",
  "meta": {
    "code": "PUNISHMENT_CREATED_OK",
    "traceId": "8d4c5c8c4e624154bd7f5105f6254bc7",
    "timestamp": "2026-03-13T12:00:00Z"
  }
}
```

Коды ответов:
- PUNISHMENT_CREATED_OK — наказание успешно создано (201)
- PUNISHMENT_VALIDATION_ERROR — ошибка при валидации (422)
- PUNISHMENT_INTERNAL_ERROR — внутренная ошибка (500)

---

## Проверка активных наказаний

GET `/punishments/check?userId={userId}&serverName={serverName}'

Примечания:
- Если авторизация идёт по токену сервера то serverName указывать нельзя, он подставится сам
- Endpoint выдаёт не только локальные наказания с сервера, а также глобальные наказания (те которые не привязаны ни к какому серверу)
- Есди авторизация идёт **не** по токену сервера и serverName отсутствует то в ответ придут только глобальные наказания

Ответ:

```json
{
  "data": [
    {
      "type": "BAN",
      "reason": "Cheating",
      "issuedBy": "user=a8d1c6d2-5b65-4c24-bb18-1a28c4f8b9a1",
      "expiresAt": "2026-03-14T12:00:00Z",
      "createdAt": "2026-03-13T12:00:00Z",
    }
  ],
  "message": "Active punishments fetched",
  "meta": {
    "code": "PUNISHMENT_CHECK_OK",
    "traceId": "8d4c5c8c4e624154bd7f5105f6254bc7",
    "timestamp": "2026-03-13T12:00:00Z"
  }
}
```

Коды ответов:
- PUNISHMENT_CHECK_OK — наказания успешно проверены (200)
- PUNISHMENT_VALIDATION_ERROR — ошибка при валидации (422)
- PUNISHMENT_INTERNAL_ERROR — внутренная ошибка (500)

---

## История наказаний

GET `/punishments/history?userId={userId}&serverName={serverName}'

Примечания:
- Если авторизация идёт по токену сервера то serverName указывать нельзя, он подставится сам
- Endpoint выдаёт не только локальные наказания с сервера, а также глобальные наказания (те которые не привязаны ни к какому серверу)
- Есди авторизация идёт **не** по токену сервера и serverName отсутствует то в ответ придут только глобальные наказания

Тут должна быть пагинация

Ответ:

```json
{
  "data": [
    {
      "id": "0c0c7a0c-7a0c-7a0c-7a0c-0c0c7a0c7a0c",
      "type": "BAN",
      "reason": "Cheating",
      "issuedBy": "user=a8d1c6d2-5b65-4c24-bb18-1a28c4f8b9a1",
      "serverName": "survival-1",
      "createdAt": "2026-03-13T12:00:00Z",
      "expiresAt": "2026-03-14T12:00:00Z",
      "revokedAt": null,
      "revokedBy": null,
      "revokedReason": null
    }
  ],
  "message": "Punishment history fetched",
  "meta": {
    "code": "PUNISHMENT_HISTORY_OK",
    "traceId": "8d4c5c8c4e624154bd7f5105f6254bc7",
    "timestamp": "2026-03-13T12:00:00Z"
  }
}
```

Коды ответов:
- PUNISHMENT_HISTORY_OK — история наказаний успешно получена (200)
- PUNISHMENT_VALIDATION_ERROR — ошибка при валидации (422)
- PUNISHMENT_INTERNAL_ERROR — внутренная ошибка (500)

---

## Отмена наказания

POST `/punishments/{punishmentId}/revoke`

```json
{
  "revokedBy": "user=a8d1c6d2-5b65-4c24-bb18-1a28c4f8b9a1",
  "revokedReason": "Appeal accepted"
}
```

Ответ:

```json
{
  "data": {
    "punishmentId": "0c0c7a0c-7a0c-7a0c-7a0c-0c0c7a0c7a0c"
  },
  "message": "Punishment revoked",
  "meta": {
    "code": "PUNISHMENT_REVOKED_OK",
    "traceId": "8d4c5c8c4e624154bd7f5105f6254bc7",
    "timestamp": "2026-03-13T12:00:00Z"
  }
}
```

Коды ответов:
- PUNISHMENT_REVOKED_OK — наказание успешно снято (200)
- PUNISHMENT_ALREADY_REVOKED — наказание уже было снято (400)
- PUNISHMENT_NOT_FOUND — наказание не существует (404)
- PUNISHMENT_VALIDATION_ERROR — ошибка при валидации (422)
- PUNISHMENT_INTERNAL_ERROR — внутренная ошибка (500)

