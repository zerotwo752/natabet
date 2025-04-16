import streamlit as st
import base64
from pathlib import Path
import os

# Configuración de la página en modo "wide"
st.set_page_config(layout="wide")

#############################################
# Función para convertir imágenes a Base64
#############################################
def to_base64(img_path: Path) -> str:
    if img_path.exists():
        return base64.b64encode(img_path.read_bytes()).decode()
    return ""

#############################################
# Rutas globales (con la misma estructura que en el código original)
#############################################
BASE_DIR = Path(__file__).parent.parent  # Sube un nivel desde la carpeta actual (/pages)
IMAGES_DIR = BASE_DIR / "imagenes"       
SOCIAL_DIR = BASE_DIR / "social"          
YAPE_PATH = BASE_DIR / "yape"             

#############################################
# Inyección de CSS global con fondo (pato)
#############################################
pato_img_path = SOCIAL_DIR / "pato.gif"
pato_img_base64 = to_base64(pato_img_path)

st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/gif;base64,{pato_img_base64}");
        background-size: cover;
        background-position: center 70%;
        background-attachment: fixed;
        background-color: #1a1a1a;
        color: #FFFFFF !important;
    }}
    [data-testid="stSidebar"], [data-testid="stSidebar"] * {{
        background-color: #1a1a1a !important;
        color: #FFFFFF !important;
    }}
    h1, h2, h3, h4, h5, h6 {{
        color: #FFD700 !important;
    }}
    .header-container {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 10px 20px;
    }}
    .logo-and-text {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}
    .logo {{
        width: 50px;
        height: auto;
    }}
    .brand-name {{
        font-size: 24px;
        font-weight: bold;
        color: #FFFFFF;
        text-shadow:
            -1px -1px 0 purple,
             1px -1px 0 purple,
            -1px  1px 0 purple,
             1px  1px 0 purple;
    }}
    .social-icon {{
        width: 60px;
        height: auto;
        margin-left: 12px;
        cursor: pointer;
        transition: transform 0.2s;
    }}
    .social-icon:hover {{
        transform: scale(1.1);
    }}
    .yape-container {{
        text-align: center;
        margin-top: 50px;
    }}
    .yape-container img {{
        width: 250px;
        cursor: pointer;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        transition: transform 0.3s;
    }}
    .yape-container img:hover {{
        transform: scale(1.05);
    }}
    </style>
    """, unsafe_allow_html=True)

#############################################
# Header: Logo, Marca y Redes Sociales
#############################################
titulo_img_path = SOCIAL_DIR / "titulo.png"
titulo_img_base64 = to_base64(titulo_img_path)

kick_img_path = SOCIAL_DIR / "kick.png"
kick_img_base64 = to_base64(kick_img_path)

tiktok_img_path = SOCIAL_DIR / "tiktok.png"
tiktok_img_base64 = to_base64(tiktok_img_path)

x_img_path = SOCIAL_DIR / "x.png"
x_img_base64 = to_base64(x_img_path)

header_html = f"""
<div class="header-container">
  <div class="logo-and-text">
    <img src="data:image/png;base64,{titulo_img_base64}" alt="Logo" class="logo"/>
    <span class="brand-name">ÑATABET</span>
  </div>
  <div class="right-links">
    <a href="https://kick.com/yairlonelys" target="_blank">
        <img src="data:image/png;base64,{kick_img_base64}" class="social-icon">
    </a>
    <a href="https://x.com/YairLonelys" target="_blank">
        <img src="data:image/png;base64,{x_img_base64}" class="social-icon">
    </a>
    <a href="https://www.tiktok.com/@yairlonelyss" target="_blank">
        <img src="data:image/png;base64,{tiktok_img_base64}" class="social-icon">
    </a>
  </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

#############################################
# Imagen y función de Yape
#############################################
yape_img_path = YAPE_PATH / "yape.png"  # Asegúrate de que esta imagen exista en la carpeta yape
yape_img_base64 = to_base64(yape_img_path)
yape_url = "https://www.yape.com.pe/"  # Modifica la URL según lo que necesites

st.markdown(f"""
    <div class="yape-container">
        <a href="{yape_url}" target="_blank">
            <img src="data:image/png;base64,{yape_img_base64}" alt="Yape">
        </a>
    </div>
    """, unsafe_allow_html=True)

#############################################
# Sidebar: Solo Login (Área de Administrador)
#############################################
with st.sidebar.expander("ADMIN (LOGIN)", expanded=True):
    admin_credentials = {
        'yair': 'yair123',
        'fernando': 'fernando123'
    }
    if 'is_admin' not in st.session_state:
        st.session_state.is_admin = False
    if not st.session_state.is_admin:
        username = st.text_input("Usuario", key="login_username")
        password = st.text_input("Contraseña", type="password", key="login_password")
        if st.button("Ingresar", key="login_button"):
            if username in admin_credentials and admin_credentials[username] == password:
                st.session_state.is_admin = True
                st.success("👑 Administrador autenticado")
            else:
                st.error("Credenciales incorrectas")
    else:
        st.write("👑 Administrador conectado")
        if st.button("🔒 Cerrar sesión"):
            st.session_state.is_admin = False

#############################################
# Contenido principal
#############################################
st.markdown("<h2 style='text-align: center; color: #FFFFFF;'>Bienvenido a ÑATABET</h2>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #FFFFFF;'>eliminado.</p>", unsafe_allow_html=True)



