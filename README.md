# Hedge Fund Index MVP

A comprehensive hedge fund analysis platform built with Streamlit, providing insights into institutional investment patterns through SEC 13F filings data.

## Overview

The Hedge Fund Index MVP is a proof-of-concept application that processes and visualizes SEC 13F filings to provide comprehensive analysis of hedge fund and institutional investor portfolios. The application offers interactive dashboards, portfolio heatmaps, holdings analysis, and market insights based on real SEC filing data.

## Features

### 🏠 Overview Dashboard
- **Key Metrics**: Total funds, holdings, AUM, and unique securities
- **Top Funds Ranking**: Ranked list of funds by assets under management
- **Real-time Data**: Based on latest SEC 13F filings

### 📈 Fund Analysis
- **Portfolio Metrics**: Detailed fund-specific statistics
- **Interactive Treemap**: Advanced hierarchical visualization with real-time price data
- **Sector Analysis**: Portfolio breakdown by industry with performance metrics
- **Top Holdings Tables**: Comprehensive holdings breakdown with values and percentages
- **Fund Selection**: Dropdown to analyze any fund in the dataset

### 🔍 Holdings Explorer
- **Advanced Search**: Intelligent search for securities by ticker, company name, or partial matches
- **Cross-Fund Analysis**: See which funds hold specific securities with position sizes
- **Fuzzy Matching**: Find securities even with partial or approximate names
- **Fund Holdings**: Complete list of funds holding searched securities with values

### 📊 Market Insights
- **Popular Securities**: Most widely held securities across all funds
- **Market Concentration**: Analysis of institutional ownership patterns
- **Interactive Visualizations**: Bar charts and data tables

### ⚙️ Data Processing
- **Dataset Information**: Comprehensive data quality metrics
- **Sample Data Preview**: Raw data inspection capabilities
- **Export Functionality**: CSV export for processed data

## Technology Stack

- **Frontend**: Streamlit
- **Data Processing**: Pandas, NumPy
- **Visualizations**: Plotly, Seaborn
- **Market Data**: Yahoo Finance API (yfinance)
- **Data Source**: SEC 13F filings (TSV format)
- **Environment**: Python 3.11+

## Installation

### Prerequisites
- Python 3.11 or higher
- pip package manager
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/kaljuvee/hedge-fund-index.git
   cd hedge-fund-index
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Create .env file (do not commit to repository)
   echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
   ```

4. **Prepare data**
   ```bash
   # Run the automated setup script
   python setup_data.py
   ```
   
   This script will:
   - Reassemble the large INFOTABLE.tsv from 4 smaller chunks
   - Verify all required data files are present
   - Test data loading functionality
   
   **Manual setup (alternative):**
   ```bash
   # If you prefer manual setup
   python utils/reassemble_data.py
   ```

5. **Run the application**
   ```bash
   streamlit run Home.py
   ```

6. **Access the application**
   - Open your browser to `http://localhost:8501`

## Data Structure

The application processes SEC 13F filing data with the following key components:

### Data Chunking Approach
Due to GitHub's 100MB file size limit, the large INFOTABLE.tsv file (338MB) is split into 4 smaller chunks:
- `INFOTABLE_chunk_1.tsv` (~85MB)
- `INFOTABLE_chunk_2.tsv` (~85MB) 
- `INFOTABLE_chunk_3.tsv` (~84MB)
- `INFOTABLE_chunk_4.tsv` (~84MB)

The setup script automatically reassembles these chunks into the full dataset.

### Enhanced Search Engine
The application includes an advanced search engine with:
- **Indexed Lookups**: Pre-built indexes for fast fund and security searches
- **Fuzzy Matching**: Intelligent partial matching for fund names and tickers
- **Multi-key Search**: Search by company name, ticker symbol, or CUSIP
- **Performance Optimization**: Efficient data structures for large dataset queries

### INFOTABLE.tsv
Contains detailed holdings information:
- `NAMEOFISSUER`: Security name
- `VALUE`: Market value of holdings
- `SSHPRNAMT`: Number of shares or principal amount
- `CUSIP`: Security identifier
- `PUTCALL`: Options type (if applicable)

### COVERPAGE.tsv
Contains fund information:
- `FILINGMANAGER_NAME`: Fund/manager name
- `ACCESSION_NUMBER`: Unique filing identifier
- `REPORTCALENDARORQUARTER`: Reporting period

### SUMMARYPAGE.tsv
Contains portfolio summaries:
- `TABLEVALUETOTAL`: Total portfolio value
- `TABLEENTRYTOTAL`: Number of holdings

## Advanced Features

### 🗺️ Interactive Treemap Visualization

The Fund Analysis page features an advanced treemap visualization that provides:

#### **Hierarchical Organization**
- **Sector Grouping**: Stocks are organized by industry sector (Technology, Healthcare, Financial, etc.)
- **Company Level**: Within each sector, individual companies are displayed
- **Size Representation**: Box size represents portfolio allocation percentage

#### **Real-Time Performance Data**
- **Price Changes**: 1-month price performance from Yahoo Finance
- **Color Coding**: 
  - 🔴 **Red**: Stocks that declined in the past month
  - 🟡 **Yellow**: Neutral performance (near 0% change)
  - 🟢 **Green**: Stocks that gained value
- **Dynamic Updates**: Live data fetching for current market conditions

#### **Interactive Features**
- **Hover Information**: Detailed data on each position including:
  - Company name and ticker
  - Portfolio percentage
  - Position value
  - Number of shares
  - 1-month price change
- **Zoom and Pan**: Navigate through large portfolios
- **Sector Drill-Down**: Click on sectors to explore individual holdings

#### **Sector Analysis Dashboard**
- **Sector Distribution**: Table showing allocation by industry
- **Performance Summary**: Average price changes per sector
- **Risk Metrics**: Concentration analysis and diversification insights

### 📊 Data Integration

The treemap integrates multiple data sources:
- **SEC 13F Filings**: Portfolio holdings and values
- **Yahoo Finance**: Real-time price data and sector information
- **Ticker Mapping**: Automatic company name to ticker symbol conversion

## Usage Examples

### Analyzing a Specific Fund
1. Navigate to the "Fund Analysis" page
2. Select a fund from the dropdown (e.g., "VANGUARD GROUP INC")
3. View portfolio metrics, sector analysis, and interactive treemap
4. Hover over treemap boxes to see detailed position information
5. Analyze sector concentration and recent performance

### Searching for Securities
1. Go to "Holdings Explorer"
2. Enter a security name (e.g., "NVIDIA")
3. View aggregated holdings and fund ownership

### Market Analysis
1. Visit "Market Insights"
2. Explore most popular securities
3. Analyze institutional ownership patterns

## Sample Output

The application provides analysis similar to professional financial platforms, including:

- **Portfolio Value**: $5.53B (example: Vanguard Group Inc)
- **Total Positions**: 16,744 holdings
- **Top Holdings**: Apple Inc, Microsoft Corp, NVIDIA Corporation
- **Interactive Treemap**: Hierarchical visualization with real-time performance data
- **Sector Analysis**: Technology (45%), Healthcare (20%), Financial (15%), etc.
- **Performance Metrics**: Average 1-month change: +3.2%, 65% positive movers
- **Cross-Fund Analysis**: Which institutions hold specific securities

### 🎯 Treemap Interpretation Guide

#### **Visual Elements**
- **Box Size**: Larger boxes = higher portfolio allocation (higher concentration risk)
- **Color Intensity**: Deeper red/green = larger price movements
- **Sector Grouping**: Related companies clustered together

#### **Risk Analysis**
- **Concentration Risk**: Large boxes indicate over-concentration
- **Sector Risk**: Heavy sector weighting may indicate sector-specific bets
- **Performance Risk**: Red clusters show underperforming sectors

#### **Investment Insights**
- **Sector Trends**: Green sectors may indicate fund's growth focus
- **Diversification**: Well-distributed colors suggest balanced approach
- **Active Management**: Mixed performance suggests active stock selection

## Data Sources

- **Primary**: SEC 13F filings from EDGAR database
- **Format**: Tab-separated values (TSV)
- **Update Frequency**: Quarterly (as per SEC requirements)
- **Coverage**: All institutional investment managers with >$100M AUM

## Architecture

```
hedge-fund-index/
├── Home.py                # Main Streamlit application
├── utils/
│   └── data_processor.py  # SEC 13F data processing utilities
├── data/
│   ├── chunks/           # Data chunks (under 100MB each)
│   └── processed/        # Processed CSV exports
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables (not committed)
└── README.md             # This documentation
```

## Performance Considerations

- **Data Size**: Handles 3.4M+ holdings records efficiently
- **Memory Usage**: Optimized pandas operations for large datasets
- **Caching**: Streamlit session state for data persistence
- **Loading Time**: Initial data load ~10-15 seconds

## Future Enhancements

### Planned Features
- **13D/G Filings Integration**: Activist investor tracking
- **Historical Analysis**: Time-series portfolio changes
- **AI-Powered Insights**: OpenAI/LangChain document processing
- **Advanced Visualizations**: Additional chart types and filters
- **Export Capabilities**: PDF reports and Excel exports

### Technical Improvements
- **Database Integration**: Replace CSV with PostgreSQL/MongoDB
- **API Development**: REST API for programmatic access
- **Real-time Updates**: Automated SEC filing ingestion
- **Performance Optimization**: Distributed computing for large datasets
