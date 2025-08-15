
"""
Hedge Fund Index MVP - Streamlit Application
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import custom utilities
import sys
sys.path.append('utils')
try:
    from utils.data_processor import SEC13FProcessor
except ImportError:
    # Fallback for different import paths
    from data_processor import SEC13FProcessor

# Page configuration
st.set_page_config(
    page_title="Hedge Fund Index",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state
if 'processor' not in st.session_state:
    st.session_state.processor = None
    st.session_state.data_loaded = False

def load_data():
    """Load SEC 13F data"""
    if not st.session_state.data_loaded:
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
    fig = px.treemap(
        holdings_data,
        values='portfolio_pct',
        names='NAMEOFISSUER',
        title="Portfolio Holdings Heatmap",
        color='portfolio_pct',
        color_continuous_scale='RdYlBu_r',
        hover_data=['VALUE']
    )
    
    fig.update_layout(
        height=600,
        font_size=12
    )
    
    return fig

def create_top_holdings_table(holdings_data):
    """Create formatted holdings table"""
    if holdings_data.empty:
        return None
        
    # Format the data for display
    display_data = holdings_data.copy()
    display_data['VALUE'] = display_data['VALUE'].apply(lambda x: f"${x:,.0f}")
    display_data['portfolio_pct'] = display_data['portfolio_pct'].apply(lambda x: f"{x:.2f}%")
    display_data['SSHPRNAMT'] = display_data['SSHPRNAMT'].apply(lambda x: f"{x:,.0f}")
    
    # Rename columns for display
    display_data = display_data.rename(columns={
        'NAMEOFISSUER': 'Security',
        'TITLEOFCLASS': 'Type',
        'VALUE': 'Value',
        'SSHPRNAMT': 'Shares',
        'portfolio_pct': 'Portfolio %',
        'PUTCALL': 'Put/Call'
    })
    
    return display_data[['Security', 'Type', 'Value', 'Shares', 'Portfolio %', 'Put/Call']]

def main():
    """Main application"""
    
    # Sidebar navigation
    st.sidebar.title("📊 Hedge Fund Index")
    st.sidebar.markdown("---")
    
    # Navigation
    pages = {
        "🏠 Overview": "overview",
        "📈 Fund Analysis": "fund_analysis", 
        "🔍 Holdings Explorer": "holdings_explorer",
        "📊 Market Insights": "market_insights",
        "⚙️ Data Processing": "data_processing"
    }
    
    selected_page = st.sidebar.selectbox("Navigate to:", list(pages.keys()))
    page_key = pages[selected_page]
    
    # Load data
    processor = load_data()
    
    # Page routing
    if page_key == "overview":
        show_overview(processor)
    elif page_key == "fund_analysis":
        show_fund_analysis(processor)
    elif page_key == "holdings_explorer":
        show_holdings_explorer(processor)
    elif page_key == "market_insights":
        show_market_insights(processor)
    elif page_key == "data_processing":
        show_data_processing(processor)

def show_overview(processor):
    """Overview page"""
    st.title("🏠 Hedge Fund Index - Overview")
    st.markdown("---")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Funds", len(processor.coverpage_df))
    
    with col2:
        total_holdings = len(processor.infotable_df)
        st.metric("Total Holdings", f"{total_holdings:,}")
    
    with col3:
        total_value = processor.infotable_df['VALUE'].sum()
        st.metric("Total AUM", f"${total_value/1e9:.1f}B")
    
    with col4:
        unique_securities = processor.infotable_df['NAMEOFISSUER'].nunique()
        st.metric("Unique Securities", f"{unique_securities:,}")
    
    st.markdown("---")
    
    # Top funds by AUM
    st.subheader("📊 Top Funds by Assets Under Management")
    
    funds_list = processor.get_fund_list()
    top_funds = funds_list.head(20)
    
    # Format for display
    display_funds = top_funds.copy()
    display_funds['TABLEVALUETOTAL'] = display_funds['TABLEVALUETOTAL'].apply(
        lambda x: f"${x/1e6:.1f}M" if pd.notna(x) else "N/A"
    )
    display_funds['TABLEENTRYTOTAL'] = display_funds['TABLEENTRYTOTAL'].apply(
        lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A"
    )
    
    display_funds = display_funds.rename(columns={
        'FILINGMANAGER_NAME': 'Fund Name',
        'TABLEVALUETOTAL': 'Portfolio Value',
        'TABLEENTRYTOTAL': 'Total Positions'
    })
    
    st.dataframe(
        display_funds[['Fund Name', 'Portfolio Value', 'Total Positions']],
        use_container_width=True,
        height=400
    )

def show_fund_analysis(processor):
    """Fund analysis page"""
    st.title("📈 Fund Analysis")
    st.markdown("---")
    
    # Fund selection
    funds_list = processor.get_fund_list()
    fund_names = funds_list['FILINGMANAGER_NAME'].tolist()
    
    selected_fund = st.selectbox(
        "Select a fund to analyze:",
        fund_names,
        index=0 if fund_names else None
    )
    
    if selected_fund:
        # Get fund summary
        summary = processor.get_fund_summary(selected_fund)
        
        if 'error' not in summary:
            # Display fund metrics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Portfolio Value", 
                    f"${summary['total_portfolio_value']/1e6:.1f}M"
                )
            
            with col2:
                st.metric("Total Positions", summary['total_positions'])
            
            with col3:
                st.metric("Unique Securities", summary['unique_securities'])
            
            st.markdown("---")
            
            # Get top holdings
            top_holdings = processor.get_top_holdings(selected_fund, top_n=100)
            
            if not top_holdings.empty:
                # Create two columns for heatmap and table
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("📊 Portfolio Heatmap")
                    heatmap_data = processor.create_heatmap_data(selected_fund)
                    if not heatmap_data.empty:
                        fig = create_heatmap(heatmap_data)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    st.subheader("🔝 Top Holdings")
                    table_data = create_top_holdings_table(top_holdings.head(20))
                    if table_data is not None:
                        st.dataframe(table_data, use_container_width=True, height=600)
                
                # Full holdings table
                st.markdown("---")
                st.subheader("📋 Complete Holdings")
                full_table = create_top_holdings_table(top_holdings)
                if full_table is not None:
                    st.dataframe(full_table, use_container_width=True, height=400)
        else:
            st.error(summary['error'])

def show_holdings_explorer(processor):
    """Holdings explorer page"""
    st.title("🔍 Holdings Explorer")
    st.markdown("---")
    
    # Search functionality
    search_term = st.text_input("Search for securities:", placeholder="e.g., NVIDIA, Apple, Tesla")
    
    if search_term:
        # Search in holdings data
        holdings = processor.infotable_df
        search_results = holdings[
            holdings['NAMEOFISSUER'].str.contains(search_term, case=False, na=False)
        ]
        
        if not search_results.empty:
            st.subheader(f"📊 Search Results for '{search_term}'")
            
            # Group by fund and security
            grouped = search_results.groupby(['NAMEOFISSUER', 'TITLEOFCLASS']).agg({
                'VALUE': 'sum',
                'SSHPRNAMT': 'sum'
            }).reset_index()
            
            # Sort by value
            grouped = grouped.sort_values('VALUE', ascending=False)
            
            # Format for display
            display_results = grouped.copy()
            display_results['VALUE'] = display_results['VALUE'].apply(lambda x: f"${x:,.0f}")
            display_results['SSHPRNAMT'] = display_results['SSHPRNAMT'].apply(lambda x: f"{x:,.0f}")
            
            display_results = display_results.rename(columns={
                'NAMEOFISSUER': 'Security',
                'TITLEOFCLASS': 'Type',
                'VALUE': 'Total Value',
                'SSHPRNAMT': 'Total Shares'
            })
            
            st.dataframe(display_results, use_container_width=True)
            
            # Show which funds hold this security
            st.subheader("🏢 Funds Holding This Security")
            
            # Get fund names for these holdings
            accession_numbers = search_results['ACCESSION_NUMBER'].unique()
            fund_info = processor.coverpage_df[
                processor.coverpage_df['ACCESSION_NUMBER'].isin(accession_numbers)
            ][['FILINGMANAGER_NAME', 'ACCESSION_NUMBER']]
            
            # Merge with holdings
            fund_holdings = search_results.merge(fund_info, on='ACCESSION_NUMBER')
            fund_summary = fund_holdings.groupby('FILINGMANAGER_NAME').agg({
                'VALUE': 'sum',
                'SSHPRNAMT': 'sum'
            }).reset_index()
            
            fund_summary = fund_summary.sort_values('VALUE', ascending=False)
            
            # Format for display
            fund_summary['VALUE'] = fund_summary['VALUE'].apply(lambda x: f"${x:,.0f}")
            fund_summary['SSHPRNAMT'] = fund_summary['SSHPRNAMT'].apply(lambda x: f"{x:,.0f}")
            
            fund_summary = fund_summary.rename(columns={
                'FILINGMANAGER_NAME': 'Fund Name',
                'VALUE': 'Position Value',
                'SSHPRNAMT': 'Shares Held'
            })
            
            st.dataframe(fund_summary, use_container_width=True)
        else:
            st.info(f"No holdings found for '{search_term}'")

def show_market_insights(processor):
    """Market insights page"""
    st.title("📊 Market Insights")
    st.markdown("---")
    
    st.subheader("🔝 Most Popular Securities")
    
    # Analyze most held securities
    holdings = processor.infotable_df
    
    # Count number of funds holding each security
    security_popularity = holdings.groupby('NAMEOFISSUER').agg({
        'ACCESSION_NUMBER': 'nunique',  # Number of funds
        'VALUE': 'sum',  # Total value across all funds
        'SSHPRNAMT': 'sum'  # Total shares
    }).reset_index()
    
    security_popularity = security_popularity.rename(columns={
        'ACCESSION_NUMBER': 'num_funds',
        'NAMEOFISSUER': 'security'
    })
    
    # Sort by number of funds holding
    security_popularity = security_popularity.sort_values('num_funds', ascending=False)
    
    # Display top securities
    top_securities = security_popularity.head(20)
    
    # Create visualization
    fig = px.bar(
        top_securities,
        x='security',
        y='num_funds',
        title="Most Widely Held Securities",
        labels={'num_funds': 'Number of Funds', 'security': 'Security'}
    )
    fig.update_xaxes(tickangle=45)
    fig.update_layout(height=500)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Table view
    display_securities = top_securities.copy()
    display_securities['VALUE'] = display_securities['VALUE'].apply(lambda x: f"${x/1e6:.1f}M")
    display_securities['SSHPRNAMT'] = display_securities['SSHPRNAMT'].apply(lambda x: f"{x:,.0f}")
    
    display_securities = display_securities.rename(columns={
        'security': 'Security',
        'num_funds': 'Funds Holding',
        'VALUE': 'Total Value',
        'SSHPRNAMT': 'Total Shares'
    })
    
    st.dataframe(display_securities, use_container_width=True)

def show_data_processing(processor):
    """Data processing page"""
    st.title("⚙️ Data Processing")
    st.markdown("---")
    
    st.subheader("📊 Dataset Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Holdings Data (INFOTABLE.tsv)**")
        st.write(f"- Records: {len(processor.infotable_df):,}")
        st.write(f"- Columns: {len(processor.infotable_df.columns)}")
        st.write(f"- Memory usage: {processor.infotable_df.memory_usage(deep=True).sum() / 1e6:.1f} MB")
        
        st.write("**Fund Data (COVERPAGE.tsv)**")
        st.write(f"- Records: {len(processor.coverpage_df):,}")
        st.write(f"- Columns: {len(processor.coverpage_df.columns)}")
    
    with col2:
        st.write("**Data Quality Checks**")
        
        # Check for missing values in key fields
        missing_values = processor.infotable_df[['NAMEOFISSUER', 'VALUE', 'SSHPRNAMT']].isnull().sum()
        st.write("Missing values:")
        for col, count in missing_values.items():
            st.write(f"- {col}: {count:,}")
    
    # Sample data preview
    st.subheader("📋 Sample Data Preview")
    
    tab1, tab2 = st.tabs(["Holdings Sample", "Fund Sample"])
    
    with tab1:
        st.dataframe(processor.infotable_df.head(10), use_container_width=True)
    
    with tab2:
        st.dataframe(processor.coverpage_df.head(10), use_container_width=True)
    
    # Export functionality
    st.subheader("💾 Export Data")
    
    if st.button("Export Processed Data to CSV"):
        with st.spinner("Exporting data..."):
            processor.export_to_csv('data/processed')
        st.success("Data exported to data/processed/ directory")

if __name__ == "__main__":
    main()

