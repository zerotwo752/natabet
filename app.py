# app.py - Punto de entrada principal
import streamlit as st

# Configuración básica de la página
st.set_page_config(
    page_title="Dota 2 Manager",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS global mínimo
st.markdown("""
<style>
[data-testid="stSidebar"] {
    background: #1a1a1a !important;
}
</style>
""", unsafe_allow_html=True)

# Página principal vacía con navegación
def main():
    st.title("🏆 Dota 2 Team Manager")
    st.subheader("Selecciona una página en el sidebar")
    
    # Información básica en el sidebar
    with st.sidebar:
        st.header("Navegación")
        st.page_link("app.py", label="Inicio", icon="🏠")
        st.page_link("pages/1_Equipos.py", label="Gestión de Equipos", icon="⚔️")
        st.page_link("pages/2_Apuestas.py", label="Sistema de Apuestas", icon="💰")
        
        st.divider()
        st.markdown("**Desarrollado por:**  \nYair Lonelys")
        st.markdown("[Repositorio GitHub](https://github.com/tu_usuario/dota-manager)")

if __name__ == "__main__":
    main()
