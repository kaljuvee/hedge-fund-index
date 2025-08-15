"""
Hedge Fund Index MVP - Main Application
"""
import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# Disable file watching to prevent inotify issues on Streamlit Cloud
import os
os.environ['STREAMLIT_SERVER_FILE_WATCHER_TYPE'] = 'none'
os.environ['STREAMLIT_SERVER_RUN_ON_SAVE'] = 'false'

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

def main():
    """Main application"""
    st.title("🏠 Hedge Fund Index - Overview")
    
    # Load data
    processor = load_data()
    
    # Display key metrics
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
    
    # Display top funds
    st.subheader("📊 Top Funds by Assets Under Management")
    
    # Load and merge summary data
    try:
        summary_df = pd.read_csv(os.path.join('data', 'SUMMARYPAGE.tsv'), sep='\t')
        
        # Merge coverpage with summary data
        fund_summary = processor.coverpage_df.merge(
            summary_df[['ACCESSION_NUMBER', 'TABLEVALUETOTAL', 'TABLEENTRYTOTAL']], 
            on='ACCESSION_NUMBER', 
            how='left'
        )
        
        # Sort by portfolio value
        fund_summary = fund_summary.sort_values('TABLEVALUETOTAL', ascending=False, na_position='last')
        
        # Display top 20 funds
        top_funds = fund_summary.head(20)[['FILINGMANAGER_NAME', 'TABLEVALUETOTAL', 'TABLEENTRYTOTAL']]
        top_funds.columns = ['Fund Name', 'Portfolio Value', 'Total Positions']
        top_funds['Portfolio Value'] = top_funds['Portfolio Value'].apply(lambda x: f"${x/1e6:.1f}M" if pd.notna(x) else "N/A")
        top_funds['Total Positions'] = top_funds['Total Positions'].apply(lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A")
        
        st.dataframe(top_funds, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading fund summary data: {str(e)}")
        
        # Fallback: show funds without portfolio values
        top_funds_fallback = processor.coverpage_df.head(20)[['FILINGMANAGER_NAME']]
        top_funds_fallback.columns = ['Fund Name']
        st.dataframe(top_funds_fallback, use_container_width=True)
    
    # Instructions for navigation
    st.info("📌 **Navigation**: Use the sidebar to explore different features:")
    st.write("- **📈 Fund Analysis**: Analyze individual fund portfolios")
    st.write("- **🔍 Holdings Explorer**: Search for securities across all funds")
    st.write("- **📊 Market Insights**: View most popular securities")
    st.write("- **⚙️ Data Processing**: View data quality and export options")

if __name__ == "__main__":
    main()

