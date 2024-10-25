FROM ubuntu:latest

# Actualiza el sistema e instala Mosquitto
RUN apt update && apt upgrade -y && \
    apt install -y mosquitto mosquitto-clients

# Crea el archivo de contraseñas e introduce el primer par de credenciales
RUN mkdir -p /etc/mosquitto-pw && \
    touch /etc/mosquitto-pw/passwd && \
    mosquitto_passwd -b /etc/mosquitto-pw/passwd g07 g07pw && \
    mosquitto_passwd -b /etc/mosquitto-pw/passwd fic_server fic_password

# Lanza Mosquitto
CMD ["/usr/sbin/mosquitto", "-c", "/etc/mosquitto/mosquitto.conf"]