import streamlit as st
import pandas as pd
import math
from datetime import date

# ============================================================
# SPORTS BETTING AI ULTIMATE v3 PRO
# iPad/Web Streamlit App
# Modules:
# - Pro Dashboard
# - Today's Best Bets builder
# - Soccer / World Cup AI
# - MLB Under Pro v3
# - NBA / NFL models
# - Live Bet AI: BET NOW / WAIT / PASS
# - Sharp Money: RLM / Steam / CLV projection
# - Bankroll + Kelly stake
# - Bet Tracker
# ============================================================

st.set_page_config(
    page_title="Sports Betting AI Ultimate v3 Pro",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Global styles
# -----------------------------
st.markdown("""
<style>
.block-container {padding-top: 1.2rem;}
[data-testid="stMetricValue"] {font-size: 1.9rem;}
.pick-card {
    border: 1px solid rgba(120,120,120,0.25);
    border-radius: 14px;
    padding: 14px;
    margin: 8px 0;
    background: rgba(120,120,120,0.06);
}
.elite {border-left: 8px solid #00c853;}
.strong {border-left: 8px solid #64dd17;}
.playable {border-left: 8px solid #ffd600;}
.pass {border-left: 8px solid #ff5252;}
.small-note {font-size: 0.88rem; opacity: 0.8;}
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

def implied_prob(decimal_odds):
    return 100 / decimal_odds if decimal_odds and decimal_odds > 1 else 0

def decimal_profit(decimal_odds):
    return max(decimal_odds - 1, 0)

def model_prob_from_score(score):
    return clamp(45 + (score - 60) * 0.72, 5, 94)

def kelly_fraction(model_prob_pct, decimal_odds):
    p = model_prob_pct / 100
    b = decimal_odds - 1
    if b <= 0:
        return 0
    q = 1 - p
    k = (b * p - q) / b
    return max(0, k)

def stars(score):
    score = float(score)
    if score >= 88: return "⭐⭐⭐⭐⭐"
    if score >= 80: return "⭐⭐⭐⭐"
    if score >= 70: return "⭐⭐⭐"
    if score >= 60: return "⭐⭐"
    return "⭐"

def grade(score):
    score = float(score)
    if score >= 88: return "ELITE"
    if score >= 80: return "STRONG"
    if score >= 70: return "PLAYABLE"
    if score >= 60: return "LEAN"
    return "PASS"

def grade_class(score):
    score = float(score)
    if score >= 88: return "elite"
    if score >= 80: return "strong"
    if score >= 70: return "playable"
    return "pass"

def action_label(score):
    if score >= 88:
        return "BET NOW"
    if score >= 80:
        return "PLAY"
    if score >= 70:
        return "SMALL / WAIT"
    if score >= 60:
        return "LEAN ONLY"
    return "PASS"

def stake_fixed(score, bankroll, risk_pct):
    base = bankroll * risk_pct / 100
    if score >= 88: return round(base * 1.25, 2)
    if score >= 80: return round(base, 2)
    if score >= 70: return round(base * 0.5, 2)
    return 0.0

def stake_kelly(score, odds, bankroll, max_pct):
    model = model_prob_from_score(score)
    kelly = kelly_fraction(model, odds)
    quarter = kelly * 0.25
    capped = min(quarter, max_pct / 100)
    return round(bankroll * capped, 2), round(kelly * 100, 2), round(quarter * 100, 2)

def pick_row(sport, match, market, pick, score, odds, note, bankroll, risk_pct, max_kelly_pct):
    score = clamp(score)
    model = model_prob_from_score(score)
    market_p = implied_prob(odds)
    edge = model - market_p
    k_stake, full_kelly, q_kelly = stake_kelly(score, odds, bankroll, max_kelly_pct)
    fixed = stake_fixed(score, bankroll, risk_pct)
    suggested = min(max(fixed, k_stake), bankroll * max_kelly_pct / 100)
    return {
        "Sport": sport,
        "Match": match,
        "Market": market,
        "Pick": pick,
        "Action": action_label(score),
        "Score": round(score, 1),
        "Stars": stars(score),
        "Grade": grade(score),
        "Odds": round(odds, 2),
        "Model %": round(model, 1),
        "Market %": round(market_p, 1),
        "Edge %": round(edge, 1),
        "Fixed Stake $": fixed,
        "Kelly 1/4 %": q_kelly,
        "Suggested $": round(suggested, 2),
        "Note": note,
    }

def sort_df(rows):
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(["Score", "Edge %"], ascending=False).reset_index(drop=True)

def render_best_card(row):
    css = grade_class(row["Score"])
    st.markdown(f"""
    <div class="pick-card {css}">
        <h3>{row['Stars']} {row['Pick']} — {row['Action']}</h3>
        <b>{row['Sport']} | {row['Match']} | {row['Market']}</b><br>
        Score: <b>{row['Score']}</b> / 100 &nbsp; | &nbsp;
        Edge: <b>{row['Edge %']}%</b> &nbsp; | &nbsp;
        Suggested: <b>${row['Suggested $']}</b><br>
        <span class="small-note">{row['Note']}</span>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# Scoring engines
# -----------------------------
def soccer_strength(rank, form, xgf, xga, injuries, motivation, rest, fatigue, home_advantage):
    rank_score = clamp(100 - rank * 0.75, 8, 100)
    form_score = clamp(form / 15 * 100)
    xg_score = clamp(xgf * 34 + (2.15 - xga) * 24)
    rest_score = clamp(rest * 13, 15, 100)
    score = rank_score*.18 + form_score*.22 + xg_score*.26 + motivation*10*.20 + rest_score*.10
    score += home_advantage * 1.8
    score -= injuries*4.1 + fatigue*2.6
    return clamp(score)

def soccer_total(total, axgf, bxgf, axga, bxga, pace, weather, pressure, must_win, move, ref_cards):
    projection = clamp((axgf + bxgf)*0.56 + (2.2-axga)*0.24 + (2.2-bxga)*0.24, .7, 4.8)
    over = 50 + (projection-total)*20 + pace*2.3 + must_win*1.9 + max(move,0)*8 - weather*2.5 - pressure*2.0 + ref_cards*.3
    under = 50 + (total-projection)*20 + weather*2.8 + pressure*2.6 + max(-move,0)*8 - pace*2.1 - must_win*1.5 + ref_cards*.8
    return clamp(over), clamp(under), projection

def mlb_expected_runs(total, pitcher_a, pitcher_b, bullpen, park, weather, ump, offense_cold):
    # Lower projection favors Under
    raw = 9.2
    raw -= (pitcher_a + pitcher_b) * 0.22
    raw -= bullpen * 0.13
    raw -= park * 0.12
    raw -= weather * 0.16
    raw -= ump * 0.10
    raw -= offense_cold * 0.15
    return max(4.0, min(12.5, raw))

def mlb_under_score(total, pitcher_a, pitcher_b, bullpen, park, weather, ump, offense_cold, line_drop, public_over, wind_in, ump_zone):
    projection = mlb_expected_runs(total, pitcher_a, pitcher_b, bullpen, park, weather, ump, offense_cold)
    score = 48 + (total - projection) * 9
    score += pitcher_a*1.15 + pitcher_b*1.15 + bullpen*1.4 + park*1.1 + weather*1.35 + ump*1.1
    score += offense_cold*1.25 + max(line_drop,0)*7 + max(public_over-58,0)*0.22 + wind_in*1.4 + ump_zone*1.0
    if total >= 9: score += 5
    if total <= 7: score -= 5
    return clamp(score), projection

def nba_total_score(total, pace, off_rating, def_rating, injuries_under, rest_slow, line_move, public_over):
    over = 50 + (pace-5)*3.1 + (off_rating-112)*0.7 - (def_rating-112)*0.35 + max(line_move,0)*5 - injuries_under*1.4
    under = 50 - (pace-5)*3.1 - (off_rating-112)*0.7 + (def_rating-112)*0.45 + injuries_under*2.0 + rest_slow*1.3 + max(-line_move,0)*5 + max(public_over-60,0)*0.22
    return clamp(over), clamp(under)

def nfl_total_score(total, pace, run_rate, weather_under, defense_strength, turnover_risk, redzone, line_move):
    over = 50 + (pace-5)*2.8 - run_rate*1.35 - weather_under*2.4 - defense_strength*1.45 + turnover_risk*1.1 + redzone*1.4 + max(line_move,0)*6
    under = 50 - (pace-5)*2.8 + run_rate*1.6 + weather_under*2.8 + defense_strength*1.9 - turnover_risk*.8 - redzone*.9 + max(-line_move,0)*6
    return clamp(over), clamp(under)

def live_under_score(progress, score_units, live_total, shots, chances, attacks, tempo, pressure, weather, line_value):
    score = 48
    if progress >= 20 and score_units == 0: score += 16
    if progress >= 30 and score_units <= 1: score += 12
    if progress >= 55 and score_units <= 1: score += 8
    score += clamp(live_total - score_units, 0, 5)*4.5
    score += line_value*1.8 + weather*2.1
    score -= shots*3.0 + chances*7.2 + attacks*.16 + tempo*2.6 + pressure*2.2
    if score_units >= 3 and progress < 55: score -= 25
    if progress < 15: score -= 8
    return clamp(score)

def sharp_money_score(open_line, current_line, public, tickets, handle, side, minutes_since_move):
    move = current_line - open_line
    score = 50
    notes = []
    if handle - tickets >= 15:
        score += 15; notes.append("Handle cao hơn tickets: dấu hiệu tiền lớn.")
    if public >= 60 and ((side == "Under" and move < 0) or (side == "Over" and move > 0) or (side == "Dog" and move > 0)):
        score += 15; notes.append("Line đi chống/khác public.")
    if abs(move) >= .5:
        score += 9; notes.append("Line move mạnh.")
    if abs(move) >= .5 and minutes_since_move <= 20:
        score += 10; notes.append("Steam move nhanh.")
    clv = abs(move) * 6 + max(handle-tickets, 0)*.25
    if clv >= 10:
        score += 6; notes.append("CLV projection tốt.")
    if not notes:
        notes.append("Sharp signal chưa rõ.")
    return clamp(score), round(clv, 1), " | ".join(notes)

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("🏆 Ultimate v3 Pro")
bankroll = st.sidebar.number_input("Bankroll ($)", 10.0, 100000.0, 1000.0, 25.0)
risk_pct = st.sidebar.slider("Fixed risk mỗi kèo (%)", 0.1, 5.0, 1.0, 0.1)
max_kelly_pct = st.sidebar.slider("Kelly cap tối đa (%)", 0.25, 5.0, 2.0, 0.25)
min_score = st.sidebar.slider("Chỉ hiện kèo từ điểm", 50, 95, 70)
elite_only = st.sidebar.checkbox("Chỉ hiện kèo 85+", value=False)
st.sidebar.warning("Kỷ luật vốn: không all-in, không gỡ thua, kèo thấp thì bỏ.")

# -----------------------------
# Main
# -----------------------------
st.title("🏆 Sports Betting AI Ultimate v3 Pro")
st.caption("Best Bets • AI Score • Kelly Stake • MLB Under Pro • Soccer • NBA • NFL • Live Bet • Sharp Money")

tabs = st.tabs([
    "📊 Pro Dashboard",
    "⭐ Best Bets",
    "⚽ Soccer",
    "⚾ MLB Under Pro",
    "🏀 NBA",
    "🏈 NFL",
    "🔥 Live Bet",
    "📈 Sharp Money",
    "🧾 Tracker",
])

# Dashboard
with tabs[0]:
    st.subheader("📊 Pro Dashboard")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("88+", "ELITE", "BET NOW")
    c2.metric("80–87", "STRONG", "PLAY")
    c3.metric("70–79", "PLAYABLE", "SMALL/WAIT")
    c4.metric("<70", "PASS", "NO BET")

    st.info("V3 Pro thêm Kelly stake, CLV projection, Steam Move, AI action label và Today’s Best Bets. Dữ liệu vẫn nhập tay để an toàn và dễ dùng trên iPad.")

    st.write("### Cách dùng nhanh")
    st.write("1. Vào tab từng môn để nhập odds/dữ liệu. 2. Chỉ đánh kèo 80+. 3. 88+ mới xem là kèo mạnh. 4. Live Bet phải có đủ tempo/pressure/chances.")

# Best Bets
with tabs[1]:
    st.subheader("⭐ Today's Best Bets Builder")
    st.write("Nhập nhanh 3 kèo bạn đang cân nhắc, bot sẽ xếp hạng.")
    rows = []
    for i in range(1, 4):
        with st.expander(f"Kèo #{i}", expanded=(i == 1)):
            c1, c2, c3 = st.columns(3)
            sport = c1.selectbox(f"Sport {i}", ["MLB", "Soccer", "NBA", "NFL"], key=f"bb_sport_{i}")
            match = c2.text_input(f"Match {i}", f"Game {i}", key=f"bb_match_{i}")
            pick = c3.text_input(f"Pick {i}", f"Under", key=f"bb_pick_{i}")
            c4, c5, c6 = st.columns(3)
            score_input = c4.slider(f"Model score {i}", 0, 100, 75, key=f"bb_score_{i}")
            odds = c5.number_input(f"Odds {i}", 1.01, 20.0, 1.91, 0.01, key=f"bb_odds_{i}")
            note = c6.text_input(f"Note {i}", "manual candidate", key=f"bb_note_{i}")
            rows.append(pick_row(sport, match, "Manual", pick, score_input, odds, note, bankroll, risk_pct, max_kelly_pct))
    df = sort_df(rows)
    threshold = 85 if elite_only else min_score
    st.dataframe(df[df["Score"] >= threshold], use_container_width=True)
    if not df.empty:
        render_best_card(df.iloc[0])

# Soccer
with tabs[2]:
    st.subheader("⚽ Soccer / World Cup AI")
    col1, col2 = st.columns(2)
    with col1:
        a = st.text_input("Team A", "France")
        ar = st.number_input("Team A rank", 1, 210, 2)
        af = st.slider("Team A form last 5", 0, 15, 12)
        axgf = st.number_input("Team A xG For", 0.0, 5.0, 2.10, .05)
        axga = st.number_input("Team A xG Against", 0.0, 5.0, .90, .05)
        ainj = st.slider("Team A injuries", 0, 10, 2)
        amot = st.slider("Team A motivation", 0, 10, 8)
        arest = st.slider("Team A rest days", 0, 10, 5)
        afat = st.slider("Team A fatigue", 0, 10, 2)
        ahome = st.slider("Team A home/venue edge", -5, 5, 0)
    with col2:
        b = st.text_input("Team B", "Norway")
        br = st.number_input("Team B rank", 1, 210, 38)
        bf = st.slider("Team B form last 5", 0, 15, 9)
        bxgf = st.number_input("Team B xG For", 0.0, 5.0, 1.60, .05)
        bxga = st.number_input("Team B xG Against", 0.0, 5.0, 1.15, .05)
        binj = st.slider("Team B injuries", 0, 10, 3)
        bmot = st.slider("Team B motivation", 0, 10, 8)
        brest = st.slider("Team B rest days", 0, 10, 5)
        bfat = st.slider("Team B fatigue", 0, 10, 3)
        bhome = st.slider("Team B home/venue edge", -5, 5, 0)

    c1, c2, c3, c4 = st.columns(4)
    aodds = c1.number_input("Team A ML odds", 1.01, 20.0, 1.85, .01)
    bodds = c2.number_input("Team B ML odds", 1.01, 20.0, 4.20, .01)
    total = c3.number_input("O/U total", .5, 8.5, 2.5, .25)
    open_total = c4.number_input("Opening total", .5, 8.5, 2.5, .25)

    d1, d2, d3, d4, d5 = st.columns(5)
    pace = d1.slider("Pace", 0, 10, 5)
    weather = d2.slider("Bad weather", 0, 10, 2)
    pressure = d3.slider("Pressure/caution", 0, 10, 6)
    mustwin = d4.slider("Must-win attack", 0, 10, 5)
    ref_cards = d5.slider("Ref card tendency", 0, 10, 5)

    if st.button("Analyze Soccer", type="primary"):
        ascore = soccer_strength(ar, af, axgf, axga, ainj, amot, arest, afat, ahome)
        bscore = soccer_strength(br, bf, bxgf, bxga, binj, bmot, brest, bfat, bhome)
        diff = ascore - bscore
        over, under, proj = soccer_total(total, axgf, bxgf, axga, bxga, pace, weather, pressure, mustwin, total-open_total, ref_cards)
        rows = [
            pick_row("Soccer", f"{a} vs {b}", "ML", f"{a} ML", clamp(58+diff*.56), aodds, f"Strength {ascore:.1f} vs {bscore:.1f}", bankroll, risk_pct, max_kelly_pct),
            pick_row("Soccer", f"{a} vs {b}", "ML", f"{b} ML", clamp(58-diff*.56), bodds, "Upset model", bankroll, risk_pct, max_kelly_pct),
            pick_row("Soccer", f"{a} vs {b}", "Total", f"Over {total}", over, 1.91, f"Projected goals {proj:.2f}", bankroll, risk_pct, max_kelly_pct),
            pick_row("Soccer", f"{a} vs {b}", "Total", f"Under {total}", under, 1.91, f"Projected goals {proj:.2f}", bankroll, risk_pct, max_kelly_pct),
        ]
        df = sort_df(rows)
        threshold = 85 if elite_only else min_score
        st.dataframe(df[df["Score"] >= threshold], use_container_width=True)
        render_best_card(df.iloc[0])

# MLB
with tabs[3]:
    st.subheader("⚾ MLB Under Pro v3")
    c1, c2 = st.columns(2)
    with c1:
        match = st.text_input("MLB Match", "SEA vs BAL")
        total = st.number_input("Game total", 5.5, 14.5, 8.0, .5)
        p1 = st.slider("Pitcher A quality", 0, 10, 7)
        p2 = st.slider("Pitcher B quality", 0, 10, 7)
        bullpen = st.slider("Bullpen freshness", 0, 10, 7)
        cold = st.slider("Both offenses cold", 0, 10, 6)
    with c2:
        park = st.slider("Park supports Under", 0, 10, 6)
        weather = st.slider("Weather supports Under", 0, 10, 5)
        ump = st.slider("Umpire Under tendency", 0, 10, 5)
        wind_in = st.slider("Wind blowing in", 0, 10, 4)
        ump_zone = st.slider("Wide strike zone", 0, 10, 5)
        open_total = st.number_input("Opening total MLB", 5.5, 14.5, 8.5, .5)
        public_over = st.slider("Public on Over %", 0, 100, 62)

    if st.button("Analyze MLB Under", type="primary"):
        score, projection = mlb_under_score(total, p1, p2, bullpen, park, weather, ump, cold, open_total-total, public_over, wind_in, ump_zone)
        row = pick_row("MLB", match, "Total", f"Under {total}", score, 1.91, f"Projected runs {projection:.2f} | Line drop {open_total-total:+.1f}", bankroll, risk_pct, max_kelly_pct)
        st.dataframe(pd.DataFrame([row]), use_container_width=True)
        render_best_card(row)
        if score >= 88:
            st.success("MLB Under rất mạnh. Nếu live vẫn ít hit/traffic sau 2 innings thì càng đẹp.")
        elif score >= 80:
            st.info("Under đáng đánh, nhưng vẫn nên kiểm tra lineup và bullpen trước trận.")
        else:
            st.warning("Chưa đủ mạnh. Nên chờ live.")

# NBA
with tabs[4]:
    st.subheader("🏀 NBA AI")
    match = st.text_input("NBA Match", "NYK vs SAS")
    total = st.number_input("NBA O/U", 180.5, 260.5, 216.5, .5)
    c1, c2, c3 = st.columns(3)
    pace = c1.slider("NBA pace", 0, 10, 5)
    offense = c2.number_input("Combined offense rating", 95.0, 130.0, 113.0, .5)
    defense = c3.number_input("Combined defense allowed", 95.0, 130.0, 112.0, .5)
    injuries = st.slider("Injuries support Under", 0, 10, 4)
    rest_slow = st.slider("Rest / fatigue slow game", 0, 10, 4)
    open_total = st.number_input("Opening NBA total", 180.5, 260.5, 217.5, .5)
    public = st.slider("Public Over %", 0, 100, 60)

    if st.button("Analyze NBA", type="primary"):
        over, under = nba_total_score(total, pace, offense, defense, injuries, rest_slow, total-open_total, public)
        df = sort_df([
            pick_row("NBA", match, "Total", f"Over {total}", over, 1.91, "Pace/offense model", bankroll, risk_pct, max_kelly_pct),
            pick_row("NBA", match, "Total", f"Under {total}", under, 1.91, "Pace/injury/line model", bankroll, risk_pct, max_kelly_pct),
        ])
        st.dataframe(df, use_container_width=True)
        render_best_card(df.iloc[0])

# NFL
with tabs[5]:
    st.subheader("🏈 NFL AI")
    match = st.text_input("NFL Match", "SEA vs WAS")
    total = st.number_input("NFL O/U", 30.5, 60.5, 44.5, .5)
    c1, c2, c3 = st.columns(3)
    pace = c1.slider("NFL pace", 0, 10, 5)
    run = c2.slider("Run rate / clock drain", 0, 10, 6)
    weather = c3.slider("Weather supports Under", 0, 10, 4)
    defense = st.slider("Defense strength", 0, 10, 6)
    turnover = st.slider("Turnover / short field risk", 0, 10, 4)
    redzone = st.slider("Red zone efficiency supports Over", 0, 10, 5)
    open_total = st.number_input("Opening NFL total", 30.5, 60.5, 45.0, .5)

    if st.button("Analyze NFL", type="primary"):
        over, under = nfl_total_score(total, pace, run, weather, defense, turnover, redzone, total-open_total)
        df = sort_df([
            pick_row("NFL", match, "Total", f"Over {total}", over, 1.91, "Tempo/redzone model", bankroll, risk_pct, max_kelly_pct),
            pick_row("NFL", match, "Total", f"Under {total}", under, 1.91, "Clock/weather/defense model", bankroll, risk_pct, max_kelly_pct),
        ])
        st.dataframe(df, use_container_width=True)
        render_best_card(df.iloc[0])

# Live Bet
with tabs[6]:
    st.subheader("🔥 Live Bet AI — BET NOW / WAIT / PASS")
    sport = st.selectbox("Sport", ["Soccer", "MLB", "NBA", "NFL"])
    c1, c2, c3, c4 = st.columns(4)
    progress = c1.slider("Minute / progress", 1, 120, 25)
    score_units = c2.slider("Current goals/runs", 0, 20, 0)
    live_total = c3.number_input("Live total", .5, 300.5, 2.5, .25)
    shots = c4.slider("Shots on target / pressure stat", 0, 30, 2)
    d1, d2, d3, d4, d5 = st.columns(5)
    chances = d1.slider("Big chances", 0, 20, 0)
    attacks = d2.slider("Danger attacks", 0, 200, 18)
    tempo = d3.slider("Live tempo", 0, 10, 3)
    pressure = d4.slider("Favorite pressure", 0, 10, 4)
    weather = d5.slider("Live Under condition", 0, 10, 2)
    line_value = st.slider("Live line value still good", 0, 10, 5)

    if st.button("Analyze Live Under", type="primary"):
        score = live_under_score(progress, score_units, live_total, shots, chances, attacks, tempo, pressure, weather, line_value)
        row = pick_row(sport, "Live Game", "Live Total", f"Live Under {live_total}", score, 1.91, f"Progress {progress}, score units {score_units}", bankroll, risk_pct, max_kelly_pct)
        st.dataframe(pd.DataFrame([row]), use_container_width=True)
        render_best_card(row)

# Sharp Money
with tabs[7]:
    st.subheader("📈 Sharp Money Pro — RLM / Steam / CLV")
    c1, c2, c3 = st.columns(3)
    open_line = c1.number_input("Opening line", -20.0, 300.0, 2.5, .25)
    current_line = c2.number_input("Current line", -20.0, 300.0, 2.25, .25)
    side = c3.selectbox("Side", ["Under", "Over", "Favorite", "Dog"])
    d1, d2, d3, d4 = st.columns(4)
    public = d1.slider("Public %", 0, 100, 65)
    tickets = d2.slider("Tickets %", 0, 100, 62)
    handle = d3.slider("Handle %", 0, 100, 78)
    minutes = d4.slider("Minutes since move", 1, 180, 15)

    if st.button("Analyze Sharp Money", type="primary"):
        score, clv, note = sharp_money_score(open_line, current_line, public, tickets, handle, side, minutes)
        row = pick_row("Market", "Line Movement", "Sharp", side, score, 1.91, f"CLV projection {clv} | {note}", bankroll, risk_pct, max_kelly_pct)
        st.dataframe(pd.DataFrame([row]), use_container_width=True)
        render_best_card(row)
        st.info(note)

# Tracker
with tabs[8]:
    st.subheader("🧾 Bet Tracker")
    if "bets_v3" not in st.session_state:
        st.session_state.bets_v3 = []

    c1, c2 = st.columns(2)
    with c1:
        d = st.date_input("Date", date.today())
        sport = st.selectbox("Tracker sport", ["Soccer", "MLB", "NBA", "NFL", "Other"])
        match = st.text_input("Tracker match", "France vs Norway")
        pick = st.text_input("Pick", "France ML")
    with c2:
        odds = st.number_input("Odds", 1.01, 20.0, 1.91, .01)
        amount = st.number_input("Stake $", 0.0, 10000.0, 10.0, 1.0)
        result = st.selectbox("Result", ["Pending", "Win", "Loss", "Push"])
        score = st.slider("Bot score", 0, 100, 80)

    if st.button("Add Bet"):
        profit = amount*(odds-1) if result == "Win" else (-amount if result == "Loss" else 0)
        st.session_state.bets_v3.append({
            "Date": str(d),
            "Sport": sport,
            "Match": match,
            "Pick": pick,
            "Odds": odds,
            "Stake": amount,
            "Score": score,
            "Result": result,
            "Profit": round(profit, 2),
        })

    df = pd.DataFrame(st.session_state.bets_v3)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        settled = df[df["Result"].isin(["Win", "Loss", "Push"])]
        profit = settled["Profit"].sum() if not settled.empty else 0
        st.metric("Profit", f"${profit:.2f}")
        if not settled.empty and settled["Stake"].sum() > 0:
            st.metric("ROI", f"{profit / settled['Stake'].sum() * 100:.1f}%")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "bet_tracker_v3.csv", "text/csv")
    else:
        st.info("Chưa có kèo nào.")
