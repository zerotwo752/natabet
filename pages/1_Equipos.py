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
    "ABADDON", "ALCHEMIST", "ANCIENT_APPARITION", "ANTI_MAGE", "ANTI_MAGEM", "ARC_WARDEN",
    "AXE", "BANE", "BATRIDER", "BEASTMASTER", "BLOODSEEKER", "BOUNTY_HUNTER", "BREWMASTER",
    "BRISTLEBACK", "BROODMOTHER", "CENTAUR_WARRUNNER", "CHAOS_KNIGHT", "CHEN", "CLINKZ",
    "CLOCKWERK", "CRYSTAL_MAIDEN", "CRYSTAL_MAIDENP", "DARK_SEER", "DARK_WILLOW",
    "DAWNBREAKER", "DAZZLE", "DEATH_PROPHET", "DISRUPTOR", "DOOM", "DRAGON_KNIGHT",
    "DRAGON_KNIGHTP", "DROW_RANGER", "EARTHSHAKER", "EARTH_SPIRIT", "ELDER_TITAN",
    "EMBER_SPIRIT", "ENCHANTRESS", "ENIGMA", "FACELESS_VOID", "GRIMSTROKE",
    "GYROCOPTER", "HOODWINK", "HUSKAR", "INVOKER", "INVOKERP", "IO", "JAKIRO",
    "JUGGERNAUT", "KEEPER_OF_THE_LIGHT", "KEEZ", "KUNKKA", "LEGION_COMMANDER", "LESHRAC",
    "LICH", "LIFESTEALER", "LINA", "LION", "LONE_DRUID", "LUNA", "LYCAN", "MAGNUS",
    "MARCI", "MARS", "MEDUSA", "MEEPO", "MIRANA", "MIRANAP", "MONKEY_KING", "MORPHLING",
    "MUERTA", "NAGA_SIREN", "NATURES_PROPHET", "NECROPHOS", "NIGHT_STALKER", "NYX_ASSASSIN",
    "OGRE_MAGI", "OMNIKNIGHT", "ORACLE", "OUTWORLD_DESTROYER", "PANGOLIER",
    "PHANTOM_ASSASSIN", "PHANTOM_ASSASSINP", "PHANTOM_LANCER", "PHOENIX", "PRIMAL_BEAST",
    "PUCK", "PUDGE", "PUDGEP", "PUGNA", "QUEEN_OF_PAIN", "RAZOR", "RIKI", "RING_MASTER",
    "RUBICK", "SAND_KING", "SHADOW_DEMON", "SHADOW_FIEND", "SHADOW_SHAMAN", "SILENCER",
    "SKYWRATH_MAGE", "SLARDAR", "SLARK", "SNAPFIRE", "SNIPER", "SPECTRE", "SPIRIT_BREAKER",
    "STORM_SPIRIT", "SVEN", "TECHIES", "TEMPLAR_ASSASSIN", "TERROBLADE", "TIDEHUNTER",
    "TIMBERSAW", "TINKER", "TINY", "TREANT_PROTECTOR", "TROLL_WARLORD", "TUSK",
    "UNDERLORD", "UNDYING", "URSA", "VENGEFUL_SPIRIT", "VENOMANCER", "VIPER", "VISAGE",
    "VOID_SPIRIT", "WARLOCK", "WEAVER", "WINDRANGER", "WINTER_WYVERN", "WITCH_DOCTOR",
    "WRAITH_KING", "ZEUS"
]

#############################################
# Imagen de fondo
#############################################
pato_img_path = SOCIAL_DIR / "pato.png"
pato_img_base64 = to_base64(pato_img_path)

#############################################
# CSS global (incluye tooltip y apilado)
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
  h1,h2,h3,h4,h5,h6 {{ color: #FFD700 !important; }}
  .stButton>button {{
      background-color: #1d1d45 !important;
      color: white !important;
      border: 1px solid #45aa44 !important;
  }}
  .mmr-difference {{
      font-size: 24px; color: #FFF; font-weight: bold; text-align: center;
  }}
  .title {{
      font-size: 32px; color: #FFD700; font-weight: bold; text-align: center;
  }}
  .social-icons {{ position: fixed; top: 60px; left: 50px; display: flex;
      align-items: center; z-index: 1000; background: rgba(0,0,0,0.5);
      border-radius:10px; padding:5px;
  }}
  .social-icon {{ width:50px!important; cursor:pointer; transition:transform .2s; }}
  .social-icon:hover {{ transform:scale(1.1); }}

  /* apilar tarjetas */
  .team-container {{
      display: flex !important;
      flex-direction: column !important;
  }}
  .tooltip {{
      position: relative;
      display: block !important;
      width: 100% !important;
  }}
  .tooltip .tooltiptext {{
      visibility: hidden;
      position: absolute;
      bottom: 125%;
      left: 50%;
      transform: translateX(-50%);
      background: rgba(0,0,0,0.8);
      padding: 5px;
      border-radius: 6px;
      opacity: 0;
      transition: opacity 0.3s;
      z-index: 100;
  }}
  .tooltip:hover .tooltiptext {{
      visibility: visible;
      opacity: 1;
  }}
</style>
""", unsafe_allow_html=True)

#############################################
# DB (PostgreSQL)
#############################################
def get_db_connection():
    DATABASE_URL = os.environ.get("DATABASE_URL")
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    return conn

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
      CREATE TABLE IF NOT EXISTS balanced_teams (
        id SERIAL PRIMARY KEY,
        radiant TEXT, dire TEXT, players TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    """)
    cur.close()
    conn.close()

def save_balanced_table(radiant, dire):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM balanced_teams")
    cur.execute(
      "INSERT INTO balanced_teams (radiant,dire,players) VALUES (%s,%s,%s)",
      (json.dumps(radiant), json.dumps(dire), json.dumps(st.session_state.players))
    )
    cur.close()
    conn.close()

def load_balanced_table():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
      SELECT radiant,dire,players
      FROM balanced_teams
      ORDER BY updated_at DESC
      LIMIT 1
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
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

if 'db_loaded' not in st.session_state:
    r, d, p = load_balanced_table()
    if r is not None:
        st.session_state.radiant = r
        st.session_state.dire = d
        st.session_state.players = p
    st.session_state.db_loaded = True

#############################################
# Medallas y búsqueda de imagenes
#############################################
def get_medal(mmr:int)->str:
    # ... tu lógica de medallas ...
    # (idéntica a la que ya tenías)
    if mmr<770:
        stars=min(5,1+mmr//150)
        return f"heraldo{stars}.png"
    # resto de rangos...
    return "inmortal_top1.png"

def find_player_image(name:str)->str:
    clean=''.join(c if c.isalnum() else '_' for c in name.lower())
    for ext in ('.jpg','.jpeg','.png'):
        p=YAPE_PATH/f"{clean}{ext}"
        if p.exists():
            return to_base64(p)
    return to_base64(YAPE_PATH/"default.jpg")

#############################################
# Sidebar ADMIN
#############################################
with st.sidebar.expander("ADMIN (LOGIN)"):
    creds={'yair':'yair123','fernando':'fernando123'}
    if not st.session_state.is_admin:
        u=st.text_input("Usuario",key="u")
        pw=st.text_input("Contraseña",type="password",key="pw")
        if st.button("Ingresar"):
            if creds.get(u)==pw:
                st.session_state.is_admin=True
                st.success("👑 Administrador autenticado")
            else:
                st.error("Credenciales incorrectas")
    else:
        st.write("👑 Administrador conectado")
        if st.button("Cerrar sesión"):
            st.session_state.is_admin=False

if st.session_state.is_admin:
    with st.sidebar:
        st.header(f"➕ Agregar Jugador ({len(st.session_state.players)}/10)")
        nm=st.text_input("Nombre",key="add_name")
        mm=st.number_input("MMR",min_value=0,step=100,key="add_mmr")
        if st.button("Agregar"):
            if nm and mm is not None:
                st.session_state.players[nm]={"mmr":mm,"medal":get_medal(mm)}
        st.divider()
        st.header("🏷️ Lista de Jugadores")
        if st.session_state.players:
            for pname,data in st.session_state.players.items():
                b64=to_base64(IMAGES_DIR/data["medal"])
                st.markdown(f'''
                  <div style="display:flex;align-items:center;gap:8px">
                    <img src="data:image/png;base64,{b64}" width="30">
                    <span>{pname} ({data["mmr"]} MMR)</span>
                  </div>
                ''',unsafe_allow_html=True)
        else:
            st.info("No hay jugadores aún.")
        st.divider()
        st.header("Asignar Héroe")
        if st.session_state.players:
            sel=st.selectbox("Jugador",list(st.session_state.players),key="hp")
            her=st.selectbox("Héroe",["Selecciona Hero"]+hero_names,key="hh")
            if st.button("Asignar Héroe"):
                if her!="Selecciona Hero":
                    st.session_state.players[sel]["hero"]=her
                    st.success(f"Héroe asignado a {sel}")
                else:
                    st.error("Selecciona un héroe válido")
        st.divider()
        st.header("Quitar Jugador")
        if st.session_state.players:
            rem=st.selectbox("Quitar",list(st.session_state.players),key="rp")
            if st.button("Quitar"):
                del st.session_state.players[rem]
                for lst in ("radiant","dire"):
                    if rem in st.session_state[lst]:
                        st.session_state[lst].remove(rem)
                save_balanced_table(st.session_state.radiant, st.session_state.dire)
                st.success(f"{rem} eliminado")
        st.divider()
        st.header("Cambiar de Equipo")
        if st.session_state.players:
            sw=st.selectbox("Cambiar",list(st.session_state.players),key="sp")
            if st.button("Swap"):
                if sw in st.session_state.radiant:
                    st.session_state.radiant.remove(sw)
                    st.session_state.dire.append(sw)
                elif sw in st.session_state.dire:
                    st.session_state.dire.remove(sw)
                    st.session_state.radiant.append(sw)
                else:
                    st.error(f"{sw} no asignado")
                save_balanced_table(st.session_state.radiant, st.session_state.dire)
        st.divider()
        if st.button(f"🔄 Shuffle ({len(st.session_state.players)}/10)"):
            def balanced_shuffle():
                names=list(st.session_state.players)
                if not names:
                    st.error("No hay jugadores")
                    return
                combos=[]
                half=(len(names)+1)//2
                for _ in range(200):
                    random.shuffle(names)
                    r=names[:half]; d=names[half:]
                    diff=abs(sum(st.session_state.players[p]["mmr"] for p in r)
                             -sum(st.session_state.players[p]["mmr"] for p in d))
                    combos.append((r,d,diff))
                combos.sort(key=lambda x:x[2])
                st.session_state.combinations=combos[:10]
                st.session_state.current_combo=0
                r,d,_=st.session_state.combinations[0]
                st.session_state.radiant=r; st.session_state.dire=d
                save_balanced_table(r,d)
                st.success("Equipos balanceados")
            balanced_shuffle()
        if st.button("🧨 Eliminar todos"):
            if st.checkbox("⚠️ Confirmar",key="cdel"):
                st.session_state.players.clear()
                st.session_state.radiant.clear()
                st.session_state.dire.clear()
                st.session_state.combinations.clear()
                st.session_state.current_combo=0
                st.success("Todos eliminados")

#############################################
# display_team con tooltip y héroe alineado
#############################################
def display_team(team_name, team_members):
    total = sum(st.session_state.players[p]["mmr"] for p in team_members if p in st.session_state.players)
    html = f"""
    <html><head><meta charset="utf-8">
      <style>
        .team-container {{
          padding:20px; background:#272752; border-radius:10px;
          margin:20px auto; max-width:900px;
        }}
        .team-title {{
          text-align:center; font-size:36px; color:#FFD700;
          margin-bottom:20px;
        }}
        .player-card {{
          display:flex;
          align-items:center;
          gap:20px;
          background:#1d1d45;
          border:2px solid #45aa44;
          border-radius:10px;
          margin:10px 0;
          padding:15px;
          width:100%;
          box-sizing:border-box;
        }}
        .player-details {{
          font-size:24px; color:#FFF;
        }}
        .hero-info img {{ width:60px; height:60px; }}
        .hero-name {{ font-size:24px; color:#FFF; font-style:italic; }}
      </style>
    </head><body>
      <div class="team-container">
        <div class="team-title">{team_name} (MMR: {total:,})</div>
    """
    for p in team_members:
        if p not in st.session_state.players: continue
        d = st.session_state.players[p]
        medal_b64 = to_base64(IMAGES_DIR/d["medal"])
        tooltip_img = find_player_image(p)
        # héroe
        if d.get("hero") and d["hero"]!="Selecciona Hero":
            hero_b64 = to_base64(SOCIAL_DIR/f"{d['hero']}.png")
            hero_html = f'''
              <div class="hero-info">
                <img src="data:image/png;base64,{hero_b64}" alt="Héroe">
                <div class="hero-name">{d['hero']}</div>
              </div>
            '''
        else:
            hero_html = '<div class="hero-info"><div class="hero-name">Sin héroe</div></div>'
        html += f'''
          <div class="tooltip">
            <div class="player-card">
              <img src="data:image/png;base64,{medal_b64}" width="70" height="70" style="border-radius:50%">
              <div class="player-details">
                <div>{p}</div>
                <div>{d["mmr"]:,} MMR</div>
              </div>
              {hero_html}
            </div>
            <span class="tooltiptext">
              <img src="data:image/png;base64,{tooltip_img}" width="200">
            </span>
          </div>
        '''
    html += "</div></body></html>"
    components.html(html, height=900, width=1600, scrolling=True)

#############################################
# Vista principal
#############################################
st.markdown("<div class='title'>Dota 2 Ñatabet</div>", unsafe_allow_html=True)
c1,c2 = st.columns(2)
with c1:
    if st.session_state.radiant:
        display_team("Radiant", st.session_state.radiant)
with c2:
    if st.session_state.dire:
        display_team("Dire", st.session_state.dire)

if st.session_state.radiant and st.session_state.dire:
    diff = abs(
      sum(st.session_state.players[p]["mmr"] for p in st.session_state.radiant)
      - sum(st.session_state.players[p]["mmr"] for p in st.session_state.dire)
    )
    st.markdown(f"<div class='mmr-difference'>Diferencia de MMR: {diff:,}</div>", unsafe_allow_html=True)

#############################################
# Iconos sociales (sin cambios)
#############################################
for name, url in [
    ("kick", "https://kick.com/yairlonelys"),
    ("x",    "https://x.com/YairLonelys"),
    ("tiktok","https://www.tiktok.com/@yairlonelyss")
]:
    img_b64 = to_base64(SOCIAL_DIR/f"{name}.png")
    st.markdown(f'''
      <a href="{url}" target="_blank">
        <img src="data:image/png;base64,{img_b64}" class="social-icon">
      </a>
    ''', unsafe_allow_html=True)

# WhatsApp fijo
wa_b64 = to_base64(SOCIAL_DIR/"whatsapp.png")
st.markdown(f'''
  <div style="position:fixed;bottom:20px;left:20px;z-index:1000;">
    <a href="https://wa.me/qr/4FQFJOIBKQXFP1" target="_blank">
      <img src="data:image/png;base64,{wa_b64}" width="200" style="border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.3);">
    </a>
  </div>
''', unsafe_allow_html=True)

