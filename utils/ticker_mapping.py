import pandas as pd
import os
from typing import Optional, Dict, Tuple
from datetime import datetime

class TickerMapping:
    """Manages company name to ticker mappings using a CSV file"""
    
    def __init__(self, csv_path: str = "data/company_ticker.csv"):
        self.csv_path = csv_path
        self.mapping = {}
        self.load_mapping()
    
    def load_mapping(self):
        """Load the ticker mapping from CSV file"""
        try:
            if os.path.exists(self.csv_path):
                df = pd.read_csv(self.csv_path)
                # Create a dictionary for fast lookups
                self.mapping = {}
                for _, row in df.iterrows():
                    company_name = str(row['company_name']).upper().strip()
                    self.mapping[company_name] = {
                        'ticker': row['ticker'],
                        'sector': row['sector'],
                        'source': row['source'],
                        'last_updated': row['last_updated']
                    }
                print(f"Loaded {len(self.mapping)} ticker mappings from {self.csv_path}")
            else:
                print(f"Ticker mapping file not found: {self.csv_path}")
                self.mapping = {}
        except Exception as e:
            print(f"Error loading ticker mapping: {e}")
            self.mapping = {}
    
    def get_ticker(self, company_name: str) -> Optional[str]:
        """Get ticker for a company name"""
        clean_name = str(company_name).upper().strip()
        if clean_name in self.mapping:
            return self.mapping[clean_name]['ticker']
        return None
    
    def get_sector(self, company_name: str) -> Optional[str]:
        """Get sector for a company name"""
        clean_name = str(company_name).upper().strip()
        if clean_name in self.mapping:
            return self.mapping[clean_name]['sector']
        return None
    
    def get_info(self, company_name: str) -> Optional[Dict]:
        """Get all info for a company name"""
        clean_name = str(company_name).upper().strip()
        if clean_name in self.mapping:
            return self.mapping[clean_name].copy()
        return None
    
    def add_mapping(self, company_name: str, ticker: str, sector: str = "Unknown", source: str = "auto"):
        """Add a new mapping to the CSV file"""
        try:
            clean_name = str(company_name).upper().strip()
            
            # Load existing data first
            if os.path.exists(self.csv_path):
                df = pd.read_csv(self.csv_path)
            else:
                df = pd.DataFrame(columns=['company_name', 'ticker', 'sector', 'source', 'last_updated'])
            
            # Check if company already exists (case-insensitive)
            existing_mask = df['company_name'].str.upper().str.strip() == clean_name
            existing_idx = df[existing_mask].index
            
            if len(existing_idx) > 0:
                # Update existing entry - preserve existing data if new data is not better
                existing_row = df.loc[existing_idx[0]]
                existing_sector = existing_row['sector']
                existing_source = existing_row['source']
                
                # Only update if we have better information
                should_update = False
                new_sector = sector
                new_source = source
                
                # If existing sector is "Unknown" and new sector is not, update
                if existing_sector == "Unknown" and sector != "Unknown":
                    should_update = True
                # If existing source is "auto" and new source is more specific, update
                elif existing_source == "auto" and source in ["yfinance", "openai", "manual"]:
                    should_update = True
                # If we're getting sector info for the first time
                elif existing_sector == "Unknown" and sector != "Unknown":
                    should_update = True
                
                if should_update:
                    df.loc[existing_idx[0], 'ticker'] = ticker
                    df.loc[existing_idx[0], 'sector'] = new_sector
                    df.loc[existing_idx[0], 'source'] = new_source
                    df.loc[existing_idx[0], 'last_updated'] = datetime.now().strftime('%Y-%m-%d')
                    print(f"Updated mapping for {company_name} -> {ticker} (sector: {new_sector})")
                else:
                    print(f"Keeping existing mapping for {company_name} (already has {existing_sector} from {existing_source})")
            else:
                # Add new entry
                new_row = pd.DataFrame([{
                    'company_name': company_name,
                    'ticker': ticker,
                    'sector': sector,
                    'source': source,
                    'last_updated': datetime.now().strftime('%Y-%m-%d')
                }])
                df = pd.concat([df, new_row], ignore_index=True)
                print(f"Added new mapping: {company_name} -> {ticker} (sector: {sector})")
            
            # Update memory mapping
            self.mapping[clean_name] = {
                'ticker': ticker,
                'sector': sector,
                'source': source,
                'last_updated': datetime.now().strftime('%Y-%m-%d')
            }
            
            # Save to CSV
            os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)
            df.to_csv(self.csv_path, index=False)
            
        except Exception as e:
            print(f"Error adding mapping for {company_name}: {e}")
    
    def search_similar(self, company_name: str, threshold: float = 0.8) -> list:
        """Search for similar company names using fuzzy matching"""
        from difflib import SequenceMatcher
        
        clean_name = str(company_name).upper().strip()
        similar = []
        
        for mapped_name in self.mapping.keys():
            similarity = SequenceMatcher(None, clean_name, mapped_name).ratio()
            if similarity >= threshold:
                similar.append({
                    'company_name': mapped_name,
                    'similarity': similarity,
                    'info': self.mapping[mapped_name]
                })
        
        # Sort by similarity
        similar.sort(key=lambda x: x['similarity'], reverse=True)
        return similar
    
    def get_stats(self) -> Dict:
        """Get statistics about the mapping"""
        if not self.mapping:
            return {'total': 0, 'sectors': {}, 'sources': {}}
        
        sectors = {}
        sources = {}
        
        for info in self.mapping.values():
            sector = info['sector']
            source = info['source']
            
            sectors[sector] = sectors.get(sector, 0) + 1
            sources[source] = sources.get(source, 0) + 1
        
        return {
            'total': len(self.mapping),
            'sectors': sectors,
            'sources': sources
        }
    
    def bulk_add_mappings(self, mappings: list):
        """Add multiple mappings at once"""
        for mapping in mappings:
            if len(mapping) >= 2:
                company_name = mapping[0]
                ticker = mapping[1]
                sector = mapping[2] if len(mapping) > 2 else "Unknown"
                source = mapping[3] if len(mapping) > 3 else "bulk"
                self.add_mapping(company_name, ticker, sector, source)
    
    def get_missing_tickers(self, company_names: list) -> list:
        """Get list of company names that don't have ticker mappings"""
        missing = []
        for company in company_names:
            if not self.get_ticker(company):
                missing.append(company)
        return missing
    
    def get_missing_sectors(self, company_names: list) -> list:
        """Get list of company names that don't have sector mappings"""
        missing = []
        for company in company_names:
            sector = self.get_sector(company)
            if not sector or sector == "Unknown":
                missing.append(company)
        return missing

# Global instance
ticker_mapping = TickerMapping()
