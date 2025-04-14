

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import streamlit.components.v1 as components  # Import components for HTML embedding

# Set page config - set to wide layout by default
st.set_page_config(
    page_title="Comfort Inn Edgware Earth Day Dashboard", 
    page_icon="🌍", 
    layout="wide",
    initial_sidebar_state="collapsed"  # Start with sidebar collapsed
)

# Constants
ELECTRICITY_FACTOR = 0.20493  # CO2 emission factor for electricity
SELECTED_HOTEL = 'CIE'  # Fixed to CIV, no selection needed

# Comfort Inn Brand Colors
COMFORT_BLUE = "#003B71"
COMFORT_ORANGE = "#F37021"
COMFORT_YELLOW = "#FFC72C"
COMFORT_LIGHT_BLUE = "#E0F2FE"
COMFORT_LIGHT_GREEN = "#ECFDF5"

# Load and process data
def load_data():
    try:
        # Load the CSV file
        df = pd.read_csv('elec.csv')
        
        # Parse dates in DD/MM/YYYY format
        if 'Month' in df.columns:
            try:
                df['Date'] = pd.to_datetime(df['Month'], format='%d/%m/%Y', errors='coerce')
                
                # Extract components from dates
                df['Year'] = df['Date'].dt.year
                df['MonthNum'] = df['Date'].dt.month
                df['MonthName'] = df['Date'].dt.strftime('%b')
                
                # Sort by date
                df = df.sort_values('Date')
                
                # Aggregate by month (in case of duplicates)
                df = df.groupby(['Year', 'MonthNum', 'MonthName']).mean(numeric_only=True).reset_index()
                
                # Recreate Date column
                df['Date'] = pd.to_datetime(df['Year'].astype(str) + '-' + df['MonthNum'].astype(str) + '-01')
                df = df.sort_values('Date')
                
            except Exception as e:
                st.error(f"Error parsing dates: {str(e)}")
                return pd.DataFrame()
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame()

# Calculate comparison for Jan-March
def calculate_q1_comparison(df, hotel=SELECTED_HOTEL):
    try:
        # Get Jan-March months
        q1_months = [1, 2, 3]  # Jan, Feb, Mar
        
        # Get all years in the data
        years = sorted(df['Year'].unique())
        
        # Only proceed if we have at least 2 years
        if len(years) < 2:
            st.warning("Need at least 2 years of data for comparison.")
            return None
        
        current_year = years[-1]
        previous_year = years[-2]
        
        # Filter data by year and Jan-March months
        current_data = df[(df['Year'] == current_year) & (df['MonthNum'].isin(q1_months))]
        previous_data = df[(df['Year'] == previous_year) & (df['MonthNum'].isin(q1_months))]
        
        # Ensure we have data for both periods
        if len(current_data) == 0 or len(previous_data) == 0:
            st.warning("Missing data for one of the comparison periods.")
            return None
        
        # Calculate totals
        current_total = current_data[hotel].sum()
        previous_total = previous_data[hotel].sum()
        
        # Calculate percent change
        percent_change = ((current_total - previous_total) / previous_total) * 100
        
        # Calculate energy saved (if there's a reduction)
        energy_saved = previous_total - current_total if percent_change < 0 else 0
        
        # Calculate CO2 prevented
        co2_prevented = energy_saved * ELECTRICITY_FACTOR
        
        return {
            'current_year': current_year,
            'previous_year': previous_year,
            'current_total': current_total,
            'previous_total': previous_total,
            'percent_change': percent_change,
            'energy_saved': energy_saved,
            'co2_prevented': co2_prevented,
            'q1_months': q1_months,
            'months_compared': len(current_data)
        }
    except Exception as e:
        st.error(f"Error calculating comparison: {str(e)}")
        return None

# Create a simple Jan-March comparison chart
def create_q1_chart(df, comparison, hotel=SELECTED_HOTEL):
    try:
        if not comparison:
            return None
        
        # Get Jan-March months
        q1_months = [1, 2, 3]  # Jan, Feb, Mar
        
        # Get comparison years
        current_year = comparison['current_year']
        previous_year = comparison['previous_year']
        
        # Create data for chart
        chart_data = []
        
        # Get monthly data for both years
        for month in q1_months:
            # Current year
            current_month_data = df[(df['Year'] == current_year) & (df['MonthNum'] == month)]
            if len(current_month_data) > 0:
                month_name = current_month_data['MonthName'].iloc[0]
                chart_data.append({
                    'Month': month_name,
                    'Value': current_month_data[hotel].iloc[0],
                    'Year': str(current_year)
                })
            
            # Previous year
            previous_month_data = df[(df['Year'] == previous_year) & (df['MonthNum'] == month)]
            if len(previous_month_data) > 0:
                month_name = previous_month_data['MonthName'].iloc[0]
                chart_data.append({
                    'Month': month_name,
                    'Value': previous_month_data[hotel].iloc[0],
                    'Year': str(previous_year)
                })
        
        # Create dataframe
        chart_df = pd.DataFrame(chart_data)
        
        # Create chart with Comfort Inn colors
        fig = px.bar(
            chart_df, 
            x='Month', 
            y='Value', 
            color='Year',
            labels={'Value': 'Energy (kWh)', 'Month': 'Month'},
            barmode='group',
            text_auto='.2s',  # Use shortened number format
            color_discrete_sequence=[COMFORT_BLUE, COMFORT_ORANGE]  # Use Comfort Inn colors
        )
        
        # Update layout - FIXED xaxis property
        fig.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),  # Compact margins
            xaxis=dict(
                categoryorder='array',
                categoryarray=['Jan', 'Feb', 'Mar']
            ),
            yaxis=dict(
                title='Energy (kWh)',
                tickformat=','
            ),
            plot_bgcolor='rgba(255, 255, 255, 0.9)',
            paper_bgcolor='rgba(255, 255, 255, 0.9)',
            font=dict(family='Arial, sans-serif')
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating Jan-March chart: {str(e)}")
        return None

# Create trend chart with Jan-March highlighted
def create_trend_chart(df, hotel=SELECTED_HOTEL, highlight_q1=True):
    try:
        if len(df) == 0:
            return None
        
        # Create dataframe for the chart
        if highlight_q1:
            # Add a column to highlight Jan-March months
            df['Period'] = df.apply(
                lambda row: 'Jan - March' if row['MonthNum'] in [1, 2, 3] else 'Other Months', 
                axis=1
            )
            
            # Create chart with Jan-March highlighted with Comfort Inn colors
            fig = px.line(
                df,
                x='Date',
                y=hotel,
                color='Period',
                markers=True,
                labels={'Date': 'Month', hotel: 'Energy (kWh)'},
                color_discrete_map={
                    'Jan - March': COMFORT_ORANGE,  # Orange for Jan-March
                    'Other Months': COMFORT_BLUE    # Blue for other months
                }
            )
        else:
            # Regular chart without highlighting
            fig = px.line(
                df,
                x='Date',
                y=hotel,
                markers=True,
                labels={'Date': 'Month', hotel: 'Energy (kWh)'},
                line_color=COMFORT_BLUE
            )
        
        # Format chart
        fig.update_layout(
            title=f"Monthly Energy Usage Trend",
            xaxis=dict(
                tickformat='%b %Y',
                tickangle=-45
            ),
            yaxis=dict(
                title='Energy (kWh)',
                tickformat=','
            ),
            plot_bgcolor='rgba(255, 255, 255, 0.9)',
            paper_bgcolor='rgba(255, 255, 255, 0.9)',
            font=dict(family='Arial, sans-serif')
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating trend chart: {str(e)}")
        return None

# Main function
def main():
    # Load CSS with Comfort Inn branding
    st.markdown(f"""
    <style>
        /* Main container adjustments to prevent scrolling */
        .main .block-container {{
            padding-top: 0.5rem;
            padding-bottom: 0;
            padding-left: 1rem;
            padding-right: 1rem;
            max-width: 100%;
        }}
        
        /* Comfort Inn specific styling */
        .comfort-header {{
            background: linear-gradient(to right, {COMFORT_BLUE}, {COMFORT_BLUE}e0);
            padding: 0.7rem 1rem;
            border-radius: 0.5rem;
            color: white;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        .comfort-logo {{
            font-family: 'Arial', sans-serif;
            font-weight: 700;
            font-size: 1.5rem;
            color: white;
            display: flex;
            align-items: center;
        }}
        
        .comfort-logo-icon {{
            color: {COMFORT_YELLOW};
            margin-right: 0.5rem;
            font-size: 1.7rem;
        }}
        
        .comfort-tagline {{
            font-size: 0.9rem;
            opacity: 0.9;
            font-weight: 300;
        }}
        
        .champion-container {{
            background-color: {COMFORT_LIGHT_GREEN};
            border-radius: 0.5rem;
            padding: 0.8rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            display: flex;
            align-items: center;
            gap: 0.8rem;
            border: 1px solid #A7F3D0;
            margin-bottom: 1rem;
        }}
        
        .champion-info {{
            flex: 1;
        }}
        
        .champion-info h3 {{
            margin-top: 0;
            margin-bottom: 0.3rem;
            color: {COMFORT_BLUE};
            font-size: 1rem;
        }}
        
        .champion-info p {{
            margin: 0;
            line-height: 1.3;
            color: #333;
            font-size: 0.9rem;
        }}
        
        .champion-photo {{
            width: 60px;
            height: 60px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid {COMFORT_ORANGE};
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        /* Energy savings banner */
        .energy-savings-banner {{
            background-color: {COMFORT_LIGHT_BLUE};
            padding: 0.6rem;
            border-radius: 0.3rem;
            margin: 0.5rem 0 0.5rem 0;
            display: flex;
            flex-wrap: wrap;
            gap: 0.5rem;
            justify-content: space-between;
            border: 1px solid {COMFORT_BLUE}40;
        }}
        
        .energy-reminder {{
            background-color: white;
            padding: 0.5rem 0.8rem;
            border-radius: 0.3rem;
            margin: 0;
            flex: 1 1 auto;
            min-width: 150px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
            text-align: center;
            border-left: 3px solid {COMFORT_BLUE};
        }}
        
        .energy-reminder p {{
            margin: 0;
            color: #333;
            font-size: 0.85rem;
            white-space: nowrap;
        }}
        
        /* Custom metric styles */
        .metric-card {{
            background-color: white;
            border-radius: 0.5rem;
            padding: 0.7rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border-top: 3px solid {COMFORT_ORANGE};
            text-align: center;
            height: 100%;
        }}
        
        .metric-value {{
            font-size: 1.6rem;
            font-weight: 700;
            color: {COMFORT_BLUE};
            margin: 0.3rem 0;
        }}
        
        .metric-label {{
            font-size: 0.85rem;
            color: #555;
            margin-bottom: 0.3rem;
        }}
        
        .metric-delta {{
            font-size: 0.8rem;
            padding: 0.15rem 0.4rem;
            border-radius: 1rem;
            display: inline-block;
        }}
        
        .metric-delta.positive {{
            background-color: #ECFDF5;
            color: #065F46;
        }}
        
        .metric-delta.negative {{
            background-color: #FEF2F2;
            color: #991B1B;
        }}
        
        /* Section headings */
        h3 {{
            color: {COMFORT_BLUE};
            margin-top: 0.7rem;
            margin-bottom: 0.5rem;
            font-size: 1.1rem;
        }}
        
        /* Footer */
        .footer {{
            text-align: center;
            padding: 0.5rem;
            color: #666;
            font-size: 0.75rem;
            margin-top: 0.5rem;
        }}
        
        /* Make all cards the same height */
        .equal-height {{
            display: flex;
            flex-direction: column;
            height: 100%;
        }}
        
        /* Reduce padding for plotly charts */
        .js-plotly-plot {{
            padding: 0 !important;
        }}
        
        .js-plotly-plot .plotly {{
            min-height: 0 !important;
        }}
        
        /* Hide fullscreen button on plotly charts */
        .modebar-btn[data-title="Toggle Fullscreen"] {{
            display: none !important;
        }}
        
        /* Compress whitespace in general */
        .block-container > div:first-child {{
            margin-bottom: 0 !important;
            padding-bottom: 0 !important;
        }}
        
        /* Hide element overflows */
        .element-container {{
            overflow: hidden;
        }}
    </style>
    """, unsafe_allow_html=True)
    
    # Custom Comfort Inn Header with logo
    st.markdown(f"""
    <div class="comfort-header">
        <div class="comfort-logo">
            <span class="comfort-logo-icon">☀️</span>
            Comfort Inn Edgware
        </div>
        <div class="comfort-tagline">
            Earth Day Energy Dashboard | April 2025
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    df = load_data()
    
    if df.empty:
        st.error("No data loaded. Please check your elec.csv file.")
        return
    
    # Calculate Jan-March comparison
    comparison = calculate_q1_comparison(df)
    
    # Main content - use columns for layout
    if comparison:
        # Calculate guest usage data (simulated)
        avg_guests_per_night = 57  # Using the provided number of guests per night
        total_q1_consumption = comparison['current_total']  # Total consumption in Q1
        days_in_q1 = 90  # Approximate days in Jan-Mar
        
        # Calculate average consumption per guest per night
        avg_consumption_per_guest = (total_q1_consumption / days_in_q1) / avg_guests_per_night
        
        # KPI row with 4 custom styled metrics
        kpi_cols = st.columns(4)
        
        with kpi_cols[0]:
            direction = "Reduction" if comparison['percent_change'] < 0 else "Increase"
            delta_class = "positive" if comparison['percent_change'] < 0 else "negative"
            
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Jan-Mar {comparison['current_year']} vs {comparison['previous_year']}</div>
                <div class="metric-value">{abs(comparison['percent_change']):.1f}%</div>
                <div class="metric-delta {delta_class}">{direction}</div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi_cols[1]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">Energy Saved (Jan-Mar)</div>
                <div class="metric-value">{comparison['energy_saved']:,.0f} kWh</div>
                <div class="metric-delta positive">Conservation</div>
            </div>
            """, unsafe_allow_html=True)
        
        with kpi_cols[2]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">CO₂ Prevented (Jan-Mar)</div>
                <div class="metric-value">{comparison['co2_prevented']:,.0f} kg</div>
                <div class="metric-delta positive">Emissions Reduction</div>
            </div>
            """, unsafe_allow_html=True)
            
        with kpi_cols[3]:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">👤 GUEST USAGE</div>
                <div class="metric-value">{avg_consumption_per_guest:.1f} kWh</div>
                <div class="metric-delta positive">Per Guest Per Night</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Champion Section with Comfort Inn styling
    st.markdown("""
    <div class="champion-container">
        <img src="https://ui-avatars.com/api/?name=Asina&background=F37021&color=fff&size=60" class="champion-photo">
        <div class="champion-info">
            <h3>Asina, Green Champion</h3>
            <p>"We've made great progress in Jan - March! Let's keep up the momentum! Remember to turn off lights when leaving a room and report any issues with equipment immediately."</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Two column layout for chart and feedback
    col1, col2 = st.columns(2)
    
    # Jan-March comparison chart
    with col1:
        st.markdown("<h3>Jan - March Comparison</h3>", unsafe_allow_html=True)
        q1_chart = create_q1_chart(df, comparison)
        if q1_chart:
            # Update chart height to make it more compact
            q1_chart.update_layout(height=300, margin=dict(l=40, r=10, t=30, b=40))
            st.plotly_chart(q1_chart, use_container_width=True, config={'displayModeBar': False})
    
    # Add Sli.do interactive widget section
    with col2:
        st.markdown("""
        <h3>Earth Day Feedback & Ideas
            <a href="https://app.sli.do/event/3WAHPxwukLUzmdQH8VPyY8" target="_blank" style="font-size: 0.75rem; color: #F37021; margin-left: 10px; text-decoration: none;">
                📱 Click to open Slido on your device
            </a>
        </h3>
        """, unsafe_allow_html=True)
        
        # Embed Sli.do using components.html with reduced height
        components.html(
            """
            <div style="width: 100%; height: 100%;">
                <iframe src="https://wall.sli.do/event/3WAHPxwukLUzmdQH8VPyY8/?section=cf35fe01-35ec-4732-a24f-01dbb4257c08" 
                        frameborder="0" 
                        style="width: 100%; height: 300px;" 
                        allow="camera; microphone; fullscreen; display-capture; autoplay">
                </iframe>
            </div>
            """,
            height=300,
        )
    
    # Energy saving reminders as a banner at the bottom
    st.markdown("<h3>Quick Energy-Saving Reminders</h3>", unsafe_allow_html=True)
    
    reminders = [
        "💡 Turn off lights in unoccupied areas",
        "🚿 Report leaking taps immediately",
        "🌡️ Keep thermostat at 21-23°C",
        "☀️ Use natural light when possible",
        "🔌 Unplug equipment when not in use",
        "🚶‍♂️ Use stairs for trips under 3 floors"
    ]
    
    # Create a horizontal banner with all reminders
    reminder_html = '<div class="energy-savings-banner">'
    for reminder in reminders:
        reminder_html += f'<div class="energy-reminder"><p>{reminder}</p></div>'
    reminder_html += '</div>'
    
    st.markdown(reminder_html, unsafe_allow_html=True)
    
    # Footer with Comfort Inn branding
    st.markdown("""
    <div class="footer">
        <p>Comfort Inn Edgware - Earth Day Power Up Initiative | Last Updated: March 31, 2025</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()