"""
Fund Analysis Page - Individual Fund Portfolio Analysis
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
sys.path.append('utils')

try:
    from utils.data_processor import SEC13FProcessor
except ImportError:
    from data_processor import SEC13FProcessor

st.set_page_config(page_title="Fund Analysis", page_icon="📈", layout="wide")

def load_data():
    """Load data from session state or initialize"""
    if 'processor' not in st.session_state or st.session_state.processor is None:
        with st.spinner("Loading SEC 13F data..."):
            processor = SEC13FProcessor('data')
            processor.load_data()
            st.session_state.processor = processor
            st.session_state.data_loaded = True
        st.success("Data loaded successfully!")
    return st.session_state.processor

def create_heatmap(holdings_data):
    """Create portfolio heatmap visualization"""
    if holdings_data.empty:
        return None
    
    # Prepare data for treemap
    holdings_data = holdings_data.head(30)  # Top 30 for better visualization
    holdings_data['portfolio_pct'] = (holdings_data['VALUE'] / holdings_data['VALUE'].sum()) * 100
    
    fig = px.treemap(
        holdings_data,
        values='VALUE',
        names='NAMEOFISSUER',
        title="Portfolio Holdings Heatmap (Top 30)",
        color='portfolio_pct',
        color_continuous_scale='RdYlBu_r',
        hover_data={'VALUE': ':,.0f', 'portfolio_pct': ':.2f'}
    )
    
    fig.update_layout(height=500)
    return fig

def main():
    st.title("📈 Fund Analysis")
    
    # Load data
    processor = load_data()
    
    # Get list of funds
    funds_list = processor.coverpage_df['FILINGMANAGER_NAME'].dropna().unique()
    funds_list = sorted([fund for fund in funds_list if fund and str(fund).strip()])
    
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
                
                portfolio_value = fund_summary['TABLEVALUETOTAL'].iloc[0] if not fund_summary.empty else None
                total_positions = fund_summary['TABLEENTRYTOTAL'].iloc[0] if not fund_summary.empty else None
                
                with col1:
                    st.metric("Portfolio Value", f"${portfolio_value/1e6:.1f}M" if pd.notna(portfolio_value) else "N/A")
                
                with col2:
                    st.metric("Total Positions", f"{total_positions:,.0f}" if pd.notna(total_positions) else "N/A")
                
            except Exception as e:
                st.warning(f"Could not load portfolio metrics: {str(e)}")
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
                
                # Portfolio heatmap
                st.subheader("🗺️ Portfolio Heatmap")
                heatmap_fig = create_heatmap(top_holdings)
                if heatmap_fig:
                    st.plotly_chart(heatmap_fig, use_container_width=True)
            else:
                st.warning("No holdings data found for this fund.")
        else:
            st.error("Fund data not found.")
    else:
        st.info("Please select a fund to analyze.")

if __name__ == "__main__":
    main()

