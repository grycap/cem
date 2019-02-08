#!/bin/bash
set -e
DEFAULT_CEM_SERVER_IP="0.0.0.0"
DEFAULT_DB_PATH="/var/www/www-data/cem.db"

if [ "$1" = 'apache2-foreground' ]; then

    if [[ -z "${CEM_SERVER_IP}" ]]; then
        CEM_SERVER_IP=${DEFAULT_CEM_SERVER_IP?}
    fi
    if [[ -z "${DB_PATH}" ]]; then
        DB_PATH=${DEFAULT_DB_PATH?}
    fi
    echo "CEM_SERVER_IP is ${CEM_SERVER_IP}"
    echo "DB_PATH is ${DB_PATH}"
    
    sed -i 's/cem_host=""/cem_host="'${CEM_SERVER_IP}'"/g' /var/www/html/config.php
    sed -i 's/db=""/db="'${DB_PATH}'"/g' /var/www/html/config.php

    echo "Starting apache..."
    apache2-foreground

fi
exec "$@"