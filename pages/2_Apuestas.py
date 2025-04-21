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

# Rutas base de recursos
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
# Sidebar: Autenticación
# -----------------------------------------
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'apostador' not in st.session_state:
    st.session_state.apostador = None
if 'apostador_user' not in st.session_state:
    st.session_state.apostador_user = None

auth_sidebar = st.sidebar

# Admin (solo si no hay apostador logueado)
if st.session_state.apostador is None:
    auth_sidebar.markdown("### 👑 Admin")
    with auth_sidebar.expander("Admin Login", expanded=True):
        if not st.session_state.is_admin:
            admin_u = st.text_input("Usuario Admin", key="admin_user")
            admin_p = st.text_input("Contraseña", type="password", key="admin_pwd")
            if st.button("Ingresar Admin"):
                if admin_u=='yair' and admin_p=='yair123':
                    st.session_state.is_admin = True
                    st.success("Admin autenticado")
                else:
                    st.error("Credenciales incorrectas")
        else:
            auth_sidebar.write("Admin conectado")
            if st.button("Cerrar sesión Admin"):
                st.session_state.is_admin = False

# Separador
auth_sidebar.markdown("---")
# Sección Apostador
auth_sidebar.markdown("### 🎲 Apostador")
with auth_sidebar.expander("Login / Registro", expanded=True):
    mode = st.radio("Selecciona acción", ("Login","Registrarse"), key="mode_user")
    usr = st.text_input("Usuario", key="usr")
    pwd = st.text_input("Contraseña", type="password", key="pwd")
    conn = get_db_connection(); cur = conn.cursor()
    if mode=="Registrarse":
        if st.button("Crear cuenta"):
            if not valid_password(pwd):
                st.error("La contraseña requiere 7+ caract., 1 mayúscula y 1 símbolo.")
            else:
                try:
                    cur.execute(
                        "INSERT INTO users_apostador (username,password) VALUES (%s,%s)",
                        (usr,pwd)
                    )
                    conn.commit(); st.success("Cuenta creada. Ahora ingresa.")
                except psycopg2.IntegrityError:
                    st.error("El usuario ya existe.")
    else:
        if st.button("Ingresar"):
            cur.execute(
                "SELECT id FROM users_apostador WHERE username=%s AND password=%s",(usr,pwd)
            )
            rec = cur.fetchone()
            if rec:
                st.session_state.apostador = rec[0]
                st.session_state.apostador_user = usr
                st.success(f"Bienvenido, {usr}")
            else:
                st.error("Usuario o contraseña incorrectos.")
    cur.close(); conn.close()

# Si apostador logueado, mostrar indicador y boton de logout, ocultar Admin
if st.session_state.apostador:
    auth_sidebar.markdown("---")
    auth_sidebar.markdown(f"**👤 Conectado como:** {st.session_state.apostador_user}")
    if auth_sidebar.button("Cerrar sesión Apostador"):
        st.session_state.apostador = None
        st.session_state.apostador_user = None
        st.success("Sesión de apostador cerrada.")

# Sección Cambio de contraseña (solo Admin y sin apostador)
if st.session_state.is_admin and st.session_state.apostador is None:
    auth_sidebar.markdown("---")
    with auth_sidebar.expander("🔑 Cambio de contraseña", expanded=False):
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
    # Listado de apostadores
    auth_sidebar.markdown("---")
    with auth_sidebar.expander("📋 Listado de apostadores", expanded=False):
        conn = get_db_connection(); cur = conn.cursor()
        cur.execute("SELECT username, created_at FROM users_apostador ORDER BY created_at DESC")
        rows = cur.fetchall(); cur.close(); conn.close()
        df_users = pd.DataFrame(rows, columns=["Usuario","Creado en"])
        auth_sidebar.dataframe(df_users, use_container_width=True)

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
        # TODO: lógica de mostrar y edición de apuestas
