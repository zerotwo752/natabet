import streamlit as st
import random
from pathlib import Path
import base64
import json
import os
import psycopg2
import streamlit.components.v1 as components

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
# Rutas globales
#############################################
BASE_DIR = Path(__file__).parent.parent  # Sube un nivel desde /pages
IMAGES_DIR = BASE_DIR / "imagenes"        # Ruta: web/imagenes
SOCIAL_DIR = BASE_DIR / "social"          # Ruta: web/social
YAPE_PATH = BASE_DIR / "yape"             # Ruta: web/yape

#############################################
# Lista de héroes (sin extensión)
#############################################
hero_names = [
    # ... tu lista de héroes aquí ...
    "ABADDON", "ALCHEMIST", "ANCIENT_APPARITION", # etc.
]

#############################################
# Definir y convertir la imagen de fondo (pato)
#############################################
pato_img_path = SOCIAL_DIR / "pato.png"
pato_img_base64 = to_base64(pato_img_path)

#############################################
# Inyección de CSS global
#############################################
st.markdown(f"""
    <style>
    .stApp {{
        background-image: url("data:image/png;base64,{pato_img_base64}");
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
    .stButton>button {{
        background-color: #1d1d45 !important;
        color: white !important;
        border: 1px solid #45aa44 !important;
    }}
    .player-box {{
        background-color: #1d1d45;
        color: #FFFFFF;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 5px;
        font-size: 16px;
    }}
    .mmr-difference {{
        font-size: 24px;
        color: #FFFFFF;
        font-weight: bold;
        text-align: center;
    }}
    .title {{
        font-size: 32px;
        color: #FFD700;
        font-weight: bold;
        text-align: center;
    }}
    .team-title {{
        font-size: 28px;
        color: #FFFFFF;
        font-weight: bold;
    }}
    .social-icons {{
        position: fixed;
        top: 60px;
        left: 50px;
        display: flex;
        align-items: center;
        z-index: 1000;
        background-color: rgba(0, 0, 0, 0.5);
        border-radius: 10px;
        padding: 5px;
    }}
    .social-icon {{
        width: 50px !important;
        height: auto;
        cursor: pointer;
        transition: transform 0.2s;
    }}
    .social-icon:hover {{
        transform: scale(1.1);
    }}

    /* ---- Aquí agregamos para que las tarjetas se apilen ---- */
    .team-container {{
        display: flex !important;
        flex-direction: column !important;
    }}
    .tooltip {{
        display: block !important;
        width: 100% !important;
    }}
    .player-card {{
        width: 100% !important;
        box-sizing: border-box;
    }}
    /* -------------------------------------------------------- */
    </style>
""", unsafe_allow_html=True)

#############################################
# Configuración de la Base de Datos (PostgreSQL)
#############################################
def get_db_connection():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS balanced_teams (
            id SERIAL PRIMARY KEY,
            radiant TEXT,
            dire TEXT,
            players TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cursor.close()
    conn.close()

def save_balanced_table(radiant, dire):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM balanced_teams")
    cursor.execute(
        "INSERT INTO balanced_teams (radiant, dire, players) VALUES (%s, %s, %s)",
        (json.dumps(radiant), json.dumps(dire), json.dumps(st.session_state.players))
    )
    cursor.close()
    conn.close()

def load_balanced_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT radiant, dire, players FROM balanced_teams ORDER BY updated_at DESC LIMIT 1")
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if row:
        return json.loads(row[0]), json.loads(row[1]), json.loads(row[2])
    else:
        return None, None, None

init_db()

#############################################
# Estado inicial
#############################################
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'players' not in st.session_state:
    st.session_state.players = {}
if 'radiant' not in st.session_state:
    st.session_state.radiant = []
if 'dire' not in st.session_state:
    st.session_state.dire = []
if 'combinations' not in st.session_state:
    st.session_state.combinations = []
if 'current_combo' not in st.session_state:
    st.session_state.current_combo = 0

if "db_loaded" not in st.session_state:
    radiant, dire, players = load_balanced_table()
    if radiant is not None and dire is not None:
        st.session_state.radiant = radiant
        st.session_state.dire = dire
        st.session_state.players = players
    st.session_state.db_loaded = True

#############################################
# Funciones auxiliares (get_medal, find_player_image...)
#############################################
# ... tu lógica de medallas y búsqueda de imagenes ...

#############################################
# Sidebar de ADMIN (login, agregar, shuffle...)
#############################################
# ... tu código de administración intacto ...

#############################################
# Función para mostrar equipos (vista de usuarios)
#############################################
def display_team(team_name, team_members):
    total_mmr = sum(
        st.session_state.players[p]["mmr"]
        for p in team_members
        if p in st.session_state.players
    )
    team_html = f"""
    <html>
      <head>
        <meta charset="utf-8">
        <style>
          .team-container {{
              padding: 20px;
              background-color: #272752;
              border-radius: 10px;
              margin: 20px auto;
              max-width: 900px;
          }}
          .team-title {{
              text-align: center;
              font-size: 36px;
              font-weight: bold;
              color: #FFD700;
              margin-bottom: 20px;
          }}
          .player-card {{
              display: flex;
              justify-content: space-between;
              align-items: center;
              background-color: #1d1d45;
              border: 2px solid #45aa44;
              border-radius: 10px;
              margin: 10px 0;
              padding: 15px;
              width: 100%;
              box-sizing: border-box;
          }}
          .player-info {{
              display: flex;
              align-items: center;
          }}
          .player-info img {{
              border-radius: 50%;
              margin-right: 15px;
              width: 70px;
              height: 70px;
          }}
          .player-details {{
              font-size: 24px;
              color: #FFFFFF;
          }}
          .hero-info {{
              display: flex;
              align-items: center;
          }}
          .hero-info img {{
              width: 60px;
              height: 60px;
              margin-right: 10px;
          }}
          .hero-name {{
              font-size: 24px;
              color: #FFFFFF;
              font-style: italic;
          }}
        </style>
      </head>
      <body>
        <div class="team-container">
          <div class="team-title">{team_name} (MMR: {total_mmr:,})</div>
    """
    for player in team_members:
        if player not in st.session_state.players:
            continue
        data = st.session_state.players[player]
        medal_b64 = to_base64(IMAGES_DIR / data["medal"])
        # héroe
        if data.get("hero") and data["hero"] != "Selecciona Hero":
            hero_b64 = to_base64(SOCIAL_DIR / f"{data['hero']}.png")
            hero_html = f"""
              <div class="hero-info">
                  <img src="data:image/png;base64,{hero_b64}" alt="Héroe">
                  <span class="hero-name">{data['hero']}</span>
              </div>
            """
        else:
            hero_html = '<div class="hero-info"><span class="hero-name">Sin héroe</span></div>'
        team_html += f"""
          <div class="tooltip">
            <div class="player-card">
              <div class="player-info">
                <img src="data:image/png;base64,{medal_b64}" alt="Medalla">
                <div class="player-details">
                  <div>{player}</div>
                  <div>{data['mmr']:,} MMR</div>
                </div>
              </div>
              {hero_html}
            </div>
          </div>
        """
    team_html += """
        </div>
      </body>
    </html>
    """
    components.html(team_html, height=900, width=1600, scrolling=True)

#############################################
# Vista principal
#############################################
st.markdown("<div class='title'>Dota 2 Ñatabet</div>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    if st.session_state.radiant:
        display_team("Radiant", st.session_state.radiant)
with col2:
    if st.session_state.dire:
        display_team("Dire", st.session_state.dire)

if st.session_state.radiant and st.session_state.dire:
    diff = abs(
        sum(st.session_state.players[p]["mmr"] for p in st.session_state.radiant) -
        sum(st.session_state.players[p]["mmr"] for p in st.session_state.dire)
    )
    st.markdown(f"<div class='mmr-difference'>Diferencia de MMR: {diff:,}</div>", unsafe_allow_html=True)

#############################################
# Iconos sociales (igual que antes)
#############################################
# ... tu bloque de redes intacto ...



