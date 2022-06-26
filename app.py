# Instalacao de bibliotecas necessarias

import streamlit as st
import geemap.foliumap as geemap
import json
import ee
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import pylandstats as pls
import collections
import geopandas as gpd

collections.Callable = collections.abc.Callable



@st.cache(allow_output_mutation=True)
def uploaded_file_to_gdf(data):
    import tempfile
    import os
    import uuid

    _, file_extension = os.path.splitext(data.name)
    file_id = str(uuid.uuid4())
    file_path = os.path.join(tempfile.gettempdir(), f"{file_id}{file_extension}")

    with open(file_path, "wb") as file:
        file.write(data.getbuffer())

    if file_path.lower().endswith(".kml"):
        gpd.io.file.fiona.drvsupport.supported_drivers["KML"] = "rw"
        gdf = gpd.read_file(file_path, driver="KML")
    else:
        gdf = gpd.read_file(file_path)

    return gdf



original_title = '<h1 style="color:Blue"> 🏞️ Landscape Metrics Extractor   </h1>'
st.markdown(original_title, unsafe_allow_html=True)
st.caption(
    "Powered by  MapBiomas,Pylandstats, Google Earth Engine and Geemap,| Developed by Pedro Higuchi ([@pe_hi](https://twitter.com/pe_hi))"
)
st.caption("Contato: higuchip@gmail.com")
st.markdown(
    "<h4 style=' color: black; background-color:lightgreen; padding:25px; border-radius: 25px; box-shadow: 0 0 0.1em black'>Aplicativo Web para extração de métricas de paisagem de pontos de interesse a partir da base de dados do MapBiomas</h4>",
    unsafe_allow_html=True,
)
st.caption("Em desenvolvimento")

st.markdown("___")

###########################

st.markdown(
    "<h3>1) Selecione um ponto de interesse 📌 </h3>",
    unsafe_allow_html=True,
)

st.warning(
    "Usar **apenas** a ferramenta 'Draw a marker', para selecionar os pontos de interesse e, em seguida, clicar em 'Export'."
)

Map = geemap.Map(center=[-15.7801, -47.9292], zoom=5, Draw_export=True)
Map.add_basemap("HYBRID")
Map.to_streamlit(height=400)


st.markdown("""---""")

# Definição de um buffer de 5000 m de raio e, posteriormente,inserindo um quadrado em seu redor 


st.markdown(
    "<h3>2) Upload do arquivo GeoJSON 📤</h3>",
    unsafe_allow_html=True,
)


data = st.file_uploader(
    "Fazer o upload do arquivo GeoJSON exportado no passo acima para utilizar como áreas de interesse 👇👇",
    type=["geojson"],
)
st.markdown("""---""")

if data:
    st.markdown(
    "<h3>3) Defina o tamanho do raio (m) do buffer</h3>",
    unsafe_allow_html=True,
)
    buffer_dist = st.slider('Tamanho do raio (m) do buffer:', 1000, 2500, 5000)


    gdf = uploaded_file_to_gdf(data)

    gdf = gdf.to_json()
    gdf = json.loads(gdf)
    gdf = gdf["features"]
    if len(gdf) > 1:
        st.write(
        "Você selecionou mais de um ponto de interesse. Por favor, selecione apenas um ponto de interesse."
    )
        st.stop()
    roi = ee.FeatureCollection(gdf)
    roi_buffer = roi.geometry().buffer(buffer_dist)
    
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<h5 style=' color: black; background-color:yellow; padding:5px; border-radius: 5px; box-shadow: 0 0 0.1em black'> Área de interesse:</h5>", unsafe_allow_html=True)
        Map = geemap.Map()
        Map.add_basemap("HYBRID")
        Map.centerObject(roi, zoom=11)
        Map.addLayer(roi_buffer, {}, "ROI")
        Map.to_streamlit(height=300, width=400)

    # Baixando MapBiomas
    mb = ee.Image("projects/mapbiomas-workspace/public/collection6/mapbiomas_collection60_integration_v1")

    # Selecao de ano, sample rectangle para o buffer considerado
    mb_year_sample = mb.select('classification_2020').sampleRectangle(roi_buffer)
    mb_year_sample_get= mb_year_sample.get('classification_2020')
    np_arr_mb = np.array(mb_year_sample_get.getInfo())
    
    #instanciando pylandstat
    with col2:
        st.markdown("<h5 style=' color: black; background-color:yellow; padding:5px; border-radius: 5px; box-shadow: 0 0 0.1em black'> Classes de cobertura do solo:</h5>", unsafe_allow_html=True)

        ls = pls.Landscape(np_arr_mb , res=(30,30))
        ls.plot_landscape(legend=True) 
        st.set_option('deprecation.showPyplotGlobalUse', False)
        st.text("")
        st.pyplot()

    st.markdown("""---""")
    st.markdown("<h5 style=' color: black; background-color:yellow; padding:5px; border-radius: 5px; box-shadow: 0 0 0.1em black'> Métricas da paisagem:</h5>", unsafe_allow_html=True)
    class_metrics_df = ls.compute_class_metrics_df(metrics = ['total_area', 'proportion_of_landscape', 'number_of_patches',
       'largest_patch_index', 'total_edge', 
       'landscape_shape_index',  'area_mn',  'perimeter_mn',
    'perimeter_area_ratio_mn', 'shape_index_mn','fractal_dimension_mn',  'euclidean_nearest_neighbor_mn'])
    
    classes_index = (map(int, class_metrics_df.index))
    classes_index = list(classes_index)
    #classes_index
    

    legend_keys = [' ', # 0
                'Floresta', # 1 1. Forest
                ' ', # 2  
                'Formacao florestal', # 3 1.1. Forest Formation 
                'Savana', # 4 1.2. Savanna Formation
                'Mangue', # 5 1.2. Mangrove 
                ' ', # 6
                ' ', # 7
                ' ', # 8
                'Silvicultura', # 9 3.2. Forest Plantation
                'Formação natural nao-florestal', # 10  Non Forest Natural Formation
                'Campo Alagado e Área Pantanosa', # 11 Wetlands
                'Campos', # 12 Grassland
                'Outras formacoes nao-florestais', # 13 2.5. Other non Forest Formations
                'Agropecuaria', # 14 3. Farming
                'Pastagem', # 15 3.1. Pasture
                ' ', # 16
                ' ', # 17
                'Agricultura', # 18 3.2. Agriculture
                'Agricultura temporarias', # 19 3.2.1. Temporary Crop
                'Cana', # 20  3.2.1.2. Sugar cane
                'Mosaico de Agricultura e Pastagem', # 21 3.4. Mosaic Agriculture and Pasture
                'Area nao Vegetada', # 22 4. Non vegetated Area
                'Dunas', # 23 4.1. Beach, Dune and Sand Spot
                'Area Urbanizada', # 24 4.2. Urban Area 
                'Outras areas nao vegetadas', # 25 4.4. Other non Vegetaded Areas
                'Agua', # 26 5. Water
                'Nao Observado', # 27 6. Non Observed
                ' ', # 28
                'Afloramento rochoso', # 29 2.4. Rocky Outcrop
                'Mineracao', # 30 4.3. Mining
                'Aquicultura', # 31 5.2. Aquaculture
                'Sal', # 32  2.3. Salt Flat
                'Rio, lago e oceano', # 33 5.1. River,Lake and Ocean
                ' ', # 34
                ' ', # 35
                'Lavoura Perene', # 36 3.2.2. Perennial Corp
                ' ', # 37
                ' ', # 38
                'Soja', # 39 3.2.1.1. Soybean
                'Arroz', # 40 3.2.1.3. Rice
                'Outras culturas temporarias', # 41 3.2.1.4. Other temporary Crops
                ' ', # 42
                ' ', # 43
                ' ', # 44
                ' ', # 45
                'cafe', # 46 3.2.2.1. Coffee 
                'Citrus', # 47 3.2.2.2. Citrus
                'Outras lavouras perenes',# 48 3.2.2.3. Other Perennial Crop 
                'Restinga arborea']# 49 1.4. Wooded Restinga

    keys = list(range(len(legend_keys)))
    legend_dict= {keys[i]: legend_keys[i] for i in range(len(legend_keys))}
    
    replaced_list = [x if x not in legend_dict else legend_dict[x] for x in classes_index ]
    
    class_metrics_df.index = replaced_list 

    st.text("")
    st.text("Elementos com mais do que 10% de proporção na paisagem: ")

    class_metrics_df_sub = class_metrics_df[class_metrics_df['proportion_of_landscape'] > 10]

    class_metrics_df_sub = class_metrics_df_sub.sort_values(by=['total_area'], ascending=False)
    class_metrics_df_sub
    st.markdown(
        "<h3> 👇👇👇 clique para  o download</h3>",
        unsafe_allow_html=True,
    )

    def convert_df(df):
        return df.to_csv(sep=";", decimal=",").encode("utf-8")

    csv = convert_df(class_metrics_df_sub)

    st.download_button(
        "Download CSV...",
        csv,
        "file.csv",
        "text/csv",
        key="download-csv",
    )
    st.markdown("---")

    st.markdown(
        "<h5>Detalhamento:</h5>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "Para maiores informações, acessar o site do [PyLandStats](https://pylandstats.readthedocs.io/en/latest/)."
    )

    metrics_names =  ['total_area', 'proportion_of_landscape', 'number_of_patches',
       'largest_patch_index', 'total_edge', 
       'landscape_shape_index',  'area_mn',  'perimeter_mn',
    'perimeter_area_ratio_mn', 'shape_index_mn','fractal_dimension_mn',  'euclidean_nearest_neighbor_mn']
    metrics_traducao = ['Área Total (ha)', 
    'Proporção da paisagem (%)', 'Número de Manchas',
    'Índice de maior mancha ', 'Total de Bordas', 'Índice de forma da paisagem',
    'Área média (ha)', 'Perímetro médio (m)', 'razão de perímetro/área média','média de índice de forma', 'Dimensão fractal média', 'Distância média para o vizinho mais próximo(m)']

    zipped = list(zip(metrics_names, metrics_traducao))

    detalhamento_df = pd.DataFrame(zipped, columns=['Item', 'Métricas'])
    st.table(detalhamento_df.set_index("Item"))

st.subheader("Referências:")
st.text("")
st.markdown("Bosch M. 2019. “PyLandStats: An open-source Pythonic library to compute landscape metrics”. PLOS ONE, 14(12), 1-19. doi.org/10.1371/journal.pone.0225734")

st.markdown(
    "Souza at. al. (2020) - Reconstructing Three Decades of Land Use and Land Cover Changes in Brazilian Biomes with Landsat Archive and Earth Engine - Remote Sensing, Volume 12, Issue 17, 10.3390/rs12172735."
)
st.markdown(
    "Wu, Q., (2020). geemap: A Python package for interactive mapping with Google Earth Engine. The Journal of Open Source Software, 5(51), 2305. https://doi.org/10.21105/joss.02305"
)
st.markdown(
    "Wu, Q., Lane, C. R., Li, X., Zhao, K., Zhou, Y., Clinton, N., DeVries, B., Golden, H. E., & Lang, M. W. (2019). Integrating LiDAR data and multi-temporal aerial imagery to map wetland inundation dynamics using Google Earth Engine. Remote Sensing of Environment, 228, 1-13. https://doi.org/10.1016/j.rse.2019.04.015 (pdf | source code)"
)

st.markdown(
    'Projeto MapBiomas - é uma iniciativa multi-institucional para gerar mapas anuais de uso e cobertura da terra a partir de processos de classificação automática aplicada a imagens de satélite. A descrição completa do projeto encontra-se em http://mapbiomas.org".'
)

st.markdown("___")
    
