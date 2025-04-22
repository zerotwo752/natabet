import streamlit as st
import base64
from pathlib import Path
import pandas as pd
import psycopg2
import os
import re
from datetime import datetime

# -----------------------------------------
# Configuración de la página
# -----------------------------------------
st.set_page_config(page_title="ÑATABET - Apuestas", layout="wide")

# Rutas base de recursos
de_file = Path(__file__).resolve().parent
BASE_DIR = de_file
IMAGES_DIR = BASE_DIR / "imagenes"
SOCIAL_DIR = BASE_DIR / "social"
YAPE_PATH = BASE_DIR / "yape"

# URL de la base de datos en Railway / Streamlit Cloud
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:wKuijKwZqsUgOZJhiEqXraNgXugQnShg@caboose.proxy.rlwy.net:25343/railway?sslmode=require"
)

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
def init_db():
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bets (
            id SERIAL PRIMARY KEY,
            game_id INT,
            username TEXT,
            monto INT,
            equipo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users_apostador (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            coins INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    conn.commit(); cur.close(); conn.close()

init_db()

# -----------------------------------------
# Funciones de Apuestas
# -----------------------------------------
def get_bets(game_id):
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute(
        "SELECT id, username, monto, equipo, created_at FROM bets WHERE game_id = %s ORDER BY created_at",
        (game_id,)
    )
    rows = cur.fetchall(); cur.close(); conn.close()
    return rows


def get_summary(game_id):
    bets = get_bets(game_id)
    total_r = sum(m for (_, _, m, eq, _) in bets if eq == "Radiant")
    total_d = sum(m for (_, _, m, eq, _) in bets if eq == "Dire")
    return total_r, total_d, abs(total_r - total_d)


def place_bet(game_id, username, amount, team):
    # Realiza la apuesta descontando coins y guardando registro
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT coins FROM users_apostador WHERE username = %s", (username,))
    result = cur.fetchone()
    if not result:
        cur.close(); conn.close(); return False, "Usuario no existe"
    coins = result[0]
    if amount > coins:
        cur.close(); conn.close(); return False, "Saldo insuficiente"
    cur.execute("UPDATE users_apostador SET coins = coins - %s WHERE username = %s", (amount, username))
    cur.execute(
        "INSERT INTO bets (game_id, username, monto, equipo) VALUES (%s, %s, %s, %s)",
        (game_id, username, amount, team)
    )
    conn.commit(); cur.close(); conn.close()
    return True, None


def settle_bets(game_id, winner):
    bets = get_bets(game_id)
    pool = sum(m for (_, _, m, eq, _) in bets if eq != winner)
    remaining = pool
    conn = get_db_connection(); cur = conn.cursor()
    for _, user, amount, eq, _ in bets:
        if eq == winner:
            credit = int(amount * 1.8) if remaining >= amount else int(remaining * 1.8) + (amount - remaining)
            remaining = max(0, remaining - amount)
            cur.execute(
                "UPDATE users_apostador SET coins = coins + %s WHERE username = %s",
                (credit, user)
            )
    cur.execute("DELETE FROM bets WHERE game_id = %s", (game_id,))
    conn.commit(); cur.close(); conn.close()

# -----------------------------------------
# Estilos globales
# -----------------------------------------
st.markdown(f"""
<style>
.stApp {{
    background: url('data:image/gif;base64,{to_base64(SOCIAL_DIR/'pato.gif')}') center 70% / cover fixed #1a1a1a;
    color: #FFF !important;
}}
.header-container {{ display:flex; align-items:center; justify-content:space-between; padding:10px 20px; }}
.logo {{ width:50px; height:auto; }}
.header-container h1 {{ font-size:2rem; margin:0; color:#FFD700;
    text-shadow:-1px -1px 0 purple,1px -1px 0 purple,-1px 1px 0 purple,1px 1px 0 purple;
}}
.social-icon {{ width:30px !important; margin-left:10px; transition:transform .2s; }}
.social-icon:hover {{ transform:scale(1.1); }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------
# Sidebar: Autenticación
# -----------------------------------------
if 'is_admin' not in st.session_state: st.session_state.is_admin = False
if 'apostador' not in st.session_state: st.session_state.apostador = None
if 'apostador_user' not in st.session_state: st.session_state.apostador_user = None

auth = st.sidebar

# Admin login (oculto si hay apostador)
if st.session_state.apostador is None:
    with auth.expander("👑 Admin", expanded=True):
        if not st.session_state.is_admin:
            u = st.text_input("Usuario Admin", key="admin_u")
            p = st.text_input("Contraseña Admin", type="password", key="admin_p")
            if st.button("Ingresar Admin"):
                if u=='yair' and p=='yair123': st.session_state.is_admin = True; st.success("Admin autenticado")
                else: st.error("Credenciales incorrectas")
        else:
            st.write("Admin conectado")
            if st.button("Cerrar sesión Admin"): st.session_state.is_admin = False; st.success("Sesión cerrada")

auth.markdown("---")

# Apostador login/registro
def handle_apostador():
    mode = st.radio("Acción", ("Login","Registrarse"), key="mode_user")
    usr = st.text_input("Usuario", key="usr")
    pwd = st.text_input("Contraseña", type="password", key="pwd")
    conn = get_db_connection(); cur = conn.cursor()
    if mode == "Registrarse" and st.button("Crear cuenta"):
        if not valid_password(pwd): st.error("La contraseña requiere 7+ caract., 1 mayúscula y 1 símbolo.")
        else:
            try:
                cur.execute("INSERT INTO users_apostador (username,password) VALUES (%s,%s)", (usr,pwd))
                conn.commit(); st.success("Cuenta creada. Ingresa ahora.")
            except psycopg2.IntegrityError: st.error("El usuario ya existe.")
    if mode == "Login" and st.button("Ingresar"):
        cur.execute("SELECT id FROM users_apostador WHERE username=%s AND password=%s", (usr,pwd))
        rec = cur.fetchone()
        if rec:
            st.session_state.apostador = rec[0]; st.session_state.apostador_user = usr; st.success(f"Bienvenido, {usr}")
        else: st.error("Usuario o contraseña incorrectos.")
    cur.close(); conn.close()

with auth.expander("🎲 Apostador", expanded=True):
    handle_apostador()

# Indicador/Logout para apostador
auth.markdown("---")
if st.session_state.apostador:
    auth.write(f"👤 {st.session_state.apostador_user}")
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT coins FROM users_apostador WHERE id=%s", (st.session_state.apostador,))
    balance = cur.fetchone()[0]; cur.close(); conn.close()
    auth.write(f"💰 {balance:,} ÑataCoins")
    if auth.button("Cerrar sesión Apostador"):
        st.session_state.apostador = None; st.session_state.apostador_user = None; st.success("Sesión cerrada")

# -----------------------------------------
# Header principal y redes
# -----------------------------------------
logo_b64 = to_base64(SOCIAL_DIR/'titulo.png')
st.markdown(f"""
<div class="header-container">
  <div style="display:flex;gap:12px;align-items:center;">
    <img src="data:image/png;base64,{logo_b64}" class="logo"/>
    <h1>ÑATABET</h1>
  </div>
  <div style="display:flex;align-items:center;">
    <a href="https://kick.com/yairlonelys" target="_blank"><img src="data:image/png;base64,{to_base64(SOCIAL_DIR/'kick.png')}" class="social-icon"/></a>
    <a href="https://x.com/YairLonelys" target="_blank"><img src="data:image/png;base64,{to_base64(SOCIAL_DIR/'x.png')}" class="social-icon"/></a>
    <a href="https://www.tiktok.com/@yairlonelyss" target="_blank"><img src="data:image/png;base64,{to_base64(SOCIAL_DIR/'tiktok.png')}" class="social-icon"/></a>
  </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------
# Pestañas de juegos y lógica de apuestas
# -----------------------------------------
tabs = st.tabs(["Game 1","Game 2","Game 3"])
for i, tab in enumerate(tabs, start=1):
    with tab:
        st.subheader(f"Apuestas - Game {i}")
        total_r, total_d, diff = get_summary(i)
        if st.session_state.is_admin:
            df = pd.DataFrame(get_bets(i), columns=["ID","Usuario","Monto","Equipo","Hora"])
            st.table(df)
            c1, c2 = st.columns(2)
            if c1.button(f"GANO RADIANT_{i}", key=f"win_r{i}"):
                settle_bets(i, 'Radiant'); st.success("Pagos realizados a Radiant.")
            if c2.button(f"GANO DIRE_{i}", key=f"win_d{i}"):
                settle_bets(i, 'Dire'); st.success("Pagos realizados a Dire.")
        elif st.session_state.apostador:
            st.write(f"Total Radiant: {total_r} | Total Dire: {total_d} | Dif: {diff}")
            amt = st.number_input("Monto a apostar", min_value=1, step=1, key=f"amt_{i}")
            col_r, col_d = st.columns(2)
            with col_r:
                if st.button("APOSTAR RADIANT", key=f"bet_r{i}"):
                    try:
                        if amt <= 0:
                            st.warning("Ingresa un monto válido.")
                        elif total_r > total_d:
                            st.warning("Radiant tiene más apuestas ahora.")
                        else:
                            ok, msg = place_bet(i, st.session_state.apostador_user, amt, 'Radiant')
                            st.success("Apuesta registrada.") if ok else st.error(msg)
                    except Exception as e:
                        st.error("Error al procesar la apuesta."); st.exception(e)
            with col_d:
                if st.button("APOSTAR DIRE", key=f"bet_d{i}"):
                    try:
                        if amt <= 0:
                            st.warning("Ingresa un monto válido.")
                        elif total_d > total_r:
                            st.warning("Dire tiene más apuestas ahora.")
                        else:
                            ok, msg = place_bet(i, st.session_state.apostador_user, amt, 'Dire')
                            st.success("Apuesta registrada.") if ok else st.error(msg)
                    except Exception as e:
                        st.error("Error al procesar la apuesta."); st.exception(e)
        else:
            st.info(f"Total Radiant: {total_r} | Total Dire: {total_d} | Dif: {diff}")
            st.info("Inicia sesión para apostar o ver más detalles.")
