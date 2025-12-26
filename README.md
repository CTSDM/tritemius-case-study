# MEMPOOL FIREHOSE
![CI status](https://github.com/ctsdm/tritemius-case-study/actions/workflows/ci.yml/badge.svg)

## Desarrollo en local
Se necesita uv version >= 0.9 y docker-compose
1. Clona el repositorio y accede al directorio creado.
2. Crea un fichero `.env` con los contenidos de `.env.example`:
```bash
cp .env.example .env
```
3. Instala las dependencias necesarias:
```bash
uv sync --dev
```
4. Levanta los contenedores de postgres y rabbitmq:
```bash
docker-compose -f docker-compose-dev.yaml up -d
```
5. Ejecuta las migraciones para inicializar la base de datos:
```bash
uv run alembic upgrade head
```
6. Ejecuta FastAPI en una terminal; en caso de que el puerto este ocupado, cambia `API_PORT` en `.env` a otro puerto:
```bash
source .env && uv run fastapi dev src/api/main.py --port=$API_PORT
```
7. Ejecuta el worker en otra terminal:
```bash
uv run python -m src.worker.main
```
8. Para detener los contenedores:
```bash
docker-compose -f docker-compose-dev.yaml down
```
