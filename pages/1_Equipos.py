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
    "ABADDON", "ALCHEMIST", "ANCIENT_APPARITION", "ANTI_MAGE", "ANTI_MAGEM",
    "ARC_WARDEN", "AXE", "BANE", "BATRIDER", "BEASTMASTER", "BLOODSEEKER",
    "BOUNTY_HUNTER", "BREWMASTER", "BRISTLEBACK", "BROODMOTHER",
    "CENTAUR_WARRUNNER", "CHAOS_KNIGHT", "CHEN", "CLINKZ", "CLOCKWERK",
    "CRYSTAL_MAIDEN", "CRYSTAL_MAIDENP", "DARK_SEER", "DARK_WILLOW",
    "DAWNBREAKER", "DAZZLE", "DEATH_PROPHET", "DISRUPTOR", "DOOM",
    "DRAGON_KNIGHT", "DRAGON_KNIGHTP", "DROW_RANGER", "EARTHSHAKER",
    "EARTH_SPIRIT", "ELDER_TITAN", "EMBER_SPIRIT", "ENCHANTRESS",
    "ENIGMA", "FACELESS_VOID", "GRIMSTROKE", "GYROCOPTER", "HOODWINK",
    "HUSKAR", "INVOKER", "INVOKERP", "IO", "JAKIRO", "JUGGERNAUT",
    "KEEPER_OF_THE_LIGHT", "KEEZ", "KUNKKA", "LEGION_COMMANDER",
    "LESHRAC", "LICH", "LIFESTEALER", "LINA", "LION", "LONE_DRUID",
    "LUNA", "LYCAN", "MAGNUS", "MARCI", "MARS", "MEDUSA", "MEEPO",
    "MIRANA", "MIRANAP", "MONKEY_KING", "MORPHLING", "MUERTA",
    "NAGA_SIREN", "NATURES_PROPHET", "NECROPHOS", "NIGHT_STALKER",
    "NYX_ASSASSIN", "OGRE_MAGI", "OMNIKNIGHT", "ORACLE",
    "OUTWORLD_DESTROYER", "PANGOLIER", "PHANTOM_ASSASSIN",
    "PHANTOM_ASSASSINP", "PHANTOM_LANCER", "PHOENIX", "PRIMAL_BEAST",
    "PUCK", "PUDGE", "PUDGEP", "PUGNA", "QUEEN_OF_PAIN", "RAZOR",
    "RIKI", "RING_MASTER", "RUBICK", "SAND_KING", "SHADOW_DEMON",
    "SHADOW_FIEND", "SHADOW_SHAMAN", "SILENCER", "SKYWRATH_MAGE",
    "SLARDAR", "SLARK", "SNAPFIRE", "SNIPER", "SPECTRE",
    "SPIRIT_BREAKER", "STORM_SPIRIT", "SVEN", "TECHIES",
    "TEMPLAR_ASSASSIN", "TERROBLADE", "TIDEHUNTER", "TIMBERSAW",
    "TINKER", "TINY", "TREANT_PROTECTOR", "TROLL_WARLORD", "TUSK",
    "UNDERLORD", "UNDYING", "URSA", "VENGEFUL_SPIRIT", "VENOMANCER",
    "VIPER", "VISAGE", "VOID_SPIRIT", "WARLOCK", "WEAVER",
    "WINDRANGER", "WINTER_WYVERN", "WITCH_DOCTOR", "WRAITH_KING", "ZEUS"
]

#############################################
# Imagen de fondo (pato)
#############################################
pato_img_path = SOCIAL_DIR / "pato.png"
pato_img_base64 = to_base64(pato_img_path)

#############################################
# CSS global (fondo, sidebar, botones y tarjetas)
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
    [data-testid="stSidebar"] {{
        background-color: #1a1a1a !important;
        color: #FFFFFF !important;
    }}
    .stButton>button {{
        background-color: #1d1d45 !important;
        color: white !important;
        border: 1px solid #45aa44 !important;
    }}
    .team-title {{
        font-size: 36px;
        text-align: center;
        margin: 30px 0;
        font-weight: bold;
        color: #FFFFFF;
    }}
    .player-card {{
        width: 90%;
        border: 2px solid #45aa44;
        border-radius: 10px;
        padding: 20px;
        background-color: #1d1d45;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }}
    .nickname {{
        font-size: 32px;
        font-weight: bold;
        color: #FFFFFF;
    }}
    .mmr {{
        font-size: 28px;
        color: #FFFFFF;
    }}
    .hero-name {{
        font-size: 32px;
        font-style: italic;
        color: #FFFFFF;
        margin-top: 10px;
    }}
    .title {{
        font-size: 40px;
        color: #FFD700;
        font-weight: bold;
        text-align: center;
    }}
    .mmr-difference {{
        font-size: 28px;
        color: #FFFFFF;
        font-weight: bold;
        text-align: center;
        margin-top: 20px;
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
        cursor: pointer;
        margin-right: 10px;
        transition: transform 0.2s;
    }}
    .social-icon:hover {{
        transform: scale(1.1);
    }}
    </style>
""", unsafe_allow_html=True)

#############################################
# Configuración de la Base de Datos
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
        "INSERT INTO balanced_teams (radiant, dire, players) VALUES (%s,%s,%s)",
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
if 'selected_player' not in st.session_state:
    st.session_state.selected_player = None

if "db_loaded" not in st.session_state:
    rad, di, pl = load_balanced_table()
    if rad:
        st.session_state.radiant = rad
        st.session_state.dire = di
        st.session_state.players = pl
    st.session_state.db_loaded = True

#############################################
# Medallas según MMR
#############################################
def get_medal(mmr):
    if mmr < 770:
        s = min(5, 1 + mmr//150); return f"heraldo{s}.png"
    if mmr < 1540:
        s = min(5, 1 + (mmr-770)//160); return f"guardian{s}.png"
    if mmr < 2310:
        s = min(5, 1 + (mmr-1540)//160); return f"cruzado{s}.png"
    if mmr < 3080:
        s = min(5, 1 + (mmr-2310)//150); return f"arconte{s}.png"
    if mmr < 3850:
        s = min(5, 1 + (mmr-3080)//150); return f"leyenda{s}.png"
    if mmr < 4620:
        s = min(5, 1 + (mmr-3850)//150); return f"ancestro{s}.png"
    if mmr < 5621:
        s = min(5, 1 + (mmr-4620)//200); return f"divino{s}.png"
    if mmr < 6300: return "inmortal0.png"
    if mmr < 8500: return "inmortal.png"
    if mmr < 12500: return "inmortal_top.png"
    return "inmortal_top1.png"

#############################################
# Login Admin
#############################################
with st.sidebar.expander("ADMIN (LOGIN)"):
    creds = {'yair':'yair123','fernando':'fernando123'}
    if not st.session_state.is_admin:
        u = st.text_input("Usuario", key="u")
        p = st.text_input("Contraseña", type="password", key="p")
        if st.button("Ingresar"):
            if creds.get(u)==p:
                st.session_state.is_admin=True; st.success("👑 Autenticado")
            else: st.error("Credenciales incorrectas")
    else:
        st.write("👑 Conectado")
        if st.button("🔒 Cerrar sesión"):
            st.session_state.is_admin=False

#############################################
# Panel Admin: añadir/jugadores, shuffle, etc.
#############################################
if st.session_state.is_admin:
    with st.sidebar:
        st.header(f"➕ Agregar Jugador ({len(st.session_state.players)}/10)")
        n = st.text_input("Nombre", key="add_n")
        m = st.number_input("MMR", min_value=0, step=100, key="add_m")
        if st.button("Agregar"):
            if n and m is not None:
                st.session_state.players[n] = {"mmr":m,"medal":get_medal(m)}
        st.divider()
        st.header("🏷️ Lista de Jugadores")
        if st.session_state.players:
            for pn, dt in st.session_state.players.items():
                mb = to_base64(IMAGES_DIR/ dt["medal"])
                st.markdown(
                    f"""<div style="display:flex;align-items:center;gap:8px">
                        <img src="data:image/png;base64,{mb}" width="30">
                        <span>{pn} ({dt['mmr']} MMR)</span>
                    </div>""",
                    unsafe_allow_html=True
                )
        else:
            st.info("No hay jugadores aún.")
        st.divider()
        if st.button(f"🔄 Shuffle Equipos ({len(st.session_state.players)}/10)"):
            def bs():
                names = list(st.session_state.players)
                combos=[]
                sz=(len(names)+1)//2
                for _ in range(200):
                    random.shuffle(names)
                    r=names[:sz]; d=names[sz:]
                    diff=abs(sum(st.session_state.players[x]["mmr"] for x in r)
                             - sum(st.session_state.players[x]["mmr"] for x in d))
                    combos.append((r,d,diff))
                combos.sort(key=lambda x:x[2])
                st.session_state.combinations=combos[:10]
                st.session_state.current_combo=0
                st.session_state.radiant,st.session_state.dire,_=combos[0]
                save_balanced_table(st.session_state.radiant,st.session_state.dire)
                st.success("¡Equipos balanceados!")
            bs()
        if st.button("🧨 Eliminar todos"):
            if st.checkbox("⚠️ Seguro?", key="delc"):
                st.session_state.players.clear()
                st.session_state.radiant.clear()
                st.session_state.dire.clear()
                st.session_state.combinations.clear()
                st.session_state.current_combo=0
                st.session_state.selected_player=None
                st.success("✅ Eliminados")
        st.divider()
        c1,c2,c3=st.columns(3)
        with c1:
            if st.button("🗑️ Quitar", disabled=not st.session_state.selected_player):
                p=st.session_state.selected_player
                if p:
                    if p in st.session_state.radiant: st.session_state.radiant.remove(p)
                    if p in st.session_state.dire:    st.session_state.dire.remove(p)
                    del st.session_state.players[p]
                    st.session_state.selected_player=None
                    save_balanced_table(st.session_state.radiant,st.session_state.dire)
        with c2:
            if st.button("🔄 Swap", disabled=not st.session_state.selected_player):
                p=st.session_state.selected_player
                if p:
                    if p in st.session_state.radiant:
                        st.session_state.radiant.remove(p)
                        st.session_state.dire.append(p)
                    else:
                        st.session_state.dire.remove(p)
                        st.session_state.radiant.append(p)
                    save_balanced_table(st.session_state.radiant,st.session_state.dire)
        with c3:
            if st.session_state.combinations:
                st.caption(f"Combo {st.session_state.current_combo+1}/{len(st.session_state.combinations)}")

#############################################
# Función display_team actualizada
#############################################
def display_team(team_name, team_members):
    total = sum(st.session_state.players[p]["mmr"] for p in team_members)
    is_rad = team_name.lower()=="radiant"
    mstyle = "margin:0 auto 0 0;" if is_rad else "margin:0 0 0 auto;"
    st.markdown(f"<div class='team-title'>{team_name} (MMR: {total:,})</div>", unsafe_allow_html=True)
    for pl in team_members:
        if pl not in st.session_state.players: continue
        d = st.session_state.players[pl]
        mb = to_base64(IMAGES_DIR/d["medal"])
        hero = d.get("hero","Sin héroe")
        hb = to_base64(SOCIAL_DIR/f"{hero}.png") if hero!="Sin héroe" else ""
        # abre tarjeta
        st.markdown(f"<div class='player-card' style='{mstyle}'>", unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns([1,3,3,1])
        with c1:
            if mb: st.image(f"data:image/png;base64,{mb}", width=80)
        with c2:
            st.markdown(
                f"<div class='nickname'>{pl}</div>"
                f"<div class='mmr'>{d['mmr']:,} MMR</div>",
                unsafe_allow_html=True
            )
        with c3:
            if hb: st.image(f"data:image/png;base64,{hb}", width=80)
            st.markdown(f"<div class='hero-name'>{hero}</div>", unsafe_allow_html=True)
            if st.session_state.is_admin:
                opts = ["Selecciona Hero"]+hero_names
                cur = hero if hero in opts else "Selecciona Hero"
                idx = opts.index(cur)
                sel = st.selectbox("", opts, key=f"hero_sel_{pl}", index=idx)
                if sel!="Selecciona Hero":
                    st.session_state.players[pl]["hero"]=sel
        with c4:
            if st.session_state.is_admin:
                if st.button("Seleccionar", key=f"sel_{pl}"):
                    st.session_state.selected_player=pl
        # cierra tarjeta
        st.markdown("</div>", unsafe_allow_html=True)

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
# Redes sociales
#############################################
for name, url, img in [
    ("kick","https://kick.com/yairlonelys","kick.png"),
    ("x","https://x.com/YairLonelys","x.png"),
    ("tiktok","https://www.tiktok.com/@yairlonelyss","tiktok.png")
]:
    b = to_base64(SOCIAL_DIR/img)
    st.markdown(
        f"<a href='{url}' target='_blank'>"
        f"<img src='data:image/png;base64,{b}' class='social-icon'></a>",
        unsafe_allow_html=True
    )
wh = to_base64(SOCIAL_DIR/"whatsapp.png")
st.markdown(f"""
<div style='position:fixed;bottom:20px;left:20px;z-index:1000;'>
  <a href='https://wa.me/qr/4FQFJOIBKQXFP1' target='_blank'>
    <img src='data:image/png;base64,{wh}' width='200'
         style='border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.3);'>
  </a>
</div>
""", unsafe_allow_html=True)




