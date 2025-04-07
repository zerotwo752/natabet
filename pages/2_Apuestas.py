import streamlit as st

st.title("💰 Sistema de Apuestas")

# Ejemplo básico - amplía esto
with st.form("apuesta_form"):
    st.write("**Realizar una apuesta**")
    equipo = st.radio("Equipo favorito:", ["Radiant", "Dire"])
    monto = st.number_input("Monto a apostar:", min_value=1, step=10)
    
    if st.form_submit_button("Apostar"):
        st.success(f"✅ Apuesta de {monto} USD en {equipo} registrada!")
        # Aquí puedes agregar lógica para guardar apuestas
