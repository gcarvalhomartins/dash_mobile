import requests as rq
import json
import pandas as pd
import streamlit as st
import pydeck as pdk
import os

# Desabilitar a barra lateral, o cabeçalho e o rodapé
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}  /* Ocultar o menu principal */
        footer {visibility: hidden;}     /* Ocultar o rodapé */
        header {visibility: hidden;}     /* Ocultar o cabeçalho */
        .stApp {padding-top: 0;}         /* Ajustar o padding do topo */
        .css-1v3fvcr {display: none;}    /* Ocultar o ícone do criador */
    </style>
""", unsafe_allow_html=True)



# Carrega variáveis de ambiente
# load_dotenv()

# Acessa os segredos armazenados no Streamlit Cloud
api_url = st.secrets["API_URL_UNIDADES"]
api_key = st.secrets["API_KEY"]
api_url_fiscalizacoes = st.secrets["API_URL_FISCALIZACOES"]

# # Configuração das URLs e da chave de API
api_url = os.getenv('API_URL_UNIDADES')
api_key = os.getenv('API_KEY')
api_url_fiscalizacoes = os.getenv("API_URL_FISCALIZACOES")

# Cabeçalhos de autenticação
headers = {"apikey": f"{api_key}"}

# Consulta dados da API das unidades
response = rq.get(api_url, headers=headers)
data_unidades = json.loads(response.text)
df_unidades = pd.DataFrame(data_unidades)

# Remove linhas onde 'coordenadas' é nulo
df_unidades = df_unidades.dropna(subset=['coordenadas'])

# Função para separar as coordenadas em latitude e longitude
def separar_coordenadas(coordenadas):
    lat, lon = map(float, coordenadas.split(','))
    return pd.Series([lat, lon], index=['latitude', 'longitude'])

# Aplica a função para criar colunas de latitude e longitude
df_unidades[['latitude', 'longitude']] = df_unidades['coordenadas'].apply(separar_coordenadas)

# Consulta dados da API de fiscalizações
response_fiscalizacoes = rq.get(api_url_fiscalizacoes, headers=headers)
data_fiscalizacoes = json.loads(response_fiscalizacoes.text)
df_fiscalizacoes = pd.DataFrame(data_fiscalizacoes)

# Filtra fiscalizações apenas para tipos Checkin e Checkout e coordenadas não nulas
df_fiscalizacoes = df_fiscalizacoes[
    (df_fiscalizacoes['tipo'].isin(['Checkin', 'Checkout'])) & 
    df_fiscalizacoes[['latitude', 'longitude']].notna().all(axis=1)
]

# Adiciona uma coluna 'color' no DataFrame com base no tipo de fiscalização
df_fiscalizacoes['color'] = df_fiscalizacoes['tipo'].apply(lambda x: [0, 255, 0, 160] if x == "Checkin" else [255, 0, 0, 160])

# Formata a distância para exibir em km e metros
df_fiscalizacoes['distancia_formatada'] = df_fiscalizacoes['distancia'].apply(
    lambda d: f"{int(d // 1000)} km {int(d % 1000)} m"
)

def main():
    st.title("TCE AM")

    # Filtro de cidades em ordem alfabética, removendo valores nulos
    cidades = sorted(df_unidades['cidade'].dropna().unique())
    cidades_selecionadas = st.selectbox("Selecione uma cidade", options=["Todas as cidades"] + cidades)

    # Filtrar unidades com base na cidade selecionada e ordenar em ordem alfabética
    if cidades_selecionadas == "Todas as cidades":
        unidades = sorted(df_unidades['unidade'].dropna().unique())
    else:
        unidades = sorted(df_unidades[df_unidades['cidade'] == cidades_selecionadas]['unidade'].dropna().unique())
    
    # Filtro de unidades
    unidades_selecionadas = st.selectbox("Selecione uma unidade", options=["Todas as unidades"] + unidades)
    
    # Filtro por tipo (Checkin e Checkout)
    tipos = ["Todos os tipos"] + sorted(df_fiscalizacoes['tipo'].dropna().unique())
    tipo_selecionado = st.selectbox("Selecione um tipo", options=tipos)
    
    # Filtra o DataFrame das unidades com base nos filtros selecionados
    df_unidades_filtrado = df_unidades.copy()
    if cidades_selecionadas != "Todas as cidades":
        df_unidades_filtrado = df_unidades_filtrado[df_unidades_filtrado['cidade'] == cidades_selecionadas]
    if unidades_selecionadas != "Todas as unidades":
        df_unidades_filtrado = df_unidades_filtrado[df_unidades_filtrado['unidade'] == unidades_selecionadas]
    
    # Garantir que registros com latitude e longitude estejam presentes
    df_unidades_filtrado = df_unidades_filtrado.dropna(subset=['latitude', 'longitude'])

    # Aplica o filtro de tipo no DataFrame de fiscalizações, caso selecionado
    df_fiscalizacoes_filtrado = df_fiscalizacoes.copy()
    if tipo_selecionado != "Todos os tipos":
        df_fiscalizacoes_filtrado = df_fiscalizacoes_filtrado[df_fiscalizacoes_filtrado['tipo'] == tipo_selecionado]

    # Filtro de comunicantes com base nos outros filtros aplicados
    comunicantes = ["Todos os comunicantes"] + sorted(df_fiscalizacoes_filtrado['nomecomunicante'].dropna().unique())
    comunicante_selecionado = st.selectbox("Selecione um comunicante", options=comunicantes)

    # Aplica o filtro de comunicante, caso selecionado
    if comunicante_selecionado != "Todos os comunicantes":
        df_fiscalizacoes_filtrado = df_fiscalizacoes_filtrado[df_fiscalizacoes_filtrado['nomecomunicante'] == comunicante_selecionado]

    if not df_unidades_filtrado.empty:
        st.subheader("Mapa de Localização das Unidades e Fiscalizações")

        # Camada para unidades (pontos) com cor azul
        layer_unidades = pdk.Layer(
            'ScatterplotLayer',
            data=df_unidades_filtrado,
            get_position='[longitude, latitude]',
            get_color='[0, 0, 255, 160]',  # Azul para unidades
            get_radius=40,  # Tamanho dos pontos
            pickable=True,
            tooltip={
                "html": "<b>Unidade:</b> {unidade}<br>",
                "style": {"backgroundColor": "steelblue", "color": "white"}
            }
        )

        # Camada para fiscalizações com cores diferentes para Checkin e Checkout
        layer_fiscalizacoes = pdk.Layer(
            "ScatterplotLayer",
            data=df_fiscalizacoes_filtrado,
            get_position="[longitude, latitude]",
            get_color="color",  # Usa a coluna 'color' para definir a cor
            get_radius=2,  # Tamanho dos pontos
            pickable=True,
            
        )

        # Define o centro do mapa com base na média das coordenadas das unidades
        view_state = pdk.ViewState(
            latitude=df_unidades_filtrado['latitude'].mean(),
            longitude=df_unidades_filtrado['longitude'].mean(),
            zoom=12,
            pitch=0,
        )

        # Renderiza o mapa com ambas as camadas e um tooltip único
        r = pdk.Deck(
            map_style='mapbox://styles/mapbox/streets-v11',
            layers=[layer_unidades, layer_fiscalizacoes],
            initial_view_state=view_state,
            tooltip={
                "html": "<b>Unidade:</b> {unidade}<br>",
                "style": {"backgroundColor": "steelblue", "color": "white"}
            }
        )

        st.pydeck_chart(r)
    else:
        st.write("Localização não encontrada pelo filtro selecionado")

main()
