"""
SEC 13F Data Processing Utilities
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import os

class SEC13FProcessor:
    """Process SEC 13F data for hedge fund analysis"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.infotable_df = None
        self.coverpage_df = None
        self.submission_df = None
        self.summarypage_df = None
        
    def load_data(self):
        """Load all SEC 13F data files"""
        try:
            # Load main data files
            self.infotable_df = pd.read_csv(
                os.path.join(self.data_dir, 'INFOTABLE.tsv'), 
                sep='\t', 
                low_memory=False
            )
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
            
            print(f"Loaded {len(self.infotable_df)} holdings records")
            print(f"Loaded {len(self.coverpage_df)} fund records")
            
        except Exception as e:
            print(f"Error loading data: {e}")
            
    def get_fund_summary(self, fund_name: str = None) -> Dict:
        """Get summary statistics for a specific fund or all funds"""
        if fund_name:
            # Filter for specific fund
            fund_data = self.coverpage_df[
                self.coverpage_df['FILINGMANAGER_NAME'].str.contains(fund_name, case=False, na=False)
            ]
            if fund_data.empty:
                return {"error": f"Fund '{fund_name}' not found"}
                
            accession_numbers = fund_data['ACCESSION_NUMBER'].tolist()
            holdings = self.infotable_df[
                self.infotable_df['ACCESSION_NUMBER'].isin(accession_numbers)
            ]
        else:
            holdings = self.infotable_df
            
        # Calculate summary statistics
        total_value = holdings['VALUE'].sum()
        total_positions = len(holdings)
        unique_securities = holdings['NAMEOFISSUER'].nunique()
        
        return {
            'total_portfolio_value': total_value,
            'total_positions': total_positions,
            'unique_securities': unique_securities,
            'holdings_data': holdings
        }
        
    def get_top_holdings(self, fund_name: str = None, top_n: int = 100) -> pd.DataFrame:
        """Get top holdings for a fund"""
        summary = self.get_fund_summary(fund_name)
        if 'error' in summary:
            return pd.DataFrame()
            
        holdings = summary['holdings_data']
        
        # Group by security and sum values
        top_holdings = holdings.groupby(['NAMEOFISSUER', 'TITLEOFCLASS']).agg({
            'VALUE': 'sum',
            'SSHPRNAMT': 'sum',
            'PUTCALL': 'first',
            'CUSIP': 'first'
        }).reset_index()
        
        # Calculate portfolio percentage
        total_value = summary['total_portfolio_value']
        top_holdings['portfolio_pct'] = (top_holdings['VALUE'] / total_value) * 100
        
        # Sort by value and get top N
        top_holdings = top_holdings.sort_values('VALUE', ascending=False).head(top_n)
        
        return top_holdings
        
    def get_fund_list(self) -> pd.DataFrame:
        """Get list of all funds in the dataset"""
        funds = self.coverpage_df[['FILINGMANAGER_NAME', 'ACCESSION_NUMBER']].copy()
        
        # Add portfolio values from summary page
        funds = funds.merge(
            self.summarypage_df[['ACCESSION_NUMBER', 'TABLEVALUETOTAL', 'TABLEENTRYTOTAL']], 
            on='ACCESSION_NUMBER', 
            how='left'
        )
        
        # Sort by portfolio value
        funds = funds.sort_values('TABLEVALUETOTAL', ascending=False, na_position='last')
        
        return funds
        
    def create_heatmap_data(self, fund_name: str = None) -> pd.DataFrame:
        """Create data for portfolio heatmap visualization"""
        top_holdings = self.get_top_holdings(fund_name, top_n=50)
        
        if top_holdings.empty:
            return pd.DataFrame()
            
        # Create heatmap data with security symbols (simplified)
        heatmap_data = top_holdings.copy()
        heatmap_data['symbol'] = heatmap_data['NAMEOFISSUER'].str.extract(r'([A-Z]{2,5})')
        heatmap_data['size'] = heatmap_data['portfolio_pct']
        
        return heatmap_data[['symbol', 'NAMEOFISSUER', 'VALUE', 'portfolio_pct', 'size']].head(30)
        
    def export_to_csv(self, output_dir: str):
        """Export processed data to CSV files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Export fund list
        funds = self.get_fund_list()
        funds.to_csv(os.path.join(output_dir, 'fund_list.csv'), index=False)
        
        # Export top 10 funds' holdings
        top_funds = funds.head(10)
        
        for _, fund in top_funds.iterrows():
            fund_name = fund['FILINGMANAGER_NAME']
            safe_name = "".join(c for c in fund_name if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
            
            holdings = self.get_top_holdings(fund_name, top_n=100)
            if not holdings.empty:
                holdings.to_csv(
                    os.path.join(output_dir, f'{safe_name}_holdings.csv'), 
                    index=False
                )
                
        print(f"Data exported to {output_dir}")

if __name__ == "__main__":
    # Test the processor
    processor = SEC13FProcessor('/home/ubuntu/hedge-fund-index/data')
    processor.load_data()
    
    # Test with Laurion Capital Management
    summary = processor.get_fund_summary('Laurion Capital Management')
    print(f"Laurion Capital Summary: {summary}")
    
    # Export processed data
    processor.export_to_csv('/home/ubuntu/hedge-fund-index/data/processed')

