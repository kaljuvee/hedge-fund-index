"""
Holdings Explorer Page - Search Securities Across All Funds
"""
import streamlit as st
import pandas as pd
import sys
sys.path.append('utils')

try:
    from utils.data_processor import SEC13FProcessor
except ImportError:
    from data_processor import SEC13FProcessor

st.set_page_config(page_title="Holdings Explorer", page_icon="🔍", layout="wide")

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

def search_securities(processor, query):
    """Search for securities by name"""
    if not query:
        return pd.DataFrame(), pd.DataFrame()
    
    # Search in holdings data
    holdings = processor.infotable_df
    mask = holdings['NAMEOFISSUER'].str.contains(query, case=False, na=False)
    matching_holdings = holdings[mask]
    
    if matching_holdings.empty:
        return pd.DataFrame(), pd.DataFrame()
    
    # Aggregate by security
    security_summary = matching_holdings.groupby(['NAMEOFISSUER', 'TITLEOFCLASS']).agg({
        'VALUE': 'sum',
        'SSHPRNAMT': 'sum',
        'ACCESSION_NUMBER': 'count'
    }).reset_index()
    
    security_summary.columns = ['Security', 'Type', 'Total Value', 'Total Shares', 'Fund Count']
    security_summary = security_summary.sort_values('Total Value', ascending=False)
    
    # Get funds holding these securities
    accession_numbers = matching_holdings['ACCESSION_NUMBER'].unique()
    fund_data = processor.coverpage_df[
        processor.coverpage_df['ACCESSION_NUMBER'].isin(accession_numbers)
    ]
    
    # Merge with holdings to get position values
    fund_holdings = matching_holdings.merge(
        fund_data[['ACCESSION_NUMBER', 'FILINGMANAGER_NAME']], 
        on='ACCESSION_NUMBER'
    )
    
    fund_summary = fund_holdings.groupby('FILINGMANAGER_NAME').agg({
        'VALUE': 'sum',
        'SSHPRNAMT': 'sum'
    }).reset_index()
    
    fund_summary.columns = ['Fund Name', 'Position Value', 'Shares Held']
    fund_summary = fund_summary.sort_values('Position Value', ascending=False)
    
    return security_summary, fund_summary

def main():
    st.title("🔍 Holdings Explorer")
    
    # Load data
    processor = load_data()
    
    # Initialize session state for search
    if 'search_query' not in st.session_state:
        st.session_state.search_query = ""
    
    # Search interface
    query = st.text_input(
        "Search for securities:",
        value=st.session_state.search_query,
        placeholder="e.g., NVIDIA, Apple, Tesla",
        help="Enter a company name or ticker symbol to search across all fund holdings"
    )
    
    # Update session state if query changed
    if query != st.session_state.search_query:
        st.session_state.search_query = query
    
    if query:
        with st.spinner("Searching..."):
            security_results, fund_results = search_securities(processor, query)
        
        if not security_results.empty:
            st.subheader(f"📊 Search Results for '{query}'")
            
            # Format security results for display
            display_securities = security_results.copy()
            display_securities['Total Value'] = display_securities['Total Value'].apply(lambda x: f"${x:,.0f}")
            display_securities['Total Shares'] = display_securities['Total Shares'].apply(lambda x: f"{x:,.0f}")
            
            st.dataframe(display_securities, use_container_width=True)
            
            if not fund_results.empty:
                st.subheader("🏢 Funds Holding This Security")
                
                # Format fund results for display
                display_funds = fund_results.copy()
                display_funds['Position Value'] = display_funds['Position Value'].apply(lambda x: f"${x:,.0f}")
                display_funds['Shares Held'] = display_funds['Shares Held'].apply(lambda x: f"{x:,.0f}")
                
                st.dataframe(display_funds, use_container_width=True)
                
                # Summary statistics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    total_funds = len(fund_results)
                    st.metric("Funds Holding", total_funds)
                
                with col2:
                    total_value = fund_results['Position Value'].sum()
                    st.metric("Total Position Value", f"${total_value/1e9:.1f}B")
                
                with col3:
                    avg_position = fund_results['Position Value'].mean()
                    st.metric("Average Position", f"${avg_position/1e6:.1f}M")
        else:
            st.warning(f"No securities found matching '{query}'. Try a different search term.")
    else:
        st.info("Enter a search term to find securities across all fund holdings.")
        
        # Show some example searches
        st.subheader("💡 Example Searches")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Search NVIDIA"):
                # Use session state to trigger search
                st.session_state.search_query = "NVIDIA"
                st.rerun()
        
        with col2:
            if st.button("Search Apple"):
                # Use session state to trigger search
                st.session_state.search_query = "APPLE"
                st.rerun()
        
        with col3:
            if st.button("Search Tesla"):
                # Use session state to trigger search
                st.session_state.search_query = "TESLA"
                st.rerun()

if __name__ == "__main__":
    main()

