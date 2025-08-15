"""
Data Processing Page - Data Quality and Export Options
"""
import streamlit as st
import pandas as pd
import os
import sys
sys.path.append('utils')

try:
    from utils.data_processor import SEC13FProcessor
except ImportError:
    from data_processor import SEC13FProcessor

st.set_page_config(page_title="Data Processing", page_icon="⚙️", layout="wide")

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

def main():
    st.title("⚙️ Data Processing")
    
    # Documentation and Help Section
    with st.expander("📖 How to Use This Page", expanded=False):
        st.markdown("""
        ## 🎯 Purpose
        Monitor data quality, export datasets, and manage the SEC 13F filing data used throughout the application.
        
        ## 🔍 How to Use
        
        ### 1. **Data Overview** 📋
        - **Holdings Data**: Information about individual fund positions
        - **Fund Data**: Information about hedge fund managers
        - **Memory Usage**: How much space the data occupies
        
        ### 2. **Data Quality Checks** 🔍
        - **Missing Values**: Identifies incomplete data fields
        - **Data Completeness**: Percentage of missing data
        - **Key Fields**: Critical fields like company names, values, and shares
        
        ### 3. **Data Samples** 📊
        - **Holdings Sample**: See actual fund position data
        - **Fund Sample**: See fund manager information
        - **Field Definitions**: Understand what each column represents
        
        ### 4. **Export Options** 💾
        - **Holdings Export**: Download all fund positions as CSV
        - **Funds Export**: Download fund manager data as CSV
        - **Summary Report**: Download aggregated statistics
        
        ### 5. **File Information** 📁
        - **File Sizes**: How much space each data file uses
        - **File Types**: TSV, CSV, and JSON formats
        - **Data Sources**: Original SEC filing data
        
        ### 6. **Data Management** 🔄
        - **Refresh Data**: Reload data from source files
        - **Clear Cache**: Remove cached data to free memory
        
        ## 📊 Understanding the Data
        
        ### **Holdings Data (INFOTABLE.tsv):**
        - **NAMEOFISSUER**: Company name
        - **VALUE**: Position value in dollars
        - **SSHPRNAMT**: Number of shares held
        - **TITLEOFCLASS**: Type of security
        - **CUSIP**: Unique security identifier
        - **ACCESSION_NUMBER**: Links to fund information
        
        ### **Fund Data (COVERPAGE.tsv):**
        - **FILINGMANAGER_NAME**: Hedge fund name
        - **ACCESSION_NUMBER**: Unique filing identifier
        - **TABLEVALUETOTAL**: Total portfolio value
        - **TABLEENTRYTOTAL**: Total number of positions
        
        ## 💡 Data Quality Tips
        
        - **Low Missing Values** = High quality data
        - **Consistent Formats** = Reliable analysis
        - **Large File Sizes** = Comprehensive coverage
        - **Recent Data** = Current market conditions
        
        ## ⚠️ Important Notes
        
        - Data comes from SEC 13F quarterly filings
        - Filings are typically 45 days after quarter end
        - Large positions may be reported differently
        - Some funds may not file if below threshold
        - Data represents end-of-quarter snapshots
        
        ## 🔧 Troubleshooting
        
        **If data seems incomplete:**
        - Check file sizes in File Information
        - Look for missing values in Data Quality
        - Try refreshing data
        - Clear cache if memory issues occur
        """)
    
    # Load data
    
    # Load data
    processor = load_data()
    
    # Data overview
    st.subheader("📋 Data Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Holdings Data (INFOTABLE.tsv):**")
        st.write(f"- Records: {len(processor.infotable_df):,}")
        st.write(f"- Columns: {len(processor.infotable_df.columns)}")
        st.write(f"- Memory usage: {processor.infotable_df.memory_usage(deep=True).sum() / 1e6:.1f} MB")
    
    with col2:
        st.write("**Fund Data (COVERPAGE.tsv):**")
        st.write(f"- Records: {len(processor.coverpage_df):,}")
        st.write(f"- Columns: {len(processor.coverpage_df.columns)}")
    
    # Data quality checks
    st.subheader("🔍 Data Quality")
    
    # Missing values analysis
    st.write("**Missing Values in Key Fields:**")
    missing_values = processor.infotable_df[['NAMEOFISSUER', 'VALUE', 'SSHPRNAMT']].isnull().sum()
    missing_df = pd.DataFrame({
        'Field': missing_values.index,
        'Missing Count': missing_values.values,
        'Missing %': (missing_values.values / len(processor.infotable_df) * 100).round(2)
    })
    st.dataframe(missing_df, use_container_width=True)
    
    # Data samples
    st.subheader("📊 Data Samples")
    
    tab1, tab2 = st.tabs(["Holdings Sample", "Fund Sample"])
    
    with tab1:
        st.write("**Sample Holdings Data:**")
        st.dataframe(processor.infotable_df.head(10), use_container_width=True)
    
    with tab2:
        st.write("**Sample Fund Data:**")
        st.dataframe(processor.coverpage_df.head(10), use_container_width=True)
    
    # Export options
    st.subheader("💾 Export Options")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("Export Holdings to CSV"):
            try:
                output_path = "data/processed/holdings_export.csv"
                os.makedirs("data/processed", exist_ok=True)
                processor.infotable_df.to_csv(output_path, index=False)
                st.success(f"Holdings data exported to {output_path}")
            except Exception as e:
                st.error(f"Export failed: {str(e)}")
    
    with col2:
        if st.button("Export Funds to CSV"):
            try:
                output_path = "data/processed/funds_export.csv"
                os.makedirs("data/processed", exist_ok=True)
                processor.coverpage_df.to_csv(output_path, index=False)
                st.success(f"Fund data exported to {output_path}")
            except Exception as e:
                st.error(f"Export failed: {str(e)}")
    
    with col3:
        if st.button("Export Summary Report"):
            try:
                # Create summary report
                summary_data = {
                    'Metric': [
                        'Total Funds',
                        'Total Holdings',
                        'Total AUM',
                        'Unique Securities',
                        'Average Portfolio Value',
                        'Average Positions per Fund'
                    ],
                    'Value': [
                        len(processor.coverpage_df),
                        len(processor.infotable_df),
                        f"${processor.infotable_df['VALUE'].sum()/1e12:.2f}T",
                        processor.infotable_df['NAMEOFISSUER'].nunique(),
                        f"${processor.coverpage_df['TABLEVALUETOTAL'].mean()/1e9:.2f}B",
                        f"{processor.coverpage_df['TABLEENTRIESTOTAL'].mean():.0f}"
                    ]
                }
                
                summary_df = pd.DataFrame(summary_data)
                output_path = "data/processed/summary_report.csv"
                os.makedirs("data/processed", exist_ok=True)
                summary_df.to_csv(output_path, index=False)
                st.success(f"Summary report exported to {output_path}")
                st.dataframe(summary_df, use_container_width=True)
            except Exception as e:
                st.error(f"Export failed: {str(e)}")
    
    # File information
    st.subheader("📁 File Information")
    
    data_dir = "data"
    if os.path.exists(data_dir):
        files_info = []
        for file in os.listdir(data_dir):
            if file.endswith(('.tsv', '.csv', '.json')):
                file_path = os.path.join(data_dir, file)
                file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
                files_info.append({
                    'File': file,
                    'Size (MB)': f"{file_size:.1f}",
                    'Type': file.split('.')[-1].upper()
                })
        
        if files_info:
            files_df = pd.DataFrame(files_info)
            st.dataframe(files_df, use_container_width=True)
        else:
            st.info("No data files found in the data directory.")
    else:
        st.warning("Data directory not found.")
    
    # Data refresh
    st.subheader("🔄 Data Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Refresh Data"):
            # Clear session state to force reload
            if 'processor' in st.session_state:
                del st.session_state.processor
            if 'data_loaded' in st.session_state:
                del st.session_state.data_loaded
            st.experimental_rerun()
    
    with col2:
        if st.button("Clear Cache"):
            st.cache_data.clear()
            st.success("Cache cleared successfully!")

if __name__ == "__main__":
    main()

