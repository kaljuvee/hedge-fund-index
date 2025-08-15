import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import sys
import os

# Add the parent directory to the path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from utils.data_processor import SEC13FProcessor
except ImportError:
    try:
        from data_processor import SEC13FProcessor
    except ImportError:
        st.error("Could not import SEC13FProcessor")

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
    """Create a treemap heatmap of portfolio holdings"""
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
        
        # Generate random colors for red-to-green spectrum
        np.random.seed(42)  # For consistent colors
        n_holdings = len(top_holdings)
        random_colors = np.random.uniform(0, 1, n_holdings)
        top_holdings['color_value'] = random_colors
        
        # Create labels with company name and percentage
        top_holdings['label'] = top_holdings.apply(
            lambda row: f"{row['NAMEOFISSUER']}<br>{row['portfolio_pct']:.1f}%", 
            axis=1
        )
        
        # Create treemap
        fig = px.treemap(
            top_holdings,
            values='portfolio_pct',
            names='label',
            title='Portfolio Holdings Heatmap (Top 20)',
            color='color_value',
            color_continuous_scale='RdYlGn',  # Red to Yellow to Green
            hover_data={
                'VALUE': ':,.0f',
                'portfolio_pct': ':.2f',
                'SSHPRNAMT': ':,.0f'
            }
        )
        
        # Update layout
        fig.update_layout(
            height=600,
            font_size=12,
            title_font_size=16,
            margin=dict(t=50, l=25, r=25, b=25),
            coloraxis_showscale=False  # Hide color scale since colors are random
        )
        
        # Update traces for better text display
        fig.update_traces(
            textfont_size=10,
            textposition="middle center",
            texttemplate="%{label}",
            hovertemplate="<b>%{label}</b><br>Value: $%{customdata[0]:,.0f}<br>Percentage: %{customdata[1]:.2f}%<br>Shares: %{customdata[2]:,.0f}<extra></extra>"
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Error creating heatmap: {str(e)}")
        return None

def main():
    st.title("📈 Fund Analysis")
    
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
                
                # Portfolio heatmap
                st.subheader("🗺️ Portfolio Heatmap")
                st.write("Portfolio Holdings Heatmap (Top 20)")
                
                heatmap_fig = create_heatmap(top_holdings)
                if heatmap_fig:
                    st.plotly_chart(heatmap_fig, use_container_width=True)
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

