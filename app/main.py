import streamlit as st
import requests

# API Configuration
API_URL = "http://localhost:8000"

# Page configuration
st.set_page_config(
    page_title="NEPSE Trading Bot",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Helper functions
def check_api_health():
    """Check if API is running"""
    try:
        response = requests.get(f"{API_URL}/", timeout=5)
        return response.json()
    except:
        return None

def get_stock_list():
    """Get list of all stocks"""
    try:
        response = requests.get(f"{API_URL}/stocks")
        if response.status_code == 200:
            return response.json()['symbols']
        return []
    except:
        return []

def get_stock_info(symbol):
    """Get stock information"""
    try:
        response = requests.get(f"{API_URL}/stocks/{symbol}")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def get_indicators(symbol):
    """Get technical indicators"""
    try:
        response = requests.get(f"{API_URL}/stocks/{symbol}/indicators")
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

def analyze_stock_api(symbol, strategy):
    """Call API to analyze stock"""
    try:
        response = requests.post(
            f"{API_URL}/analyze",
            json={"symbol": symbol, "strategy": strategy}
        )
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None

# Main App
def main():
    st.markdown('<div class="main-header">📈 NEPSE Multi-Strategy RAG Trading Bot</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">AI-Powered Stock Analysis for Nepal Stock Exchange</div>', unsafe_allow_html=True)

    # Check API health
    api_status = check_api_health()

    if not api_status:
        st.error("❌ Cannot connect to API. Please make sure the FastAPI server is running on http://localhost:8000")
        st.info("Run: `uvicorn app.api:app --reload` in your terminal")
        st.stop()

    # Sidebar
    with st.sidebar:
        # Stock selection
        stocks = get_stock_list()
        if not stocks:
            st.error("No stocks available")
            st.stop()

        selected_stock = st.selectbox("📊 Select Stock Symbol", stocks)

        # Strategy selection
        strategy = st.selectbox(
            "🎯 Trading Strategy",
            ["multi-strategy", "trend-following", "mean reversion", "swing trading", "breakout/pullback"]
        )

    # Main content
    if selected_stock:
        # Get stock info
        stock_info = get_stock_info(selected_stock)

        if stock_info:
            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Close Price", f"Rs. {stock_info['close']:.2f}",
                         f"{stock_info['diff_percent']:.2f}%")

            with col2:
                st.metric("Volume", f"{stock_info['volume']:,}")

            with col3:
                rsi_value = stock_info['rsi']
                rsi_status = "Overbought" if rsi_value > 70 else "Oversold" if rsi_value < 30 else "Neutral"
                st.metric("RSI", f"{rsi_value:.2f}", rsi_status)

            with col4:
                st.metric("52W High", f"Rs. {stock_info['week_52_high']:.2f}")

            st.markdown("---")

            # AI Analysis Section
            st.markdown("### 🤖 AI-Powered Trading Recommendation")
            st.info("⏱️ **Note:** Analysis may take 10-30 seconds due to Google API rate limits. Please be patient.")

            if not api_status.get('bot_initialized'):
                st.error("❌ RAG Bot not initialized. Please set GOOGLE_API_KEY environment variable and restart the API.")
            else:
                if st.button("🔍 Get AI Analysis", type="primary", use_container_width=True):
                    with st.spinner(f"Analyzing {selected_stock} using {strategy} strategy..."):
                        # Get indicators for display
                        indicators = get_indicators(selected_stock)
                        result = analyze_stock_api(selected_stock, strategy)

                        if result and result['success']:
                            st.markdown("---")

                            # Show technical indicators first
                            if indicators:
                                st.markdown("### 📊 Current Technical Indicators")

                                col1, col2, col3 = st.columns(3)

                                with col1:
                                    st.markdown("**📈 Moving Averages**")
                                    st.write(f"MA20: Rs. {indicators['moving_averages']['ma20']:.2f}")
                                    st.write(f"MA50: Rs. {indicators['moving_averages']['ma50']:.2f}")

                                    st.markdown("**💰 Price**")
                                    st.write(f"Close: Rs. {indicators['price']['close']:.2f}")
                                    st.write(f"VWAP: Rs. {indicators['price']['vwap']:.2f}")
                                    st.write(f"Change: {indicators['change_percent']:.2f}%")

                                with col2:
                                    st.markdown("**📊 Momentum**")
                                    rsi = indicators['momentum']['rsi']
                                    rsi_signal = "🔴 Overbought" if rsi > 70 else "🟢 Oversold" if rsi < 30 else "🟡 Neutral"
                                    st.write(f"RSI: {rsi:.2f} ({rsi_signal})")
                                    st.write(f"MACD: {indicators['momentum']['macd']:.2f}")
                                    st.write(f"Signal: {indicators['momentum']['macd_signal']:.2f}")

                                    macd_hist = indicators['momentum']['macd'] - indicators['momentum']['macd_signal']
                                    macd_trend = "🟢 Bullish" if macd_hist > 0 else "🔴 Bearish"
                                    st.write(f"Trend: {macd_trend}")

                                with col3:
                                    st.markdown("**📉 Bollinger Bands**")
                                    st.write(f"Upper: Rs. {indicators['bollinger_bands']['upper']:.2f}")
                                    st.write(f"Middle: Rs. {indicators['bollinger_bands']['middle']:.2f}")
                                    st.write(f"Lower: Rs. {indicators['bollinger_bands']['lower']:.2f}")

                                    # BB position
                                    close = indicators['price']['close']
                                    bb_upper = indicators['bollinger_bands']['upper']
                                    bb_lower = indicators['bollinger_bands']['lower']

                                    if close > bb_upper:
                                        bb_pos = "🔴 Above Upper (Overbought)"
                                    elif close < bb_lower:
                                        bb_pos = "🟢 Below Lower (Oversold)"
                                    else:
                                        bb_pos = "🟡 Within Bands (Normal)"
                                    st.write(f"Position: {bb_pos}")

                                st.markdown("---")

                            # Show AI analysis
                            st.markdown("### 💡 AI Analysis & Recommendation")
                            st.markdown(result['analysis'])
                            st.markdown("---")
                            st.warning("⚠️ **Disclaimer**: This is an AI-generated analysis for educational purposes only.")
                        elif result:
                            st.error(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                        else:
                            st.error("❌ Failed to get analysis from API")

if __name__ == "__main__":
    main()
