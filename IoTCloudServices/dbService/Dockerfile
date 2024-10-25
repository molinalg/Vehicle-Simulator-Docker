FROM mariadb:latest

# Actualiza el sistema e instala Mysql
RUN apt update && apt upgrade -y

RUN mkdir -p /docker-entrypoint-initdb.d/

ADD initial_script.sql /docker-entrypoint-initdb.d/ddl.sql