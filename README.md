# 🏞️ Landscape Metrics Extractor

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://higuchip-landscapemetrics-app-fqk94t.streamlit.app/)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)


**Aplicativo Web para extração de métricas de paisagem de pontos de interesse a partir da base de dados do MapBiomas**

Desenvolvido por [Pedro Higuchi](https://twitter.com/pe_hi) | Contato: higuchip@gmail.com

---

## 📖 Descrição

O **Landscape Metrics Extractor** é uma aplicação web desenvolvida em Streamlit que permite extrair e analisar métricas de paisagem para pontos específicos no território brasileiro. A aplicação utiliza dados do MapBiomas (Collection 9) através do Google Earth Engine e calcula métricas detalhadas usando a biblioteca PyLandStats.

### 🎯 Funcionalidades Principais

- **📍 Seleção Interativa**: Interface com mapas para seleção de pontos de interesse
- **🛰️ Dados Atualizados**: Acesso aos dados mais recentes do MapBiomas (Collection 9)
- **📊 Análise Robusta**: Cálculo de 12+ métricas de paisagem diferentes
- **🔒 Segurança**: Validação completa de arquivos e autenticação segura
- **📥 Exportação**: Download dos resultados em formato CSV
- **🗺️ Visualização**: Mapas interativos e gráficos das classes de uso do solo

---

## 🚀 Demo Online

Acesse a versão online da aplicação: **[Landscape Metrics Extractor](https://higuchip-landscapemetrics-app-fqk94t.streamlit.app/)**

---

## 🛠️ Tecnologias Utilizadas

### Principais Bibliotecas

| Biblioteca | Versão | Função |
|------------|--------|---------|
| `streamlit` | 1.32.0 | Interface web |
| `geemap` | 0.30.0 | Integração Google Earth Engine |
| `pylandstats` | 3.0.0 | Cálculo de métricas de paisagem |
| `geopandas` | 0.14.3 | Processamento de dados geoespaciais |
| `earthengine-api` | 0.1.394 | API Google Earth Engine |

### Fontes de Dados

- **MapBiomas Collection 9**: Dados de uso e cobertura da terra (2023)
- **Google Earth Engine**: Plataforma de processamento geoespacial
- **Worldclim**: Dados bioclimáticos complementares

---

## 📋 Pré-requisitos

### 1. Conta Google Earth Engine
- Cadastro em: https://earthengine.google.com
- Criação de conta de serviço com permissões adequadas
- Download do arquivo JSON das credenciais

### 2. Python 3.8+
```bash
python --version  # Deve ser 3.8 ou superior
```

---

## 🔧 Instalação

### 1. Clone o Repositório
```bash
git clone https://github.com/seu-usuario/landscape-metrics-extractor.git
cd landscape-metrics-extractor
```

### 2. Crie um Ambiente Virtual
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 3. Instale as Dependências
```bash
pip install -r requirements.txt
```

### 4. Configure as Credenciais

#### Desenvolvimento Local
Crie um arquivo `.streamlit/secrets.toml`:
```toml
[secrets]
gee_service_account_credentials = '''
{
  "type": "service_account",
  "project_id": "seu-projeto-gcp",
  "private_key_id": "...",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "sua-conta-servico@seu-projeto.iam.gserviceaccount.com",
  "client_id": "...",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "..."
}
'''
```

#### Deploy no Streamlit Cloud
1. Acesse [share.streamlit.io](https://share.streamlit.io)
2. Configure o repositório
3. Adicione o segredo `gee_service_account_credentials` nas configurações

---

## 🎮 Como Usar

### 1. Inicie a Aplicação
```bash
streamlit run app.py
```

### 2. Siga o Fluxo da Interface

#### **Passo 1: Seleção do Ponto**
- Use a ferramenta "Draw a marker" no mapa
- Selecione **apenas um ponto** de interesse
- Clique em "Export" para gerar o arquivo GeoJSON

#### **Passo 2: Upload do Arquivo**
- Faça upload do arquivo GeoJSON exportado
- Limite: 10MB, apenas arquivos .geojson

#### **Passo 3: Configuração do Buffer**
- Ajuste o raio do buffer (1-10km)
- Buffer maior = área de análise maior

### 3. Visualize os Resultados
- **Mapa da área**: Visualização do buffer aplicado
- **Classes de uso**: Gráfico das classes encontradas
- **Métricas detalhadas**: Tabela com 12+ métricas
- **Download**: Arquivo CSV formatado

---

## 📊 Métricas Calculadas

| Métrica | Descrição | Unidade |
|---------|-----------|---------|
| `total_area` | Área total da classe | ha |
| `proportion_of_landscape` | Proporção na paisagem | % |
| `number_of_patches` | Número de manchas | - |
| `largest_patch_index` | Índice da maior mancha | % |
| `total_edge` | Total de bordas | m |
| `landscape_shape_index` | Índice de forma da paisagem | - |
| `area_mn` | Área média das manchas | ha |
| `perimeter_mn` | Perímetro médio | m |
| `shape_index_mn` | Índice de forma médio | - |
| `fractal_dimension_mn` | Dimensão fractal média | - |
| `euclidean_nearest_neighbor_mn` | Distância média ao vizinho mais próximo | m |

---

## 🗂️ Estrutura do Projeto

```
landscape-metrics-extractor/
├── app.py                 # Aplicação principal
├── requirements.txt       # Dependências Python
├── README.md             # Este arquivo
├── .streamlit/
│   └── secrets.toml      # Credenciais locais
├── assets/
│   ├── demo_data.geojson # Dados de exemplo
│   └── screenshots/      # Capturas de tela
└── docs/
    ├── INSTALL.md        # Guia de instalação detalhado
    └── API.md           # Documentação da API
```

---

## 🔒 Segurança

### Validações Implementadas
- ✅ **Tamanho de arquivo**: Máximo 10MB
- ✅ **Tipos permitidos**: Apenas .geojson
- ✅ **Sanitização**: Nomes de arquivo e caminhos
- ✅ **Path traversal**: Proteção contra ataques
- ✅ **Autenticação**: Credenciais via secrets

### Limites de Uso
- **Pontos por upload**: 1 ponto
- **Buffer máximo**: 10km
- **Timeout**: 60s por operação
- **Região**: Apenas território brasileiro

---

## 🌍 Classes MapBiomas Suportadas

| Código | Classe | Código | Classe |
|--------|--------|--------|--------|
| 1 | Floresta | 15 | Pastagem |
| 4 | Savana | 18 | Agricultura |
| 12 | Campo | 21 | Mosaico Agro-Pastagem |
| 26 | Água | 24 | Área Urbanizada |

*Classificação completa disponível em: [MapBiomas](https://mapbiomas.org/codigos-da-legenda)*

---

## 🐛 Solução de Problemas

### Problemas Comuns

#### 1. Erro de Autenticação Earth Engine
```
❌ Falha na inicialização do Earth Engine
```
**Solução**: Verifique se as credenciais estão corretas e a conta de serviço tem permissões para Earth Engine.

#### 2. Arquivo GeoJSON Inválido
```
❌ Nenhuma geometria válida encontrada
```
**Solução**: Certifique-se de que o arquivo contém exatamente um ponto válido.

#### 3. Região Sem Dados
```
⚠️ Usando dados representativos da região
```
**Solução**: Normal para algumas regiões. O sistema usa dados típicos da área.

### Logs e Debug

Para ativar logs detalhados:
```bash
streamlit run app.py --logger.level=debug
```

---

## 🤝 Contribuindo

### Como Contribuir
1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-funcionalidade`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/nova-funcionalidade`)
5. Abra um Pull Request

### Diretrizes
- Siga o padrão PEP 8 para Python
- Adicione testes para novas funcionalidades
- Atualize a documentação quando necessário
- Mantenha compatibilidade com Python 3.8+

---

## 📄 Licença

Este projeto está licenciado sob a Licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

## 📚 Referências

### Artigos Científicos
- **Bosch M.** (2019). PyLandStats: An open-source Pythonic library to compute landscape metrics. *PLOS ONE*, 14(12), 1-19.
- **Souza et al.** (2020). Reconstructing Three Decades of Land Use and Land Cover Changes in Brazilian Biomes with Landsat Archive and Earth Engine. *Remote Sensing*, 12(17).

### Ferramentas e Dados
- [MapBiomas](https://mapbiomas.org/) - Mapeamento anual da cobertura e uso da terra do Brasil
- [Google Earth Engine](https://earthengine.google.com/) - Plataforma de análise geoespacial
- [PyLandStats](https://pylandstats.readthedocs.io/) - Biblioteca para métricas de paisagem
- [Streamlit](https://streamlit.io/) - Framework para aplicações web em Python

---

## 👨‍💻 Autor

**Pedro Higuchi**
- Twitter: [@pe_hi](https://twitter.com/pe_hi)
- Email: higuchip@gmail.com
- GitHub: [Seu GitHub](https://github.com/seu-usuario)

---

## 🆘 Suporte

Para suporte, abra uma [issue](https://github.com/seu-usuario/landscape-metrics-extractor/issues) ou entre em contato via email.

### Links Úteis
- [Documentação Streamlit](https://docs.streamlit.io/)
- [Google Earth Engine Docs](https://developers.google.com/earth-engine/)
- [PyLandStats Docs](https://pylandstats.readthedocs.io/)
- [MapBiomas Docs](https://mapbiomas.org/downloads)

---

**⭐ Se este projeto foi útil, considere dar uma estrela no GitHub!**
