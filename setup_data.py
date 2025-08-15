#!/usr/bin/env python3
"""
Setup script for Hedge Fund Index data preparation
This script reassembles the INFOTABLE.tsv from chunks and prepares the data for use.
"""
import os
import sys
import subprocess

def check_requirements():
    """Check if required packages are installed"""
    try:
        import pandas
        import numpy
        print("✓ Required packages are installed")
        return True
    except ImportError as e:
        print(f"✗ Missing required package: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def setup_data():
    """Setup data from chunks"""
    print("🔧 Setting up Hedge Fund Index data...")
    
    # Check if chunks exist
    chunks_dir = 'data/chunks'
    if not os.path.exists(chunks_dir):
        print(f"✗ Chunks directory not found: {chunks_dir}")
        print("Please ensure the repository was cloned correctly.")
        return False
    
    # Check if INFOTABLE.tsv already exists
    infotable_path = 'data/INFOTABLE.tsv'
    if os.path.exists(infotable_path):
        print("✓ INFOTABLE.tsv already exists")
        return True
    
    # Reassemble from chunks
    print("📦 Reassembling INFOTABLE.tsv from chunks...")
    try:
        from utils.reassemble_data import reassemble_infotable
        reassemble_infotable(chunks_dir, infotable_path)
        print("✓ INFOTABLE.tsv created successfully!")
        return True
    except Exception as e:
        print(f"✗ Error reassembling data: {e}")
        return False

def verify_data():
    """Verify that all required data files are present"""
    print("🔍 Verifying data files...")
    
    required_files = [
        'data/INFOTABLE.tsv',
        'data/COVERPAGE.tsv',
        'data/SUBMISSION.tsv',
        'data/SUMMARYPAGE.tsv',
        'data/FORM13F_metadata.json'
    ]
    
    all_present = True
    for file_path in required_files:
        if os.path.exists(file_path):
            size_mb = os.path.getsize(file_path) / (1024 * 1024)
            print(f"✓ {file_path} ({size_mb:.1f} MB)")
        else:
            print(f"✗ {file_path} - Missing!")
            all_present = False
    
    return all_present

def test_data_loading():
    """Test that data can be loaded successfully"""
    print("🧪 Testing data loading...")
    
    try:
        from utils.data_processor import SEC13FProcessor
        
        processor = SEC13FProcessor()
        stats = processor.get_summary_stats()
        
        print(f"✓ Data loaded successfully!")
        print(f"  📊 Total Funds: {stats['total_funds']:,}")
        print(f"  📈 Total Holdings: {stats['total_holdings']:,}")
        print(f"  💰 Total AUM: ${stats['total_aum_billions']:.1f}B")
        print(f"  🏢 Unique Securities: {stats['unique_securities']:,}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error loading data: {e}")
        return False

def main():
    """Main setup function"""
    print("🚀 Hedge Fund Index Data Setup")
    print("=" * 40)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Setup data
    if not setup_data():
        sys.exit(1)
    
    # Verify data
    if not verify_data():
        sys.exit(1)
    
    # Test data loading
    if not test_data_loading():
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("\nYou can now run the application with:")
    print("  streamlit run app.py")
    print("\nOr test the search functionality:")
    print("  python -c \"from utils.data_processor import quick_fund_search; print(quick_fund_search('vanguard'))\"")

if __name__ == "__main__":
    main()

