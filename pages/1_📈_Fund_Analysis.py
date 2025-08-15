import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import sys
import os

# Add the parent directory to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.data_processor import SEC13FProcessor
    from utils.yf_util import get_stock_info_batch, extract_ticker_from_cusip
except ImportError:
    try:
        from data_processor import SEC13FProcessor
        from yf_util import get_stock_info_batch, extract_ticker_from_cusip
    except ImportError:
        st.error("Could not import required modules")

@st.cache_data
def load_data():
    """Load and cache the SEC 13F data"""
    try:
        processor = SEC13FProcessor()
        processor.load_data()  # Call load_data method
        return processor
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

def create_heatmap(holdings_df):
    """Create a treemap heatmap of portfolio holdings with price changes and sectors"""
    try:
        if holdings_df.empty or len(holdings_df) < 1:
            st.info("Not enough holdings data to create heatmap (minimum 1 holding required)")
            return None
        
        # Take top 20 holdings for better visualization
        top_holdings = holdings_df.head(20).copy()
        
        # Ensure we have the required columns
        if 'portfolio_pct' not in top_holdings.columns:
            st.error("Portfolio percentage data not available")
            return None
        
        # Extract tickers from company names
        top_holdings['ticker'] = top_holdings['NAMEOFISSUER'].apply(extract_ticker_from_cusip)
        
        # Get stock information for available tickers
        available_tickers = [ticker for ticker in top_holdings['ticker'] if ticker]
        
        if available_tickers:
            with st.spinner("Fetching stock price changes and sector data..."):
                stock_info = get_stock_info_batch(available_tickers)
            
            # Add stock information to holdings
            top_holdings['price_change'] = top_holdings['ticker'].apply(
                lambda x: stock_info.get(x, {}).get('price_change') if x else None
            )
            top_holdings['sector'] = top_holdings['ticker'].apply(
                lambda x: stock_info.get(x, {}).get('sector') if x else "Unknown"
            )
        else:
            top_holdings['price_change'] = None
            top_holdings['sector'] = "Unknown"
        
        # Use price change for color, fallback to random if no data
        if top_holdings['price_change'].notna().any():
            # Normalize price changes to 0-1 range for color mapping
            price_changes = top_holdings['price_change'].fillna(0)
            max_change = max(abs(price_changes.min()), abs(price_changes.max()))
            if max_change > 0:
                top_holdings['color_value'] = price_changes / max_change
            else:
                top_holdings['color_value'] = 0
        else:
            # Fallback to random colors
            np.random.seed(42)
            top_holdings['color_value'] = np.random.uniform(0, 1, len(top_holdings))
        
        # Create labels with company name, ticker, and percentage
        top_holdings['label'] = top_holdings.apply(
            lambda row: f"{row['NAMEOFISSUER']}<br>{row['ticker'] or 'N/A'}<br>{row['portfolio_pct']:.1f}%", 
            axis=1
        )
        
        # Ensure all required columns exist and are properly formatted
        treemap_data = top_holdings.copy()
        
        # Clean up sector names and ensure they're strings
        treemap_data['sector'] = treemap_data['sector'].fillna('Unknown').astype(str)
        
        # Ensure color_value is numeric
        treemap_data['color_value'] = pd.to_numeric(treemap_data['color_value'], errors='coerce').fillna(0)
        
        # Ensure portfolio_pct is numeric
        treemap_data['portfolio_pct'] = pd.to_numeric(treemap_data['portfolio_pct'], errors='coerce').fillna(0)
        
        # Create treemap with simplified configuration
        fig = px.treemap(
            treemap_data,
            path=['sector', 'label'],
            values='portfolio_pct',
            color='color_value',
            color_continuous_scale='RdYlGn',
            title='Portfolio Holdings by Sector (Top 20)',
            hover_data=['VALUE', 'portfolio_pct', 'SSHPRNAMT', 'price_change', 'ticker']
        )
        
        # Update layout
        fig.update_layout(
            height=700,
            font_size=11,
            title_font_size=16,
            margin=dict(t=50, l=25, r=25, b=25),
            coloraxis_showscale=True,
            coloraxis_colorbar=dict(
                title="Price Change %",
                thickness=15,
                len=0.5
            )
        )
        
        # Update traces for better text display
        fig.update_traces(
            textfont_size=9,
            textposition="middle center",
            texttemplate="%{label}"
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating heatmap: {str(e)}")
        # Add debugging information
        st.write("Debug info:")
        st.write(f"DataFrame shape: {top_holdings.shape}")
        st.write(f"Columns: {list(top_holdings.columns)}")
        st.write(f"Sample data:")
        st.write(top_holdings.head())
        return None

def main():
    st.title("📈 Fund Analysis")
    
    # Documentation and Help Section
    with st.expander("📖 How to Use This Page", expanded=False):
        st.markdown("""
        ## 🎯 Purpose
        This page provides detailed analysis of individual hedge fund portfolios, including holdings, sector breakdown, and performance metrics.
        
        ## 🔍 How to Use
        
        ### 1. **Select a Fund**
        - Use the dropdown to choose from available hedge funds
        - Funds are listed by their filing manager name
        
        ### 2. **View Portfolio Metrics**
        - **Portfolio Value**: Total value of all holdings
        - **Total Positions**: Number of individual securities held
        - **Unique Securities**: Number of different companies/entities
        
        ### 3. **Analyze Top Holdings**
        - View the fund's largest positions by value
        - See portfolio allocation percentages
        - Identify concentration risk
        
        ### 4. **Sector Analysis** 📊
        - **Sector Distribution**: How the portfolio is allocated across industries
        - **Price Change Summary**: Average 1-month performance of holdings
        - **Positive/Negative Movers**: Count of stocks that gained or lost value
        
        ### 5. **Interactive Treemap** 🗺️
        The treemap visualization provides:
        - **Hierarchical View**: Stocks grouped by sector → company
        - **Size**: Box size represents portfolio allocation percentage
        - **Color Coding**: 
          - 🔴 **Red**: Stocks that declined in the past month
          - 🟡 **Yellow**: Neutral performance
          - 🟢 **Green**: Stocks that gained value
        - **Hover Information**: Detailed data on each position
        
        ## 💡 Interpretation Tips
        
        - **Large boxes** = High portfolio concentration (potential risk)
        - **Red clusters** = Sectors with recent underperformance
        - **Green clusters** = Sectors with recent outperformance
        - **Sector diversity** = Lower concentration risk
        
        ## ⚠️ Data Notes
        - Price changes are based on 1-month Yahoo Finance data
        - Sector information comes from Yahoo Finance
        - Some companies may not have ticker mappings available
        """)
    
    # Load data
    
    # Load data
    processor = load_data()
    
    if processor is None:
        st.error("Failed to load data processor")
        return
    
    # Get list of funds
    try:
        funds_list = processor.coverpage_df['FILINGMANAGER_NAME'].dropna().unique()
        funds_list = sorted([fund for fund in funds_list if fund and str(fund).strip()])
    except Exception as e:
        st.error(f"Error loading funds list: {str(e)}")
        funds_list = []
    
    # Fund selection
    selected_fund = st.selectbox(
        "Select a fund to analyze:",
        funds_list,
        index=0 if funds_list else None
    )
    
    if selected_fund:
        # Get fund data
        fund_data = processor.coverpage_df[
            processor.coverpage_df['FILINGMANAGER_NAME'] == selected_fund
        ]
        
        if not fund_data.empty:
            # Load summary data for portfolio metrics
            try:
                summary_df = pd.read_csv('data/SUMMARYPAGE.tsv', sep='\t')
                fund_summary = fund_data.merge(
                    summary_df[['ACCESSION_NUMBER', 'TABLEVALUETOTAL', 'TABLEENTRYTOTAL']], 
                    on='ACCESSION_NUMBER', 
                    how='left'
                )
                
                # Display fund metrics
                col1, col2, col3 = st.columns(3)
                
                portfolio_value = fund_summary['TABLEVALUETOTAL'].sum() if 'TABLEVALUETOTAL' in fund_summary.columns else 0
                total_positions = fund_summary['TABLEENTRYTOTAL'].sum() if 'TABLEENTRYTOTAL' in fund_summary.columns else 0
                
                with col1:
                    st.metric("Portfolio Value", f"${portfolio_value/1e6:.1f}M")
                
                with col2:
                    st.metric("Total Positions", f"{total_positions:,}")
                
            except Exception as e:
                st.warning(f"Could not load summary data: {str(e)}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Portfolio Value", "N/A")
                with col2:
                    st.metric("Total Positions", "N/A")
            
            # Get holdings for this fund
            accession_numbers = fund_data['ACCESSION_NUMBER'].tolist()
            holdings = processor.infotable_df[
                processor.infotable_df['ACCESSION_NUMBER'].isin(accession_numbers)
            ]
            
            unique_securities = holdings['NAMEOFISSUER'].nunique() if not holdings.empty else 0
            
            with col3:
                st.metric("Unique Securities", f"{unique_securities:,}")
            
            if not holdings.empty:
                # Top holdings
                st.subheader("🔝 Top Holdings")
                
                top_holdings = holdings.groupby(['NAMEOFISSUER', 'TITLEOFCLASS']).agg({
                    'VALUE': 'sum',
                    'SSHPRNAMT': 'sum',
                    'PUTCALL': 'first',
                    'CUSIP': 'first'
                }).reset_index()
                
                # Calculate portfolio percentage
                total_value = top_holdings['VALUE'].sum()
                top_holdings['portfolio_pct'] = (top_holdings['VALUE'] / total_value) * 100
                
                # Sort and display top 50
                top_holdings = top_holdings.sort_values('VALUE', ascending=False).head(50)
                
                # Format for display
                display_holdings = top_holdings.copy()
                display_holdings['VALUE'] = display_holdings['VALUE'].apply(lambda x: f"${x/1e6:.1f}M")
                display_holdings['SSHPRNAMT'] = display_holdings['SSHPRNAMT'].apply(lambda x: f"{x:,.0f}")
                display_holdings['portfolio_pct'] = display_holdings['portfolio_pct'].apply(lambda x: f"{x:.2f}%")
                
                display_holdings = display_holdings[['NAMEOFISSUER', 'TITLEOFCLASS', 'VALUE', 'SSHPRNAMT', 'portfolio_pct']]
                display_holdings.columns = ['Security', 'Type', 'Value', 'Shares', 'Portfolio %']
                
                st.dataframe(display_holdings, use_container_width=True)
                
                # Sector and Price Change Analysis
                if not top_holdings.empty:
                    # Extract tickers and get stock info for analysis
                    top_holdings_analysis = top_holdings.copy()
                    top_holdings_analysis['ticker'] = top_holdings_analysis['NAMEOFISSUER'].apply(extract_ticker_from_cusip)
                    available_tickers = [ticker for ticker in top_holdings_analysis['ticker'] if ticker]
                    
                    if available_tickers:
                        with st.spinner("Analyzing sector distribution and price changes..."):
                            stock_info = get_stock_info_batch(available_tickers)
                        
                        # Add stock information
                        top_holdings_analysis['price_change'] = top_holdings_analysis['ticker'].apply(
                            lambda x: stock_info.get(x, {}).get('price_change') if x else None
                        )
                        top_holdings_analysis['sector'] = top_holdings_analysis['ticker'].apply(
                            lambda x: stock_info.get(x, {}).get('sector') if x else "Unknown"
                        )
                        
                        # Sector breakdown
                        st.subheader("📊 Sector Analysis")
                        sector_breakdown = top_holdings_analysis.groupby('sector').agg({
                            'VALUE': 'sum',
                            'portfolio_pct': 'sum',
                            'price_change': 'mean'
                        }).round(2)
                        sector_breakdown = sector_breakdown.sort_values('VALUE', ascending=False)
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**Sector Distribution by Value:**")
                            sector_display = sector_breakdown.copy()
                            sector_display['VALUE'] = sector_display['VALUE'].apply(lambda x: f"${x/1e6:.1f}M")
                            sector_display['portfolio_pct'] = sector_display['portfolio_pct'].apply(lambda x: f"{x:.1f}%")
                            sector_display['price_change'] = sector_display['price_change'].apply(lambda x: f"{x:.2f}%" if pd.notna(x) else "N/A")
                            sector_display.columns = ['Value', 'Portfolio %', 'Avg Price Change']
                            st.dataframe(sector_display, use_container_width=True)
                        
                        with col2:
                            st.write("**Price Change Summary:**")
                            price_summary = top_holdings_analysis[top_holdings_analysis['price_change'].notna()]
                            if not price_summary.empty:
                                avg_change = price_summary['price_change'].mean()
                                positive_count = (price_summary['price_change'] > 0).sum()
                                total_count = len(price_summary)
                                
                                st.metric("Average 1-Month Change", f"{avg_change:.2f}%")
                                st.metric("Positive Movers", f"{positive_count}/{total_count} ({positive_count/total_count*100:.1f}%)")
                                st.metric("Negative Movers", f"{total_count-positive_count}/{total_count} ({(total_count-positive_count)/total_count*100:.1f}%)")
                            else:
                                st.info("No price change data available")
                
                # Portfolio heatmap
                st.subheader("🗺️ Portfolio Heatmap by Sector")
                st.write("Portfolio Holdings Treemap with 1-Month Price Changes (Top 20)")
                
                heatmap_fig = create_heatmap(top_holdings)
                if heatmap_fig:
                    # Use plotly_chart with proper configuration for treemap
                    st.plotly_chart(
                        heatmap_fig, 
                        use_container_width=True,
                        config={
                            'displayModeBar': True,
                            'displaylogo': False,
                            'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d']
                        }
                    )
                    
                    # Add legend explanation
                    st.markdown("""
                    **Color Legend:**
                    - 🔴 **Red**: Negative price change (stock declined)
                    - 🟡 **Yellow**: Neutral price change
                    - 🟢 **Green**: Positive price change (stock gained)
                    """)
                else:
                    st.info("Heatmap could not be generated for this fund.")
            else:
                st.warning("No holdings data found for this fund.")
        else:
            st.error("Fund data not found.")
    else:
        st.info("Please select a fund to analyze.")

if __name__ == "__main__":
    main()

