Вот пример **README для микросервиса наказаний**, оформленный в том же стиле, что и ваш пример (`svc-whitelist`). Без лишней документации, но с понятной структурой.

---

# svc-punishments

Микросервис хранения и управления наказаниями игроков сети серверов Minecraft.
Сервис **не исполняет наказания**, а только хранит данные и предоставляет REST API для работы с ними.

Исполнение наказаний (бан, мут, кик) выполняется плагинами серверов.
Сервис используется для проверки активных наказаний и хранения полной истории.

Поддерживаемые типы наказаний:

* BAN (перманентный бан)
* TEMP_BAN (временный бан)
* MUTE (перманентный мут)
* TEMP_MUTE (временный мут)
* IP_BAN (бан по IP)
* WARN (предупреждение)

Поддерживаются:

* **глобальные наказания** (на всю сеть)
* **локальные наказания** (на конкретный сервер)

---

## Клонирование репозитория

```bash
git clone https://github.com/FreedomDevs/svc-punishments
cd svc-punishments
```

---

## Установка зависимостей

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Запуск

```bash
uvicorn app.main:app --host 0.0.0.0 --port 9010 --reload
```

Документация будет доступна по адресу:

```
http://localhost:9010/docs
```

---

# Пример запросов

## Создание наказания

POST `/v1/punishments`

```json
{
  "userId": "c9a6467e-3d02-4f29-95c2-7a0c1d0c7c12",
  "type": "TEMP_BAN",
  "reason": "Cheating",
  "serverName": "survival-1",
  "duration": 3600
}
```

Ответ:

```
201 Created
```

```json
{
  "punishmentId": "0c0c7a0c-7a0c-7a0c-7a0c-0c0c7a0c7a0c"
}
```

---

## Проверка активных наказаний

GET `/v1/punishments/check?userId={userId}&serverName={serverName}`

Ответ:

```json
{
  "punishments": [
    {
      "type": "TEMP_BAN",
      "reason": "Cheating",
      "issuedBy": "admin-id",
      "expiresAt": "2026-03-15T12:00:00Z"
    }
  ]
}
```

---

## История наказаний

GET `/v1/punishments/history?userId={userId}`

Возвращает полную историю наказаний игрока.

---

## Отмена наказания

POST `/v1/punishments/{punishmentId}/revoke`

```json
{
  "revokedBy": "admin-id",
  "reason": "Appeal accepted"
}
```

Ответ:

```
200 OK
```

---

# Эндпоинты

| Метод | Endpoint                    | Описание                     |
| ----- | --------------------------- | ---------------------------- |
| POST  | /v1/punishments             | Выдать наказание             |
| GET   | /v1/punishments/check       | Проверить активные наказания |
| GET   | /v1/punishments/history     | Получить историю наказаний   |
| POST  | /v1/punishments/{id}/revoke | Отменить наказание           |
| GET   | /health                     | Сервер здоров                |
| GET   | /live                       | Сервер жив                   |

---

# HTTP коды статусов

| Код                    | HTTP | Описание                     |
| ---------------------- | ---- | ---------------------------- |
| PUNISHMENT_CREATED_OK  | 201  | Наказание успешно выдано     |
| PUNISHMENTS_CHECK_OK   | 200  | Проверка наказаний выполнена |
| PUNISHMENTS_HISTORY_OK | 200  | История получена             |
| PUNISHMENT_REVOKED_OK  | 200  | Наказание отменено           |
| PUNISHMENT_NOT_FOUND   | 404  | Наказание не найдено         |
| INVALID_REQUEST        | 400  | Некорректный запрос          |
| INTERNAL_ERROR         | 500  | Внутренняя ошибка сервера    |
| HEALTH_OK              | 200  | Сервис здоров                |
| LIVE_OK                | 200  | Сервис жив                   |

---

Если хочешь, я могу ещё:

* сделать **более "production" README как в крупных open-source сервисах**,
* добавить **структуру проекта**,
* добавить **описание БД**,
* или **оформить так, чтобы выглядело как реальный enterprise-микросервис** (это часто требуют на стажировках и в компаниях).
