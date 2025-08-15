#!/usr/bin/env python3
"""
Test script for CSV-based ticker mapping functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ticker_mapping import TickerMapping

def test_ticker_mapping():
    """Test the ticker mapping functionality"""
    
    print("Testing CSV-based ticker mapping...")
    
    # Create a test instance
    test_csv_path = "data/test_company_ticker.csv"
    mapping = TickerMapping(test_csv_path)
    
    # Test companies
    test_companies = [
        "APPLE INC",
        "MICROSOFT CORP",
        "HESS CORP",
        "ADVANCED MICRO DEVICES INC",
        "BRIDGEBIO PHARMA INC",
        "UNKNOWN COMPANY XYZ",
    ]
    
    print("\n1. Testing ticker lookup:")
    for company in test_companies:
        ticker = mapping.get_ticker(company)
        sector = mapping.get_sector(company)
        print(f"  {company} -> ticker: {ticker}, sector: {sector}")
    
    print("\n2. Testing adding new mappings:")
    # Add some test mappings
    mapping.add_mapping("TEST COMPANY A", "TESTA", "Technology", "test")
    mapping.add_mapping("TEST COMPANY B", "TESTB", "Healthcare", "test")
    
    print("\n3. Testing lookup after adding:")
    for company in ["TEST COMPANY A", "TEST COMPANY B"]:
        ticker = mapping.get_ticker(company)
        sector = mapping.get_sector(company)
        print(f"  {company} -> ticker: {ticker}, sector: {sector}")
    
    print("\n4. Testing similar company search:")
    similar = mapping.search_similar("APPLE", threshold=0.7)
    print(f"  Similar to 'APPLE': {len(similar)} matches")
    for match in similar[:3]:  # Show top 3
        print(f"    {match['company_name']} (similarity: {match['similarity']:.2f})")
    
    print("\n5. Testing statistics:")
    stats = mapping.get_stats()
    print(f"  Total mappings: {stats['total']}")
    print(f"  Sectors: {stats['sectors']}")
    print(f"  Sources: {stats['sources']}")
    
    # Clean up test file
    if os.path.exists(test_csv_path):
        os.remove(test_csv_path)
        print(f"\nCleaned up test file: {test_csv_path}")

def test_global_mapping():
    """Test the global ticker mapping instance"""
    
    print("\n6. Testing global ticker mapping instance:")
    
    try:
        from utils.yf_util import ticker_mapping
        
        # Test some lookups
        test_companies = [
            "APPLE INC",
            "HESS CORP",
            "ADVANCED MICRO DEVICES INC",
        ]
        
        for company in test_companies:
            ticker = ticker_mapping.get_ticker(company)
            sector = ticker_mapping.get_sector(company)
            print(f"  {company} -> ticker: {ticker}, sector: {sector}")
            
    except Exception as e:
        print(f"  Error testing global mapping: {e}")

if __name__ == "__main__":
    test_ticker_mapping()
    test_global_mapping()
