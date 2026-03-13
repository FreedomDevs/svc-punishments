---

# svc-punishments

Микросервис хранения и управления наказаниями игроков сети серверов Minecraft.

Сервис хранит информацию о наказаниях и предоставляет REST API для работы с ними.
Исполнение наказаний (бан, мут и т.д.) выполняется серверными плагинами.

Поддерживаемые типы наказаний:

* BAN
* MUTE
* WARN

Поддерживаются:

* **глобальные наказания** (serverName = null)
* **локальные наказания** (на конкретный сервер)

Все наказания сохраняются в PostgreSQL и доступны через REST API.

---

# Запуск

Сервис запускается через **docker compose**.

```bash
docker compose up --build
```

После запуска будут подняты:

* **svc-punishments-app-dev** — приложение
* **svc-punishments-postgres** — база данных

IP сервиса из docker-compose:

```
http://[fd98:2dd6:8f48:1d99:5902:b7ae::2]
```

IP базы данных:

```
[fd98:2dd6:8f48:1d99:5902:b7ae::3]:5432
```

Swagger документация будет доступна:

```
http://[fd98:2dd6:8f48:1d99:5902:b7ae::2]/docs
```

---

# Пример запросов

## Создание наказания

POST `/punishments`

```
{
  "userId": "c9a6467e-3d02-4f29-95c2-7a0c1d0c7c12",
  "type": "BAN",
  "reason": "Cheating",
  "serverName": "survival-1",
  "duration": 3600,
  "issuedBy": "a8d1c6d2-5b65-4c24-bb18-1a28c4f8b9a1"
}
```

Ответ:

```
201 Created
```

```
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

---

## Проверка активных наказаний

GET

```
/punishments/check?userId={userId}&serverName={serverName}
```

Ответ:

```
{
  "data": [
    {
      "type": "BAN",
      "reason": "Cheating",
      "issuedBy": "a8d1c6d2-5b65-4c24-bb18-1a28c4f8b9a1",
      "expiresAt": "2026-03-14T12:00:00Z",
      "createdAt": "2026-03-13T12:00:00Z",
      "issued": "User"
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

---

## История наказаний

GET

```
/punishments/history?userId={userId}
```

Ответ:

```
{
  "data": [
    {
      "id": "0c0c7a0c-7a0c-7a0c-7a0c-0c0c7a0c7a0c",
      "type": "BAN",
      "reason": "Cheating",
      "issuedBy": "a8d1c6d2-5b65-4c24-bb18-1a28c4f8b9a1",
      "serverName": "survival-1",
      "createdAt": "2026-03-13T12:00:00Z",
      "expiresAt": "2026-03-14T12:00:00Z",
      "revokedAt": null,
      "issued": "User",
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

---

## Отмена наказания

POST

```
/punishments/{punishmentId}/revoke
```

```
{
  "revokedBy": "a8d1c6d2-5b65-4c24-bb18-1a28c4f8b9a1",
  "reason": "Appeal accepted"
}
```

Ответ:

```
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

---

# Эндпоинты

| метод | endpoint                 | описание                     |
| ----- | ------------------------ | ---------------------------- |
| POST  | /punishments             | выдать наказание             |
| GET   | /punishments/check       | проверить активные наказания |
| GET   | /punishments/history     | получить историю наказаний   |
| POST  | /punishments/{id}/revoke | отменить наказание           |

---

# HTTP коды статусов

| код                        | описание                    |
| -------------------------- | --------------------------- |
| PUNISHMENT_CREATED_OK      | наказание создано           |
| PUNISHMENT_CHECK_OK        | активные наказания получены |
| PUNISHMENT_HISTORY_OK      | история получена            |
| PUNISHMENT_REVOKED_OK      | наказание отменено          |
| PUNISHMENT_NOT_FOUND       | наказание не найдено        |
| PUNISHMENT_ALREADY_REVOKED | наказание уже отменено      |

---
