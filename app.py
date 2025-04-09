import streamlit as st
import os
from pathlib import Path

# Configuración
YAPE_PATH = "yape/"
DEFAULT_IMAGE = "default.jpg"
#############################################
# Función para convertir imágenes a Base64
#############################################
def to_base64(img_path: Path) -> str:
    if img_path.exists():
        return base64.b64encode(img_path.read_bytes()).decode()
    return ""

# Función mejorada para buscar imágenes
def find_player_image(player_name):
    player_lower = player_name.lower().replace('*', '_star')  # Maneja caracteres especiales
    
    # Orden de búsqueda: jpeg -> jpg -> png
    for ext in ['.jpeg', '.jpg', '.png']:
        image_path = f"{YAPE_PATH}{player_lower}{ext}"
        if os.path.exists(image_path):
            return image_path
    
    return f"{YAPE_PATH}{DEFAULT_IMAGE}"

# Función tooltip con soporte para yair.jpeg
def player_with_tooltip(player_name, display_name=None):
    img_src = find_player_image(player_name)
    display_text = display_name if display_name else player_name
    
    return f"""
    <div class="player-tooltip">
        {display_text}
        <img class="tooltip-image" src="{img_src}" alt="{player_name}">
    </div>
    """

# CSS mejorado
st.markdown("""
<style>
.player-tooltip {
    position: relative;
    display: inline-block;
    cursor: help;
    color: #4a8bfc;
    margin: 0 5px;
    font-weight: bold;
    transition: all 0.2s;
}
.player-tooltip:hover {
    color: #2a6fcc;
    text-shadow: 0 0 5px rgba(74, 139, 252, 0.3);
}
.player-tooltip .tooltip-image {
    display: none;
    position: absolute;
    z-index: 1000;
    width: 220px;
    max-height: 300px;
    object-fit: cover;
    border: 3px solid #4a8bfc;
    background: white;
    padding: 5px;
    border-radius: 10px;
    box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    bottom: 100%;
    left: 50%;
    transform: translateX(-50%);
}
.player-tooltip:hover .tooltip-image {
    display: block;
    animation: tooltipFade 0.25s ease-out;
}
@keyframes tooltipFade {
    0% { opacity: 0; transform: translateX(-50%) translateY(15px); }
    100% { opacity: 1; transform: translateX(-50%) translateY(0); }
}
</style>
""", unsafe_allow_html=True)

# Página principal
def main():
    st.title("🏆 Dota 2 Team Manager")
    
    st.header("Jugadores Disponibles")
    
    # Ejemplo con tu imagen yair.jpeg
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Core Players")
        st.markdown(player_with_tooltip("yair", "Yair (Carry)"), unsafe_allow_html=True)
        st.markdown(player_with_tooltip("quinn", "Quinn (Mid)"), unsafe_allow_html=True)
    
    with col2:
        st.markdown("### Support Players")
        st.markdown(player_with_tooltip("tofu", "Tofu (Support)"), unsafe_allow_html=True)
        st.markdown(player_with_tooltip("fly", "Fly (Captain)"), unsafe_allow_html=True)
    
    st.warning("Nota: Solo yair.jpeg está implementado actualmente. Otros mostrarán la imagen por defecto.")

if __name__ == "__main__":
    main()
