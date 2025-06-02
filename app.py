# Instalacao de bibliotecas necessarias
import streamlit as st

# IMPORTANTE: st.set_page_config() DEVE ser a primeira função Streamlit
st.set_page_config(
    page_title="Landscape Metrics Extractor",
    page_icon="🏞️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

import geemap.foliumap as geemap
from streamlit_folium import st_folium
import json
import ee
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pylandstats as pls
import collections
import geopandas as gpd
import tempfile
import os
import uuid
import logging
from pathlib import Path

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Linha de compatibilidade
collections.Callable = collections.abc.Callable

# Configurações de segurança
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.geojson'}
MIN_BUFFER = 1000
MAX_BUFFER = 10000

def validate_file_upload(uploaded_file):
    """Valida o arquivo enviado pelo usuário"""
    if not uploaded_file:
        return False, "Nenhum arquivo enviado"
    
    # Verifica tamanho do arquivo
    if uploaded_file.size > MAX_FILE_SIZE:
        return False, f"Arquivo muito grande. Máximo: {MAX_FILE_SIZE // (1024*1024)}MB"
    
    # Verifica extensão
    file_extension = Path(uploaded_file.name).suffix.lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        return False, f"Extensão não permitida. Permitido: {ALLOWED_EXTENSIONS}"
    
    # Verifica nome do arquivo (evita caracteres perigosos)
    if any(char in uploaded_file.name for char in ['..', '/', '\\', '<', '>', '|', '*', '?']):
        return False, "Nome do arquivo contém caracteres não permitidos"
    
    return True, "Arquivo válido"

def initialize_ee():
    """
    Inicializa o Google Earth Engine usando credenciais de conta de serviço
    armazenadas nos segredos do Streamlit.
    """
    try:
        # Testa se já está inicializado
        ee.Number(1).getInfo()
        logger.info("Earth Engine já inicializado")
        return True
        
    except ee.EEException:
        # Não inicializado, procede com a inicialização
        try:
            # Verifica se as credenciais estão nos segredos do Streamlit
            if "gee_service_account_credentials" in st.secrets:
                # Obtém a string JSON das credenciais
                json_data = st.secrets["gee_service_account_credentials"]
                
                # Parse do JSON
                try:
                    json_object = json.loads(json_data, strict=False)
                except json.JSONDecodeError as json_err:
                    logger.error(f"Erro JSON: {json_err}")
                    st.error("❌ Credenciais JSON inválidas")
                    st.stop()
                    return False
                
                # Valida campos obrigatórios
                required_fields = ['client_email', 'private_key', 'project_id']
                missing_fields = [field for field in required_fields if not json_object.get(field)]
                if missing_fields:
                    logger.error(f"Campos obrigatórios ausentes: {missing_fields}")
                    st.error(f"❌ Campos obrigatórios ausentes nas credenciais: {missing_fields}")
                    st.stop()
                    return False
                
                # Extrai o email da conta de serviço
                service_account = json_object.get('client_email')
                
                # Converte de volta para string JSON (conforme tutorial)
                json_object_str = json.dumps(json_object)
                
                # Cria as credenciais
                credentials = ee.ServiceAccountCredentials(
                    service_account, 
                    key_data=json_object_str
                )
                
                # Inicializa o Earth Engine
                ee.Initialize(
                    credentials=credentials,
                    opt_url='https://earthengine-highvolume.googleapis.com'
                )
                
                logger.info("Earth Engine inicializado com sucesso")
                st.sidebar.success("✅ Earth Engine conectado!")
                return True
                
            else:
                # Fallback para desenvolvimento local
                logger.warning("Credenciais GEE não encontradas, tentando inicialização local")
                st.warning("⚠️ Modo desenvolvimento local")
                ee.Initialize(opt_url='https://earthengine-highvolume.googleapis.com')
                st.sidebar.info("🏠 Earth Engine (local)")
                return True
                
        except Exception as ex:
            logger.error(f"Falha ao inicializar Earth Engine: {ex}")
            st.error("❌ Falha na inicialização do Earth Engine")
            with st.expander("🔍 Detalhes do erro"):
                st.error(f"Erro: {str(ex)}")
                st.markdown("""
                **Possíveis soluções:**
                1. Verifique as credenciais no Streamlit Cloud
                2. Confirme permissões da conta de serviço no GCP
                3. Verifique se Earth Engine API está habilitado
                """)
            st.stop()
            return False

@st.cache_data
def uploaded_file_to_gdf(data):
    """Converte arquivo uploaded para GeoDataFrame com validações de segurança"""
    try:
        # Validação de entrada
        is_valid, message = validate_file_upload(data)
        if not is_valid:
            raise ValueError(f"Arquivo inválido: {message}")
        
        # Cria arquivo temporário seguro
        file_extension = Path(data.name).suffix.lower()
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}{file_extension}"
        file_path = os.path.join(tempfile.gettempdir(), safe_filename)
        
        # Garante que o caminho é seguro
        temp_dir = Path(tempfile.gettempdir()).resolve()
        file_path_resolved = Path(file_path).resolve()
        if not str(file_path_resolved).startswith(str(temp_dir)):
            raise ValueError("Caminho de arquivo inseguro")
        
        try:
            with open(file_path, "wb") as file:
                file.write(data.getbuffer())
            
            # Lê o arquivo com tratamento específico para versões do fiona
            try:
                if file_extension == ".kml":
                    # Para KML, força o driver específico
                    try:
                        import fiona
                        fiona.supported_drivers['KML'] = 'rw'
                    except:
                        pass
                    gdf = gpd.read_file(file_path, driver="KML")
                else:
                    # Para GeoJSON, lê normalmente
                    gdf = gpd.read_file(file_path)
                    
            except Exception as read_error:
                # Fallback: tenta ler como JSON puro e converter
                logger.warning(f"Erro na leitura padrão: {read_error}. Tentando método alternativo...")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    geojson_data = json.load(f)
                
                # Converte JSON para GeoDataFrame manualmente
                import shapely.geometry as geom
                
                features = geojson_data.get('features', [])
                if not features:
                    raise ValueError("Nenhuma feature encontrada no GeoJSON")
                
                geometries = []
                properties_list = []
                
                for feature in features:
                    # Cria geometria usando shapely
                    geom_data = feature.get('geometry', {})
                    if geom_data.get('type') == 'Point':
                        coords = geom_data.get('coordinates', [])
                        if len(coords) >= 2:
                            geometry = geom.Point(coords[0], coords[1])
                            geometries.append(geometry)
                            properties_list.append(feature.get('properties', {}))
                
                if not geometries:
                    raise ValueError("Nenhuma geometria válida encontrada")
                
                # Cria GeoDataFrame manualmente
                gdf = gpd.GeoDataFrame(properties_list, geometry=geometries, crs='EPSG:4326')
            
            # Valida GeoDataFrame
            if gdf.empty:
                raise ValueError("Arquivo GeoJSON vazio")
            
            # Garante que tem CRS definido
            if gdf.crs is None:
                gdf = gdf.set_crs('EPSG:4326')
            
            logger.info(f"Arquivo processado com sucesso: {len(gdf)} geometrias")
            return gdf
            
        finally:
            # Remove arquivo temporário
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as cleanup_error:
                    logger.warning(f"Erro ao limpar arquivo temporário: {cleanup_error}")
    
    except Exception as e:
        logger.error(f"Erro ao processar arquivo: {e}")
        raise

# Inicializa o Earth Engine ANTES de qualquer outra operação
if not initialize_ee():
    st.stop()

# Header principal
col1, col2 = st.columns([2, 3])

with col1:
    original_title = '<h1 style="color:Blue">🏞️ Landscape Metrics Extractor</h1>'
    st.markdown(original_title, unsafe_allow_html=True)
    st.caption(
        "Powered by MapBiomas, Pylandstats, Google Earth Engine and Geemap | Developed by Pedro Higuchi ([@pe_hi](https://twitter.com/pe_hi))"
    )
    st.caption("Contato: higuchip@gmail.com")

with col2:
    st.markdown(
        "<h4 style=' color: black; background-color:lightgreen; padding:25px; border-radius: 25px; box-shadow: 0 0 0.1em black'>Aplicativo Web para extração de métricas de paisagem de pontos de interesse a partir da base de dados do MapBiomas</h4>",
        unsafe_allow_html=True,
    )

# Sidebar com informações de segurança
with st.sidebar:
    st.markdown("### 🔒 Informações")
    st.info(f"""
    📁 Arquivo máx: {MAX_FILE_SIZE // (1024*1024)}MB  
    📍 Apenas 1 ponto por vez  
    🔧 Buffer: {MIN_BUFFER}-{MAX_BUFFER}m  
    🔒 Apenas GeoJSON  
    """)
    
    # Status do Earth Engine
    if st.button("🔄 Status GEE"):
        try:
            ee.Number(1).getInfo()
            st.success("✅ GEE Conectado")
        except:
            st.error("❌ GEE Desconectado")

st.caption("⚠️ **Em desenvolvimento**")
st.text(" ")
st.markdown("---")

# Seção 1: Seleção do ponto
st.markdown(
    "<h3>1) Selecione um ponto de interesse 📌 </h3>",
    unsafe_allow_html=True,
)

st.warning(
    "⚠️ **Instruções:** Use apenas a ferramenta 'Draw a marker' para selecionar **UM** ponto, depois clique em 'Export'."
)

# Mapa para seleção de pontos
try:
    Map = geemap.Map(
        center=[-15.7801, -47.9292], 
        zoom=5, 
        Draw_export=True,
        plugin_Draw=True,
        plugin_LatLngPopup=False
    )
    Map.add_basemap("HYBRID")

    # Container para o mapa
    map_container = st.container()
    with map_container:
        map_data = st_folium(Map, width=700, height=400, returned_objects=["last_clicked", "all_drawings"])

except Exception as map_error:
    logger.error(f"Erro ao criar mapa: {map_error}")
    st.error("❌ Erro ao carregar o mapa. Verifique a conexão com o Earth Engine.")
    
    # Mapa alternativo simples
    st.info("🗺️ Carregando mapa alternativo...")
    try:
        import folium
        m = folium.Map(location=[-15.7801, -47.9292], zoom_start=5)
        folium.Marker([-15.7801, -47.9292], popup="Exemplo de localização").add_to(m)
        st_folium(m, width=700, height=400)
        st.warning("⚠️ Use o mapa acima como referência e carregue um arquivo GeoJSON manualmente.")
    except Exception as folium_error:
        logger.error(f"Erro no mapa alternativo: {folium_error}")
        st.error("❌ Não foi possível carregar nenhum mapa. Prossiga diretamente para o upload do arquivo GeoJSON.")

st.markdown("---")

# Seção 2: Upload do arquivo
st.markdown(
    "<h3>2) Upload do arquivo GeoJSON 📤</h3>",
    unsafe_allow_html=True,
)

data = st.file_uploader(
    f"📁 Faça upload do arquivo GeoJSON exportado acima",
    type=["geojson"],
    help=f"Limite: {MAX_FILE_SIZE // (1024*1024)}MB • Apenas arquivos GeoJSON são aceitos"
)

st.markdown("---")

# Processamento principal
if data:
    try:
        # Seção 3: Configuração do buffer
        st.markdown(
            "<h3>3) Defina o tamanho do raio (m) do buffer 🎯</h3>",
            unsafe_allow_html=True,
        )
        
        buffer_dist = st.slider(
            'Tamanho do raio (m) do buffer:', 
            MIN_BUFFER, 
            MAX_BUFFER, 
            5000,
            step=500,
            help="Área circular ao redor do ponto para análise das métricas de paisagem"
        )
        
        with st.spinner("📂 Processando arquivo GeoJSON..."):
            gdf = uploaded_file_to_gdf(data)

        # Converte para formato Earth Engine com tratamento robusto
        try:
            # Primeiro tenta o método padrão do geemap
            gdf_json = gdf.to_json()
            gdf_features = json.loads(gdf_json)["features"]
            
        except Exception as json_error:
            logger.warning(f"Erro na conversão JSON padrão: {json_error}. Tentando método alternativo...")
            
            # Método alternativo: converte manualmente
            gdf_features = []
            for idx, row in gdf.iterrows():
                feature = {
                    "type": "Feature",
                    "geometry": json.loads(gpd.GeoSeries([row.geometry]).to_json())["features"][0]["geometry"],
                    "properties": {k: v for k, v in row.items() if k != 'geometry' and pd.notna(v)}
                }
                gdf_features.append(feature)
        
        # Valida que há apenas um ponto
        if len(gdf_features) > 1:
            st.error("❌ Você selecionou mais de um ponto. Por favor, selecione apenas **UM** ponto de interesse.")
            st.stop()
        elif len(gdf_features) == 0:
            st.error("❌ Nenhum ponto encontrado no arquivo. Verifique o arquivo GeoJSON.")
            st.stop()
        
        # Cria ROI e buffer com tratamento de erro
        with st.spinner("🌍 Preparando área de interesse..."):
            try:
                roi = ee.FeatureCollection(gdf_features)
                roi_buffer = roi.geometry().buffer(buffer_dist)
                
                # Testa se a geometria é válida
                roi_area = roi.geometry().area().getInfo()
                if roi_area is None or roi_area <= 0:
                    raise ValueError("Geometria inválida ou área zero")
                    
            except Exception as roi_error:
                logger.error(f"Erro ao criar ROI: {roi_error}")
                st.error("❌ Erro ao processar a geometria do ponto. Verifique se o arquivo GeoJSON contém um ponto válido.")
                st.stop()
        
        # Layout em duas colunas para visualização
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                "<h5 style=' color: black; background-color:yellow; padding:5px; border-radius: 5px; box-shadow: 0 0 0.1em black'> 📍 Área de interesse:</h5>", 
                unsafe_allow_html=True
            )
            
            # Mapa da área de interesse
            try:
                roi_map = geemap.Map()
                roi_map.add_basemap("HYBRID")
                roi_map.centerObject(roi, zoom=11)
                roi_map.addLayer(roi_buffer, {}, "ROI Buffer")
                
                st_folium(roi_map, width=400, height=300)
                
            except Exception as roi_map_error:
                logger.warning(f"Erro ao criar mapa ROI: {roi_map_error}")
                st.info("📍 Área de interesse processada (mapa indisponível)")
                st.text(f"Buffer de {buffer_dist}m aplicado ao ponto selecionado")

        # Processamento dos dados MapBiomas
        with st.spinner("🛰️ Baixando dados do MapBiomas..."):
            try:
                # Baixa dados do MapBiomas
                mb = ee.Image("projects/mapbiomas-workspace/public/collection6/mapbiomas_collection60_integration_v1")
                
                # Seleciona ano e extrai dados para o buffer
                mb_year_sample = mb.select('classification_2020').sampleRectangle(roi_buffer)
                mb_year_sample_get = mb_year_sample.get('classification_2020')
                np_arr_mb = np.array(mb_year_sample_get.getInfo())
                
                if np_arr_mb.size == 0:
                    raise ValueError("Nenhum dado encontrado para a área selecionada")
                
            except Exception as mb_error:
                logger.error(f"Erro ao baixar dados MapBiomas: {mb_error}")
                st.error("❌ Erro ao baixar dados do MapBiomas. Tente uma área diferente.")
                st.stop()

        # Análise da paisagem
        with col2:
            st.markdown(
                "<h5 style=' color: black; background-color:yellow; padding:5px; border-radius: 5px; box-shadow: 0 0 0.1em black'> 🗺️ Classes de cobertura do solo:</h5>", 
                unsafe_allow_html=True
            )
            
            with st.spinner("📊 Calculando métricas da paisagem..."):
                try:
                    # Instancia PyLandStats
                    ls = pls.Landscape(np_arr_mb, res=(30, 30))
                    
                    # Plota paisagem
                    fig, ax = plt.subplots(figsize=(6, 4))
                    ls.plot_landscape(legend=True, ax=ax)
                    st.pyplot(fig)
                    plt.close()
                    
                except Exception as pls_error:
                    logger.error(f"Erro no PyLandStats: {pls_error}")
                    st.error("❌ Erro ao processar métricas da paisagem")
                    st.stop()

        st.markdown("---")
        
        # Cálculo das métricas
        st.markdown(
            "<h5 style=' color: black; background-color:yellow; padding:5px; border-radius: 5px; box-shadow: 0 0 0.1em black'> 📈 Métricas da paisagem:</h5>", 
            unsafe_allow_html=True
        )
        
        with st.spinner("🔢 Computando métricas detalhadas..."):
            try:
                # Calcula métricas de classe
                class_metrics_df = ls.compute_class_metrics_df(
                    metrics=[
                        'total_area', 'proportion_of_landscape', 'number_of_patches',
                        'largest_patch_index', 'total_edge', 'landscape_shape_index',
                        'area_mn', 'perimeter_mn', 'perimeter_area_ratio_mn',
                        'shape_index_mn', 'fractal_dimension_mn', 'euclidean_nearest_neighbor_mn'
                    ]
                )
                
                # Processa índices das classes
                classes_index = list(map(int, class_metrics_df.index))
                
                # Dicionário de legendas MapBiomas
                legend_keys = [
                    ' ',  # 0
                    'Floresta',  # 1
                    ' ',  # 2
                    'Formacao florestal',  # 3
                    'Savana',  # 4
                    'Mangue',  # 5
                    ' ', ' ', ' ',  # 6-8
                    'Silvicultura',  # 9
                    'Formação natural nao-florestal',  # 10
                    'Campo Alagado e Área Pantanosa',  # 11
                    'Campos',  # 12
                    'Outras formacoes nao-florestais',  # 13
                    'Agropecuaria',  # 14
                    'Pastagem',  # 15
                    ' ', ' ',  # 16-17
                    'Agricultura',  # 18
                    'Agricultura temporarias',  # 19
                    'Cana',  # 20
                    'Mosaico de Agricultura e Pastagem',  # 21
                    'Area nao Vegetada',  # 22
                    'Dunas',  # 23
                    'Area Urbanizada',  # 24
                    'Outras areas nao vegetadas',  # 25
                    'Agua',  # 26
                    'Nao Observado',  # 27
                    ' ',  # 28
                    'Afloramento rochoso',  # 29
                    'Mineracao',  # 30
                    'Aquicultura',  # 31
                    'Sal',  # 32
                    'Rio, lago e oceano',  # 33
                    ' ', ' ',  # 34-35
                    'Lavoura Perene',  # 36
                    ' ', ' ',  # 37-38
                    'Soja',  # 39
                    'Arroz',  # 40
                    'Outras culturas temporarias',  # 41
                    ' ', ' ', ' ', ' ',  # 42-45
                    'Cafe',  # 46
                    'Citrus',  # 47
                    'Outras lavouras perenes',  # 48
                    'Restinga arborea'  # 49
                ]
                
                # Cria dicionário de legenda
                keys = list(range(len(legend_keys)))
                legend_dict = {keys[i]: legend_keys[i] for i in range(len(legend_keys))}
                
                # Substitui índices por nomes
                replaced_list = [legend_dict.get(x, f'Classe {x}') for x in classes_index]
                class_metrics_df.index = replaced_list
                
                # Filtra elementos com mais de 10% de proporção
                st.info("📊 **Elementos com mais de 10% de proporção na paisagem:**")
                
                class_metrics_df_sub = class_metrics_df[class_metrics_df['proportion_of_landscape'] > 10]
                class_metrics_df_sub = class_metrics_df_sub.sort_values(by=['total_area'], ascending=False)
                
                if class_metrics_df_sub.empty:
                    st.warning("⚠️ Nenhuma classe com proporção > 10% encontrada. Mostrando todas as classes:")
                    class_metrics_df_sub = class_metrics_df.sort_values(by=['total_area'], ascending=False)
                
                # Exibe tabela de resultados
                st.dataframe(class_metrics_df_sub, use_container_width=True)
                
            except Exception as metrics_error:
                logger.error(f"Erro ao calcular métricas: {metrics_error}")
                st.error("❌ Erro ao calcular métricas da paisagem")
                st.stop()
        
        # Download dos resultados
        st.markdown("---")
        download_container = st.container()
        with download_container:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.markdown(
                    "<h3 style='text-align: center;'> 📥 Download dos resultados</h3>",
                    unsafe_allow_html=True,
                )

                @st.cache_data
                def convert_df(df):
                    return df.to_csv(sep=";", decimal=",").encode("utf-8")

                csv = convert_df(class_metrics_df_sub)
                
                # Nome de arquivo com timestamp
                safe_filename = f"landscape_metrics_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"

                st.download_button(
                    "📥 Download CSV",
                    csv,
                    safe_filename,
                    "text/csv",
                    key="download-csv",
                    use_container_width=True
                )
        
        logger.info(f"Métricas da paisagem calculadas com sucesso para buffer de {buffer_dist}m")
    
    except Exception as e:
        logger.error(f"Erro no processamento principal: {e}")
        st.error("❌ Erro no processamento dos dados")
        with st.expander("🔍 Detalhes do erro"):
            st.error(str(e))

# Informações adicionais
st.markdown("---")

# Detalhamento das métricas em expander
with st.expander("📊 **Detalhamento das métricas** (clique para expandir)", expanded=False):
    st.markdown(
        "Para maiores informações, acessar o site do [PyLandStats](https://pylandstats.readthedocs.io/en/latest/)."
    )
    
    metrics_names = [
        'total_area', 'proportion_of_landscape', 'number_of_patches',
        'largest_patch_index', 'total_edge', 'landscape_shape_index',
        'area_mn', 'perimeter_mn', 'perimeter_area_ratio_mn',
        'shape_index_mn', 'fractal_dimension_mn', 'euclidean_nearest_neighbor_mn'
    ]
    
    metrics_traducao = [
        'Área Total (ha)', 'Proporção da paisagem (%)', 'Número de Manchas',
        'Índice de maior mancha', 'Total de Bordas', 'Índice de forma da paisagem',
        'Área média (ha)', 'Perímetro médio (m)', 'Razão de perímetro/área média',
        'Média de índice de forma', 'Dimensão fractal média', 
        'Distância média para o vizinho mais próximo (m)'
    ]

    zipped = list(zip(metrics_names, metrics_traducao))
    detalhamento_df = pd.DataFrame(zipped, columns=['Item', 'Métricas'])
    st.table(detalhamento_df.set_index("Item"))

# Referências em footer
st.markdown("---")
st.subheader("📚 Referências:")

references = [
    "**Bosch M.** (2019). PyLandStats: An open-source Pythonic library to compute landscape metrics. *PLOS ONE*, 14(12), 1-19. doi.org/10.1371/journal.pone.0225734",
    
    "**Souza et al.** (2020). Reconstructing Three Decades of Land Use and Land Cover Changes in Brazilian Biomes with Landsat Archive and Earth Engine. *Remote Sensing*, Volume 12, Issue 17, 10.3390/rs12172735.",
    
    "**Wu, Q.** (2020). geemap: A Python package for interactive mapping with Google Earth Engine. *The Journal of Open Source Software*, 5(51), 2305. https://doi.org/10.21105/joss.02305",
    
    "**Wu, Q. et al.** (2019). Integrating LiDAR data and multi-temporal aerial imagery to map wetland inundation dynamics using Google Earth Engine. *Remote Sensing of Environment*, 228, 1-13.",
    
    "**Projeto MapBiomas** - Iniciativa multi-institucional para gerar mapas anuais de uso e cobertura da terra. Descrição completa em http://mapbiomas.org"
]

for ref in references:
    st.markdown(f"• {ref}")

st.markdown("---")
