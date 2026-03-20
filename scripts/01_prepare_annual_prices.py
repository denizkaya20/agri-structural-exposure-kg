"""
01_prepare_annual_prices.py
----------------------------
Cleans the World Bank CMO historical annual commodity price dataset.

Input : data/raw/CMO-Historical-Data-Annual.xlsx  (sheet: "Annual Prices (Real)")
Output: data/processed/annual_prices_clean.csv

The script reads the wide-format Excel sheet, maps commodity column names to
the project's canonical crop names, and converts to long format.

Price unit: constant 2010 USD per metric tonne.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT_DIR / "data" / "raw" / "CMO-Historical-Data-Annual.xlsx"
OUT_PATH = ROOT_DIR / "data" / "processed" / "annual_prices_clean.csv"

# ---------------------------------------------------------------------------
# Column mapping  (Excel header → canonical crop name)
# ---------------------------------------------------------------------------
PRICE_COLUMN_MAP: dict[str, str] = {
    "Soybeans":      "Soybeans",
    "Barley":        "Barley",
    "Maize":         "Maize",
    "Rice, Thai 5%": "Rice",
    "Wheat, US HRW": "Wheat",
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Raw price file not found: {RAW_PATH}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    # The sheet has a non-standard layout:
    #   row 6 (0-based) → commodity names
    #   row 7           → units
    #   row 8+          → annual data
    raw = pd.read_excel(RAW_PATH, sheet_name="Annual Prices (Real)", header=None)

    header_row = raw.iloc[6].tolist()
    data = raw.iloc[8:].copy()
    data.columns = ["Year"] + header_row[1:]

    # Keep only target commodities
    keep_cols = ["Year"] + list(PRICE_COLUMN_MAP.keys())
    data = data[keep_cols].copy()

    # Wide → long
    long_df = data.melt(
        id_vars="Year",
        var_name="RawCrop",
        value_name="Price_real_2010USD_per_tonne",
    )

    long_df["Year"] = pd.to_numeric(long_df["Year"], errors="coerce")
    long_df["Price_real_2010USD_per_tonne"] = pd.to_numeric(
        long_df["Price_real_2010USD_per_tonne"], errors="coerce"
    )

    long_df = long_df.dropna(subset=["Year", "Price_real_2010USD_per_tonne"]).copy()
    long_df["Year"] = long_df["Year"].astype(int)
    long_df["Crop"] = long_df["RawCrop"].map(PRICE_COLUMN_MAP)

    long_df = (
        long_df[["Year", "Crop", "Price_real_2010USD_per_tonne"]]
        .sort_values(["Year", "Crop"])
        .reset_index(drop=True)
    )

    long_df.to_csv(OUT_PATH, index=False)

    print("\n=== Annual prices preprocessing completed ===")
    print(f"Output : {OUT_PATH}")
    print(f"Rows   : {len(long_df)}")
    print(f"Crops  : {long_df['Crop'].nunique()}")
    print(f"Years  : {long_df['Year'].min()} – {long_df['Year'].max()}")


if __name__ == "__main__":
    main()
