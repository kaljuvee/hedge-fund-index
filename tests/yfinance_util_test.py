#!/usr/bin/env python3
"""
Test script for Yahoo Finance sector classification functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.yf_util import get_stock_sector, extract_ticker_from_cusip, get_stock_info_batch

def test_yfinance_sector_classification():
    """Test Yahoo Finance sector classification for various companies"""
    
    print("Testing Yahoo Finance sector classification...")
    
    # Test companies from the treemap that showed as "Unknown"
    test_companies = [
        ("ISHARES TR", "IEMG"),  # ETF
        ("HESS CORP", "HES"),    # Energy
        ("ADVANCED MICRO DEVICES INC", "AMD"),  # Technology
        ("BRIDGEBIO PHARMA INC", "BBIO"),  # Healthcare
        ("MARVELL TECHNOLOGY INC", "MRVL"),  # Technology
        ("DISCOVER FINL SVCS", "DFS"),  # Financial Services
        ("ANSYS INC", "ANSS"),  # Technology
        ("SHELL PLC", "SHEL"),  # Energy
        ("GOLDMAN SACHS GROUP INC", "GS"),  # Financial Services
        ("UNITED STATES STL CORP NEW", "X"),  # Basic Materials
        ("ALLSTATE CORP", "ALL"),  # Financial Services
        ("HCA HEALTHCARE INC", "HCA"),  # Healthcare
        ("TESLA INC", "TSLA"),  # Consumer Cyclical
        ("META PLATFORMS INC", "META"),  # Communication Services
        ("ALPHABET INC", "GOOGL"),  # Communication Services
        ("APPLE INC", "AAPL"),  # Technology
        ("CISCO SYS INC", "CSCO"),  # Technology
        ("JPMORGAN CHASE & CO.", "JPM"),  # Financial Services
    ]
    
    print("\n1. Testing ticker extraction:")
    for company, expected_ticker in test_companies:
        extracted_ticker = extract_ticker_from_cusip(company)
        status = "✅" if extracted_ticker == expected_ticker else "❌"
        print(f"  {status} {company} -> {extracted_ticker} (expected: {expected_ticker})")
        
        # If extraction failed, show what we got
        if extracted_ticker != expected_ticker:
            print(f"    Note: Got '{extracted_ticker}' instead of '{expected_ticker}'")
    
    print("\n2. Testing Yahoo Finance sector classification:")
    for company, ticker in test_companies:
        try:
            sector = get_stock_sector(ticker, company)
            print(f"  {ticker} ({company}): {sector}")
        except Exception as e:
            print(f"  {ticker} ({company}): Error - {e}")
    
    print("\n3. Testing batch processing:")
    try:
        # Test with a subset of companies
        test_subset = test_companies[:5]  # First 5 companies
        tickers = [ticker for _, ticker in test_subset]
        company_names = {ticker: company for company, ticker in test_subset}
        
        print(f"  Testing batch processing for {len(tickers)} companies...")
        results = get_stock_info_batch(tickers, company_names)
        
        for ticker, data in results.items():
            print(f"    {ticker}: sector={data['sector']}, price_change={data['price_change']}")
            
    except Exception as e:
        print(f"  Batch processing error: {e}")
    
    print("\n4. Testing ETF detection:")
    etf_companies = [
        ("ISHARES TR", "IEMG"),
        ("SPDR S&P 500 ETF TRUST", "SPY"),
        ("VANGUARD TOTAL STOCK MARKET ETF", "VTI"),
        ("INVESCO QQQ TRUST", "QQQ"),
        ("ISHARES CORE S&P 500 ETF", "IVV"),
    ]
    
    for company, ticker in etf_companies:
        try:
            sector = get_stock_sector(ticker, company)
            print(f"  {ticker} ({company}): {sector}")
        except Exception as e:
            print(f"  {ticker} ({company}): Error - {e}")

def test_yfinance_api_connection():
    """Test if Yahoo Finance API is working"""
    print("\n5. Testing Yahoo Finance API connection:")
    
    try:
        import yfinance as yf
        
        # Test with a well-known stock
        test_stock = yf.Ticker("AAPL")
        info = test_stock.info
        
        if info:
            print(f"  ✅ Yahoo Finance API working")
            print(f"  ✅ AAPL info retrieved: {info.get('longName', 'N/A')}")
            print(f"  ✅ AAPL sector: {info.get('sector', 'N/A')}")
        else:
            print("  ❌ Yahoo Finance API returned no data")
            
    except Exception as e:
        print(f"  ❌ Yahoo Finance API test failed: {e}")

def test_sector_fallback_mechanism():
    """Test the fallback mechanism when Yahoo Finance fails"""
    print("\n6. Testing sector fallback mechanism:")
    
    # Test with companies that might not have clear sector info
    problematic_companies = [
        ("ISHARES TR", "IEMG"),  # ETF
        ("UNITED STATES STL CORP NEW", "X"),  # Basic Materials
        ("DISCOVER FINL SVCS", "DFS"),  # Financial Services
    ]
    
    for company, ticker in problematic_companies:
        try:
            print(f"\n  Testing {ticker} ({company}):")
            
            # Test Yahoo Finance only
            yf_sector = get_stock_sector(ticker, company)
            print(f"    Yahoo Finance result: {yf_sector}")
            
            # Test with fallback (this would use OpenAI if available)
            # Note: This might fail if OpenAI API key is not set
            try:
                from utils.openai_util import get_sector_with_fallback
                fallback_sector = get_sector_with_fallback(company, ticker)
                print(f"    Fallback result: {fallback_sector}")
            except Exception as e:
                print(f"    Fallback failed: {e}")
                
        except Exception as e:
            print(f"    Error testing {ticker}: {e}")

if __name__ == "__main__":
    test_yfinance_api_connection()
    test_yfinance_sector_classification()
    test_sector_fallback_mechanism()
