from __future__ import annotations
import pandas as pd
import numpy as np

REQUIRED_NAV_COLUMNS = {"date", "scheme", "nav"}

def clean_nav(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().lower() for c in out.columns]
    missing = REQUIRED_NAV_COLUMNS - set(out.columns)
    if missing:
        raise ValueError(f"NAV file must contain columns: {', '.join(sorted(REQUIRED_NAV_COLUMNS))}. Missing: {', '.join(sorted(missing))}")
    out["date"] = pd.to_datetime(out["date"], errors="coerce", dayfirst=True)
    out["nav"] = pd.to_numeric(out["nav"].astype(str).str.replace(",", "", regex=False), errors="coerce")
    out["scheme"] = out["scheme"].astype(str).str.strip()
    out = out.dropna(subset=["date", "nav", "scheme"])
    out = out[out["nav"] > 0].sort_values(["scheme", "date"])
    return out.drop_duplicates(["scheme", "date"], keep="last")

def cagr(start: float, end: float, years: float) -> float | None:
    if start <= 0 or end <= 0 or years <= 0:
        return None
    return (end / start) ** (1 / years) - 1

def scheme_metrics(nav_df: pd.DataFrame) -> pd.DataFrame:
    nav = clean_nav(nav_df)
    rows = []
    for scheme, g in nav.groupby("scheme"):
        g = g.sort_values("date").copy()
        first, last = g.iloc[0], g.iloc[-1]
        years = (last.date - first.date).days / 365.25
        returns = g.set_index("date")["nav"].resample("W-FRI").last().dropna().pct_change().dropna()
        vol = float(returns.std() * np.sqrt(52)) if len(returns) > 2 else None
        peak = g["nav"].cummax()
        drawdown = g["nav"] / peak - 1
        rows.append({
            "scheme": scheme,
            "first_nav_date": first.date.date().isoformat(),
            "latest_nav_date": last.date.date().isoformat(),
            "observations": int(len(g)),
            "latest_nav": float(last.nav),
            "period_return_pct": float((last.nav / first.nav - 1) * 100) if first.nav else None,
            "annualised_return_pct": (cagr(float(first.nav), float(last.nav), years) * 100) if years >= 0.25 else None,
            "annualised_volatility_pct": vol * 100 if vol is not None else None,
            "max_drawdown_pct": float(drawdown.min() * 100),
            "history_years": years,
        })
    return pd.DataFrame(rows)

def score_fund(quant_score: float | None, qualitative_score: float | None, quant_weight: float = 0.60) -> dict:
    """Scores are only calculated when both evidence-based inputs exist."""
    if quant_score is None or qualitative_score is None:
        return {"combined_score": None, "status": "INSUFFICIENT EVIDENCE"}
    q = min(100.0, max(0.0, float(quant_score)))
    qual = min(100.0, max(0.0, float(qualitative_score)))
    return {"combined_score": round(q * quant_weight + qual * (1 - quant_weight), 1), "status": "USER-ASSESSED INPUTS"}

def simple_portfolio_summary(holdings: pd.DataFrame) -> dict:
    required = {"scheme", "invested", "current_value"}
    if not required.issubset(holdings.columns):
        raise ValueError(f"Holdings need columns: {', '.join(sorted(required))}")
    h = holdings.copy()
    for c in ["invested", "current_value"]:
        h[c] = pd.to_numeric(h[c], errors="coerce").fillna(0)
    invested = float(h.invested.sum())
    value = float(h.current_value.sum())
    return {"invested": invested, "current_value": value, "gain": value-invested,
            "return_pct": ((value/invested)-1)*100 if invested else None}
