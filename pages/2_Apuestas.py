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
    return base64.b64encode(img_path.read_bytes()).decode() if img_path.exists() else ""

# -----------------------------------------
# DataFrame vacío de apuestas
# -----------------------------------------
def get_empty_bets_df() -> pd.DataFrame:
    return pd.DataFrame({
        "Nombre":       pd.Series(dtype="str"),
        "Monto":        pd.Series(dtype="float"),
        "Equipo":       pd.Series(dtype="str"),
        "Check":        pd.Series(dtype="bool"),
        "Notas":        pd.Series(dtype="str"),
    })

# -----------------------------------------
# Funciones de conexión a PostgreSQL
# -----------------------------------------
def get_db_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")

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
    conn.commit(); cur.close(); conn.close()

def load_bets() -> pd.DataFrame:
    conn = get_db_connection()
    df = pd.read_sql("""
        SELECT
          nombre    AS "Nombre",
          monto     AS "Monto",
          equipo    AS "Equipo",
          multiplicado AS "Multiplicado",
          check_col    AS "Check",
          notas      AS "Notas"
        FROM bets
        ORDER BY id
    """, conn)
    conn.close()
    if df.empty:
        df = get_empty_bets_df()
        df["Multiplicado"] = np.nan
    return df

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
            float(row["Monto"] or 0),
            row.get("Equipo",""),
            float((row["Monto"] or 0)*1.8),
            bool(row["Check"] or False),
            row.get("Notas","")
        ))
    conn.commit(); cur.close(); conn.close()

# -----------------------------------------
# Inicializa DB y carga datos en session
# -----------------------------------------
init_db()
if "df_bets" not in st.session_state:
    df0 = load_bets()
    # quitamos "Multiplicado" de la edición; lo generamos en la tabla
    st.session_state.df_bets   = df0.drop(columns=["Multiplicado"], errors="ignore")
    st.session_state.edited_df  = st.session_state.df_bets.copy()

# -----------------------------------------
# Auth & rutas
# -----------------------------------------
if 'is_admin' not in st.session_state: st.session_state.is_admin = False
BASE_DIR, IMAGES_DIR, SOCIAL_DIR, YAPE_PATH = Path(__file__).parent.parent, None, None, None
BASE_DIR  = Path(__file__).parent.parent
IMAGES_DIR= BASE_DIR/"imagenes"; SOCIAL_DIR= BASE_DIR/"social"; YAPE_PATH= BASE_DIR/"yape"

# -----------------------------------------
# CSS + fondo + logos + sidebar login
# -----------------------------------------
pato_b64 = to_base64(SOCIAL_DIR/"pato.gif")
st.markdown(f"""
<style>
.stApp {{
  background: url("data:image/gif;base64,{pato_b64}") center 70% / cover fixed #1a1a1a;
  color: #FFF !important;
}}
[data-testid="stSidebar"] *, h1,h2,h3,h4,h5,h6 {{
  background: #1a1a1a !important; color: #FFF !important;
}}
h1,h2,h3,h4,h5,h6 {{ color: #FFD700 !important; }}
.header-container {{
  display:flex;align-items:center;justify-content:space-between;
  padding:10px 20px;
}}
.logo {{ width:50px; }}
.brand-name {{
  font-size:24px;font-weight:bold;color:#FFF;
  text-shadow:-1px -1px 0 purple,1px -1px 0 purple,-1px 1px 0 purple,1px 1px 0 purple;
}}
.social-icon {{ width:60px;margin-left:12px;cursor:pointer;transition:.2s; }}
.social-icon:hover {{ transform:scale(1.1); }}
.yape-container {{ text-align:center;margin:25px 0; }}
.yape-container img {{
  width:250px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.3);
  transition:transform .3s;
}}
.yape-container img:hover {{ transform:scale(1.05); }}
.tabla-container {{
  background: rgba(0,0,0,0.7);padding:20px;border-radius:12px;
  margin:20px auto;width:90%;
}}
.metrics-container {{
  background: rgba(0,0,0,0.7);padding:20px;border-radius:12px;
  margin:20px auto;width:60%;
}}
</style>
""", unsafe_allow_html=True)

with st.sidebar.expander("ADMIN (LOGIN)", expanded=True):
    creds = {'yair':'yair123','fernando':'fernando123'}
    if not st.session_state.is_admin:
        u = st.text_input("Usuario",key="u"); p = st.text_input("Contraseña",type="password",key="p")
        if st.button("Ingresar"):
            if creds.get(u)==p:
                st.session_state.is_admin=True; st.success("👑 Admin autenticado")
            else: st.error("Credenciales incorrectas")
    else:
        st.write("👑 Admin conectado")
        if st.button("🔒 Cerrar sesión"): st.session_state.is_admin=False
        if st.button("💾 Guardar apuestas"):
            # volcamos a df_bets y guardamos
            st.session_state.df_bets = st.session_state.edited_df.copy()
            save_bets(st.session_state.df_bets)
            st.success("¡Apuestas guardadas!")

# -----------------------------------------
# Header + redes
# -----------------------------------------
logo_b64   = to_base64(SOCIAL_DIR/"titulo.png")
kick_b64   = to_base64(SOCIAL_DIR/"kick.png")
x_b64      = to_base64(SOCIAL_DIR/"x.png")
tiktok_b64 = to_base64(SOCIAL_DIR/"tiktok.png")
st.markdown(f"""
<div class="header-container">
  <div style="display:flex;align-items:center;gap:12px;">
    <img src="data:image/png;base64,{logo_b64}" class="logo"><span class="brand-name">ÑATABET</span>
  </div>
  <div>
    <a href="https://kick.com/yairlonelys"><img src="data:image/png;base64,{kick_b64}" class="social-icon"></a>
    <a href="https://x.com/YairLonelys"><img src="data:image/png;base64,{x_b64}" class="social-icon"></a>
    <a href="https://www.tiktok.com/@yairlonelyss"><img src="data:image/png;base64,{tiktok_b64}" class="social-icon"></a>
  </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------
# Yape
# -----------------------------------------
yape_b64 = to_base64(YAPE_PATH/"yape.png")
st.markdown(f"""
<div class="yape-container">
  <a href="https://www.yape.com.pe/"><img src="data:image/png;base64,{yape_b64}" alt="Yape"></a>
</div>
""", unsafe_allow_html=True)

# -----------------------------------------
# Editor con ComputedColumn para Multiplicado
# -----------------------------------------
if st.session_state.is_admin:
    with st.container():
        st.markdown("<div class='tabla-container'>",unsafe_allow_html=True)
        edited = st.data_editor(
            st.session_state.edited_df,
            column_config={
                "Nombre": st.column_config.TextColumn("Nombre"),
                "Monto":  st.column_config.NumberColumn("Monto", step=1.0,format="%.2f"),
                "Equipo": st.column_config.SelectboxColumn("Equipo",options=["","Radiant","Dire"]),
                "Check":  st.column_config.CheckboxColumn("Check"),
                "Notas":  st.column_config.TextColumn("Notas"),
            },
            computed_columns=[
                st.column_config.ComputedColumn("Multiplicado","Monto * 1.8",format="%.2f")
            ],
            key="bets_editor",
            num_rows="dynamic",
            use_container_width=True
        )
        st.session_state.edited_df = edited.copy()
        st.markdown("</div>",unsafe_allow_html=True)

# -----------------------------------------
# Métricas
# -----------------------------------------
df_show = (st.session_state.edited_df if st.session_state.is_admin
           else st.session_state.df_bets)
sum_r = df_show[df_show["Equipo"]=="Radiant"]["Monto"].sum()
sum_d = df_show[df_show["Equipo"]=="Dire"]["Monto"].sum()
diff  = abs(sum_r - sum_d)
with st.container():
    st.markdown("<div class='metrics-container'>",unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    c1.metric("Radiant",f"{sum_r:.2f}")
    c2.metric("Dire",   f"{sum_d:.2f}")
    c3.metric("Diferencia",f"{diff:.2f}")
    st.markdown("</div>",unsafe_allow_html=True)

