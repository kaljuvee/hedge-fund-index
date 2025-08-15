#!/usr/bin/env python3
"""
Main Streamlit application entry point for Streamlit Cloud deployment
"""

import streamlit as st
import os
import sys

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set page config
st.set_page_config(
    page_title="Hedge Fund Index",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Import and run the main application
if __name__ == "__main__":
    # Import the main app
    from Home import main
    
    # Run the main function
    main()
