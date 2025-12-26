# MEMPOOL FIREHOSE
![CI status](https://github.com/ctsdm/tritemius-case-study/actions/workflows/ci.yml/badge.svg)

## Arquitectura

```mermaid
  flowchart TB
      Client([Cliente]) -->|POST /transactions| API[API FastAPI]
      API -->|202 Accepted| Client
      API -->|Publish| RMQ[(RabbitMQ)]
      RMQ -->|Consume| Worker
      subgraph Worker["Worker (x N replicas)"]
      Classify[Clasificar con Oráculo ML]
      end
      Worker -->|"risk > 0.8"| DB[(PostgreSQL)]
```

### Componentes

| Componente | Descripción |
|------------|-------------|
| **API** | Recibe transacciones y las encola. Responde `202 Accepted` de forma inmediata. |
| **RabbitMQ** | Cola de mensajes que desacopla la recepción del procesamiento. |
| **Workers** | Consumen transacciones, ejecutan el oráculo ML y persisten resultados de alta prioridad. |
| **PostgreSQL** | Almacena únicamente transacciones con `risk_score > 0.8`. |

### Flujo de datos

1. El cliente envía una transacción vía `POST /transactions`
2. La API añade a la cola el mensaje en RabbitMQ y responde `202`
3. Un worker disponible consume el mensaje
4. El oráculo clasifica la transacción y calcula el `risk_score`
5. Si `risk_score > 0.8`, se persiste en PostgreSQL

Esta arquitectura permite escalar los workers horizontalmente y desacoplar el endpoint de la carga de procesamiento de los workers.

## Ejecucion de la arquitectura
Se necesita `uv` version >= 0.9 y `docker`
### Levantar la arquitectura
1. Clona el repositorio y accede al directorio creado.
2. Crea un fichero `.env` con los contenidos de `.env.example`:
```bash
cp .env.example .env
```
3. Levanta los contenedores de PostgreSQL, RabbitMQ, FastAPI y Workers (2 instancias):
```bash
docker compose up -d
```
4. Para detener los contenedores:
```bash
docker compose down
```
### Scripts para ejecutar pruebas
En las pruebas, se espera que el 20% de los resultados sean de alta prioridad ya que se ha usado una distribucion uniforme para el calculo de `risk_score`.
- Enviar 20 transactions a `/transactions` y consultar la base de datos:
```bash
uv run scripts/verify_flow.py
```
- Prueba de estres al endpoint `/transactions` con monitoreo de como se vacia la cola:
```bash
# Prueba basica, 20 requests concurrentes hasta un total de 1000.
uv run scripts/load_test.py
# Prueba mas pesada, 50 requests concurrentes hasta un total de 5000.
uv run scripts/load_test.py --requests 5000 --concurrency 50
```
- Obtener estadisticas de la base de datos:
```bash
# Estadisticas totales
uv run scripts/query_db.py
# Obtener las ultimas 10 transacciones
uv run scripts/query_db.py --recent 10
```

## Desarrollo en local
Se necesita uv versión >= 0.9 y `docker`
1. Clona el repositorio y accede al directorio creado.
2. Crea un fichero `.env` con los contenidos de `.env.example`:
```bash
cp .env.example .env
```
3. Instala las dependencias necesarias:
```bash
uv sync --dev
```
4. Levanta los contenedores de PostgreSQL y RabbitMQ:
```bash
docker compose -f docker-compose-dev.yaml up -d
```
5. Ejecuta las migraciones para inicializar la base de datos:
```bash
uv run alembic upgrade head
```
6. Ejecuta FastAPI en una terminal; en caso de que el puerto esté ocupado, cambia `API_PORT` en `.env` a otro puerto:
```bash
source .env && uv run fastapi dev src/api/main.py --port=$API_PORT
```
7. Ejecuta el worker en otra terminal:
```bash
uv run python -m src.worker.main
```
8. Para detener los contenedores:
```bash
docker compose -f docker-compose-dev.yaml down
```
