"""Hệ thiết kế của giao diện (design tokens + component) — phong cách hệ thống quản trị rủi ro ngân hàng.

Token lấy theo slide đề án: navy đậm + vàng đồng; chữ Montserrat (tiêu đề) và Be Vietnam Pro (nội dung).
Mọi trang dùng các hàm ở đây thay vì tự viết HTML/CSS, để giao diện nhất quán. Tài liệu: docs/design_system.md.
"""

from __future__ import annotations

import html
from urllib.parse import quote

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# ---------------------------------------------------------------------------
# 1. Design tokens
# ---------------------------------------------------------------------------
T = {
    "navy900": "#0F1E3A", "navy800": "#1B2B4B", "navy700": "#1B3A6B", "navy100": "#E7EDF7", "navy50": "#F3F6FB",
    "gold600": "#8C6A14", "gold500": "#B8902F", "gold300": "#D9B35A", "gold50": "#FBF6EA",
    "bg": "#F4F6FA", "surface": "#FFFFFF", "border": "#E3E8F0", "grid": "#E9EDF3",
    "text": "#14213D", "text2": "#4A5873", "muted": "#627089",
    "good": "#1A7F37", "good_bg": "#E8F5EC", "warn": "#9A6700", "warn_bg": "#FFF6DB",
    "bad": "#B42318", "bad_bg": "#FDECEA", "info": "#1B3A6B", "info_bg": "#E7EDF7",
}
# Bảng màu phân loại (thứ tự cố định) — validate_palette.js: ALL CHECKS PASS (light), 3 màu đầu đạt cả chế độ mọi cặp
SERIES = ["#2D66AD", "#B07D18", "#1B9A84", "#D0593C", "#7C5CB0", "#D9669C"]
SEQ = ["#EEF3FA", "#B4C9E7", "#6A91C7", "#2D66AD", "#1B3B66", "#0F1E3A"]
FONT_BODY = "Be Vietnam Pro, Segoe UI, Arial, sans-serif"
FONT_HEAD = "Montserrat, Be Vietnam Pro, Segoe UI, Arial, sans-serif"
PORT_COLOR = {"VN100": SERIES[0], "VN50_SP50": SERIES[1], "SP100": SERIES[2]}

ICON = {  # icon SVG nét mảnh (kiểu Lucide), màu kế thừa currentColor
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="M12 8v8" opacity=".55"/>',
    "layers": '<path d="m12 2 9 5-9 5-9-5 9-5z"/><path d="m3 12 9 5 9-5"/><path d="m3 17 9 5 9-5"/>',
    "target": '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="5"/><circle cx="12" cy="12" r="1.5"/>',
    "db": '<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v6c0 1.7 3.6 3 8 3s8-1.3 8-3V5"/><path d="M4 11v6c0 1.7 3.6 3 8 3s8-1.3 8-3v-6"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "chart": '<path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-6"/>',
    "play": '<polygon points="7 4 19 12 7 20 7 4"/>',
    "book": '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5z"/><path d="M4 19.5V21h16"/>',
    "alert": '<path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
}


def icon(name: str, size: int = 20, color: str = "#1B2B4B", stroke: float = 2) -> str:
    """Icon SVG nhúng dạng ảnh data-URI (st.html lọc thẻ <svg> trực tiếp nhưng giữ <img>)."""
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" stroke="{color}" '
           f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">{ICON[name]}</svg>')
    return f'<img src="data:image/svg+xml;utf8,{quote(svg)}" width="{size}" height="{size}" alt="" style="display:block">'


def num(x: float, d: int = 1, suffix: str = "", sign: bool = False) -> str:
    """Định dạng số kiểu Việt Nam: dấu phẩy thập phân, dấu chấm hàng nghìn."""
    s = f"{x:+,.{d}f}" if sign else f"{x:,.{d}f}"
    return s.replace(",", "§").replace(".", ",").replace("§", ".") + suffix


# ---------------------------------------------------------------------------
# 2. CSS toàn cục (gọi một lần ở app.py)
# ---------------------------------------------------------------------------
CSS = f"""
<style>
.block-container {{ padding-top: 4.5rem !important; padding-bottom: 3rem; max-width: 1320px; }}
h1, h2, h3, h4 {{ letter-spacing: -0.01em; color: {T['text']}; }}
[data-testid="stSidebar"] {{ border-right: 1px solid {T['navy800']}; }}
[data-testid="stSidebarNav"] span {{ font-weight: 500; }}
[data-testid="stSidebarNavSeparator"] {{ border-color: #2A3B5E; }}
[data-testid="stExpander"] details {{ border-radius: 10px; background: {T['surface']}; }}
[data-testid="stMetric"] {{ background: {T['surface']}; border: 1px solid {T['border']}; border-radius: 12px; padding: 14px 16px; }}
div[data-testid="stTabs"] button[role="tab"] p {{ font-weight: 600; }}
.stButton > button[kind="primary"] {{ background: {T['navy700']}; border-color: {T['navy700']}; }}
.stButton > button[kind="primary"]:hover {{ background: {T['navy900']}; border-color: {T['navy900']}; }}

.mr-hero {{ display: flex; gap: 22px; align-items: center; margin: 0 0 18px 0; }}
.mr-hero .shield {{ flex: 0 0 64px; height: 64px; border-radius: 50%; background: {T['navy800']}; color: #fff;
                    display: flex; align-items: center; justify-content: center; }}
.mr-eyebrow {{ font: 700 12px/1.2 {FONT_HEAD}; letter-spacing: .22em; text-transform: uppercase; color: {T['gold600']}; }}
.mr-title {{ font: 700 30px/1.2 {FONT_HEAD}; color: {T['navy800']}; margin: 6px 0 4px; }}
.mr-sub {{ font: italic 400 15px/1.4 {FONT_BODY}; color: {T['text2']}; }}

.mr-section {{ display: flex; align-items: center; gap: 12px; margin: 26px 0 12px; }}
.mr-section .dot {{ width: 34px; height: 34px; border-radius: 50%; background: {T['gold500']}; color: #fff;
                    display: flex; align-items: center; justify-content: center; flex: 0 0 34px; }}
.mr-section .t {{ font: 700 19px/1.2 {FONT_HEAD}; color: {T['navy800']}; }}
.mr-section .s {{ font: 400 13px/1.3 {FONT_BODY}; color: {T['muted']}; margin-left: 4px; }}

.mr-grid {{ display: grid; gap: 14px; grid-template-columns: repeat(var(--n, 4), minmax(0, 1fr)); margin: 6px 0 8px; }}
@media (max-width: 900px) {{ .mr-grid {{ grid-template-columns: repeat(2, minmax(0, 1fr)); }} }}
@media (max-width: 560px) {{ .mr-grid {{ grid-template-columns: 1fr; }} }}
.mr-kpi {{ background: {T['surface']}; border: 1px solid {T['border']}; border-radius: 12px; padding: 16px 18px;
           box-shadow: 0 1px 2px rgba(16,24,40,.05); position: relative; overflow: hidden; }}
.mr-kpi::before {{ content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 4px; background: var(--accent, {T['navy700']}); }}
.mr-kpi .l {{ font: 600 11.5px/1.3 {FONT_BODY}; letter-spacing: .08em; text-transform: uppercase; color: {T['muted']}; }}
.mr-kpi .v {{ font: 700 26px/1.2 {FONT_HEAD}; color: {T['navy800']}; margin: 8px 0 6px; }}
.mr-kpi .n {{ font: 400 13px/1.45 {FONT_BODY}; color: {T['text2']}; }}

.mr-pill {{ display: inline-flex; align-items: center; gap: 6px; padding: 3px 10px; border-radius: 999px;
            font: 600 12.5px/1.4 {FONT_BODY}; max-width: 100%; }}
.mr-pill.good {{ background: {T['good_bg']}; color: {T['good']}; }}
.mr-pill.warn {{ background: {T['warn_bg']}; color: {T['warn']}; }}
.mr-pill.bad  {{ background: {T['bad_bg']};  color: {T['bad']}; }}
.mr-pill.info {{ background: {T['info_bg']}; color: {T['info']}; }}

.mr-navy {{ background: {T['navy800']}; color: #E6EBF3; border-radius: 14px; padding: 22px 24px; height: 100%; }}
.mr-navy h4 {{ color: #fff; font: 700 19px/1.2 {FONT_HEAD}; margin: 0 0 14px; display: flex; gap: 10px; align-items: center; }}
.mr-navy .it {{ display: flex; gap: 14px; margin: 14px 0; }}
.mr-navy .num {{ flex: 0 0 32px; height: 32px; border-radius: 50%; background: {T['gold500']}; color: #fff;
                 font: 700 15px/32px {FONT_HEAD}; text-align: center; }}
.mr-navy .tt {{ font: 600 14.5px/1.4 {FONT_BODY}; color: #fff; }}
.mr-navy .dd {{ font: 400 13px/1.5 {FONT_BODY}; color: #C9D3E4; margin-top: 3px; }}

.mr-card {{ background: {T['surface']}; border: 1px solid {T['border']}; border-radius: 14px; padding: 18px 20px; height: 100%; }}
.mr-card ul {{ margin: 4px 0 0 0; padding-left: 0; list-style: none; }}
.mr-card li {{ display: flex; gap: 10px; align-items: flex-start; padding: 8px 0; border-bottom: 1px dashed {T['border']};
               font: 400 14.5px/1.5 {FONT_BODY}; color: {T['text']}; }}
.mr-card li:last-child {{ border-bottom: 0; }}
.mr-card li .ok {{ color: {T['good']}; flex: 0 0 18px; margin-top: 3px; }}

.mr-callout {{ background: {T['gold50']}; border: 1px solid #EFE2BF; border-left: 4px solid {T['gold500']}; border-radius: 10px;
               padding: 14px 18px; margin: 8px 0 14px; font: 400 14.5px/1.6 {FONT_BODY}; color: {T['text']}; }}
.mr-callout b.h {{ font-family: {FONT_HEAD}; color: {T['navy800']}; display: block; margin-bottom: 4px; }}

.mr-source {{ background: {T['navy50']}; border: 1px solid {T['border']}; border-radius: 12px; padding: 14px 18px;
              display: flex; gap: 14px; align-items: center; margin-top: 26px; font: 400 13px/1.6 {FONT_BODY}; color: {T['text2']}; }}
.mr-source .ic {{ flex: 0 0 40px; height: 40px; border-radius: 50%; background: {T['navy800']}; color: #fff;
                  display: flex; align-items: center; justify-content: center; }}
.mr-source b {{ color: {T['navy800']}; }}

.mr-brand {{ display: flex; gap: 10px; align-items: center; padding: 4px 2px 12px; }}
.mr-brand .b1 {{ font: 700 14px/1.2 {FONT_HEAD}; color: #fff; }}
.mr-brand .b2 {{ font: 600 10.5px/1.3 {FONT_BODY}; letter-spacing: .14em; text-transform: uppercase; color: {T['gold300']}; }}
</style>
"""


def inject_css() -> None:
    st.html(CSS)


# ---------------------------------------------------------------------------
# 3. Component
# ---------------------------------------------------------------------------
def page_header(title: str, subtitle: str = "", eyebrow: str = "Đề án 03 · Quản trị rủi ro", ic: str = "shield") -> None:
    st.html(f'<div class="mr-hero"><div class="shield">{icon(ic, 30, "#fff", 2)}</div><div>'
            f'<div class="mr-eyebrow">{html.escape(eyebrow)}</div><div class="mr-title">{html.escape(title)}</div>'
            f'<div class="mr-sub">{html.escape(subtitle)}</div></div></div>')


def section(title: str, ic: str = "layers", sub: str = "") -> None:
    s = f'<span class="s">{html.escape(sub)}</span>' if sub else ""
    st.html(f'<div class="mr-section"><div class="dot">{icon(ic, 18, "#fff", 2.2)}</div>'
            f'<div class="t">{html.escape(title)}</div>{s}</div>')


def pill(kind: str, text: str) -> str:
    """Huy hiệu trạng thái: luôn có biểu tượng + chữ (không chỉ dựa vào màu)."""
    sym = {"good": "✓", "warn": "!", "bad": "✕", "info": "i"}[kind]
    return f'<span class="mr-pill {kind}">{sym} {html.escape(text)}</span>'


def kpis(items: list[dict]) -> None:
    """items: dict(label, value, note, accent, pill=(kind, text))."""
    cards = []
    for it in items:
        badge = pill(*it["pill"]) if it.get("pill") else ""
        cards.append(f'<div class="mr-kpi" style="--accent:{it.get("accent", T["navy700"])}"><div class="l">{html.escape(it["label"])}</div>'
                     f'<div class="v">{html.escape(str(it["value"]))}</div><div class="n">{it.get("note", "")} {badge}</div></div>')
    st.html(f'<div class="mr-grid" style="--n:{min(len(cards), 4)}">{"".join(cards)}</div>')


def navy_panel(title: str, items: list[tuple[str, str]], ic: str = "target") -> None:
    rows = "".join(f'<div class="it"><div class="num">{i}</div><div><div class="tt">{html.escape(a)}</div>'
                   f'<div class="dd">{b}</div></div></div>' for i, (a, b) in enumerate(items, 1))
    st.html(f'<div class="mr-navy"><h4>{icon(ic, 22, "#fff")} {html.escape(title)}</h4>{rows}</div>')


def check_card(title: str, items: list[str], ic: str = "layers") -> None:
    lis = "".join(f'<li><span class="ok">{icon("check", 18, T["good"], 2.6)}</span><span>{x}</span></li>' for x in items)
    st.html(f'<div class="mr-card"><div class="mr-section" style="margin-top:0"><div class="dot">{icon(ic, 18, "#fff", 2.2)}</div>'
            f'<div class="t">{html.escape(title)}</div></div><ul>{lis}</ul></div>')


def callout(text_md: str, heading: str = "Kết luận chính") -> None:
    body = html.escape(text_md).replace("\n", "<br>")
    for tag in ("**",):
        parts = body.split(tag)
        body = "".join(p if i % 2 == 0 else f"<b>{p}</b>" for i, p in enumerate(parts))
    st.html(f'<div class="mr-callout"><b class="h">{html.escape(heading)}</b>{body}</div>')


def source_bar() -> None:
    st.html(f'<div class="mr-source"><div class="ic">{icon("db", 20, "#fff")}</div><div>'
            '<b>Nguồn dữ liệu:</b> Investing.com (giá đóng cửa VN-Index, S&amp;P 500, USD/VND) · IMF IFS (CPI, 2010 = 100) · giá S&amp;P 500 khớp FRED SP500 (lệch tối đa 0,0024%, T0b)<br>'
            '<b>Tài liệu nền:</b> <i>Bollerslev (1986), J. of Econometrics · Kupiec (1995), J. of Derivatives · '
            'Christoffersen (1998), Int. Economic Review</i></div></div>')


LOGO_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="236" height="44" viewBox="0 0 236 44"><circle cx="22" cy="22" r="20" fill="#B8902F"/>'
            '<path d="M22 33s8-4 8-10v-7l-8-3-8 3v7c0 6 8 10 8 10z" fill="none" stroke="#fff" stroke-width="2.2" stroke-linejoin="round"/>'
            '<text x="52" y="20" font-family="Montserrat, Segoe UI, Arial" font-weight="700" font-size="14" fill="#FFFFFF">VaR · ES · Backtesting</text>'
            '<text x="52" y="36" font-family="Segoe UI, Arial" font-weight="600" font-size="10" letter-spacing="1.6" fill="#D9B35A">ĐỀ ÁN 03 · UEL</text></svg>')


def logo() -> None:
    """Logo ở đầu thanh bên (st.logo), phía trên menu điều hướng."""
    from pathlib import Path

    f = Path(__file__).parent / "static" / "logo.svg"
    if not f.exists():
        f.write_text(LOGO_SVG, encoding="utf-8")
    st.logo(str(f), size="large")


def sidebar_brand() -> None:
    st.sidebar.html(f'<div class="mr-brand"><div style="width:38px;height:38px;border-radius:50%;background:{T["gold500"]};'
                    f'display:flex;align-items:center;justify-content:center">{icon("shield", 20, "#fff")}</div>'
                    '<div><div class="b1">VaR · ES · Backtesting</div><div class="b2">Đề án 03 · UEL</div></div></div>')


# ---------------------------------------------------------------------------
# 4. Biểu đồ & bảng
# ---------------------------------------------------------------------------
pio.templates["nganhang"] = go.layout.Template(layout=go.Layout(
    font=dict(family=FONT_BODY, size=13, color=T["text"]), colorway=SERIES,
    title=dict(font=dict(family=FONT_HEAD, size=16, color=T["navy800"]), x=0, xanchor="left"),
    paper_bgcolor=T["surface"], plot_bgcolor=T["surface"],
    xaxis=dict(gridcolor=T["grid"], linecolor=T["border"], zerolinecolor=T["border"], tickfont=dict(color=T["text2"])),
    yaxis=dict(gridcolor=T["grid"], linecolor=T["border"], zerolinecolor="#C9D2E0", tickfont=dict(color=T["text2"])),
    legend=dict(orientation="h", yanchor="top", y=-0.1, x=0, font=dict(size=12.5, color=T["text2"]), title_text=""),
    hoverlabel=dict(bgcolor="#FFFFFF", bordercolor=T["navy700"], font=dict(family=FONT_BODY, color=T["text"])),
    margin=dict(l=12, r=12, t=56, b=20)))
pio.templates.default = "nganhang"


def style(fig: go.Figure, height: int = 420, pct: bool = False, title: str | None = None) -> go.Figure:
    fig.update_layout(template="nganhang", height=height, hovermode="x unified")
    if title:
        fig.update_layout(title_text=title)
    if pct:
        fig.update_yaxes(tickformat=".1%")
    fig.update_traces(selector=dict(type="scatter", mode="lines"), line=dict(width=1.8))
    return fig


def table(df: pd.DataFrame, pct: list[str] | None = None, p: list[str] | None = None, num: list[str] | None = None,
          rename: dict | None = None, height: int | None = None) -> None:
    """Bảng dễ đọc: đổi tên cột tiếng Việt, % có 2 chữ số, p-value 3 chữ số, ẩn chỉ số dòng."""
    d = df.copy()
    cfg = {}
    for c in pct or []:
        if c in d:
            d[c] = d[c] * 100
            cfg[c] = st.column_config.NumberColumn(format="%.2f %%")
    for c in p or []:
        if c in d:
            cfg[c] = st.column_config.NumberColumn(format="%.3f")
    for c in num or []:
        if c in d:
            cfg[c] = st.column_config.NumberColumn(format="%.3f")
    if rename:
        d = d.rename(columns=rename)
        cfg = {rename.get(k, k): v for k, v in cfg.items()}
    kw = {"height": height} if height else {}
    st.dataframe(d, hide_index=True, width="stretch", column_config=cfg, **kw)


def verdict_pill(ok: bool | None, yes: str = "Đạt", no: str = "Không đạt") -> str:
    if ok is None:
        return pill("info", "Không áp dụng")
    return pill("good", yes) if ok else pill("bad", no)
