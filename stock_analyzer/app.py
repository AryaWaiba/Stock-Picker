import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os

# Import modules
import data_fetcher
import fundamentals
import valuation
import technicals
import risk
import scoring
import utils

# Set page config
st.set_page_config(page_title="Stock Analyzer | Pro", layout="wide", initial_sidebar_state="collapsed")

# --- FIDELITY-STYLE CSS ---
# Colors: Fidelity Green (#128848), Fidelity Blue (#174291), Text (#111111), Light Bg (#F7F9FA)
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #ffffff;
        color: #111111;
        font-family: 'Arial', sans-serif;
    }
    
    /* Headings - Corporate & Crisp */
    h1, h2, h3 {
        font-family: 'Arial', sans-serif;
        color: #111111;
        font-weight: 700;
        letter-spacing: -0.2px;
    }
    
    h1 {
        font-size: 24px;
        color: #174291; /* Fidelity Blue Header */
        border-bottom: 2px solid #128848; /* Green Underline */
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #F7F9FA;
        border-right: 1px solid #dcdcdc;
    }
    
    /* Research Cards (Boxy, bordered) */
    .rh-card {
        background-color: #ffffff;
        border: 1px solid #cccccc; /* Harder border */
        padding: 20px;
        border-radius: 2px; /* Square corners */
        box-shadow: none; /* Flat design */
        margin-bottom: 15px;
    }
    
    /* Metrics - Data Dense */
    .metric-label {
        font-size: 12px;
        font-weight: 600;
        color: #555555;
        text-transform: uppercase;
    }
    
    .metric-value {
        font-size: 20px;
        font-weight: 700;
        color: #111111;
        font-family: 'Consolas', 'Courier New', monospace; /* Number font */
    }
    
    /* Badges / Chips */
    .badge {
        padding: 2px 8px;
        border-radius: 2px;
        font-size: 11px;
        font-weight: 700;
        border: 1px solid #ddd;
    }
    
    .badge-green { background-color: #e8f5e9; color: #1b5e20; border-color: #c8e6c9; }
    .badge-yellow { background-color: #fffde7; color: #f57f17; border-color: #fff9c4; }
    .badge-red { background-color: #ffebee; color: #c62828; border-color: #ffcdd2; }
    
    /* Tabs - Professional Line */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0px;
        border-bottom: 2px solid #128848;
    }

    .stTabs [data-baseweb="tab"] {
        height: 40px;
        background-color: #f0f0f0;
        border: 1px solid #ddd;
        border-bottom: none;
        color: #555;
        font-weight: 600;
        font-size: 13px;
        margin-right: 4px;
        border-radius: 4px 4px 0 0;
    }

    .stTabs [aria-selected="true"] {
        background-color: #128848; /* Active Green */
        color: white;
        border: 1px solid #128848;
    }
    
    /* Buttons */
    div.stButton > button {
        background-color: #128848; /* Fidelity Green */
        color: white;
        border-radius: 2px;
        border: none;
        padding: 6px 20px;
        text-transform: uppercase;
        font-size: 12px;
        letter-spacing: 0.5px;
    }
    div.stButton > button:hover {
        background-color: #0e6b38;
    }

</style>
""", unsafe_allow_html=True)

# sidebar
with st.sidebar:
    st.markdown("## ⚡ FinSightX")
    
    # Navigation
    page = st.radio("VIEW", ["Dashboard", "Stock Analysis", "Watchlist"], label_visibility="collapsed")
    
    st.markdown("---")
    
    if page == "Stock Analysis":
        ticker_input = st.text_input("ENTER TICKER", value="AAPL").upper().strip()
        run_btn = st.button("GET QUOTE", type="primary")
    else:
        st.markdown("### Daily Leaders")
        st.caption("Institutional Grade Analysis")
        
    st.markdown("---")
    
    # --- MARKET MINI-BOARD ---
    st.markdown("### Market Pulse")
    try:
        import yfinance as yf
        indices = {"SPY": "S&P 500", "QQQ": "Nasdaq", "DIA": "Dow 30"}
        for sym, name in indices.items():
            idx_data = yf.Ticker(sym).history(period="2d")
            if not idx_data.empty:
                last_price = idx_data['Close'].iloc[-1]
                prev_price = idx_data['Close'].iloc[-2]
                chg = last_price - prev_price
                pct = (chg / prev_price) * 100
                color = "#128848" if chg >= 0 else "#D32F2F"
                sign = "+" if chg >= 0 else ""
                st.markdown(f"""
                <div style='margin-bottom: 8px;'>
                    <div style='font-size: 11px; color: #666; font-weight: 700;'>{name} ({sym})</div>
                    <div style='font-size: 14px; font-weight: 700;'>
                        ${last_price:,.2f} 
                        <span style='color: {color}; font-size: 11px;'>{sign}{pct:.2f}%</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
    except:
        st.caption("Market data unavailable")

    st.markdown("---")
    
    # --- SCANNER & WATCHLIST STATS ---
    if os.path.exists("scan_history.csv"):
        hist_df = pd.read_csv("scan_history.csv")
        ticker_count = hist_df['Ticker'].nunique()
        last_update = hist_df['Date'].max()
        st.markdown(f"""
        <div style='background: #f8f9fa; padding: 10px; border-radius: 4px; border: 1px solid #eee;'>
            <div style='font-size: 10px; color: #888; text-transform: uppercase; font-weight: 800;'>Analysis Universe</div>
            <div style='font-size: 18px; font-weight: 800; color: #174291;'>{ticker_count} <span style='font-size: 10px; color: #666;'>TICKERS</span></div>
            <div style='font-size: 10px; color: #888; margin-top: 5px;'>Last Refresh: {last_update}</div>
        </div>
        """, unsafe_allow_html=True)
        
    wl = utils.load_watchlist()
    if wl:
        st.markdown(f"⭐ **{len(wl)}** Saved Stocks")

    st.markdown("---")
    st.markdown("v3.0.0 | Connected")

# --- PAGE: DASHBOARD (Top 10) ---
if page == "Dashboard":
    # Main Dashboard UI
    st.markdown("## Top Opportunities 🚀")
    
    # --- MARKET CONTEXT PANEL ("WHAT CHANGED") ---
    if os.path.exists("scan_history.csv"):
        try:
            hist_df = pd.read_csv("scan_history.csv")
            dates = sorted(hist_df['Date'].unique(), reverse=True)
            
            if len(dates) >= 2:
                latest = dates[0]
                prev = dates[1]
                
                # Get Top 10 for both days
                df_lat = hist_df[hist_df['Date'] == latest].sort_values("Rank").head(10)
                df_prev = hist_df[hist_df['Date'] == prev].sort_values("Rank").head(10)
                
                lat_tickers = set(df_lat['Ticker'])
                prev_tickers = set(df_prev['Ticker'])
                
                # 1. New Entrants
                new_entrants = list(lat_tickers - prev_tickers)
                
                # 2. Dropped Out
                dropped_out = list(prev_tickers - lat_tickers)
                
                # 3. Big Movers (Rank Gain >= 3)
                movers = []
                common = lat_tickers.intersection(prev_tickers)
                for t in common:
                    r_new = df_lat[df_lat['Ticker']==t]['Rank'].iloc[0]
                    r_old = df_prev[df_prev['Ticker']==t]['Rank'].iloc[0]
                    if (r_old - r_new) >= 2:
                        movers.append(f"{t} (+{int(r_old - r_new)})")
                        
                with st.expander("📊 Market Context: What Changed Today?", expanded=False):
                    ctx1, ctx2, ctx3 = st.columns(3)
                    with ctx1:
                        st.markdown("**✨ New Entrants**")
                        if new_entrants:
                            for t in new_entrants: st.markdown(f"- **{t}**")
                        else:
                            st.caption("No new top 10 entrants.")
                            
                    with ctx2:
                        st.markdown("**🚀 Big Movers**")
                        if movers:
                            for m in movers: st.markdown(f"- **{m}**")
                        else:
                            st.caption("Stable rankings today.")
                            
                    with ctx3:
                        st.markdown("**📉 Dropped Out**")
                        if dropped_out:
                            for t in dropped_out: st.markdown(f"- {t}")
                        else:
                            st.caption("No dropouts.")
        except Exception as e:
            st.error(f"Error loading context: {e}")
            
    # Load Data
    try:
        df_top = pd.read_excel("top10_pro.xlsx")
        
        # --- MARKET PULSE AI SUMMARY ---
        if not df_top.empty:
            top_sectors = df_top['Sector'].value_counts().head(3)
            top_stock = df_top.iloc[0]
            avg_score = df_top['TotalScore'].mean()
            
            pulse_text = f"**📈 Market Pulse:** Today's leaders span **{', '.join(top_sectors.index[:2])}**. "
            pulse_text += f"Top pick **{top_stock['Ticker']}** scores **{top_stock['TotalScore']:.0f}** "
            pulse_text += f"with {top_stock.get('AI_Insight', 'strong fundamentals')[:50]}... "
            pulse_text += f"Average Top 10 score: **{avg_score:.1f}**."
            
            st.info(pulse_text)
        
        # --- FILTERING & SORTING CONTROLS ---
        with st.expander("🔧 Filter & Sort Options", expanded=False):
            ctrl1, ctrl2, ctrl3 = st.columns(3)
            
            with ctrl1:
                sort_by = st.selectbox("Sort By", ["Score (High to Low)", "Score (Low to High)", "Ticker (A-Z)"], index=0)
            
            with ctrl2:
                all_sectors = ["All Sectors"] + sorted(df_top['Sector'].unique().tolist())
                filter_sector = st.multiselect("Filter by Sector", all_sectors, default=["All Sectors"])
            
            with ctrl3:
                # Removed redundant multiselect to keep UI clean as requested ("short filter")
                st.caption("Ratings: 💡 AI-Driven")
        
        # Apply filters
        df_filtered = df_top.copy()
        
        # 0. Pre-calculate Rating for Filtering (Nomenclature: BUY/HOLD/SELL)
        def get_rating(s):
            if s > 80: return "BUY"
            if s > 60: return "HOLD"
            return "SELL"
        df_filtered['Rating'] = df_filtered['TotalScore'].apply(get_rating)
        
        # 1. Sector Filter
        if "All Sectors" not in filter_sector and filter_sector:
            df_filtered = df_filtered[df_filtered['Sector'].isin(filter_sector)]
            
        # 2. Quick Rating Filter (Pills) - Compact & Fast
        st.write("") # Spacer
        quick_rating = st.pills(
            "Quick Rating Filter", 
            ["All", "BUY", "HOLD", "SELL"], 
            selection_mode="single", 
            default="All", 
            label_visibility="visible"
        )
        
        if quick_rating != "All":
            df_filtered = df_filtered[df_filtered['Rating'] == quick_rating]
        
        # Apply sorting
        if sort_by == "Score (High to Low)":
            df_filtered = df_filtered.sort_values("TotalScore", ascending=False)
        elif sort_by == "Score (Low to High)":
            df_filtered = df_filtered.sort_values("TotalScore", ascending=True)
        elif sort_by == "Ticker (A-Z)":
            df_filtered = df_filtered.sort_values("Ticker")
        
        df_top = df_filtered.reset_index(drop=True)
        
        # 1. KPI Cards
        c1, c2, c3 = st.columns(3)
        if not df_top.empty:
            top_pick = df_top.iloc[0]
            avg_score = df_top['TotalScore'].mean()
            sectors = df_top['Sector'].nunique()
            
            c1.markdown(f"""
            <div class='rh-card' style='padding:15px; text-align:center;'>
                <div style='color:#666; font-size:11px; font-weight:bold;'>TOP RANKED</div>
                <div style='font-size:20px; font-weight:bold; color:#174291;'>{top_pick['Ticker']}</div>
                <div style='color:#128848; font-weight:bold; font-size:14px;'>{top_pick['TotalScore']:.1f} Score</div>
            </div>""", unsafe_allow_html=True)
            
            c2.markdown(f"""
            <div class='rh-card' style='padding:15px; text-align:center;'>
                <div style='color:#666; font-size:11px; font-weight:bold;'>AVG SCORE</div>
                <div style='font-size:20px; font-weight:bold; color:#111;'>{avg_score:.1f}</div>
                <div style='color:#888; font-size:12px;'>Top 10 Average</div>
            </div>""", unsafe_allow_html=True)
            
            c3.markdown(f"""
            <div class='rh-card' style='padding:15px; text-align:center;'>
                <div style='color:#666; font-size:11px; font-weight:bold;'>DIVERSITY</div>
                <div style='font-size:20px; font-weight:bold; color:#111;'>{sectors}</div>
                <div style='color:#888; font-size:12px;'>Sectors</div>
            </div>""", unsafe_allow_html=True)

        # 2. Main Layout
        col_list, col_charts = st.columns([2, 1])
        
        with col_list:
            st.markdown("#### 🏆 Top Opportunities")
            
            # --- RENDER CARDS ---
            from ai_insights import generate_fidelity_card
            
            # Show all available top picks (up to 10)
            for i, row in df_top.iterrows():
                # Map DF row to metrics expected by card
                metrics_scan = {
                    "ROE": (row.get('ROIC', 0) or 0) * 100, 
                    "RevenueGrowth": row.get('Rev_CAGR_3Y', 0),
                    "EPSGrowth": row.get('EPS_Growth_3Y', 0) or row.get('Rev_CAGR_3Y', 0) * 0.8, # Fallback if EPS growth not in DF
                    "PE": row.get('ForwardPE', 0),
                    "ForwardPE": row.get('ForwardPE', 0),
                    "Price": row.get('Price', 0),
                    "DebtToEquity": row.get('Debt_EBITDA', 0) * 20, # Heuristic mapping for display
                    "Beta": row.get('Beta', 1.0),
                    "CompanyName": row.get('Name', row.get('Ticker', 'Unknown')),
                    "Rank": i + 1,
                    "TotalScore": row['TotalScore'] * 0.6, # Scaling to 60 as per new UI
                    "Score_Fundamentals": row.get('Score_Quality', 50),
                    "Score_Technicals": row.get('Score_Technicals', 50),
                    "Score_Risk": row.get('Score_Risk', 50)
                }
                
                # Determine Rating color
                score = row['TotalScore']
                rating_label = "BUY" if score > 80 else "HOLD" if score > 60 else "SELL"
                
                # Render Card
                st.markdown(f"**#{i+1}**")
                card_html = generate_fidelity_card(row['Ticker'], rating_label, metrics_scan)
                st.markdown(card_html, unsafe_allow_html=True)
                
            # Fallback Table in Expander
            with st.expander("View Full Data Table"):
                 st.dataframe(df_top)

        with col_charts:
            # --- ENHANCED SECTOR PIE CHART ---
            st.markdown("#### Sector Allocation")
            sector_counts = df_top['Sector'].value_counts()
            
            # Calculate percentages
            total = sector_counts.sum()
            percentages = (sector_counts / total * 100).round(1)
            
            # Create labels with percentages
            labels_with_pct = [f"{sector}<br>{pct}%" for sector, pct in zip(sector_counts.index, percentages)]
            
            fig_pie = go.Figure(data=[go.Pie(
                labels=labels_with_pct,
                values=sector_counts.values,
                hole=.5,
                textinfo='label',
                textposition='outside',
                marker=dict(
                    colors=['#00C805', '#174291', '#FFC107', '#E63946', '#6366f1', '#8b5cf6', '#ec4899'],
                    line=dict(color='white', width=2)
                ),
                hovertemplate='<b>%{label}</b><br>Count: %{value}<extra></extra>'
            )])
            
            fig_pie.update_layout(
                margin=dict(l=0, r=0, t=0, b=0),
                height=280,
                showlegend=False,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # Show top 3 sectors with stock names
            st.caption("**Top Sectors:**")
            for i, (sector, count) in enumerate(sector_counts.head(3).items(), 1):
                stocks_in_sector = df_top[df_top['Sector'] == sector]['Ticker'].tolist()
                st.caption(f"{i}. **{sector}** ({count}) - {', '.join(stocks_in_sector[:3])}")
            
            # --- ENHANCED RANK HISTORY CHART ---
            st.markdown("#### Rank History")
            if os.path.exists("scan_history.csv"):
                hist_df = pd.read_csv("scan_history.csv")
                # Filter for top 5 current
                top_5_tickers = df_top.head(5)['Ticker'].tolist()
                hist_filtered = hist_df[hist_df['Ticker'].isin(top_5_tickers)]
                
                fig_trend = go.Figure()
                
                colors = ['#00C805', '#174291', '#FFC107', '#E63946', '#6366f1']
                
                for idx, t in enumerate(top_5_tickers):
                    t_data = hist_filtered[hist_filtered['Ticker'] == t].sort_values("Date")
                    if not t_data.empty:
                        # Calculate rank change
                        if len(t_data) >= 2:
                            rank_change = t_data.iloc[-2]['Rank'] - t_data.iloc[-1]['Rank']
                            change_symbol = "↑" if rank_change > 0 else "↓" if rank_change < 0 else "→"
                            change_text = f" ({change_symbol}{abs(rank_change):.0f})" if rank_change != 0 else ""
                        else:
                            change_text = ""
                        
                        # Add line with markers
                        fig_trend.add_trace(go.Scatter(
                            x=t_data['Date'],
                            y=t_data['Rank'],
                            mode='lines+markers',
                            name=f"{t}{change_text}",
                            line=dict(color=colors[idx % len(colors)], width=2),
                            marker=dict(size=8, symbol='circle', line=dict(width=2, color='white')),
                            hovertemplate='<b>%{fullData.name}</b><br>Date: %{x}<br>Rank: %{y}<br><extra></extra>'
                        ))
                
                fig_trend.update_layout(
                    height=280,
                    margin=dict(l=0, r=0, t=10, b=0),
                    yaxis=dict(
                        autorange="reversed",
                        title="Rank",
                        gridcolor='#f0f0f0',
                        showgrid=True
                    ),
                    xaxis=dict(
                        showgrid=False,
                        title=""
                    ),
                    template="plotly_white",
                    showlegend=True,
                    legend=dict(
                        orientation="v",
                        yanchor="top",
                        y=1,
                        xanchor="left",
                        x=1.02,
                        font=dict(size=10)
                    ),
                    hovermode='x unified',
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='white'
                )
                st.plotly_chart(fig_trend, use_container_width=True)

    except Exception as e:
        st.error(f"Please run 'scanner_pro.py' to generate data. Error: {e}")

# --- PAGE: INDIVIDUAL STOCK ---
elif page == "Stock Analysis":
    if run_btn or ticker_input:
        with st.spinner("Fetching data..."):
            data = data_fetcher.get_stock_data(ticker_input)

        if not data:
            st.error(f"Ticker '{ticker_input}' not found.")
        else:
            # Run Analysis
            fund_res = fundamentals.analyze_fundamentals(data)
            val_res = valuation.analyze_valuation(data)
            tech_res = technicals.analyze_technicals(data)
            risk_res = risk.analyze_risk(data)
            score_res = scoring.factor_scores(fund_res, val_res, tech_res, risk_res)
            
            # --- HEADER SECTION ---
            curr_price = data_fetcher.get_market_price(data)
            hist = data['history']
            
            # Fallback if curr_price is None
            if curr_price is None and not hist.empty:
               curr_price = hist['Close'].iloc[-1]
            elif curr_price is None:
               curr_price = 0.0

            # Calculate daily change
            if len(hist) >= 2:
                prev_close = hist['Close'].iloc[-2]
                effective_price = curr_price if curr_price > 0 else hist['Close'].iloc[-1]
                change = effective_price - prev_close
                pct_change = (change / prev_close) * 100
                color_hex = "#00C805" if change >= 0 else "#FF5000"
                sign = "+" if change >= 0 else ""
                delta_str = f"{sign}{change:.2f} ({sign}{pct_change:.2f}%)"
            else:
                color_hex = "#000000"
                delta_str = "0.00 (0.00%)"
            
            info = data['info']
            name = info.get('longName', ticker_input)
            header_placeholder = st.empty()
            
            # --- WATCHLIST BUTTON ---
            wl_col1, wl_col2 = st.columns([4, 1])
            with wl_col1:
                st.markdown(f"**{info.get('sector', 'Unknown Sector')}** • {info.get('industry', 'Unknown Industry')}")
            with wl_col2:
                watchlist = utils.load_watchlist()
                is_in_wl = ticker_input in watchlist
                btn_label = "⭐ Saved" if is_in_wl else "☆ Save"
                if st.button(btn_label, key=f"wl_{ticker_input}"):
                    msg = utils.toggle_watchlist(ticker_input)
                    st.success(f"{msg} Watchlist: {ticker_input}")
                    st.rerun()
            
            st.markdown("")

            # --- AI ANALYST INSIGHT ---
            from ai_insights import generate_fidelity_card
            metrics_card = {
                "ROE": (fund_res['metrics'].get('ROE') or 0) * 100,
                "RevenueGrowth": fund_res['metrics'].get('Revenue Growth (3Y)') or fund_res['metrics'].get('Revenue Growth (1Y)') or 0,
                "EPSGrowth": info.get('earningsGrowth', 0),
                "PE": val_res['metrics'].get('Trailing P/E') or 0,
                "ForwardPE": val_res['metrics'].get('Forward P/E') or 0,
                "DebtToEquity": (info.get('debtToEquity') or 0),
                "Price": tech_res['metrics'].get('Price') or 0,
                "Beta": risk_res['metrics'].get('Beta') or 1.0,
                "CompanyName": info.get('longName', ticker_input),
                "Rank": "N/A",
                "TotalScore": score_res['total_score'] * 0.6,
                "Score_Fundamentals": fund_res.get('score', 0) * 10,
                "Score_Technicals": tech_res.get('score', 0) * 10,
                "Score_Risk": risk_res.get('score', 0) * 10
            }
            insight_html = generate_fidelity_card(ticker_input, score_res['recommendation'].split(" ")[0].upper(), metrics_card)
    
            # --- MAIN GRID ---
            c_left, c_right = st.columns([2, 1])
            
            with c_left:
                c_time, c_spacer, c_style = st.columns([0.7, 0.1, 0.2])
                with c_time:
                    time_periods = ["1D", "5D", "1M", "6M", "YTD", "1Y", "5Y", "MAX"]
                    selected_period = st.radio("Range", time_periods, index=0, horizontal=True, label_visibility="collapsed")
                with c_style:
                    style_map = {"📈 Line": "Line", "🕯️ Candle": "Candle"}
                    chart_style_label = st.radio("Style", list(style_map.keys()), index=0, horizontal=True, label_visibility="collapsed")
                    chart_style = style_map[chart_style_label]
                
                df_chart = hist.copy()
                if selected_period == "1D": 
                    with st.spinner("Loading intraday data..."):
                        try:
                            intraday = data['ticker'].history(period="1d", interval="5m")
                            if not intraday.empty:
                                df_chart = intraday
                        except:
                            pass 
                elif selected_period == "5D":
                    with st.spinner("Loading intraday data..."):
                        try:
                            intraday = data['ticker'].history(period="5d", interval="15m")
                            if not intraday.empty:
                                df_chart = intraday
                        except:
                            cutoff = pd.Timestamp.now(tz=df_chart.index.tz) - pd.Timedelta(days=5)
                            df_chart = df_chart[df_chart.index >= cutoff]
                else:
                    if selected_period == "1M": delta = pd.Timedelta(days=30)
                    elif selected_period == "6M": delta = pd.Timedelta(days=180)
                    elif selected_period == "YTD": delta = pd.Timestamp.now(tz=df_chart.index.tz) - pd.Timestamp(f"{pd.Timestamp.now().year}-01-01").tz_localize(df_chart.index.tz)
                    elif selected_period == "1Y": delta = pd.Timedelta(days=365)
                    elif selected_period == "5Y": delta = pd.Timedelta(days=365*5)
                    else: delta = None
                    if delta:
                        cutoff = pd.Timestamp.now(tz=df_chart.index.tz) - delta
                        df_chart = df_chart[df_chart.index >= cutoff]

                try:
                    current_price_disp = df_chart['Close'].iloc[-1]
                    start_price_disp = df_chart['Close'].iloc[0]
                    change_disp = current_price_disp - start_price_disp
                    pct_change_disp = (change_disp / start_price_disp) * 100
                    period_map = {"1D": "today", "5D": "past 5 days", "1M": "past month", "6M": "past 6 months", "YTD": "YTD", "1Y": "past year", "5Y": "past 5 years", "MAX": "all time"}
                    period_label = period_map.get(selected_period, "")
                    color_h = "#128848" if change_disp >= 0 else "#D32F2F"
                    sign_h = "+" if change_disp >= 0 else ""
                    delta_html = f"{sign_h}{change_disp:.2f} ({sign_h}{pct_change_disp:.2f}%) <span style='font-size:0.5em; color:#666;'> {period_label}</span>"
                    header_html = f"""
                    <div style='margin-bottom: 20px;'>
                        <h1 style='margin-bottom: 5px;'>{name}</h1>
                        <h2 style='color: {color_h}; margin-top: -10px;'>
                            ${current_price_disp:,.2f} 
                            <span style='font-size: 0.6em; color: {color_h}; font-weight: 500;'>{delta_html}</span>
                        </h2>
                    </div>
                    """
                    header_placeholder.markdown(header_html, unsafe_allow_html=True)
                except Exception as e:
                    header_placeholder.error(f"Error updating header: {e}")

                fig = go.Figure()
                if not df_chart.empty:
                    chart_color = '#128848' if change_disp >= 0 else '#D32F2F'
                    if chart_style == "Candle":
                        fig.add_trace(go.Candlestick(x=df_chart.index, open=df_chart['Open'], high=df_chart['High'], low=df_chart['Low'], close=df_chart['Close'], increasing_line_color='#128848', decreasing_line_color='#D32F2F', name='Price'))
                    else:
                        fig.add_trace(go.Scatter(x=df_chart.index, y=df_chart['Close'], mode='lines', line=dict(color=chart_color, width=2), name='Price'))
                
                fig.update_layout(
                    paper_bgcolor='white', plot_bgcolor='white',
                    xaxis=dict(
                        showgrid=False, zeroline=False, showticklabels=True,
                        tickformat="%I:%M %p" if selected_period == "1D" else "%b %d" if selected_period in ["5D", "1M"] else "%b %Y",
                        rangeslider=dict(visible=True, thickness=0.08),
                        rangeselector=dict(
                            buttons=list([
                                dict(count=1, label="1m", step="month", stepmode="backward"),
                                dict(count=6, label="6m", step="month", stepmode="backward"),
                                dict(count=1, label="YTD", step="year", stepmode="todate"),
                                dict(count=1, label="1y", step="year", stepmode="backward"),
                                dict(step="all")
                            ]),
                            font=dict(size=11), y=1.1
                        )
                    ), 
                    yaxis=dict(showgrid=True, gridcolor='#f0f0f0', zeroline=False, showticklabels=True, side='right'), 
                    margin=dict(l=0, r=40, t=60, b=20), height=420, hovermode="x unified", showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
            with c_right:
                st.markdown("### About")
                st.write(info.get('longBusinessSummary', 'No summary available.')[:800] + "...")
                st.markdown("---")
                s, i = info.get('sector', 'N/A'), info.get('industry', 'N/A')
                st.caption(f"**Sector:** {s}")
                st.caption(f"**Industry:** {i}")

            # --- TABS ---
            tab1, tab2, tab3 = st.tabs(["Overview", "Financials", "Analysis"])
            
            with tab1:
                st.markdown("### AI Analysis")
                st.markdown(insight_html, unsafe_allow_html=True)
                st.markdown("### Company Profile")
                st.write(info.get('longBusinessSummary', 'No summary available.'))
                st.markdown("### Key Statistics")
                k1, k2, k3, k4 = st.columns(4)
                k1.metric("Market Cap", utils.format_large_number(info.get('marketCap')))
                k2.metric("P/E Ratio", f"{info.get('forwardPE', 0):.1f}")
                k3.metric("EPS (TTM)", f"${info.get('trailingEps', 0):.2f}")
                k4.metric("Beta", f"{info.get('beta', 0):.2f}")
                k5, k6, k7, k8 = st.columns(4)
                k5.metric("52W High", f"${info.get('fiftyTwoWeekHigh', 0):.2f}")
                k6.metric("52W Low", f"${info.get('fiftyTwoWeekLow', 0):.2f}")
                k7.metric("Div Yield", f"{info.get('dividendYield', 0)*100:.2f}%" if info.get('dividendYield') else "-")
                k8.metric("Volume", utils.format_large_number(info.get('volume')))

            with tab2:
                st.markdown("### Financial Performance")
                fin_df = data['financials'].T
                cash_df = data['cashflow'].T
                if not fin_df.empty:
                    fig_inc = go.Figure()
                    rev_col = [c for c in fin_df.columns if "Total Revenue" in c or "Revenue" in c]
                    inc_col = [c for c in fin_df.columns if "Net Income" in c]
                    rev_col = rev_col[0] if rev_col else None
                    inc_col = inc_col[0] if inc_col else None
                    if rev_col:
                        fig_inc.add_trace(go.Bar(x=fin_df.index.strftime('%Y'), y=fin_df[rev_col], name='Revenue', marker_color='#00C805'))
                    if inc_col:
                        fig_inc.add_trace(go.Bar(x=fin_df.index.strftime('%Y'), y=fin_df[inc_col], name='Net Income', marker_color='#000000'))
                    fig_inc.update_layout(title="Revenue vs Net Income", barmode='group', paper_bgcolor='white', plot_bgcolor='white', height=350, margin=dict(l=0, r=0, t=30, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                    st.plotly_chart(fig_inc, use_container_width=True)
                    if not cash_df.empty:
                        fig_cf = go.Figure()
                        ocf_col = [c for c in cash_df.columns if "Operating Cash Flow" in c]
                        fcf_col = [c for c in cash_df.columns if "Free Cash Flow" in c]
                        if ocf_col: fig_cf.add_trace(go.Bar(x=cash_df.index.strftime('%Y'), y=cash_df[ocf_col[0]], name='Operating CF', marker_color='#2962FF'))
                        if fcf_col: fig_cf.add_trace(go.Bar(x=cash_df.index.strftime('%Y'), y=cash_df[fcf_col[0]], name='Free Cash Flow', marker_color='#00C853'))
                        fig_cf.update_layout(title="Cash Flow Strength", barmode='group', paper_bgcolor='white', plot_bgcolor='white', height=350, margin=dict(l=0, r=0, t=30, b=20), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                        st.plotly_chart(fig_cf, use_container_width=True)
                    st.markdown("#### Annual Financials Data")
                    st.dataframe(fin_df.style.format("{:,.0f}"))
                else:
                    st.write("No financial data available.")

            with tab3:
                st.markdown("### Factor Radar")
                categories = ['Fundamentals', 'Valuation', 'Technicals', 'Risk']
                scores = [fund_res['score'], val_res['score'], tech_res['score'], risk_res['score']]
                categories = categories + [categories[0]]
                scores = scores + [scores[0]]
                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(r=scores, theta=categories, fill='toself', name=ticker_input, line_color='#00C805', fillcolor='rgba(0, 200, 5, 0.2)'))
                fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 10])), showlegend=False, height=400, margin=dict(l=40, r=40, t=20, b=20))
                c_radar, c_breakdown = st.columns([1, 1])
                with c_radar: st.plotly_chart(fig_radar, use_container_width=True)
                with c_breakdown:
                    st.markdown("#### Score Breakdown")
                    for k, v in {"Fundamentals": fund_res, "Valuation": val_res, "Technicals": tech_res, "Risk": risk_res}.items():
                        st.write(f"**{k}**")
                        st.progress(v['score'] / 10)
                        reasons = v.get('reasons', [])
                        if reasons: st.caption(f"• {reasons[0]}")
                st.markdown("---")
                # --- RATING HISTORY TRACK ---
                st.markdown("### 30-Day Rating History")
                if os.path.exists("scan_history.csv"):
                    hist_df = pd.read_csv("scan_history.csv")
                    t_hist = hist_df[hist_df['Ticker'] == ticker_input].sort_values("Date").tail(30)
                    if not t_hist.empty:
                        def score_to_rating(s):
                            if s > 80: return 3
                            if s > 60: return 2
                            return 1
                        t_hist['RatingNum'] = t_hist['TotalScore'].apply(score_to_rating)
                        t_hist['RatingLabel'] = t_hist['TotalScore'].apply(lambda s: "BUY" if s > 80 else "HOLD" if s > 60 else "SELL")
                        fig_range = go.Figure()
                        fig_range.add_trace(go.Scatter(x=t_hist['Date'], y=t_hist['RatingNum'], mode='lines+markers', line=dict(shape='hv', color='#174291', width=3), marker=dict(size=10, color='#174291', line=dict(width=2, color='white')), text=t_hist['RatingLabel'], hovertemplate="<b>Date: %{x}</b><br>Rating: %{text}<extra></extra>"))
                        fig_range.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=0), yaxis=dict(tickmode='array', tickvals=[1, 2, 3], ticktext=['SELL', 'HOLD', 'BUY'], range=[0.5, 3.5], gridcolor='#f0f0f0'), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='white')
                        st.plotly_chart(fig_range, use_container_width=True)
                    else: st.caption("No historical scan data available for this ticker yet.")
                else: st.caption("Scan history file not found.")

    else:
        st.markdown("""
        <div style='text-align: center; padding-top: 100px;'>
            <h1 style='color: #ccc; font-size: 4em;'>🔍</h1>
            <h2 style='color: #666;'>Enter a ticker to start</h2>
            <p style='color: #888;'>Explore the S&P 500 with institutional-grade AI analysis.</p>
        </div>
        """, unsafe_allow_html=True)

# --- PAGE: WATCHLIST ---
elif page == "Watchlist":
    st.markdown("## ⭐ My Watchlist")
    
    watchlist = utils.load_watchlist()
    
    if not watchlist:
        st.info("Your watchlist is empty. Add stocks from the Stock Analysis page!")
    else:
        st.caption(f"{len(watchlist)} stocks saved")
        
        # Display each watchlist stock with mini analysis
        for ticker in watchlist:
            with st.expander(f"**{ticker}**", expanded=False):
                try:
                    # Fetch data
                    import data_fetcher
                    data = data_fetcher.get_stock_data(ticker)
                    
                    # Run analysis
                    fund_res = fundamentals.analyze_fundamentals(data)
                    val_res = valuation.analyze_valuation(data)
                    tech_res = technicals.analyze_technicals(data)
                    risk_res = risk.analyze_risk(data)
                    score_res = scoring.factor_scores(fund_res, val_res, tech_res, risk_res)
                    
                    # Build metrics for card
                    metrics_wl = {
                        "ROE": (fund_res['metrics'].get('ROE') or 0) * 100,
                        "RevenueGrowth": fund_res['metrics'].get('Revenue Growth (3Y)') or fund_res['metrics'].get('Revenue Growth (1Y)') or 0,
                        "EPSGrowth": data['info'].get('earningsGrowth', 0),
                        "PE": val_res['metrics'].get('Trailing P/E') or 0,
                        "ForwardPE": val_res['metrics'].get('Forward P/E') or 0,
                        "DebtToEquity": (data['info'].get('debtToEquity') or 0),
                        "Price": tech_res['metrics'].get('Price') or 0,
                        "Beta": risk_res['metrics'].get('Beta') or 1.0,
                        "CompanyName": data['info'].get('longName', ticker),
                        "Rank": "N/A",
                        "TotalScore": score_res['total_score'] * 0.6,
                        "Score_Fundamentals": fund_res.get('score', 0) * 10,
                        "Score_Technicals": tech_res.get('score', 0) * 10,
                        "Score_Risk": risk_res.get('score', 0) * 10
                    }
                    
                    from ai_insights import generate_fidelity_card
                    card_html = generate_fidelity_card(ticker, score_res['recommendation'].split(" ")[0].upper(), metrics_wl)
                    st.markdown(card_html, unsafe_allow_html=True)
                    
                    # Remove button
                    if st.button(f"Remove {ticker}", key=f"rm_{ticker}"):
                        utils.toggle_watchlist(ticker)
                        st.success(f"Removed {ticker} from watchlist")
                        st.rerun()
                        
                except Exception as e:
                    st.error(f"Error loading {ticker}: {str(e)}")

