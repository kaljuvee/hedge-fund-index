#!/usr/bin/env python3
"""
Test script for treemap functionality
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

def test_simple_treemap():
    """Test basic treemap functionality"""
    
    # Create simple test data
    test_data = pd.DataFrame({
        'sector': ['Technology', 'Technology', 'Healthcare', 'Healthcare', 'Financial'],
        'company': ['Apple', 'Microsoft', 'Johnson & Johnson', 'Pfizer', 'JPMorgan'],
        'value': [100, 80, 60, 40, 50],
        'price_change': [5.2, -2.1, 1.8, -0.5, 3.2],
        'ticker': ['AAPL', 'MSFT', 'JNJ', 'PFE', 'JPM']
    })
    
    # Create labels
    test_data['label'] = test_data.apply(
        lambda row: f"{row['company']}<br>{row['ticker']}<br>{row['value']:.1f}%", 
        axis=1
    )
    
    # Normalize price changes for color
    test_data['color_value'] = test_data['price_change'] / max(abs(test_data['price_change'].min()), abs(test_data['price_change'].max()))
    
    st.write("Test Data:")
    st.write(test_data)
    
    try:
        # Create treemap
        fig = px.treemap(
            test_data,
            path=['sector', 'label'],
            values='value',
            color='color_value',
            color_continuous_scale='RdYlGn',
            title='Test Treemap'
        )
        
        # Update layout
        fig.update_layout(
            height=500,
            coloraxis_showscale=True,
            coloraxis_colorbar=dict(
                title="Price Change %",
                thickness=15,
                len=0.5
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.success("Treemap created successfully!")
        
    except Exception as e:
        st.error(f"Error creating treemap: {str(e)}")
        st.write("Test data for debugging:")
        st.write(test_data.dtypes)
        st.write(test_data.isnull().sum())

if __name__ == "__main__":
    st.title("Treemap Test")
    test_simple_treemap()
