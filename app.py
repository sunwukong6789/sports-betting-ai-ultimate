import streamlit as st
import pandas as pd
from utils.ui import inject_css, render_card
from utils.ai_engine import pick_row, rank

st.set_page_config(
    page_title="Sports Betting AI Ultimate v7 Pro Max",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

st.sidebar.title("🏆 AI Ultimate v7")
bankroll = st.sidebar.number_input("Current Bankroll ($)", 10.0, 1000000.0, 10000.0, 100.0)
strategy = st.sidebar.selectbox("Betting Strategy", ["Kelly Criterion", "Flat Bet", "Conservative", "Aggressive"])
risk_pct = st.sidebar.slider("Risk per bet (%)", 0.1, 5.0, 1.5, .1)
kelly_cap = st.sidebar.slider("Max Bet / Kelly cap (%)", .25, 5.0, 2.0, .25)
min_score = st.sidebar.slider("Min AI Score", 50, 98, 70)
only_best = st.sidebar.checkbox("Only show best 85+", value=False)
st.sidebar.divider()
st.sidebar.selectbox("Quick Sport Filter", ["All Sports", "MLB", "Soccer", "NBA", "NFL"])
st.sidebar.selectbox("Market Filter", ["All Markets", "Under", "Over", "ML", "Spread"])
st.sidebar.success("All systems operational • v7.0 Pro Max")
st.sidebar.info("Use pages on the left for each sport module.")

st.title("🏆 Sports Betting AI Ultimate v7 Pro Max")
st.caption("AI Powered • Data Driven • Win More • Multi-page Streamlit Project")

rows = [
    pick_row("MLB", "SEA vs BAL", "Total", "Under 7.5", 94, 1.91, "Best bet • pitcher + weather + sharp", bankroll, risk_pct, kelly_cap, strategy),
    pick_row("MLB", "TB vs NYY", "Total", "Under 8.0", 89, 1.91, "RLM + bullpen fresh", bankroll, risk_pct, kelly_cap, strategy),
    pick_row("MLB", "CHC vs STL", "Total", "Under 8.5", 86, 1.91, "Park + wind + public over", bankroll, risk_pct, kelly_cap, strategy),
    pick_row("MLB", "CLE vs MIN", "Total", "Under 7.5", 85, 1.91, "Pitching edge + sharp under", bankroll, risk_pct, kelly_cap, strategy),
    pick_row("Soccer", "MCI vs BVB", "Total", "Under 3.5", 87, 1.91, "High value match", bankroll, risk_pct, kelly_cap, strategy),
    pick_row("NBA", "BOS vs MIA", "Total", "Under 214.5", 85, 1.91, "Slow pace + injuries", bankroll, risk_pct, kelly_cap, strategy),
    pick_row("NFL", "KC vs BUF", "Total", "Under 48.5", 84, 1.91, "Weather + run rate", bankroll, risk_pct, kelly_cap, strategy),
]
df = rank(rows)
render_card(df.iloc[0])

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Best Bets", "10", "Today")
c2.metric("Avg AI Score", "83.7", "Top 20")
c3.metric("Total Edge", "+11.2%", "Avg")
c4.metric("Win Rate 30D", "61.8%", "+3.4%")
c5.metric("ROI 30D", "+18.9%", "+4.1%")
c6.metric("Profit 30D", "$1,890", "+$245")

left, right = st.columns([1.25, 1])
with left:
    st.markdown('<div class="pro-card"><h3>⭐ Today’s Top 10 Best Bets</h3></div>', unsafe_allow_html=True)
    threshold = 85 if only_best else min_score
    st.dataframe(df[df["AI Score"] >= threshold], use_container_width=True)
with right:
    st.markdown('<div class="pro-card"><h3>🔥 Sharp Money Moves</h3></div>', unsafe_allow_html=True)
    sharp_df = pd.DataFrame([
        {"Matchup":"SEA vs BAL","Move":"7.5 → 7.0","Sharp %":"81%","Signal":"Strong Sharp"},
        {"Matchup":"TB vs NYY","Move":"8.0 → 7.5","Sharp %":"74%","Signal":"Strong Sharp"},
        {"Matchup":"CLE vs MIN","Move":"7.5 → 7.0","Sharp %":"69%","Signal":"Sharp"},
        {"Matchup":"LAD vs COL","Move":"11.0 → 10.5","Sharp %":"56%","Signal":"Public"},
    ])
    st.dataframe(sharp_df, use_container_width=True)

a,b,c,d = st.columns(4)
a.metric("AI Score Distribution", "68 Bets", "18% Elite")
b.metric("Win Probability", "83%", "Under model")
c.metric("Edge Distribution", "+17.2%", "Top edge")
d.metric("Sports Breakdown", "MLB 42", "Soccer 12")

st.markdown('<div class="pro-card"><h3>⭐ Upcoming High Value Matches</h3></div>', unsafe_allow_html=True)
upcoming = pd.DataFrame([
    {"Sport":"MLB","Match":"NYY vs BOS","Pick":"Under 8.0","AI Score":88,"Edge":"+13.2%"},
    {"Sport":"Soccer","Match":"MCI vs BVB","Pick":"Under 3.5","AI Score":87,"Edge":"+11.8%"},
    {"Sport":"NBA","Match":"BOS vs MIA","Pick":"Under 214.5","AI Score":85,"Edge":"+10.6%"},
    {"Sport":"NFL","Match":"KC vs BUF","Pick":"Under 48.5","AI Score":84,"Edge":"+9.9%"},
])
st.dataframe(upcoming, use_container_width=True)

st.markdown('<div class="footer">Sports Betting AI Ultimate v7 Pro Max • Bet Responsibly</div>', unsafe_allow_html=True)
