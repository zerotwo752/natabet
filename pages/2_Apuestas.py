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
st.set_page_config(layout="wide")

# Rutas base de recursos
BASE_DIR   = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / "imagenes"
SOCIAL_DIR = BASE_DIR / "social"
YAPE_PATH  = BASE_DIR / "yape"

# URL de la base de datos en Railway
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
@st.cache_resource
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Tabla de apuestas
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bets (
            id SERIAL PRIMARY KEY,
            game_id INT,
            username TEXT,
            monto INT,
            equipo TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    # Tabla de apostadores
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users_apostador (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            coins INT DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
    conn.commit()
    cur.close()
    conn.close()

init_db()

# -----------------------------------------
# Funciones de Apuestas
# -----------------------------------------
def get_bets(game_id):
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT id, username, monto, equipo, created_at FROM bets WHERE game_id=%s ORDER BY created_at", (game_id,))
    rows = cur.fetchall()
    cur.close(); conn.close()
    return rows

def get_summary(game_id):
    rows = get_bets(game_id)
    total_r = sum(r[2] for r in rows if r[3] == 'Radiant')
    total_d = sum(r[2] for r in rows if r[3] == 'Dire')
    return total_r, total_d, abs(total_r - total_d)

def place_bet(game_id, username, amount, team):
    # Deduct coins and insert bet
    conn = get_db_connection(); cur = conn.cursor()
    cur.execute("SELECT coins FROM users_apostador WHERE username=%s", (username,))
    coins = cur.fetchone()[0]
    if amount > coins:
        cur.close(); conn.close()
        return False, "Saldo insuficiente"
    new_coins = coins - amount
    cur.execute("UPDATE users_apostador SET coins=%s WHERE username=%s", (new_coins, username))
    cur.execute(
        "INSERT INTO bets (game_id, username, monto, equipo) VALUES (%s,%s,%s,%s)",
        (game_id, username, amount, team)
    )
    conn.commit(); cur.close(); conn.close()
    return True, None

def settle_bets(game_id, winner):
    # winner: 'Radiant' or 'Dire'
    rows = get_bets(game_id)
    losers = [r for r in rows if r[3] != winner]
    winners = [r for r in rows if r[3] == winner]
    pool = sum(r[2] for r in losers)
    remaining = pool
    conn = get_db_connection(); cur = conn.cursor()
    for bid, user, amt, team, ts in winners:
        if remaining <= 0:
            credit = amt  # refund stake
        elif remaining >= amt:
            credit = int(amt * 1.8)
            remaining -= amt
        else:
            matched = remaining
            credit = int(matched * 1.8) + (amt - matched)
            remaining = 0
        # actualizar balance
        cur.execute("UPDATE users_apostador SET coins = coins + %s WHERE username=%s", (credit, user))
    # eliminar apuestas
    cur.execute("DELETE FROM bets WHERE game_id=%s", (game_id,))
    conn.commit(); cur.close(); conn.close()

def delete_user_bets(game_id, username):
    rows = [r for r in get_bets(game_id) if r[1] == username]
    total = sum(r[2] for r in rows)
    conn = get_db_connection(); cur = conn.cursor()
    # eliminar
    cur.execute("DELETE FROM bets WHERE game_id=%s AND username=%s", (game_id, username))
    # reembolsar
    cur.execute("UPDATE users_apostador SET coins = coins + %s WHERE username=%s", (total, username))
    conn.commit(); cur.close(); conn.close()

# -----------------------------------------
# CSS global
# -----------------------------------------
pato_b64 = to_base64(SOCIAL_DIR / "pato.gif")
st.markdown(f"""
<style>
.stApp {{ background: url(\"data:image/gif;base64,{pato_b64}\") center/cover fixed #000; color:#FFF; }}
.header-container {{ flex display; justify-content:space-between; align-items:center; }}
.header-container h1 {{ font-size:3rem; -webkit-text-stroke:1px purple; text-shadow:1px 1px 0 purple; }}
.header-container img {{ width:40px; }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------
# Sidebar: Autenticación y Admin
# -----------------------------------------
if 'is_admin' not in st.session_state: st.session_state.is_admin = False
if 'apostador' not in st.session_state: st.session_state.apostador = None
if 'apostador_user' not in st.session_state: st.session_state.apostador_user = None

auth = st.sidebar
# Admin Login
if not st.session_state.apostador:
    auth.markdown("### 👑 Admin")
    with auth.expander("Admin Login", expanded=True):
        if not st.session_state.is_admin:
            u = st.text_input("Usuario Admin", key="adminu")
            p = st.text_input("Password", type="password", key="adminp")
            if st.button("Ingresar Admin"):
                if u=='yair' and p=='yair123': st.session_state.is_admin=True; st.success("Admin autenticado")
                else: st.error("Credenciales incorrectas")
        else:
            auth.write("Admin conectado")
            if st.button("Cerrar sesión Admin"): st.session_state.is_admin=False
# Apostador Login/Register
auth.markdown("---")
with auth.expander("🎲 Apostador", expanded=True):
    mode = st.radio("Acción", ("Login","Registrarse"), key="md")
    uu = st.text_input("Usuario", key="uu")
    pp = st.text_input("Password", type="password", key="pp")
    conn = get_db_connection(); cur = conn.cursor()
    if mode=='Registrarse' and st.button("Crear cuenta"):
        if not valid_password(pp): st.error("Pwd:7+ carac, 1 mayúsc,1 símbolo.")
        else:
            try: cur.execute("INSERT INTO users_apostador(username,password) VALUES(%s,%s)",(uu,pp)); conn.commit(); st.success("Cuenta creada.")
            except: st.error("Usuario ya existe.")
    if mode=='Login' and st.button("Ingresar"): 
        cur.execute("SELECT id FROM users_apostador WHERE username=%s AND password=%s",(uu,pp))
        r=cur.fetchone()
        if r: st.session_state.apostador=r[0]; st.session_state.apostador_user=uu; st.success(f"Bienvenido {uu}")
        else: st.error("Credenciales inválidas")
    cur.close(); conn.close()
# Mostrar saldo si apostador logueado
if st.session_state.apostador:
    auth.markdown("---")
    auth.write(f"👤 {st.session_state.apostador_user}")
    conn=get_db_connection();c=conn.cursor();c.execute("SELECT coins FROM users_apostador WHERE id=%s",(st.session_state.apostador,));saldo=c.fetchone()[0];c.close();conn.close()
    auth.write(f"💰 {saldo} ÑataCoins")
    if auth.button("Logout Apostador"): st.session_state.apostador=None; st.session_state.apostador_user=None; st.success("Logout exitoso")
# Cambio pwd y listado y administrar bets y coins para admin
if st.session_state.is_admin and not st.session_state.apostador:
    auth.markdown("---")
    with auth.expander("🔑 Cambio Password",expanded=False):
        cu=st.text_input("Usuario",key="cuser"); np=st.text_input("New Pwd",type="password",key="npwd")
        if st.button("Actualizar"):
            conn=get_db_connection();cur=conn.cursor()
            cur.execute("SELECT id FROM users_apostador WHERE username=%s",(cu,));r=cur.fetchone()
            if not r: st.error("No existe.")
            elif not valid_password(np): st.error("Pwd inválida.")
            else: cur.execute("UPDATE users_apostador SET password=%s WHERE username=%s",(np,cu));conn.commit();st.success("Pwd updated")
            cur.close();conn.close()
    auth.markdown("---")
    with auth.expander("📋 Listado Usuarios",expanded=False):
        conn=get_db_connection();cur=conn.cursor();cur.execute("SELECT username,coins,created_at FROM users_apostador ORDER BY created_at DESC");rs=cur.fetchall();cur.close();conn.close()
        df=pd.DataFrame(rs,columns=["Usuario","ÑataCoins","Creado en"])
        auth.dataframe(df,use_container_width=True)
    auth.markdown("---")
    with auth.expander("💰 Administrar Coins",expanded=False):
        act=st.selectbox("Acción",("Agregar","Quitar"),key="act"); uu2=st.text_input("Usuario",key="cu2"); am=st.number_input("Coins",min_value=0,step=1,key="am2")
        if st.button("Ejecutar",key="exec2"):
            conn=get_db_connection();cur=conn.cursor();cur.execute("SELECT coins FROM users_apostador WHERE username=%s",(uu2,));r=cur.fetchone()
            if not r: st.error("No existe.")
            else:
                cur_bal=r[0]
                if act=='Quitar' and am>cur_bal: st.error(f"{cur_bal} disponibles.");cur.close();conn.close(); st.stop()
                new_bal=cur_bal+(am if act=='Agregar' else -am)
                cur.execute("UPDATE users_apostador SET coins=%s WHERE username=%s",(new_bal,uu2));conn.commit();st.success(f"Nuevo saldo {new_bal}")
            cur.close();conn.close()
    auth.markdown("---")
    with auth.expander("🎯 Administrar Bets",expanded=False):
        gsel=st.selectbox("Game",("Game 1","Game 2","Game 3"),key="gsel");u_del=st.text_input("Usuario",key="udel");
        if st.button("Eliminar Bet",key="delbet"):
            gid=int(gsel.split()[-1])
            delete_user_bets(gid,u_del)
            st.success(f"Bets de {u_del} eliminadas y reembolsadas.")

# -----------------------------------------
# Header
# -----------------------------------------
logo_b64 = to_base64(SOCIAL_DIR / "titulo.png")
st.markdown(f"""
<div class="header-container">
  <img src="data:image/png;base64,{logo_b64}"/>
  <h1>ÑATABET</h1>
  <div>
    <a href="https://kick.com/yairlonelys"><img src="data:image/png;base64,{to_base64(SOCIAL_DIR/"kick.png")}"/></a>
    <a href="https://x.com/YairLonelys"><img src="data:image/png;base64,{to_base64(SOCIAL_DIR/"x.png")}"/></a>
    <a href="https://www.tiktok.com/@yairlonelyss"><img src="data:image/png;base64,{to_base64(SOCIAL_DIR/"tiktok.png")}"/></a>
  </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------
# Tabs de Juegos
# -----------------------------------------
tabs = st.tabs(["Game 1","Game 2","Game 3"])
for i, tab in enumerate(tabs, start=1):
    with tab:
        st.subheader(f"Apuestas - Game {i}")
        # Mostrar tabla según rol
        rows = get_bets(i)
        if st.session_state.is_admin:
            df = pd.DataFrame(rows, columns=["ID","Usuario","Monto","Equipo","Hora"])
            st.table(df)
            # Botones de resultado
            col1, col2 = st.columns(2)
            if col1.button(f"GANO RADIANT {i}"):
                settle_bets(i,'Radiant'); st.success("Pagos realizados a Radiant.")
            if col2.button(f"GANO DIRE {i}"):
                settle_bets(i,'Dire'); st.success("Pagos realizados a Dire.")
        elif st.session_state.apostador:
            total_r, total_d, diff = get_summary(i)
            st.write(f"Total Radiant: {total_r}  |  Total Dire: {total_d}  |  Dif: {diff}")
            # Botones de apuesta
            allow_r = total_r <= total_d
            allow_d = total_d <= total_r
            amt = st.number_input("Monto a apostar", min_value=1, step=1, key=f"amt{i}")
            c1, c2 = st.columns(2)
            if c1.button("APOSTAR RADIANT", key=f"br{i}", disabled=not allow_r):
                ok,msg = place_bet(i, st.session_state.apostador_user, amt, 'Radiant')
                st.success("Apuesta registrada.") if ok else st.error(msg)
            if c2.button("APOSTAR DIRE", key=f"bd{i}", disabled=not allow_d):
                ok,msg = place_bet(i, st.session_state.apostador_user, amt, 'Dire')
                st.success("Apuesta registrada.") if ok else st.error(msg)
        else:
            total_r, total_d, diff = get_summary(i)
            st.write(f"Total Radiant: {total_r}  |  Total Dire: {total_d}  |  Dif: {diff}")
            st.info("Inicia sesión para apostar o ver más detalles.")

