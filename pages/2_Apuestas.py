import streamlit as st
import base64
from pathlib import Path
import pandas as pd
import psycopg2
import os
import re

# -----------------------------------------
# Configuración de la página
# -----------------------------------------
st.set_page_config(layout="wide")

# Definir rutas base de recursos
BASE_DIR  = Path(__file__).parent.parent
IMAGES_DIR= BASE_DIR/"imagenes"
SOCIAL_DIR= BASE_DIR/"social"
YAPE_PATH = BASE_DIR/"yape"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:...@...")

# -----------------------------------------
# Utilitarios
# -----------------------------------------
def to_base64(img_path: Path) -> str:
    return base64.b64encode(img_path.read_bytes()).decode() if img_path.exists() else ""

def get_db_connection():
    return psycopg2.connect(DATABASE_URL, sslmode="require")

# Verificar formato de contraseña
def valid_password(pw: str) -> bool:
    return bool(re.match(r'^(?=.*[A-Z])(?=.*\W).{7,}$', pw))

# -----------------------------------------
# Inicializar Base de Datos
# -----------------------------------------
@st.cache_resource
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Crear tabla de apuestas
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
    # Crear tabla de apostadores
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users_apostador (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    conn.commit(); cur.close(); conn.close()

# Ejecutar inicialización
def main():
    init_db()

    # -----------------------------------------
    # CSS global: fondo y estilos de header
    # -----------------------------------------
    pato_b64 = to_base64(SOCIAL_DIR/"pato.gif")
    st.markdown(f"""
    <style>
    .stApp {{
      background: url(\"data:image/gif;base64,{pato_b64}\") center 70% / cover fixed #1a1a1a;
      color: #FFF !important;
    }}
    .header-container {{
      display: flex;
      align-items: center;
      justify-content: space-between;
      background: transparent;
      padding: 10px;
    }}
    .header-container h1 {{
      color: #FFF;
      margin: 0;
      font-size: 3rem;
      -webkit-text-stroke: 1px purple;
      text-shadow: -1px -1px 0 purple, 1px -1px 0 purple, -1px 1px 0 purple, 1px 1px 0 purple;
    }}
    .header-container img.logo {{ width: 70px !important; }}
    .header-container img.social-icon {{ width: 40px !important; }}
    </style>
    """, unsafe_allow_html=True)

    # -----------------------------------------
    # Sidebar: Admin + Apostador + Cambio de contraseña
    # -----------------------------------------
    st.sidebar.markdown("### 👑 Admin")
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    with st.sidebar.expander("Admin Login", expanded=True):
        if not st.session_state.is_admin:
            user = st.text_input("Usuario Admin", key="admin_user")
            pwd  = st.text_input("Contraseña", type="password", key="admin_pwd")
            if st.button("Ingresar Admin"):
                if user=='yair' and pwd=='yair123':
                    st.session_state.is_admin = True; st.success("Admin autenticado")
                else: st.error("Credenciales incorrectas")
        else:
            st.write("Admin conectado")
            if st.button("Cerrar sesión Admin"): st.session_state.is_admin=False

    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🎲 Apostador")
    if 'apostador' not in st.session_state:
        st.session_state.apostador = None
    with st.sidebar.expander("Login / Registro", expanded=True):
        mode = st.radio("Selecciona acción", ("Login","Registrarse"), key="mode_user")
        username = st.text_input("Usuario", key="usr")
        password = st.text_input("Contraseña", type="password", key="pwd")
        conn = get_db_connection(); cur = conn.cursor()
        if mode=="Registrarse":
            if st.button("Crear cuenta"):
                if not valid_password(password):
                    st.error("La contraseña requiere 7+ caract., 1 mayúscula y 1 símbolo.")
                else:
                    try:
                        cur.execute(
                            "INSERT INTO users_apostador (username,password) VALUES (%s,%s)",
                            (username,password)
                        )
                        conn.commit(); st.success("Cuenta creada. Ahora ingresa.")
                    except psycopg2.IntegrityError:
                        st.error("El usuario ya existe.")
        else:
            if st.button("Ingresar"):
                cur.execute(
                    "SELECT id FROM users_apostador WHERE username=%s AND password=%s",(username,password)
                )
                rec = cur.fetchone()
                if rec:
                    st.session_state.apostador = rec[0]; st.success(f"Bienvenido, {username}")
                else: st.error("Usuario o contraseña incorrectos.")
        cur.close(); conn.close()

    # Cambio de contraseña
    st.sidebar.markdown("---")
    with st.sidebar.expander("🔑 Cambio de contraseña", expanded=False):
        user_cp = st.text_input("Usuario a modificar", key="cp_user")
        new_pw  = st.text_input("Nueva contraseña", type="password", key="cp_pwd")
        if st.button("Actualizar contraseña"):
            conn = get_db_connection(); cur = conn.cursor()
            cur.execute("SELECT id FROM users_apostador WHERE username=%s", (user_cp,))
            rec = cur.fetchone()
            if not rec:
                st.error("Apostador no registrado.")
            elif not valid_password(new_pw):
                st.error("La nueva contraseña requiere 7+ caract., 1 mayúscula y 1 símbolo.")
            else:
                cur.execute(
                    "UPDATE users_apostador SET password=%s WHERE username=%s", (new_pw, user_cp)
                )
                conn.commit(); st.success("Contraseña actualizada exitosamente.")
            cur.close(); conn.close()

    # -----------------------------------------
    # Header: Logo, título y redes sociales
    # -----------------------------------------
    logo_b64   = to_base64(SOCIAL_DIR/"titulo.png")
    kick_b64   = to_base64(SOCIAL_DIR/"kick.png")
    x_b64      = to_base64(SOCIAL_DIR/"x.png")
    tiktok_b64 = to_base64(SOCIAL_DIR/"tiktok.png")

    st.markdown(f"""
    <div class="header-container">
      <div style="display:flex;align-items:center;gap:12px;">
        <img class="logo" src="data:image/png;base64,{logo_b64}" />
        <h1>ÑATABET</h1>
      </div>
      <div style="display:flex;gap:12px;">
        <a href="https://kick.com/yairlonelys"><img class="social-icon" src="data:image/png;base64,{kick_b64}"/></a>
        <a href="https://x.com/YairLonelys"><img class="social-icon" src="data:image/png;base64,{x_b64}"/></a>
        <a href="https://www.tiktok.com/@yairlonelyss"><img class="social-icon" src="data:image/png;base64,{tiktok_b64}"/></a>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # -----------------------------------------
    # Separar en pestañas: Game 1, 2 y 3
    # -----------------------------------------
    tabs = st.tabs(["Game 1","Game 2","Game 3"])
    for i, tab in enumerate(tabs, start=1):
        with tab:
            st.subheader(f"Apuestas - Game {i}")
            st.info("Aquí irá la tabla de apuestas para este juego.")
            # TODO: lógica de mostr y edición de apuestas

if __name__ == "__main__":
    main()
