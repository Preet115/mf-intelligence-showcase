import json
from datetime import date
import streamlit as st
import pandas as pd
import plotly.express as px
from analytics import clean_nav, scheme_metrics, score_fund, simple_portfolio_summary

st.set_page_config(page_title="MF Intelligence | MVP", page_icon="📊", layout="wide")
st.title("Mutual Fund Intelligence Platform")
st.caption("MVP 0.3 · Interactive showcase · Dynamic inputs · Evidence-led analysis · Not investment advice")
st.info("SHOWCASE MODE — the default holdings are fictional examples, not real investments or live market values. Privacy by design: never enter your name, PAN, folio number, bank details, credentials, address, or other identifiers. Data is held only in the current app session; it is not permanently saved.")

CATEGORIES = ["Short-duration debt", "Liquid / overnight debt", "Corporate bond debt", "Gilt debt", "Hybrid", "Equity: large cap", "Equity: large & mid cap", "Equity: mid cap", "Equity: small cap", "Index / ETF", "Gold", "International equity", "Other / not mapped"]
OBJECTIVES = ["Education / near-term expense", "Emergency reserve", "Home / major purchase", "Long-term wealth growth", "Retirement", "General savings", "Other"]
HORIZONS = ["Under 1 year", "1–3 years", "3–5 years", "5+ years", "Not decided"]
RISK_LEVELS = ["Very low", "Low", "Moderate", "High", "Very high", "Not decided"]

# Session defaults: user can add/remove/replace rows at any time.
if "holdings_data" not in st.session_state:
    st.session_state.holdings_data = pd.DataFrame([
        {"scheme_name":"Demo Short Duration Debt Fund", "scheme_code":"DEMO-001", "plan":"Direct", "option":"Growth", "category":"Short-duration debt", "units":100.0, "invested_amount_inr":10000.0, "current_value_inr":10250.0, "purpose":"Illustrative near-term allocation", "last_updated":str(date.today())},
        {"scheme_name":"Demo Gold Fund", "scheme_code":"DEMO-002", "plan":"Direct", "option":"Growth", "category":"Gold", "units":250.0, "invested_amount_inr":5000.0, "current_value_inr":5350.0, "purpose":"Illustrative diversification", "last_updated":str(date.today())},
        {"scheme_name":"Demo Large & Mid Cap Fund", "scheme_code":"DEMO-003", "plan":"Direct", "option":"Growth", "category":"Equity: large & mid cap", "units":200.0, "invested_amount_inr":8000.0, "current_value_inr":8400.0, "purpose":"Illustrative long-term growth", "last_updated":str(date.today())},
    ])
if "profile" not in st.session_state:
    st.session_state.profile = {"objective":"Education / near-term expense", "horizon":"Under 1 year", "risk":"Moderate", "cash_need":0.0, "cash_need_date":None, "monthly_contribution":5000.0, "emergency_fund":"Not specified", "notes":""}

with st.sidebar:
    st.header("Analysis philosophy")
    st.metric("Quantitative weight", "60%")
    st.metric("Qualitative weight", "40%")
    st.markdown("**Decision principle**")
    st.write("Evidence before scores. Separate verified facts, estimates, and judgement. Forecasts are scenarios, not promises.")
    st.markdown("**Data status**")
    st.warning("No live data feed or persistent database connected.")

st.header("1 · Dynamic investor requirements")
st.caption("Update these whenever your goals, available balance, time horizon or monthly contribution changes. These are analysis assumptions, not identity details.")
p = st.session_state.profile
with st.form("profile_form"):
    c1,c2,c3 = st.columns(3)
    objective = c1.selectbox("Primary objective", OBJECTIVES, index=OBJECTIVES.index(p["objective"]))
    horizon = c2.selectbox("Expected investment horizon", HORIZONS, index=HORIZONS.index(p["horizon"]))
    risk = c3.selectbox("Comfort with investment loss / volatility", RISK_LEVELS, index=RISK_LEVELS.index(p["risk"]))
    c4,c5,c6 = st.columns(3)
    cash_need = c4.number_input("Amount likely needed (₹; optional)", min_value=0.0, value=float(p["cash_need"]), step=1000.0)
    cash_need_date = c5.date_input("Expected date needed (optional)", value=p["cash_need_date"])
    monthly_contribution = c6.number_input("Planned monthly contribution (₹)", min_value=0.0, value=float(p["monthly_contribution"]), step=500.0)
    emergency_fund = st.selectbox("Emergency reserve status", ["Not specified", "Less than 1 month of expenses", "1–3 months", "3–6 months", "6+ months", "Prefer not to include"], index=["Not specified", "Less than 1 month of expenses", "1–3 months", "3–6 months", "6+ months", "Prefer not to include"].index(p["emergency_fund"]))
    notes = st.text_area("Other constraints (optional; no personal identifiers)", value=p["notes"], placeholder="Example: capital stability is important; avoid adding funds; only evaluate existing schemes.")
    profile_saved = st.form_submit_button("Save analysis assumptions")
if profile_saved:
    st.session_state.profile = {"objective":objective,"horizon":horizon,"risk":risk,"cash_need":cash_need,"cash_need_date":cash_need_date,"monthly_contribution":monthly_contribution,"emergency_fund":emergency_fund,"notes":notes}
    st.success("Assumptions updated for this session. They can be changed again at any time.")

st.header("2 · Dynamic portfolio holdings")
st.caption("Add, edit or delete funds. Keep the exact scheme name, plan and option consistent with the official statement. Do not enter folio numbers or account identifiers.")
holdings_input = st.data_editor(
    st.session_state.holdings_data,
    num_rows="dynamic", use_container_width=True, key="holdings_editor",
    column_config={
        "scheme_name": st.column_config.TextColumn("Scheme name *", required=True),
        "scheme_code": st.column_config.TextColumn("AMFI / scheme code (optional)"),
        "plan": st.column_config.SelectboxColumn("Plan", options=["Direct", "Regular", "Unknown"], required=True),
        "option": st.column_config.SelectboxColumn("Option", options=["Growth", "IDCW payout", "IDCW reinvestment", "Unknown"], required=True),
        "category": st.column_config.SelectboxColumn("Category", options=CATEGORIES, required=True),
        "units": st.column_config.NumberColumn("Units (optional)", min_value=0.0, step=0.001, format="%.3f"),
        "invested_amount_inr": st.column_config.NumberColumn("Invested amount (₹)", min_value=0.0, step=100.0, format="%.2f", required=True),
        "current_value_inr": st.column_config.NumberColumn("Current value (₹)", min_value=0.0, step=100.0, format="%.2f", required=True),
        "purpose": st.column_config.TextColumn("Goal / purpose"),
        "last_updated": st.column_config.TextColumn("Value as-of date (YYYY-MM-DD)"),
    })
st.session_state.holdings_data = holdings_input.copy()
valid_holdings = holdings_input.copy()
for col in ["invested_amount_inr", "current_value_inr", "units"]:
    valid_holdings[col] = pd.to_numeric(valid_holdings[col], errors="coerce")
valid_holdings = valid_holdings[valid_holdings["scheme_name"].fillna("").astype(str).str.strip().ne("")]
summary_df = valid_holdings.rename(columns={"scheme_name":"scheme", "invested_amount_inr":"invested", "current_value_inr":"current_value"})
if len(summary_df):
    summary = simple_portfolio_summary(summary_df)
    a,b,c,d = st.columns(4)
    a.metric("Invested amount", f"₹{summary['invested']:,.0f}")
    b.metric("Current value entered", f"₹{summary['current_value']:,.0f}")
    c.metric("Unrealised gain / loss", f"₹{summary['gain']:,.0f}")
    d.metric("Simple return", f"{summary['return_pct']:.2f}%" if summary['return_pct'] is not None else "—")
    st.caption("These KPIs are only as current as the values entered. Simple return is not XIRR and does not account for dated cash flows.")
else:
    st.info("Add at least one scheme row to see portfolio KPIs.")

c1,c2 = st.columns(2)
with c1:
    st.download_button("Download holdings CSV template / current holdings", valid_holdings.to_csv(index=False).encode("utf-8"), "mf_holdings.csv", "text/csv")
with c2:
    config = {"profile": {k:(v.isoformat() if hasattr(v,"isoformat") and v is not None else v) for k,v in st.session_state.profile.items()}, "holdings": valid_holdings.where(pd.notna(valid_holdings), None).to_dict(orient="records"), "note":"Contains no personal identifiers. Review before sharing."}
    st.download_button("Export analysis setup JSON", json.dumps(config, indent=2, default=str).encode("utf-8"), "mf_analysis_setup.json", "application/json")

st.subheader("Optional · Import holdings CSV")
imported = st.file_uploader("Import a previously exported holdings CSV", type=["csv"], key="holdings_import")
if imported is not None:
    try:
        incoming = pd.read_csv(imported)
        required = {"scheme_name", "invested_amount_inr", "current_value_inr"}
        if not required.issubset(incoming.columns):
            st.error("CSV needs at least scheme_name, invested_amount_inr and current_value_inr columns.")
        else:
            st.dataframe(incoming, use_container_width=True, hide_index=True)
            if st.button("Replace current holdings with imported file"):
                for col, default in {"scheme_code":"", "plan":"Unknown", "option":"Unknown", "category":"Other / not mapped", "units":None, "purpose":"", "last_updated":str(date.today())}.items():
                    if col not in incoming.columns: incoming[col] = default
                st.session_state.holdings_data = incoming[["scheme_name","scheme_code","plan","option","category","units","invested_amount_inr","current_value_inr","purpose","last_updated"]]
                st.rerun()
    except Exception as exc:
        st.error(f"Could not read holdings CSV: {exc}")

st.header("3 · Transaction ledger for XIRR and tax analysis")
st.caption("This is the schema for a future lot-level engine. Add dated transactions when available; never include folio IDs, PAN, bank details or investor names. Tax results will remain unavailable until rules and data are validated.")
transaction_template = pd.DataFrame(columns=["date", "scheme_name", "transaction_type", "amount_inr", "units", "nav", "exit_load_inr", "source_as_of"])
transactions = st.data_editor(transaction_template, num_rows="dynamic", use_container_width=True, key="transaction_ledger", column_config={
    "date":st.column_config.DateColumn("Transaction date", format="YYYY-MM-DD"),
    "scheme_name":st.column_config.TextColumn("Scheme name", required=True),
    "transaction_type":st.column_config.SelectboxColumn("Type", options=["Purchase", "SIP purchase", "Switch-in", "Redemption", "Switch-out", "Dividend / IDCW", "Other"], required=True),
    "amount_inr":st.column_config.NumberColumn("Cash flow amount (₹)", min_value=0.0, step=100.0),
    "units":st.column_config.NumberColumn("Units", min_value=0.0, step=0.001),
    "nav":st.column_config.NumberColumn("NAV (₹)", min_value=0.0, step=0.01),
    "exit_load_inr":st.column_config.NumberColumn("Exit load paid (₹; if known)", min_value=0.0, step=1.0),
    "source_as_of":st.column_config.TextColumn("Evidence / statement date")
})
st.download_button("Download transaction ledger template", transaction_template.to_csv(index=False).encode("utf-8"), "mf_transaction_ledger_template.csv", "text/csv")
st.info("The transaction grid is a data-capture template in this MVP. XIRR, tax lots, holding-period classification and redemption simulations are next-stage features, not yet calculated here.")

st.header("4 · Quantitative engine: import NAV history")
st.write("Upload CSV with columns **date, scheme, nav**. Use official AMFI/AMC data for real analysis. A clearly labelled synthetic sample is included in the project for demonstration only.")
with open("data/sample_nav_synthetic.csv", "rb") as sample_file:
    st.download_button("Download synthetic NAV sample (demo only)", sample_file, "sample_nav_synthetic.csv", "text/csv")
upload = st.file_uploader("Upload NAV history CSV", type=["csv"], key="nav_upload")
if upload:
    try:
        raw = pd.read_csv(upload)
        nav = clean_nav(raw)
        metrics = scheme_metrics(nav)
        st.success(f"Loaded {len(nav):,} valid NAV observations across {nav['scheme'].nunique()} schemes.")
        st.dataframe(metrics, use_container_width=True, hide_index=True)
        selected = st.selectbox("Plot scheme NAV", sorted(nav.scheme.unique()))
        plot = nav[nav.scheme == selected]
        st.plotly_chart(px.line(plot, x="date", y="nav", title=f"NAV history — {selected}"), use_container_width=True)
        st.download_button("Download calculated metrics CSV", metrics.to_csv(index=False).encode(), "mf_metrics.csv", "text/csv")
    except Exception as e:
        st.error(f"Could not process file: {e}")
else:
    st.info("No NAV data loaded. NAV metrics remain blank until valid data is imported.")

st.header("5 · 60/40 evidence scorecard")
st.write("Enter analyst scores only after reviewing the supporting evidence. Scores are inputs, not automated recommendations.")
if len(valid_holdings):
    with st.form("score_form"):
        scheme = st.selectbox("Scheme", valid_holdings["scheme_name"].tolist())
        qscore = st.slider("Quantitative score (0–100)", 0, 100, 50)
        qualscore = st.slider("Qualitative score (0–100)", 0, 100, 50)
        evidence = st.text_area("Evidence / rationale (source and as-of date required)", placeholder="Example: benchmark-relative performance, drawdown, expense ratio, portfolio quality, manager commentary...")
        submitted = st.form_submit_button("Calculate provisional score")
    if submitted:
        if len(evidence.strip()) < 20 or "http" not in evidence.lower() and "source:" not in evidence.lower():
            st.error("Add meaningful rationale and a source reference (URL or 'Source: ...') before calculating the score.")
        else:
            result = score_fund(qscore, qualscore)
            st.metric(f"Provisional 60/40 score — {scheme}", f"{result['combined_score']}/100")
            st.caption("User-assessed inputs · Not independently validated · Not a buy/sell signal")
            st.write("**Recorded rationale:**", evidence)
else:
    st.info("Add a holding before scoring a scheme.")

st.header("6 · Decision panel")
left,right = st.columns(2)
with left:
    st.markdown("**Actions to compare in later versions**")
    st.write("- Hold existing units\n- Redeem fully or partially\n- Switch, subject to tax and exit load\n- Redirect future contributions\n- Add a new fund and test overlap")
with right:
    st.markdown("**Checks required before a recommendation**")
    st.write("- Goal, horizon and cash requirement\n- Exact scheme, plan, option and category\n- Dated transaction lots / units\n- Exit load and applicable tax rules\n- Official NAV and factsheet freshness\n- Evidence source and confidence level")

st.header("7 · Source register")
st.markdown("- [AMFI NAV history](https://www.amfiindia.com/net-asset-value/nav-history) — NAV source and date checks\n- [Income Tax Department: Capital Gains](https://www.incometaxindia.gov.in/w/capital-gain) — tax rules must be versioned by transfer date and financial year\n- [SEBI mutual fund investor education](https://investor.sebi.gov.in/understanding_mf.html) — product and risk basics")
st.caption("Showcase limitations: no live data refresh, no persistent storage, no automated recommendation, and no verified tax engine. Synthetic data is for interaction testing only. Still to implement: benchmark mapping, fund overlap, news intelligence, lot-level XIRR, reviewed tax scenarios, alerts, tests, audit log and production security.")
