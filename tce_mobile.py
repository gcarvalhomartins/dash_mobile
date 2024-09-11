import requests as rq
import json
import pandas as pd
import streamlit as st
import pydeck as pdk
#import os
#from dotenv import load_dotenv

#load_dotenv()

# Acessa os segredos armazenados no Streamlit Cloud
api_url = st.secrets["API_URL_UNIDADES"]
api_key = st.secrets["API_KEY"]

# Configura o cabeçalho da API
headers = {"apikey": f"{api_key}"}
response = rq.get(api_url, headers=headers)

# Converte a resposta para um DataFrame
data = json.loads(response.text)
df = pd.DataFrame(data)

# Função para separar as coordenadas em latitude e longitude
def separar_coordenadas(coordenadas):
    lat, lon = map(float, coordenadas.split(','))
    return pd.Series([lat, lon], index=['latitude', 'longitude'])

# Aplica a função para criar as colunas de latitude e longitude
df[['latitude', 'longitude']] = df['coordenadas'].apply(separar_coordenadas)

def main():
    st.title("TCE AM")

    # Filtro de cidades
    cidades = df['cidade'].unique()
    cidades_selecionadas = st.selectbox("Selecione uma cidade", options=["Todas as cidades"] + list(cidades))

    # Filtrar unidades com base na cidade selecionada
    if cidades_selecionadas == "Todas as cidades":
        unidades = df['unidade'].unique()
    else:
        unidades = df[df['cidade'] == cidades_selecionadas]['unidade'].unique()
    
    # Filtro de unidades
    unidades_selecionadas = st.selectbox("Selecione uma unidade", options=["Todas as unidades"] + list(unidades))

    # Filtrar por cidade e unidade
    df_filtrando = df.copy()

    if cidades_selecionadas != "Todas as cidades":
        df_filtrando = df_filtrando[df_filtrando['cidade'] == cidades_selecionadas]

    if unidades_selecionadas != "Todas as unidades":
        df_filtrando = df_filtrando[df_filtrando['unidade'] == unidades_selecionadas]

    df_filtrando = df_filtrando.dropna(subset=['latitude', 'longitude'])

    # Verifica se há dados filtrados
    if not df_filtrando.empty:
        st.subheader("Mapa de Localização das Unidades")

        # Define a camada de pontos no mapa
         
        layer = pdk.Layer(
            'ScatterplotLayer',
            data=df_filtrando,
            get_position='[longitude, latitude]',
            get_color='[200, 30, 0, 160]',  # Cor do marcador
            get_radius=100,  # Tamanho dos pontos
            pickable=True,
        )

        # Define o centro do mapa com base na média das coordenadas
        view_state = pdk.ViewState(
            latitude=df_filtrando['latitude'].mean(),
            longitude=df_filtrando['longitude'].mean(),
            zoom=12,
            pitch=0,
        )

        # Renderiza o mapa
        r = pdk.Deck(
            map_style='mapbox://styles/mapbox/streets-v11',
            layers=[layer],
            initial_view_state=view_state,
            tooltip={"text": "{unidade}"},  # Tooltip para mostrar a unidade
        )

        st.pydeck_chart(r)

    else:
        st.write("Localização não encontrada pelo filtro selecionado")

main()
