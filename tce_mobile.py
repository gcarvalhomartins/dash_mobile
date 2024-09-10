import os
import requests as rq
import json
import pandas as pd
import streamlit as st
import folium as fl
from streamlit_folium import st_folium
from dotenv import load_dotenv


load_dotenv()

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

    if cidades_selecionadas != "Selecione uma opção..." and unidades_selecionadas != "Selecione uma opção...":

        df_filtrando = df[(df['cidade'] == cidades_selecionadas) & (df['unidade'] == unidades_selecionadas)]

        df_filtrando = df_filtrando.dropna(subset=['latitude', 'longitude'])

        if not df_filtrando.empty:

            st.subheader("Mapa de Localização das Unidades")

            m = fl.Map(location=[df_filtrando['latitude'].mean(), df_filtrando['longitude'].mean()], zoom_start=12)

            cores = {
                'Checkin': 'blue',
                'Check-in': 'blue',
                'Checkout': 'red',
                'Unidades': 'purple'
            }

            for _, row in df_filtrando.iterrows():
                fl.Marker(
                    location=[row['latitude'], row['longitude']],
                    popup=row['unidade'],
                    icon=fl.Icon(color=cores.get(row['unidade'], 'gray'))
                ).add_to(m)

                fl.Circle(
                    location=[row['latitude'], row['longitude']],
                    radius=100,
                    color=cores.get(row['unidade'], 'gray'),
                    fill=True,
                    fill_opacity=0.2
                ).add_to(m)
     
            st_folium(m, width=800, height=500)
 
        else:
            st.write("Localização não encontrada pelo filtro selecionado")
    else:
        st.write("Selecione uma cidade ou unidade...")

main()


# st.subheader(f'Tabela de unidades e categorias selecionadas: {cidades_selecionadas} e {unidades_selecionadas}')
# st.dataframe(df_filtrando) 
# test