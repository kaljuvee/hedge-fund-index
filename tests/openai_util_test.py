#!/usr/bin/env python3
"""
Test script for OpenAI sector classification functionality
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.openai_util import get_sector_from_openai, get_sector_with_fallback, get_ticker_from_openai, get_ticker_with_fallback

def test_openai_sector_classification():
    """Test OpenAI sector classification for various companies"""
    
    print("Testing OpenAI sector classification...")
    
    # Test companies that might not have clear sector info from Yahoo Finance
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
    
    print("\n1. Testing direct OpenAI sector classification:")
    for company, ticker in test_companies:
        try:
            sector = get_sector_from_openai(company, ticker)
            print(f"  {ticker} ({company}): {sector}")
        except Exception as e:
            print(f"  {ticker} ({company}): Error - {e}")
    
    print("\n2. Testing cached sector classification:")
    for company, ticker in test_companies:
        try:
            sector = get_sector_with_fallback(company, ticker, use_cache=True)
            print(f"  {ticker} ({company}): {sector}")
        except Exception as e:
            print(f"  {ticker} ({company}): Error - {e}")
    
    print("\n3. Testing ETF detection:")
    etf_companies = [
        ("ISHARES TR", "IEMG"),
        ("SPDR S&P 500 ETF TRUST", "SPY"),
        ("VANGUARD TOTAL STOCK MARKET ETF", "VTI"),
        ("INVESCO QQQ TRUST", "QQQ"),
    ]
    
    for company, ticker in etf_companies:
        try:
            sector = get_sector_from_openai(company, ticker)
            print(f"  {ticker} ({company}): {sector}")
        except Exception as e:
            print(f"  {ticker} ({company}): Error - {e}")

def test_openai_api_connection():
    """Test if OpenAI API is properly configured"""
    print("\n4. Testing OpenAI API connection:")
    
    try:
        import openai
        from dotenv import load_dotenv
        
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY')
        
        if api_key:
            print(f"  ✅ OpenAI API key found (length: {len(api_key)})")
            
            # Test a simple API call
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Say 'test'"}],
                max_tokens=5
            )
            print(f"  ✅ OpenAI API call successful: {response.choices[0].message.content}")
        else:
            print("  ❌ OpenAI API key not found in environment variables")
            
    except Exception as e:
        print(f"  ❌ OpenAI API test failed: {e}")

def test_openai_ticker_extraction():
    """Test OpenAI ticker extraction for various companies"""
    
    print("\n5. Testing OpenAI ticker extraction:")
    
    # Test companies that might not have clear ticker mappings
    test_companies = [
        "HESS CORP",
        "ADVANCED MICRO DEVICES INC", 
        "BRIDGEBIO PHARMA INC",
        "MARVELL TECHNOLOGY INC",
        "DISCOVER FINL SVCS",
        "ANSYS INC",
        "SHELL PLC",
        "GOLDMAN SACHS GROUP INC",
        "UNITED STATES STL CORP NEW",
        "ALLSTATE CORP",
        "HCA HEALTHCARE INC",
        "ISHARES TR",  # ETF
        "SPDR S&P 500 ETF TRUST",  # ETF
    ]
    
    print("\nTesting direct OpenAI ticker extraction:")
    for company in test_companies:
        try:
            ticker = get_ticker_from_openai(company)
            print(f"  {company} -> {ticker}")
        except Exception as e:
            print(f"  {company} -> Error: {e}")
    
    print("\nTesting cached ticker extraction:")
    for company in test_companies:
        try:
            ticker = get_ticker_with_fallback(company, use_cache=True)
            print(f"  {company} -> {ticker}")
        except Exception as e:
            print(f"  {company} -> Error: {e}")

if __name__ == "__main__":
    test_openai_api_connection()
    test_openai_sector_classification()
    test_openai_ticker_extraction()
