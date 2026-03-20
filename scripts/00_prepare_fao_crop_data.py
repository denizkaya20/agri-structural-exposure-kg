"""
00_prepare_fao_crop_data.py
---------------------------
Cleans and standardises the raw FAOSTAT crop production dataset.

Input : data/raw/FAOSTAT_data_en_3-8-2026.csv
Output: data/processed/faostat_crop_observations_clean.csv

Filtering scope
---------------
- Countries : Brazil, China, Egypt, France, India, Italy,
              Spain, Turkey, Ukraine, United States
- Crops     : Barley, Maize, Rice, Soybeans, Wheat
- Elements  : Production (t), Yield (kg/ha), Area harvested (ha)
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths (relative to project root)
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT_DIR / "data" / "raw" / "FAOSTAT_data_en_3-8-2026.csv"
OUT_PATH = ROOT_DIR / "data" / "processed" / "faostat_crop_observations_clean.csv"

# ---------------------------------------------------------------------------
# Mapping tables
# ---------------------------------------------------------------------------
COUNTRY_MAP: dict[str, tuple[str, str]] = {
    "Brazil":                   ("Brazil",        "BRA"),
    "China":                    ("China",         "CHN"),
    "Egypt":                    ("Egypt",         "EGY"),
    "France":                   ("France",        "FRA"),
    "India":                    ("India",         "IND"),
    "Italy":                    ("Italy",         "ITA"),
    "Spain":                    ("Spain",         "ESP"),
    "Turkey":                   ("Turkey",        "TUR"),
    "Türkiye":                  ("Turkey",        "TUR"),
    "Ukraine":                  ("Ukraine",       "UKR"),
    "United States":            ("United States", "USA"),
    "United States of America": ("United States", "USA"),
}

ITEM_MAP: dict[str, str] = {
    "Barley":       "Barley",
    "Maize (corn)": "Maize",
    "Rice":         "Rice",
    "Soya beans":   "Soybeans",
    "Wheat":        "Wheat",
}

ELEMENT_MAP: dict[str, str] = {
    "Production":     "Production",
    "Yield":          "Yield",
    "Area harvested": "Area harvested",
}

EXPECTED_UNITS: dict[str, str] = {
    "Production":     "t",
    "Yield":          "kg/ha",
    "Area harvested": "ha",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _strip_object_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Strip whitespace and replace bare 'nan' strings with pd.NA."""
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip().replace("nan", pd.NA)
    return df


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Raw FAO file not found: {RAW_PATH}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # Load
    df = pd.read_csv(RAW_PATH)
    df.columns = [c.strip() for c in df.columns]
    df = _strip_object_columns(df)

    # Filter
    df = df[df["Area"].isin(COUNTRY_MAP)].copy()
    df = df[df["Item"].isin(ITEM_MAP)].copy()
    df = df[df["Element"].isin(ELEMENT_MAP)].copy()

    # Standardise names
    df["Entity"]  = df["Area"].map(lambda x: COUNTRY_MAP[x][0])
    df["Code"]    = df["Area"].map(lambda x: COUNTRY_MAP[x][1])
    df["Crop"]    = df["Item"].map(ITEM_MAP)
    df["Element"] = df["Element"].map(ELEMENT_MAP)

    # Rename columns
    df = df.rename(
        columns={
            "Area Code (M49)": "M49",
            "Item Code (CPC)": "ItemCode",
            "Element Code":    "ElementCode",
            "Flag Description": "FlagDescription",
        }
    )

    keep_cols = [
        "Entity", "Code", "M49", "Year", "Crop",
        "ItemCode", "Element", "ElementCode",
        "Unit", "Value", "Flag", "FlagDescription", "Note",
    ]
    df = df[keep_cols].copy()

    # Type coercion
    for col in ["Year", "Value", "M49", "ItemCode", "ElementCode"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    for col in ["Flag", "FlagDescription", "Note"]:
        df[col] = df[col].fillna("")

    df = df.dropna(
        subset=["Entity", "Code", "M49", "Year", "Crop",
                "ItemCode", "Element", "ElementCode", "Unit", "Value"]
    ).copy()

    df["Year"]        = df["Year"].astype(int)
    df["M49"]         = df["M49"].astype(int)
    df["ItemCode"]    = df["ItemCode"].astype(int)
    df["ElementCode"] = df["ElementCode"].astype(int)
    df["Value"]       = df["Value"].astype(float)

    # Unit validation
    df["_expected_unit"] = df["Element"].map(EXPECTED_UNITS)
    bad = df[df["Unit"] != df["_expected_unit"]]
    if not bad.empty:
        print("[WARNING] Unexpected units:")
        print(bad[["Entity", "Year", "Crop", "Element", "Unit", "_expected_unit"]].head(20))
    df = df.drop(columns=["_expected_unit"])

    # Duplicate check
    dup_mask = df.duplicated(subset=["Entity", "Code", "Year", "Crop", "Element"], keep=False)
    if dup_mask.any():
        print(f"[WARNING] {dup_mask.sum()} duplicate rows found.")

    df = df.sort_values(["Entity", "Year", "Crop", "Element"]).reset_index(drop=True)
    df.to_csv(OUT_PATH, index=False)

    print("\n=== FAO preprocessing completed ===")
    print(f"Output : {OUT_PATH}")
    print(f"Rows   : {len(df)}")
    print(f"Countries : {df['Entity'].nunique()} | Crops : {df['Crop'].nunique()}")
    print(f"Years  : {df['Year'].min()} – {df['Year'].max()}")


if __name__ == "__main__":
    main()
