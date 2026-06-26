import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime

# ============================================================
# WORLD CUP BETTING BOT PRO — v1 FINAL
# Author: ChatGPT
# Purpose: Support pre-match + live betting analysis for soccer
# Notes:
# - This app does NOT guarantee winning bets.
# - Use it as a decision-support tool, not financial advice.
# - Always bet responsibly.
# ============================================================

st.set_page_config(
    page_title="World Cup Betting Bot Pro",
    page_icon="⚽",
    layout="wide"
)

# -----------------------------
# Utility functions
# -----------------------------

def clamp(value, low, high):
    return max(low, min(high, value))


def safe_float(value, default=0.0):
    try:
        return float(value)
    except Exception:
        return default


def implied_probability(decimal_odds):
    if decimal_odds <= 1:
        return 0
    return 100 / decimal_odds


def value_edge(model_prob, market_prob):
    return model_prob - market_prob


def star_rating(score):
    if score >= 85:
        return "⭐⭐⭐⭐⭐"
    if score >= 75:
        return "⭐⭐⭐⭐"
    if score >= 65:
        return "⭐⭐⭐"
    if score >= 55:
        return "⭐⭐"
    return "⭐"


def confidence_label(score):
    if score >= 85:
        return "Very Strong"
    if score >= 75:
        return "Strong"
    if score >= 65:
        return "Playable"
    if score >= 55:
        return "Lean only"
    return "Pass"


def risk_label(score):
    if score >= 80:
        return "Low / Medium"
    if score >= 65:
        return "Medium"
    if score >= 50:
        return "Medium / High"
    return "High"


def american_to_decimal(odds):
    odds = safe_float(odds, 0)
    if odds == 0:
        return 0
    if odds > 0:
        return 1 + odds / 100
    return 1 + 100 / abs(odds)


def recommend_stake(score):
    if score >= 88:
        return "1.25u max"
    if score >= 80:
        return "1.00u"
    if score >= 72:
        return "0.75u"
    if score >= 65:
        return "0.50u"
    return "No bet / Watch live"


# -----------------------------
# Core scoring model
# -----------------------------

def team_strength_score(
    fifa_rank,
    form_points,
    xg_for,
    xg_against,
    injury_level,
    motivation,
    rest_days,
    travel_fatigue
):
    """
    Higher score = stronger team spot.
    fifa_rank: lower is better.
    form_points: last 5 match points, 0-15.
    xg_for / xg_against: attacking and defensive quality.
    injury_level: 0 none, 10 severe.
    motivation: 0-10.
    rest_days: days since previous match.
    travel_fatigue: 0-10.
    """
    rank_component = clamp(100 - fifa_rank * 0.75, 10, 100)
    form_component = clamp((form_points / 15) * 100, 0, 100)
    xg_component = clamp((xg_for * 32) + ((2.0 - xg_against) * 24), 0, 100)
    motivation_component = motivation * 10
    rest_component = clamp(rest_days * 12, 20, 100)

    penalty = injury_level * 4.5 + travel_fatigue * 2.8

    score = (
        rank_component * 0.20
        + form_component * 0.22
        + xg_component * 0.25
        + motivation_component * 0.20
        + rest_component * 0.13
        - penalty
    )
    return clamp(score, 0, 100)


def moneyline_score(team_a_score, team_b_score, odds_decimal):
    diff = team_a_score - team_b_score
    model_prob = clamp(50 + diff * 0.65, 5, 92)
    market_prob = implied_probability(odds_decimal)
    edge = value_edge(model_prob, market_prob)
    final_score = clamp(55 + diff * 0.55 + edge * 0.9, 0, 100)
    return final_score, model_prob, market_prob, edge


def handicap_score(team_score, opponent_score, handicap_line, odds_decimal):
    diff = team_score - opponent_score
    handicap_factor = -handicap_line * 8
    model_cover_prob = clamp(50 + diff * 0.55 + handicap_factor, 5, 90)
    market_prob = implied_probability(odds_decimal)
    edge = model_cover_prob - market_prob
    final_score = clamp(52 + diff * 0.50 + handicap_factor * 0.70 + edge * 0.85, 0, 100)
    return final_score, model_cover_prob, market_prob, edge


def total_score(
    total_line,
    team_a_xg_for,
    team_b_xg_for,
    team_a_xg_against,
    team_b_xg_against,
    pace,
    weather_bad,
    referee_cards,
    knockout_pressure,
    must_win_level,
    market_move_total
):
    """
    Returns over_score and under_score.
    weather_bad: 0-10, higher supports under.
    pace: 0-10, higher supports over.
    referee_cards: 0-10, high cards can slow game but also create pens/cards.
    knockout_pressure: 0-10, higher supports under.
    must_win_level: 0-10, higher supports over late-game.
    market_move_total: current total - opening total. Negative move supports under.
    """

    expected_goals = (
        team_a_xg_for * 0.35
        + team_b_xg_for * 0.35
        + (2.0 - team_a_xg_against) * 0.15
        + (2.0 - team_b_xg_against) * 0.15
    )

    base_total_projection = clamp(expected_goals, 0.6, 4.2)

    over_raw = (
        50
        + (base_total_projection - total_line) * 20
        + pace * 2.2
        + must_win_level * 1.7
        + max(market_move_total, 0) * 7
        - weather_bad * 2.4
        - knockout_pressure * 2.0
        - referee_cards * 0.7
    )

    under_raw = (
        50
        + (total_line - base_total_projection) * 20
        + weather_bad * 2.5
        + knockout_pressure * 2.4
        + referee_cards * 0.9
        + max(-market_move_total, 0) * 7
        - pace * 2.0
        - must_win_level * 1.4
    )

    return clamp(over_raw, 0, 100), clamp(under_raw, 0, 100), base_total_projection


def live_under_score(
    minute,
    current_goals,
    live_total,
    shots_on_target,
    big_chances,
    dangerous_attacks,
    cards,
    tempo,
    favorite_pressure,
    weather_bad
):
    """
    Designed for live under spots.
    Strong under conditions:
    - 0-0 or low score after 20-30 minutes
    - Low shots on target
    - Low big chances
    - Slow tempo
    - Bad weather
    - Live total still high enough
    """
    score = 50

    if minute >= 20 and current_goals == 0:
        score += 15
    if minute >= 30 and current_goals <= 1:
        score += 10
    if minute >= 55 and current_goals <= 1:
        score += 8

    score += clamp(live_total - current_goals, 0, 4) * 4

    score -= shots_on_target * 3.2
    score -= big_chances * 6.5
    score -= dangerous_attacks * 0.18
    score -= tempo * 2.6
    score -= favorite_pressure * 2.2

    score += weather_bad * 2.0
    score += cards * 0.6

    if current_goals >= 3:
        score -= 22
    if minute < 15:
        score -= 8

    return clamp(score, 0, 100)


def sharp_money_score(open_line, current_line, public_percent, bet_percent, handle_percent):
    """
    Basic sharp indicator:
    - Reverse line movement
    - Handle > bets
    - Line moves against public
    """
    line_move = current_line - open_line
    score = 50
    notes = []

    if handle_percent - bet_percent >= 15:
        score += 15
        notes.append("Handle cao hơn số vé: có dấu hiệu tiền lớn.")

    if public_percent >= 60 and line_move < 0:
        score += 18
        notes.append("Reverse line movement chống public.")

    if public_percent <= 40 and line_move > 0:
        score += 12
        notes.append("Line đi cùng phe ít người chơi.")

    if abs(line_move) >= 0.5:
        score += 8
        notes.append("Line movement đáng chú ý.")

    if not notes:
        notes.append("Chưa thấy tín hiệu sharp rõ.")

    return clamp(score, 0, 100), notes


def build_pick_table(picks):
    df = pd.DataFrame(picks)
    if df.empty:
        return df
    return df.sort_values(by="Score", ascending=False).reset_index(drop=True)


# -----------------------------
# UI
# -----------------------------

st.title("⚽ World Cup Betting Bot Pro — Final Version")
st.caption("Pre-match + Live Bet + ML/Handicap + Over/Under + Sharp Money + Risk Control")

with st.expander("⚠️ Lưu ý quan trọng", expanded=False):
    st.write(
        """
        Bot này chỉ hỗ trợ phân tích xác suất và rủi ro. Không có kèo nào chắc thắng 100%.
        Hãy quản lý vốn, không all-in, và tránh đuổi kèo khi thua.
        """
    )

tab1, tab2, tab3, tab4 = st.tabs(
    ["🏟️ Pre-match", "🔥 Live Bet", "📈 Sharp Money", "🧾 Bet Slip Builder"]
)

# -----------------------------
# Tab 1: Pre-match
# -----------------------------

with tab1:
    st.subheader("🏟️ Pre-match Analyzer")

    colA, colB = st.columns(2)

    with colA:
        team_a = st.text_input("Team A", "France")
        a_fifa_rank = st.number_input("Team A FIFA rank", 1, 210, 2)
        a_form = st.slider("Team A form points last 5 games", 0, 15, 12)
        a_xg_for = st.number_input("Team A xG For", 0.0, 5.0, 2.10, step=0.05)
        a_xg_against = st.number_input("Team A xG Against", 0.0, 5.0, 0.90, step=0.05)
        a_injuries = st.slider("Team A injury level", 0, 10, 2)
        a_motivation = st.slider("Team A motivation", 0, 10, 8)
        a_rest = st.slider("Team A rest days", 0, 10, 5)
        a_fatigue = st.slider("Team A travel fatigue", 0, 10, 2)

    with colB:
        team_b = st.text_input("Team B", "Norway")
        b_fifa_rank = st.number_input("Team B FIFA rank", 1, 210, 38)
        b_form = st.slider("Team B form points last 5 games", 0, 15, 9)
        b_xg_for = st.number_input("Team B xG For", 0.0, 5.0, 1.60, step=0.05)
        b_xg_against = st.number_input("Team B xG Against", 0.0, 5.0, 1.15, step=0.05)
        b_injuries = st.slider("Team B injury level", 0, 10, 3)
        b_motivation = st.slider("Team B motivation", 0, 10, 8)
        b_rest = st.slider("Team B rest days", 0, 10, 5)
        b_fatigue = st.slider("Team B travel fatigue", 0, 10, 3)

    st.divider()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        team_a_ml_odds = st.number_input(f"{team_a} ML decimal odds", 1.01, 20.0, 1.85, step=0.01)
    with c2:
        team_b_ml_odds = st.number_input(f"{team_b} ML decimal odds", 1.01, 20.0, 4.20, step=0.01)
    with c3:
        handicap_line = st.number_input(f"{team_a} handicap line", -5.0, 5.0, -0.75, step=0.25)
    with c4:
        handicap_odds = st.number_input("Handicap decimal odds", 1.01, 20.0, 1.95, step=0.01)

    d1, d2, d3, d4, d5 = st.columns(5)
    with d1:
        total_line = st.number_input("O/U line", 0.5, 8.5, 2.5, step=0.25)
    with d2:
        pace = st.slider("Match pace", 0, 10, 5)
    with d3:
        bad_weather = st.slider("Bad weather", 0, 10, 2)
    with d4:
        knockout_pressure = st.slider("Pressure / caution", 0, 10, 6)
    with d5:
        must_win = st.slider("Must-win attacking pressure", 0, 10, 5)

    referee_cards = st.slider("Referee cards tendency", 0, 10, 5)
    opening_total = st.number_input("Opening total", 0.5, 8.5, 2.5, step=0.25)
    market_move_total = total_line - opening_total

    if st.button("🔍 Analyze Pre-match", type="primary"):
        a_score = team_strength_score(
            a_fifa_rank, a_form, a_xg_for, a_xg_against,
            a_injuries, a_motivation, a_rest, a_fatigue
        )
        b_score = team_strength_score(
            b_fifa_rank, b_form, b_xg_for, b_xg_against,
            b_injuries, b_motivation, b_rest, b_fatigue
        )

        a_ml_score, a_model_prob, a_market_prob, a_edge = moneyline_score(a_score, b_score, team_a_ml_odds)
        b_ml_score, b_model_prob, b_market_prob, b_edge = moneyline_score(b_score, a_score, team_b_ml_odds)
        ah_score, ah_model_prob, ah_market_prob, ah_edge = handicap_score(a_score, b_score, handicap_line, handicap_odds)
        over_score, under_score, projected_total = total_score(
            total_line, a_xg_for, b_xg_for, a_xg_against, b_xg_against,
            pace, bad_weather, referee_cards, knockout_pressure, must_win, market_move_total
        )

        picks = [
            {
                "Pick": f"{team_a} ML",
                "Score": round(a_ml_score, 1),
                "Stars": star_rating(a_ml_score),
                "Confidence": confidence_label(a_ml_score),
                "Risk": risk_label(a_ml_score),
                "Stake": recommend_stake(a_ml_score),
                "Model Prob %": round(a_model_prob, 1),
                "Market Prob %": round(a_market_prob, 1),
                "Edge %": round(a_edge, 1)
            },
            {
                "Pick": f"{team_b} ML",
                "Score": round(b_ml_score, 1),
                "Stars": star_rating(b_ml_score),
                "Confidence": confidence_label(b_ml_score),
                "Risk": risk_label(b_ml_score),
                "Stake": recommend_stake(b_ml_score),
                "Model Prob %": round(b_model_prob, 1),
                "Market Prob %": round(b_market_prob, 1),
                "Edge %": round(b_edge, 1)
            },
            {
                "Pick": f"{team_a} {handicap_line:+}",
                "Score": round(ah_score, 1),
                "Stars": star_rating(ah_score),
                "Confidence": confidence_label(ah_score),
                "Risk": risk_label(ah_score),
                "Stake": recommend_stake(ah_score),
                "Model Prob %": round(ah_model_prob, 1),
                "Market Prob %": round(ah_market_prob, 1),
                "Edge %": round(ah_edge, 1)
            },
            {
                "Pick": f"Over {total_line}",
                "Score": round(over_score, 1),
                "Stars": star_rating(over_score),
                "Confidence": confidence_label(over_score),
                "Risk": risk_label(over_score),
                "Stake": recommend_stake(over_score),
                "Model Prob %": "",
                "Market Prob %": "",
                "Edge %": ""
            },
            {
                "Pick": f"Under {total_line}",
                "Score": round(under_score, 1),
                "Stars": star_rating(under_score),
                "Confidence": confidence_label(under_score),
                "Risk": risk_label(under_score),
                "Stake": recommend_stake(under_score),
                "Model Prob %": "",
                "Market Prob %": "",
                "Edge %": ""
            }
        ]

        st.metric(f"{team_a} Strength", f"{a_score:.1f}/100")
        st.metric(f"{team_b} Strength", f"{b_score:.1f}/100")
        st.metric("Projected Total Goals", f"{projected_total:.2f}")

        df = build_pick_table(picks)
        st.dataframe(df, use_container_width=True)

        best_pick = df.iloc[0]
        st.success(
            f"Best pick: {best_pick['Pick']} — {best_pick['Stars']} "
            f"Score {best_pick['Score']} | Stake: {best_pick['Stake']}"
        )

        if best_pick["Score"] < 65:
            st.warning("Không có kèo thật sự mạnh. Nên bỏ qua hoặc đợi live.")

# -----------------------------
# Tab 2: Live Bet
# -----------------------------

with tab2:
    st.subheader("🔥 Live Under / Live Bet Analyzer")

    l1, l2, l3, l4 = st.columns(4)
    with l1:
        live_minute = st.slider("Minute", 1, 120, 25)
        current_goals = st.slider("Current goals", 0, 8, 0)
    with l2:
        live_total = st.number_input("Live O/U total", 0.5, 8.5, 2.5, step=0.25)
        live_sot = st.slider("Shots on target total", 0, 20, 2)
    with l3:
        big_chances = st.slider("Big chances", 0, 10, 0)
        dangerous_attacks = st.slider("Dangerous attacks total", 0, 150, 18)
    with l4:
        live_cards = st.slider("Cards", 0, 12, 1)
        live_tempo = st.slider("Tempo", 0, 10, 3)

    favorite_pressure = st.slider("Favorite pressure", 0, 10, 4)
    live_weather_bad = st.slider("Live bad weather", 0, 10, 2)

    if st.button("🔥 Analyze Live Under", type="primary"):
        lu_score = live_under_score(
            live_minute, current_goals, live_total, live_sot,
            big_chances, dangerous_attacks, live_cards,
            live_tempo, favorite_pressure, live_weather_bad
        )

        st.metric("Live Under Score", f"{lu_score:.1f}/100", star_rating(lu_score))
        st.write(f"Confidence: **{confidence_label(lu_score)}**")
        st.write(f"Suggested stake: **{recommend_stake(lu_score)}**")

        if lu_score >= 80:
            st.success("Live Under rất đẹp nếu odds không bị ép quá thấp.")
        elif lu_score >= 68:
            st.info("Có thể vào nhẹ hoặc chờ thêm 5-10 phút.")
        else:
            st.warning("Chưa đủ đẹp. Không nên vào Under lúc này.")

        rules = []
        if live_minute >= 20 and current_goals == 0:
            rules.append("0-0 sau 20 phút: tốt cho Under.")
        if live_sot <= 2:
            rules.append("Shots on target thấp.")
        if big_chances == 0:
            rules.append("Chưa có big chance rõ.")
        if live_tempo <= 4:
            rules.append("Tempo chậm.")
        if favorite_pressure >= 7:
            rules.append("Cửa trên ép mạnh: coi chừng bàn đến.")
        if current_goals >= 2 and live_minute < 35:
            rules.append("Có bàn sớm nhiều: tránh Under.")

        st.write("### Notes")
        for r in rules:
            st.write(f"- {r}")

# -----------------------------
# Tab 3: Sharp Money
# -----------------------------

with tab3:
    st.subheader("📈 Sharp Money / Line Movement")

    s1, s2, s3 = st.columns(3)
    with s1:
        open_line = st.number_input("Opening line", -5.0, 8.5, 2.5, step=0.25)
    with s2:
        current_line = st.number_input("Current line", -5.0, 8.5, 2.25, step=0.25)
    with s3:
        market_type = st.selectbox("Market type", ["Total O/U", "Handicap", "Moneyline"])

    p1, p2, p3 = st.columns(3)
    with p1:
        public_percent = st.slider("Public %", 0, 100, 65)
    with p2:
        bet_percent = st.slider("Bet ticket %", 0, 100, 62)
    with p3:
        handle_percent = st.slider("Money handle %", 0, 100, 78)

    if st.button("📈 Analyze Sharp Signal", type="primary"):
        sm_score, sm_notes = sharp_money_score(
            open_line, current_line, public_percent, bet_percent, handle_percent
        )
        st.metric("Sharp Money Score", f"{sm_score:.1f}/100", star_rating(sm_score))

        for note in sm_notes:
            st.write(f"- {note}")

        if sm_score >= 80:
            st.success("Sharp signal mạnh. Có thể theo nếu trùng với model.")
        elif sm_score >= 65:
            st.info("Có tín hiệu, nhưng cần xác nhận với phong độ / đội hình.")
        else:
            st.warning("Chưa đủ sharp. Không nên chỉ dựa vào line movement.")

# -----------------------------
# Tab 4: Bet Slip Builder
# -----------------------------

with tab4:
    st.subheader("🧾 Bet Slip Builder")

    st.write("Dùng phần này để quản lý vốn trước khi vào kèo.")

    bankroll = st.number_input("Bankroll ($)", 10.0, 100000.0, 1000.0, step=10.0)
    risk_per_bet = st.slider("Risk per bet %", 0.1, 5.0, 1.0, step=0.1)
    pick_name = st.text_input("Pick name", "France ML")
    pick_score = st.slider("Bot score", 0, 100, 78)
    decimal_odds = st.number_input("Decimal odds", 1.01, 20.0, 1.85, step=0.01)

    base_stake = bankroll * risk_per_bet / 100

    if pick_score >= 85:
        stake_multiplier = 1.25
    elif pick_score >= 75:
        stake_multiplier = 1.0
    elif pick_score >= 65:
        stake_multiplier = 0.5
    else:
        stake_multiplier = 0

    suggested_amount = base_stake * stake_multiplier
    potential_profit = suggested_amount * (decimal_odds - 1)

    st.metric("Suggested stake", f"${suggested_amount:.2f}")
    st.metric("Potential profit", f"${potential_profit:.2f}")
    st.metric("Risk label", risk_label(pick_score))

    if pick_score < 65:
        st.warning("Bot score thấp hơn 65: nên bỏ qua.")
    elif suggested_amount > bankroll * 0.03:
        st.warning("Stake hơi cao. Không nên vượt quá 3% bankroll cho 1 kèo.")
    else:
        st.success("Stake hợp lý theo bankroll.")

    st.write("### Simple rules")
    st.write("- Không all-in.")
    st.write("- Không gỡ thua bằng cách tăng tiền gấp đôi.")
    st.write("- Kèo dưới 65 điểm: bỏ qua.")
    st.write("- Kèo live chỉ vào khi có đủ dữ liệu: phút, shots, big chances, tempo.")
