"""
SEC 13F Data Processing Utilities with Enhanced Search Capabilities
"""
import pandas as pd
import numpy as np
import os
import json
import glob
from typing import Dict, List, Tuple

# Import search utils with fallback
try:
    from .search_utils import HedgeFundSearchEngine
except ImportError:
    try:
        from utils.search_utils import HedgeFundSearchEngine
    except ImportError:
        from search_utils import HedgeFundSearchEngine

class SEC13FProcessor:
    """Process SEC 13F filing data with enhanced search capabilities"""
    
    def __init__(self, data_dir: str = 'data'):
        self.data_dir = data_dir
        self.infotable_df = None
        self.coverpage_df = None
        self.submission_df = None
        self.summarypage_df = None
        self.metadata = None
        self.search_engine = None
        
    def load_data(self):
        """Load all SEC 13F data files"""
        print("Loading SEC 13F data...")
        
        # Try to load main INFOTABLE file first
        infotable_path = os.path.join(self.data_dir, 'INFOTABLE.tsv')
        
        if os.path.exists(infotable_path):
            print("Loading from main INFOTABLE.tsv file...")
            self.infotable_df = pd.read_csv(infotable_path, sep='\t', low_memory=False)
        else:
            # Load from chunks
            print("Main INFOTABLE.tsv not found, loading from chunks...")
            self._load_from_chunks()
        
        # Load other data files
        self.coverpage_df = pd.read_csv(
            os.path.join(self.data_dir, 'COVERPAGE.tsv'), 
            sep='\t'
        )
        
        self.submission_df = pd.read_csv(
            os.path.join(self.data_dir, 'SUBMISSION.tsv'), 
            sep='\t'
        )
        
        self.summarypage_df = pd.read_csv(
            os.path.join(self.data_dir, 'SUMMARYPAGE.tsv'), 
            sep='\t'
        )
        
        # Load metadata
        metadata_path = os.path.join(self.data_dir, 'FORM13F_metadata.json')
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
        
        # Initialize search engine
        self.search_engine = HedgeFundSearchEngine(self.data_dir)
        
        print(f"Loaded {len(self.infotable_df):,} holdings records")
        print(f"Loaded {len(self.coverpage_df):,} fund records")
        
    def _load_from_chunks(self):
        """Load INFOTABLE from chunks"""
        chunks_dir = os.path.join(self.data_dir, 'chunks')
        
        if not os.path.exists(chunks_dir):
            raise FileNotFoundError(
                f"Neither INFOTABLE.tsv nor chunks directory found in {self.data_dir}!\n"
                "Please run 'python utils/reassemble_data.py' to create INFOTABLE.tsv from chunks."
            )
        
        # Find chunk files
        chunk_pattern = os.path.join(chunks_dir, 'INFOTABLE_chunk_*.tsv')
        chunk_files = sorted(glob.glob(chunk_pattern))
        
        if not chunk_files:
            raise FileNotFoundError(f"No chunk files found in {chunks_dir}")
        
        print(f"Loading from {len(chunk_files)} chunk files...")
        
        # Load and concatenate chunks
        dfs = []
        for chunk_file in chunk_files:
            print(f"  Loading {os.path.basename(chunk_file)}...")
            df = pd.read_csv(chunk_file, sep='\t', low_memory=False)
            dfs.append(df)
        
        self.infotable_df = pd.concat(dfs, ignore_index=True)
        print(f"Successfully loaded {len(self.infotable_df):,} records from chunks")
        
    def get_summary_stats(self) -> Dict:
        """Get summary statistics"""
        if self.infotable_df is None:
            self.load_data()
        
        # Merge with fund names
        holdings_with_funds = self.infotable_df.merge(
            self.coverpage_df[['ACCESSION_NUMBER', 'FILINGMANAGER_NAME']], 
            on='ACCESSION_NUMBER'
        )
        
        total_funds = self.coverpage_df['FILINGMANAGER_NAME'].nunique()
        total_holdings = len(self.infotable_df)
        total_aum = self.infotable_df['VALUE'].sum() / 1000  # Convert to billions
        unique_securities = self.infotable_df['NAMEOFISSUER'].nunique()
        
        return {
            'total_funds': total_funds,
            'total_holdings': total_holdings,
            'total_aum_billions': total_aum,
            'unique_securities': unique_securities
        }
    
    def get_top_funds(self, top_n: int = 20) -> pd.DataFrame:
        """Get top funds by AUM"""
        if self.infotable_df is None:
            self.load_data()
        
        # Calculate portfolio values by fund
        fund_portfolios = self.infotable_df.groupby('ACCESSION_NUMBER').agg({
            'VALUE': 'sum',
            'NAMEOFISSUER': 'count'
        }).reset_index()
        
        fund_portfolios.columns = ['ACCESSION_NUMBER', 'portfolio_value', 'total_positions']
        
        # Merge with fund names
        fund_portfolios = fund_portfolios.merge(
            self.coverpage_df[['ACCESSION_NUMBER', 'FILINGMANAGER_NAME']], 
            on='ACCESSION_NUMBER'
        )
        
        # Sort by portfolio value
        top_funds = fund_portfolios.sort_values('portfolio_value', ascending=False).head(top_n)
        
        return top_funds[['FILINGMANAGER_NAME', 'portfolio_value', 'total_positions']]
    
    def get_fund_holdings(self, fund_name: str, top_n: int = 50) -> pd.DataFrame:
        """Get holdings for a specific fund using enhanced search"""
        if self.search_engine is None:
            self.load_data()
        
        return self.search_engine.get_fund_holdings(fund_name, top_n)
    
    def search_securities(self, query: str) -> pd.DataFrame:
        """Search for securities by name using enhanced search"""
        if self.search_engine is None:
            self.load_data()
        
        return self.search_engine.get_security_holders(query)
    
    def search_funds(self, query: str, limit: int = 20) -> List[Dict]:
        """Search for funds by name"""
        if self.search_engine is None:
            self.load_data()
        
        return self.search_engine.search_funds(query, limit)
    
    def search_stocks(self, query: str, limit: int = 20) -> List[Dict]:
        """Search for stocks/securities by ticker or name"""
        if self.search_engine is None:
            self.load_data()
        
        return self.search_engine.search_securities(query, limit)
    
    def get_fund_statistics(self, fund_name: str) -> Dict:
        """Get comprehensive statistics for a fund"""
        if self.search_engine is None:
            self.load_data()
        
        return self.search_engine.get_fund_statistics(fund_name)
    
    def get_popular_securities(self, top_n: int = 50) -> pd.DataFrame:
        """Get most popular securities by number of funds holding them"""
        if self.infotable_df is None:
            self.load_data()
        
        # Count funds per security
        security_popularity = self.infotable_df.groupby('NAMEOFISSUER').agg({
            'ACCESSION_NUMBER': 'nunique',
            'VALUE': 'sum',
            'SSHPRNAMT': 'sum'
        }).reset_index()
        
        security_popularity.columns = ['Security', 'Fund_Count', 'Total_Value', 'Total_Shares']
        
        # Sort by fund count
        popular_securities = security_popularity.sort_values('Fund_Count', ascending=False).head(top_n)
        
        return popular_securities
    
    def export_processed_data(self, output_dir: str = 'data/processed'):
        """Export processed data to CSV files"""
        os.makedirs(output_dir, exist_ok=True)
        
        if self.infotable_df is None:
            self.load_data()
        
        # Export summary data
        summary_stats = self.get_summary_stats()
        with open(os.path.join(output_dir, 'summary_stats.json'), 'w') as f:
            json.dump(summary_stats, f, indent=2)
        
        # Export top funds
        top_funds = self.get_top_funds(100)
        top_funds.to_csv(os.path.join(output_dir, 'top_funds.csv'), index=False)
        
        # Export popular securities
        popular_securities = self.get_popular_securities(200)
        popular_securities.to_csv(os.path.join(output_dir, 'popular_securities.csv'), index=False)
        
        print(f"Processed data exported to {output_dir}")
    
    def setup_data_from_chunks(self):
        """Setup main INFOTABLE.tsv from chunks if needed"""
        infotable_path = os.path.join(self.data_dir, 'INFOTABLE.tsv')
        chunks_dir = os.path.join(self.data_dir, 'chunks')
        
        if not os.path.exists(infotable_path) and os.path.exists(chunks_dir):
            print("Setting up INFOTABLE.tsv from chunks...")
            try:
                from .reassemble_data import reassemble_infotable
            except ImportError:
                try:
                    from utils.reassemble_data import reassemble_infotable
                except ImportError:
                    from reassemble_data import reassemble_infotable
            reassemble_infotable(chunks_dir, infotable_path)
            print("INFOTABLE.tsv created successfully!")

# Legacy compatibility functions
def get_fund_summary(data_dir: str, fund_name: str = None) -> Dict:
    """Legacy function for backward compatibility"""
    processor = SEC13FProcessor(data_dir)
    if fund_name:
        return processor.get_fund_statistics(fund_name)
    else:
        return processor.get_summary_stats()

def get_top_holdings(data_dir: str, fund_name: str = None, top_n: int = 100) -> pd.DataFrame:
    """Legacy function for backward compatibility"""
    processor = SEC13FProcessor(data_dir)
    return processor.get_fund_holdings(fund_name, top_n)

def get_fund_list(data_dir: str) -> pd.DataFrame:
    """Legacy function for backward compatibility"""
    processor = SEC13FProcessor(data_dir)
    return processor.get_top_funds(100)

def create_heatmap_data(data_dir: str, fund_name: str = None) -> pd.DataFrame:
    """Legacy function for backward compatibility"""
    processor = SEC13FProcessor(data_dir)
    holdings = processor.get_fund_holdings(fund_name, 50)
    
    if holdings.empty:
        return pd.DataFrame()
    
    # Create heatmap data
    heatmap_data = holdings.copy()
    heatmap_data['symbol'] = heatmap_data['NAMEOFISSUER'].str.extract(r'([A-Z]{2,5})')
    heatmap_data['size'] = heatmap_data['portfolio_pct']
    
    return heatmap_data[['symbol', 'NAMEOFISSUER', 'VALUE', 'portfolio_pct', 'size']].head(30)

# Convenience functions for easy use
def quick_fund_search(query: str, data_dir: str = 'data') -> List[Dict]:
    """Quick search for hedge funds"""
    processor = SEC13FProcessor(data_dir)
    return processor.search_funds(query)

def quick_stock_search(query: str, data_dir: str = 'data') -> List[Dict]:
    """Quick search for stocks/securities"""
    processor = SEC13FProcessor(data_dir)
    return processor.search_stocks(query)

def quick_fund_analysis(fund_name: str, data_dir: str = 'data') -> Dict:
    """Quick fund analysis"""
    processor = SEC13FProcessor(data_dir)
    return processor.get_fund_statistics(fund_name)

if __name__ == "__main__":
    # Test the enhanced processor
    processor = SEC13FProcessor()
    
    # Get summary stats
    stats = processor.get_summary_stats()
    print("Summary Statistics:")
    print(f"  Total Funds: {stats['total_funds']:,}")
    print(f"  Total Holdings: {stats['total_holdings']:,}")
    print(f"  Total AUM: ${stats['total_aum_billions']:.1f}B")
    print(f"  Unique Securities: {stats['unique_securities']:,}")
    
    # Test fund search
    print("\nTesting fund search for 'vanguard':")
    funds = processor.search_funds('vanguard', limit=5)
    for fund in funds:
        print(f"  {fund['name']}")
    
    # Test stock search
    print("\nTesting stock search for 'apple':")
    stocks = processor.search_stocks('apple', limit=5)
    for stock in stocks:
        print(f"  {stock['name']}")
    
    # Test fund analysis
    print("\nTesting fund analysis for 'vanguard':")
    analysis = processor.get_fund_statistics('vanguard')
    if 'error' not in analysis:
        print(f"  Portfolio Value: ${analysis['total_portfolio_value']:,.0f}")
        print(f"  Total Positions: {analysis['total_positions']:,}")
        print(f"  Top Holding: {analysis['top_holding']}")
    
    # Export processed data
    processor.export_processed_data()

