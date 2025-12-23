import pandas as pd
from pathlib import Path


def load_kpis() -> tuple[pd.DataFrame, pd.DataFrame]:
    monthly = pd.read_csv("./kpis_monthly.csv", parse_dates=["InvoiceMonth"])
    # monthly = pd.read_csv("data/processed/kpis_monthly.csv", parse_dates=["InvoiceMonth"])
    country = pd.read_csv("./kpis_monthly_country.csv", parse_dates=["InvoiceMonth"])
    # country = pd.read_csv("data/processed/kpis_monthly_country.csv", parse_dates=["InvoiceMonth"])
    return monthly.sort_values("InvoiceMonth"), country.sort_values(["Country", "InvoiceMonth"])


def add_derived_metrics(monthly: pd.DataFrame) -> pd.DataFrame:
    m = monthly.copy()

    # Helpful derived metrics
    m["Revenue_Rolling3M"] = m["Revenue"].rolling(3).mean()
    m["Orders_Rolling3M"] = m["Orders"].rolling(3).mean()
    m["ActiveCustomers_Rolling3M"] = m["ActiveCustomers"].rolling(3).mean()

    # Revenue per customer (proxy for monetization intensity)
    m["RevenuePerCustomer"] = m["Revenue"] / m["ActiveCustomers"]

    return m


def top_months(monthly: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    cols = ["InvoiceMonth", "Revenue", "Orders", "ActiveCustomers", "UnitsSold", "AOV",
            "Revenue_MoM_Growth", "ActiveCustomers_MoM_Growth"]
    return monthly[cols].sort_values("Revenue", ascending=False).head(n)


def nov_dec_comparison(monthly: pd.DataFrame) -> pd.DataFrame:
    m = monthly.copy()
    m["Year"] = m["InvoiceMonth"].dt.year
    m["Month"] = m["InvoiceMonth"].dt.month

    # Compare Nov (11) vs Dec (12) within each year
    pivot = (
        m[m["Month"].isin([11, 12])]
        .pivot_table(index="Year", columns="Month", values=["Revenue", "Orders", "ActiveCustomers", "AOV"], aggfunc="sum")
    )

    # Flatten columns
    pivot.columns = [f"{metric}_M{month}" for metric, month in pivot.columns]
    pivot = pivot.reset_index()

    # Add deltas
    for metric in ["Revenue", "Orders", "ActiveCustomers", "AOV"]:
        nov = f"{metric}_M11"
        dec = f"{metric}_M12"
        if nov in pivot.columns and dec in pivot.columns:
            pivot[f"{metric}_DecMinusNov"] = pivot[dec] - pivot[nov]
            pivot[f"{metric}_DecVsNov_Pct"] = (pivot[dec] / pivot[nov]) - 1

    return pivot


def revenue_drivers(monthly: pd.DataFrame) -> pd.DataFrame:
    # Simple correlation to understand if Revenue moves more with Orders or AOV
    m = monthly.copy()
    corr_orders = m["Revenue"].corr(m["Orders"])
    corr_aov = m["Revenue"].corr(m["AOV"])
    corr_customers = m["Revenue"].corr(m["ActiveCustomers"])

    return pd.DataFrame(
        [
            {"Driver": "Orders", "CorrelationWithRevenue": corr_orders},
            {"Driver": "AOV", "CorrelationWithRevenue": corr_aov},
            {"Driver": "ActiveCustomers", "CorrelationWithRevenue": corr_customers},
        ]
    ).sort_values("CorrelationWithRevenue", ascending=False)


def top_countries_overall(country: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    agg = (
        country.groupby("Country", as_index=False)
        .agg(
            Revenue=("Revenue", "sum"),
            Orders=("Orders", "sum"),
            ActiveCustomers=("ActiveCustomers", "sum"),
            UnitsSold=("UnitsSold", "sum"),
        )
    )
    agg["AOV"] = agg["Revenue"] / agg["Orders"]
    return agg.sort_values("Revenue", ascending=False).head(top_n)


def country_concentration(country_top: pd.DataFrame) -> pd.DataFrame:
    # concentration for top countries
    total_revenue = country_top["Revenue"].sum()
    df = country_top.copy()
    df["RevenueShare"] = df["Revenue"] / total_revenue
    df["CumulativeShare"] = df["RevenueShare"].cumsum()
    return df[["Country", "Revenue", "RevenueShare", "CumulativeShare"]]


def fastest_growing_countries(country: pd.DataFrame, min_months: int = 12, top_n: int = 10) -> pd.DataFrame:
    # Growth = last month revenue / first month revenue - 1
    # Only countries with enough months of data are considered.
    rows = []
    for c, grp in country.groupby("Country"):
        g = grp.sort_values("InvoiceMonth")
        if len(g) < min_months:
            continue

        first = g.iloc[0]["Revenue"]
        last = g.iloc[-1]["Revenue"]

        if first <= 0:
            continue

        growth = (last / first) - 1
        rows.append(
            {"Country": c, "Months": len(g), "FirstRevenue": first, "LastRevenue": last, "GrowthPct": growth}
        )

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values("GrowthPct", ascending=False).head(top_n)


def save_outputs(output_dir: Path, name: str, df: pd.DataFrame) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_dir / f"{name}.csv", index=False)


def main():
    monthly, country = load_kpis()
    monthly = add_derived_metrics(monthly)

    out_dir = Path("outputs/insights")

    # 1) Top months by revenue
    save_outputs(out_dir, "top_months_by_revenue", top_months(monthly, n=8))

    # 2) Nov vs Dec comparisons by year
    save_outputs(out_dir, "nov_dec_comparison_by_year", nov_dec_comparison(monthly))

    # 3) Revenue driver correlations
    save_outputs(out_dir, "revenue_driver_correlations", revenue_drivers(monthly))

    # 4) Top countries overall
    top_ctry = top_countries_overall(country, top_n=12)
    save_outputs(out_dir, "top_countries_overall", top_ctry)

    # 5) Concentration among top countries
    save_outputs(out_dir, "top_country_revenue_concentration", country_concentration(top_ctry))

    # 6) Fastest growing countries (based on first vs last month revenue)
    save_outputs(out_dir, "fastest_growing_countries", fastest_growing_countries(country, min_months=12, top_n=12))

    print("Insight evidence generated in:", out_dir)
    print("Files created:")
    for p in sorted(out_dir.glob("*.csv")):
        print("-", p.name)


if __name__ == "__main__":
    main()
