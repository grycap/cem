#!/bin/bash
set -e
DEFAULT_CEM_SERVER_IP="0.0.0.0"

if [ "$1" = 'apache2-foreground' ]; then

    if [[ -z "${CEM_SERVER_IP}" ]]; then
        CEM_SERVER_IP=${DEFAULT_CEM_SERVER_IP?}
    fi
    if [[ -z "${DB_PATH}" ]]; then
        DB_PATH=${DEFAULT_DB_PATH?}
    fi
    echo "CEM_SERVER_IP is ${CEM_SERVER_IP}"
    echo "cem.db must be mounted at /var/www/www-data/cem.db"

    sed -i 's/cem_host="XXX"/cem_host="'${CEM_SERVER_IP}'"/g' /var/www/html/config.php

    echo "Starting apache..."
    apache2-foreground

fi
exec "$@"