# Blockchain abierto y estabilidad de plataformas DeFi
## Evidencia cuantitativa sobre volatilidad, liquidez y sentimiento de mercado

**Autor:** Andrade Cuadra, José Manuel  
**Institución:** Instituto de Estudios Superiores de Administración (IESA)  
**Publicación:** Capítulo de libro — *Volumen conmemorativo 50 aniversario del Doctorado en Ciencias Económicas*, Universidad Católica Andrés Bello (UCAB), Caracas, Venezuela, 2026.  
**Editor:** Luis Morales, Director del Doctorado en Ciencias Económicas, UCAB.

---

## Descripción

Este repositorio contiene el pipeline completo de adquisición, procesamiento y análisis econométrico utilizado en la investigación empírica del artículo. El trabajo examina la estabilidad de las plataformas de finanzas descentralizadas (DeFi) sobre blockchain abierto durante el período 2020–2025, mediante la integración de 2.192 observaciones diarias de liquidez on-chain, precios de activos, variables macroeconómicas y sentimiento de mercado.

---

## Estructura del repositorio

```
defi-stability-research/
│
├── data/
│   ├── raw/                    # Datos descargados directamente de las fuentes
│   ├── interim/                # Datos en procesamiento intermedio
│   └── processed/              # Panel maestro listo para análisis
│
├── src/
│   ├── ingestion/              # Scripts de descarga de datos
│   │   ├── credentials.py      # Gestión de credenciales (.env)
│   │   ├── fetch_fred.py       # VIX, Fed Funds Rate, DXY desde FRED
│   │   ├── fetch_defillama.py  # TVL total, Uniswap, Aave desde DeFiLlama
│   │   ├── fetch_binance.py    # ETH/USD, BTC/USD, USDC/USDT desde Binance
│   │   ├── fetch_coingecko.py  # Precios de stablecoins
│   │   └── fetch_sentiment.py  # Índice Miedo y Codicia, Google Trends
│   │
│   ├── processing/             # Scripts de transformación y feature engineering
│   │   ├── merge_panel.py      # Integración de todas las series en panel diario
│   │   └── compute_features.py # Retornos, volatilidad, eventos, sentimiento
│   │
│   └── modeling/               # Scripts de análisis econométrico
│       ├── descriptive_stats.py    # Tabla 1: estadísticas descriptivas + Jarque-Bera
│       ├── correlation_matrix.py   # Tabla 2: matriz de correlaciones de Pearson
│       ├── garch_model.py          # Tabla 3: estimación GARCH(1,1) ETH y BTC
│       ├── event_study.py          # Tabla 4: estudio de eventos LUNA/FTX/SVB
│       ├── lead_lag_sentiment.py   # Tabla 5: correlación cruzada con desfase temporal
│       └── regression_sentiment.py # Tabla 6: regresión OLS con errores HAC
│
├── scripts/
│   ├── run_ingestion.py        # Ejecuta pipeline completo de descarga
│   ├── run_processing.py       # Ejecuta pipeline de procesamiento
│   └── run_analysis.py         # Ejecuta todos los módulos de análisis
│
├── outputs/
│   └── tables/                 # CSVs con resultados de todos los análisis
│
├── powerbi/
│   └── datasets/               # Tablas exportadas para Power BI
│
├── .env.example                # Plantilla de credenciales (sin claves reales)
├── requirements.txt            # Dependencias Python
└── README.md                   # Este documento
```

---

## Fuentes de datos

| Fuente | Variable | Frecuencia | Acceso |
|--------|----------|------------|--------|
| Binance API v3 | ETH/USD, BTC/USD OHLCV | Diaria | Público, sin clave |
| Binance API v3 | USDC/USDT precio | Diaria | Público, sin clave |
| DeFiLlama API | TVL total DeFi, Uniswap, Aave | Diaria | Público, sin clave |
| FRED (St. Louis Fed) | VIX (VIXCLS), Fed Funds Rate, DXY | Diaria/mensual | Clave gratuita |
| Alternative.me | Índice de Miedo y Codicia | Diaria | Público, sin clave |
| Google Trends (pytrends) | DeFi, crypto crash, Ethereum | Semanal | Público, sin clave |

---

## Requisitos

### Python

```
Python >= 3.11
arch >= 8.0.0
statsmodels >= 0.14.0
pandas >= 2.0.0
numpy >= 1.26.0
requests >= 2.31.0
scipy >= 1.11.0
pytrends >= 4.9.0
python-dotenv >= 1.0.0
```

Instalar dependencias:

```bash
pip install arch statsmodels pandas numpy requests scipy pytrends python-dotenv
```

> **Nota:** El pipeline completo fue probado en Python 3.11 y 3.13.

### R

El análisis de robustez y las visualizaciones complementarias se realizaron en R. Las bibliotecas principales empleadas son:

```r
install.packages(c("quantmod", "rugarch", "PerformanceAnalytics",
                   "tidyverse", "lubridate", "ggplot2"))
```

---

## Configuración de credenciales

Copiar `.env.example` a `.env` y completar las claves:

```bash
cp .env.example .env
```

El archivo `.env` contiene:

```
FRED_API_KEY=your_key_here      # https://fred.stlouisfed.org/docs/api/api_key.html
```

El archivo `.env` **nunca** debe subirse al repositorio. Está incluido en `.gitignore`.

---

## Procedimiento de reproducción

> **Requisito previo:** Clonar el repositorio y situarse dentro de la carpeta raíz antes de ejecutar cualquier script.
>
> ```bash
> git clone https://github.com/jmandradecuadra/defi-stability-research.git
> cd defi-stability-research
> ```

### Paso 1 — Descarga de datos

```bash
PYTHONPATH=. python scripts/run_ingestion.py
```

Tiempo estimado: 3–5 minutos. Genera 11 archivos CSV en `data/raw/`.

### Paso 2 — Procesamiento

```bash
PYTHONPATH=. python scripts/run_processing.py
```

Tiempo estimado: < 5 segundos. Genera:

- `data/processed/master_panel.csv` — panel de 2.192 × 22 variables
- `data/processed/master_panel_features.csv` — panel de 2.192 × 42 variables con todas las variables derivadas
- 4 tablas exportadas a `outputs/tables/` y `powerbi/datasets/`

### Paso 3 — Análisis econométrico

```bash
PYTHONPATH=. python scripts/run_analysis.py
```

Tiempo estimado: 3–5 segundos. Genera las Tablas 1 a 6 del artículo en `outputs/tables/`:

| Archivo | Contenido | Tabla en artículo |
|---------|-----------|-------------------|
| `table1_descriptive_stats.csv` | Estadísticas descriptivas + Jarque-Bera | Tabla 1 |
| `table2_correlation_matrix.csv` | Matriz de correlaciones de Pearson | Tabla 2 |
| `table2_pvalues.csv` | Valores p para la matriz de correlaciones | Tabla 2 |
| `table3_garch_results.csv` | Parámetros GARCH(1,1) ETH y BTC | Tabla 3 |
| `table4_event_study_summary.csv` | Métricas pre/post evento sistémico | Tabla 4 |
| `table5_lead_lag_sentiment.csv` | Correlaciones cruzadas con desfase | Tabla 5 |
| `table6_regression_coefficients.csv` | Coeficientes OLS con errores HAC | Tabla 6 |
| `table6_regression_diagnostics.csv` | Métricas de ajuste del modelo | Tabla 6 |
| `regression_residuals.csv` | Residuos para diagnóstico | — |
| `event_study_windows.csv` | Datos completos por ventana de evento | — |

---

## Descripción del pipeline

### Ingestion layer (`src/ingestion/`)

Cada script de ingesta es independiente y puede ejecutarse de forma aislada. El módulo `credentials.py` carga las claves desde `.env` y valida su presencia antes de cualquier llamada a fuente de datos. Las fuentes sin clave (DeFiLlama, Binance, Fear & Greed, Google Trends) se acceden directamente. Las fuentes con clave gratuita (FRED) requieren registro previo. El script `run_ingestion.py` orquesta todos los módulos en secuencia y ejecuta validación de outputs al finalizar.

### Processing layer (`src/processing/`)

`merge_panel.py` construye la espina diaria del panel (2020-01-01 a 2025-12-31) y une todas las series mediante left join sobre la fecha, aplicando forward-fill a las series de frecuencia mensual (FEDFUNDS) y semanal (Google Trends). `compute_features.py` deriva todas las variables de segundo orden: retornos logarítmicos, volatilidad rodante a 30 días anualizada, drawdown del TVL respecto al máximo de 90 días, variables binarias de evento para los tres choques sistémicos, episodios de de-peg de USDC, e índice de sentimiento compuesto.

### Modeling layer (`src/modeling/`)

Cada script de análisis lee `master_panel_features.csv` de forma independiente y exporta sus resultados como CSV numerados conforme a las tablas del artículo. El modelo GARCH(1,1) se estima mediante la biblioteca `arch` de Python con distribución normal y sin reescalado automático (los retornos se escalan manualmente al porcentaje para garantizar la estabilidad numérica del optimizador). La regresión OLS emplea `statsmodels` con `cov_type='HAC'` y selección automática del ancho de banda de Newey-West.

---

## Decisiones metodológicas documentadas

| Decisión | Justificación |
|----------|---------------|
| Frecuencia diaria en lugar de intradiaria | Disponibilidad homogénea de todas las fuentes en frecuencia diaria. Las series FRED son diarias o mensuales. |
| Forward-fill para FEDFUNDS y Google Trends | La tasa de política monetaria y las tendencias de búsqueda son variables de estado que no varían entre observaciones de la misma frecuencia más lenta. |
| USDC como única stablecoin | USDT no tiene un par USD limpio disponible en Binance con cobertura histórica completa desde 2020. USDC es la stablecoin analíticamente más relevante dado el episodio SVB. |
| HAC en lugar de errores estándar convencionales | El estadístico de Durbin-Watson (1,759) y la naturaleza de series de tiempo del panel justifican la corrección ante autocorrelación y heterocedasticidad de forma desconocida. |
| Ventana de evento ±30 días | Período suficiente para capturar efectos de anticipación y propagación, sin solapamiento entre los eventos LUNA (mayo 2022) y FTX (noviembre 2022). |
| Comparación por promedios de período en estudios de eventos | Los porcentajes de variación del TVL comparan promedios de 30 días antes y después del evento, no valores pico a valle, produciendo estimaciones más conservadoras que las cifras absolutas citadas en fuentes de la industria. |

---

## Limitaciones conocidas

- El período muestral (2020–2025) comprende dos regímenes de volatilidad extrema —el ciclo alcista de 2021 y la secuencia de colapsos de 2022— lo que influye en la magnitud de la persistencia GARCH estimada (α+β=0,986). Estudios con ventanas más acotadas o períodos de menor estrés típicamente reportan valores en el rango 0,97–0,98.
- La serie DXY (DTWEXBGS) de FRED presenta cobertura incompleta en los primeros meses de 2020, lo que reduce el número de observaciones válidas en la regresión OLS (N=1.163 sobre 2.192 observaciones totales del panel).
- El análisis se limita a datos de frecuencia diaria. Extensiones con datos intradiarios o de alta frecuencia para pruebas de varianza ratio y análisis de microestructura quedan para trabajo futuro.

---

## Citación

Si utiliza el código o los datos procesados de este repositorio, por favor cite:

```
Andrade Cuadra, J. M. (2026). Blockchain abierto y estabilidad de plataformas DeFi:
evidencia cuantitativa sobre volatilidad, liquidez y sentimiento de mercado.
En L. Morales (Ed.), [Título del volumen — confirmar con editor].
Universidad Católica Andrés Bello.
```

---

## Licencia

El código de este repositorio se publica bajo licencia MIT. Los datos descargados de fuentes externas están sujetos a los términos de uso de cada proveedor.

---

## Contacto

José Manuel Andrade Cuadra  
jose.andrade@iesa.edu.ve  
Instituto de Estudios Superiores de Administración (IESA), Caracas, Venezuela
