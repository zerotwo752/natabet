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

auto_init = init_db()

# -----------------------------------------
# Funciones de Apuestas
# -----------------------------------------
def get_bets(game_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, username, monto, equipo, created_at FROM bets WHERE game_id = %s ORDER BY created_at",
        (game_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_summary(game_id):
    bets = get_bets(game_id)
    total_r = sum(m for (_, _, m, equipo, _) in bets if equipo == 'Radiant')
    total_d = sum(m for (_, _, m, equipo, _) in bets if equipo == 'Dire')
    diff = abs(total_r - total_d)
    return total_r, total_d, diff


def place_bet(game_id, username, amount, team):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT coins FROM users_apostador WHERE username = %s",
        (username,)
    )
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
    # Descontar monedas
    cur.execute(
        "UPDATE users_apostador SET coins = coins - %s WHERE username = %s",
        (amount, username)
    )
    # Registrar apuesta
    cur.execute(
        "INSERT INTO bets (game_id, username, monto, equipo) VALUES (%s, %s, %s, %s)",
        (game_id, username, amount, team)
    )
    conn.commit()
    cur.close()
    conn.close()
    return True, None


def settle_bets(game_id, winner):
    bets = get_bets(game_id)
    losers = [b for b in bets if b[3] != winner]
    winners = [b for b in bets if b[3] == winner]
    pool = sum(m for (_, _, m, _, _) in losers)
    remaining = pool
    conn = get_db_connection()
    cur = conn.cursor()
    for _, user, amount, _, _ in winners:
        if remaining <= 0:
            credit = amount
        elif remaining >= amount:
            credit = int(amount * 1.8)
            remaining -= amount
        else:
            matched = remaining
            credit = int(matched * 1.8) + (amount - matched)
            remaining = 0
        cur.execute(
            "UPDATE users_apostador SET coins = coins + %s WHERE username = %s",
            (credit, user)
        )
    cur.execute(
        "DELETE FROM bets WHERE game_id = %s",
        (game_id,)
    )
    conn.commit()
    cur.close()
    conn.close()


def delete_user_bets(game_id, username):
    bets = get_bets(game_id)
    total_refund = sum(m for (_, u, m, _, _) in bets if u == username)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "DELETE FROM bets WHERE game_id = %s AND username = %s",
        (game_id, username)
    )
    cur.execute(
        "UPDATE users_apostador SET coins = coins + %s WHERE username = %s",
        (total_refund, username)
    )
    conn.commit()
    cur.close()
    conn.close()

# -----------------------------------------
# CSS global: fondo y estilos
# -----------------------------------------
st.markdown(f"""
<style>
.stApp {{
  background: url(\"data:image/gif;base64,{to_base64(SOCIAL_DIR / 'pato.gif')}\") center/cover fixed #000;
  color: #FFF !important;
}}
.header-container {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px;
}}
.header-container h1 {{
  font-size: 3rem;
  -webkit-text-stroke: 1px purple;
  text-shadow: 1px 1px 0 purple;
  margin: 0;
}}
.header-container img {{
  width: 40px;
  margin-left: 10px;
}}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------
# Sidebar: Autenticación y Admin
# -----------------------------------------
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'apostador' not in st.session_state:
    st.session_state.apostador = None
if 'apostador_user' not in st.session_state:
    st.session_state.apostador_user = None

auth = st.sidebar
# Admin Login
auth.markdown("### 👑 Admin")
with auth.expander("Admin Login", expanded=True):
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
# Apostador Login/Register
auth.markdown("---")
with auth.expander("🎲 Apostador", expanded=True):
    mode = st.radio("Acción", ("Login","Registrarse"), key="md")
    uu = st.text_input("Usuario", key="uu")
    pp = st.text_input("Contraseña", type="password", key="pp")
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
# Mostrar saldo apostador
if st.session_state.apostador:
    auth.markdown("---")
    auth.write(f"👤 {st.session_state.apostador_user}")
    conn=get_db_connection();c=conn.cursor();c.execute("SELECT coins FROM users_apostador WHERE id=%s",(st.session_state.apostador,));saldo=c.fetchone()[0];c.close();conn.close()
    auth.write(f"💰 {saldo} ÑataCoins")
    if auth.button("Logout Apostador"): st.session_state.apostador=None; st.session_state.apostador_user=None; st.success("Logout exitoso")
# Admin additional
if st.session_state.is_admin and not st.session_state.apostador:
    auth.markdown("---")
    with auth.expander("🔑 Cambio Password",expanded=False):
        cu=st.text_input("Usuario",key="cuser"); np=st.text_input("New Pwd",type="password",key="npwd")
        if st.button("Actualizar"):
            conn=get_db_connection();cur=conn.cursor();cur.execute("SELECT id FROM users_apostador WHERE username=%s",(cu,));r=cur.fetchone()
            if not r: st.error("No existe.")
            elif not valid_password(np): st.error("Pwd inválida.")
            else: cur.execute("UPDATE users_apostador SET password=%s WHERE username=%s",(np,cu));conn.commit();st.success("Pwd updated")
            cur.close();conn.close()
    with auth.expander("📋 Listado Usuarios",expanded=False):
        conn=get_db_connection();cur=conn.cursor();cur.execute("SELECT username,coins,created_at FROM users_apostador ORDER BY created_at DESC");rs=cur.fetchall();cur.close();conn.close()
        auth.dataframe(pd.DataFrame(rs,columns=["Usuario","ÑataCoins","Creado en"]))
    with auth.expander("💰 Admin Coins",expanded=False):
        act=st.selectbox("Acción",("Agregar","Quitar"),key="act"); uu2=st.text_input("Usuario",key="cu2"); am=st.number_input("Coins",min_value=0,step=1,key="am2")
        if st.button("Ejecutar",key="exec2"):
            conn=get_db_connection();cur=conn.cursor();cur.execute("SELECT coins FROM users_apostador WHERE username=%s",(uu2,));r=cur.fetchone()
            if not r: st.error("No existe.")
            else:
                bal=r[0]
                if act=='Quitar' and am>bal: st.error(f"{bal} disponibles.");cur.close();conn.close();st.stop()
                new_bal=bal+(am if act=='Agregar' else -am)
                cur.execute("UPDATE users_apostador SET coins=%s WHERE username=%s",(new_bal,uu2));conn.commit();st.success(f"Nuevo saldo {new_bal}")
            cur.close();conn.close()
    with auth.expander("🎯 Admin Bets",expanded=False):
        gs=st.selectbox("Game",(1,2,3),key="gs"); ub=st.text_input("User to delete bets",key="ub")
        if st.button("Del Bets"): delete_user_bets(gs,ub); st.success(f"Deleted and refunded {ub} bets for Game {gs}.")
# Header
logo_b64=to_base64(SOCIAL_DIR/"titulo.png")
st.markdown(f"""
<div class='header-container'>
  <div style='display:flex;align-items:center;gap:12px;'>
    <img src='data:image/png;base64,{logo_b64}' class='logo'/>
    <h1>ÑATABET</h1>
  </div>
  <div style='display:flex;gap:12px;'>
    <a href='https://kick.com/yairlonelys'><img src='data:image/png;base64,{to_base64(SOCIAL_DIR/'kick.png')}'/></a>
    <a href='https://x.com/YairLonelys'><img src='data:image/png;base64,{to_base64(SOCIAL_DIR/'x.png')}'/></a>
    <a href='https://www.tiktok.com/@yairlonelyss'><img src='data:image/png;base64,{to_base64(SOCIAL_DIR/'tiktok.png')}'/></a>
  </div>
</div>
""",unsafe_allow_html=True)
# Pestañas
tabs=st.tabs(["Game 1","Game 2","Game 3"])
for i,tab in enumerate(tabs,1):
    with tab:
        st.subheader(f"Apuestas - Game {i}")
        total_r,total_d,diff=get_summary(i)
        if st.session_state.is_admin:
            df=pd.DataFrame(get_bets(i),columns=["ID","Usuario","Monto","Equipo","Hora"])
            st.table(df)
            c1,c2=st.columns(2)
            if c1.button(f"GANO RADIANT {i}"): settle_bets(i,'Radiant');st.success("Pagos Radiant.")
            if c2.button(f"GANO DIRE {i}"): settle_bets(i,'Dire');st.success("Pagos Dire.")
        elif st.session_state.apostador:
            st.write(f"Total R:{total_r} | D:{total_d} | Dif:{diff}")
            allow_r=total_r<=total_d;allow_d=total_d<=total_r
            amt=st.number_input("Monto",min_value=1,key=f"amt{i}")
            br,bd=st.columns(2)
            if br.button("APOSTAR R",key=f"r{i}",disabled=not allow_r):ok,msg=place_bet(i,st.session_state.apostador_user,amt,'Radiant');st.success("Ok") if ok else st.error(msg)
            if bd.button("APOSTAR D",key=f"d{i}",disabled=not allow_d):ok,msg=place_bet(i,st.session_state.apostador_user,amt,'Dire');st.success("Ok") if ok else st.error(msg)
        else:
            st.write(f"R:{total_r} | D:{total_d} | Dif:{diff}")
            st.info("Ingresa para apostar.")
