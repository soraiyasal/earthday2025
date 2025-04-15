import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import random
import streamlit.components.v1 as components

# Set page config - must be first Streamlit command
st.set_page_config(
    page_title="Westin Earth Day 2025", 
    page_icon="🌍", 
    layout="wide",
    initial_sidebar_state="collapsed"  # Start with sidebar collapsed
)

# Hide sidebar completely with CSS
st.markdown("""
<style>
    [data-testid="collapsedControl"] {display: none;}
    section[data-testid="stSidebar"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

# Set the specific hotel for this dashboard
HOTEL_NAME = "Westin"

# MPAN to Hotel mapping
mpan_to_hotel = {
    "2500021277783": "Westin", 
    "1200051315859": "Camden", 
    "2500021281362": "Canopy",
    "1200052502710": "EH", 
    "1050000997145": "St Albans"
}

# Get MPAN for this hotel
def get_hotel_mpan(hotel_name):
    for mpan, hotel in mpan_to_hotel.items():
        if hotel == hotel_name:
            return mpan
    return None

HOTEL_MPAN = get_hotel_mpan(HOTEL_NAME)

# Electricity factors
ELECTRICITY_FACTOR = 0.20493  # 2024/2025 factor

# Load data from SQLite database
@st.cache_data(show_spinner=False)
def load_data():
    try:
        conn = sqlite3.connect('electricity_data.db')
        
        # If we have a valid MPAN for this hotel, filter by it
        if HOTEL_MPAN:
            query = f"""
            SELECT strftime('%Y-%m-%d %H:%M:%S', Date) as Date,
                   [Total Usage],
                   "00:00","00:30","01:00","01:30","02:00","02:30","03:00","03:30",
                   "04:00","04:30","05:00","05:30","06:00","06:30","07:00","07:30",
                   "08:00","08:30","09:00","09:30","10:00","10:30","11:00","11:30",
                   "12:00","12:30","13:00","13:30","14:00","14:30","15:00","15:30",
                   "16:00","16:30","17:00","17:30","18:00","18:30","19:00","19:30",
                   "20:00","20:30","21:00","21:30","22:00","22:30","23:00","23:30"
            FROM hh_data
            WHERE [Meter Point] = '{HOTEL_MPAN}'
            ORDER BY Date
            """
        else:
            # If no MPAN is found, load data without filtering
            query = """
            SELECT strftime('%Y-%m-%d %H:%M:%S', Date) as Date,
                   [Meter Point],
                   [Total Usage],
                   "00:00","00:30","01:00","01:30","02:00","02:30","03:00","03:30",
                   "04:00","04:30","05:00","05:30","06:00","06:30","07:00","07:30",
                   "08:00","08:30","09:00","09:30","10:00","10:30","11:00","11:30",
                   "12:00","12:30","13:00","13:30","14:00","14:30","15:00","15:30",
                   "16:00","16:30","17:00","17:30","18:00","18:30","19:00","19:30",
                   "20:00","20:30","21:00","21:30","22:00","22:30","23:00","23:30"
            FROM hh_data
            ORDER BY Date
            """
        
        data = pd.read_sql_query(query, conn)
        data['Date'] = pd.to_datetime(data['Date'])
        
        # If we didn't filter by MPAN, filter the data after loading
        if not HOTEL_MPAN and 'Meter Point' in data.columns:
            data["Meter Point"] = data["Meter Point"].astype(str)
            data["Hotel"] = data["Meter Point"].map(mpan_to_hotel)
            data = data[data["Hotel"] == HOTEL_NAME]
        
        # Ensure numeric values for time columns and Total Usage
        time_cols = [f"{str(hour).zfill(2)}:{minute}" 
                    for hour in range(24) 
                    for minute in ['00', '30']]
        for col in time_cols + ['Total Usage']:
            data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
        
        # Extract year from date for easier filtering
        data['Year'] = data['Date'].dt.year
        
        return data
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        # Return simulated data if database fails
        return generate_simulated_data()
    finally:
        if 'conn' in locals():
            conn.close()

# Generate simulated data for testing or when database fails
def generate_simulated_data():
    # Create date range for the last 2 years
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365*2)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # Generate realistic usage data with seasonal patterns and year-over-year improvement
    base_usage = 200  # Base kWh per day
    
    # Create data with seasonal patterns and weekday/weekend variation
    usage_data = []
    for date in dates:
        # Seasonal factor (higher in winter, lower in summer)
        month = date.month
        season_factor = 1.0 + 0.3 * np.cos((month - 1) * np.pi / 6)
        
        # Weekend factor (higher on weekends)
        weekend_factor = 1.2 if date.weekday() >= 5 else 1.0
        
        # Year factor (current year uses less energy than previous)
        year_factor = 0.85 if date.year == datetime.today().year else 1.0
        
        # Combine factors with random noise
        daily_usage = base_usage * season_factor * weekend_factor * year_factor * random.uniform(0.9, 1.1)
        
        usage_data.append(daily_usage)
    
    # Create dataframe
    data = pd.DataFrame({
        'Date': dates,
        'Total Usage': usage_data,
        'Year': [d.year for d in dates]
    })
    
    # Add time columns (not used in this view, but included for compatibility)
    time_cols = [f"{str(hour).zfill(2)}:{minute}" 
                for hour in range(24) 
                for minute in ['00', '30']]
    
    for col in time_cols:
        data[col] = 0
    
    return data

# Get matching day pairs for accurate comparison
def get_matching_day_pairs(data, current_start, current_end, compare_start, compare_end):
    """
    Extracts only day pairs that exist in both current and comparison periods,
    matching by day-of-week and week-of-month to ensure valid comparisons.
    """
    # Filter basic date ranges
    current_data = data[(data['Date'] >= current_start) & (data['Date'] <= current_end)].copy()
    compare_data = data[(data['Date'] >= compare_start) & (data['Date'] <= compare_end)].copy()
    
    # Create matching metadata
    current_data['day_of_week'] = current_data['Date'].dt.dayofweek
    current_data['week_of_month'] = (current_data['Date'].dt.day - 1) // 7 + 1
    current_data['month'] = current_data['Date'].dt.month
    
    compare_data['day_of_week'] = compare_data['Date'].dt.dayofweek
    compare_data['week_of_month'] = (compare_data['Date'].dt.day - 1) // 7 + 1
    compare_data['month'] = compare_data['Date'].dt.month
    
    # Create a match key for equivalent days (same day-of-week, week-of-month, month)
    current_data['match_key'] = current_data['month'].astype(str) + "-" + \
                               current_data['week_of_month'].astype(str) + "-" + \
                               current_data['day_of_week'].astype(str)
    
    compare_data['match_key'] = compare_data['month'].astype(str) + "-" + \
                               compare_data['week_of_month'].astype(str) + "-" + \
                               compare_data['day_of_week'].astype(str)
    
    # Find common match keys
    current_keys = set(current_data['match_key'])
    compare_keys = set(compare_data['match_key'])
    common_keys = current_keys.intersection(compare_keys)
    
    # Filter to matching days only
    current_matched = current_data[current_data['match_key'].isin(common_keys)]
    compare_matched = compare_data[compare_data['match_key'].isin(common_keys)]
    
    # Calculate match quality metrics
    total_expected_days = (current_end - current_start).days + 1
    match_percentage = (len(common_keys) / total_expected_days) * 100
    
    return {
        'current_data': current_matched,
        'compare_data': compare_matched,
        'matched_day_count': len(common_keys),
        'expected_day_count': total_expected_days,
        'match_percentage': match_percentage
    }

# Get KPIs using matched day pairs
def get_matched_kpis(data, current_start, current_end, compare_start, compare_end):
    # Get matched day pairs
    matched_data = get_matching_day_pairs(data, current_start, current_end, compare_start, compare_end)
    
    current_data = matched_data['current_data']
    compare_data = matched_data['compare_data']
    
    # Calculate metrics based only on matched days
    current_total = current_data['Total Usage'].sum()
    compare_total = compare_data['Total Usage'].sum()
    
    # Handle edge case where compare_total is 0
    if compare_total == 0:
        percent_change = 0
    else:
        percent_change = ((current_total - compare_total) / compare_total) * 100
    
    # Calculate daily averages
    current_daily_avg = current_data['Total Usage'].mean()
    compare_daily_avg = compare_data['Total Usage'].mean()
    
    # Calculate CO2 impact
    co2_saved = (compare_total - current_total) * ELECTRICITY_FACTOR
    
    # Calculate kWh saved
    kwh_saved = compare_total - current_total
    
    # Calculate per-guest usage (with average of 202 guests per night)
    avg_guests = 202
    if len(current_data) > 0:
        guest_usage = current_total / (len(current_data) * avg_guests)
    else:
        guest_usage = 0 
    
    # Add context to CO2 saved - trees equivalent
    # Average tree absorbs about 22 kg of CO2 per year
    trees_equivalent = int(co2_saved / 22)
    
    # Calculate progress toward 10% savings goal
    target_savings_percent = 10
    target_usage = compare_total * (1 - target_savings_percent/100)
    progress_percentage = min(100, max(0, ((compare_total - current_total) / (compare_total - target_usage)) * 100))
    
    # Make sure kwh_saved and co2_saved are properly calculated
    # If current_total is higher than compare_total, then there are no savings
    if current_total >= compare_total:
        kwh_saved = 0
        co2_saved = 0
        # Also make sure progress is 0 when there are no savings
        progress_percentage = 0
    else:
        kwh_saved = compare_total - current_total
        co2_saved = kwh_saved * ELECTRICITY_FACTOR
    
    remaining_kwh = max(0, current_total - target_usage)
    
    # Include match quality metrics
    return {
        'current_total': current_total,
        'compare_total': compare_total,
        'percent_change': percent_change,
        'current_daily_avg': current_daily_avg,
        'compare_daily_avg': compare_daily_avg,
        'co2_saved': co2_saved,
        'kwh_saved': kwh_saved,
        'matched_day_count': matched_data['matched_day_count'],
        'expected_day_count': matched_data['expected_day_count'],
        'match_percentage': matched_data['match_percentage'],
        'guest_usage': guest_usage,
        'progress_percentage': progress_percentage,
        'remaining_kwh': remaining_kwh,
        'target_savings_percent': target_savings_percent,
        'trees_equivalent': trees_equivalent
    }

# Get compare dates from previous year
def get_comparative_period(current_start, current_end):
    # Get same period from last year
    days_diff = (current_end - current_start).days
    last_year_end = current_end - pd.DateOffset(years=1)
    last_year_start = last_year_end - timedelta(days=days_diff)
    
    return last_year_start, last_year_end

def get_hourly_chart(data, current_start, current_end):
    # Use full data for hourly analysis
    current_period_data = data[(data['Date'] >= current_start) & (data['Date'] <= current_end)]
    
    # Check if we have time columns in our data
    time_cols = [f"{str(hour).zfill(2)}:{minute}" 
                for hour in range(24) 
                for minute in ['00', '30']]
                
    hourly_columns_exist = all(col in current_period_data.columns for col in time_cols[:4])
    
    if hourly_columns_exist:
        # For half-hourly data, use the raw time columns directly
        hh_data = []
        
        for col in time_cols:
            hh_data.append({
                'time_slot': col,
                'usage': current_period_data[col].mean()
            })
        
        hh_df = pd.DataFrame(hh_data)
        
        # Add hour information for sorting and grouping
        hh_df['hour'] = hh_df['time_slot'].apply(lambda x: int(x.split(':')[0]))
        hh_df['minute'] = hh_df['time_slot'].apply(lambda x: x.split(':')[1])
        
        # Find top 5 peak half-hour periods
        top_periods = hh_df.nlargest(5, 'usage')
        
        # Create half-hourly chart with Westin colors - using Granite to Basil gradient
        hour_fig = px.bar(
            hh_df,
            x='time_slot',
            y='usage',
            color='usage',
            # Updated to Westin color palette - Granite to Basil gradient
            color_continuous_scale=[[0, "#51555A"], [0.5, "#6aad90"], [1, "#294237"]],
            labels={'usage': 'Energy (kWh)', 'time_slot': 'Time of Day'}
        )
        
        # Only show every 2-hour label to avoid crowding
        show_labels = hh_df.loc[hh_df['minute'] == '00', 'time_slot'].iloc[::2].tolist()
        
        hour_fig.update_layout(
            coloraxis_showscale=False,
            height=240,
            margin=dict(l=5, r=5, t=5, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                tickmode='array',
                tickvals=show_labels,
                ticktext=show_labels,
                title=None,
                gridcolor='#E9E9E9',
                tickfont=dict(size=9, family="Arial, sans-serif")
            ),
            yaxis=dict(
                title=None,
                gridcolor='#E9E9E9',
                tickfont=dict(size=9, family="Arial, sans-serif")
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=10,
                font_family="Arial, sans-serif"
            )
        )
        
        # Format peak times for display
        peak_times = []
        for _, period in top_periods.iterrows():
            # Convert 24h time to 12h format for readability
            hour = int(period['time_slot'].split(':')[0])
            minute = period['time_slot'].split(':')[1]
            ampm = 'am' if hour < 12 else 'pm'
            hour_12 = hour if hour <= 12 else hour - 12
            hour_12 = 12 if hour_12 == 0 else hour_12
            peak_times.append(f"{hour_12}:{minute}{ampm}")
        
        return {
            'figure': hour_fig,
            'peak_times': peak_times,
            'type': 'hourly'
        }
    else:
        # Fall back to daily pattern if hourly data is not available
        dow_data = current_period_data.copy()
        dow_data['day_of_week'] = dow_data['Date'].dt.dayofweek
        dow_data['day_name'] = dow_data['Date'].dt.day_name()
        
        # Aggregate by day of week
        dow_avg = dow_data.groupby(['day_of_week', 'day_name'])['Total Usage'].mean().reset_index()
        dow_avg = dow_avg.sort_values('day_of_week')
        
        # Create day of week chart with Westin colors
        dow_fig = px.bar(
            dow_avg,
            x='day_name',
            y='Total Usage',
            color='Total Usage',
            # Updated to Westin color palette - Granite to Basil gradient
            color_continuous_scale=[[0, "#51555A"], [0.5, "#81858C"], [1, "#294237"]],
            labels={'Total Usage': 'Energy (kWh)', 'day_name': 'Day of Week'}
        )
        
        dow_fig.update_layout(
            coloraxis_showscale=False,
            height=240,
            margin=dict(l=5, r=5, t=5, b=20),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(
                title=None,
                gridcolor='#E9E9E9',
                categoryorder='array',
                categoryarray=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                tickfont=dict(size=9, family="Arial, sans-serif")
            ),
            yaxis=dict(
                title=None,
                gridcolor='#E9E9E9',
                tickfont=dict(size=9, family="Arial, sans-serif")
            ),
            hoverlabel=dict(
                bgcolor="white",
                font_size=10,
                font_family="Arial, sans-serif"
            )
        )
        
        # Find highest usage days
        top_days = dow_avg.nlargest(2, 'Total Usage')
        
        return {
            'figure': dow_fig,
            'peak_days': top_days['day_name'].tolist(),
            'type': 'daily'
        }
    
# Main dashboard
def main():
    # Load custom CSS with Westin branding and responsive design
    st.markdown("""
    <style>
        /* Main header styling */
        .header-container {
            background-color: #51555A;  /* Westin Granite */
            padding: 0.5rem;
            border-radius: 0.4rem;
            color: white;
            text-align: center;
            margin-bottom: 0.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        /* Westin logo style in header */
        .westin-header-logo {
            height: 40px;
            margin-right: 10px;
            vertical-align: middle;
        }
        
        /* Header title with logo styling */
        .header-title {
            font-size: 1.6rem;
            font-weight: 700;
            margin: 0;
            color: white;
            flex-grow: 1;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.3);
            letter-spacing: 0.5px;
            background-color: #51555A; /* Westin Granite */
            font-family: 'Arial', sans-serif;
            display: flex;
            align-items: center;
        }
        
        .period-selector {
            width: 180px;
            margin-right: 0.5rem;
        }
        
        /* Ultra-compact body styling */
        .block-container {
            padding-top: 0.2rem !important;
            padding-bottom: 0.2rem !important;
            max-width: 100% !important;
        }
        
        div.stApp > header {
            display: none;
        }
        
        .main > div {
            padding-left: 1rem;
            padding-right: 1rem;
        }
        
        /* Fixed height card styling */
        .card {
            background-color: white;
            border-radius: 0.4rem;
            padding: 0.6rem 0.8rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            border: 1px solid #E9E9E9; /* Lighter Granite */
            height: 110px !important;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            margin-bottom: 0.6rem;
            overflow: hidden;
        }
        
        /* Fix truncation issues with labels */
        .metric-label {
            font-size: 0.9rem;
            color: #51555A; /* Westin Granite */
            margin-bottom: 0.3rem;
            font-family: 'Arial', sans-serif;
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
            display: block !important;
            -webkit-line-clamp: unset !important;
            -webkit-box-orient: unset !important;
            line-height: 1.2;
            max-height: none !important;
        }
        
        /* Fix truncation issues with values */
        .metric-value {
            font-size: 1.3rem;
            font-weight: 700;
            color: #294237; /* Westin Basil */
            margin: 0.2rem 0;
            font-family: 'Arial', sans-serif;
            white-space: normal !important;
            overflow: visible !important;
            text-overflow: clip !important;
            line-height: 1.2;
            max-height: none !important;
        }
        
        /* Fix truncation issues with delta indicators */
        .metric-delta {
            font-size: 0.8rem;
            color: #007a3e; /* Darker green */
            font-weight: 600;
            padding: 0.2rem 0.4rem;
            background-color: #e9f7ef; /* Light mint */
            border-radius: 0.25rem;
            display: block !important;
            overflow: visible !important;
            text-overflow: clip !important;
            white-space: normal !important;
            max-width: 100%;
            line-height: 1.2;
            max-height: none !important;
            font-family: 'Arial', sans-serif;
        }
        
        .metric-delta.negative {
            color: #B4786C; /* Westin Terracotta */
            background-color: #fdf2f0;
        }
        
        /* Progress bar styling */
        .progress-container {
            width: 100%;
            height: 10px;
            background-color: #E9E9E9; /* Light Granite */
            border-radius: 5px;
            margin-top: 0.2rem;
        }
        
        .progress-bar {
            height: 100%;
            border-radius: 5px;
            background-color: #294237; /* Westin Basil */
        }
        
        /* Make champion container match metric card height */
        .champion-container {
            background-color: #f2f7f6;  /* Light Basil */
            border-radius: 0.4rem;
            padding: 0.6rem;
            display: flex;
            align-items: center;
            gap: 0.6rem;
            height: 110px !important;
            border: 1px solid #294237;  /* Westin Basil border */
            margin-bottom: 0.6rem;
            overflow: hidden;
        }
        
        .champion-photo {
            width: 50px;
            height: 50px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid #294237;  /* Westin Basil */
            flex-shrink: 0;
        }
        
        .champion-info {
            flex: 1;
            overflow: hidden;
        }
        
        .champion-info h3 {
            font-size: 0.85rem;
            margin-top: 0;
            margin-bottom: 0.2rem;
            color: #294237;  /* Westin Basil */
            font-family: 'Arial', sans-serif;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }
        
        .champion-info p {
            font-size: 0.75rem;
            margin: 0;
            line-height: 1.2;
            color: #51555A;  /* Westin Granite */
            font-family: 'Arial', sans-serif;
            overflow: auto !important; /* Changed from 'hidden' to 'auto' to enable scrolling */
            max-height: 2.7em; /* Maintain height but allow scrolling */
            padding-right: 5px; /* Add some padding for the scrollbar */
        }
        
        /* Chart title styling */
        .chart-title {
            font-size: 0.85rem;
            margin-top: 0;
            margin-bottom: 0.3rem;
            color: #51555A;  /* Westin Granite */
            font-weight: 600;
            font-family: 'Arial', sans-serif;
        }
        
        .chart-subtitle {
            font-size: 0.7rem;
            margin: 0;
            color: #51555A;  /* Westin Granite */
            text-align: center;
            font-family: 'Arial', sans-serif;
        }
        
        /* Chart container with margin */
        .chart-container {
            margin-bottom: 0.8rem;
        }
        
        /* Tips styling with better visibility */
        .tips-section {
            height: auto;
            min-height: 110px;
            background-color: #f2f7f6;  /* Very light Basil */
            padding: 0.6rem;
            border-radius: 0.4rem;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            border: 1px solid #294237;  /* Westin Basil */
            display: flex;
            flex-direction: column;
            margin-bottom: 0.8rem;
            max-height: 200px;
            overflow-y: auto;
        }
        
        .tips-section h3 {
            font-size: 0.85rem;
            margin-top: 0;
            margin-bottom: 0.3rem;
            color: #294237;  /* Westin Basil */
            font-weight: 600;
            font-family: 'Arial', sans-serif;
        }
        
        .tips-container {
            display: flex;
            flex-wrap: wrap;
            gap: 0.4rem;
            margin-top: 0.2rem;
            overflow: visible;
        }
        
        .tip-chip {
            background-color: white;
            padding: 0.2rem 0.4rem;
            border-radius: 9999px;
            font-size: 0.7rem;
            white-space: nowrap;
            border: 1px solid #51555A;  /* Westin Granite */
            color: #294237;  /* Westin Basil for text */
            font-family: 'Arial', sans-serif;
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
font-weight: 600;
        }
        
        /* Feedback container with margin */
        .feedback-container {
            margin-bottom: 0.8rem;
        }
        
        /* Feedback title styling */
        .feedback-title {
            font-size: 0.85rem;
            margin-top: 0;
            margin-bottom: 0.3rem;
            color: #294237;  /* Westin Basil */
            font-weight: 600;
            font-family: 'Arial', sans-serif;
        }
        
        /* Footer */
        .footer {
            text-align: center;
            color: #51555A;  /* Westin Granite */
            font-size: 0.65rem;
            margin-top: 0.5rem;
            margin-bottom: 0.5rem;
            font-family: 'Arial', sans-serif;
        }
        
        /* Fix for plot background */
        .js-plotly-plot .plotly .main-svg {
            background-color: transparent !important;
        }
        
        /* Remove padding from columns */
        div.css-1r6slb0.e1tzin5v2 {
            padding: 0.1rem !important;
        }
        
        /* Hide streamlit elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Time frame selector note styling */
        .timeframe-note {
            font-size: 0.7rem;
            font-style: italic;
            color: #B4786C; /* Westin Terracotta */
            margin-top: 2px;
            margin-bottom: 5px;
            text-align: center;
        }
        
/* Responsive adjustments */
        @media (max-width: 992px) {
            .header-title {
                font-size: 1.2rem;
            }
            
            .westin-header-logo {
                height: 30px;
            }
            
            /* Adjusted card height for mobile */
            .card {
                height: 100px !important;
            }

            .champion-container {
                height: 100px !important; /* Match card height on mobile */
            }
            
            .card {
                background-color: #FFFFFF;
                border-color: #51555A;
            }
            
            .metric-label {
                color: #51555A;
            }
            
            .metric-value {
                color: #294237;
            }
            
            .metric-delta {
                background-color: rgba(233, 247, 239, 0.1);
                color: #294237;
            }
                
            .champion-info p {
                overflow: auto !important; /* Enable scrolling on mobile too */
                max-height: 1.8em;
            }
            
            /* Stack columns on mobile */
            .mobile-stack {
                display: flex;
                flex-direction: column;
            }
            
            .mobile-stack > div {
                width: 100% !important;
                margin-bottom: 0.8rem;
            }
            
            /* Adjust padding for mobile */
            .main > div {
                padding-left: 0.5rem;
                padding-right: 0.5rem;
            }
            
            /* Ensure tips are fully visible on mobile */
            .tips-section {
                max-height: 250px; /* Taller on mobile for better visibility */
            }
            
            .tip-chip {
                font-weight: 700; /* Bolder on mobile for better visibility */
            }
            
            /* Better mobile chart spacing */
            .chart-container {
                margin-bottom: 1rem;
            }
            
            /* Better mobile Slido container spacing */
            .feedback-container {
                margin-bottom: 1rem;
            }
            
            /* Make timeframe-note more visible on mobile */
            .timeframe-note {
                font-size: 0.75rem;
                font-weight: 600;
                color: #B4786C;
            }
        }
        
        /* Dark mode support */
        @media (prefers-color-scheme: dark) {
            .card {
                background-color: #1e2a38;
                border-color: #294237;
            }
            
            .metric-value {
                color: #f0f0f0;
            }
            .metric-delta {
                color: white !important; /* Force white text */
                background-color: rgba(41, 66, 55, 0.3); /* Keep the semi-transparent background */
            }
            
            .metric-delta.negative {
                color: white !important; /* Force white text for negative values too */
                background-color: rgba(180, 120, 108, 0.2); /* Keep the semi-transparent background */
            }
            
            .champion-container {
                background-color: #1e2a38;
            }
            
            .champion-info p {
                color: #e0e0e0;
            }
            
            .tips-section {
                background-color: #1e2a38;
            }
            
            .tip-chip {
                background-color: #2c3e50;
                color: #a7bdb3;
                border-color: #294237;
            }
            
            .chart-subtitle {
                color: #e0e0e0;
            }
            
            .timeframe-note {
                color: #f2c1b6; /* Lighter Terracotta for dark mode */
            }
        }
        
        /* Hide dropdown arrow for period selector */
        .period-selector button {
            display: none !important;
        }
        
        /* Fix for Streamlit components */
        .stSelectbox > div > div {
            background-color: #1e2a38 !important; /* Dark background */
            color: #f0f0f0 !important; /* Light text */
            border-color: #294237 !important; /* Westin Basil border */
        }
        
        /* Style for dropdown options in dark mode */
        .stSelectbox ul {
            background-color: #1e2a38 !important;
            color: #f0f0f0 !important;
        }
        
        /* Dropdown arrow color in dark mode */
        .stSelectbox svg {
            color: #f0f0f0 !important;
        }
        
        /* Westin logo style */
        .westin-logo {
            height: 24px;
            margin-right: 8px;
            vertical-align: middle;
        }
        
        /* Add Westin's "Heavenly" cloud element */
        .heavenly-element {
            position: absolute;
            top: 5px;
            right: 5px;
            width: 30px;
            height: 30px;
            background-color: #f2f7f6;
            border-radius: 50%;
            opacity: 0.5;
        }
        
        /* Wellness message styling */
        .wellness-message {
            font-style: italic;
            color: #51555A;
            font-size: 0.7rem;
            text-align: center;
            margin-top: 0.4rem;
            margin-bottom: 0.4rem;
            font-family: 'Arial', sans-serif;
        }
    </style>
    """, unsafe_allow_html=True)

    # Add responsive JavaScript for detecting mobile devices and fitting text
    st.markdown("""
    <script>
        // Add mobile class to body if screen width is less than 768px
        function checkMobile() {
            if (window.innerWidth < 768) {
                document.body.classList.add('mobile');
                
                // Find all elements with the class 'row' and add the 'mobile-stack' class
                const rows = document.querySelectorAll('.row');
                rows.forEach(row => {
                    row.classList.add('mobile-stack');
                });
                
                // Add a class to the document root for CSS targeting
                document.documentElement.classList.add('mobile-view');
            } else {
                document.body.classList.remove('mobile');
                document.documentElement.classList.remove('mobile-view');
                
                // Remove 'mobile-stack' class from rows
                const rows = document.querySelectorAll('.row');
                rows.forEach(row => {
                    row.classList.remove('mobile-stack');
                });
            }
        }
        
        // Run mobile detection on load and on resize
        window.addEventListener('load', checkMobile);
        window.addEventListener('resize', checkMobile);
        
        // Function to ensure text fits within fixed height cards
        function adjustCardText() {
            // Handle metric values
            document.querySelectorAll('.metric-value').forEach(el => {
                const originalFontSize = parseFloat(getComputedStyle(el).fontSize);
                let fontSize = originalFontSize;
                
                // If text overflows, reduce font size
                while (el.scrollWidth > el.offsetWidth && fontSize > 9) {
                    fontSize -= 0.5;
                    el.style.fontSize = fontSize + 'px';
                }
                
                // If text still overflows at minimum size, add ellipsis
                if (el.scrollWidth > el.offsetWidth) {
                    el.style.textOverflow = 'ellipsis';
                }
            });
            
            // Handle metric labels
            document.querySelectorAll('.metric-label').forEach(el => {
                if (el.scrollHeight > el.offsetHeight) {
                    el.style.webkitLineClamp = '1';
                }
            });
            
            // Handle metric deltas - these can wrap but need to fit vertically
            document.querySelectorAll('.metric-delta').forEach(el => {
                if (el.scrollHeight > el.offsetHeight) {
                    let text = el.textContent;
                    // Shorten text if it's too long
                    if (text.length > 30) {
                        el.textContent = text.substring(0, 27) + '...';
                    }
                }
            });
            
            // Make champion info text scrollable instead of truncated
            document.querySelectorAll('.champion-info p').forEach(el => {
                // Remove line clamp and enable scrolling
                el.style.webkitLineClamp = 'none';
                el.style.overflow = 'auto';
            });
            
            // Ensure tip chips are visible
            document.querySelectorAll('.tip-chip').forEach(chip => {
                chip.style.color = '#294237'; // Changed to Westin Basil
                chip.style.fontWeight = '600';
            });
        }
        
        // Run text adjustments after content loads
        window.addEventListener('load', function() {
            adjustCardText();
            
            // Check again after a slight delay to ensure all content is fully rendered
            setTimeout(adjustCardText, 300);
        });
        
        // Also run adjustments on resize
        window.addEventListener('resize', adjustCardText);
        
        // Set mobile detection in sessionStorage
        if (window.innerWidth < 768) {
            sessionStorage.setItem('is_mobile', 'true');
        } else {
            sessionStorage.setItem('is_mobile', 'false');
        }
    </script>
    """, unsafe_allow_html=True)

    # Load data
    data = load_data()
    
    if len(data) == 0:
        st.warning(f"No data found for {HOTEL_NAME}. Please check your hotel name and MPAN mapping.")
        st.stop()
    
    # Define time periods
    today = datetime.today()
    
    # For Earth Day challenge - UPDATED DATES
    challenge_start = datetime(2025, 4, 15)  # Changed from 14 to 15
    challenge_end = datetime(2025, 4, 22)  # Same end date
    
    # For current view (default to Year to Date)
    current_end = today
    current_start = datetime(today.year, 1, 1)  # Year to date by default
    
    # Header with period selector
    header_col1, header_col2 = st.columns([4, 1])

    # Replace the existing header code in the header_col1 section with this:

# Replace the existing header code in the header_col1 section with this:

    with header_col1:
        # Load and encode the image
        import base64
        from pathlib import Path
        
        try:
            # Load and encode the image
            img_path = "logos/westin_logo.png"
            with open(img_path, "rb") as f:
                img_data = base64.b64encode(f.read()).decode()
            
            # Create HTML with both logo and text explicitly left-aligned
            st.markdown(f"""
            <div style="display: flex; flex-direction: column; align-items: flex-start; justify-content: flex-start; gap: 5px; margin-left: 0;">
                <img src="data:image/png;base64,{img_data}" 
                    style="height: 65px; display: block; margin-left: 0; align-self: flex-start;"
                    alt="Westin">
                <span style="color: #51555A; font-size: 1.5rem; font-weight: 700; font-family: Arial, sans-serif; 
                            display: block; margin-left: 0; padding: 0; text-align: left; align-self: flex-start;">
                    Celebrates Earth Day 2025
                </span>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            # Fallback if image loading fails
            st.markdown("""
            <div style="display: flex; flex-direction: column; align-items: flex-start; justify-content: flex-start; margin-left: 0;">
                <span style="color: #51555A; font-size: 1.5rem; font-weight: 700; font-family: Arial, sans-serif; 
                            display: block; margin-left: 0; padding: 0; text-align: left; align-self: flex-start;">
                    THE WESTIN LONDON CITY Celebrates Earth Day 2025
                </span>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            # Fallback if image loading fails
            st.markdown("""
            <div style="display: flex; flex-direction: column; align-items: center; text-align: center;">
                <span style="color: #51555A; font-size: 1.5rem; font-weight: 700; font-family: Arial, sans-serif; 
                            display: block; margin: 10px auto; padding: 0; text-align: center;">
                    THE WESTIN LONDON CITY Celebrates Earth Day 2025
                </span>
            </div>
            """, unsafe_allow_html=True)

    with header_col2:
        # Period selector
        period = st.selectbox(
            "",
            options=[
                "Year to Date",
                "Last 7 Days", 
                "Last 30 Days"
            ],
            index=0,
            label_visibility="collapsed"
        )
        
        # Add a note for mobile users about the time frame selector

        
    # Set date ranges based on selection
    if period == "Last 7 Days":
        current_end = today
        current_start = today - timedelta(days=7)
    elif period == "Last 30 Days":
        current_end = today
        current_start = today - timedelta(days=30)
    elif period == "Year to Date":
        current_end = today
        current_start = datetime(today.year, 1, 1)

    else:
        current_start = challenge_start - timedelta(days=365)
        current_end = challenge_end - timedelta(days=365)
    
    # Get comparison period (same days last year)
    compare_start, compare_end = get_comparative_period(current_start, current_end)
    
    # Get KPIs using matched day pairs
    kpis = get_matched_kpis(data, current_start, current_end, compare_start, compare_end)
    
    # Get energy chart
    try:
        energy_chart = get_hourly_chart(data, current_start, current_end)
    except Exception as e:
        energy_chart = None
    
    # Check if on mobile for layout
    is_mobile = st.session_state.get('is_mobile', False)

    # Row 1: KPIs and Champion - responsive layout
    if is_mobile:
        # Mobile layout - stack cards
        row1_cols = st.columns([1])
        
        with row1_cols[0]:
            # CO2 Saved
            st.markdown(f"""
            <div class="card">
                <p class="metric-label">🌍 CO₂ SAVED</p>
                <p class="metric-value">{kpis['co2_saved']:,.0f} kg</p>
                <p class="metric-delta">CARBON REDUCTION</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Energy saved
            st.markdown(f"""
            <div class="card">
                <p class="metric-label">💡 ENERGY SAVED</p>
                <p class="metric-value">{kpis['kwh_saved']:,.0f} kWh</p>
                <p class="metric-delta">VS LAST YEAR</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Guest Usage with lightbulb equivalence
            # Calculate lightbulb equivalence (assuming standard UK 10W LED bulb running for 10 hours)
            # 10W bulb for 10 hours = 0.1 kWh, so divide guest usage by 0.1 to get number of bulbs
            lightbulb_equivalent = int(kpis['guest_usage'] / 0.1)
            
            st.markdown(f"""
            <div class="card">
                <p class="metric-label">👤 GUEST USAGE</p>
                <p class="metric-value">{kpis['guest_usage']:,.2f} kWh</p>
                <p class="metric-delta">= {lightbulb_equivalent} LED BULBS FOR 10 HOURS</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Progress to Goal - simplified with clearer progress indicators
            current_percentage = abs(kpis['percent_change']) if kpis['percent_change'] < 0 else 0.0
            target_percentage = kpis['target_savings_percent']
            progress_towards_target = min(100, (current_percentage / target_percentage) * 100)
            
            # Percentage remaining to target
            percentage_remaining = max(0, target_percentage - current_percentage)
            

            st.markdown(f"""
            <div class="card">
                <p class="metric-label">🎯 {target_percentage}% SAVINGS GOAL</p>
                <div class="progress-container">
                    <div class="progress-bar" style="width: {progress_towards_target}%;"></div>
                </div>
                <p class="metric-value">{current_percentage:.1f}% SAVED</p>
                <p class="metric-delta">{percentage_remaining:.1f}% MORE NEEDED</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Green Champion with Westin styling - Updated text
            st.markdown("""
            <div class="champion-container">
                <img src="https://ui-avatars.com/api/?name=JG&background=294237&color=fff&size=50" class="champion-photo">
                <div class="champion-info">
                    <h3>Jekaterina and Gayatri - Green Champions</h3>
                    <p>"At The Westin London City, we're committed to sustainability as part of our wellness pillar. Meet us for personalised energy-saving tips."</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Desktop layout - cards in a row
        row1_cols = st.columns([1, 1, 1, 1, 3])
        
        # KPIs
        with row1_cols[0]:
            # CO2 SAVED
            st.markdown(f"""
            <div class="card">
                <p class="metric-label">🌍 CO₂ SAVED</p>
                <p class="metric-value">{kpis['co2_saved']:,.0f} kg</p>
                <p class="metric-delta">CARBON REDUCTION</p>
            </div>
            """, unsafe_allow_html=True)
        
        with row1_cols[1]:
            # Energy saved
            st.markdown(f"""
            <div class="card">
                <p class="metric-label">💡 ENERGY SAVED</p>
                <p class="metric-value">{kpis['kwh_saved']:,.0f} kWh</p>
                <p class="metric-delta">VS LAST YEAR</p>
            </div>
            """, unsafe_allow_html=True)
        
        with row1_cols[2]:
            # Guest Usage (NEW) instead of Daily Average with lightbulb equivalence
            # Calculate lightbulb equivalence (assuming standard UK 10W LED bulb running for 10 hours)
            # 10W bulb for 10 hours = 0.1 kWh, so divide guest usage by 0.1 to get number of bulbs
            lightbulb_equivalent = int(kpis['guest_usage'] / 0.1)
            
            st.markdown(f"""
            <div class="card">
                <p class="metric-label">👤 GUEST USAGE</p>
                <p class="metric-value">{kpis['guest_usage']:,.2f} kWh</p>
                <p class="metric-delta">= {lightbulb_equivalent} LED BULBS FOR 10 HOURS</p>
            </div>
            """, unsafe_allow_html=True)
            
        with row1_cols[3]:
            # Progress to Goal - simplified with clearer progress indicators
            current_percentage = abs(kpis['percent_change']) if kpis['percent_change'] < 0 else 0.0
            target_percentage = kpis['target_savings_percent']
            progress_towards_target = kpis['progress_percentage']  # Use the correct value from KPIs
            
            # Percentage remaining to target
            percentage_remaining = max(0, target_percentage - current_percentage)
            
            st.markdown(f"""
            <div class="card">
                <p class="metric-label">🎯{target_percentage}% GOAL</p>
                <div class="progress-container">
                    <div class="progress-bar" style="width: {progress_towards_target}%;"></div>
                </div>
                <p class="metric-value">{current_percentage:.1f}% SAVED</p>
                <p class="metric-delta">{percentage_remaining:.1f}% MORE NEEDED</p>
            </div>
            """, unsafe_allow_html=True)
        
        with row1_cols[4]:
            # Green Champion with Westin styling - Updated text
            st.markdown("""
            <div class="champion-container">
                <img src="https://ui-avatars.com/api/?name=JG&background=294237&color=fff&size=50" class="champion-photo">
                <div class="champion-info">
                    <h3>Jekaterina and Gayatri - Green Champions</h3>
                    <p>"At The Westin London City, we're committed to sustainability as part of our wellness pillar. Meet us for personalised energy-saving tips."</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
# Row 2: Main content - chart and tips - responsive layout
    if is_mobile:
        # Mobile layout - stack columns
        # Peak Energy Chart 
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="chart-title">Peak Energy Periods</h3>', unsafe_allow_html=True)
        
        if energy_chart:
            st.plotly_chart(energy_chart['figure'], use_container_width=True, config={'displayModeBar': False})
            
            if energy_chart['type'] == 'hourly':
                st.markdown(f"""
                <p class="chart-subtitle">
                    <strong>Peak times:</strong> {', '.join(energy_chart['peak_times'][:3])}
                </p>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <p class="chart-subtitle">
                    <strong>Highest usage:</strong> {', '.join(energy_chart['peak_days'])}
                </p>
                """, unsafe_allow_html=True)
        else:
            st.info("Energy data unavailable")
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Slido with Westin-styled title
        st.markdown('<div class="feedback-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="feedback-title">Heavenly Ideas for Earth Day</h3>', unsafe_allow_html=True)
        
        # Embed Sli.do with adjusted height and clickable link
        st.markdown("""
        <a href="https://app.sli.do/event/3WAHPxwukLUzmdQH8VPyY8" target="_blank" style="font-size: 0.75rem; color: #fe5000; margin-bottom: 5px; display: block;">
            📱 Click here to open Slido on your device
        </a>
        """, unsafe_allow_html=True)
        
        components.html(
            """
            <iframe src="https://wall.sli.do/event/3WAHPxwukLUzmdQH8VPyY8/?section=cf35fe01-35ec-4732-a24f-01dbb4257c08" 
                    frameborder="0" 
                    style="width: 100%; height: 230px;" 
                    allow="camera; microphone; fullscreen; display-capture; autoplay">
            </iframe>
            """,
            height=250,
        )
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        # Desktop layout - side by side
        row2_cols = st.columns([1, 1])
        
        # Peak Energy Chart 
        with row2_cols[0]:
            st.markdown('<div class="chart-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="chart-title">Peak Energy Periods</h3>', unsafe_allow_html=True)
            
            if energy_chart:
                st.plotly_chart(energy_chart['figure'], use_container_width=True, config={'displayModeBar': False})
                
                if energy_chart['type'] == 'hourly':
                    st.markdown(f"""
                    <p class="chart-subtitle">
                        <strong>Peak times:</strong> {', '.join(energy_chart['peak_times'][:3])}
                    </p>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <p class="chart-subtitle">
                        <strong>Highest usage:</strong> {', '.join(energy_chart['peak_days'])}
                    </p>
                    """, unsafe_allow_html=True)
            else:
                st.info("Energy data unavailable")
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Slido with Westin-styled title
        with row2_cols[1]:
            st.markdown('<div class="feedback-container">', unsafe_allow_html=True)
            st.markdown('<h3 class="feedback-title">Heavenly Ideas for Earth Day</h3>', unsafe_allow_html=True)
            
            # Embed Sli.do with adjusted height and clickable link
            st.markdown("""
            <a href="https://app.sli.do/event/3WAHPxwukLUzmdQH8VPyY8" target="_blank" style="font-size: 0.75rem; color: #fe5000; margin-bottom: 5px; display: block;">
                📱 Click here to open Slido on your device
            </a>
            """, unsafe_allow_html=True)
            
            components.html(
                """
                <iframe src="https://wall.sli.do/event/3WAHPxwukLUzmdQH8VPyY8/?section=cf35fe01-35ec-4732-a24f-01dbb4257c08" 
                        frameborder="0" 
                        style="width: 100%; height: 230px;" 
                        allow="camera; microphone; fullscreen; display-capture; autoplay">
                </iframe>
                """,
                height=250,
            )
            st.markdown('</div>', unsafe_allow_html=True)
            
    # Row 3: Tips section in full width - ensure it's scrollable on small screens
    st.markdown("""
    <div class="tips-section">
        <h3>Wellness & Sustainability Tips</h3>
        <div class="tips-container">
            <div class="tip-chip">💡 Natural lighting</div>
            <div class="tip-chip">🚿 Shorter Heavenly Shower</div>
            <div class="tip-chip">🌡️ Thermostat at 22°C</div>
            <div class="tip-chip">☀️ Embrace daylight</div>
            <div class="tip-chip">🔌 Unplug devices</div>
            <div class="tip-chip">🚶‍♂️ Take the stairs</div>
            <div class="tip-chip">🧺 Reuse Heavenly linens</div>
            <div class="tip-chip">💧 Report leaks</div>
            <div class="tip-chip">🚪 Close doors</div>
            <div class="tip-chip">🔆 Task lighting</div>
            <div class="tip-chip">🌱 Join our green team</div>
            <div class="tip-chip">♻️ Recycle</div>
            <div class="tip-chip">🔧 Report issues</div>
            <div class="tip-chip">💻 Power down</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Westin's wellness message
    st.markdown("""
    <div class="wellness-message">
        "For a better you. For a better world." - The Westin London City
    </div>
    """, unsafe_allow_html=True)
    
    # Footer with Westin branding and matched days info
    st.markdown(f"""
    <div class="footer">
        The Westin London City | Earth Day Challenge | {current_start.strftime('%b %d')} - {current_end.strftime('%b %d, %Y')} | vs {compare_start.strftime('%b %d')} - {compare_end.strftime('%b %d, %Y')} | Based on {kpis['matched_day_count']} matched days out of {kpis['expected_day_count']} expected
    </div>
    """, unsafe_allow_html=True)
    
    # Set session state based on screen width at start
    if 'is_mobile' not in st.session_state:
        # Default to desktop view initially
        st.session_state['is_mobile'] = False
        
    # Add extra JavaScript to ensure tip-chips are fully visible in all modes
    st.markdown("""
    <script>
        // Function to ensure tip chips are visible
        function ensureTipChipsVisible() {
            document.querySelectorAll('.tip-chip').forEach(chip => {
                // Force color and font weight to ensure visibility
                chip.style.color = '#294237'; // Westin Basil
                chip.style.fontWeight = '600';
                
                // Add hover effect
chip.addEventListener('mouseout', function() {
                    this.style.backgroundColor = 'white';
                    this.style.color = '#294237'; // Westin Basil
                });
                
                // Handle dark mode
                if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
                    chip.style.backgroundColor = '#2c3e50';
                    chip.style.color = '#a7bdb3'; // Light Basil
                    chip.style.borderColor = '#294237'; // Westin Basil
                    
                    // Dark mode hover effect
                    chip.addEventListener('mouseover', function() {
                        this.style.backgroundColor = '#37516e';
                        this.style.color = '#a7bdb3'; // Light Basil
                    });
                    
                    chip.addEventListener('mouseout', function() {
                        this.style.backgroundColor = '#2c3e50';
                        this.style.color = '#a7bdb3'; // Light Basil
                    });
                }
            });
        }
        
        // Run after DOM is loaded
        document.addEventListener('DOMContentLoaded', ensureTipChipsVisible);
        
        // Also run after a slight delay to ensure all content is loaded
        setTimeout(ensureTipChipsVisible, 500);
    </script>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()