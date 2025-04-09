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
              width: 800px;
              margin: 20px auto;
              padding: 20px;
              background-color: #272752;
              border-radius: 10px;
              overflow: visible;
          }}
          .team-title {{
              text-align: center;
              font-size: 36px;
              font-weight: bold;
              color: #FFD700;
              margin-bottom: 20px;
          }}
          .player-card {{
              position: relative; /* Necesario para el tooltip */
              display: flex;
              align-items: center;
              background-color: #1d1d45;
              border: 2px solid #45aa44;
              border-radius: 10px;
              margin: 10px 0;
              padding: 15px;
              transition: background-color 0.3s;
          }}
          .player-card:hover {{
              background-color: #29295e;
          }}
          .player-info {{
              display: flex;
              align-items: center;
          }}
          .player-info img.medalla {{
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
              margin-left: 20px;
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
          /* Tooltip: se posiciona dentro de la player-card */
          .tooltiptext {{
              visibility: hidden;
              width: auto;
              background-color: rgba(0,0,0,0.8);
              padding: 5px;
              border-radius: 6px;
              position: absolute;
              z-index: 1;
              bottom: 125%;
              left: 50%;
              transform: translateX(-50%);
              opacity: 0;
              transition: opacity 0.3s;
          }}
          .player-card:hover .tooltiptext {{
              visibility: visible;
              opacity: 1;
          }}

          /* Scrollbar personalizado para navegadores Webkit */
          ::-webkit-scrollbar {{
              width: 20px;
              height: 20px;
          }}
          ::-webkit-scrollbar-track {{
              background: #2c2c2c;
          }}
          ::-webkit-scrollbar-thumb {{
              background-color: #555;
              border-radius: 10px;
              border: 3px solid #2c2c2c;
          }}
          ::-webkit-scrollbar-thumb:hover {{
              background-color: #444;
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
        player_data = st.session_state.players[player]
        medal_img_path = IMAGES_DIR / player_data["medal"]
        medal_img = to_base64(medal_img_path) if medal_img_path.exists() else ""
        # Obtenemos la imagen para el tooltip usando find_player_image.
        # Esto retornará la imagen del jugador si existe en "yape", o la imagen default.
        tooltip_img = find_player_image(player)
        tooltip_html = f"""<span class="tooltiptext"><img src="data:image/png;base64,{tooltip_img}" style="width:200px;"></span>"""

        # Información del héroe se genera igual
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
        # La tarjeta se integra en la player-card y el tooltip se muestra al hacer hover sobre ella.
        card = f"""
          <div class="player-card">
              <div class="player-info">
                  <img class="medalla" src="data:image/png;base64,{medal_img}" alt="Medalla">
                  <div class="player-details">
                      <div>{player}</div>
                      <div>{player_data['mmr']:,} MMR</div>
                  </div>
                  {hero_info}
              </div>
              {tooltip_html}
          </div>
        """
        team_html += card
    team_html += """
        </div>
      </body>
    </html>
    """
    components.html(team_html, height=900, width=1600, scrolling=True)
