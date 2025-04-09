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
BASE_DIR = Path(__file__).parent.parent
IMAGES_DIR = BASE_DIR / "imagenes"
SOCIAL_DIR = BASE_DIR / "social"
YAPE_PATH = BASE_DIR / "yape"

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
# Imagen de fondo (pato)
#############################################
pato_img_path = SOCIAL_DIR / "pato.png"
pato_img_base64 = to_base64(pato_img_path)

#############################################
# CSS global
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
.team-title {{
    font-size: 36px;
    text-align: center;
    margin: 30px 0;
    font-weight: bold;
    color: #FFFFFF;
}}
.player-card {{
    border: 2px solid #45aa44;
    border-radius: 10px;
    padding: 20px;
    background-color: #1d1d45;
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
}}
.nickname {{ font-size: 28px; font-weight: bold; color: #FFFFFF; }}
.mmr {{ font-size: 24px; color: #FFFFFF; }}
.hero-name {{ font-size: 24px; font-style: italic; color: #FFFFFF; margin-top: 5px; }}
</style>
""", unsafe_allow_html=True)

#############################################
# Grid estático 2x5 (solo estética)
#############################################
grid_items = "".join(["<div class='grid-item'></div>" for _ in range(10)])
grid_html = f"""
<html>
<head>
<style>
.grid-container {{
  display: grid;
  grid-template-columns: repeat(5,1fr);
  grid-template-rows: repeat(2,150px);
  gap: 10px;
  width: 90%;
  margin: 0 auto;
}}
.grid-item {{
  border: 2px dashed #45aa44;
  border-radius: 8px;
  background-color: rgba(29,29,69,0.3);
}}
</style>
</head>
<body>
<div class="grid-container">
  {grid_items}
</div>
</body>
</html>
"""
components.html(grid_html, height=340, scrolling=False)

# Empuja el contenido Streamlit hacia arriba para “superponerlo”
st.markdown("<div style='margin-top:-320px'></div>", unsafe_allow_html=True)

#############################################
# (Aquí continúa TODO tu código: DB, login, admin, shuffle...)
#############################################
def get_db_connection():
    conn = psycopg2.connect(os.environ["DATABASE_URL"])
    conn.autocommit = True
    return conn

def init_db():
    c = get_db_connection().cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS balanced_teams (
            id SERIAL PRIMARY KEY,
            radiant TEXT, dire TEXT, players TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.close()

def save_balanced_table(radiant, dire):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM balanced_teams")
    cur.execute(
        "INSERT INTO balanced_teams (radiant,dire,players) VALUES (%s,%s,%s)",
        (json.dumps(radiant), json.dumps(dire), json.dumps(st.session_state.players))
    )
    cur.close()

def load_balanced_table():
    cur = get_db_connection().cursor()
    cur.execute("SELECT radiant,dire,players FROM balanced_teams ORDER BY updated_at DESC LIMIT 1")
    row = cur.fetchone()
    cur.close()
    if row:
        return json.loads(row[0]), json.loads(row[1]), json.loads(row[2])
    return None, None, None

init_db()

# Estado inicial
for key, val in [
    ('is_admin', False), ('players', {}), ('radiant', []),
    ('dire', []), ('combinations', []), ('current_combo', 0),
    ('selected_player', None)
]:
    if key not in st.session_state:
        st.session_state[key] = val

if "db_loaded" not in st.session_state:
    rad, di, pl = load_balanced_table()
    if rad:
        st.session_state.radiant, st.session_state.dire, st.session_state.players = rad, di, pl
    st.session_state.db_loaded = True

# Medallas
def get_medal(mmr):
    # ... tu lógica ...
    return "heraldo1.png"

# Login Admin
with st.sidebar.expander("ADMIN (LOGIN)"):
    creds = {'yair':'yair123','fernando':'fernando123'}
    if not st.session_state.is_admin:
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("Ingresar"):
            if creds.get(u)==p:
                st.session_state.is_admin=True; st.success("👑 Autenticado")
            else: st.error("Credenciales incorrectas")
    else:
        st.write("👑 Conectado")
        if st.button("🔒 Cerrar sesión"):
            st.session_state.is_admin=False

# Admin controls (añadir, shuffle, etc.)
if st.session_state.is_admin:
    with st.sidebar:
        st.header(f"➕ Agregar Jugador ({len(st.session_state.players)}/10)")
        n = st.text_input("Nombre", key="add_n")
        m = st.number_input("MMR", min_value=0, step=100, key="add_m")
        if st.button("Agregar"):
            if n and m is not None:
                st.session_state.players[n] = {"mmr":m, "medal":get_medal(m)}
        st.divider()
        if st.button(f"🔄 Shuffle ({len(st.session_state.players)}/10)"):
            # ... tu shuffle ...
            pass
        if st.button("🧨 Eliminar todos"):
            st.session_state.players.clear()

#############################################
# Función para mostrar equipos (con widgets encima del grid)
#############################################
def display_team(team_name, members):
    total = sum(st.session_state.players[p]["mmr"] for p in members if p in st.session_state.players)
    st.markdown(f"<div class='team-title'>{team_name} (MMR: {total:,})</div>", unsafe_allow_html=True)
    for p in members:
        data = st.session_state.players.get(p)
        if not data: continue
        med = to_base64(IMAGES_DIR/data["medal"])
        hero = data.get("hero","Sin héroe")
        himg = to_base64(SOCIAL_DIR/f"{hero}.png") if hero!="Sin héroe" else ""
        st.markdown("<div class='player-card'>", unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns([1,3,3,1])
        with c1:
            st.image(f"data:image/png;base64,{med}", width=70)
        with c2:
            st.markdown(f"<div class='nickname'>{p}</div><div class='mmr'>{data['mmr']:,} MMR</div>",
                        unsafe_allow_html=True)
        with c3:
            if himg: st.image(f"data:image/png;base64,{himg}", width=70)
            st.markdown(f"<div class='hero-name'>{hero}</div>", unsafe_allow_html=True)
            if st.session_state.is_admin:
                opts = ["Selecciona Hero"]+hero_names
                idx = opts.index(hero) if hero in opts else 0
                sel = st.selectbox("", opts, key=f"hero_{p}", index=idx)
                if sel!="Selecciona Hero":
                    st.session_state.players[p]["hero"]=sel
        with c4:
            if st.session_state.is_admin and st.button("Seleccionar", key=f"sel_{p}"):
                st.session_state.selected_player = p
        st.markdown("</div>", unsafe_allow_html=True)

#############################################
# Vista principal
#############################################
st.markdown("<h1 class='title'>Dota 2 Ñatabet</h1>", unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    display_team("Radiant", st.session_state.radiant)
with col2:
    display_team("Dire", st.session_state.dire)

if st.session_state.radiant and st.session_state.dire:
    diff = abs(
        sum(st.session_state.players[p]["mmr"] for p in st.session_state.radiant) -
        sum(st.session_state.players[p]["mmr"] for p in st.session_state.dire)
    )
    st.markdown(f"<div class='mmr'>{diff:,} de diferencia</div>", unsafe_allow_html=True)

#############################################
# Redes sociales
#############################################
for img,name,url in [
    ("kick.png","Kick","https://kick.com/yairlonelys"),
    ("x.png","X","https://x.com/YairLonelys"),
    ("tiktok.png","TikTok","https://www.tiktok.com/@yairlonelyss")
]:
    b = to_base64(SOCIAL_DIR/img)
    st.markdown(
        f"<a href='{url}' target='_blank'>"
        f"<img src='data:image/png;base64,{b}' width='45' style='margin-right:10px;'>"
        f"</a>",
        unsafe_allow_html=True
    )

wh = to_base64(SOCIAL_DIR/"whatsapp.png")
st.markdown(f"""
<div style='position:fixed;bottom:20px;left:20px;'>
  <a href='https://wa.me/qr/4FQFJOIBKQXFP1' target='_blank'>
    <img src='data:image/png;base64,{wh}' width='200' style='border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.3);'>
  </a>
</div>
""", unsafe_allow_html=True)



