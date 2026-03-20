# 🌾 Agricultural Structural Exposure Knowledge Graph

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![RDFLib](https://img.shields.io/badge/rdflib-7.x-green.svg)](https://rdflib.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Knowledge Graph (KG) project that integrates multi-source agricultural data — crop production, commodity prices, climate anomalies, and gross production values — into a unified RDF graph and answers five structural exposure research questions via SPARQL.

---

## 🏗️ Architecture

```
Raw Data (CSV / XLSX)
        │
        ▼
┌─────────────────────────────┐
│  00 – Prepare FAO crop data │  FAOSTAT → faostat_crop_observations_clean.csv
│  01 – Prepare annual prices │  World Bank CMO → annual_prices_clean.csv
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  02 – Build RDF             │  CSV + OWL ontology → modular Turtle files
│       entities.ttl          │  Countries & commodities
│       crop_observations.ttl │  Production / Yield / Area harvested
│       prices.ttl            │  Global commodity prices
│       climate.ttl           │  Precipitation anomalies
│       gross_value.ttl       │  Gross production values
│       agri_kg.ttl           │  Merged KG
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  SPARQL Queries (RQ1–RQ5)   │  Answered via GraphDB / Apache Jena
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  05 – Visualisation         │  Matplotlib / Seaborn figures
└─────────────────────────────┘
```

---

## 📊 Research Questions

| ID   | Question |
|------|----------|
| RQ1  | Which country-commodity pairs show the highest structural dependency shares? |
| RQ1b | What is the average dependency share by country and commodity (2000–2020)? |
| RQ2  | When do compound shocks occur (low production + high global price)? |
| RQ3  | How do precipitation anomalies correlate with wheat and rice production? |
| RQ4  | Which commodities exhibit the highest price volatility over 2000–2020? |
| RQ5  | How do structural exposure profiles compare across similar economies? |

---

## 🗂️ Project Structure

```
agri_kg_project/
├── scripts/
│   ├── 00_prepare_fao_crop_data.py   # Clean FAOSTAT crop data
│   ├── 01_prepare_annual_prices.py   # Clean World Bank price data
│   ├── 02_build_rdf.py               # Build RDF KG from cleaned CSVs
│   └── 05_visualization.py           # Generate RQ figures
├── data/
│   ├── raw/                          # Original source files (not tracked)
│   └── processed/                    # Cleaned CSV outputs
├── ontology/
│   └── agri_ontology.ttl             # OWL ontology (AGRI namespace)
├── rdf/                              # Generated Turtle files
├── queries/
│   └── Results/                      # SPARQL query result CSVs
│       ├── RQ1/ RQ1b/ RQ2/ RQ3/ RQ4/ RQ5/
├── figures/                          # Generated PNG visualisations
└── requirements.txt
```

---

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/denizkaya20/agri-knowledge-graph.git
cd agri-knowledge-graph

# 2. Install dependencies
pip install -r requirements.txt

# 3. Place raw files in data/raw/
#    - FAOSTAT_data_en_3-8-2026.csv
#    - CMO-Historical-Data-Annual.xlsx

# 4. Run preprocessing
python scripts/00_prepare_fao_crop_data.py
python scripts/01_prepare_annual_prices.py

# 5. Build the Knowledge Graph
python scripts/02_build_rdf.py

# 6. Load rdf/agri_kg.ttl into GraphDB or Apache Jena
#    and run SPARQL queries → save results to queries/Results/

# 7. Generate figures
python scripts/05_visualization.py
```

---

## 🌍 Data Sources

| Dataset | Source | Coverage |
|---------|--------|----------|
| Crop production / yield / area | [FAOSTAT](https://www.fao.org/faostat/) | 10 countries, 5 crops, 2000–2022 |
| Commodity prices (real) | [World Bank CMO](https://www.worldbank.org/en/research/commodity-markets) | 5 crops, 1960–2023 |
| Precipitation anomaly | Climate research dataset | 10 countries, 2000–2020 |
| Gross production value | FAOSTAT | 10 countries, 2000–2020 |

**Countries:** Brazil, China, Egypt, France, India, Italy, Spain, Turkey, Ukraine, United States

**Crops:** Barley, Maize, Rice, Soybeans, Wheat

---

## 🔒 Data Privacy

All datasets used in this project are publicly available from official international sources (FAO, World Bank). No personal data is present in any file.

---

## 📝 License

MIT License — see [LICENSE](LICENSE).
