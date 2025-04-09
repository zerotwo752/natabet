import os
import psycopg2
import streamlit as st

DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL is None:
    st.error("DATABASE_URL no está definida")
else:
    st.write("Conectando a:", DATABASE_URL)
    try:
        conn = psycopg2.connect(DATABASE_URL)
        st.success("Conexión exitosa")
        conn.close()
    except Exception as e:
        st.error(f"Error de conexión: {e}")
