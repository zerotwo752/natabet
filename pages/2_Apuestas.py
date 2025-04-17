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
    df = pd.read_sql("SELECT nombre, monto, equipo, multiplicado, check_col AS check, notas FROM bets ORDER BY id", conn)
    conn.close()
    if df.empty:
        return get_empty_bets_df()
    return df

def save_bets(df: pd.DataFrame):
    conn = get_db_connection()
    cur = conn.cursor()
    # Vaciar tabla
    cur.execute("TRUNCATE bets")
    # Insertar filas
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
if "df_bets" not in st.session_state or "db_loaded" not in st.session_state:
    st.session_state.df_bets = load_bets()
    st.session_state.db_loaded = True

# -----------------------------------------
# Inicializar estado de autenticación
# -----------------------------------------
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# -----------------------------------------
# Rutas de carpetas (ajusta según tu estructura)
# -----------------------------------------
BASE_DIR   = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / "imagenes"
SOCIAL_DIR = BASE_DIR / "social"
YAPE_PATH  = BASE_DIR / "yape"

# -----------------------------------------
# Inyección de CSS global
# -----------------------------------------
pato_b64 = to_base64(SOCIAL_DIR / "pato.gif")
st.markdown(f"""
<style>
  .stApp {{
    background: url("data:image/gif;base64,{pato_b64}") center 70% / cover fixed #1a1a1a;
    color: #FFF !important;
  }}
  [data-testid="stSidebar"] *, h1, h2, h3, h4, h5, h6 {{
    background: #1a1a1a !important;
    color: #FFF !important;
  }}
  h1, h2, h3, h4, h5, h6 {{ color: #FFD700 !important; }}
  .header-container {{
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 20px;
  }}
  .logo {{ width:50px; }}
  .brand-name {{
    font-size:24px; font-weight:bold; color:#FFF;
    text-shadow:-1px -1px 0 purple,1px -1px 0 purple,-1px 1px 0 purple,1px 1px 0 purple;
  }}
  .social-icon {{ width:60px; margin-left:12px; cursor:pointer; transition:.2s; }}
  .social-icon:hover {{ transform:scale(1.1); }}
  .yape-container {{ text-align:center; margin:25px 0; }}
  .yape-container img {{
    width:250px; border-radius:12px; box-shadow:0 4px 12px rgba(0,0,0,0.3);
    transition:transform .3s;
  }}
  .yape-container img:hover {{ transform:scale(1.05); }}
  .tabla-container {{
    background: rgba(0,0,0,0.7); padding:20px; border-radius:12px;
    margin: 20px auto; width:90%;
  }}
  .metrics-container {{
    background: rgba(0,0,0,0.7); padding:20px; border-radius:12px;
    margin: 20px auto; width:60%;
  }}
</style>
""", unsafe_allow_html=True)

# -----------------------------------------
# Sidebar: Login de Admin
# -----------------------------------------
with st.sidebar.expander("ADMIN (LOGIN)", expanded=True):
    admin_creds = {'yair': 'yair123', 'fernando': 'fernando123'}
    if not st.session_state.is_admin:
        u = st.text_input("Usuario", key="login_user")
        p = st.text_input("Contraseña", type="password", key="login_pass")
        if st.button("Ingresar", key="login_btn"):
            if u in admin_creds and admin_creds[u] == p:
                st.session_state.is_admin = True
                st.success("👑 Administrador autenticado")
            else:
                st.error("Credenciales incorrectas")
    else:
        st.write("👑 Administrador conectado")
        if st.button("🔒 Cerrar sesión", key="logout_btn"):
            st.session_state.is_admin = False

# -----------------------------------------
# Header: Logo + ÑATABET + Redes Sociales
# -----------------------------------------
logo_b64   = to_base64(SOCIAL_DIR / "titulo.png")
kick_b64   = to_base64(SOCIAL_DIR / "kick.png")
x_b64      = to_base64(SOCIAL_DIR / "x.png")
tiktok_b64 = to_base64(SOCIAL_DIR / "tiktok.png")

st.markdown(f"""
<div class="header-container">
  <div style="display:flex; align-items:center; gap:12px;">
    <img src="data:image/png;base64,{logo_b64}" class="logo" alt="Logo">
    <span class="brand-name">ÑATABET</span>
  </div>
  <div>
    <a href="https://kick.com/yairlonelys" target="_blank">
      <img src="data:image/png;base64,{kick_b64}" class="social-icon">
    </a>
    <a href="https://x.com/YairLonelys" target="_blank">
      <img src="data:image/png;base64,{x_b64}" class="social-icon">
    </a>
    <a href="https://www.tiktok.com/@yairlonelyss" target="_blank">
      <img src="data:image/png;base64,{tiktok_b64}" class="social-icon">
    </a>
  </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------
# Yape
# -----------------------------------------
yape_b64 = to_base64(YAPE_PATH / "yape.png")
yape_url = "https://www.yape.com.pe/"
st.markdown(f"""
<div class="yape-container">
  <a href="{yape_url}" target="_blank">
    <img src="data:image/png;base64,{yape_b64}" alt="Yape">
  </a>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------
# DataFrame vacío de apuestas
# -----------------------------------------
def get_empty_bets_df():
    return pd.DataFrame({
        "Nombre":       pd.Series(dtype="str"),
        "Monto":        pd.Series(dtype="float"),
        "Equipo":       pd.Series(dtype="str"),
        "Multiplicado": pd.Series(dtype="float"),
        "Check":        pd.Series(dtype="bool"),
        "Notas":        pd.Series(dtype="str"),
    })

# -----------------------------------------
# Función para recalcular
# -----------------------------------------
def recalc(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Monto"] = pd.to_numeric(df["Monto"], errors="coerce")
    df["Multiplicado"] = df["Monto"] * 1.8
    return df.fillna({
        "Nombre": "",
        "Monto": 0.0,
        "Equipo": "",
        "Multiplicado": 0.0,
        "Check": False,
        "Notas": ""
    })

# -----------------------------------------
# Editor de apuestas (sólo Admin)
# -----------------------------------------
if st.session_state.is_admin:
    with st.container():
        st.markdown("<div class='tabla-container'>", unsafe_allow_html=True)
        edited = st.data_editor(
            recalc(st.session_state.df_bets),
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
        # Guardamos si hubo cambio
        if not edited.equals(st.session_state.df_bets):
            st.session_state.df_bets = recalc(edited)
            save_bets(st.session_state.df_bets)
        st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------------------
# Métricas siempre visibles
# -----------------------------------------
df = st.session_state.df_bets
sum_r     = df[df["Equipo"] == "Radiant"]["Monto"].sum()
sum_d     = df[df["Equipo"] == "Dire"]["Monto"].sum()
difference = abs(sum_r - sum_d)

with st.container():
    st.markdown("<div class='metrics-container'>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    c1.metric("Radiant", f"{sum_r:.2f}")
    c2.metric("Dire",    f"{sum_d:.2f}")
    c3.metric("Diferencia", f"{difference:.2f}")
    st.markdown("</div>", unsafe_allow_html=True)
