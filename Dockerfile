FROM python:3.9-slim

# Instalar las herramientas necesarias
RUN apt-get update && apt-get install -y \
    libpq-dev gcc && \
    apt-get clean

# Configurar el directorio de trabajo
WORKDIR /app


# Copiar el archivo de dependencias e instalar
COPY requirements.txt .
RUN mkdir -p /app/data_download
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código de la aplicación
COPY . .

# Exponer el puerto 5000 para Flask
EXPOSE 5000

CMD ["python", "main.py"]
