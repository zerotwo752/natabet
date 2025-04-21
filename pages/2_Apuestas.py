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
BASE_DIR = Path(__file__).parent.parent
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
# Inicializar Base de Datos (migraciones)
# -----------------------------------------
def init_db():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # Tabla bets con created_at
        cur.execute("""
            CREATE TABLE IF NOT EXISTS bets (
                id SERIAL PRIMARY KEY,
                game_id INT,
                username TEXT,
                monto INT,
                equipo TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        # Tabla users_apostador
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users_apostador (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE,
                password TEXT,
                coins INT DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )
        # Asegurar columna created_at en bets (migración si existía sin)
        cur.execute("""
            ALTER TABLE bets
            ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """
        )
        conn.commit()
    except Exception as e:
        print("❌ Error inicializando la base de datos:", e)
    finally:
        cur.close()
        conn.close()

# Ejecutar migraciones en cada inicio
init_db()

# -----------------------------------------
# Funciones de Apuestas
# -----------------------------------------
def get_bets(game_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, monto, equipo, created_at "
        "FROM bets WHERE game_id = %s ORDER BY created_at",
        (game_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_summary(game_id):
    bets = get_bets(game_id)
    total_r = sum(m for (_, _, m, eq, _) in bets if eq == "Radiant")
    total_d = sum(m for (_, _, m, eq, _) in bets if eq == "Dire")
    diff = abs(total_r - total_d)
    return total_r, total_d, diff


def place_bet(game_id, username, amount, team):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT coins FROM users_apostador WHERE username = %s", (username,))
    result = cur.fetchone()
    if not result:
        cur.close()
        conn.close()
        return False, "Usuario no existe"
    coins = result[0]
    if amount > coins:
        cur.close()
        conn.close()
        return False, "Saldo insuficiente"
    cur.execute(
        "UPDATE users_apostador SET coins = coins - %s WHERE username = %s",
        (amount, username),
    )
    cur.execute(
        "INSERT INTO bets (game_id, username, monto, equipo) VALUES (%s, %s, %s, %s)",
        (game_id, username, amount, team),
    )
    conn.commit()
    cur.close()
    conn.close()
    return True, None


def settle_bets(game_id, winner):
    bets = get_bets(game_id)
    pool = sum(m for (_, _, m, eq, _) in bets if eq != winner)
    remaining = pool
    conn = get_db_connection()
    cur = conn.cursor()
    for _, user, amount, eq, _ in bets:
        if eq == winner:
            if remaining >= amount:
                credit = int(amount * 1.8)
                remaining -= amount
            else:
                credit = int(remaining * 1.8) + (amount - remaining)
                remaining = 0
            cur.execute(
                "UPDATE users_apostador SET coins = coins + %s WHERE username = %s",
                (credit, user),
            )
    cur.execute("DELETE FROM bets WHERE game_id = %s", (game_id,))
    conn.commit()
    cur.close()
    conn.close()


def delete_user_bets(game_id, username):
    bets = get_bets(game_id)
    refund = sum(m for (_, u, m, _, _) in bets if u == username)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM bets WHERE game_id = %s AND username = %s",
        (game_id, username),
    )
    cur.execute(
        "UPDATE users_apostador SET coins = coins + %s WHERE username = %s",
        (refund, username),
    )
    conn.commit()
    cur.close()
    conn.close()

# -----------------------------------------
# Estilos globales (incluye fondo pato)
# -----------------------------------------
st.markdown(f"""
<style>
.stApp {{
    background-image: url('data:image/gif;base64,{to_base64(SOCIAL_DIR/'pato.gif')}');
    background-size: cover;
    background-position: center 70%;
    background-attachment: fixed;
    background-color: #1a1a1a;
    color: #FFFFFF !important;
}}
.header-container {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 20px;
    background: transparent;
}}
.logo {{
    width: 50px;
    height: auto;
}}
.header-container h1 {{
    font-size: 2rem;
    margin: 0;
    color: #FFD700;
    text-shadow:
      -1px -1px 0 purple,
       1px -1px 0 purple,
      -1px  1px 0 purple,
       1px  1px 0 purple;
}}
.social-icon {{
    width: 30px !important;
    height: auto;
    margin-left: 10px;
    transition: transform 0.2s;
}}
.social-icon:hover {{
    transform: scale(1.1);
}}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------
# Sidebar: Admin y Apostador
# -----------------------------------------
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'apostador' not in st.session_state:
    st.session_state.apostador = None
if 'apostador_user' not in st.session_state:
    st.session_state.apostador_user = None

auth = st.sidebar

with auth.expander("👑 Admin", expanded=True):
    if not st.session_state.is_admin:
        u = st.text_input("Usuario Admin", key="admin_u")
        p = st.text_input("Contraseña Admin", type="password", key="admin_p")
        if st.button("Ingresar Admin"):
            if u == 'yair' and p == 'yair123':
                st.session_state.is_admin = True
                st.success("Admin autenticado")
            else:
                st.error("Credenciales incorrectas")
    else:
        st.write("Admin conectado")
        if st.button("Cerrar sesión Admin"):
            st.session_state.is_admin = False
            st.success("Sesión cerrada")

auth.markdown("---")

with auth.expander("🎲 Apostador", expanded=True):
    mode = st.radio("Acción", ("Login", "Registrarse"), key="mode_user")
    usr = st.text_input("Usuario", key="usr")
    pwd = st.text_input("Contraseña", type="password", key="pwd")
    conn = get_db_connection()
    cur = conn.cursor()
    if mode == "Registrarse" and st.button("Crear cuenta"):
        if not valid_password(pwd):
            st.error("La contraseña requiere 7+ caract., 1 mayúscula y 1 símbolo.")
        else:
            try:
                cur.execute(
                    "INSERT INTO users_apostador (username, password) VALUES (%s, %s)",
                    (usr, pwd),
                )
                conn.commit()
                st.success("Cuenta creada. Ingresa ahora.")
            except psycopg2.IntegrityError:
                st.error("El usuario ya existe.")
    if mode == "Login" and st.button("Ingresar"):
        cur.execute(
            "SELECT id FROM users_apostador WHERE username = %s AND password = %s",
            (usr, pwd),
        )
        rec = cur.fetchone()
        if rec:
            st.session_state.apostador = rec[0]
            st.session_state.apostador_user = usr
            st.success(f"Bienvenido, {usr}")
        else:
            st.error("Usuario o contraseña incorrectos.")
    cur.close()
    conn.close()

if st.session_state.apostador:
    auth.markdown("---")
    auth.write(f"👤 {st.session_state.apostador_user}")
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT coins FROM users_apostador WHERE id = %s",
        (st.session_state.apostador,),
    )
    balance = cur.fetchone()[0]
    cur.close()
    conn.close()
    auth.write(f"💰 {balance:,} ÑataCoins")
    if auth.button("Cerrar sesión Apostador"):
        st.session_state.apostador = None
        st.session_state.apostador_user = None
        st.success("Sesión cerrada.")

# -----------------------------------------
# Header principal y redes
# -----------------------------------------
logo_b64 = to_base64(SOCIAL_DIR / 'titulo.png')
st.markdown(f"""
<div class="header-container">
  <div style="display:flex;align-items:center;gap:12px;">
    <img src="data:image/png;base64,{logo_b64}" class="logo" />
    <h1>ÑATABET</h1>
  </div>
  <div style="display:flex;align-items:center;">
    <a href="https://kick.com/yairlonelys" target="_blank">
      <img src="data:image/png;base64,{to_base64(SOCIAL_DIR/'kick.png')}" class="social-icon" />
    </a>
    <a href="https://x.com/YairLonelys" target="_blank">
      <img src="data:image/png;base64,{to_base64(SOCIAL_DIR/'x.png')}" class="social-icon" />
    </a>
    <a href="https://www.tiktok.com/@yairlonelyss" target="_blank">
      <img src="data:image/png;base64,{to_base64(SOCIAL_DIR/'tiktok.png')}" class="social-icon" />
    </a>
  </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------
# Pestañas de juegos y lógica de apuestas
# -----------------------------------------
tabs = st.tabs(["Game 1", "Game 2", "Game 3"])
for i, tab in enumerate(tabs, start=1):
    with tab:
        st.subheader(f"Apuestas - Game {i}")
        total_r, total_d, diff = get_summary(i)
        if st.session_state.is_admin:
            df = pd.DataFrame(get_bets(i), columns=["ID", "Usuario", "Monto", "Equipo", "Hora"])
            st.table(df)
            c1, c2 = st.columns(2)
            if c1.button(f"GANO RADIANT {i}"):
                settle_bets(i, 'Radiant')
                st.success("Pagos realizados a Radiant.")
            if c2.button(f"GANO DIRE {i}"):
                settle_bets(i, 'Dire')
                st.success("Pagos realizados a Dire.")
        elif st.session_state.apostador:
            st.write(f"Total Radiant: {total_r} | Total Dire: {total_d} | Dif: {diff}")
            amt = st.number_input("Monto a apostar", min_value=1, key=f"amt{i}")
            br, bd = st.columns(2)
            if br.button("APOSTAR RADIANT", key=f"r{i}", disabled=total_r > total_d):
                ok, msg = place_bet(i, st.session_state.apostador_user, amt, 'Radiant')
                st.success("Apuesta registrada.") if ok else st.error(msg)
            if bd.button("APOSTAR DIRE", key=f"d{i}", disabled=total_d > total_r):
                ok, msg = place_bet(i, st.session_state.apostador_user, amt, 'Dire')
                st.success("Apuesta registrada.") if ok else st.error(msg)
        else:
            st.write(f"Total Radiant: {total_r} | Total Dire: {total_d} | Dif: {diff}")
            st.info("Inicia sesión para apostar o ver más detalles.")
