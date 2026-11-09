"""SawalSetu – Streamlit front end.

Runs the same RAG pipeline as the FastAPI backend in-process, so it deploys as a single
Python app on Streamlit Community Cloud. Configuration comes from st.secrets (on Cloud) or a
.env file / environment variables (locally); see .env.example for the keys.
"""
from __future__ import annotations

import asyncio
import html
import os
import re
import sys
from datetime import datetime
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "backend"))

# Streamlit Cloud keeps secrets in st.secrets; the backend reads environment variables.
try:
    for key, value in st.secrets.items():
        if isinstance(value, (str, int, float)) and key.isupper():
            os.environ.setdefault(key, str(value))
except Exception:  # no secrets.toml locally – that is fine
    pass
os.environ.setdefault("DATA_DIR", str(ROOT / "backend" / "data"))

from app.config import settings  # noqa: E402
from app.rag.documents import inr  # noqa: E402
from app.rag.llm import build_answerer  # noqa: E402
from app.rag.pipeline import Pipeline  # noqa: E402

SUGGESTIONS = [
    "Which party has the highest outstanding?",
    "Monthly sales vs purchases?",
    "Top 5 customers by sales?",
    "Which invoices are overdue?",
    "What are my payables this month?",
    "Sales trend in last 12 months?",
]

KIND_LABEL = {
    "analytics": "Summary", "sale_bill": "Sales invoice", "sale_order": "Sales order",
    "sale_challan": "Delivery challan", "purchase_bill": "Purchase bill", "purchase_order": "Purchase order",
    "purchase_return": "Purchase return", "ledger": "Party master", "item": "Item master",
    "ecom_order": "Marketplace order",
}

st.set_page_config(page_title="SawalSetu · Ask your books", page_icon="📒", layout="wide",
                   initial_sidebar_state="collapsed")

CSS = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..700;1,9..144,300..700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{--paper:#F6F1E7;--paper2:#EFE8DA;--paper3:#E7DFCD;--ink:#14201C;--muted:#5B6560;--faint:#8A918C;
--hair:#D9D0BF;--em:#0F5C4A;--emt:#E3EFE8;--saf:#E0862B;--red:#B3412E;}
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stAppViewContainer"]>section{background:var(--paper)!important;color:var(--ink)!important;}
[data-testid="stHeader"],#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important;}
.block-container{padding:1.6rem 2.2rem 6rem!important;max-width:1700px!important;}
html,body,[class*="css"],p,li,span,div,button,textarea,input{font-family:"Inter",system-ui,sans-serif;}
.ff{font-family:"Fraunces",Georgia,serif!important;font-variation-settings:"opsz" 72;}
.tab{font-variant-numeric:tabular-nums lining-nums;}
.wordmark{font-family:"Fraunces",serif;font-weight:700;font-size:46px;letter-spacing:-0.02em;line-height:1;color:var(--ink);}
.tagline{font-weight:600;font-size:14px;letter-spacing:.3em;text-transform:uppercase;margin-top:8px;}
.card{background:#FBF8F1;border:1px solid var(--hair);border-radius:14px;padding:18px 20px;}
.card h3{font-family:"Fraunces",serif;font-size:21px;font-weight:600;margin:0 0 12px;display:inline-block;border-bottom:2px solid var(--ink);padding-bottom:3px;}
.mb{font-weight:700;font-style:italic;font-size:21px;letter-spacing:-0.02em;}
.mb .m{color:#D7262C}.mb .b{color:#1F4E9C}.mb sup{font-size:9px;color:var(--muted);font-style:normal;margin-left:2px}
.pill{display:inline-flex;align-items:center;gap:7px;border-radius:999px;padding:5px 12px;font-size:13px;font-weight:600;color:#F6F1E7;background:var(--em);}
.pill.warn{background:var(--saf)}.pill i{width:8px;height:8px;border-radius:50%;background:#F6F1E7;display:inline-block}
.row{display:flex;align-items:baseline;gap:10px;font-size:16px;margin:7px 0;}
.row::after{content:"";flex:1;order:1;border-bottom:2px dotted var(--hair);transform:translateY(-4px)}
.row b{order:2;font-weight:600}
.h2{font-family:"Fraunces",serif;font-size:23px;font-weight:600;margin:4px 0 10px;}
.company{font-family:"Fraunces",serif;font-size:29px;font-weight:600;letter-spacing:-0.01em;}
.seg{display:inline-flex;border:1px solid var(--hair);border-radius:10px;padding:4px;background:#FBF8F1;font-size:17px;}
.seg span{padding:6px 20px;border-radius:7px;color:var(--ink)}.seg span.on{background:var(--em);color:#F6F1E7;font-weight:600}
.rule{border-bottom:1px solid var(--hair);margin:14px 0 22px;}
.q{border-left:4px solid var(--saf);padding-left:18px;margin:26px 0 18px;font-family:"Fraunces",serif;font-style:italic;font-weight:500;font-size:34px;line-height:1.2;color:var(--ink);}
.who{font-size:18px;margin:0 0 10px;color:var(--muted)}.who b{font-family:"Fraunces",serif;color:var(--em);font-weight:600}
[class*="st-key-ans"] p{font-size:18px!important;line-height:1.6;color:var(--ink)}
[class*="st-key-ans"] [data-testid="stMarkdownContainer"]>p:first-child{font-size:22px!important;line-height:1.45}
[class*="st-key-ans"] li{font-size:18px!important;line-height:1.6}[class*="st-key-ans"] li::marker{color:var(--em)}
[class*="st-key-ans"] blockquote{border-left:4px solid var(--em)!important;margin:1.1em 0 1.3em!important;padding:.5em 0 .5em 1.4rem!important;background:none!important}
[class*="st-key-ans"] blockquote p{margin:0!important}
[class*="st-key-ans"] blockquote,[class*="st-key-ans"] blockquote p,[class*="st-key-ans"] blockquote li{color:var(--ink)!important;opacity:1!important}
[class*="st-key-ans"] .big{color:var(--em)!important}
.big{display:block;font-family:"Fraunces",serif;font-weight:650;font-size:60px;line-height:1;color:var(--em);letter-spacing:-0.01em;font-variant-numeric:tabular-nums}
.lbl{display:block;font-family:"Inter",sans-serif;font-size:13px;font-weight:650;letter-spacing:.22em;text-transform:uppercase;color:var(--muted);margin-top:10px}
[class*="st-key-ans"] blockquote ul{margin:.7em 0 0 1.1em}[class*="st-key-ans"] blockquote li{font-size:19px!important;color:var(--ink)}
[class*="st-key-ans"] table{width:100%;border-collapse:collapse;font-size:18px;margin:.6em 0 1.2em}
[class*="st-key-ans"] thead tr{background:var(--paper2)}[class*="st-key-ans"] th{text-align:left;font-weight:650;padding:.6em .9em;border-bottom:1px solid var(--hair)}
[class*="st-key-ans"] td{padding:.65em .9em;border-bottom:1px solid var(--hair);font-variant-numeric:tabular-nums}
[class*="st-key-ans"] td:not(:first-child),[class*="st-key-ans"] th:not(:first-child){text-align:right}
.cite{display:inline-block;border:1.5px solid var(--em);border-radius:5px;color:var(--em);background:var(--paper);font-family:"JetBrains Mono",monospace;font-size:12px;font-weight:600;padding:1px 5px;margin:0 3px;vertical-align:.25em;line-height:1.2}
.kpis{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;}
.kpi{border:1px solid var(--hair);border-radius:12px;padding:14px 16px;background:#FBF8F1;min-width:0}
.kpi.on{background:var(--emt);border-color:#CDE0D6}
.kpi .l{font-size:12px;font-weight:650;letter-spacing:.12em;text-transform:uppercase;color:var(--muted);white-space:nowrap}
.kpi .v{font-family:"Fraunces",serif;font-weight:650;font-size:clamp(22px,2vw,34px);line-height:1.05;margin-top:8px;color:var(--ink);font-variant-numeric:tabular-nums;white-space:nowrap}
.kpi .d{margin-top:6px;font-size:15px;font-weight:650;color:var(--em)}.kpi .d.neg{color:var(--red)}
.ctitle{font-family:"Fraunces",serif;font-size:21px;font-weight:600;margin:0 0 4px}
.src{border:1px solid var(--hair);border-radius:12px;padding:12px 16px;margin:0 0 10px;background:#FBF8F1;display:grid;grid-template-columns:auto 1fr auto;gap:0 14px;align-items:start}
.src .n{border:1.5px solid var(--em);border-radius:5px;color:var(--em);font-family:"JetBrains Mono",monospace;font-size:13px;font-weight:600;padding:3px 6px;margin-top:2px}
.src .k{font-size:12px;font-weight:650;letter-spacing:.16em;text-transform:uppercase;color:var(--muted)}
.src .t{font-size:17px;font-weight:650;margin-top:3px;color:var(--ink)}
.src .x{font-size:14.5px;color:var(--muted);margin-top:4px;line-height:1.45}
.src .x b{color:var(--ink);font-weight:600;font-variant-numeric:tabular-nums}
.src .kv{text-align:right;font-size:15px;white-space:nowrap;color:var(--muted)}.src .kv b{color:var(--ink);font-weight:650;display:block;font-variant-numeric:tabular-nums}
.foot{display:flex;justify-content:space-between;align-items:center;border-top:1px solid var(--hair);padding-top:14px;margin-top:18px;font-size:14px;color:var(--ink)}
div.stButton>button{width:100%;justify-content:flex-start;text-align:left;background:#FBF8F1;border:1px solid rgba(20,32,28,.3);border-radius:10px;color:var(--ink);font-size:16px;padding:.7rem 1rem;font-weight:500;line-height:1.3}
div.stButton>button:hover{border-color:var(--em);background:var(--emt);color:var(--em)}
div.stButton>button p{font-size:16px;white-space:normal;text-align:left;overflow:visible;text-overflow:clip}
div.stButton>button{white-space:normal;height:auto;min-height:0}
div.stButton>button div{white-space:normal;overflow:visible}
div.stButton>button[kind="primary"]{background:var(--paper);border:1px solid rgba(20,32,28,.4);justify-content:center}
[data-testid="stChatInput"]{background:#FBF8F1!important;border:1px solid var(--hair)!important;border-radius:999px!important}
[data-testid="stChatInput"] textarea{font-size:17px!important;color:var(--ink)!important}
[data-testid="stChatInput"] textarea::placeholder{color:var(--muted)!important}
[data-testid="stChatInput"] button{background:var(--em)!important;border-radius:50%!important;color:#F6F1E7!important}
[data-testid="stBottom"]>div,[data-testid="stBottomBlockContainer"]{background:var(--paper)!important}
.hint{font-size:14px;color:var(--muted);margin-top:6px}
.empty h1{font-family:"Fraunces",serif;font-size:44px;font-weight:600;line-height:1.05;letter-spacing:-0.01em;margin:10px 0 14px}
.empty h1 em{font-weight:300;color:var(--muted)}
.empty p{font-size:19px;color:var(--muted);max-width:620px;line-height:1.5}
</style>
"""
st.html(CSS)


@st.cache_resource(show_spinner="Reading your MargBooks data…")
def get_pipeline() -> Pipeline:
    p = Pipeline(settings)
    if not p.status()["ready"] and settings.margbooks_mode != "live":
        asyncio.run(p.sync())
    return p


pipeline = get_pipeline()
status = pipeline.status()
kpis = pipeline.kpis or {}

if "messages" not in st.session_state:
    st.session_state.messages = []
if "pending" not in st.session_state:
    st.session_state.pending = None


def esc(s: object) -> str:
    return html.escape(str(s))


def short_inr(v: float | None) -> str:
    if v is None:
        return "—"
    a = abs(v)
    if a >= 1e7:
        return f"₹{v / 1e7:.2f} Cr"
    if a >= 1e5:
        return f"₹{v / 1e5:.1f} L"
    return inr(v)


def short_month(label: str | None) -> str:
    return f"{label[:3]} {label[-4:]}" if label else ""


def relative(iso: str | None) -> str:
    if not iso:
        return "never"
    mins = int((datetime.now().astimezone() - datetime.fromisoformat(iso)).total_seconds() // 60)
    if mins < 1:
        return "just now"
    if mins < 60:
        return f"{mins} min ago"
    return f"{mins // 60} h ago" if mins < 1440 else f"{mins // 1440} d ago"


def render_answer(text: str) -> str:
    """Markdown with [n] citations turned into chips and the headline blockquote marked up."""
    text = re.sub(r"\[(\d{1,2})\](?!\()", lambda m: f'<span class="cite">[{m.group(1)}]</span>', text)
    text = re.sub(
        r"^> (₹[^\n_]+?)\s*\n> _([^_\n]+)_\s*\n",
        lambda m: f'> <span class="big">{m.group(1).strip()}</span><span class="lbl">{m.group(2).strip()}</span>\n',
        text,
        flags=re.M,
    )
    return text


def highlight(text: str) -> str:
    return re.sub(r"(₹[\d,\.]+(?:\s?(?:L|Cr))?|\b\d[\d,\.]*%?)", r"<b>\1</b>", esc(text))


def source_card(s: dict) -> str:
    md = s.get("metadata") or {}
    kv = ""
    if s["kind"] == "analytics" and md.get("pending") is not None:
        kv = f'<div class="kv">Outstanding<b>{short_inr(md["pending"])}</b></div>'
    elif md.get("amount"):
        kv = f'<div class="kv">Amount<b>{short_inr(md["amount"])}</b></div>'
    snippet = " ".join(re.split(r"(?<=[.!?])\s+", s["text"].strip())[:2])
    return (
        f'<div class="src"><span class="n">[{s["n"]}]</span><div><div class="k">{esc(KIND_LABEL.get(s["kind"], s["kind"]))}</div>'
        f'<div class="t">{esc(s["title"])}</div><div class="x">{highlight(snippet)}</div></div>{kv}</div>'
    )


LLM_TIMEOUT_S = 90


@st.cache_resource(ttl=600, show_spinner=False)
def llm_health(provider: str, key_fingerprint: str) -> tuple[bool, str]:
    """Cheap, cached check that the configured LLM key actually works (shown in the footer)."""
    import httpx

    try:
        if provider == "groq":
            from app.rag.llm import GroqAnswerer

            answerer = GroqAnswerer(settings)
            model = answerer.resolve_model()
            note = "" if model == settings.groq_model else f" (GROQ_MODEL '{settings.groq_model}' unavailable)"
            return True, f"Groq · {model}{note}"
        if provider == "claude":
            return True, f"Claude · {settings.claude_model}"
        return False, "Offline mode – add GROQ_API_KEY in secrets for written answers"
    except Exception as exc:  # network problems etc.
        return False, f"Cannot reach {provider}: {exc}"


def answer_stream(question: str, history: list[dict], placeholder, sources_box) -> tuple[str, list[dict]]:
    """Stream the pipeline's answer into a placeholder; returns (text, sources).

    If the model call fails or exceeds LLM_TIMEOUT_S, the error is shown and the offline
    (retrieval-only) answer is rendered instead, so the user is never left waiting.
    """
    pipeline.answerer = build_answerer(settings)  # fresh async client per event loop
    provider = pipeline.answerer.name
    buf: list[str] = []
    sources: list[dict] = []
    started = datetime.now()

    def paint(suffix: str = " ▍") -> None:
        placeholder.markdown(render_answer("".join(buf)) + suffix, unsafe_allow_html=True)

    async def consume(gen) -> None:
        async for ev in gen:
            if ev["type"] == "sources":
                sources.extend(ev["sources"])
                sources_box.html("".join(source_card(s) for s in sources[:6]))
            elif ev["type"] == "token":
                buf.append(ev["text"])
                paint()
            elif ev["type"] == "error":
                raise RuntimeError(ev["message"])

    async def run() -> None:
        await asyncio.wait_for(consume(pipeline.answer(question, history)), timeout=LLM_TIMEOUT_S)

    placeholder.markdown(f"_Thinking with {provider.title()}…_" if provider != "offline" else "_Reading your books…_")
    try:
        asyncio.run(run())
    except Exception as exc:
        elapsed = (datetime.now() - started).total_seconds()
        reason = f"{provider.title()} timed out after {elapsed:.0f}s" if isinstance(exc, asyncio.TimeoutError) else f"{provider.title()} error: {exc}"
        buf.clear()
        buf.append(f"_⚠ {reason}. Showing the matching MargBooks passages instead._\n\n")
        docs = [d for d, _ in pipeline.retrieve(question)]
        from app.rag.llm import OfflineAnswerer

        async def fallback() -> None:
            async for ev in OfflineAnswerer(settings).stream(question, docs, history):
                if ev["type"] == "token":
                    buf.append(ev["text"])
                    paint()

        asyncio.run(fallback())
    text = "".join(buf)
    placeholder.markdown(render_answer(text), unsafe_allow_html=True)
    return text, sources


# ------------------------------------------------------------------ layout
left, center, right = st.columns([1.0, 2.15, 1.45], gap="large")

with left:
    st.html('<div class="wordmark">SawalSetu</div><div class="tagline">Ask your books</div><div style="height:22px"></div>')
    counts = status.get("counts", {})
    pill_cls = "pill" if status["ready"] else "pill warn"
    pill_txt = f"Synced {relative(status['last_sync'])}" if status["ready"] else "Not synced"
    st.html(
        f'<div class="card"><h3>Data Source</h3>'
        f'<div style="display:flex;justify-content:space-between;align-items:center;gap:10px">'
        f'<span class="mb"><span class="m">Marg</span><span class="b">Books</span><sup>®</sup></span>'
        f'<span class="{pill_cls}"><i></i>{pill_txt}</span></div>'
        f'<div style="margin-top:14px">'
        + "".join(
            f'<div class="row"><span>{label}</span><b class="tab">{counts.get(k, 0):,}</b></div>'
            for k, label in (("sale_bills", "Sales invoices"), ("purchase_bills", "Purchase bills"),
                             ("ledgers", "Parties"), ("items", "Items"))
        )
        + "</div></div>"
    )
    if st.button("⟳  Sync now", type="primary", use_container_width=True):
        with st.spinner("Pulling data from MargBooks…"):
            try:
                asyncio.run(pipeline.sync())
                st.rerun()
            except Exception as exc:  # surface connector errors
                st.error(str(exc))
    st.html('<div style="height:10px"></div><div class="h2">Ask about</div>')
    for q in SUGGESTIONS:
        if st.button(f"🔍  {q}", key=f"sug-{q}"):
            st.session_state.pending = q
            st.rerun()
    fy_start = datetime.now().year if datetime.now().month >= 4 else datetime.now().year - 1
    llm = status["llm"]
    ok, llm_label = llm_health(llm["provider"], (settings.groq_api_key or settings.anthropic_api_key)[-6:])
    st.html(
        f'<div class="foot"><span>🏪&nbsp; {esc(status["company"])} · FY {fy_start}-{str(fy_start + 1)[-2:]}</span><span>⚙</span></div>'
        f'<div class="hint" style="color:{"#0F5C4A" if ok else "#B3412E"}">{"●" if ok else "▲"} {esc(llm_label)}</div>'
    )

with right:
    delta = None
    if kpis.get("prev_month_sales"):
        delta = (kpis["last_month_sales"] - kpis["prev_month_sales"]) / kpis["prev_month_sales"] * 100
    delta_html = (
        f'<div class="d {"neg" if delta < 0 else ""}">{"▲" if delta >= 0 else "▼"} {abs(delta):.1f}%</div>' if delta is not None else ""
    )
    st.html(
        f'<div class="kpis">'
        f'<div class="kpi on"><div class="l">Sales {esc(short_month(kpis.get("last_month_label"))[:3])}</div><div class="v">{short_inr(kpis.get("last_month_sales"))}</div>{delta_html}</div>'
        f'<div class="kpi"><div class="l">Receivables</div><div class="v">{short_inr(kpis.get("receivables"))}</div></div>'
        f'<div class="kpi"><div class="l">Payables</div><div class="v">{short_inr(kpis.get("payables"))}</div></div>'
        f'</div><div style="height:16px"></div>'
    )
    monthly = kpis.get("monthly") or []
    if monthly:
        df = pd.DataFrame(monthly)
        df["Sales"] = df["sales"] / 1e5
        df["Purchases"] = df["purchases"] / 1e5
        long = df.melt(id_vars=["label"], value_vars=["Sales", "Purchases"], var_name="Series", value_name="lakh")
        chart = (
            alt.Chart(long)
            .mark_line(point=alt.OverlayMarkDef(filled=False, fill="#F6F1E7", size=45, strokeWidth=2), strokeWidth=2.5)
            .encode(
                x=alt.X("label:N", sort=list(df["label"]), title=None,
                        axis=alt.Axis(labelFont="JetBrains Mono", labelFontSize=12, labelColor="#5B6560",
                                      domainColor="#D9D0BF", tickColor="#D9D0BF", labelAngle=0,
                                      labelExpr="slice(datum.label, 0, 3)")),
                y=alt.Y("lakh:Q", title=None,
                        axis=alt.Axis(labelExpr="format(datum.value, '.0f') + ' L'", labelFont="Inter",
                                      labelFontSize=12, labelColor="#5B6560", grid=False, domainColor="#D9D0BF",
                                      tickColor="#D9D0BF")),
                color=alt.Color("Series:N", scale=alt.Scale(domain=["Sales", "Purchases"], range=["#0F5C4A", "#E0862B"]),
                                legend=alt.Legend(title=None, orient="top", direction="horizontal", labelFont="Inter",
                                                  labelFontSize=14, symbolType="stroke", symbolStrokeWidth=3)),
                tooltip=[alt.Tooltip("label:N", title="Month"), alt.Tooltip("Series:N"),
                         alt.Tooltip("lakh:Q", title="₹ lakh", format=".1f")],
            )
            .properties(height=230, title=alt.TitleParams("Sales vs Purchases (Last 12 Months)", font="Fraunces",
                                                           fontSize=21, fontWeight=600, color="#14201C", anchor="start"))
            .configure_view(strokeWidth=0)
            .configure(background="transparent")
        )
        st.altair_chart(chart, use_container_width=True)
    st.html('<div class="ctitle">Sources for this answer</div>')
    sources_box = st.empty()

with center:
    st.html(
        f'<div style="display:flex;justify-content:space-between;align-items:center">'
        f'<span class="company">{esc(status["company"])}</span>'
        f'<span class="seg"><span class="on">Answers</span><span>Evidence</span></span></div><div class="rule"></div>'
    )
    msgs = st.session_state.messages
    if not msgs and not st.session_state.pending:
        st.html(
            '<div class="empty"><h1>Ask your books <em>anything.</em></h1>'
            "<p>Sales, udhaar, suppliers, items. Every number comes with the MargBooks record behind it.</p></div>"
        )
    latest_sources: list[dict] = []
    for i, m in enumerate(msgs):
        if m["role"] == "user":
            st.html(f'<div class="q">{esc(m["content"])}</div>')
        else:
            st.html(f'<div class="who"><b>SawalSetu</b> · Today, {m["at"]}</div>')
            with st.container(key=f"ans-{i}"):
                st.markdown(render_answer(m["content"]), unsafe_allow_html=True)
            latest_sources = m.get("sources") or []

    pending = st.session_state.pending
    if pending:
        st.session_state.pending = None
        st.html(f'<div class="q">{esc(pending)}</div>')
        now = datetime.now().strftime("%I:%M %p").lstrip("0")
        st.html(f'<div class="who"><b>SawalSetu</b> · Today, {now}</div>')
        with st.container(key=f"ans-live-{len(msgs)}"):
            placeholder = st.empty()
        history = [{"role": m["role"], "content": m["content"]} for m in msgs]
        text, sources = answer_stream(pending, history, placeholder, sources_box)
        msgs.append({"role": "user", "content": pending, "at": now})
        msgs.append({"role": "assistant", "content": text, "sources": sources, "at": now})
        latest_sources = sources
    elif latest_sources:
        sources_box.html("".join(source_card(s) for s in latest_sources[:6]))
    else:
        rows = kpis.get("receivables_rows") or []
        sources_box.html(
            '<div class="x" style="color:#5B6560;font-size:15px;margin-bottom:10px">Ask a question to see the passages behind the answer. Largest outstanding balances right now:</div>'
            + "".join(
                f'<div class="src"><span class="n">{i + 1}</span><div><div class="k">Customer</div><div class="t">{esc(r["party"])}</div>'
                f'<div class="x">{esc(r["invoices"])} unpaid invoices{" · <b style=color:#B3412E>" + short_inr(r["overdue"]) + " overdue</b>" if r["overdue"] else ""}</div></div>'
                f'<div class="kv">Outstanding<b>{short_inr(r["pending"])}</b></div></div>'
                for i, r in enumerate(rows[:5])
            )
        )

question = st.chat_input("Ask anything about your books… e.g. kis party ka udhaar sabse zyada hai?")
if question:
    st.session_state.pending = question
    st.rerun()
