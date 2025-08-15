"""
Market Insights Page - Popular Securities and Market Trends
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import sys
sys.path.append('utils')

try:
    from utils.data_processor import SEC13FProcessor
except ImportError:
    from data_processor import SEC13FProcessor

st.set_page_config(page_title="Market Insights", page_icon="📊", layout="wide")

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

def get_popular_securities(processor, top_n=50):
    """Get most popular securities by total value and fund count"""
    holdings = processor.infotable_df
    
    # Aggregate by security
    popular = holdings.groupby(['NAMEOFISSUER', 'TITLEOFCLASS']).agg({
        'VALUE': 'sum',
        'SSHPRNAMT': 'sum',
        'ACCESSION_NUMBER': 'nunique'
    }).reset_index()
    
    popular.columns = ['Security', 'Type', 'Total Value', 'Total Shares', 'Fund Count']
    popular = popular.sort_values('Total Value', ascending=False).head(top_n)
    
    return popular

def get_fund_concentration(processor, top_n=20):
    """Get fund concentration metrics"""
    try:
        # Load summary data
        summary_df = pd.read_csv('data/SUMMARYPAGE.tsv', sep='\t')
        
        # Merge with coverpage data
        fund_summary = processor.coverpage_df.merge(
            summary_df[['ACCESSION_NUMBER', 'TABLEVALUETOTAL', 'TABLEENTRYTOTAL']], 
            on='ACCESSION_NUMBER', 
            how='left'
        )
        
        # Sort by portfolio value
        fund_summary = fund_summary.sort_values('TABLEVALUETOTAL', ascending=False, na_position='last')
        
        top_funds = fund_summary.head(top_n)
        return top_funds[['FILINGMANAGER_NAME', 'TABLEVALUETOTAL', 'TABLEENTRYTOTAL']]
        
    except Exception as e:
        st.warning(f"Could not load fund concentration data: {str(e)}")
        # Fallback: return basic fund data
        return processor.coverpage_df.head(top_n)[['FILINGMANAGER_NAME']]

def main():
    st.title("📊 Market Insights")
    
    # Load data
    processor = load_data()
    
    # Market overview metrics
    st.subheader("🌍 Market Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_funds = len(processor.coverpage_df)
        st.metric("Total Funds", f"{total_funds:,}")
    
    with col2:
        total_holdings = len(processor.infotable_df)
        st.metric("Total Holdings", f"{total_holdings:,}")
    
    with col3:
        total_value = processor.infotable_df['VALUE'].sum()
        st.metric("Total AUM", f"${total_value/1e12:.1f}T")
    
    with col4:
        unique_securities = processor.infotable_df['NAMEOFISSUER'].nunique()
        st.metric("Unique Securities", f"{unique_securities:,}")
    
    # Most popular securities
    st.subheader("🔥 Most Popular Securities")
    
    popular_securities = get_popular_securities(processor, 30)
    
    # Format for display
    display_popular = popular_securities.copy()
    display_popular['Total Value'] = display_popular['Total Value'].apply(lambda x: f"${x/1e9:.1f}B")
    display_popular['Total Shares'] = display_popular['Total Shares'].apply(lambda x: f"{x/1e6:.1f}M")
    
    st.dataframe(display_popular, use_container_width=True)
    
    # Visualization: Top securities by value
    st.subheader("📈 Top Securities by Total Value")
    
    top_10_securities = popular_securities.head(10)
    fig_bar = px.bar(
        top_10_securities,
        x='Total Value',
        y='Security',
        orientation='h',
        title="Top 10 Securities by Total Value Across All Funds",
        labels={'Total Value': 'Total Value ($)', 'Security': 'Security Name'}
    )
    fig_bar.update_layout(height=500, yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig_bar, use_container_width=True)
    
    # Fund concentration
    st.subheader("🏛️ Fund Concentration")
    
    fund_concentration = get_fund_concentration(processor, 15)
    
    # Format for display
    display_concentration = fund_concentration.copy()
    display_concentration.columns = ['Fund Name', 'Portfolio Value', 'Total Positions']
    display_concentration['Portfolio Value'] = display_concentration['Portfolio Value'].apply(
        lambda x: f"${x/1e9:.1f}B" if pd.notna(x) else "N/A"
    )
    display_concentration['Total Positions'] = display_concentration['Total Positions'].apply(
        lambda x: f"{x:,.0f}" if pd.notna(x) else "N/A"
    )
    
    st.dataframe(display_concentration, use_container_width=True)
    
    # Pie chart of top funds
    st.subheader("🥧 Market Share Distribution")
    
    # Get top 10 funds for pie chart
    top_funds_pie = fund_concentration.head(10).copy()
    
    # Check if we have the right columns and data
    if not top_funds_pie.empty and len(top_funds_pie.columns) >= 2:
        # Use the actual column names from the dataframe
        fund_name_col = top_funds_pie.columns[0]  # Fund Name
        portfolio_value_col = top_funds_pie.columns[1]  # Portfolio Value
        
        # Filter out rows with missing portfolio values
        top_funds_pie = top_funds_pie.dropna(subset=[portfolio_value_col])
        
        if not top_funds_pie.empty:
            # Convert portfolio values back to numeric for plotting
            try:
                # Extract numeric values from formatted strings like "$5531119.7M"
                numeric_values = []
                for val in fund_concentration.head(10)[portfolio_value_col]:
                    if pd.notna(val) and isinstance(val, (int, float)):
                        numeric_values.append(val)
                    else:
                        numeric_values.append(0)
                
                top_funds_pie['numeric_value'] = numeric_values[:len(top_funds_pie)]
                
                # Only create pie chart if we have valid data
                if top_funds_pie['numeric_value'].sum() > 0:
                    fig_pie = px.pie(
                        top_funds_pie,
                        values='numeric_value',
                        names=fund_name_col,
                        title="Top 10 Funds by Portfolio Value"
                    )
                    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                    fig_pie.update_layout(height=500)
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("Portfolio value data not available for pie chart visualization.")
            except Exception as e:
                st.warning(f"Could not create pie chart: {str(e)}")
        else:
            st.info("No valid portfolio data available for pie chart.")
    else:
        st.info("Insufficient data for market share visualization.")
    
    # Market statistics
    st.subheader("📈 Market Statistics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Security Distribution:**")
        # Count securities by type
        security_types = processor.infotable_df['TITLEOFCLASS'].value_counts().head(10)
        st.bar_chart(security_types)
    
    with col2:
        st.write("**Value Distribution:**")
        # Show value distribution statistics
        value_stats = processor.infotable_df['VALUE'].describe()
        st.write(f"- Mean Position: ${value_stats['mean']/1e6:.1f}M")
        st.write(f"- Median Position: ${value_stats['50%']/1e6:.1f}M")
        st.write(f"- Max Position: ${value_stats['max']/1e9:.1f}B")
        st.write(f"- Total Positions: {len(processor.infotable_df):,}")

if __name__ == "__main__":
    main()

