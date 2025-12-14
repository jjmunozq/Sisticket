#!/usr/bin/env python3
"""
Herramienta de despliegue automático para el proyecto.
Funciones:
 - opcional: pull de imágenes
 - docker-compose up -d (con/ sin build)
 - espera a que los servicios queden 'Up' / 'healthy' (si tienen healthcheck)
 - opcional: ejecutar comandos post-deploy (migrations, seeds, tests)

Uso básico:
  python3 tools/deploy.py --pull --build --timeout 300

Requiere: Python 3.6+, Docker Compose en PATH
"""

import argparse
import subprocess
import sys
import time
from typing import List
import importlib.util
import os


def run(cmd: List[str], capture=False, check=True):
    print("$", " ".join(cmd))
    if capture:
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if check and res.returncode != 0:
            print(res.stdout)
            print(res.stderr, file=sys.stderr)
            raise SystemExit(res.returncode)
        return res.stdout
    else:
        res = subprocess.run(cmd)
        if check and res.returncode != 0:
            raise SystemExit(res.returncode)
        return None


def get_compose_services(compose_file: str) -> List[str]:
    # Obtiene la lista de servicios del compose
    out = run(["docker-compose", "-f", compose_file, "config", "--services"], capture=True)
    services = [s.strip() for s in out.splitlines() if s.strip()]
    return services


def wait_for_services(services: List[str], project_dir: str, timeout: int = 300):
    start = time.time()
    print(f"Esperando hasta {timeout}s a que los servicios estén 'Up' y (si aplica) 'healthy'...")
    while True:
        elapsed = time.time() - start
        if elapsed > timeout:
            print("Timeout esperando servicios. Mostrar estado actual:")
            run(["docker-compose", "ps"], check=False)
            raise SystemExit(2)

        out = run(["docker-compose", "ps"], capture=True)
        all_ok = True
        lines = out.splitlines()
        # Buscar cada servicio en el output y revisa su columna State
        for svc in services:
            matching = [l for l in lines if l.startswith(svc + " ") or (" " + svc + " ") in l]
            if not matching:
                # puede que el formato no contenga el servicio name al inicio; fall-back
                if svc not in out:
                    print(f"Servicio {svc} no aparece en 'docker-compose ps' aún.")
                    all_ok = False
                    continue
                else:
                    matching = [l for l in lines if svc in l]
            state_ok = False
            for m in matching:
                # heurística: buscar 'Up' y opcionalmente 'healthy'
                if "Up" in m and ("(healthy)" in m or "(unhealthy)" not in m):
                    state_ok = True
                    break
            if not state_ok:
                all_ok = False
                print(f"Servicio {svc} aún no listo: línea ejemplo -> {matching[0] if matching else '<no-line>'}")
        if all_ok:
            print("Todos los servicios están arriba y saludables (o sin healthcheck).")
            return
        time.sleep(5)


def main():
    parser = argparse.ArgumentParser(description="Deploy helper for Ticket-master (docker-compose)")
    parser.add_argument("--compose-file", default="docker-compose.yml", help="Path to docker-compose file")
    parser.add_argument("--pull", action="store_true", help="Pull images before starting")
    parser.add_argument("--build", action="store_true", help="Build images before starting")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds to wait for services")
    parser.add_argument("--post-cmd", action="append", help="Command to run after deployment (can be used multiple times)")
    parser.add_argument("--no-start-tests", dest="start_tests", action="store_false", help="Do not start test scripts after deploy")
    parser.set_defaults(start_tests=True)

    args = parser.parse_args()

    # Try loading configuration from tools/deploy_config.py if present
    cfg_path = os.path.join(os.path.dirname(__file__), "deploy_config.py")
    cfg = None
    if os.path.exists(cfg_path):
        spec = importlib.util.spec_from_file_location("deploy_config", cfg_path)
        cfg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cfg)

    # Merge config defaults if provided
    if cfg is not None:
        if hasattr(cfg, 'COMPOSE_FILE') and not parser.get_default('compose_file') == args.compose_file:
            # CLI override already applied; keep args.compose_file
            pass
        # Use config values if CLI did not set flags explicitly
        if not any(arg in sys.argv for arg in ("--pull",)) and getattr(cfg, 'PULL', False):
            args.pull = True
        if not any(arg in sys.argv for arg in ("--build",)) and getattr(cfg, 'BUILD', False):
            args.build = True
        if not any(arg in sys.argv for arg in ("--timeout",)):
            args.timeout = getattr(cfg, 'TIMEOUT', args.timeout)
        if not any(arg in sys.argv for arg in ("--no-start-tests",)):
            args.start_tests = getattr(cfg, 'START_TESTS', args.start_tests)
        # Post commands from config if not provided via CLI
        if args.post_cmd is None and getattr(cfg, 'POST_CMDS', None):
            args.post_cmd = list(getattr(cfg, 'POST_CMDS'))

    # Pull
    if args.pull:
        run(["docker-compose", "-f", args.compose_file, "pull"])

    # Build / Up
    up_cmd = ["docker-compose", "-f", args.compose_file, "up", "-d"]
    if args.build:
        up_cmd.append("--build")
    run(up_cmd)

    # Wait services
    try:
        services = get_compose_services(args.compose_file)
    except Exception:
        services = []
    if services:
        wait_for_services(services, ".", timeout=args.timeout)
    else:
        print("No se pudo enumerar servicios del compose; omitiendo espera automatizada.")

    # Ejecutar comandos post-deploy
    if args.post_cmd:
        for cmd in args.post_cmd:
            print(f"Ejecutando post-cmd: {cmd}")
            run(cmd.split(), check=False)

    # Start test scripts (opcional)
    if args.start_tests:
        print("Arrancando scripts de prueba (si existen)...")
        # Solo inicia los principales si están presentes
        run(["bash", "-c", "[ -x tools/test_start_all.sh ] && bash tools/test_start_all.sh || true"], check=False)

    print("Despliegue completado.")


if __name__ == '__main__':
    main()
