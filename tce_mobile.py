import os
import requests as rq
import json
import pandas as pd
import streamlit as st
import pydeck as pdk
#from dotenv import load_dotenv

#load_dotenv()

api_url = st.secrets("API_URL_UNIDADES")
api_key = st.secrets("API_KEY")

headers = {"apikey": f"{api_key}"}
response = rq.get(api_url, headers=headers)

data = json.loads(response.text)
df = pd.DataFrame(data)

# Função para separar as coordenadas em latitude e longitude
def separar_coordenadas(coordenadas):
    lat, lon = map(float, coordenadas.split(','))
    return pd.Series([lat, lon], index=['latitude', 'longitude'])

# Aplicar a função para criar as colunas de latitude e longitude
df[['latitude', 'longitude']] = df['coordenadas'].apply(separar_coordenadas)

def main():
    st.title("TCE MOBILE =)")

    cidades = df['cidade'].unique()
    cidades_selecionadas = st.selectbox("Selecione uma cidade", options=["selecione uma cidade"] + list(cidades))

    unidades = df['unidade'].unique()
    unidades_selecionadas = st.selectbox("Selecione uma unidade", options=["selecione uma unidade"] + list(unidades))

    if cidades_selecionadas != "Selecione uma cidade" and unidades_selecionadas != "Selecione uma unidade":

        df_filtrando = df[(df['cidade'] == cidades_selecionadas) & (df['unidade'] == unidades_selecionadas)]

        df_filtrando = df_filtrando.dropna(subset=['latitude', 'longitude'])

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
                layers=[layer],
                initial_view_state=view_state,
                tooltip={"text": "{unidade}"},  # Tooltip para mostrar a unidade
            )

            st.pydeck_chart(r)

        else:
            st.write("Localização não encontrada pelo filtro selecionado")
    else:
        st.write("Selecione uma cidade ou unidade...")

main()
