"""
02_build_rdf.py
---------------
Converts cleaned CSV datasets into a modular RDF Knowledge Graph (Turtle format).

Inputs  (data/processed/)
--------------------------
- faostat_crop_observations_clean.csv
- annual_prices_clean.csv
- global_precipitation_anomaly_clean.csv
- gross_production_value_clean.csv

Outputs (rdf/)
--------------
- entities.ttl              Country and commodity nodes
- crop_observations.ttl     Production / Yield / Area harvested observations
- prices.ttl                Global commodity price observations
- climate.ttl               Annual precipitation anomaly observations
- gross_value.ttl           Gross production value observations
- agri_kg.ttl               Merged KG (ontology + all instance graphs)

Ontology namespace: http://example.org/agri/
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL, XSD, DCTERMS

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR     = Path(__file__).resolve().parents[1]
DATA_DIR     = ROOT_DIR / "data" / "processed"
ONTOLOGY_PATH = ROOT_DIR / "ontology" / "agri_ontology.ttl"
RDF_DIR      = ROOT_DIR / "rdf"

FAO_PATH     = DATA_DIR / "faostat_crop_observations_clean.csv"
PRICES_PATH  = DATA_DIR / "annual_prices_clean.csv"
CLIMATE_PATH = DATA_DIR / "global_precipitation_anomaly_clean.csv"
GROSS_PATH   = DATA_DIR / "gross_production_value_clean.csv"

# ---------------------------------------------------------------------------
# Namespaces
# ---------------------------------------------------------------------------
AGRI = Namespace("http://example.org/agri/")
SKOS = Namespace("http://www.w3.org/2004/02/skos/core#")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def bind_prefixes(graph: Graph) -> None:
    """Bind all standard namespace prefixes to *graph*."""
    graph.bind("agri",    AGRI)
    graph.bind("rdf",     RDF)
    graph.bind("rdfs",    RDFS)
    graph.bind("owl",     OWL)
    graph.bind("xsd",     XSD)
    graph.bind("dcterms", DCTERMS)
    graph.bind("skos",    SKOS)


def drop_index_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove accidental index columns left by pandas serialisation."""
    return df.drop(columns=[c for c in ("index", "Unnamed: 0") if c in df.columns])


def slugify(text: str) -> str:
    """Convert a label to a URL-safe slug."""
    return str(text).strip().lower().replace(" ", "-")


def to_decimal_literal(value: float) -> Literal:
    """
    Return an ``xsd:decimal`` literal for *value*.

    Passing the value as a string forces rdflib to annotate it with
    ``xsd:decimal`` rather than ``xsd:double``.
    """
    return Literal(str(round(float(value), 10)), datatype=XSD.decimal)


# ---------------------------------------------------------------------------
# URI factories
# ---------------------------------------------------------------------------

def country_uri(code: str) -> URIRef:
    return URIRef(f"http://example.org/agri/country/{code}")

def commodity_uri(crop: str) -> URIRef:
    return URIRef(f"http://example.org/agri/commodity/{slugify(crop)}")

def production_obs_uri(code: str, crop: str, year: int) -> URIRef:
    return URIRef(f"http://example.org/agri/observation/production/{code}/{slugify(crop)}/{year}")

def yield_obs_uri(code: str, crop: str, year: int) -> URIRef:
    return URIRef(f"http://example.org/agri/observation/yield/{code}/{slugify(crop)}/{year}")

def harvested_area_obs_uri(code: str, crop: str, year: int) -> URIRef:
    return URIRef(f"http://example.org/agri/observation/harvested-area/{code}/{slugify(crop)}/{year}")

def price_obs_uri(crop: str, year: int) -> URIRef:
    return URIRef(f"http://example.org/agri/observation/price/{slugify(crop)}/{year}")

def climate_obs_uri(code: str, year: int) -> URIRef:
    return URIRef(f"http://example.org/agri/observation/climate/{code}/{year}")

def gross_value_obs_uri(code: str, year: int) -> URIRef:
    return URIRef(f"http://example.org/agri/observation/gross-production-value/{code}/{year}")


# ---------------------------------------------------------------------------
# Entity builders
# ---------------------------------------------------------------------------

def add_country(graph: Graph, label: str, code: str, m49=None) -> URIRef:
    uri = country_uri(code)
    graph.add((uri, RDF.type,      AGRI.Country))
    graph.add((uri, RDFS.label,    Literal(label, lang="en")))
    graph.add((uri, AGRI.iso3Code, Literal(code, datatype=XSD.string)))
    if m49 is not None and pd.notna(m49):
        graph.add((uri, AGRI.m49Code, Literal(int(m49), datatype=XSD.integer)))
    return uri


def add_commodity(graph: Graph, crop: str) -> URIRef:
    uri = commodity_uri(crop)
    graph.add((uri, RDF.type,   AGRI.Commodity))
    graph.add((uri, RDFS.label, Literal(crop, lang="en")))
    return uri


def merge_graphs(target: Graph, source: Graph) -> None:
    """Copy all triples from *source* into *target*."""
    for triple in source:
        target.add(triple)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    RDF_DIR.mkdir(parents=True, exist_ok=True)

    for path in [FAO_PATH, PRICES_PATH, CLIMATE_PATH, GROSS_PATH, ONTOLOGY_PATH]:
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    fao_df     = drop_index_columns(pd.read_csv(FAO_PATH))
    prices_df  = drop_index_columns(pd.read_csv(PRICES_PATH))
    climate_df = drop_index_columns(pd.read_csv(CLIMATE_PATH))
    gross_df   = drop_index_columns(pd.read_csv(GROSS_PATH))

    # Initialise sub-graphs
    entities_g = Graph()
    crop_g     = Graph()
    prices_g   = Graph()
    climate_g  = Graph()
    gross_g    = Graph()
    merged_g   = Graph()

    for graph in (entities_g, crop_g, prices_g, climate_g, gross_g, merged_g):
        bind_prefixes(graph)

    # ------------------------------------------------------------------
    # Countries
    # ------------------------------------------------------------------
    countries: dict[str, dict] = {}

    for _, row in fao_df[["Entity", "Code", "M49"]].drop_duplicates().iterrows():
        countries[row["Code"]] = {"label": row["Entity"], "m49": row["M49"]}

    for _, row in climate_df[["Entity", "Code"]].drop_duplicates().iterrows():
        countries.setdefault(row["Code"], {"label": row["Entity"], "m49": None})

    for _, row in gross_df[["Entity", "Code"]].drop_duplicates().iterrows():
        countries.setdefault(row["Code"], {"label": row["Entity"], "m49": None})

    for code, meta in sorted(countries.items()):
        add_country(entities_g, meta["label"], code, meta["m49"])

    # ------------------------------------------------------------------
    # Commodities
    # ------------------------------------------------------------------
    all_crops = (
        set(fao_df["Crop"].dropna().unique())
        | set(prices_df["Crop"].dropna().unique())
    )
    for crop in sorted(all_crops):
        add_commodity(entities_g, crop)

    # ------------------------------------------------------------------
    # Crop observations (FAO)
    # ------------------------------------------------------------------
    _obs_class_map = {
        "Production":     (production_obs_uri,    AGRI.ProductionObservation),
        "Yield":          (yield_obs_uri,          AGRI.YieldObservation),
        "Area harvested": (harvested_area_obs_uri, AGRI.HarvestedAreaObservation),
    }

    for _, row in fao_df.iterrows():
        code    = str(row["Code"])
        crop    = str(row["Crop"])
        year    = int(row["Year"])
        element = str(row["Element"])

        if element not in _obs_class_map:
            continue

        uri_fn, obs_class = _obs_class_map[element]
        uri = uri_fn(code, crop, year)

        crop_g.add((uri, RDF.type,          obs_class))
        crop_g.add((uri, AGRI.refCountry,   country_uri(code)))
        crop_g.add((uri, AGRI.refCommodity, commodity_uri(crop)))
        crop_g.add((uri, AGRI.refYear,      Literal(str(year), datatype=XSD.gYear)))
        crop_g.add((uri, AGRI.numericValue, to_decimal_literal(row["Value"])))
        crop_g.add((uri, AGRI.unit,         Literal(str(row["Unit"]), datatype=XSD.string)))
        crop_g.add((uri, DCTERMS.source,    AGRI["dataset-faostat-crops"]))

        for prop, col in [
            (AGRI.hasFlag,        "Flag"),
            (AGRI.flagDescription, "FlagDescription"),
            (AGRI.note,            "Note"),
        ]:
            val = str(row.get(col, ""))
            if val:
                crop_g.add((uri, prop, Literal(val, datatype=XSD.string)))

    # ------------------------------------------------------------------
    # Price observations
    # ------------------------------------------------------------------
    for _, row in prices_df.iterrows():
        crop = str(row["Crop"])
        year = int(row["Year"])
        uri  = price_obs_uri(crop, year)

        prices_g.add((uri, RDF.type,          AGRI.PriceObservation))
        prices_g.add((uri, AGRI.refCommodity, commodity_uri(crop)))
        prices_g.add((uri, AGRI.refYear,      Literal(str(year), datatype=XSD.gYear)))
        prices_g.add((uri, AGRI.numericValue, to_decimal_literal(row["Price_real_2010USD_per_tonne"])))
        prices_g.add((uri, AGRI.unit,         Literal("real2010USD/mt", datatype=XSD.string)))
        prices_g.add((uri, DCTERMS.source,    AGRI["dataset-worldbank-prices"]))

    # ------------------------------------------------------------------
    # Climate observations
    # ------------------------------------------------------------------
    climate_value_col = "Annual precipitation anomaly"

    for _, row in climate_df.iterrows():
        code = str(row["Code"])
        year = int(row["Year"])
        uri  = climate_obs_uri(code, year)

        climate_g.add((uri, RDF.type,          AGRI.ClimateObservation))
        climate_g.add((uri, AGRI.refCountry,   country_uri(code)))
        climate_g.add((uri, AGRI.refYear,      Literal(str(year), datatype=XSD.gYear)))
        climate_g.add((uri, AGRI.numericValue, to_decimal_literal(row[climate_value_col])))
        climate_g.add((uri, AGRI.unit,         Literal("mm", datatype=XSD.string)))
        climate_g.add((uri, DCTERMS.source,    AGRI["dataset-precipitation-anomaly"]))

    # ------------------------------------------------------------------
    # Gross production value observations
    # ------------------------------------------------------------------
    gross_value_col = "GrossProductionValue_currentUSD"

    for _, row in gross_df.iterrows():
        code = str(row["Code"])
        year = int(row["Year"])
        uri  = gross_value_obs_uri(code, year)

        gross_g.add((uri, RDF.type,          AGRI.GrossProductionValueObservation))
        gross_g.add((uri, AGRI.refCountry,   country_uri(code)))
        gross_g.add((uri, AGRI.refYear,      Literal(str(year), datatype=XSD.gYear)))
        gross_g.add((uri, AGRI.numericValue, to_decimal_literal(row[gross_value_col])))
        gross_g.add((uri, AGRI.unit,         Literal("currentUSD", datatype=XSD.string)))
        gross_g.add((uri, DCTERMS.source,    AGRI["dataset-gross-production-value"]))

    # ------------------------------------------------------------------
    # Serialise modular graphs
    # ------------------------------------------------------------------
    entities_g.serialize(destination=RDF_DIR / "entities.ttl",         format="turtle")
    crop_g.serialize(    destination=RDF_DIR / "crop_observations.ttl", format="turtle")
    prices_g.serialize(  destination=RDF_DIR / "prices.ttl",            format="turtle")
    climate_g.serialize( destination=RDF_DIR / "climate.ttl",           format="turtle")
    gross_g.serialize(   destination=RDF_DIR / "gross_value.ttl",       format="turtle")

    # ------------------------------------------------------------------
    # Build merged KG
    # ------------------------------------------------------------------
    merged_g.parse(str(ONTOLOGY_PATH), format="turtle")
    for sub_graph in (entities_g, crop_g, prices_g, climate_g, gross_g):
        merge_graphs(merged_g, sub_graph)

    merged_g.serialize(destination=RDF_DIR / "agri_kg.ttl", format="turtle")

    print("\n=== RDF generation completed ===")
    print(f"  Entities triples    : {len(entities_g)}")
    print(f"  Crop obs triples    : {len(crop_g)}")
    print(f"  Price triples       : {len(prices_g)}")
    print(f"  Climate triples     : {len(climate_g)}")
    print(f"  Gross value triples : {len(gross_g)}")
    print(f"  Merged KG triples   : {len(merged_g)}")


if __name__ == "__main__":
    main()
