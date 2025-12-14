# Despliegue automático (Python)

Este documento explica cómo funciona y cómo usar la herramienta de despliegue automática incluida en el proyecto.

Archivos relevantes
- `tools/deploy.py` — Script principal de despliegue en Python. Ejecuta `docker-compose up -d`, espera a que los servicios estén listos, puede ejecutar comandos post-deploy y (opcionalmente) arranca los scripts de prueba.
- `tools/deploy_config.py` — Archivo de configuración separado y editable que define valores por defecto (como `PULL`, `BUILD`, `TIMEOUT`, `POST_CMDS`, `TEST_ENV`). El script `deploy.py` carga este archivo automáticamente si existe; los argumentos de línea de comandos tienen prioridad.
- `tools/test_start_all.sh` — Helper que arranca los scripts de prueba en background (genera PID files en la raíz del repo y escribe logs en `logs/`).
- `Makefile` — contiene el objetivo `deploy` que invoca `python3 tools/deploy.py --pull --build --timeout 600`.

Requisitos
- Docker y Docker Compose instalados y accesibles en el PATH.
- Python 3.6+ (solo para ejecutar `tools/deploy.py` localmente).
- Permisos de usuario para ejecutar Docker (ej. pertenecer al grupo `docker` o usar `sudo`).

Cómo usar

1) Ver la ayuda rápida

```bash
python3 tools/deploy.py --help
```

2) Despliegue rápido (usa valores por defecto del `deploy_config.py` si existe)

```bash
make deploy
```

Esto hará: `docker-compose pull` (si está habilitado), `docker-compose up -d` (con build si se solicita), esperará a que los servicios estén UP/healthy (timeout configurable) y lanzará `tools/test_start_all.sh` para arrancar los scripts de prueba.

3) Ejecutar manualmente con opciones

- Pull + build + esperar 10 minutos (600s):

```bash
python3 tools/deploy.py --pull --build --timeout 600
```

- No arrancar tests automáticos:

```bash
python3 tools/deploy.py --pull --build --no-start-tests
```

- Añadir comandos post deploy (ej. migraciones):

```bash
python3 tools/deploy.py --pull --build --post-cmd "docker-compose exec app php /var/www/html/migrate.php" --post-cmd "echo 'done'"
```

Configuración (editar `tools/deploy_config.py`)

Ejemplo de valores que puedes cambiar:

- `COMPOSE_FILE` — archivo compose a usar (por defecto `docker-compose.yml`).
- `PULL` — `True/False` para hacer `docker-compose pull` por defecto.
- `BUILD` — `True/False` para pasar `--build` a `docker-compose up`.
- `TIMEOUT` — segundos a esperar por servicios saludables.
- `POST_CMDS` — lista de comandos a ejecutar tras el `up`.
- `TEST_ENV` — diccionario con variables de entorno sugeridas para los scripts de prueba.

Ejemplo mínimo:

```py
COMPOSE_FILE = "docker-compose.yml"
PULL = True
BUILD = True
TIMEOUT = 600
POST_CMDS = ["docker-compose exec app php /var/www/html/seed.php"]
TEST_ENV = {"CONCURRENCY": "10", "BATCH_INSERT": "10000"}
```

Cómo el script aplica la configuración
- `deploy.py` carga `tools/deploy_config.py` si existe.
- Los valores en la CLI siempre tienen prioridad sobre la configuración.
- Si se configura `POST_CMDS` en el archivo de configuración y no se pasan `--post-cmd` en la CLI, el script usará `POST_CMDS`.

Logs y PIDs
- `tools/test_start_all.sh` crea PID files en la raíz: `.test_load_3h.pid`, `.test_db_stress.pid`, `.test_mysql_intensive.pid`.
- Los logs de cada test se escriben en `logs/` (ej.: `logs/test_db_stress.log`).

Detener y limpiar
- Para detener el stack sin eliminar volúmenes:

```bash
docker-compose down
```

- Para detener y eliminar volúmenes:

```bash
docker-compose down -v
```

- Para detener los scripts de prueba que arrancó `test_start_all.sh`:

```bash
for f in .test_*.pid; do [ -f "$f" ] && kill "$(cat $f)" && rm -f "$f"; done
```

Notas de seguridad y rendimiento
- El script ejecuta `docker-compose` y comandos shell: modifica `tools/deploy_config.py` y `POST_CMDS` con cuidado.
- Los tests que vienen con el repositorio generan una carga muy alta en la BD. Ejecuta en entornos controlados y monitoriza recursos (CPU, memoria, I/O).
