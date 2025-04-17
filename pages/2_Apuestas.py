import streamlit as st
import base64
from pathlib import Path
import pandas as pd
import numpy as np
import os
import psycopg2

# -----------------------------------------
# Configuración de la página
# -----------------------------------------
st.set_page_config(layout="wide")

# -----------------------------------------
# Función para convertir imágenes a Base64
# -----------------------------------------
def to_base64(img_path: Path) -> str:
    if img_path.exists():
        return base64.b64encode(img_path.read_bytes()).decode()
    return ""

# -----------------------------------------
# DataFrame vacío de apuestas
# -----------------------------------------
def get_empty_bets_df() -> pd.DataFrame:
    return pd.DataFrame({
        "Nombre":       pd.Series(dtype="str"),
        "Monto":        pd.Series(dtype="float"),
        "Equipo":       pd.Series(dtype="str"),
        "Multiplicado": pd.Series(dtype="float"),
        "Check":        pd.Series(dtype="bool"),
        "Notas":        pd.Series(dtype="str"),
    })

# -----------------------------------------
# Funciones de conexión a PostgreSQL
# -----------------------------------------
def get_db_connection():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    return psycopg2.connect(DATABASE_URL, sslmode="require")

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bets (
            id SERIAL PRIMARY KEY,
            nombre TEXT,
            monto REAL,
            equipo TEXT,
            multiplicado REAL,
            check_col BOOLEAN,
            notas TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def load_bets() -> pd.DataFrame:
    conn = get_db_connection()
    df = pd.read_sql(
        """
        SELECT
          nombre    AS "Nombre",
          monto     AS "Monto",
          equipo    AS "Equipo",
          multiplicado AS "Multiplicado",
          check_col    AS "Check",
          notas      AS "Notas"
        FROM bets
        ORDER BY id
        """,
        conn
    )
    conn.close()
    return df if not df.empty else get_empty_bets_df()

def save_bets(df: pd.DataFrame):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("TRUNCATE bets")
    for _, row in df.iterrows():
        cur.execute("""
            INSERT INTO bets (nombre, monto, equipo, multiplicado, check_col, notas)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            row["Nombre"],
            float(row["Monto"]),
            row["Equipo"],
            float(row["Multiplicado"]),
            bool(row["Check"]),
            row["Notas"]
        ))
    conn.commit()
    cur.close()
    conn.close()

# -----------------------------------------
# Inicializa la base de datos y carga datos
# -----------------------------------------
init_db()
if "df_bets" not in st.session_state:
    st.session_state.df_bets    = load_bets()
    # El borrador que usaremos en el editor:
    st.session_state.edited_df  = st.session_state.df_bets.copy()
    st.session_state.db_loaded  = True

# -----------------------------------------
# Inicializar estado de autenticación
# -----------------------------------------
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# -----------------------------------------
# Rutas de carpetas
# -----------------------------------------
BASE_DIR   = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / "imagenes"
SOCIAL_DIR = BASE_DIR / "social"
YAPE_PATH  = BASE_DIR / "yape"

# -----------------------------------------
# Inyección de CSS global (tu CSS completo aquí)
# -----------------------------------------
pato_b64 = to_base64(SOCIAL_DIR / "pato.gif")
st.markdown(f"""
<style>
  .stApp {{
    background: url("data:image/gif;base64,{pato_b64}") center 70% / cover fixed #1a1a1a;
    color: #FFF !important;
  }}
  /* ... resto de tu CSS ... */
</style>
""", unsafe_allow_html=True)

# -----------------------------------------
# Sidebar: Login de Admin + Guardar
# -----------------------------------------
with st.sidebar.expander("ADMIN (LOGIN)", expanded=True):
    admin_creds = {'yair': 'yair123', 'fernando': 'fernando123'}
    if not st.session_state.is_admin:
        user = st.text_input("Usuario", key="login_user")
        pwd  = st.text_input("Contraseña", type="password", key="login_pass")
        if st.button("Ingresar", key="login_btn"):
            if user in admin_creds and admin_creds[user] == pwd:
                st.session_state.is_admin = True
                st.success("👑 Admin autenticado")
            else:
                st.error("Credenciales incorrectas")
    else:
        st.write("👑 Admin conectado")
        if st.button("🔒 Cerrar sesión", key="logout_btn"):
            st.session_state.is_admin = False

        # Botón para guardar el borrador en la DB
        if st.button("💾 Guardar apuestas", key="save_btn"):
            st.session_state.df_bets = st.session_state.edited_df.copy()
            save_bets(st.session_state.df_bets)
            st.success("¡Apuestas guardadas!")

# -----------------------------------------
# Header, Yape y demás bloques visuales
# (copia aquí todo tu HTML/MD con logos e imágenes)
# -----------------------------------------

# -----------------------------------------
# Función para recalcular montos
# -----------------------------------------
def recalc(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Monto"]         = pd.to_numeric(df["Monto"], errors="coerce")
    df["Multiplicado"]  = df["Monto"] * 1.8
    return df.fillna({
        "Nombre": "",
        "Monto": 0.0,
        "Equipo": "",
        "Multiplicado": 0.0,
        "Check": False,
        "Notas": ""
    })

# -----------------------------------------
# Editor de apuestas (solo Admin)
# -----------------------------------------
if st.session_state.is_admin:
    with st.container():
        st.markdown("<div class='tabla-container'>", unsafe_allow_html=True)
        # Partimos siempre del borrador recalc
        initial = recalc(st.session_state.edited_df)
        edited  = st.data_editor(
            initial,
            column_config={
                "Nombre":       st.column_config.TextColumn("Nombre"),
                "Monto":        st.column_config.NumberColumn("Monto", step=1.0, format="%.2f"),
                "Equipo":       st.column_config.SelectboxColumn("Equipo", options=["", "Radiant", "Dire"]),
                "Multiplicado": st.column_config.NumberColumn("Multiplicado", disabled=True, format="%.2f"),
                "Check":        st.column_config.CheckboxColumn("Check"),
                "Notas":        st.column_config.TextColumn("Notas"),
            },
            key="bets_editor",
            num_rows="dynamic",
            use_container_width=True
        )
        # Actualizamos inmediatamente el borrador,
        # de modo que en el siguiente rerun Multiplicado refleje el cambio
        st.session_state.edited_df = recalc(edited)
        st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------------------
# Métricas siempre visibles
# -----------------------------------------
df_to_show = (st.session_state.edited_df
              if st.session_state.is_admin
              else st.session_state.df_bets)

sum_r      = df_to_show[df_to_show["Equipo"] == "Radiant"]["Monto"].sum()
sum_d      = df_to_show[df_to_show["Equipo"] == "Dire"]["Monto"].sum()
difference = abs(sum_r - sum_d)

with st.container():
    st.markdown("<div class='metrics-container'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Radiant", f"{sum_r:.2f}")
    c2.metric("Dire",    f"{sum_d:.2f}")
    c3.metric("Diferencia", f"{difference:.2f}")
    st.markdown("</div>", unsafe_allow_html=True)

