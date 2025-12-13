FROM php:7.4-fpm

# Instalar dependencias
RUN apt-get update && apt-get install -y \
    default-mysql-client \
    zip \
    unzip \
    && docker-php-ext-install mysqli pdo pdo_mysql \
    && rm -rf /var/lib/apt/lists/*

# Copiar configuración PHP
COPY ./php.ini /usr/local/etc/php/php.ini

# Directorio de trabajo
WORKDIR /var/www/html

# Copiar código
COPY ./TICKET /var/www/html

# Permisos
RUN chown -R www-data:www-data /var/www/html

EXPOSE 9000

CMD ["php-fpm"]
