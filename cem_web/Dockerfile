FROM php:apache
MAINTAINER serlohu@upv.es
LABEL version = '0.0.1'

RUN apt-get update && apt-get install --no-install-recommends apache2 -y && docker-php-ext-install mysqli
COPY ./src/ /var/www/html/
RUN mkdir /var/www/www-data && chown www-data /var/www/
COPY ./docker-entrypoint.sh /
RUN chmod u+x /docker-entrypoint.sh

EXPOSE 80
WORKDIR /var/www/html

ENTRYPOINT ["/docker-entrypoint.sh"]
CMD ["apache2-foreground"]
