"""
Search utilities for hedge fund and stock/ticker analysis
"""
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
import re
import os

class HedgeFundSearchEngine:
    """Advanced search engine for hedge fund data"""
    
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.infotable_df = None
        self.coverpage_df = None
        self.fund_lookup = {}
        self.ticker_lookup = {}
        self.loaded = False
        
    def load_data(self):
        """Load and index data for fast searching"""
        if self.loaded:
            return
            
        print("Loading and indexing data for search...")
        
        # Load coverpage data first (always needed)
        coverpage_path = os.path.join(self.data_dir, 'COVERPAGE.tsv')
        if os.path.exists(coverpage_path):
            self.coverpage_df = pd.read_csv(coverpage_path, sep='\t')
        else:
            raise FileNotFoundError(f"COVERPAGE.tsv not found in {self.data_dir}")
        
        # Load infotable data
        infotable_path = os.path.join(self.data_dir, 'INFOTABLE.tsv')
        if os.path.exists(infotable_path):
            self.infotable_df = pd.read_csv(infotable_path, sep='\t', low_memory=False)
        else:
            # Try to load from chunks if main file doesn't exist
            self._load_from_chunks()
        
        # Create search indexes
        self._build_fund_lookup()
        self._build_ticker_lookup()
        
        self.loaded = True
        print(f"Search engine ready! Indexed {len(self.fund_lookup)} funds and {len(self.ticker_lookup)} securities.")
    
    def _load_from_chunks(self):
        """Load INFOTABLE from chunks if main file doesn't exist"""
        chunks_dir = os.path.join(self.data_dir, 'chunks')
        if not os.path.exists(chunks_dir):
            raise FileNotFoundError("Neither INFOTABLE.tsv nor chunks directory found!")
        
        print("Loading from chunks...")
        chunk_files = sorted([f for f in os.listdir(chunks_dir) if f.startswith('INFOTABLE_chunk_')])
        
        dfs = []
        for chunk_file in chunk_files:
            chunk_path = os.path.join(chunks_dir, chunk_file)
            df = pd.read_csv(chunk_path, sep='\t', low_memory=False)
            dfs.append(df)
        
        self.infotable_df = pd.concat(dfs, ignore_index=True)
        print(f"Loaded {len(self.infotable_df)} records from {len(chunk_files)} chunks")
    
    def _build_fund_lookup(self):
        """Build lookup index for fund names"""
        self.fund_lookup = {}
        
        for _, row in self.coverpage_df.iterrows():
            fund_name = row['FILINGMANAGER_NAME']
            accession = row['ACCESSION_NUMBER']
            
            # Skip if fund_name is null or empty
            if pd.isna(fund_name) or not str(fund_name).strip():
                continue
                
            fund_name = str(fund_name).strip()
            
            # Create multiple search keys
            keys = [
                fund_name.lower(),
                fund_name.lower().replace(',', ''),
                fund_name.lower().replace('.', ''),
                fund_name.lower().replace(' ', ''),
            ]
            
            # Extract key words for partial matching
            words = re.findall(r'\b\w+\b', fund_name.lower())
            keys.extend(words)
            
            for key in keys:
                if key not in self.fund_lookup:
                    self.fund_lookup[key] = []
                self.fund_lookup[key].append({
                    'name': fund_name,
                    'accession': accession
                })
    
    def _build_ticker_lookup(self):
        """Build lookup index for tickers and security names"""
        self.ticker_lookup = {}
        
        # Sample data to build index (use first 100k records for performance)
        sample_df = self.infotable_df.head(100000)
        
        for _, row in sample_df.iterrows():
            security_name = row['NAMEOFISSUER']
            
            # Extract potential ticker symbols
            tickers = re.findall(r'\b[A-Z]{1,5}\b', security_name)
            
            # Create search keys
            keys = [security_name.lower()]
            keys.extend([t.lower() for t in tickers])
            
            # Add company name variations
            company_words = re.findall(r'\b\w+\b', security_name.lower())
            keys.extend(company_words)
            
            for key in keys:
                if key not in self.ticker_lookup:
                    self.ticker_lookup[key] = []
                if security_name not in [item['name'] for item in self.ticker_lookup[key]]:
                    self.ticker_lookup[key].append({
                        'name': security_name,
                        'cusip': row.get('CUSIP', ''),
                        'title_class': row.get('TITLEOFCLASS', '')
                    })
    
    def search_funds(self, query: str, limit: int = 20) -> List[Dict]:
        """Search for hedge funds by name"""
        if not self.loaded:
            self.load_data()
        
        query = query.lower().strip()
        results = []
        seen_names = set()
        
        # Direct matches
        if query in self.fund_lookup:
            for fund in self.fund_lookup[query]:
                if fund['name'] not in seen_names:
                    results.append(fund)
                    seen_names.add(fund['name'])
        
        # Partial matches
        for key, funds in self.fund_lookup.items():
            if query in key and len(results) < limit:
                for fund in funds:
                    if fund['name'] not in seen_names:
                        results.append(fund)
                        seen_names.add(fund['name'])
                        if len(results) >= limit:
                            break
        
        return results[:limit]
    
    def search_securities(self, query: str, limit: int = 20) -> List[Dict]:
        """Search for securities by ticker or company name"""
        if not self.loaded:
            self.load_data()
        
        query = query.lower().strip()
        results = []
        seen_names = set()
        
        # Direct matches
        if query in self.ticker_lookup:
            for security in self.ticker_lookup[query]:
                if security['name'] not in seen_names:
                    results.append(security)
                    seen_names.add(security['name'])
        
        # Partial matches
        for key, securities in self.ticker_lookup.items():
            if query in key and len(results) < limit:
                for security in securities:
                    if security['name'] not in seen_names:
                        results.append(security)
                        seen_names.add(security['name'])
                        if len(results) >= limit:
                            break
        
        return results[:limit]
    
    def get_fund_holdings(self, fund_name: str, top_n: int = 100) -> pd.DataFrame:
        """Get detailed holdings for a specific fund"""
        if not self.loaded:
            self.load_data()
        
        # Find fund accession numbers
        fund_matches = self.search_funds(fund_name, limit=5)
        if not fund_matches:
            return pd.DataFrame()
        
        accession_numbers = [match['accession'] for match in fund_matches]
        
        # Get holdings
        holdings = self.infotable_df[
            self.infotable_df['ACCESSION_NUMBER'].isin(accession_numbers)
        ].copy()
        
        if holdings.empty:
            return pd.DataFrame()
        
        # Aggregate by security
        aggregated = holdings.groupby(['NAMEOFISSUER', 'TITLEOFCLASS']).agg({
            'VALUE': 'sum',
            'SSHPRNAMT': 'sum',
            'CUSIP': 'first',
            'PUTCALL': 'first'
        }).reset_index()
        
        # Calculate portfolio percentage
        total_value = aggregated['VALUE'].sum()
        aggregated['portfolio_pct'] = (aggregated['VALUE'] / total_value) * 100
        
        # Sort by value
        aggregated = aggregated.sort_values('VALUE', ascending=False)
        
        return aggregated.head(top_n)
    
    def get_security_holders(self, security_name: str, top_n: int = 50) -> pd.DataFrame:
        """Get funds holding a specific security"""
        if not self.loaded:
            self.load_data()
        
        # Search for security
        security_matches = self.search_securities(security_name, limit=10)
        if not security_matches:
            return pd.DataFrame()
        
        security_names = [match['name'] for match in security_matches]
        
        # Get holdings
        holdings = self.infotable_df[
            self.infotable_df['NAMEOFISSUER'].isin(security_names)
        ].copy()
        
        if holdings.empty:
            return pd.DataFrame()
        
        # Get fund names
        holdings_with_funds = holdings.merge(
            self.coverpage_df[['ACCESSION_NUMBER', 'FILINGMANAGER_NAME']], 
            on='ACCESSION_NUMBER'
        )
        
        # Aggregate by fund
        fund_holdings = holdings_with_funds.groupby('FILINGMANAGER_NAME').agg({
            'VALUE': 'sum',
            'SSHPRNAMT': 'sum'
        }).reset_index()
        
        # Sort by position value
        fund_holdings = fund_holdings.sort_values('VALUE', ascending=False)
        
        return fund_holdings.head(top_n)
    
    def get_fund_statistics(self, fund_name: str) -> Dict:
        """Get comprehensive statistics for a fund"""
        holdings = self.get_fund_holdings(fund_name, top_n=1000)
        
        if holdings.empty:
            return {'error': f'Fund "{fund_name}" not found'}
        
        return {
            'total_portfolio_value': holdings['VALUE'].sum(),
            'total_positions': len(holdings),
            'unique_securities': holdings['NAMEOFISSUER'].nunique(),
            'top_holding': holdings.iloc[0]['NAMEOFISSUER'] if len(holdings) > 0 else None,
            'top_holding_value': holdings.iloc[0]['VALUE'] if len(holdings) > 0 else 0,
            'top_holding_pct': holdings.iloc[0]['portfolio_pct'] if len(holdings) > 0 else 0,
            'avg_position_size': holdings['VALUE'].mean(),
            'median_position_size': holdings['VALUE'].median()
        }

# Convenience functions for easy use
def search_hedge_funds(query: str, data_dir: str = 'data', limit: int = 20) -> List[Dict]:
    """Quick search for hedge funds"""
    engine = HedgeFundSearchEngine(data_dir)
    return engine.search_funds(query, limit)

def search_stocks(query: str, data_dir: str = 'data', limit: int = 20) -> List[Dict]:
    """Quick search for stocks/securities"""
    engine = HedgeFundSearchEngine(data_dir)
    return engine.search_securities(query, limit)

def analyze_fund(fund_name: str, data_dir: str = 'data') -> Dict:
    """Quick fund analysis"""
    engine = HedgeFundSearchEngine(data_dir)
    return engine.get_fund_statistics(fund_name)

def analyze_security(security_name: str, data_dir: str = 'data') -> pd.DataFrame:
    """Quick security holder analysis"""
    engine = HedgeFundSearchEngine(data_dir)
    return engine.get_security_holders(security_name)

if __name__ == "__main__":
    # Test the search engine
    engine = HedgeFundSearchEngine('data')
    
    print("Testing fund search:")
    funds = engine.search_funds('vanguard')
    for fund in funds[:5]:
        print(f"  {fund['name']}")
    
    print("\nTesting security search:")
    securities = engine.search_securities('apple')
    for security in securities[:5]:
        print(f"  {security['name']}")
    
    print("\nTesting fund analysis:")
    stats = engine.get_fund_statistics('vanguard')
    print(f"  Portfolio value: ${stats.get('total_portfolio_value', 0):,.0f}")
    print(f"  Total positions: {stats.get('total_positions', 0):,}")

