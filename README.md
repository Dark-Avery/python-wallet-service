# Wallet Service

REST API для кошельков на `FastAPI + PostgreSQL + SQLAlchemy 2 + Alembic`.

Сервис поддерживает:
- пополнение кошелька
- списание средств
- получение текущего баланса

Основной акцент решения:
- понятная слоистая архитектура
- корректная работа с PostgreSQL
- безопасная обработка конкурентных операций
- покрытие unit, API, integration и concurrency тестами

## Требования

- Python `3.12`
- Docker и `docker compose`

## Локальная установка

Создать виртуальное окружение и установить зависимости для разработки и тестов:

```bash
python3.12 -m venv .venv
.venv/bin/pip install -e ".[test]"
```

## Запуск

Поднять приложение и PostgreSQL:

```bash
docker compose up -d --build
```

Приложение будет доступно на:

- `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

Остановить окружение:

```bash
docker compose down -v
```

## Миграции

Ниже команды для локального запуска. Они предполагают, что PostgreSQL уже доступен по дефолтному URL из [alembic.ini](/mnt/c/programming/work/it-akad/alembic.ini) или что явно задан `DATABASE_URL`.

Применить миграции вручную:

```bash
.venv/bin/alembic upgrade head
```

Откатить миграции:

```bash
.venv/bin/alembic downgrade base
```

При запуске контейнера приложения миграции применяются автоматически перед стартом API.

## Тесты

Запустить все тесты:

```bash
.venv/bin/python -m pytest -q -s
```

Что входит в прогон:

- unit tests
- API tests
- integration tests с реальным PostgreSQL через `testcontainers`
- concurrency tests с реальным PostgreSQL

Если Docker daemon недоступен, integration/concurrency тесты будут пропущены.

Запустить только integration и concurrency слой:

```bash
.venv/bin/python -m pytest -q -s -m integration
```

## API

### POST `/api/v1/wallets/{wallet_uuid}/operation`

Тело запроса:

```json
{
  "operation_type": "DEPOSIT",
  "amount": 100
}
```

Поддерживаемые операции:

- `DEPOSIT`
- `WITHDRAW`

Ответ:

```json
{
  "wallet_uuid": "11111111-1111-1111-1111-111111111111",
  "balance": 100
}
```

Ошибки:

- `404`, если `WITHDRAW` выполняется по несуществующему кошельку
- `409`, если средств недостаточно
- `422`, если некорректен `wallet_uuid` или тело запроса

### GET `/api/v1/wallets/{wallet_uuid}`

Ответ:

```json
{
  "wallet_uuid": "11111111-1111-1111-1111-111111111111",
  "balance": 100
}
```

Ошибки:

- `404`, если кошелек не найден

## Архитектура

Проект разделен на простые слои:

- `api`
  HTTP-роуты, request/response схемы и dependency wiring
- `application`
  бизнес-логика кошелька и контракты зависимостей
- `domain`
  сущности и доменные ошибки
- `infrastructure`
  конфиг, SQLAlchemy-модели, сессии и PostgreSQL-репозиторий

Основные файлы:

- [src/wallet_service/api/routes.py](/mnt/c/programming/work/it-akad/src/wallet_service/api/routes.py)
- [src/wallet_service/application/services.py](/mnt/c/programming/work/it-akad/src/wallet_service/application/services.py)
- [src/wallet_service/application/contracts.py](/mnt/c/programming/work/it-akad/src/wallet_service/application/contracts.py)
- [src/wallet_service/infrastructure/db/repositories.py](/mnt/c/programming/work/it-akad/src/wallet_service/infrastructure/db/repositories.py)
- [src/wallet_service/infrastructure/db/models.py](/mnt/c/programming/work/it-akad/src/wallet_service/infrastructure/db/models.py)

## Конкурентность

Критичный сценарий задания: несколько запросов могут одновременно менять один и тот же кошелек.

Для этого используются два разных механизма:

- `DEPOSIT`
  реализован атомарно через PostgreSQL `INSERT ... ON CONFLICT DO UPDATE`
- `WITHDRAW`
  выполняется через `SELECT ... FOR UPDATE`, чтобы конкурентные списания по одному кошельку сериализовались

Дополнительно инвариант `balance >= 0` защищен на уровне базы через `CHECK CONSTRAINT`.

Это проверяется отдельными concurrency-тестами на реальном PostgreSQL.

## Допущения

- баланс хранится как целое число
- `amount` всегда должен быть положительным
- отдельного endpoint для создания кошелька нет
- `DEPOSIT` создает кошелек, если его еще не существует
- `WITHDRAW` по несуществующему кошельку возвращает `404`
- история операций, аутентификация и многовалютность находятся вне scope задания
- основной и поддерживаемый runtime path для сервиса и тестов это PostgreSQL
