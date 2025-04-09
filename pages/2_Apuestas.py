import os
import psycopg2

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL is None:
    print("DATABASE_URL no está definida")
else:
    print("Conectando a:", DATABASE_URL)
    try:
        conn = psycopg2.connect(DATABASE_URL)
        print("Conexión exitosa")
        conn.close()
    except Exception as e:
        print("Error de conexión:", e)
