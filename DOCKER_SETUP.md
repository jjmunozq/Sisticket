# Ticket System - Docker Setup

## Estructura Docker

La aplicación está dockerizada con los siguientes servicios:

- **MySQL**: Base de datos
- **PHP-FPM**: Aplicación PHP
- **Nginx**: Servidor web
- **Prometheus**: Recopilador de métricas
- **Node Exporter**: Métricas del sistema
- **MySQL Exporter**: Métricas de la base de datos
- **Grafana**: Visualización de métricas

## Requisitos

- Docker >= 20.10
- Docker Compose >= 1.29
- Linux/Mac o WSL2 en Windows

## Instalación y Ejecución

### 1. Construir e iniciar los servicios

```bash
docker-compose up -d
```

Esto descargará las imágenes necesarias y levantará todos los servicios.

## Acceso a la aplicación

- **Aplicación Ticket**: http://localhost
- **Grafana**: http://localhost:3000 (usuario: `admin`, contraseña: `admin123`)
- **Prometheus**: http://localhost:9090
- **MySQL**: localhost:3306 (usuario: `ticketuser`, contraseña: `ticketpass123`)
- **Node Exporter**: http://localhost:9101/metrics
- **MySQL Exporter**: http://localhost:9105/metrics

### 3. Ver logs

```bash
# Todos los servicios
docker-compose logs -f

# Servicio específico
docker-compose logs -f nginx
docker-compose logs -f app
docker-compose logs -f mysql
```

### 4. Detener servicios

```bash
docker-compose down
```

### 5. Detener y eliminar volúmenes (limpieza completa)

```bash
docker-compose down -v
```

## Configuración

### Variables de Entorno

El archivo `.env` contiene las variables de configuración:

```
MYSQL_ROOT_PASSWORD=rootpass123
MYSQL_DATABASE=tmp_ticket
MYSQL_USER=ticketuser
MYSQL_PASSWORD=ticketpass123
GRAFANA_ADMIN_PASSWORD=admin123
```

### Puertos Utilizados

| Servicio | Puerto | Acceso |
|----------|--------|--------|
| Nginx | 80, 443 | http://localhost |
| MySQL | 3306 | localhost:3306 |
| Prometheus | 9090 | http://localhost:9090 |
| Grafana | 3000 | http://localhost:3000 |
| Node Exporter | 9101 | http://localhost:9101 |
| MySQL Exporter | 9105 | http://localhost:9105 |

## Métricas y Monitoreo

### Prometheus

Scrapes automáticos cada 15 segundos de:

- **Node Exporter**: CPU, memoria, disco, red
- **MySQL Exporter**: Conexiones, queries, rendimiento

Para ver las métricas disponibles:
```
http://localhost:9090/api/v1/label/__name__/values
```

### Grafana

Dashboards preconfigurados:

1. **Sistema**: CPU, memoria, disco (Node Exporter)
2. **MySQL**: Conexiones activas, queries, latencia

Para agregar nuevos dashboards:
1. Accede a http://localhost:3000
2. Click en "+"
3. Selecciona "Dashboard"
4. Configura las métricas de Prometheus

## Desarrollo

### Editar código

El código en `./TICKET/` está sincronizado con el contenedor. Los cambios se reflejan inmediatamente.

### Instalar paquetes PHP

```bash
docker-compose exec app composer install
```

### Ejecutar comandos en la aplicación

```bash
docker-compose exec app php -v
docker-compose exec mysql mysql -u ticketuser -p tmp_ticket
```

### Reconstruir después de cambios en Dockerfile

```bash
docker-compose up -d --build
```

## Problemas Comunes

### MySQL no se conecta

Espera a que MySQL esté completamente inicializado (puede tomar ~30 segundos):

```bash
docker-compose logs mysql | grep "ready for connections"
```

### Permisos en archivos

Si hay problemas de permisos:

```bash
docker-compose exec app chown -R www-data:www-data /var/www/html
```

### Limpiar y reiniciar todo

```bash
docker-compose down -v
rm -rf grafana_data prometheus_data mysql_data  # Si existen
docker-compose up -d
```

## Seguridad en Producción

Para usar en producción, cambiar:

1. Contraseñas en `.env`
2. Certificados SSL en `./ssl/`
3. Configurar HTTPS en `nginx.conf`
4. Configurar firewall para limitar acceso a puertos

## Backups

### Backup de la base de datos

```bash
docker-compose exec mysql mysqldump -u root -prootpass123 tmp_ticket > backup.sql
```

### Restore desde backup

```bash
docker-compose exec -T mysql mysql -u root -prootpass123 tmp_ticket < backup.sql
```

## Recursos Adicionales

- [Docker Documentation](https://docs.docker.com/)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/grafana/)
- [Nginx Documentation](https://nginx.org/en/docs/)
