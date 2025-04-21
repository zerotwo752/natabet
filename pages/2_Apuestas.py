import psycopg2
import os

# Configura tu conexión a Railway (usa tu URL real si es diferente)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:wKuijKwZqsUgOZJhiEqXraNgXugQnShg@caboose.proxy.rlwy.net:25343/railway?sslmode=require"
)

def eliminar_tabla_bets():
    try:
        conn = psycopg2.connect(DATABASE_URL, sslmode="require")
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS bets;")
        conn.commit()
        print("✅ Tabla 'bets' eliminada correctamente.")
    except Exception as e:
        print("❌ Error al eliminar la tabla 'bets':", e)
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    eliminar_tabla_bets()
