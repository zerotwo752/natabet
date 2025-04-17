import streamlit as st
import base64
from pathlib import Path
import pandas as pd

# 1) Página en modo wide
st.set_page_config(layout="wide")

# 2) Autenticación básica
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False

# 3) Función para Base64
def to_base64(p: Path) -> str:
    return base64.b64encode(p.read_bytes()).decode() if p.exists() else ""

# 4) Rutas ajustadas (app.py está en la raíz del repo)
BASE_DIR   = Path(__file__).parent
IMAGES_DIR = BASE_DIR / "imagenes"
SOCIAL_DIR = BASE_DIR / "social"
YAPE_PATH  = BASE_DIR / "yape"

# 5) CSS y fondo
pato_b64 = to_base64(SOCIAL_DIR / "pato.gif")
st.markdown(f"""
<style>
  .stApp {{
    background: url("data:image/gif;base64,{pato_b64}") center 70% / cover fixed #1a1a1a;
    color: #FFF!important;
  }}
  [data-testid="stSidebar"] *, h1,h2,h3,h4,h5,h6 {{ background:#1a1a1a!important; color:#FFF!important; }}
  h1,h2,h3,h4,h5,h6 {{ color:#FFD700!important; }}
  /* ... (resto de tu CSS igual) ... */
</style>
""", unsafe_allow_html=True)

# 6) Sidebar login
with st.sidebar.expander("ADMIN (LOGIN)", expanded=True):
    creds = {'yair':'yair123','fernando':'fernando123'}
    if not st.session_state.is_admin:
        u = st.text_input("Usuario", key="u")
        p = st.text_input("Contraseña", type="password", key="p")
        if st.button("Ingresar"):
            if creds.get(u)==p:
                st.session_state.is_admin = True
                st.success("👑 Admin")
            else:
                st.error("❌")
    else:
        st.write("👑 Conectado")
        if st.button("Cerrar sesión"):
            st.session_state.is_admin = False

# 7) Header (logo + redes)
logo_b64   = to_base64(SOCIAL_DIR/"titulo.png")
kick_b64   = to_base64(SOCIAL_DIR/"kick.png")
x_b64      = to_base64(SOCIAL_DIR/"x.png")
tiktok_b64 = to_base64(SOCIAL_DIR/"tiktok.png")

st.markdown(f"""
<div style="display:flex;justify-content:space-between;align-items:center;padding:10px 20px;">
  <div style="display:flex;align-items:center;gap:12px;">
    <img src="data:image/png;base64,{logo_b64}" width="50">
    <h2 style="margin:0;color:#FFF;text-shadow:-1px -1px 0 purple,1px 1px 0 purple;">ÑATABET</h2>
  </div>
  <div>
    <a href="https://kick.com/yairlonelys"><img src="data:image/png;base64,{kick_b64}" width="60"></a>
    <a href="https://x.com/YairLonelys"><img src="data:image/png;base64,{x_b64}" width="60"></a>
    <a href="https://www.tiktok.com/@yairlonelyss"><img src="data:image/png;base64,{tiktok_b64}" width="60"></a>
  </div>
</div>
""", unsafe_allow_html=True)

# 8) Botón Yape
yape_b64  = to_base64(YAPE_PATH/"yape.png")
st.markdown(f"""
<div style="text-align:center;margin:25px 0;">
  <a href="https://www.yape.com.pe/">
    <img src="data:image/png;base64,{yape_b64}" width="250" style="border-radius:12px;">
  </a>
</div>
""", unsafe_allow_html=True)

# 9) DataFrame de apuestas
if 'df' not in st.session_state:
    st.session_state.df = pd.DataFrame({
        "Nombre":       pd.Series(dtype=str),
        "Monto":        pd.Series(dtype=float),
        "Equipo":       pd.Series(dtype=str),
        "Multiplicado": pd.Series(dtype=float),
        "Check":        pd.Series(dtype=bool),
        "Notas":        pd.Series(dtype=str),
    })

def recalc(df):
    df = df.copy()
    df["Multiplicado"] = df["Monto"] * 1.8
    return df

# 10) Sólo admin ve y edita la tabla
if st.session_state.is_admin:
    st.write("### Editor de apuestas")
    edited = st.data_editor(
        recalc(st.session_state.df),
        column_config={
            "Nombre":       st.column_config.TextColumn("Nombre"),
            "Monto":        st.column_config.NumberColumn("Monto", step=1.0, format="%.2f"),
            "Equipo":       st.column_config.SelectboxColumn("Equipo", options=["","Radiant","Dire"]),
            "Multiplicado": st.column_config.NumberColumn("Multiplicado", disabled=True, format="%.2f"),
            "Check":        st.column_config.CheckboxColumn("Check"),
            "Notas":        st.column_config.TextColumn("Notas"),
        },
        num_rows=10,
        key="editor",
    )
    st.session_state.df = recalc(edited)

# 11) Métricas — siempre visibles
df = st.session_state.df
sr = df[df.Equipo=="Radiant"].Monto.sum()
sd = df[df.Equipo=="Dire"].Monto.sum()
diff = abs(sr-sd)

st.write("### Resumen de apuestas")
st.metric("Radiant", f"{sr:.2f}")
st.metric("Dire",    f"{sd:.2f}")
st.metric("Diferencia", f"{diff:.2f}")

