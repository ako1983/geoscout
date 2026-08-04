

# GeoScout 🛰️

Plataforma de exploración mineral impulsada por IA que utiliza imágenes satelitales de Sentinel-2, agentes de LangGraph y Claude AI.

## Descripción general

GeoScout analiza imágenes satelitales de tres importantes yacimientos de exploración mineral:

1. **Mountain Pass, CA** - Elementos de Tierras Raras (ETR) en carbonatita
2. **Bingham Canyon, UT** - Yacimiento porfírico de cobre-molibdeno-oro-plata
3. **Bokan Mountain, AK** - ETR y uranio en granito peralcalino

## Características

- 📡 **Acceso a datos satelitales** - Servidor MCP para imágenes de Sentinel-2
- 🤖 **Agente de IA** - Agente de LangGraph impulsado por Claude para análisis inteligente
- 📊 **Índices minerales** - Cálculo de índices de óxidos de hierro, arcilla, ferrosos y vegetación
- 🗺️ **Interfaz interactiva** - Aplicación web de Streamlit con mapas y visualizaciones
- 🔬 **Análisis de alteración** - Identificación de zonas de alteración hidrotermal

## Arquitectura

```
geoscout/
├── mcp_server/
│   └── server.py           # MCP server exposing satellite data tools
├── agent/
│   └── mineral_agent.py    # LangGraph agent with Claude AI
├── ui/
│   └── app.py              # Streamlit web interface
└── data/
    └── (Sentinel-2 GeoTIFF files)
```

## Instalación

### 1. Requisitos previos

- Python 3.8+
- Clave API de Anthropic (para Claude)
- Cuenta de Google Earth Engine (para descargar imágenes)

### 2. Instalar dependencias

```bash
pip install earthengine-api geemap mcp langgraph langchain-anthropic streamlit folium streamlit-folium rasterio
```

### 3. Configurar variables de entorno

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

## Uso

### Paso 1: Descargar imágenes satelitales

Primero, registra tu proyecto de Google Cloud en Earth Engine:
1. Visita: https://console.cloud.google.com/earth-engine/configuration?project=gen-lang-client-0926459788
2. Registra el proyecto para obtener acceso a Earth Engine

Luego descarga las imágenes:

```bash
python download_sentinel2.py
```

Esto descarga escenas de Sentinel-2 (bandas 2,3,4,8,11,12) para los tres yacimientos en `geoscout/data/`.

### Paso 2: Ejecutar la interfaz de Streamlit

```bash
cd geoscout/ui
streamlit run app.py
```

La interfaz web se abrirá en `http://localhost:8501`

### Paso 3: Usar el servidor MCP (Opcional)

El servidor MCP se puede ejecutar de forma independiente para acceso programático:

```bash
cd geoscout/mcp_server
python server.py
```

### Paso 4: Usar el agente de IA (CLI)

Ejecuta el agente desde la línea de comandos:

```bash
cd geoscout/agent
python mineral_agent.py "Analyze Mountain Pass, CA for rare earth minerals"
```

## Características de la interfaz de Streamlit

### 1. Vista del mapa
- Mapa interactivo que muestra los tres yacimientos de exploración
- Haz clic en los marcadores para ver los detalles del sitio
- Visualiza coordenadas, geología y minerales objetivo

### 2. Índices minerales
- Calcula índices espectrales a partir de las bandas de Sentinel-2:
  - **Índice de óxidos de hierro** (Rojo/Azul): Minerales oxidados, gossans
  - **Índice ferroso** (SWIR1/NIR): Minerales que contienen hierro
  - **Índice de arcilla** (SWIR1/SWIR2): Alteración hidrotermal
  - **NDVI**: Cobertura de vegetación
- Consulta resúmenes estadísticos y visualizaciones

### 3. Zonas de alteración
- Identifica zonas de alteración hidrotermal
- Calcula porcentajes de cobertura
- Obtén recomendaciones de exploración
- Encuentra zonas de superposición de múltiples alteraciones (objetivos de alta prioridad)

### 4. Chat de IA
- Haz preguntas en lenguaje natural sobre los yacimientos
- Obtén análisis inteligente de Claude
- Ejemplos:
  - "¿Qué índices minerales debería calcular para este sitio?"
  - "Analiza los patrones de alteración en Bingham Canyon"
  - "Compara las firmas espectrales entre diferentes zonas"

## Herramientas del servidor MCP

El servidor MCP expone tres herramientas:

### 1. `get_sites`
Devuelve información sobre todos los yacimientos disponibles, incluidas coordenadas, minerales y disponibilidad de datos.

### 2. `get_image`
Obtén imágenes satelitales con opciones de visualización:
- `rgb` - Color natural
- `false_color` - Composición NIR-Rojo-Verde
- `iron_oxide` - Composición de óxidos de hierro
- `ferrous` - Composición de minerales ferrosos
- `clay` - Composición de alteración de arcilla

### 3. `calculate_mineral_index`
Calcula índices espectrales:
- `iron_oxide` - Minerales de óxidos de hierro
- `ferrous` - Minerales ferrosos
- `clay` - Alteración de arcilla
- `vegetation` - NDVI

## Herramientas del agente de LangGraph

El agente cuenta con cuatro herramientas:

1. **`get_available_sites()`** - Listar todos los yacimientos con detalles
2. **`calculate_mineral_indices(site_key)`** - Calcular todos los índices para un yacimiento
3. **`get_spectral_signature(site_key, percentile)`** - Extraer firmas de píxeles brillantes
4. **`analyze_alteration_zones(site_key)`** - Análisis integral de alteración

## Bandas de Sentinel-2 utilizadas

| Banda | Longitud de onda | Resolución | Propósito |
|------|------------|------------|---------|
| B2   | 490 nm (Blue) | 10m | Índice de óxidos de hierro, minerales arcillosos |
| B3   | 560 nm (Green) | 10m | Vegetación, visualización RGB |
| B4   | 665 nm (Red) | 10m | Óxidos de hierro, visualización RGB |
| B8   | 842 nm (NIR) | 10m | Vegetación, minerales ferrosos |
| B11  | 1610 nm (SWIR1) | 20m | Arcilla, minerales hidroxilos |
| B12  | 2190 nm (SWIR2) | 20m | Arcilla, minerales carbonatados |

## Interpretación de índices minerales

### Índice de óxidos de hierro (Rojo/Azul)
- **Alto (>1.5)**: Oxidación fuerte, gossans, limonita
- **Moderado (1.2-1.5)**: Oxidación parcial
- **Bajo (<1.2)**: Oxidación mínima

### Índice de alteración de arcilla (SWIR1/SWIR2)
- **Alto (>1.2)**: Alteración hidrotermal fuerte (filica/arcílica)
- **Moderado (1.0-1.2)**: Alteración moderada
- **Bajo (<1.0)**: Alteración mínima

### Índice ferroso (SWIR1/NIR)
- **Alto (>1.1)**: Minerales con hierro (magnetita, piroxeno)
- Útil para complejos máficos/ultramáficos

## Ejemplos de flujos de trabajo

### Flujo 1: Evaluación inicial del yacimiento

```bash
# 1. Download imagery
python download_sentinel2.py

# 2. Launch UI
cd geoscout/ui
streamlit run app.py

# 3. In UI:
#    - View site on map
#    - Calculate mineral indices
#    - Review statistics
```

### Flujo 2: Análisis detallado de exploración

```bash
# 1. Use AI agent for comprehensive analysis
cd geoscout/agent
python mineral_agent.py "Perform complete exploration analysis for Bingham Canyon including alteration zones and spectral signatures"

# 2. Review results and identify targets
# 3. Use UI to visualize specific indices
```

### Flujo 3: Análisis comparativo

```bash
# Use AI chat in Streamlit UI:
# "Compare iron oxide signatures across all three sites"
# "Which site shows the strongest hydrothermal alteration?"
# "Recommend priority targets for ground surveys"
```

## Solución de problemas

### Error de registro de Earth Engine

Si aparece: `Project is not registered to use Earth Engine`

**Solución:**
1. Visita la URL de registro en el mensaje de error
2. Registra tu proyecto para obtener acceso a Earth Engine
3. Espera unos minutos a que se complete el registro
4. Vuelve a ejecutar `download_sentinel2.py`

### Datos satelitales faltantes

Si la interfaz muestra "No data available":

**Solución:**
1. Asegúrate de haber ejecutado `download_sentinel2.py` correctamente
2. Verifica que los archivos GeoTIFF existan en `geoscout/data/`
3. Comprueba que los archivos tengan el formato: `{site_key}_sentinel2.tif`

### Clave API no encontrada

Si aparecen advertencias sobre `ANTHROPIC_API_KEY`:

**Solución:**
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

O ingresa la clave en la barra lateral de Streamlit.

## Detalles de los yacimientos

### Mountain Pass, California
- **Coordenadas:** 35.4881°N, 115.5408°W
- **Tipo de yacimiento:** ETR en carbonatita
- **Minerales clave:** Bastnásita (fluorocarbonato de ETR)
- **Geología:** Intrusión de carbonatita proterozoica
- **Enfoque de exploración:** Firmas de óxidos de hierro + ETR

### Bingham Canyon, Utah
- **Coordenadas:** 40.5231°N, 112.1500°W
- **Tipo de yacimiento:** Porfírico de Cu-Mo-Au-Ag
- **Minerales clave:** Calcopirita, molibdenita, oro nativo
- **Geología:** Porfírico de monzonita cuarzosa terciaria
- **Enfoque de exploración:** Alteración zonada (núcleo potásico, halo filico)

### Bokan Mountain, Alaska
- **Coordenadas:** 54.8867°N, 132.1583°W
- **Tipo de yacimiento:** ETR-U en granito peralcalino
- **Minerales clave:** Minerales de ETR, uraninita
- **Geología:** Granito peralcalino jurásico
- **Enfoque de exploración:** Óxidos de hierro + anomalías SWIR

## Notas técnicas

### Procesamiento de datos
- Todos los índices utilizan épsilon (1e-10) para evitar división por cero
- Estiramiento percentil (2-98%) para visualización
- El análisis estadístico utiliza solo píxeles válidos (excluye NaN/Inf)

### Rendimiento
- El procesamiento de imágenes se realiza en memoria con NumPy
- Los archivos GeoTIFF son de ~50-100 MB por yacimiento
- Las respuestas del agente suelen tardar entre 2 y 10 segundos

### Sistemas de coordenadas
- Coordenadas de entrada: WGS84 (EPSG:4326)
- Archivos GeoTIFF: WGS84 (EPSG:4326)
- Nativo de Sentinel-2: UTM (convertido durante la descarga)

## Referencias

- Sentinel-2 Mission: https://sentinel.esa.int/web/sentinel/missions/sentinel-2
- Mineral Indices: https://www.usgs.gov/spectroscopy-lab
- LangGraph: https://langchain-ai.github.io/langgraph/
- MCP Protocol: https://modelcontextprotocol.io/

## Licencia

Este proyecto es con fines educativos y de investigación.
Datos de Sentinel-2 cortesía del Programa Copérnico de la ESA.

## Contribuciones

¡Se aceptan contribuciones! Áreas para mejorar:
- Índices minerales adicionales (ASTER, Landsat)
- Clasificación con aprendizaje automático
- Análisis de series temporales
- Capacidades de exportación (KML, shapefile)
- Integración con bases de datos geológicas

## Contacto

Desarrollado con Claude Code y la IA Claude de Anthropic.
