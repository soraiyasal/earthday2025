import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import random
import os

# ─── Page config ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="⚡ Hotel Energy Race",
    page_icon="🏆",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  /* ── Base reset ── */
  [data-testid="collapsedControl"] { display: none; }
  section[data-testid="stSidebar"]  { display: none !important; }
  .block-container { padding: 1rem 1rem 3rem !important; max-width: 700px !important; }

  /* ── Fonts ── */
  @import url('https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Lora:wght@400;500;600&display=swap');
  html, body, [class*="css"] { font-family: 'Lora', Georgia, serif; }

  /* ── Hero header ── */
  .hero {
    background: linear-gradient(135deg, #0a2540 0%, #1a4a6b 60%, #00a74a 100%);
    border-radius: 20px;
    padding: 2rem 1.5rem 1.5rem;
    text-align: center;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
  }
  .hero::before {
    content: '';
    position: absolute; inset: 0;
    background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.04'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  }
  .hero-title {
    font-family: 'DM Serif Display', sans-serif;
    font-size: clamp(1.8rem, 6vw, 2.8rem);
    font-weight: 800;
    color: #ffffff;
    margin: 0 0 0.3rem;
    line-height: 1.1;
    position: relative;
  }
  .hero-subtitle {
    font-size: clamp(0.85rem, 3vw, 1rem);
    color: rgba(255,255,255,0.75);
    margin: 0;
    position: relative;
  }
  .lightning { font-size: 2.5rem; display: block; margin-bottom: 0.5rem; animation: zap 2s ease-in-out infinite; }
  @keyframes zap { 0%,100%{transform:scale(1) rotate(-5deg);} 50%{transform:scale(1.2) rotate(5deg);} }

  /* ── Period selector card ── */
  .selector-card {
    background: #f7f9fc;
    border: 1.5px solid #e2e8f0;
    border-radius: 14px;
    padding: 1rem 1.2rem;
    margin-bottom: 1.2rem;
  }

  /* ── Fact ticker ── */
  .fact-pill {
    background: linear-gradient(90deg, #e8f5e9, #e3f0ff);
    border-left: 4px solid #00a74a;
    border-radius: 10px;
    padding: 0.65rem 1rem;
    font-size: 0.85rem;
    color: #1a3a4a;
    margin-bottom: 1.4rem;
    line-height: 1.4;
  }
  .fact-pill strong { color: #00a74a; }

  /* ── KPI cards ── */
  .kpi-row { display: flex; gap: 0.75rem; margin-bottom: 1.4rem; flex-wrap: wrap; }
  .kpi-card {
    flex: 1; min-width: 120px;
    background: #ffffff;
    border: 1.5px solid #e2e8f0;
    border-radius: 16px;
    padding: 1rem 0.9rem;
    text-align: center;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    transition: transform .15s;
  }
  .kpi-card:hover { transform: translateY(-2px); }
  .kpi-icon { font-size: 1.6rem; display: block; margin-bottom: 0.25rem; }
  .kpi-value { font-family: 'DM Serif Display', sans-serif; font-size: clamp(1.3rem,4vw,1.7rem); font-weight: 800; color: #0a2540; line-height: 1.1; }
  .kpi-label { font-size: 0.72rem; color: #64748b; margin-top: 0.2rem; text-transform: uppercase; letter-spacing: .04em; font-weight: 600; }
  .kpi-sub { font-size: 0.75rem; color: #94a3b8; margin-top: 0.15rem; }

  /* ── Section heading ── */
  .section-heading {
    font-family: 'DM Serif Display', sans-serif;
    font-size: 1.1rem;
    font-weight: 700;
    color: #0a2540;
    margin: 1.5rem 0 0.75rem;
    display: flex; align-items: center; gap: 0.4rem;
  }

  /* ── Hotel rank cards ── */
  .hotel-card {
    background: #ffffff;
    border: 1.5px solid #e2e8f0;
    border-radius: 16px;
    padding: 1rem 1.1rem;
    margin-bottom: 0.75rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.04);
    position: relative;
    overflow: hidden;
  }
  .hotel-card.gold   { border-color: #f59e0b; background: linear-gradient(135deg,#fffbeb,#ffffff); }
  .hotel-card.silver { border-color: #94a3b8; background: linear-gradient(135deg,#f8fafc,#ffffff); }
  .hotel-card.bronze { border-color: #cd7f32; background: linear-gradient(135deg,#fdf6ee,#ffffff); }
  .hotel-card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.6rem; }
  .hotel-name { font-family: 'DM Serif Display', sans-serif; font-size: 1rem; font-weight: 700; color: #0a2540; }
  .hotel-badge { font-size: 1.3rem; }
  .hotel-rank { font-size: 1.4rem; margin-right: 0.4rem; }
  .hotel-pct {
    font-family: 'DM Serif Display', sans-serif;
    font-size: 1.4rem;
    font-weight: 800;
    padding: 0.15rem 0.6rem;
    border-radius: 8px;
    background: #f0fdf4;
    color: #16a34a;
  }
  .hotel-pct.negative { background: #fff1f2; color: #dc2626; }
  .hotel-pct.neutral  { background: #f1f5f9; color: #64748b; }

  /* Progress track */
  .track-wrap { position: relative; height: 14px; background: #f1f5f9; border-radius: 99px; overflow: visible; margin-bottom: 0.35rem; }
  .track-fill { height: 100%; border-radius: 99px; transition: width 0.5s ease; position: relative; }
  .track-goal-line {
    position: absolute; top: -4px; bottom: -4px; width: 3px;
    background: #ef4444; border-radius: 2px;
    left: 100%; /* Will be set inline */ transform: translateX(-50%);
  }
  .track-label-row { display: flex; justify-content: space-between; font-size: 0.72rem; color: #94a3b8; margin-top: 0.1rem; }
  .goal-hit { font-size: 0.8rem; color: #16a34a; font-weight: 600; margin-top: 0.2rem; }

  /* ── Tips grid ── */
  .tips-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 0.65rem; margin-top: 0.5rem; }
  .tip-card {
    background: #f7f9fc;
    border: 1.5px solid #e2e8f0;
    border-radius: 12px;
    padding: 0.8rem 0.7rem;
    text-align: center;
    font-size: 0.82rem;
    color: #1e293b;
    font-weight: 500;
  }
  .tip-card .tip-emoji { font-size: 1.5rem; display: block; margin-bottom: 0.3rem; }

  /* ── Next steps ── */
  .next-steps { background: linear-gradient(135deg,#0a2540,#1a4a6b); border-radius: 16px; padding: 1.2rem 1.3rem; color: #fff; margin-top: 1rem; }
  .next-steps h4 { font-family:'DM Serif Display',sans-serif; font-size:1rem; margin:0 0 0.7rem; color:#ffffff; letter-spacing:.01em; }
  .next-step-item { display:flex; align-items:flex-start; gap:0.6rem; margin-bottom:0.5rem; font-size:0.85rem; color:rgba(255,255,255,.85); }
  .step-num { background:#00a74a; color:#fff; border-radius:50%; width:20px; height:20px; display:flex; align-items:center; justify-content:center; font-size:0.7rem; font-weight:700; flex-shrink:0; margin-top:1px; }

  /* ── Footer ── */
  .dash-footer { text-align:center; font-size:0.75rem; color:#94a3b8; margin-top:2rem; padding-top:1rem; border-top:1px solid #e2e8f0; }

  /* ── Plotly override: no white box ── */
  .js-plotly-plot .plotly { background: transparent !important; }
  
  /* ── Streamlit widget overrides ── */
  [data-testid="stMetricValue"] { font-size: 1.8rem !important; }
  div[data-testid="stSelectbox"] { margin: 0 !important; }
  .stSelectbox > label { font-weight: 600 !important; font-size: 0.85rem !important; color: #374151 !important; }
  
  /* Mobile tweaks */
  @media (max-width: 480px) {
    .kpi-row { gap: 0.5rem; }
    .kpi-card { padding: 0.8rem 0.6rem; }
    .hotel-card { padding: 0.85rem 0.9rem; }
  }
</style>
""", unsafe_allow_html=True)

# ─── Constants ───────────────────────────────────────────────────────────────
mpan_to_hotel = {
    "2500021277783": "Westin",
    "1200051315859": "Camden",
    "2500021281362": "Canopy",
    "1200052502710": "EH",
    "1050000997145": "St Albans"
}

hotel_emojis  = {"Westin": "🌲", "Camden": "🏙️", "Canopy": "🌴", "EH": "🏰", "St Albans": "⛪"}
hotel_colors  = {"Westin": "#164b35", "Camden": "#8764b8", "Canopy": "#ff7800", "EH": "#00205c", "St Albans": "#002d72"}
rank_medals   = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
rank_classes  = ["gold", "silver", "bronze", "", ""]

ELECTRICITY_FACTOR = 0.00020493  # kg CO₂ per kWh (2024/25)

energy_tips = [
    {"emoji": "💡", "tip": "Turn off lights when leaving"},
    {"emoji": "🌡️", "tip": "Drop temp by 1°C"},
    {"emoji": "🚿", "tip": "Encourage shorter showers"},
    {"emoji": "🔌", "tip": "Unplug idle devices"},
    {"emoji": "⚡", "tip": "Report energy waste fast"},
    {"emoji": "🪟", "tip": "Use natural light in the day"},
]

energy_facts = [
    "A 1°C drop in room temperature saves up to **8%** on heating bills!",
    "Hotels spend **6–10%** of operating costs on energy — every kWh counts.",
    "LED lights use up to **90% less** energy than traditional bulbs.",
    "Smart thermostats can cut HVAC energy use by up to **15%**.",
    "Only **3–5%** of guests reuse towels — reminding them helps enormously!",
    "Fixing a dripping hot-water tap can save **9,000 litres** per year.",
]

# ─── DB path (absolute, so it always resolves correctly) ─────────────────────
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'electricity_data.db')

# ─── Data loading ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)   # ← re-queries DB every 5 minutes
def load_data():
    try:
        conn = sqlite3.connect(DB_PATH)
        query = """
        SELECT strftime('%Y-%m-%d', Date) as Date,
               [Meter Point],
               [Total Usage]
        FROM hh_data
        ORDER BY Date
        """
        data = pd.read_sql_query(query, conn)
        data['Date'] = pd.to_datetime(data['Date'])
        data["Meter Point"] = data["Meter Point"].astype(str)
        data["Hotel"] = data["Meter Point"].map(mpan_to_hotel)
        data['Total Usage'] = pd.to_numeric(data['Total Usage'], errors='coerce').fillna(0)
        data['Year'] = data['Date'].dt.year
        return data
    except Exception:
        return generate_simulated_data()
    finally:
        if 'conn' in locals():
            conn.close()


def generate_simulated_data():
    end_date   = datetime.today()
    start_date = end_date - timedelta(days=365 * 2)
    hotels     = list(mpan_to_hotel.values())
    all_data   = []

    configs = {
        "Westin":    {"base": 180, "improve": 0.82, "end_offset": 1},
        "Camden":    {"base": 220, "improve": 0.95, "end_offset": 0},
        "Canopy":    {"base": 200, "improve": 0.88, "end_offset": 2},
        "EH":        {"base": 190, "improve": 0.90, "end_offset": 2},
        "St Albans": {"base": 210, "improve": 0.85, "end_offset": 2},
    }

    for hotel in hotels:
        cfg = configs[hotel]
        hotel_mpan = next((m for m, h in mpan_to_hotel.items() if h == hotel), "unknown")
        hotel_end  = end_date - timedelta(days=cfg["end_offset"])
        dates = pd.date_range(start=start_date, end=hotel_end, freq='D')

        for date in dates:
            season  = 1.0 + 0.3 * np.cos((date.month - 1) * np.pi / 6)
            weekend = 1.2 if date.weekday() >= 5 else 1.0
            yfactor = cfg["improve"] if date.year == datetime.today().year else 1.0
            usage   = cfg["base"] * season * weekend * yfactor * np.random.uniform(0.9, 1.1)
            all_data.append({
                'Date': date, 'Meter Point': hotel_mpan,
                'Hotel': hotel, 'Total Usage': usage,
                'Year': date.year
            })

    return pd.DataFrame(all_data)


# ─── Date helpers ─────────────────────────────────────────────────────────────
def find_available_dates(data, year):
    year_data  = data[data['Year'] == year]
    all_hotels = list(mpan_to_hotel.values())
    all_dates  = sorted(year_data['Date'].unique())
    available  = []
    for date in all_dates:
        if all(h in year_data[year_data['Date'] == date]['Hotel'].values for h in all_hotels):
            d = pd.Timestamp(date).to_pydatetime() if isinstance(date, (np.datetime64, pd.Timestamp)) else date
            available.append(d)
    return sorted(available)


def find_matching_days(data, current_year, previous_year, start_date=None, end_date=None):
    cy_dates = [pd.Timestamp(d).to_pydatetime() for d in find_available_dates(data, current_year)]
    py_dates = [pd.Timestamp(d).to_pydatetime() for d in find_available_dates(data, previous_year)]
    common   = set(d.strftime('%m-%d') for d in cy_dates) & set(d.strftime('%m-%d') for d in py_dates)
    cy_match = [d for d in cy_dates if d.strftime('%m-%d') in common]
    py_match = [d for d in py_dates if d.strftime('%m-%d') in common]

    if start_date and end_date:
        cy_match = [d for d in cy_match if start_date <= d <= end_date]
        mds      = {d.strftime('%m-%d') for d in cy_match}
        py_match = [d for d in py_match if d.strftime('%m-%d') in mds]

    return {'current_dates': sorted(cy_match), 'previous_dates': sorted(py_match)}


def calculate_hotel_metrics(data, matched_dates):
    TARGET = 10
    cy, py = matched_dates['current_dates'], matched_dates['previous_dates']
    if not cy or not py:
        return {}

    metrics = {}
    for hotel in mpan_to_hotel.values():
        hd    = data[data['Hotel'] == hotel]
        cur   = hd[hd['Date'].isin(cy)]['Total Usage'].sum()
        prev  = hd[hd['Date'].isin(py)]['Total Usage'].sum()
        pct   = 0 if prev == 0 else ((cur - prev) / prev) * 100
        tgt   = prev * (1 - TARGET / 100)
        if cur < prev:
            prog    = min(100, ((prev - cur) / (prev - tgt)) * 100)
            saved   = prev - cur
        else:
            prog, saved = 0, 0

        metrics[hotel] = {
            'current_total':       cur,
            'previous_total':      prev,
            'percent_change':      pct,
            'progress_percentage': prog,
            'energy_reduction':    abs(min(0, pct)),
            'target_savings_percent': TARGET,
            'kwh_saved':           saved,
        }
    return metrics


def get_available_months(data, year):
    dates = find_available_dates(data, year)
    return sorted({d.month for d in dates}) if dates else []


def format_period_option(kind, value=None, month_num=None, year=None):
    if kind == "ytd":        return "🔄 Year to Date"
    if kind == "last_days":  return f"📊 Last {value} Days"
    if kind == "this_month": return "📆 This Month"
    if kind == "prev_month": return "📆 Previous Month"
    if kind == "specific_month":
        return f"📆 {datetime(year, month_num, 1).strftime('%B')} {year}"
    return "📅 Custom Period"


# ─── Charts ──────────────────────────────────────────────────────────────────
def create_race_chart(metrics):
    sorted_hotels = sorted(metrics.items(), key=lambda x: x[1]['energy_reduction'], reverse=True)
    names, reds, progs, colors_list = [], [], [], []
    for hotel, m in sorted_hotels:
        names.append(f"{hotel_emojis.get(hotel,'🏨')} {hotel}")
        reds.append(m['energy_reduction'])
        progs.append(m['progress_percentage'])
        colors_list.append(hotel_colors.get(hotel, '#002d72'))

    fig = go.Figure()
    for i, name in enumerate(names):
        fig.add_trace(go.Bar(
            y=[name], x=[reds[i]],
            orientation='h',
            marker=dict(color=colors_list[i], line=dict(width=0)),
            text=[f"  {reds[i]:.1f}%"],
            textposition='outside',
            textfont=dict(size=13, color='#0a2540', family='DM Serif Display, Georgia, serif'),
            hovertemplate=f"<b>{name}</b><br>Reduction: {reds[i]:.1f}%<br>Goal progress: {progs[i]:.0f}%<extra></extra>",
            name=name,
            width=0.55,
        ))

    max_x = max(max(reds) + 3, 12)

    # Finish-line ribbon
    fig.add_shape(type="rect", x0=10, y0=-0.5, x1=10.15, y1=len(names) - 0.5,
                  fillcolor="rgba(239,68,68,0.15)", line=dict(width=0))
    fig.add_shape(type="line", x0=10, y0=-0.5, x1=10, y1=len(names) - 0.5,
                  line=dict(color="#ef4444", width=2.5, dash="dash"))
    fig.add_annotation(x=10, y=len(names) - 0.4, text="🏁 10% Target",
                       showarrow=False, font=dict(color="#ef4444", size=12, family="DM Serif Display, Georgia, serif"),
                       yshift=14, xanchor="center")

    fig.update_layout(
        title=dict(text="<b>🏁 The Race to 10%</b>", font=dict(family="DM Serif Display, Georgia, serif", size=16, color="#0a2540"), x=0),
        margin=dict(l=0, r=50, t=44, b=10),
        height=280,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(range=[0, max_x], gridcolor='#e2e8f0', ticksuffix='%',
                   tickfont=dict(size=11, color='#64748b', family='DM Serif Display, Georgia, serif'), showline=False),
        yaxis=dict(autorange='reversed', tickfont=dict(size=12, color='#0a2540', family='DM Serif Display, Georgia, serif'), showline=False),
        showlegend=False,
        bargap=0.35,
    )
    return fig


def create_weekly_chart(data, start, end):
    period_data = data[(data['Date'] >= start) & (data['Date'] <= end)].copy()
    period_data['day_of_week'] = period_data['Date'].dt.dayofweek
    period_data['day_name']    = period_data['Date'].dt.day_name()

    daily = period_data.groupby(['day_of_week', 'day_name'])['Total Usage'].mean().reset_index()
    order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily['day_name'] = pd.Categorical(daily['day_name'], categories=order, ordered=True)
    daily = daily.sort_values('day_name')

    # Short day labels for mobile
    daily['day_short'] = daily['day_name'].astype(str).str[:3]

    max_val = daily['Total Usage'].max()
    min_val = daily['Total Usage'].min()
    bar_colors = [
        "#ef4444" if v == max_val else ("#00a74a" if v == min_val else "#3b82f6")
        for v in daily['Total Usage']
    ]

    fig = go.Figure(go.Bar(
        x=daily['day_short'],
        y=daily['Total Usage'],
        marker_color=bar_colors,
        marker_line=dict(width=0),
        width=0.6,
        hovertemplate='<b>%{x}</b><br>Avg: %{y:,.0f} kWh<extra></extra>',
    ))

    highest = daily.loc[daily['Total Usage'].idxmax(), 'day_short']
    lowest  = daily.loc[daily['Total Usage'].idxmin(), 'day_short']

    for day, label, color in [(highest, "▲ High", "#ef4444"), (lowest, "▼ Low", "#00a74a")]:
        val = daily[daily['day_short'] == day]['Total Usage'].iloc[0]
        fig.add_annotation(x=day, y=val, text=label, showarrow=False,
                           yshift=12, font=dict(size=10, color=color, family="DM Serif Display, Georgia, serif"))

    fig.update_layout(
        title=dict(text="<b>📅 Energy by Day of Week</b>", font=dict(family="DM Serif Display, Georgia, serif", size=14, color="#0a2540"), x=0),
        margin=dict(l=0, r=0, t=40, b=10),
        height=230,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(showline=False, gridcolor='rgba(0,0,0,0)', tickfont=dict(size=11, family='DM Serif Display, Georgia, serif')),
        yaxis=dict(gridcolor='#e2e8f0', tickfont=dict(size=10, color='#94a3b8', family='DM Serif Display, Georgia, serif'),
                   ticksuffix=' kWh', showline=False),
        showlegend=False,
    )
    return fig, highest, lowest


# ─── Hotel rank card HTML ─────────────────────────────────────────────────────
def hotel_card_html(rank, hotel, metrics_data):
    m          = metrics_data[hotel]
    medal      = rank_medals[rank]
    css_class  = rank_classes[rank]
    emoji      = hotel_emojis.get(hotel, "🏨")
    reduction  = m['energy_reduction']
    pct_change = m['percent_change']
    prog       = m['progress_percentage']
    color      = hotel_colors.get(hotel, "#002d72")

    pct_class = "negative" if pct_change > 0 else ("neutral" if pct_change == 0 else "")
    pct_sign  = "▲ " if pct_change > 0 else ("▼ " if pct_change < 0 else "")
    pct_disp  = f"{pct_sign}{abs(pct_change):.1f}%"

    fill_w    = min(prog, 100)
    track_pct = fill_w

    bar_color = (
        f"linear-gradient(90deg, {color}, #00a74a)"
        if pct_change < 0
        else f"linear-gradient(90deg, #ef4444, #f97316)"
    )

    goal_hit = '<div class="goal-hit">🎉 Goal reached!</div>' if prog >= 100 else ""

    return f"""
    <div class="hotel-card {css_class}">
      <div class="hotel-card-header">
        <div style="display:flex;align-items:center;gap:0.4rem;">
          <span class="hotel-rank">{medal}</span>
          <span class="hotel-badge">{emoji}</span>
          <span class="hotel-name">{hotel}</span>
        </div>
        <span class="hotel-pct {pct_class}">{pct_disp}</span>
      </div>
      <div class="track-wrap">
        <div class="track-fill" style="width:{track_pct}%;background:{bar_color};"></div>
        <div class="track-goal-line" style="left:min(100%,100%);"></div>
      </div>
      <div class="track-label-row">
        <span>{prog:.0f}% of 10% goal</span>
        <span style="color:#ef4444;">🏁 10%</span>
      </div>
      {goal_hit}
    </div>
    """


# ─── Main ────────────────────────────────────────────────────────────────────
def main():
    # ── Hero ──
    st.markdown("""
    <div class="hero">
      <span class="lightning">⚡</span>
      <div class="hero-title">Hotel Energy Race</div>
      <div class="hero-subtitle">Who's cutting the most electricity? 10% savings wins. 🏆</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Load data ──
    with st.spinner("Loading data…"):
        data = load_data()

    today        = datetime.today()
    current_year = today.year
    previous_year= current_year - 1

    current_months = get_available_months(data, current_year)
    period_options = [
        format_period_option("ytd"),
        format_period_option("last_days", 7),
        format_period_option("last_days", 30),
        format_period_option("this_month"),
        format_period_option("prev_month"),
    ]
    for m in current_months:
        period_options.append(format_period_option("specific_month", month_num=m, year=current_year))

    # ── Period selector + manual refresh ──
    col1, col2 = st.columns([5, 1])
    with col1:
        st.markdown('<div class="selector-card">', unsafe_allow_html=True)
        period = st.selectbox("📅 Select time period", options=period_options, index=3, label_visibility="visible")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown("<div style='padding-top:1.85rem;'>", unsafe_allow_html=True)
        if st.button("🔄", help="Force refresh data from DB"):
            st.cache_data.clear()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Fun fact ──
    fact = random.choice(energy_facts)
    st.markdown(f'<div class="fact-pill">💡 <strong>Did you know?</strong> {fact}</div>', unsafe_allow_html=True)

    period_text = period.split(" ", 1)[1]

    # ── Parse dates ──
    if "Year to Date" in period:
        period_end, period_start = today, datetime(current_year, 1, 1)
    elif "Last 7 Days" in period:
        period_end, period_start = today, today - timedelta(days=7)
    elif "Last 30 Days" in period:
        period_end, period_start = today, today - timedelta(days=30)
    elif "This Month" in period:
        period_start = datetime(today.year, today.month, 1)
        period_end   = today
    elif "Previous Month" in period:
        first = datetime(today.year, today.month, 1)
        last  = first - timedelta(days=1)
        period_start = datetime(last.year, last.month, 1)
        period_end   = last
    else:
        mname = period_text.split()[0]
        yr    = int(period_text.split()[1])
        mn    = datetime.strptime(mname, "%B").month
        period_start = datetime(yr, mn, 1)
        nxt_yr = yr + 1 if mn == 12 else yr
        nxt_mn = 1 if mn == 12 else mn + 1
        period_end = datetime(nxt_yr, nxt_mn, 1) - timedelta(days=1)

    matched = find_matching_days(data, current_year, previous_year, period_start, period_end)
    metrics = calculate_hotel_metrics(data, matched)

    if not metrics:
        st.error("⚠️ No data available for this period.")
        st.stop()

    # ── Date text ──
    if matched['current_dates']:
        date_info = (f"{matched['current_dates'][0].strftime('%b %d')} – "
                     f"{matched['current_dates'][-1].strftime('%b %d')}")
    else:
        date_info = "No matching days"

    if "Year to Date" in period:
        compare_text = f"YTD {current_year} vs {previous_year}"
    elif "Last" in period:
        d = "7" if "7" in period else "30"
        compare_text = f"Last {d} days vs same period last year"
    elif "This Month" in period:
        compare_text = f"{today.strftime('%B')} {current_year} vs {previous_year}"
    elif "Previous Month" in period:
        first = datetime(today.year, today.month, 1) - timedelta(days=1)
        compare_text = f"{first.strftime('%B')} {current_year} vs {previous_year}"
    else:
        compare_text = f"{period_text.split()[0]} {current_year} vs {previous_year}"

    # ── KPI row ──
    total_kwh_saved = sum(m['kwh_saved'] for m in metrics.values())
    co2_saved       = total_kwh_saved * ELECTRICITY_FACTOR
    cost_saved      = total_kwh_saved * 0.22
    num_days        = len(matched['current_dates'])

    sorted_hotels   = sorted(metrics.items(), key=lambda x: x[1]['energy_reduction'], reverse=True)
    leader, leader_m = sorted_hotels[0]
    leader_pct      = leader_m['energy_reduction']
    leader_emoji    = hotel_emojis.get(leader, "🏨")

    st.markdown(f"""
    <div class="kpi-row">
      <div class="kpi-card">
        <span class="kpi-icon">⚡</span>
        <div class="kpi-value">{total_kwh_saved:,.0f}</div>
        <div class="kpi-label">kWh Saved</div>
        <div class="kpi-sub">{compare_text}</div>
      </div>
      <div class="kpi-card">
        <span class="kpi-icon">💷</span>
        <div class="kpi-value">£{cost_saved:,.0f}</div>
        <div class="kpi-label">Money Saved</div>
        <div class="kpi-sub">At £0.22 / kWh</div>
      </div>
      <div class="kpi-card">
        <span class="kpi-icon">{leader_emoji}</span>
        <div class="kpi-value">{leader_pct:.1f}%</div>
        <div class="kpi-label">Leader</div>
        <div class="kpi-sub">{leader}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Race chart ──
    race_fig = create_race_chart(metrics)
    st.plotly_chart(race_fig, use_container_width=True, config={"displayModeBar": False})

    # ── Leaderboard cards ──
    st.markdown('<div class="section-heading">🏅 Leaderboard</div>', unsafe_allow_html=True)
    cards_html = ""
    for rank, (hotel, _) in enumerate(sorted_hotels):
        cards_html += hotel_card_html(rank, hotel, metrics)
    st.markdown(cards_html, unsafe_allow_html=True)

    # ── Weekly pattern ──
    try:
        weekly_fig, highest_day, lowest_day = create_weekly_chart(data, period_start, period_end)
        st.plotly_chart(weekly_fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f'<p style="font-size:.83rem;color:#64748b;margin:-0.5rem 0 1rem;">'
            f'⚠️ <b>{highest_day}</b> is your highest-usage day — focus efforts there!</p>',
            unsafe_allow_html=True
        )
    except Exception:
        pass

    # ── Tips ──
    st.markdown('<div class="section-heading">💡 Quick Wins</div>', unsafe_allow_html=True)
    tips_html = '<div class="tips-grid">'
    for tip in energy_tips:
        tips_html += f'<div class="tip-card"><span class="tip-emoji">{tip["emoji"]}</span>{tip["tip"]}</div>'
    tips_html += '</div>'
    st.markdown(tips_html, unsafe_allow_html=True)

    # ── Next steps ──
    st.markdown("""
    <div class="next-steps">
      <h4>🚀 Keep the momentum going</h4>
      <div class="next-step-item"><span class="step-num">1</span> Share the leaderboard with your team today</div>
      <div class="next-step-item"><span class="step-num">2</span> Pick one tip above and act on it this week</div>
      <div class="next-step-item"><span class="step-num">3</span> Focus on high-usage days highlighted above</div>
      <div class="next-step-item"><span class="step-num">4</span> Check back next week to track progress 📈</div>
    </div>
    """, unsafe_allow_html=True)

    # ── Footer ──
    st.markdown(
        f'<div class="dash-footer">4C Group · Electricity data · {date_info} · {num_days} days compared</div>',
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()