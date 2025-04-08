import streamlit as st
import random
from pathlib import Path
import base64
import os
import stat

# ===============================
# Definición de rutas globales
# ===============================
IMAGES_DIR = Path(__file__).parent / "imagenes"  # Ruta relativa
SOCIAL_DIR = Path(__file__).parent / "social"
YAPE_PATH = Path(__file__).parent / "yape"

# ===============================
# Inicialización de estado (COMPLETO) - ¡COLÓCALO AQUÍ!
# ===============================
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

# ===============================
# Funciones de conversión de imágenes
# ===============================
def img_to_base64(img_path: Path) -> str:
    """Convierte una imagen a Base64."""
    if img_path.exists():
        return base64.b64encode(img_path.read_bytes()).decode()
    return ""

def find_player_image(player_name: str) -> str:
    """
    Busca la imagen del jugador en la carpeta YAPE.
    Si existe una imagen cuyo nombre (limpio) coincide con el jugador, la retorna en Base64;
    en caso contrario retorna la imagen 'default.jpg'.
    """
    clean_name = ''.join(c if c.isalnum() else '_' for c in player_name.lower())
    for ext in ['.jpg', '.jpeg', '.png']:
        img_path = Path(f"{YAPE_PATH}{clean_name}{ext}")
        if img_path.exists():
            return img_to_base64(img_path)
    # Retornar imagen default si no se encontró la del jugador
    return img_to_base64(Path(f"{YAPE_PATH}default.jpg"))
# ===============================
# Verificación de sesión del admin
# ===============================
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False  # Inicializar el estado

# ===============================
# Función de inicio de sesión para Administradores
# ===============================
admin_credentials = {'admin': 'password123'}  # Cambia esto por tus credenciales

def show_login():
    """Muestra el formulario de login solo si no está logueado"""
    if not st.session_state.is_admin:
        with st.expander("🔑 Acceso Administrador", expanded=False):
            username = st.text_input("Usuario")
            password = st.text_input("Contraseña", type="password")
            if st.button("Ingresar"):
                if username in admin_credentials and admin_credentials[username] == password:
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    st.error("Credenciales incorrectas")

# Mostrar el login en el sidebar para admins
if st.session_state.is_admin:
    st.sidebar.write(f"👑 Administrador conectado")
    if st.sidebar.button("🔒 Cerrar sesión"):
        st.session_state.is_admin = False
        st.rerun()
else:
    show_login()  # Mostrar opción de login
# ===============================
# Lógica de la interfaz (Administradores vs Usuarios)
# ===============================
if st.session_state.is_admin:
    # Vista completa para administradores
    st.sidebar.header("Panel de Administración")
    # ... (todo el código actual del sidebar para admins)
    
    # Mostrar todos los controles de administración
    # ... (código existente de gestión de jugadores)
    
else:
    # Vista limitada para usuarios normales
    st.sidebar.empty()
    
    # Contenedor principal
    with st.container():
        st.markdown("<div class='title'>Dota 2 Ñatabet</div>", unsafe_allow_html=True)
        
        # Mensaje cuando no hay equipos
        if not st.session_state.radiant and not st.session_state.dire:
            st.markdown("""
                <div style='text-align: center; padding: 50px;'>
                    <h3 style='color: #FFD700;'>⚔️ Equipos no generados</h3>
                    <p>El administrador aún no ha creado los equipos</p>
                </div>
            """, unsafe_allow_html=True)
        
        # Mostrar equipos si existen
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.radiant:
                display_team("Radiant", st.session_state.radiant)
        
        with col2:
            if st.session_state.dire:
                display_team("Dire", st.session_state.dire)


# ===============================
# CSS personalizado (sin estilos de tooltip)
# ===============================
st.markdown("""
    <style>
        /* Estilos para el botón */
        .stButton button {
            transition: all 0.3s ease;
            background-color: #1d1d45;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 20px 50px;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.3s;
        }
        .stButton button:hover {
            background-color: #45aa44;
        }
        /* Estilos para el cuadro de la métrica */
        div[data-testid="stMetric"] {
            background: #f0f2f6;
            border-radius: 10px;
            padding: 10px;
        }
        /* Estilos para la diferencia de MMR */
        .mmr-difference {
            font-size: 24px;
            color: #FFFFFF;
            font-weight: bold;
            text-align: center;
        }
        /* Estilos para el título principal */
        .title {
            font-size: 32px;
            color: #FFD700;
            font-weight: bold;
            text-align: center;
        }
        /* Estilos para los títulos de los equipos */
        .team-title {
            font-size: 28px;
            color: #FFFFFF;
            font-weight: bold;
        }
        /* Estilos para los cuadros de jugadores */
        .player-box {
            font-size: 16px;
            color: #FFFFFF;
            background-color: #333333;
            border: 1px solid #CCCCCC;
            border-radius: 5px;
            padding: 10px;
            margin: 5px;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        /* Estilos para redes sociales */
        .social-icons {
            position: fixed;
            top: 60px;
            left: 50px;
            display: flex;
            align-items: center;
            z-index: 1000;
            background-color: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            padding: 5px;
        }
        .social-icon {
            width: 50px !important;
            height: auto;
            cursor: pointer;
            transition: transform 0.2s;
        }
        .social-icon:hover {
            transform: scale(1.1);
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateX(-50%) translateY(10px); }
            to { opacity: 1; transform: translateX(-50%) translateY(0); }
        }
        .player-button {
            background: #1d1d45;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px;
            width: 100%;
            text-align: left;
            cursor: pointer;
            font-size: 16px;
            transition: all 0.3s ease;
        }
        .player-button:hover {
            background: #45a4;
        }
    /* Estilo para la vista de usuario */
        .user-view {
            background-color: #1e1e2d;
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
        }
        .user-team-title {
            color: #FFD700;
            font-size: 24px;
            border-bottom: 2px solid #444;
            padding-bottom: 5px;
        }
    /* Efecto hover para tarjetas de jugador */
        div[data-testid="stHorizontalBlock"]:hover {
            background-color: rgba(255, 215, 0, 0.1);
            transition: all 0.3s ease;
        }
        /* Mensaje centrado para usuarios */
        .empty-teams-message {
            text-align: center;
            margin-top: 50px;
            color: #FFFFFF;
        }
    </style>
""", unsafe_allow_html=True)



# ===============================
# Código para redes sociales
# ===============================
def img_to_bytes(img_path: Path) -> str:
    """Convierte imágenes locales a Base64 (para Streamlit)."""
    if img_path.exists():
        return base64.b64encode(img_path.read_bytes()).decode()
    return ""

# Cargar imágenes de redes sociales
kick_img_path = SOCIAL_DIR / "kick.png"
tiktok_img_path = SOCIAL_DIR / "tiktok.png"
x_img_path = SOCIAL_DIR / "x.png"
whatsapp_img_path = SOCIAL_DIR / "whatsapp.png"

kick_img_base64 = img_to_bytes(kick_img_path)
tiktok_img_base64 = img_to_bytes(tiktok_img_path)
x_img_base64 = img_to_bytes(x_img_path)
whatsapp_img_base64 = img_to_bytes(whatsapp_img_path)

social_icons_html = f"""
<div class="social-icons">
    <a href="https://kick.com/yairlonelys " target="_blank">
        <img src="data:image/png;base64,{kick_img_base64}" class="social-icon" width="45">
    </a>
    <a href="https://x.com/YairLonelys " target="_blank" style="margin-left: 12px;">
        <img src="data:image/png;base64,{x_img_base64}" class="social-icon" width="45">
    </a>
    <a href="https://www.tiktok.com/@yairlonelyss " target="_blank" style="margin-left: 12px;">
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
    <a href="https://wa.me/qr/4FQFJOIBKQXFP1 " target="_blank">
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

# ===============================
# Funciones principales de la aplicación
# ===============================
def get_medal(mmr: int) -> str:
    """Determina la medalla basada en el MMR (adaptado a tus rangos)."""
    if mmr < 770:
        stars = min(5, 1 + mmr // 150)
        return f"heraldo{stars}.png"
    elif mmr < 1540:
        stars = min(5, 1 + (mmr-770) // 160)
        return f"guardian{stars}.png"
    elif mmr < 2310:
        stars = min(5, 1 + (mmr-1540) // 160)
        return f"cruzado{stars}.png"
    elif mmr < 3080:
        stars = min(5, 1 + (mmr-2310) // 150)
        return f"arconte{stars}.png"
    elif mmr < 3850:
        stars = min(5, 1 + (mmr-3080) // 150)
        return f"leyenda{stars}.png"
    elif mmr < 4620:
        stars = min(5, 1 + (mmr-3850) // 150)
        return f"ancestro{stars}.png"
    elif mmr < 5621:
        stars = min(5, 1 + (mmr-4620) // 200)
        return f"divino{stars}.png"
    elif mmr < 6300:
        return "inmortal0.png"
    elif mmr < 8500:
        return "inmortal.png"
    elif mmr < 12500:
        return "inmortal_top.png"
    else:
        return "inmortal_top1.png"


def calculate_mmr(team):
    return sum(player["mmr"] for player in team.values())

def balanced_shuffle():
    player_names = list(st.session_state.players.keys())
    if not player_names:
        st.error("¡No hay jugadores para balancear!")
        return
    
    combo_list = []
    total_players = len(player_names)
    radiant_size = (total_players + 1) // 2  # Ejemplo: 5 para 9 jugadores
    
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
    apply_combo()
    st.success(f"¡Equipos balanceados ({len(st.session_state.radiant)}v{len(st.session_state.dire)})!")

def apply_combo():
    if st.session_state.combinations:
        radiant, dire, _ = st.session_state.combinations[st.session_state.current_combo]
        st.session_state.radiant = radiant
        st.session_state.dire = dire

def delete_all_players():
    st.session_state.players.clear()
    st.session_state.radiant.clear()
    st.session_state.dire.clear()
    st.session_state.combinations.clear()
    st.session_state.current_combo = 0
    st.session_state.selected_player = None
    st.success("✅ Todos los jugadores eliminados.")

# ===============================
# Interfaz de usuario
# ===============================
with st.container():
    st.markdown("<div class='title'>Dota 2 Ñatabet</div>", unsafe_allow_html=True)
    
with st.sidebar:
    st.header(f"➕ Agregar Jugador ({len(st.session_state.players)}/10)")
    name = st.text_input("Nombre")
    mmr = st.number_input("MMR", min_value=0, step=100)
    
    if st.button("Agregar"):
        if name and mmr is not None:
            st.session_state.players[name] = {
                "mmr": mmr,
                "medal": get_medal(mmr)
            }
            st.rerun()
    
    st.divider()
    st.header("🏷️ Lista de Jugadores")
    if st.session_state.players:
        for name, data in st.session_state.players.items():
            img_path = IMAGES_DIR / data["medal"]
            img_bytes = img_to_bytes(img_path) if img_path.exists() else None
            if img_bytes:
                st.markdown(
                    f"""<div style="display: flex; align-items: center; gap: 10px;">
                        <img src="data:image/png;base64,{img_bytes}" width="30">
                        <span>{name} ({data['mmr']} MMR)</span>
                    </div>""",
                    unsafe_allow_html=True
                )
            else:
                st.error(f"Medalla no encontrada: {data['medal']}")
    else:
        st.info("No hay jugadores aún.")
    
    st.divider()
    if st.button(f"🔄 Shuffle Equipos ({len(st.session_state.players)}/10)"):
        balanced_shuffle()
    
    if st.button("🧨 Eliminar todos los jugadores"):
        if st.checkbox("⚠️ ¿Estás SEGURO?"):
            delete_all_players()

col1, col2 = st.columns(2)

def display_team(team_name, team_members):
    total_mmr = sum(st.session_state.players[p]["mmr"] for p in team_members)
    with st.container():
        st.markdown(f"<div class='team-title'>{team_name} (MMR: {total_mmr:,})</div>", unsafe_allow_html=True)
    
    for player in team_members:
        player_data = st.session_state.players[player]
        img_path = IMAGES_DIR / player_data["medal"]
        img_bytes = img_to_bytes(img_path) if img_path.exists() else None
        
        is_selected = player == st.session_state.selected_player
        border_color = "#FFD700" if is_selected else "transparent"
        
        col_a, col_b = st.columns([1, 4])
        with col_a:
            if img_bytes:
                st.markdown(
                    f"""<img src="data:image/png;base64,{img_bytes}" width="50" 
                        style="border: 2px solid {border_color}; border-radius: 50%;">""",
                    unsafe_allow_html=True
                )
            else:
                st.error(f"Imagen no encontrada: {player_data['medal']}")
        
        with col_b:
            # Se muestra el nombre y MMR sin tooltip
            clicked = st.button(
                f"{player} ({player_data['mmr']:,} MMR)",
                key=f"btn_{player}",
                help=f"Seleccionar {player}",
                use_container_width=True
            )
            if clicked:
                st.session_state.selected_player = player
                st.rerun()

with col1:
    display_team("Radiant", st.session_state.radiant)

with col2:
    display_team("Dire", st.session_state.dire)

if st.session_state.radiant and st.session_state.dire:
    diff = abs(
        sum(st.session_state.players[p]["mmr"] for p in st.session_state.radiant) - 
        sum(st.session_state.players[p]["mmr"] for p in st.session_state.dire)
    )
    with st.container():
        st.markdown(f"<div class='mmr-difference'>Diferencia de MMR: {diff:,}</div>", unsafe_allow_html=True)

col_btn1, col_btn2, col_btn3 = st.columns(3)

with col_btn1:
    if st.button("🗑️ Quitar Jugador", disabled=not st.session_state.selected_player, key="remove_player", type="primary"):
        if st.session_state.selected_player:
            if st.session_state.selected_player in st.session_state.radiant:
                st.session_state.radiant.remove(st.session_state.selected_player)
            if st.session_state.selected_player in st.session_state.dire:
                st.session_state.dire.remove(st.session_state.selected_player)
            del st.session_state.players[st.session_state.selected_player]
            st.session_state.selected_player = None
            st.rerun()

with col_btn2:
    if st.button("🔄 Cambiar de Equipo", disabled=not st.session_state.selected_player, key="swap_team", type="primary"):
        if st.session_state.selected_player:
            if st.session_state.selected_player in st.session_state.radiant:
                st.session_state.radiant.remove(st.session_state.selected_player)
                st.session_state.dire.append(st.session_state.selected_player)
            else:
                st.session_state.dire.remove(st.session_state.selected_player)
                st.session_state.radiant.append(st.session_state.selected_player)
            st.rerun()

with col_btn3:
    if st.session_state.combinations:
        st.caption(f"Combinación {st.session_state.current_combo + 1}/{len(st.session_state.combinations)}")

st.markdown("""
    <style>
        .stButton button {
            transition: all 0.3s ease;
        }
        .stButton button:hover {
            transform: scale(1.02);
        }
        div[data-testid="stMetric"] {
            background: #f0f2f6;
            border-radius: 10px;
            padding: 10px;
        }
    </style>
""", unsafe_allow_html=True)
