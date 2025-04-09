import streamlit as st
import random
from pathlib import Path
import base64
import json
import os
import psycopg2
import streamlit.components.v1 as components

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
    "ABADDON", "ALCHEMIST", "ANCIENT_APPARITION", "ANTI_MAGE", "ANTI_MAGEM", "ARC_WARDEN", "AXE", "BANE", "BATRIDER",
    "BEASTMASTER", "BLOODSEEKER", "BOUNTY_HUNTER", "BREWMASTER", "BRISTLEBACK", "BROODMOTHER", "CENTAUR_WARRUNNER",
    "CHAOS_KNIGHT", "CHEN", "CLINKZ", "CLOCKWERK", "CRYSTAL_MAIDEN", "CRYSTAL_MAIDENP", "DARK_SEER", "DARK_WILLOW",
    "DAWNBREAKER", "DAZZLE", "DEATH_PROPHET", "DISRUPTOR", "DOOM", "DRAGON_KNIGHT", "DRAGON_KNIGHTP", "DROW_RANGER",
    "EARTHSHAKER", "EARTH_SPIRIT", "ELDER_TITAN", "EMBER_SPIRIT", "ENCHANTRESS", "ENIGMA", "FACELESS_VOID", "GRIMSTROKE",
    "GYROCOPTER", "HOODWINK", "HUSKAR", "INVOKER", "INVOKERP", "IO", "JAKIRO", "JUGGERNAUT", "KEEPER_OF_THE_LIGHT",
    "KEEZ", "KUNKKA", "LEGION_COMMANDER", "LESHRAC", "LICH", "LIFESTEALER", "LINA", "LION", "LONE_DRUID", "LUNA",
    "LYCAN", "MAGNUS", "MARCI", "MARS", "MEDUSA", "MEEPO", "MIRANA", "MIRANAP", "MONKEY_KING", "MORPHLING", "MUERTA",
    "NAGA_SIREN", "NATURES_PROPHET", "NECROPHOS", "NIGHT_STALKER", "NYX_ASSASSIN", "OGRE_MAGI", "OMNIKNIGHT", "ORACLE",
    "OUTWORLD_DESTROYER", "PANGOLIER", "PHANTOM_ASSASSIN", "PHANTOM_ASSASSINP", "PHANTOM_LANCER", "PHOENIX",
    "PRIMAL_BEAST", "PUCK", "PUDGE", "PUDGEP", "PUGNA", "QUEEN_OF_PAIN", "RAZOR", "RIKI", "RING_MASTER", "RUBICK",
    "SAND_KING", "SHADOW_DEMON", "SHADOW_FIEND", "SHADOW_SHAMAN", "SILENCER", "SKYWRATH_MAGE", "SLARDAR", "SLARK",
    "SNAPFIRE", "SNIPER", "SPECTRE", "SPIRIT_BREAKER", "STORM_SPIRIT", "SVEN", "TECHIES", "TEMPLAR_ASSASSIN",
    "TERROBLADE", "TIDEHUNTER", "TIMBERSAW", "TINKER", "TINY", "TREANT_PROTECTOR", "TROLL_WARLORD", "TUSK",
    "UNDERLORD", "UNDYING", "URSA", "VENGEFUL_SPIRIT", "VENOMANCER", "VIPER", "VISAGE", "VOID_SPIRIT", "WARLOCK",
    "WEAVER", "WINDRANGER", "WINTER_WYVERN", "WITCH_DOCTOR", "WRAITH_KING", "ZEUS"
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
# Inicialización de estado
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
if 'selected_player' not in st.session_state:
    st.session_state.selected_player = None

if "db_loaded" not in st.session_state:
    radiant, dire, players = load_balanced_table()
    if radiant is not None and dire is not None:
        st.session_state.radiant = radiant
        st.session_state.dire = dire
        st.session_state.players = players
    else:
        st.session_state.radiant = []
        st.session_state.dire = []
        st.session_state.players = {}
    st.session_state.db_loaded = True

#############################################
# Función para asignar medalla según MMR
#############################################
def get_medal(mmr: int) -> str:
    if mmr < 770:
        stars = min(5, 1 + mmr // 150)
        return f"heraldo{stars}.png"
    elif mmr < 1540:
        stars = min(5, 1 + (mmr - 770) // 160)
        return f"guardian{stars}.png"
    elif mmr < 2310:
        stars = min(5, 1 + (mmr - 1540) // 160)
        return f"cruzado{stars}.png"
    elif mmr < 3080:
        stars = min(5, 1 + (mmr - 2310) // 150)
        return f"arconte{stars}.png"
    elif mmr < 3850:
        stars = min(5, 1 + (mmr - 3080) // 150)
        return f"leyenda{stars}.png"
    elif mmr < 4620:
        stars = min(5, 1 + (mmr - 3850) // 150)
        return f"ancestro{stars}.png"
    elif mmr < 5621:
        stars = min(5, 1 + (mmr - 4620) // 200)
        return f"divino{stars}.png"
    elif mmr < 6300:
        return "inmortal0.png"
    elif mmr < 8500:
        return "inmortal.png"
    elif mmr < 12500:
        return "inmortal_top.png"
    else:
        return "inmortal_top1.png"

#############################################
# Función para buscar imagen de jugador (en YAPE)
#############################################
def find_player_image(player_name: str) -> str:
    clean_name = ''.join(c if c.isalnum() else '_' for c in player_name.lower())
    for ext in ['.jpg', '.jpeg', '.png']:
        img_path = YAPE_PATH / f"{clean_name}{ext}"
        if img_path.exists():
            return to_base64(img_path)
    return to_base64(YAPE_PATH / "default.jpg")

#############################################
# Panel de Administración en el Sidebar
#############################################
with st.sidebar.expander("ADMIN (LOGIN)"):
    admin_credentials = {
        'yair': 'yair123',
        'fernando': 'fernando123'
    }
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
# Controles para Administradores en el Sidebar
#############################################
if st.session_state.is_admin:
    with st.sidebar:
        st.header(f"➕ Agregar Jugador ({len(st.session_state.players)}/10)")
        name = st.text_input("Nombre", key="add_name")
        mmr = st.number_input("MMR", min_value=0, step=100, key="add_mmr")
        if st.button("Agregar", key="add_button"):
            if name and mmr is not None:
                st.session_state.players[name] = {
                    "mmr": mmr,
                    "medal": get_medal(mmr)
                }
        st.divider()
        st.header("🏷️ Lista de Jugadores")
        if st.session_state.players:
            for pname, data in st.session_state.players.items():
                img_path = IMAGES_DIR / data["medal"]
                img_bytes = to_base64(img_path) if img_path.exists() else None
                if img_bytes:
                    st.markdown(
                        f"""<div style="display: flex; align-items: center; gap: 10px;">
                            <img src="data:image/png;base64,{img_bytes}" width="30">
                            <span>{pname} ({data['mmr']} MMR)</span>
                        </div>""",
                        unsafe_allow_html=True
                    )
                else:
                    st.error(f"Medalla no encontrada: {data['medal']}")
        else:
            st.info("No hay jugadores aún.")
        st.divider()
        # Asignar Héroe
        st.header("Asignar Héroe a Jugador")
        if st.session_state.players:
            selected_player_hero = st.selectbox("Seleccionar Jugador", list(st.session_state.players.keys()), key="hero_player")
            hero_option = st.selectbox("Seleccionar Héroe", ["Selecciona Hero"] + hero_names, key="hero_option")
            if st.button("Asignar Héroe"):
                if hero_option != "Selecciona Hero":
                    st.session_state.players[selected_player_hero]["hero"] = hero_option
                    st.success(f"Héroe asignado a {selected_player_hero}")
                else:
                    st.error("Selecciona un héroe válido")
        else:
            st.info("No hay jugadores para asignar héroe.")
        st.divider()
        # Quitar Jugador (nueva sección)
        st.header("Quitar Jugador")
        if st.session_state.players:
            selected_player_remove = st.selectbox("Seleccionar Jugador a Quitar", list(st.session_state.players.keys()), key="remove_player_sel")
            if st.button("Quitar Jugador"):
                # Eliminar jugador del diccionario
                del st.session_state.players[selected_player_remove]
                # Eliminar de equipos si está asignado
                if selected_player_remove in st.session_state.radiant:
                    st.session_state.radiant.remove(selected_player_remove)
                if selected_player_remove in st.session_state.dire:
                    st.session_state.dire.remove(selected_player_remove)
                save_balanced_table(st.session_state.radiant, st.session_state.dire)
                st.success(f"Jugador {selected_player_remove} eliminado")
        else:
            st.info("No hay jugadores para quitar.")
        st.divider()
        # Cambiar de Equipo (nueva sección)
        st.header("Cambiar de Equipo")
        if st.session_state.players:
            selected_player_swap = st.selectbox("Seleccionar Jugador para Cambiar de Equipo", list(st.session_state.players.keys()), key="swap_player_sel")
            if st.button("Cambiar de Equipo"):
                # Si el jugador está en radiant, mover a dire y viceversa
                if selected_player_swap in st.session_state.radiant:
                    st.session_state.radiant.remove(selected_player_swap)
                    st.session_state.dire.append(selected_player_swap)
                    st.success(f"{selected_player_swap} pasado a Dire")
                elif selected_player_swap in st.session_state.dire:
                    st.session_state.dire.remove(selected_player_swap)
                    st.session_state.radiant.append(selected_player_swap)
                    st.success(f"{selected_player_swap} pasado a Radiant")
                else:
                    st.error(f"{selected_player_swap} no está asignado a ningún equipo aún")
                save_balanced_table(st.session_state.radiant, st.session_state.dire)
        else:
            st.info("No hay jugadores para cambiar de equipo.")
        st.divider()
        if st.button(f"🔄 Shuffle Equipos ({len(st.session_state.players)}/10)", key="shuffle_button"):
            def balanced_shuffle():
                player_names = list(st.session_state.players.keys())
                if not player_names:
                    st.error("¡No hay jugadores para balancear!")
                    return
                combo_list = []
                total_players = len(player_names)
                radiant_size = (total_players + 1) // 2
                for _ in range(200):
                    random.shuffle(player_names)
                    radiant = player_names[:radiant_size]
                    dire = player_names[radiant_size:]
                    diff = abs(
                        sum(st.session_state.players[p]["mmr"] for p in radiant) -
                        sum(st.session_state.players[p]["mmr"] for p in dire)
                    )
                    combo_list.append((radiant, dire, diff))
                combo_list.sort(key=lambda x: x[2])
                st.session_state.combinations = combo_list[:10]
                st.session_state.current_combo = 0
                def apply_combo():
                    if st.session_state.combinations:
                        radiant, dire, _ = st.session_state.combinations[st.session_state.current_combo]
                        st.session_state.radiant = radiant
                        st.session_state.dire = dire
                apply_combo()
                save_balanced_table(st.session_state.radiant, st.session_state.dire)
                st.success(f"¡Equipos balanceados ({len(st.session_state.radiant)}v{len(st.session_state.dire)})!")
            balanced_shuffle()
        if st.button("🧨 Eliminar todos los jugadores", key="delete_all"):
            if st.checkbox("⚠️ ¿Estás SEGURO?", key="confirm_delete"):
                st.session_state.players.clear()
                st.session_state.radiant.clear()
                st.session_state.dire.clear()
                st.session_state.combinations.clear()
                st.session_state.current_combo = 0
                st.session_state.selected_player = None
                st.success("✅ Todos los jugadores eliminados.")
        st.divider()
        col_btn1, col_btn2, col_btn3 = st.columns(3)
        with col_btn1:
            st.caption("Las funciones de quitar y cambiar se usan en las secciones de este sidebar")
        with col_btn2:
            st.caption("")
        with col_btn3:
            if st.session_state.combinations:
                st.caption(f"Combinación {st.session_state.current_combo + 1}/{len(st.session_state.combinations)}")

#############################################
# Función para mostrar equipos (vista de usuarios normales)
#############################################
def display_team(team_name, team_members):
    total_mmr = sum(st.session_state.players[p]["mmr"] for p in team_members if p in st.session_state.players)
    # Armar HTML con diseño estético del cuadro
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
              max-width: 1800px;
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
              width: 100%;  /* Asegura que ocupe todo el ancho */
             
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
    # Por cada jugador, incluir tarjeta con medalla y datos
    for player in team_members:
        if player not in st.session_state.players:
            continue
        player_data = st.session_state.players[player]
        medal_img_path = IMAGES_DIR / player_data["medal"]
        medal_img = to_base64(medal_img_path) if medal_img_path.exists() else ""
        if player_data.get("hero") and player_data.get("hero") != "Selecciona Hero":
            hero_img_path = SOCIAL_DIR / f"{player_data['hero']}.png"
            hero_img = to_base64(hero_img_path) if hero_img_path.exists() else ""
            hero_info = f"""
              <div class="hero-info">
                  <img src="data:image/png;base64,{hero_img}" alt="Héroe">
                  <span class="hero-name">{player_data['hero']}</span>
              </div>
            """
        else:
            hero_info = """<div class="hero-info"><span class="hero-name">Sin héroe</span></div>"""
        card = f"""
          <div class="player-card">
              <div class="player-info">
                  <img src="data:image/png;base64,{medal_img}" alt="Medalla">
                  <div class="player-details">
                      <div>{player}</div>
                      <div>{player_data['mmr']:,} MMR</div>
                  </div>
              </div>
              {hero_info}
          </div>
        """
        team_html += card
    team_html += """
        </div>
      </body>
    </html>
    """
    components.html(team_html, height=1000, width=2000, scrolling=True)

#############################################
# Vista principal (para TODOS los usuarios)
#############################################
with st.container():
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
    with st.container():
        st.markdown(f"<div class='mmr-difference'>Diferencia de MMR: {diff:,}</div>", unsafe_allow_html=True)

#############################################
# Código para redes sociales (sin cambios)
#############################################
kick_img_path = SOCIAL_DIR / "kick.png"
tiktok_img_path = SOCIAL_DIR / "tiktok.png"
x_img_path = SOCIAL_DIR / "x.png"
whatsapp_img_path = SOCIAL_DIR / "whatsapp.png"

kick_img_base64 = to_base64(kick_img_path)
tiktok_img_base64 = to_base64(tiktok_img_path)
x_img_base64 = to_base64(x_img_path)
whatsapp_img_base64 = to_base64(whatsapp_img_path)

social_icons_html = f"""
<div class="social-icons">
    <a href="https://kick.com/yairlonelys" target="_blank">
        <img src="data:image/png;base64,{kick_img_base64}" class="social-icon" width="45">
    </a>
    <a href="https://x.com/YairLonelys" target="_blank" style="margin-left: 12px;">
        <img src="data:image/png;base64,{x_img_base64}" class="social-icon" width="45">
    </a>
    <a href="https://www.tiktok.com/@yairlonelyss" target="_blank" style="margin-left: 12px;">
        <img src="data:image/png;base64,{tiktok_img_base64}" class="social-icon" width="45">
    </a>
</div>
"""
st.markdown(social_icons_html, unsafe_allow_html=True)

whatsapp_html = f"""
<div style="
    position: fixed;
    bottom: 20px;
    left: 20px;
    z-index: 1000;
    transition: transform 0.3s;
">
    <a href="https://wa.me/qr/4FQFJOIBKQXFP1" target="_blank">
        <img 
            src="data:image/png;base64,{whatsapp_img_base64}" 
            width="200"
            style="
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                transition: transform 0.3s;
            "
            onmouseover="this.style.transform='scale(1.05)'"
            onmouseout="this.style.transform='scale(1)'"
        >
    </a>
</div>
"""
st.markdown(whatsapp_html, unsafe_allow_html=True)
