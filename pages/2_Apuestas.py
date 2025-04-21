import streamlit as st
import base64
from pathlib import Path
import pandas as pd
import psycopg2
import os
import re

# -----------------------------------------
# Configuración básica
# -----------------------------------------
st.set_page_config(layout="wide")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:...@...")
BASE_DIR = Path(__file__).parent
IMAGES_DIR = BASE_DIR / "imagenes"
SOCIAL_DIR = BASE_DIR / "social"
YAPE_PATH = BASE_DIR / "yape"

# -----------------------------------------
# Funciones utilitarias
# -----------------------------------------
def to_base64(img_path: Path) -> str:
    return base64.b64encode(img_path.read_bytes()).decode() if img_path.exists() else ""

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

# Inicializar tablas: bets, admins, apostadores
@st.cache_resource
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # tabla de apuestas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bets (
            id SERIAL PRIMARY KEY,
            game_id INT,
            nombre TEXT,
            monto REAL,
            equipo TEXT,
            notas TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    # tabla de apostadores
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users_apostador (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    conn.commit()
    cur.close(); conn.close()

# Verificar contraseña
def valid_password(pw: str) -> bool:
    # mínimo 7 caracteres, 1 mayúscula, 1 símbolo
    return bool(re.match(r'^(?=.*[A-Z])(?=.*\W).{7,}$', pw))

# -----------------------------------------
# Inicializar DB
# -----------------------------------------
init_db()

# -----------------------------------------
# Sidebar: Admin + Apostador
# -----------------------------------------
st.sidebar.markdown("### 👑 Admin")
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

with st.sidebar.expander("Admin Login", expanded=True):
    if not st.session_state.is_admin:
        user = st.text_input("Usuario Admin", key="admin_user")
        pwd = st.text_input("Contraseña", type="password", key="admin_pwd")
        if st.button("Ingresar Admin"):
            # credenciales estáticas o DB
            if user == 'yair' and pwd == 'yair123':
                st.session_state.is_admin = True
                st.success("Admin autenticado")
            else:
                st.error("Credenciales incorrectas")
    else:
        st.write("Admin conectado")
        if st.button("Cerrar sesión Admin"):
            st.session_state.is_admin = False

st.sidebar.markdown("---")
st.sidebar.markdown("### 🎲 Apostador")
if 'apostador' not in st.session_state:
    st.session_state.apostador = None

with st.sidebar.expander("Login / Registro", expanded=True):
    mode = st.radio("Selecciona acción", ("Login", "Registrarse"), key="mode_user")
    username = st.text_input("Usuario", key="usr")
    password = st.text_input("Contraseña", type="password", key="pwd")
    conn = get_db_connection()
    cur = conn.cursor()
    if mode == "Registrarse":
        if st.button("Crear cuenta"):
            if not valid_password(password):
                st.error("La contraseña requiere mínimo 7 caracteres, 1 mayúscula y 1 símbolo.")
            else:
                try:
                    cur.execute(
                        "INSERT INTO users_apostador (username, password) VALUES (%s, %s)",
                        (username, password)
                    )
                    conn.commit()
                    st.success("Cuenta creada. Ahora ingresa.")
                except Exception:
                    st.error("El usuario ya existe.")
    else:  # Login
        if st.button("Ingresar"):
            cur.execute(
                "SELECT id FROM users_apostador WHERE username=%s AND password=%s",
                (username, password)
            )
            user_rec = cur.fetchone()
            if user_rec:
                st.session_state.apostador = user_rec[0]
                st.success(f"Bienvenido, {username}")
            else:
                st.error("Usuario o contraseña incorrectos.")
    cur.close(); conn.close()

# -----------------------------------------
# Header: Logo, título y redes
# -----------------------------------------
logo_b64 = to_base64(SOCIAL_DIR / "titulo.png")
kick_b64 = to_base64(SOCIAL_DIR / "kick.png")
x_b64    = to_base64(SOCIAL_DIR / "x.png")
tiktok_b64 = to_base64(SOCIAL_DIR / "tiktok.png")

st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;background:#1a1a1a;padding:10px;">
  <div style="display:flex;align-items:center;gap:12px;">
    <img src="data:image/png;base64,{logo_b64}" style="width:50px;"/>
    <h1 style="color:#FFD700;">ÑATABET</h1>
  </div>
  <div style="display:flex;gap:12px;">
    <a href="https://kick.com/yairlonelys"><img src="data:image/png;base64,{kick_b64}" style="width:30px;"/></a>
    <a href="https://x.com/YairLonelys"><img src="data:image/png;base64,{x_b64}" style="width:30px;"/></a>
    <a href="https://www.tiktok.com/@yairlonelyss"><img src="data:image/png;base64,{tiktok_b64}" style="width:30px;"/></a>
  </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------
# Dividir en tabs por juego
# -----------------------------------------
tabs = st.tabs(["Game 1", "Game 2", "Game 3"])
for i, tab in enumerate(tabs, start=1):
    with tab:
        st.subheader(f"Apuestas - Game {i}")
        st.info("Aquí irá la tabla de apuestas para este juego.")
        # TODO: Mostrar y editar apuestas según rol (admin/apostador/public)
