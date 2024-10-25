# Usa la imagen base de Python 3.11.1
FROM python:3.11.1

# Copia el código desde la carpeta ./code a /usr/src/app en el contenedor
COPY ./code /usr/src/app

# Establece /usr/src/app como directorio de trabajo
WORKDIR /usr/src/app

# Instala los paquetes necesarios desde requirements.txt
COPY ./code/requirements.txt /usr/src/app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Ejecuta el código incluido en message_router.py
CMD ["python", "message_router.py"]