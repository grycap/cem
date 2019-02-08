FROM php:apache
MAINTAINER serlohu@upv.es
LABEL version = '0.0.1'

RUN apt-get update && apt-get install --no-install-recommends apache2 -y && docker-php-ext-install mysqli
COPY src/ /var/www/html/pyme
RUN mkdir /var/www/www-data && chown www-data /var/www/

EXPOSE 80
WORKDIR /var/www/html
CMD ["apache2-foreground"]