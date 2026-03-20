"""
05_visualization.py
--------------------
Generates one publication-quality figure per research question (RQ1–RQ5).

Usage
-----
    python scripts/05_visualization.py

Input CSVs (queries/Results/<RQ>/)
------------------------------------
RQ1  : query-result_1.csv
RQ1b : query-result_1b.csv
RQ2  : query-result_2.csv
RQ3  : query-result_3.csv
RQ4  : query-result_4.csv
RQ5  : query-result_5.csv

Output figures (figures/)
--------------------------
RQ1_top10_dependency_share.png
RQ1b_avg_dependency_heatmap.png
RQ2_compound_shock.png
RQ3_climate_production.png
RQ4_price_volatility.png
RQ5_comparative_profile.png

Requirements
------------
    pip install pandas matplotlib seaborn numpy
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR  = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT_DIR / "queries" / "Results"
FIGURES_DIR = ROOT_DIR / "figures"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

CSV: dict[str, Path] = {
    "RQ1":  RESULTS_DIR / "RQ1"  / "query-result_1.csv",
    "RQ1b": RESULTS_DIR / "RQ1b" / "query-result_1b.csv",
    "RQ2":  RESULTS_DIR / "RQ2"  / "query-result_2.csv",
    "RQ3":  RESULTS_DIR / "RQ3"  / "query-result_3.csv",
    "RQ4":  RESULTS_DIR / "RQ4"  / "query-result_4.csv",
    "RQ5":  RESULTS_DIR / "RQ5"  / "query-result_5.csv",
}

# ---------------------------------------------------------------------------
# Colour palettes
# ---------------------------------------------------------------------------
COMMODITY_COLORS: dict[str, str] = {
    "Wheat":    "#E67E22",
    "Maize":    "#F1C40F",
    "Rice":     "#27AE60",
    "Soybeans": "#2980B9",
    "Barley":   "#8E44AD",
}

COUNTRY_COLORS: dict[str, str] = {
    "Ukraine":       "#E74C3C",
    "Brazil":        "#27AE60",
    "India":         "#F39C12",
    "United States": "#2980B9",
    "France":        "#8E44AD",
    "China":         "#C0392B",
    "Egypt":         "#D4AC0D",
    "Turkey":        "#1ABC9C",
    "Italy":         "#2C3E50",
    "Spain":         "#E91E63",
}

plt.rcParams.update(
    {
        "font.family":       "DejaVu Sans",
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "axes.titlesize":    14,
        "axes.titleweight":  "bold",
        "axes.labelsize":    11,
        "xtick.labelsize":   10,
        "ytick.labelsize":   10,
        "figure.dpi":        150,
    }
)


# ---------------------------------------------------------------------------
# RQ1 — Top 10 Dependency Shares
# ---------------------------------------------------------------------------

def plot_rq1() -> None:
    """Horizontal bar chart of the top-10 country-commodity dependency shares."""
    df = pd.read_csv(CSV["RQ1"])
    df["dependencyShare"] = df["dependencyShare"].astype(float)
    df["label"] = (
        df["countryLabel"] + "\n"
        + df["commodityLabel"] + " ("
        + df["year"].astype(str) + ")"
    )
    top = df.nlargest(10, "dependencyShare")
    colors = [COMMODITY_COLORS.get(c, "#95A5A6") for c in top["commodityLabel"]]

    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.barh(
        top["label"][::-1], top["dependencyShare"][::-1],
        color=colors[::-1], edgecolor="white", height=0.65,
    )

    for bar, val in zip(bars, top["dependencyShare"][::-1]):
        ax.text(
            bar.get_width() + 0.005, bar.get_y() + bar.get_height() / 2,
            f"{val:.3f}", va="center", fontsize=9.5, color="#333333",
        )

    ax.axvline(0.25, color="grey", linestyle="--", linewidth=1, alpha=0.6,
               label="0.25 reference line")
    ax.set_xlabel("Dependency Share  (production value / gross production value)")
    ax.set_title("RQ1 — Top 10 Country-Commodity Dependency Shares\n"
                 "Single-year values, 2000–2020")
    ax.set_xlim(0, 0.48)

    legend_patches = [mpatches.Patch(color=v, label=k) for k, v in COMMODITY_COLORS.items()]
    ax.legend(handles=legend_patches, title="Commodity", loc="lower right",
              framealpha=0.85, fontsize=9)

    fig.tight_layout()
    path = FIGURES_DIR / "RQ1_top10_dependency_share.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")


# ---------------------------------------------------------------------------
# RQ1b — Average Dependency Share Heatmap
# ---------------------------------------------------------------------------

def plot_rq1b() -> None:
    """Heatmap of average dependency share by country × commodity."""
    df = pd.read_csv(CSV["RQ1b"])
    df["avgDependencyShare"] = df["avgDependencyShare"].astype(float)

    pivot = df.pivot(
        index="countryLabel", columns="commodityLabel", values="avgDependencyShare"
    ).fillna(0)

    pivot = pivot.loc[pivot.max(axis=1).sort_values(ascending=False).index]
    commodity_order = ["Wheat", "Maize", "Rice", "Soybeans", "Barley"]
    pivot = pivot[[c for c in commodity_order if c in pivot.columns]]

    fig, ax = plt.subplots(figsize=(9, 7))
    sns.heatmap(
        pivot, annot=True, fmt=".3f", cmap="YlOrRd",
        linewidths=0.5, linecolor="white", annot_kws={"size": 9},
        cbar_kws={"label": "Average Dependency Share (2000–2020)"}, ax=ax,
    )
    ax.set_title("RQ1b — Average Dependency Share by Country and Commodity\n"
                 "Darker = higher structural dependency", pad=12)
    ax.set_xlabel("Commodity")
    ax.set_ylabel("Country")
    ax.tick_params(axis="x", rotation=0)
    ax.tick_params(axis="y", rotation=0)

    fig.tight_layout()
    path = FIGURES_DIR / "RQ1b_avg_dependency_heatmap.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")


# ---------------------------------------------------------------------------
# RQ2 — Compound Shock: Low Production + High Price
# ---------------------------------------------------------------------------

def plot_rq2() -> None:
    """Scatter plot of production value vs. global commodity price."""
    df = pd.read_csv(CSV["RQ2"])
    df["prodValue"] = df["prodValue"].astype(float)
    df["price"]     = df["price"].astype(float)

    fig, ax = plt.subplots(figsize=(10, 6))
    palette = {c: COUNTRY_COLORS.get(c, "#95A5A6") for c in df["countryLabel"].unique()}

    for country, sub in df.groupby("countryLabel"):
        ax.scatter(
            sub["price"], sub["prodValue"] / 1e6,
            c=palette[country], s=60, alpha=0.8,
            edgecolors="white", linewidths=0.5, label=country, zorder=3,
        )

    for _, row in df.iterrows():
        if row["prodValue"] < 200_000 or row["price"] > 450:
            ax.annotate(
                f"{row['commodityLabel']} {int(row['year'])}",
                (row["price"], row["prodValue"] / 1e6),
                textcoords="offset points", xytext=(6, 4),
                fontsize=7.5, color="#444444",
            )

    ax.axvline(200, color="#E74C3C", linestyle="--", linewidth=1.2, alpha=0.7,
               label="Price threshold = 200 USD/t")
    ax.set_xlabel("Global Commodity Price (USD / tonne)")
    ax.set_ylabel("Production (million tonnes)")
    ax.set_title("RQ2 — Compound Shock: Low Production + High Price\n"
                 "Each point = one country-commodity-year observation")
    ax.legend(title="Country", bbox_to_anchor=(1.01, 1), loc="upper left",
              fontsize=9, framealpha=0.85)
    ax.grid(True, alpha=0.25)

    fig.tight_layout()
    path = FIGURES_DIR / "RQ2_compound_shock.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")


# ---------------------------------------------------------------------------
# RQ3 — Climate Anomaly vs. Production
# ---------------------------------------------------------------------------

def plot_rq3() -> None:
    """Faceted dual-axis chart: precipitation anomaly bars + production lines."""
    df = pd.read_csv(CSV["RQ3"])
    df["anomaly"]   = df["anomaly"].astype(float)
    df["prodValue"] = df["prodValue"].astype(float)
    df["year"]      = df["year"].astype(int)

    focus     = df[df["commodityLabel"].isin(["Wheat", "Rice"])].copy()
    countries = sorted(focus["countryLabel"].unique())

    ncols = 3
    nrows = int(np.ceil(len(countries) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(15, 4.5 * nrows),
                             constrained_layout=True)
    axes = axes.flatten()

    for i, country in enumerate(countries):
        ax  = axes[i]
        ax2 = ax.twinx()
        sub = focus[focus["countryLabel"] == country].sort_values("year")

        for commodity, color in [("Wheat", "#E67E22"), ("Rice", "#27AE60")]:
            csub = sub[sub["commodityLabel"] == commodity]
            if not csub.empty:
                ax2.plot(csub["year"], csub["prodValue"] / 1e6,
                         color=color, linewidth=2, marker="o", markersize=4,
                         label=f"{commodity} production")

        unique_years = sub.drop_duplicates("year")[["year", "anomaly"]]
        bar_colors   = ["#2980B9" if v >= 0 else "#C0392B" for v in unique_years["anomaly"]]
        ax.bar(unique_years["year"], unique_years["anomaly"],
               color=bar_colors, alpha=0.45, width=0.8)
        ax.axhline(0,   color="black",   linewidth=0.7)
        ax.axhline(-50, color="#C0392B", linestyle="--", linewidth=0.9, alpha=0.7)

        ax.set_title(country, fontsize=12, fontweight="bold")
        ax.set_ylabel("Precipitation anomaly (mm)", fontsize=8, color="#2980B9")
        ax2.set_ylabel("Production (M tonnes)",      fontsize=8)
        ax.tick_params(axis="x", labelrotation=45, labelsize=8)
        ax.tick_params(axis="y", labelsize=8)
        ax2.tick_params(axis="y", labelsize=8)

    for j in range(i + 1, len(axes)):
        axes[j].set_visible(False)

    legend_handles = [
        mpatches.Patch(color="#E67E22",              label="Wheat production"),
        mpatches.Patch(color="#27AE60",              label="Rice production"),
        mpatches.Patch(color="#2980B9", alpha=0.5,   label="Positive anomaly"),
        mpatches.Patch(color="#C0392B", alpha=0.5,   label="Negative anomaly"),
    ]
    fig.legend(handles=legend_handles, loc="lower center", ncol=4,
               fontsize=10, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("RQ3 — Precipitation Anomaly vs. Wheat & Rice Production",
                 fontsize=14, fontweight="bold", y=1.01)

    path = FIGURES_DIR / "RQ3_climate_production.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")


# ---------------------------------------------------------------------------
# RQ4 — Price Volatility
# ---------------------------------------------------------------------------

def plot_rq4() -> None:
    """Horizontal range bar chart showing min/max price per commodity."""
    df = pd.read_csv(CSV["RQ4"])
    for col in ["maxPrice", "minPrice", "priceRange"]:
        df[col] = df[col].astype(float)
    df = df.sort_values("priceRange", ascending=True)

    colors = [COMMODITY_COLORS.get(c, "#95A5A6") for c in df["commodityLabel"]]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(df["commodityLabel"], df["priceRange"],
            left=df["minPrice"], color=colors,
            edgecolor="white", height=0.55, alpha=0.85)
    ax.scatter(df["minPrice"], df["commodityLabel"],
               color="white", edgecolors=colors, s=80, zorder=5,
               linewidths=2, label="Min price")
    ax.scatter(df["maxPrice"], df["commodityLabel"],
               color=colors, edgecolors="white", s=80, zorder=5,
               linewidths=1.5, label="Max price")

    for _, row in df.iterrows():
        ax.text(
            row["minPrice"] + row["priceRange"] / 2, row["commodityLabel"],
            f"  range: {row['priceRange']:.1f}", va="center", fontsize=9.5, color="#333333",
        )

    ax.set_xlabel("Global Price (2010 USD / tonne)")
    ax.set_title("RQ4 — Commodity Price Volatility 2000–2020\n"
                 "Bar spans min to max annual price; wider = more volatile")
    ax.legend(loc="lower right", fontsize=9)
    ax.grid(True, axis="x", alpha=0.25)

    fig.tight_layout()
    path = FIGURES_DIR / "RQ4_price_volatility.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")


# ---------------------------------------------------------------------------
# RQ5 — Comparative Structural Exposure Profiles
# ---------------------------------------------------------------------------

def plot_rq5() -> None:
    """Grouped bar charts comparing dependency profiles for country pairs."""
    df = pd.read_csv(CSV["RQ5"])
    df["avgDependencyShare"] = df["avgDependencyShare"].astype(float)

    commodity_order = ["Wheat", "Maize", "Rice", "Soybeans", "Barley"]
    df["commodityLabel"] = pd.Categorical(df["commodityLabel"],
                                          categories=commodity_order, ordered=True)
    df = df.sort_values("commodityLabel")

    pair_colors = {
        "France": "#3498DB", "Italy": "#E74C3C",
        "India":  "#F39C12", "China": "#C0392B",
    }

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharey=False)
    pairs = [
        ("France vs Italy", ["France", "Italy"], axes[0]),
        ("India vs China",  ["India",  "China"],  axes[1]),
    ]

    for title, countries, ax in pairs:
        sub   = df[df["countryLabel"].isin(countries)]
        pivot = sub.pivot(index="commodityLabel", columns="countryLabel",
                          values="avgDependencyShare").fillna(0)
        pivot = pivot.reindex([c for c in commodity_order if c in pivot.index])

        x     = np.arange(len(pivot))
        width = 0.35
        cols  = [c for c in countries if c in pivot.columns]

        for j, country in enumerate(cols):
            offset = (j - 0.5) * width
            bars = ax.bar(x + offset, pivot[country], width=width,
                          color=pair_colors[country], edgecolor="white",
                          label=country, alpha=0.88)
            for bar in bars:
                h = bar.get_height()
                if h > 0.005:
                    ax.text(bar.get_x() + bar.get_width() / 2,
                            h + 0.002, f"{h:.3f}",
                            ha="center", va="bottom", fontsize=8)

        ax.set_xticks(x)
        ax.set_xticklabels(pivot.index, rotation=15, ha="right")
        ax.set_ylabel("Average Dependency Share (2000–2020)")
        ax.set_title(f"RQ5 — {title}", fontsize=12, fontweight="bold")
        ax.legend(fontsize=10)
        ax.grid(True, axis="y", alpha=0.25)
        ax.set_ylim(0, pivot.values.max() * 1.25)

    fig.suptitle("RQ5 — Comparative Structural Exposure Profiles\n"
                 "France vs Italy  |  India vs China",
                 fontsize=14, fontweight="bold")
    fig.tight_layout()

    path = FIGURES_DIR / "RQ5_comparative_profile.png"
    fig.savefig(path, bbox_inches="tight")
    plt.close()
    print(f"Saved: {path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Generating visualizations …")
    plot_rq1()
    plot_rq1b()
    plot_rq2()
    plot_rq3()
    plot_rq4()
    plot_rq5()
    print(f"\nAll figures saved to: {FIGURES_DIR}")
