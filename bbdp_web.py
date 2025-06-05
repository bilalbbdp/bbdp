
import streamlit as st
from collections import Counter
import datetime
from deriv_api import DerivAPI  # Replace with your actual Deriv API handler

# --- Initialize Deriv API ---
deriv_api = DerivAPI(api_token="your_api_token_here")  # Replace with your token

# --- Fetch Ticks ---
def fetch_ticks(api, symbol="R_10", count=120):
    response = api.ticks_history(
        symbol=symbol,
        count=count,
        end='latest',
        style='ticks'
    )
    return response.get("history", {}).get("prices", [])

# --- Analyze Even/Odd Pattern ---
def analyze_even_odd(ticks):
    pattern = []
    for tick in ticks:
        digit = int(str(tick)[-1])
        pattern.append("E" if digit % 2 == 0 else "O")
    return pattern

# --- Streamlit UI ---
st.title("📊 BBDP - Bilal's Deriv Profiteer")
st.caption("Smart Trading with Even/Odd Pattern Analysis")

# Market Selection
market = st.selectbox("Choose Market", ["R_10", "R_25", "R_50", "R_75", "R_100"])

# Fetch and analyze ticks
ticks = fetch_ticks(deriv_api, symbol=market, count=120)

if ticks:
    pattern = analyze_even_odd(ticks)
    colored = [f":green[{x}]" if x == "E" else f":red[{x}]" for x in pattern]

    st.markdown("#### Pattern (Even = Green, Odd = Red)")
    st.write(" ".join(colored))

    counts = Counter(pattern)
    st.metric("✅ Even Count", counts["E"])
    st.metric("❌ Odd Count", counts["O"])

    even_ratio = counts["E"] / len(pattern)
    suggested_trade = None
    if even_ratio > 0.6:
        suggested_trade = "Even"
    elif even_ratio < 0.4:
        suggested_trade = "Odd"

    # Auto Trade Toggle
    st.subheader("📌 Suggested Trade Based on Pattern")
    auto_trade = st.checkbox("🤖 Enable Auto-Trade")

    if suggested_trade:
        st.success(f"Suggested Trade ➤ **{suggested_trade}**")

        contract_type = "DIGITEVEN" if suggested_trade == "Even" else "DIGITODD"

        if auto_trade:
            st.warning("Auto-trading is enabled. Submitting trade...")
            try:
                response = deriv_api.buy(contract_type=contract_type, amount=1, duration=1, basis="stake", symbol=market)
                st.info(f"✅ Auto Trade Executed: {suggested_trade}")
                st.json(response)

                # Log Trade
                with open("trade_log.txt", "a") as f:
                    f.write(f"{datetime.datetime.now()} | AUTO | {suggested_trade} | {market}\n")

            except Exception as e:
                st.error(f"Auto Trade Failed: {str(e)}")
        else:
            if st.button(f"🚀 Execute Trade Manually: {suggested_trade}"):
                try:
                    response = deriv_api.buy(contract_type=contract_type, amount=1, duration=1, basis="stake", symbol=market)
                    st.info(f"✅ Manual Trade Executed: {suggested_trade}")
                    st.json(response)
                    with open("trade_log.txt", "a") as f:
                        f.write(f"{datetime.datetime.now()} | MANUAL | {suggested_trade} | {market}\n")
                except Exception as e:
                    st.error(f"Manual Trade Failed: {str(e)}")
    else:
        st.warning("⚠️ No clear trade signal right now.")

    st.caption(f"Updated at {datetime.datetime.now().strftime('%H:%M:%S')}")
else:
    st.error("❌ Could not fetch ticks. Check API token or network.")
