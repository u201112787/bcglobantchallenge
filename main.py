from flask import Flask, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import DB_CONFIG, AWS_CONFIG
import boto3
import pandas as pd
from sqlalchemy import exc, Table, MetaData, inspect
from sqlalchemy.orm import Session
import os
import pandas as pd

app = Flask(__name__)

# S3 Configuration
session = boto3.Session(
    aws_access_key_id=AWS_CONFIG['aws_access_key_id'],
    aws_secret_access_key=AWS_CONFIG['aws_secret_access_key'],
    region_name=AWS_CONFIG.get('region_name', 'us-west-2')  # Región predeterminada si no se especifica
)
s3_client = session.resource('s3')

# PostgreSQL Configuration
DB_HOST = DB_CONFIG['DB_HOST']
DB_PORT = DB_CONFIG['DB_PORT']
DB_NAME = DB_CONFIG['DB_NAME']
DB_USER = DB_CONFIG['DB_USER']
DB_PASSWORD = DB_CONFIG['DB_PASSWORD']

# Cambiar 'postgresql+psycopg2' por 'postgresql+psycopg'
engine = create_engine(f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "API is running"})

@app.route("/upload-csv", methods=["POST"])
def upload_csv():
    try:
        bucket_name = request.json.get("bucket_name")
        key_file = request.json.get("key_file")
        table_name = request.json.get("table")

        if not bucket_name:
            return jsonify({"error": "bucket_name is required"}), 400
        if not key_file:
            return jsonify({"error": "key_file is required"}), 400
        if not table_name:
            return jsonify({"error": "table is required"}), 400

        rows_inserted = process_csv(bucket_name, key_file, table_name)
        return jsonify({"message": f"Successfully uploaded {rows_inserted} rows from {key_file} to {table_name}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/batch-insert", methods=["POST"])
def batch_insert_data():
    try:
        data = request.json.get("data")
        table_name = request.json.get("table_name")
        if not data:
            return jsonify({"error": "data is required"}), 400
        if not table_name:
            return jsonify({"error": "table_name is required"}), 400

        rows_inserted = batch_insert(data, table_name)
        return jsonify({"message": f"Successfully inserted {rows_inserted} rows into {table_name}"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 400

# S3 download and processing
def get_columnnames(table):
    inspector = inspect(engine)
    columns = inspector.get_columns(table)
    column_names = [column['name'] for column in columns]
    return column_names

def process_csv(bucket_name: str, key_file: str, table_name: str):
    # script_directory = os.path.dirname(os.path.abspath(__file__))
    data_download_directory = '/app/data_download'
    csv_path = os.path.join(data_download_directory, table_name)
    try:
        s3_client.Bucket(bucket_name).download_file(key_file, csv_path)
        print(f'Archivo CSV descargado en: {csv_path}')
    except Exception as e:
        print(f'Error al descargar el archivo: {str(e)}')

    df = pd.read_csv(csv_path, header=None, names=get_columnnames(table_name))
    try: 
        df.to_sql(table_name, engine, if_exists="replace", index=False, method='multi', chunksize=1000)
    except Exception as e:
        print(f'Error al cargar el archivo: {str(e)}')
    engine.dispose()
    os.remove(csv_path)

# Batch insert
def batch_insert(data, table_name):
    session = SessionLocal()
    try:
        metadata = MetaData(bind=session.bind)
        table = Table(table_name, metadata, autoload_with=session.bind)
        with session.begin():
            session.execute(table.insert(), data)
        return len(data)
    except exc.SQLAlchemyError as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_db_connection():
    return engine.connect()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
