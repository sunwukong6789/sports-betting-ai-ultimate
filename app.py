import streamlit as st
import pandas as pd
from datetime import date

st.set_page_config(page_title="Sports Betting AI Ultimate v2", page_icon="🏆", layout="wide")

def clamp(x, lo=0, hi=100):
    return max(lo, min(hi, float(x)))

def implied_prob(odds):
    return 100 / odds if odds and odds > 1 else 0

def stars(score):
    score = float(score)
    if score >= 88: return "⭐⭐⭐⭐⭐"
    if score >= 78: return "⭐⭐⭐⭐"
    if score >= 68: return "⭐⭐⭐"
    if score >= 58: return "⭐⭐"
    return "⭐"

def grade(score):
    score = float(score)
    if score >= 88: return "ELITE"
    if score >= 78: return "STRONG"
    if score >= 68: return "PLAYABLE"
    if score >= 58: return "LEAN"
    return "PASS"

def stake(score, bankroll, risk_pct):
    base = bankroll * risk_pct / 100
    if score >= 88: return round(base * 1.25, 2)
    if score >= 78: return round(base, 2)
    if score >= 68: return round(base * 0.5, 2)
    return 0.0

def pick_row(sport, match, market, pick, score, odds, note, bankroll, risk_pct):
    model = clamp(45 + (score - 60) * 0.7, 5, 92)
    market_p = implied_prob(odds)
    return {
        "Sport": sport, "Match": match, "Market": market, "Pick": pick,
        "Score": round(score, 1), "Stars": stars(score), "Grade": grade(score),
        "Odds": odds, "Model %": round(model, 1), "Market %": round(market_p, 1),
        "Edge %": round(model - market_p, 1), "Stake $": stake(score, bankroll, risk_pct),
        "Note": note
    }

def sort_df(rows):
    df = pd.DataFrame(rows)
    if df.empty: return df
    return df.sort_values(["Score", "Edge %"], ascending=False).reset_index(drop=True)

def soccer_strength(rank, form, xgf, xga, injuries, motivation, rest, fatigue):
    rank_score = clamp(100 - rank * 0.75, 10, 100)
    form_score = clamp(form / 15 * 100)
    xg_score = clamp(xgf * 32 + (2.1 - xga) * 24)
    rest_score = clamp(rest * 13, 15, 100)
    score = rank_score * .20 + form_score * .22 + xg_score * .25 + motivation * 10 * .20 + rest_score * .13
    score -= injuries * 4.2 + fatigue * 2.4
    return clamp(score)

def soccer_total(total, axgf, bxgf, axga, bxga, pace, weather, pressure, must_win, move):
    projection = clamp((axgf + bxgf) * .55 + (2.2 - axga) * .25 + (2.2 - bxga) * .25, .8, 4.5)
    over = 50 + (projection - total) * 20 + pace * 2.2 + must_win * 1.8 + max(move, 0) * 8 - weather * 2.4 - pressure * 2
    under = 50 + (total - projection) * 20 + weather * 2.7 + pressure * 2.5 + max(-move, 0) * 8 - pace * 2 - must_win * 1.4
    return clamp(over), clamp(under), projection

def mlb_under(total, pitcher, bullpen, park, weather, ump, cold, line_drop, public_over):
    score = 42 + pitcher*2 + bullpen*1.7 + park*1.5 + weather*1.8 + ump*1.4 + cold*1.6
    score += max(line_drop, 0)*7 + max(public_over - 55, 0)*.25
    if total >= 9: score += 5
    if total <= 7: score -= 6
    return clamp(score)

def nba_total(total, pace, offense, defense, injuries, move, public_over):
    over = 50 + (pace-5)*3 + (offense-112)*.7 - (defense-112)*.4 + max(move,0)*5
    under = 50 - (pace-5)*3 - (offense-112)*.7 + (defense-112)*.5 + injuries*2 + max(-move,0)*5 + max(public_over-60,0)*.2
    return clamp(over), clamp(under)

def nfl_total(total, pace, run_rate, weather, defense, turnover, move):
    over = 50 + (pace-5)*2.8 - run_rate*1.4 - weather*2.5 - defense*1.6 + turnover*1.2 + max(move,0)*6
    under = 50 - (pace-5)*2.8 + run_rate*1.6 + weather*2.7 + defense*1.9 - turnover*.8 + max(-move,0)*6
    return clamp(over), clamp(under)

def live_under(progress, score_units, live_total, shots, chances, attacks, tempo, pressure, weather):
    score = 48
    if progress >= 20 and score_units == 0: score += 16
    if progress >= 30 and score_units <= 1: score += 12
    if progress >= 55 and score_units <= 1: score += 8
    score += clamp(live_total - score_units, 0, 5) * 4.5
    score -= shots*3.1 + chances*7 + attacks*.16 + tempo*2.6 + pressure*2.2
    score += weather*2.2
    if score_units >= 3: score -= 25
    if progress < 15: score -= 8
    return clamp(score)

def sharp(open_line, current_line, public, tickets, handle, side):
    move = current_line - open_line
    score = 50
    notes = []
    if handle - tickets >= 15:
        score += 15; notes.append("Handle cao hơn tickets: có tiền lớn.")
    if public >= 60 and ((side == "Under" and move < 0) or (side == "Dog" and move > 0)):
        score += 18; notes.append("Reverse line movement chống public.")
    if abs(move) >= .5:
        score += 8; notes.append("Line move mạnh.")
    if not notes: notes.append("Sharp signal chưa rõ.")
    return clamp(score), " | ".join(notes)

st.sidebar.title("🏆 Ultimate v2")
bankroll = st.sidebar.number_input("Bankroll ($)", 10.0, 100000.0, 1000.0, 25.0)
risk_pct = st.sidebar.slider("Risk mỗi kèo (%)", 0.1, 5.0, 1.0, 0.1)
min_score = st.sidebar.slider("Lọc kèo từ điểm", 50, 95, 68)
st.sidebar.warning("Không all-in. Kèo dưới 68 nên bỏ hoặc chờ live.")

st.title("🏆 Sports Betting AI Ultimate v2")
st.caption("Soccer/World Cup • MLB Under • NBA • NFL • Live Bet • Sharp Money • Bankroll")

tabs = st.tabs(["📊 Dashboard","⚽ Soccer","⚾ MLB Under","🏀 NBA","🏈 NFL","🔥 Live Bet","📈 Sharp Money","🧾 Tracker"])

with tabs[0]:
    st.subheader("Dashboard")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("88+", "ELITE", "1.25u max")
    c2.metric("78–87", "STRONG", "1u")
    c3.metric("68–77", "PLAYABLE", "0.5u")
    c4.metric("<68", "PASS", "Không đánh")
    st.info("Bản v2 thêm nhiều môn, live under, sharp money và tracker. Dữ liệu odds vẫn nhập tay.")

with tabs[1]:
    st.subheader("⚽ Soccer / World Cup")
    col1,col2 = st.columns(2)
    with col1:
        a = st.text_input("Team A","France")
        ar = st.number_input("Team A rank",1,210,2)
        af = st.slider("Team A form",0,15,12)
        axgf = st.number_input("Team A xG For",0.0,5.0,2.10,.05)
        axga = st.number_input("Team A xG Against",0.0,5.0,.90,.05)
        ainj = st.slider("Team A injuries",0,10,2)
        amot = st.slider("Team A motivation",0,10,8)
        arest = st.slider("Team A rest",0,10,5)
        afat = st.slider("Team A fatigue",0,10,2)
    with col2:
        b = st.text_input("Team B","Norway")
        br = st.number_input("Team B rank",1,210,38)
        bf = st.slider("Team B form",0,15,9)
        bxgf = st.number_input("Team B xG For",0.0,5.0,1.60,.05)
        bxga = st.number_input("Team B xG Against",0.0,5.0,1.15,.05)
        binj = st.slider("Team B injuries",0,10,3)
        bmot = st.slider("Team B motivation",0,10,8)
        brest = st.slider("Team B rest",0,10,5)
        bfat = st.slider("Team B fatigue",0,10,3)
    o1,o2,o3,o4 = st.columns(4)
    aodds = o1.number_input("Team A ML odds",1.01,20.0,1.85,.01)
    bodds = o2.number_input("Team B ML odds",1.01,20.0,4.20,.01)
    total = o3.number_input("O/U total",.5,8.5,2.5,.25)
    opentotal = o4.number_input("Opening total",.5,8.5,2.5,.25)
    p1,p2,p3,p4 = st.columns(4)
    pace = p1.slider("Pace",0,10,5)
    weather = p2.slider("Bad weather",0,10,2)
    pressure = p3.slider("Pressure/caution",0,10,6)
    mustwin = p4.slider("Must-win attack",0,10,5)
    if st.button("Analyze Soccer", type="primary"):
        ascore = soccer_strength(ar,af,axgf,axga,ainj,amot,arest,afat)
        bscore = soccer_strength(br,bf,bxgf,bxga,binj,bmot,brest,bfat)
        diff = ascore-bscore
        over, under, proj = soccer_total(total,axgf,bxgf,axga,bxga,pace,weather,pressure,mustwin,total-opentotal)
        rows = [
            pick_row("Soccer",f"{a} vs {b}","ML",f"{a} ML",clamp(58+diff*.55),aodds,f"Strength {ascore:.1f} vs {bscore:.1f}",bankroll,risk_pct),
            pick_row("Soccer",f"{a} vs {b}","ML",f"{b} ML",clamp(58-diff*.55),bodds,"Upset check",bankroll,risk_pct),
            pick_row("Soccer",f"{a} vs {b}","Total",f"Over {total}",over,1.91,f"Projected {proj:.2f}",bankroll,risk_pct),
            pick_row("Soccer",f"{a} vs {b}","Total",f"Under {total}",under,1.91,f"Projected {proj:.2f}",bankroll,risk_pct)
        ]
        df = sort_df(rows)
        st.dataframe(df[df["Score"]>=min_score], use_container_width=True)
        st.success(f"Best: {df.iloc[0]['Pick']} — {df.iloc[0]['Stars']} Score {df.iloc[0]['Score']}")

with tabs[2]:
    st.subheader("⚾ MLB Under Pro")
    c1,c2 = st.columns(2)
    match = c1.text_input("MLB Match","SEA vs BAL")
    total = c1.number_input("MLB total",5.5,14.5,8.0,.5)
    pitcher = c1.slider("Pitcher quality",0,10,7)
    bullpen = c1.slider("Bullpen fresh",0,10,7)
    cold = c1.slider("Offenses cold",0,10,6)
    park = c2.slider("Park Under",0,10,6)
    weather = c2.slider("Weather Under",0,10,5)
    ump = c2.slider("Ump Under",0,10,5)
    open_total = c2.number_input("Opening MLB total",5.5,14.5,8.5,.5)
    public_over = c2.slider("Public Over %",0,100,62)
    if st.button("Analyze MLB Under", type="primary"):
        sc = mlb_under(total,pitcher,bullpen,park,weather,ump,cold,open_total-total,public_over)
        row = pick_row("MLB",match,"Total",f"Under {total}",sc,1.91,f"Line drop {open_total-total:+.1f}, public over {public_over}%",bankroll,risk_pct)
        st.dataframe(pd.DataFrame([row]), use_container_width=True)

with tabs[3]:
    st.subheader("🏀 NBA")
    match = st.text_input("NBA Match","NYK vs SAS")
    total = st.number_input("NBA O/U",180.5,260.5,216.5,.5)
    c1,c2,c3 = st.columns(3)
    pace = c1.slider("NBA pace",0,10,5)
    offense = c2.number_input("Combined offense rating",95.0,130.0,113.0,.5)
    defense = c3.number_input("Combined defense allowed",95.0,130.0,112.0,.5)
    injuries = st.slider("Injuries support Under",0,10,4)
    open_total = st.number_input("Opening NBA total",180.5,260.5,217.5,.5)
    public = st.slider("NBA public Over %",0,100,60)
    if st.button("Analyze NBA", type="primary"):
        over, under = nba_total(total,pace,offense,defense,injuries,total-open_total,public)
        df = sort_df([
            pick_row("NBA",match,"Total",f"Over {total}",over,1.91,"Pace/offense model",bankroll,risk_pct),
            pick_row("NBA",match,"Total",f"Under {total}",under,1.91,"Pace/injury/line model",bankroll,risk_pct)
        ])
        st.dataframe(df, use_container_width=True)

with tabs[4]:
    st.subheader("🏈 NFL")
    match = st.text_input("NFL Match","SEA vs WAS")
    total = st.number_input("NFL O/U",30.5,60.5,44.5,.5)
    c1,c2,c3 = st.columns(3)
    pace = c1.slider("NFL pace",0,10,5)
    run = c2.slider("Run rate / clock drain",0,10,6)
    weather = c3.slider("Weather Under",0,10,4)
    defense = st.slider("Defense strength",0,10,6)
    turnover = st.slider("Turnover risk",0,10,4)
    open_total = st.number_input("Opening NFL total",30.5,60.5,45.0,.5)
    if st.button("Analyze NFL", type="primary"):
        over, under = nfl_total(total,pace,run,weather,defense,turnover,total-open_total)
        df = sort_df([
            pick_row("NFL",match,"Total",f"Over {total}",over,1.91,"Tempo model",bankroll,risk_pct),
            pick_row("NFL",match,"Total",f"Under {total}",under,1.91,"Clock/weather model",bankroll,risk_pct)
        ])
        st.dataframe(df, use_container_width=True)

with tabs[5]:
    st.subheader("🔥 Live Bet AI")
    sport = st.selectbox("Sport",["Soccer","MLB","NBA","NFL"])
    c1,c2,c3,c4 = st.columns(4)
    progress = c1.slider("Minute/progress",1,120,25)
    score_units = c2.slider("Current goals/runs",0,20,0)
    livetotal = c3.number_input("Live total",.5,300.5,2.5,.25)
    shots = c4.slider("Shots/pressure stat",0,30,2)
    c5,c6,c7,c8 = st.columns(4)
    chances = c5.slider("Big chances",0,20,0)
    attacks = c6.slider("Danger attacks",0,200,18)
    tempo = c7.slider("Live tempo",0,10,3)
    pressure = c8.slider("Favorite pressure",0,10,4)
    weather = st.slider("Live Under condition",0,10,2)
    if st.button("Analyze Live Under", type="primary"):
        sc = live_under(progress,score_units,livetotal,shots,chances,attacks,tempo,pressure,weather)
        row = pick_row(sport,"Live Game","Live Total",f"Live Under {livetotal}",sc,1.91,f"Progress {progress}, score units {score_units}",bankroll,risk_pct)
        st.dataframe(pd.DataFrame([row]), use_container_width=True)

with tabs[6]:
    st.subheader("📈 Sharp Money")
    c1,c2,c3 = st.columns(3)
    open_line = c1.number_input("Opening line",-20.0,300.0,2.5,.25)
    current_line = c2.number_input("Current line",-20.0,300.0,2.25,.25)
    side = c3.selectbox("Side",["Under","Over","Favorite","Dog"])
    c4,c5,c6 = st.columns(3)
    public = c4.slider("Public %",0,100,65)
    tickets = c5.slider("Tickets %",0,100,62)
    handle = c6.slider("Handle %",0,100,78)
    if st.button("Analyze Sharp", type="primary"):
        sc, note = sharp(open_line,current_line,public,tickets,handle,side)
        row = pick_row("Market","Line Movement","Sharp",side,sc,1.91,note,bankroll,risk_pct)
        st.dataframe(pd.DataFrame([row]), use_container_width=True)
        st.info(note)

with tabs[7]:
    st.subheader("🧾 Bet Tracker")
    if "bets" not in st.session_state:
        st.session_state.bets = []
    c1,c2 = st.columns(2)
    with c1:
        d = st.date_input("Date", date.today())
        sport = st.selectbox("Tracker sport",["Soccer","MLB","NBA","NFL","Other"])
        match = st.text_input("Tracker match","France vs Norway")
        pick = st.text_input("Pick","France ML")
    with c2:
        odds = st.number_input("Odds",1.01,20.0,1.91,.01)
        amount = st.number_input("Stake $",0.0,10000.0,10.0,1.0)
        result = st.selectbox("Result",["Pending","Win","Loss","Push"])
        score = st.slider("Bot score",0,100,75)
    if st.button("Add Bet"):
        profit = amount*(odds-1) if result=="Win" else (-amount if result=="Loss" else 0)
        st.session_state.bets.append({"Date":str(d),"Sport":sport,"Match":match,"Pick":pick,"Odds":odds,"Stake":amount,"Score":score,"Result":result,"Profit":round(profit,2)})
    df = pd.DataFrame(st.session_state.bets)
    if not df.empty:
        st.dataframe(df, use_container_width=True)
        settled = df[df["Result"].isin(["Win","Loss","Push"])]
        profit = settled["Profit"].sum()
        st.metric("Profit", f"${profit:.2f}")
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("Download CSV", csv, "bet_tracker.csv", "text/csv")
    else:
        st.info("Chưa có kèo nào.")
