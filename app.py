import streamlit as st
import pandas as pd
import math
from datetime import date, datetime, timedelta
import random

# ============================================================
# SPORTS BETTING AI ULTIMATE v4 PRO ELITE
# Streamlit dashboard for iPad / Web
# Manual-data decision support tool
# ============================================================

st.set_page_config(
    page_title="Sports Betting AI Ultimate v4 Pro Elite",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Dark Pro CSS
# -----------------------------
st.markdown("""
<style>
.stApp {
    background: radial-gradient(circle at top left, #0f172a 0%, #020617 38%, #000000 100%);
    color: #e5e7eb;
}
.block-container {padding-top: 1rem; padding-bottom: 2rem;}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #020617 0%, #0f172a 100%);
    border-right: 1px solid rgba(148,163,184,.18);
}
[data-testid="stMetric"] {
    background: rgba(15, 23, 42, .72);
    border: 1px solid rgba(148,163,184,.20);
    border-radius: 16px;
    padding: 16px;
}
[data-testid="stMetricValue"] {font-size: 1.8rem; color: #86efac;}
.pro-card {
    background: linear-gradient(145deg, rgba(15,23,42,.95), rgba(2,6,23,.95));
    border: 1px solid rgba(148,163,184,.22);
    border-radius: 18px;
    padding: 18px;
    margin: 10px 0;
    box-shadow: 0 0 28px rgba(59,130,246,.08);
}
.hero-card {
    background: linear-gradient(135deg, rgba(14,165,233,.14), rgba(34,197,94,.12), rgba(168,85,247,.12));
    border: 1px solid rgba(125,211,252,.35);
    border-radius: 22px;
    padding: 22px;
    margin: 12px 0 18px 0;
}
.elite {border-left: 8px solid #22c55e;}
.strong {border-left: 8px solid #84cc16;}
.playable {border-left: 8px solid #facc15;}
.pass {border-left: 8px solid #ef4444;}
.badge-green {
    background:#166534; color:#dcfce7; border-radius:999px; padding:4px 10px; font-weight:700;
}
.badge-yellow {
    background:#713f12; color:#fef3c7; border-radius:999px; padding:4px 10px; font-weight:700;
}
.badge-red {
    background:#7f1d1d; color:#fee2e2; border-radius:999px; padding:4px 10px; font-weight:700;
}
.small {font-size:.88rem; opacity:.78;}
.big-score {font-size:3.3rem; font-weight:900; color:#4ade80;}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Helpers
# -----------------------------
def clamp(x, lo=0, hi=100):
    try:
        return max(lo, min(hi, float(x)))
    except Exception:
        return lo

def implied_prob(odds):
    return 100 / odds if odds and odds > 1 else 0

def model_prob(score):
    return clamp(44 + (score - 55) * 0.78, 5, 95)

def kelly_fraction(prob_pct, odds):
    p = prob_pct / 100
    b = odds - 1
    if b <= 0:
        return 0
    return max(0, (b*p - (1-p))/b)

def stars(score):
    if score >= 90: return "⭐⭐⭐⭐⭐"
    if score >= 82: return "⭐⭐⭐⭐"
    if score >= 72: return "⭐⭐⭐"
    if score >= 62: return "⭐⭐"
    return "⭐"

def grade(score):
    if score >= 90: return "ELITE"
    if score >= 82: return "STRONG"
    if score >= 72: return "PLAYABLE"
    if score >= 62: return "LEAN"
    return "PASS"

def action(score):
    if score >= 90: return "🔥 BET NOW"
    if score >= 82: return "✅ PLAY"
    if score >= 72: return "🟡 CONSIDER"
    if score >= 62: return "👀 WATCH"
    return "❌ PASS"

def css_class(score):
    if score >= 90: return "elite"
    if score >= 82: return "strong"
    if score >= 72: return "playable"
    return "pass"

def suggested_stake(score, odds, bankroll, risk_pct, kelly_cap):
    fixed = bankroll * risk_pct / 100
    if score >= 90:
        fixed *= 1.25
    elif score >= 82:
        fixed *= 1
    elif score >= 72:
        fixed *= .5
    else:
        fixed = 0

    p = model_prob(score)
    k = kelly_fraction(p, odds) * .25
    k = min(k, kelly_cap/100)
    k_amt = bankroll * k
    return round(min(max(fixed, k_amt), bankroll * kelly_cap/100), 2), round(k*100, 2)

def pick_row(sport, match, market, pick, score, odds, note, bankroll, risk_pct, kelly_cap):
    score = clamp(score)
    mp = model_prob(score)
    ip = implied_prob(odds)
    stake, kelly_q = suggested_stake(score, odds, bankroll, risk_pct, kelly_cap)
    return {
        "Sport": sport,
        "Match": match,
        "Market": market,
        "Pick": pick,
        "Action": action(score),
        "AI Score": round(score, 1),
        "Stars": stars(score),
        "Grade": grade(score),
        "Odds": round(odds, 2),
        "Win Prob %": round(mp, 1),
        "Market %": round(ip, 1),
        "Edge %": round(mp - ip, 1),
        "Kelly 1/4 %": kelly_q,
        "Stake $": stake,
        "Note": note,
    }

def rank(rows):
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(["AI Score", "Edge %"], ascending=False).reset_index(drop=True)

def render_pick_card(row, title="AI Recommendation Today"):
    c = css_class(row["AI Score"])
    st.markdown(f"""
    <div class="hero-card {c}">
        <div class="small">{title}</div>
        <h2>{row['Stars']} {row['Pick']}</h2>
        <b>{row['Sport']} • {row['Match']} • {row['Market']}</b><br>
        <span class="big-score">{row['AI Score']}</span><span style="font-size:1.5rem;">/100</span>
        &nbsp;&nbsp; <span class="badge-green">{row['Action']}</span><br><br>
        Edge: <b style="color:#86efac;">{row['Edge %']}%</b> &nbsp; | &nbsp;
        Win Prob: <b>{row['Win Prob %']}%</b> &nbsp; | &nbsp;
        Kelly 1/4: <b>{row['Kelly 1/4 %']}%</b> &nbsp; | &nbsp;
        Stake: <b>${row['Stake $']}</b><br>
        <span class="small">{row['Note']}</span>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# Engines
# -----------------------------
def soccer_strength(rank_val, form, xgf, xga, injuries, motivation, rest, fatigue, venue):
    rank_score = clamp(100 - rank_val*.75, 8, 100)
    form_score = clamp(form/15*100)
    xg_score = clamp(xgf*34 + (2.15-xga)*24)
    rest_score = clamp(rest*13, 15, 100)
    score = rank_score*.18 + form_score*.22 + xg_score*.27 + motivation*10*.19 + rest_score*.10
    score += venue*1.8
    score -= injuries*4.1 + fatigue*2.5
    return clamp(score)

def soccer_total_score(total, axgf, bxgf, axga, bxga, pace, weather, pressure, mustwin, move, ref):
    proj = clamp((axgf+bxgf)*.56 + (2.2-axga)*.24 + (2.2-bxga)*.24, .7, 4.8)
    over = 50 + (proj-total)*20 + pace*2.3 + mustwin*1.9 + max(move,0)*8 - weather*2.5 - pressure*2 + ref*.3
    under = 50 + (total-proj)*20 + weather*2.8 + pressure*2.6 + max(-move,0)*8 - pace*2.1 - mustwin*1.5 + ref*.8
    return clamp(over), clamp(under), proj

def mlb_projection(total, p1, p2, bullpen, park, weather, ump, cold, wind, zone):
    proj = 9.4 - (p1+p2)*.23 - bullpen*.13 - park*.12 - weather*.16 - ump*.10 - cold*.15 - wind*.12 - zone*.09
    return max(3.7, min(12.8, proj))

def mlb_under(total, p1, p2, bullpen, park, weather, ump, cold, line_drop, public_over, wind, zone, playoff_pressure):
    proj = mlb_projection(total, p1, p2, bullpen, park, weather, ump, cold, wind, zone)
    score = 48 + (total-proj)*9.2 + p1*1.15 + p2*1.15 + bullpen*1.4 + park*1.1
    score += weather*1.35 + ump*1.1 + cold*1.25 + max(line_drop,0)*7
    score += max(public_over-58,0)*.22 + wind*1.3 + zone*1 + playoff_pressure*.9
    if total >= 9: score += 5
    if total <= 7: score -= 5
    return clamp(score), proj

def nba_scores(total, pace, offense, defense, injuries, rest_slow, move, public_over, playoff):
    over = 50 + (pace-5)*3.1 + (offense-112)*.7 - (defense-112)*.35 + max(move,0)*5 - injuries*1.4 - playoff*.8
    under = 50 - (pace-5)*3.1 - (offense-112)*.7 + (defense-112)*.45 + injuries*2 + rest_slow*1.3 + max(-move,0)*5 + max(public_over-60,0)*.22 + playoff*1.2
    return clamp(over), clamp(under)

def nfl_scores(total, pace, run, weather, defense, turnover, redzone, move, prime_time_under):
    over = 50 + (pace-5)*2.8 - run*1.35 - weather*2.4 - defense*1.45 + turnover*1.1 + redzone*1.4 + max(move,0)*6
    under = 50 - (pace-5)*2.8 + run*1.6 + weather*2.8 + defense*1.9 - turnover*.8 - redzone*.9 + max(-move,0)*6 + prime_time_under*.8
    return clamp(over), clamp(under)

def live_under(progress, score_units, live_total, shots, chances, attacks, tempo, pressure, weather, line_value, clock_drain):
    score = 48
    if progress >= 20 and score_units == 0: score += 16
    if progress >= 30 and score_units <= 1: score += 12
    if progress >= 55 and score_units <= 1: score += 8
    score += clamp(live_total-score_units, 0, 5)*4.5
    score += line_value*1.8 + weather*2.1 + clock_drain*1.3
    score -= shots*3 + chances*7.2 + attacks*.16 + tempo*2.6 + pressure*2.2
    if score_units >= 3 and progress < 55: score -= 25
    if progress < 15: score -= 8
    return clamp(score)

def sharp_score(open_line, current_line, public, tickets, handle, side, minutes):
    move = current_line - open_line
    score = 50
    notes = []
    if handle - tickets >= 15:
        score += 15; notes.append("Handle cao hơn tickets")
    if public >= 60 and ((side=="Under" and move<0) or (side=="Over" and move>0) or (side=="Dog" and move>0)):
        score += 15; notes.append("Reverse line movement")
    if abs(move) >= .5:
        score += 9; notes.append("Line move mạnh")
    if abs(move) >= .5 and minutes <= 20:
        score += 10; notes.append("Steam move nhanh")
    clv = abs(move)*6 + max(handle-tickets,0)*.25
    if clv >= 10:
        score += 6; notes.append("CLV projection tốt")
    if not notes:
        notes.append("Signal chưa rõ")
    return clamp(score), round(clv, 1), " | ".join(notes)

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("🏆 Ultimate v4 Elite")
bankroll = st.sidebar.number_input("Bankroll ($)", 10.0, 1000000.0, 10000.0, 100.0)
risk_pct = st.sidebar.slider("Risk per bet (%)", 0.1, 5.0, 1.0, .1)
kelly_cap = st.sidebar.slider("Kelly cap (%)", .25, 5.0, 2.0, .25)
min_score = st.sidebar.slider("Min AI Score", 50, 98, 75)
only_best = st.sidebar.checkbox("Only show 85+", value=False)
st.sidebar.divider()
sport_filter = st.sidebar.selectbox("Quick filter sport", ["All", "MLB", "Soccer", "NBA", "NFL"])
market_filter = st.sidebar.selectbox("Market", ["All", "Under", "Over", "ML", "Spread"])
st.sidebar.success("Model v4.0 Elite • Manual data mode")

# -----------------------------
# Header
# -----------------------------
st.title("🏆 Sports Betting AI Ultimate v4 Pro Elite")
st.caption("AI Recommendations • Best Bets • Sharp Money • Live Bet • Kelly • Tracker • iPad Pro UI")

tabs = st.tabs([
    "📊 Dashboard", "⭐ Best Bets", "⚾ MLB Under", "⚽ Soccer", "🏀 NBA",
    "🏈 NFL", "🔥 Live Bet", "📈 Sharp Money", "🧾 Tracker"
])

# -----------------------------
# Dashboard
# -----------------------------
with tabs[0]:
    sample_rows = [
        pick_row("MLB", "SEA vs BAL", "Total", "Under 7.5", 93, 1.91, "Best Bet Today • pitcher + weather + sharp", bankroll, risk_pct, kelly_cap),
        pick_row("MLB", "TB vs NYY", "Total", "Under 8.0", 89, 1.91, "RLM + bullpen fresh", bankroll, risk_pct, kelly_cap),
        pick_row("Soccer", "Spain vs Uruguay", "Total", "Under 2.5", 86, 1.91, "High pressure match", bankroll, risk_pct, kelly_cap),
    ]
    df_sample = rank(sample_rows)
    render_pick_card(df_sample.iloc[0])

    a,b,c,d,e,f = st.columns(6)
    a.metric("Best Bets", "5", "Today")
    b.metric("Avg AI Score", "82.6", "Top 10")
    c.metric("Total Edge", "+9.6%", "Avg")
    d.metric("Win Rate 30D", "61.2%", "+3.4%")
    e.metric("ROI 30D", "+17.8%", "+4.1%")
    f.metric("Profit 30D", "$1,780", "+$245")

    st.markdown('<div class="pro-card"><h3>⭐ Today’s Best Bets Preview</h3></div>', unsafe_allow_html=True)
    st.dataframe(df_sample, use_container_width=True)

# -----------------------------
# Best Bets Builder
# -----------------------------
with tabs[1]:
    st.subheader("⭐ Today's Best Bets Builder")
    rows = []
    for i in range(1, 6):
        with st.expander(f"Candidate #{i}", expanded=(i <= 2)):
            c1,c2,c3,c4 = st.columns(4)
            sport = c1.selectbox(f"Sport {i}", ["MLB","Soccer","NBA","NFL"], key=f"sport{i}")
            match = c2.text_input(f"Match {i}", f"Game {i}", key=f"match{i}")
            pick = c3.text_input(f"Pick {i}", "Under", key=f"pick{i}")
            odds = c4.number_input(f"Odds {i}", 1.01, 20.0, 1.91, .01, key=f"odds{i}")
            d1,d2,d3,d4 = st.columns(4)
            model = d1.slider(f"Base model {i}", 0, 100, 75, key=f"model{i}")
            sharp = d2.slider(f"Sharp signal {i}", 0, 100, 60, key=f"sharp{i}")
            matchup = d3.slider(f"Matchup edge {i}", 0, 100, 70, key=f"matchup{i}")
            risk = d4.slider(f"Risk penalty {i}", 0, 30, 8, key=f"risk{i}")
            score = clamp(model*.45 + sharp*.25 + matchup*.30 - risk*.65)
            rows.append(pick_row(sport, match, "Manual AI", pick, score, odds, f"Model {model}, Sharp {sharp}, Matchup {matchup}, Risk -{risk}", bankroll, risk_pct, kelly_cap))
    df = rank(rows)
    threshold = 85 if only_best else min_score
    st.dataframe(df[df["AI Score"] >= threshold], use_container_width=True)
    if not df.empty:
        render_pick_card(df.iloc[0], "Best Candidate")

# -----------------------------
# MLB Under
# -----------------------------
with tabs[2]:
    st.subheader("⚾ MLB Under Elite v4")
    c1,c2 = st.columns(2)
    with c1:
        match = st.text_input("MLB Match", "SEA vs BAL")
        total = st.number_input("Game total", 5.5, 14.5, 7.5, .5)
        p1 = st.slider("Pitcher A quality", 0, 10, 8)
        p2 = st.slider("Pitcher B quality", 0, 10, 8)
        bullpen = st.slider("Bullpen freshness", 0, 10, 8)
        cold = st.slider("Both offenses cold", 0, 10, 7)
        playoff_pressure = st.slider("Pressure / tight game", 0, 10, 5)
    with c2:
        park = st.slider("Park supports Under", 0, 10, 7)
        weather = st.slider("Weather supports Under", 0, 10, 6)
        ump = st.slider("Umpire Under tendency", 0, 10, 6)
        wind = st.slider("Wind blowing in", 0, 10, 5)
        zone = st.slider("Wide strike zone", 0, 10, 6)
        open_total = st.number_input("Opening total", 5.5, 14.5, 8.0, .5)
        public_over = st.slider("Public Over %", 0, 100, 64)

    if st.button("Analyze MLB Under Elite", type="primary"):
        score, proj = mlb_under(total, p1, p2, bullpen, park, weather, ump, cold, open_total-total, public_over, wind, zone, playoff_pressure)
        row = pick_row("MLB", match, "Total", f"Under {total}", score, 1.91, f"xRuns projection {proj:.2f} • line drop {open_total-total:+.1f}", bankroll, risk_pct, kelly_cap)
        render_pick_card(row, "MLB Under AI")
        st.dataframe(pd.DataFrame([row]), use_container_width=True)

# -----------------------------
# Soccer
# -----------------------------
with tabs[3]:
    st.subheader("⚽ Soccer AI v4")
    col1,col2 = st.columns(2)
    with col1:
        a = st.text_input("Team A", "Spain")
        ar = st.number_input("Team A rank", 1, 210, 1)
        af = st.slider("Team A form", 0, 15, 11)
        axgf = st.number_input("Team A xG For", 0.0, 5.0, 2.0, .05)
        axga = st.number_input("Team A xG Against", 0.0, 5.0, .8, .05)
        ainj = st.slider("Team A injuries", 0, 10, 2)
        amot = st.slider("Team A motivation", 0, 10, 8)
        arest = st.slider("Team A rest days", 0, 10, 5)
        afat = st.slider("Team A fatigue", 0, 10, 2)
        avenue = st.slider("Team A venue edge", -5, 5, 0)
    with col2:
        b = st.text_input("Team B", "Uruguay")
        br = st.number_input("Team B rank", 1, 210, 15)
        bf = st.slider("Team B form", 0, 15, 10)
        bxgf = st.number_input("Team B xG For", 0.0, 5.0, 1.55, .05)
        bxga = st.number_input("Team B xG Against", 0.0, 5.0, 1.05, .05)
        binj = st.slider("Team B injuries", 0, 10, 2)
        bmot = st.slider("Team B motivation", 0, 10, 9)
        brest = st.slider("Team B rest days", 0, 10, 5)
        bfat = st.slider("Team B fatigue", 0, 10, 3)
        bvenue = st.slider("Team B venue edge", -5, 5, 0)

    c1,c2,c3,c4 = st.columns(4)
    aodds = c1.number_input("Team A ML odds", 1.01, 20.0, 1.80, .01)
    bodds = c2.number_input("Team B ML odds", 1.01, 20.0, 4.50, .01)
    total = c3.number_input("O/U total", .5, 8.5, 2.5, .25)
    open_total = c4.number_input("Opening total", .5, 8.5, 2.5, .25)
    d1,d2,d3,d4,d5 = st.columns(5)
    pace = d1.slider("Pace", 0, 10, 4)
    weather = d2.slider("Bad weather", 0, 10, 3)
    pressure = d3.slider("Pressure/caution", 0, 10, 7)
    mustwin = d4.slider("Must-win attack", 0, 10, 5)
    ref = d5.slider("Ref cards", 0, 10, 5)

    if st.button("Analyze Soccer AI", type="primary"):
        ascore = soccer_strength(ar, af, axgf, axga, ainj, amot, arest, afat, avenue)
        bscore = soccer_strength(br, bf, bxgf, bxga, binj, bmot, brest, bfat, bvenue)
        diff = ascore-bscore
        over, under, proj = soccer_total_score(total, axgf, bxgf, axga, bxga, pace, weather, pressure, mustwin, total-open_total, ref)
        rows = [
            pick_row("Soccer", f"{a} vs {b}", "ML", f"{a} ML", clamp(58+diff*.56), aodds, f"Strength {ascore:.1f} vs {bscore:.1f}", bankroll, risk_pct, kelly_cap),
            pick_row("Soccer", f"{a} vs {b}", "ML", f"{b} ML", clamp(58-diff*.56), bodds, "Upset check", bankroll, risk_pct, kelly_cap),
            pick_row("Soccer", f"{a} vs {b}", "Total", f"Over {total}", over, 1.91, f"Projected goals {proj:.2f}", bankroll, risk_pct, kelly_cap),
            pick_row("Soccer", f"{a} vs {b}", "Total", f"Under {total}", under, 1.91, f"Projected goals {proj:.2f}", bankroll, risk_pct, kelly_cap),
        ]
        df = rank(rows)
        render_pick_card(df.iloc[0], "Soccer AI Recommendation")
        st.dataframe(df, use_container_width=True)

# -----------------------------
# NBA
# -----------------------------
with tabs[4]:
    st.subheader("🏀 NBA AI v4")
    match = st.text_input("NBA Match", "NYK vs SAS")
    total = st.number_input("NBA O/U", 180.5, 260.5, 216.5, .5)
    c1,c2,c3 = st.columns(3)
    pace = c1.slider("Pace", 0, 10, 5)
    offense = c2.number_input("Combined offense rating", 95.0, 130.0, 113.0, .5)
    defense = c3.number_input("Combined defense allowed", 95.0, 130.0, 112.0, .5)
    injuries = st.slider("Injuries support Under", 0, 10, 4)
    rest = st.slider("Rest/fatigue slow game", 0, 10, 4)
    playoff = st.slider("Playoff/pressure Under", 0, 10, 3)
    open_total = st.number_input("Opening NBA total", 180.5, 260.5, 217.5, .5)
    public = st.slider("Public Over %", 0, 100, 60)
    if st.button("Analyze NBA AI", type="primary"):
        over, under = nba_scores(total, pace, offense, defense, injuries, rest, total-open_total, public, playoff)
        df = rank([
            pick_row("NBA", match, "Total", f"Over {total}", over, 1.91, "Pace/offense model", bankroll, risk_pct, kelly_cap),
            pick_row("NBA", match, "Total", f"Under {total}", under, 1.91, "Pace/injury/pressure model", bankroll, risk_pct, kelly_cap),
        ])
        render_pick_card(df.iloc[0], "NBA AI Recommendation")
        st.dataframe(df, use_container_width=True)

# -----------------------------
# NFL
# -----------------------------
with tabs[5]:
    st.subheader("🏈 NFL AI v4")
    match = st.text_input("NFL Match", "SEA vs WAS")
    total = st.number_input("NFL O/U", 30.5, 60.5, 44.5, .5)
    c1,c2,c3 = st.columns(3)
    pace = c1.slider("NFL pace", 0, 10, 5)
    run = c2.slider("Run rate / clock drain", 0, 10, 6)
    weather = c3.slider("Weather Under", 0, 10, 4)
    defense = st.slider("Defense strength", 0, 10, 6)
    turnover = st.slider("Turnover / short field risk", 0, 10, 4)
    redzone = st.slider("Redzone efficiency Over", 0, 10, 5)
    primetime = st.slider("Prime-time Under angle", 0, 10, 3)
    open_total = st.number_input("Opening NFL total", 30.5, 60.5, 45.0, .5)
    if st.button("Analyze NFL AI", type="primary"):
        over, under = nfl_scores(total, pace, run, weather, defense, turnover, redzone, total-open_total, primetime)
        df = rank([
            pick_row("NFL", match, "Total", f"Over {total}", over, 1.91, "Tempo/redzone model", bankroll, risk_pct, kelly_cap),
            pick_row("NFL", match, "Total", f"Under {total}", under, 1.91, "Clock/weather/defense model", bankroll, risk_pct, kelly_cap),
        ])
        render_pick_card(df.iloc[0], "NFL AI Recommendation")
        st.dataframe(df, use_container_width=True)

# -----------------------------
# Live Bet
# -----------------------------
with tabs[6]:
    st.subheader("🔥 Live Bet AI v4")
    sport = st.selectbox("Sport", ["Soccer","MLB","NBA","NFL"])
    c1,c2,c3,c4 = st.columns(4)
    progress = c1.slider("Minute / progress", 1, 120, 25)
    score_units = c2.slider("Current goals/runs", 0, 20, 0)
    live_total_value = c3.number_input("Live total", .5, 300.5, 2.5, .25)
    shots = c4.slider("Shots/pressure stat", 0, 30, 2)
    d1,d2,d3,d4,d5 = st.columns(5)
    chances = d1.slider("Big chances", 0, 20, 0)
    attacks = d2.slider("Danger attacks", 0, 200, 18)
    tempo = d3.slider("Live tempo", 0, 10, 3)
    pressure = d4.slider("Favorite pressure", 0, 10, 4)
    weather = d5.slider("Under condition", 0, 10, 2)
    line_value = st.slider("Line value still good", 0, 10, 5)
    clock = st.slider("Clock drain / slow game", 0, 10, 5)
    if st.button("Analyze Live Bet", type="primary"):
        score = live_under(progress, score_units, live_total_value, shots, chances, attacks, tempo, pressure, weather, line_value, clock)
        row = pick_row(sport, "Live Game", "Live Total", f"Live Under {live_total_value}", score, 1.91, f"Progress {progress}, score {score_units}", bankroll, risk_pct, kelly_cap)
        render_pick_card(row, "Live Bet AI")
        st.dataframe(pd.DataFrame([row]), use_container_width=True)

# -----------------------------
# Sharp Money
# -----------------------------
with tabs[7]:
    st.subheader("📈 Sharp Money v4")
    c1,c2,c3 = st.columns(3)
    open_line = c1.number_input("Opening line", -20.0, 300.0, 7.5, .25)
    current_line = c2.number_input("Current line", -20.0, 300.0, 7.0, .25)
    side = c3.selectbox("Side", ["Under","Over","Favorite","Dog"])
    d1,d2,d3,d4 = st.columns(4)
    public = d1.slider("Public %", 0, 100, 65)
    tickets = d2.slider("Tickets %", 0, 100, 62)
    handle = d3.slider("Handle %", 0, 100, 78)
    minutes = d4.slider("Minutes since move", 1, 180, 15)
    if st.button("Analyze Sharp Money", type="primary"):
        score, clv, note = sharp_score(open_line, current_line, public, tickets, handle, side, minutes)
        row = pick_row("Market", "Line Movement", "Sharp", side, score, 1.91, f"CLV projection {clv} • {note}", bankroll, risk_pct, kelly_cap)
        render_pick_card(row, "Sharp Money Alert")
        st.dataframe(pd.DataFrame([row]), use_container_width=True)

# -----------------------------
# Tracker
# -----------------------------
with tabs[8]:
    st.subheader("🧾 Bet Tracker Pro")
    if "bets_v4" not in st.session_state:
        st.session_state.bets_v4 = []
    c1,c2 = st.columns(2)
    with c1:
        d = st.date_input("Date", date.today())
        sport = st.selectbox("Tracker sport", ["MLB","Soccer","NBA","NFL","Other"])
        match = st.text_input("Tracker match", "SEA vs BAL")
        pick = st.text_input("Pick", "Under 7.5")
    with c2:
        odds = st.number_input("Odds", 1.01, 20.0, 1.91, .01)
        amount = st.number_input("Stake $", 0.0, 100000.0, 100.0, 5.0)
        result = st.selectbox("Result", ["Pending","Win","Loss","Push"])
        score = st.slider("AI Score", 0, 100, 85)
    if st.button("Add Bet"):
        profit = amount*(odds-1) if result=="Win" else (-amount if result=="Loss" else 0)
        st.session_state.bets_v4.append({
            "Date":str(d), "Sport":sport, "Match":match, "Pick":pick, "Odds":odds,
            "Stake":amount, "AI Score":score, "Result":result, "Profit":round(profit,2)
        })
    df = pd.DataFrame(st.session_state.bets_v4)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        settled = df[df["Result"].isin(["Win","Loss","Push"])]
        total_profit = settled["Profit"].sum() if not settled.empty else 0
        total_stake = settled["Stake"].sum() if not settled.empty else 0
        wins = (settled["Result"]=="Win").sum()
        losses = (settled["Result"]=="Loss").sum()
        winrate = wins/(wins+losses)*100 if wins+losses>0 else 0
        c1,c2,c3 = st.columns(3)
        c1.metric("Profit", f"${total_profit:.2f}")
        c2.metric("ROI", f"{(total_profit/total_stake*100 if total_stake else 0):.1f}%")
        c3.metric("Win Rate", f"{winrate:.1f}%")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "bet_tracker_v4.csv", "text/csv")
    else:
        st.info("Chưa có kèo nào.")
