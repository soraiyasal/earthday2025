import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import random

# Set page config - must be first Streamlit command
st.set_page_config(
    page_title="Earth Day Hotel Race 2025", 
    page_icon="🏆", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Hide sidebar and add colorful styling
st.markdown("""
<style>
    /* Hide sidebar controls */
    [data-testid="collapsedControl"] {display: none;}
    section[data-testid="stSidebar"] {display: none !important;}
    
    /* Colorful progress bars */
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #00a74a, #4b70b3);
    }
    
    /* Eye-catching header */
    h1 {
        background: linear-gradient(to right, #00a74a, #4b70b3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem !important;
        text-align: center;
        margin-bottom: 20px;
    }
    
    /* Bold metrics */
    [data-testid="stMetricValue"] {
        font-size: 3rem !important;
        color: #002d72;
    }
</style>
""", unsafe_allow_html=True)

# MPAN to Hotel mapping
mpan_to_hotel = {
    "2500021277783": "Westin", 
    "1200051315859": "Camden", 
    "2500021281362": "Canopy",
    "1200052502710": "EH", 
    "1050000997145": "St Albans"
}

# Fun hotel emojis for visual distinction
hotel_emojis = {
    "Westin": "🌲", 
    "Camden": "🏙️", 
    "Canopy": "🌴",
    "EH": "🏰", 
    "St Albans": "⛪"
}

# Hotel colors for consistent visualization
hotel_colors = {
    "Westin": "#164b35", 
    "Camden": "#8764b8", 
    "Canopy": "#ff7800",
    "EH": "#00205c", 
    "St Albans": "#002d72"
}

# Electricity factors
ELECTRICITY_FACTOR = 0.00020493  # 2024/2025 factor

# Top energy saving tips - super simple
energy_tips = [
    {"emoji": "💡", "tip": "Turn off lights"},
    {"emoji": "🌡️", "tip": "Adjust temperature 1°"},
    {"emoji": "🚿", "tip": "Shorter showers"},
    {"emoji": "🔌", "tip": "Unplug devices"},
    {"emoji": "⚡", "tip": "Report energy waste"}
]

# Load data from SQLite database or generate simulated data
@st.cache_data(show_spinner=False)
def load_data():
    try:
        conn = sqlite3.connect('electricity_data.db')
        
        # Load data for all hotels
        query = """
        SELECT strftime('%Y-%m-%d', Date) as Date,
               [Meter Point],
               [Total Usage]
        FROM hh_data
        ORDER BY Date
        """
        
        data = pd.read_sql_query(query, conn)
        data['Date'] = pd.to_datetime(data['Date'])
        
        # Map MPAN to hotel name
        data["Meter Point"] = data["Meter Point"].astype(str)
        data["Hotel"] = data["Meter Point"].map(mpan_to_hotel)
        
        # Ensure Total Usage is numeric
        data['Total Usage'] = pd.to_numeric(data['Total Usage'], errors='coerce').fillna(0)
        
        # Extract year from date
        data['Year'] = data['Date'].dt.year
        
        return data
        
    except Exception as e:
        st.error(f"Error: {str(e)}")
        # Return simulated data if database fails
        return generate_simulated_data()
    finally:
        if 'conn' in locals():
            conn.close()

# Generate simulated data for testing
def generate_simulated_data():
    # Create date range for the last 2 years
    end_date = datetime.today()
    start_date = end_date - timedelta(days=365*2)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    # List of hotels
    hotels = list(mpan_to_hotel.values())
    
    # Generate data for each hotel
    all_data = []
    
    for hotel in hotels:
        # Base usage varies by hotel (some more efficient than others)
        if hotel == "Westin":
            base_usage = 180  # More efficient
        elif hotel == "Camden":
            base_usage = 220  # Less efficient
        elif hotel == "Canopy":
            base_usage = 200
        elif hotel == "EH":
            base_usage = 190
        else:  # St Albans
            base_usage = 210
            
        # Get MPAN for this hotel
        hotel_mpan = next((mpan for mpan, h in mpan_to_hotel.items() if h == hotel), "unknown")
            
        # Different improvement rates for each hotel
        if hotel == "Westin":
            improvement_factor = 0.82  # 18% improvement
        elif hotel == "Camden":
            improvement_factor = 0.95  # 5% improvement
        elif hotel == "Canopy":
            improvement_factor = 0.88  # 12% improvement
        elif hotel == "EH":
            improvement_factor = 0.90  # 10% improvement
        else:  # St Albans
            improvement_factor = 0.85  # 15% improvement
        
        # Simulate different data availability for each hotel
        if hotel == "Camden":
            # Camden has data up to April 16
            hotel_end_date = datetime(2025, 4, 16) if end_date > datetime(2025, 4, 16) else end_date
        elif hotel == "Westin":
            # Westin has data up to April 15
            hotel_end_date = datetime(2025, 4, 15) if end_date > datetime(2025, 4, 15) else end_date
        else:
            # Other hotels have data up to today
            hotel_end_date = end_date
            
        hotel_dates = pd.date_range(start=start_date, end=hotel_end_date, freq='D')
        
        for date in hotel_dates:
            # Seasonal factor (higher in winter, lower in summer)
            month = date.month
            season_factor = 1.0 + 0.3 * np.cos((month - 1) * np.pi / 6)
            
            # Weekend factor (higher on weekends)
            weekend_factor = 1.2 if date.weekday() >= 5 else 1.0
            
            # Year factor (current year uses less energy than previous based on hotel's improvement)
            year_factor = improvement_factor if date.year == datetime.today().year else 1.0
            
            # Combine factors with random noise
            daily_usage = base_usage * season_factor * weekend_factor * year_factor * np.random.uniform(0.9, 1.1)
            
            # Create a row for this hotel and date
            row = {
                'Date': date,
                'Meter Point': hotel_mpan,
                'Hotel': hotel,
                'Total Usage': daily_usage,
                'Year': date.year
            }
                
            all_data.append(row)
    
    # Create DataFrame from all rows
    return pd.DataFrame(all_data)

# Find what dates all hotels have data for
def find_available_dates(data, year):
    """
    Find the dates where all hotels have data for a given year
    """
    year_data = data[data['Year'] == year]
    all_hotels = list(mpan_to_hotel.values())
    
    # Get all unique dates in the year
    all_dates = sorted(year_data['Date'].unique())
    
    # For each date, check if all hotels have data
    available_dates = []
    for date in all_dates:
        # Get hotels with data for this date
        hotels_with_data = year_data[year_data['Date'] == date]['Hotel'].unique()
        
        # If all hotels have data for this date, add it to the list
        if all(hotel in hotels_with_data for hotel in all_hotels):
            # Convert to Python datetime object
            if isinstance(date, np.datetime64):
                date = pd.Timestamp(date).to_pydatetime()
            elif isinstance(date, pd.Timestamp):
                date = date.to_pydatetime()
                
            available_dates.append(date)
    
    return sorted(available_dates)

# Find matching days between years
def find_matching_days(data, current_year, previous_year, start_date=None, end_date=None):
    """
    Find days that all hotels have data for in both years
    """
    # Get available dates for each year
    current_year_dates = find_available_dates(data, current_year)
    previous_year_dates = find_available_dates(data, previous_year)
    
    # Convert numpy.datetime64 objects to Python datetime objects if needed
    current_year_dates = [pd.Timestamp(date).to_pydatetime() for date in current_year_dates]
    previous_year_dates = [pd.Timestamp(date).to_pydatetime() for date in previous_year_dates]
    
    # Create month-day format for matching (ignoring year)
    current_year_month_days = [date.strftime('%m-%d') for date in current_year_dates]
    previous_year_month_days = [date.strftime('%m-%d') for date in previous_year_dates]
    
    # Find common month-days
    common_keys = set(current_year_month_days).intersection(previous_year_month_days)
    
    # Filter to matching days only
    matching_current_dates = [date for date in current_year_dates if date.strftime('%m-%d') in common_keys]
    matching_previous_dates = [date for date in previous_year_dates if date.strftime('%m-%d') in common_keys]
    
    # If a date range is specified, filter to that range
    if start_date and end_date:
        matching_current_dates = [date for date in matching_current_dates if start_date <= date <= end_date]
        
        # Get corresponding dates from previous year
        month_days_in_range = [date.strftime('%m-%d') for date in matching_current_dates]
        matching_previous_dates = [date for date in matching_previous_dates if date.strftime('%m-%d') in month_days_in_range]
    
    return {
        'current_dates': sorted(matching_current_dates),
        'previous_dates': sorted(matching_previous_dates)
    }

# Calculate metrics using Canopy dashboard logic
def calculate_hotel_metrics(data, matched_dates):
    """
    Calculate simple metrics for each hotel using only the matched dates
    """
    # Target savings percentage
    target_savings_percent = 10
    
    # Get current and previous year dates
    current_dates = matched_dates['current_dates']
    previous_dates = matched_dates['previous_dates']
    
    if not current_dates or not previous_dates:
        return {}
    
    # Store results for each hotel
    metrics = {}
    
    # Get unique hotels
    hotels = mpan_to_hotel.values()
    
    # Calculate metrics for each hotel
    for hotel in hotels:
        # Filter data for this hotel
        hotel_data = data[data['Hotel'] == hotel]
        
        # Get current year data for matched days
        current_data = hotel_data[hotel_data['Date'].isin(current_dates)]
        
        # Get previous year data for matched days
        previous_data = hotel_data[hotel_data['Date'].isin(previous_dates)]
        
        # Calculate total usage
        current_total = current_data['Total Usage'].sum()
        previous_total = previous_data['Total Usage'].sum()
        
        # Calculate percent change - using Canopy calculation logic
        if previous_total == 0:
            percent_change = 0
        else:
            percent_change = ((current_total - previous_total) / previous_total) * 100
        
        # Calculate progress toward 10% savings goal - using Canopy calculation logic
        target_usage = previous_total * (1 - target_savings_percent/100)
        
        # If there are savings (current_total < previous_total)
        if current_total < previous_total:
            # Calculate how much of the 10% goal we've achieved
            # If we've saved exactly 10%, progress should be 100%
            # If we've saved less than 10%, progress should be proportional
            progress_percentage = min(100, ((previous_total - current_total) / (previous_total - target_usage)) * 100)
            kwh_saved = previous_total - current_total
        else:
            # No savings or increased usage
            progress_percentage = 0
            kwh_saved = 0
        
        # Store metrics
        metrics[hotel] = {
            'current_total': current_total,
            'previous_total': previous_total,
            'percent_change': percent_change,
            'progress_percentage': progress_percentage,
            'energy_reduction': abs(min(0, percent_change)),  # Only count negative percent changes as reductions
            'target_savings_percent': target_savings_percent,
            'kwh_saved': kwh_saved
        }
    
    return metrics

# Create a clear race bar chart
def create_simple_race_bar(metrics):
    # Sort hotels by energy reduction (higher reduction = better position)
    sorted_hotels = sorted(metrics.items(), key=lambda x: x[1]['energy_reduction'], reverse=True)
    
    # Create data for the chart
    hotel_names = []
    reductions = []
    progress_values = []
    colors = []
    
    for hotel, hotel_metrics in sorted_hotels:
        # Get the actual reduction percentage
        actual_reduction = hotel_metrics['energy_reduction']
        
        hotel_names.append(f"{hotel_emojis.get(hotel, '🏨')} {hotel}")
        reductions.append(actual_reduction)
        progress_values.append(hotel_metrics['progress_percentage'])
        colors.append(hotel_colors.get(hotel, '#002d72'))
    
    # Create figure
    fig = go.Figure()
    
    # Add bar for each hotel
    for i, hotel in enumerate(hotel_names):
        fig.add_trace(go.Bar(
            y=[hotel],
            x=[reductions[i]],
            orientation='h',
            marker_color=colors[i],
            text=[f"{reductions[i]:.1f}% reduction"],
            textposition='outside',
            hoverinfo='text',
            hovertext=[f"{hotel}: {reductions[i]:.1f}% reduction<br>{progress_values[i]:.0f}% of 10% goal"],
            name=hotel
        ))
    
    # Add finish line at 10%
    fig.add_shape(
        type="line",
        x0=10, y0=-0.5,
        x1=10, y1=len(hotel_names)-0.5,
        line=dict(
            color="red",
            width=3,
            dash="dash",
        )
    )
    
    # Add label for finish line
    fig.add_annotation(
        x=10,
        y=len(hotel_names),
        text="🏁 10% Goal",
        showarrow=False,
        font=dict(color="red", size=16),
        yshift=10
    )
    
    # Update layout
    fig.update_layout(
        title="Who's Saving the Most Energy?",
        xaxis_title="Energy Reduction (%)",
        margin=dict(l=10, r=60, t=40, b=10),
        height=350,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            range=[0, max(max(reductions)+2, 11)],
            gridcolor='#e6eef7',
        ),
        yaxis=dict(
            autorange='reversed'
        ),
        showlegend=False
    )
    
    return fig

# Create a simple weekly pattern chart
def create_weekly_pattern(data, current_start, current_end):
    # Filter data to current period
    period_data = data[(data['Date'] >= current_start) & (data['Date'] <= current_end)].copy()
    
    # Add day of week column
    period_data['day_of_week'] = period_data['Date'].dt.dayofweek
    period_data['day_name'] = period_data['Date'].dt.day_name()
    
    # Aggregate by day of week
    daily_totals = period_data.groupby(['day_of_week', 'day_name'])['Total Usage'].mean().reset_index()
    
    # Order days correctly
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    daily_totals['day_name'] = pd.Categorical(daily_totals['day_name'], categories=days_order, ordered=True)
    daily_totals = daily_totals.sort_values('day_name')
    
    # Create bar chart with gradient colors
    fig = px.bar(
        daily_totals, 
        x='day_name', 
        y='Total Usage',
        color='Total Usage',
        color_continuous_scale=['#e6f7e9', '#00a74a'],
        labels={'Total Usage': 'Energy (kWh)', 'day_name': ''},
        category_orders={"day_name": days_order},
        title="When Do We Use Most Energy?"
    )
    
    # Find highest usage day
    highest_day = daily_totals.loc[daily_totals['Total Usage'].idxmax(), 'day_name']
    lowest_day = daily_totals.loc[daily_totals['Total Usage'].idxmin(), 'day_name']
    
    # Add annotations for highest and lowest days
    fig.add_annotation(
        x=highest_day,
        y=daily_totals[daily_totals['day_name']==highest_day]['Total Usage'].iloc[0],
        text="Highest",
        showarrow=True,
        arrowhead=1,
        ax=0,
        ay=-40
    )
    
    fig.add_annotation(
        x=lowest_day,
        y=daily_totals[daily_totals['day_name']==lowest_day]['Total Usage'].iloc[0],
        text="Lowest",
        showarrow=True,
        arrowhead=1,
        ax=0,
        ay=-40
    )
    
    fig.update_layout(
        coloraxis_showscale=False,
        margin=dict(l=10, r=10, t=40, b=10),
        height=350,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=False
    )
    
    return fig, highest_day, lowest_day

# Main dashboard
def main():
    # Title with fun emoji
    st.title("🏆 Earth Day Hotel Race 2025")
    
    # Load data
    data = load_data()
    
    # Define time periods
    today = datetime.today()
    current_year = today.year
    previous_year = current_year - 1
    
    # Period selector with fun emojis
    col1, col2 = st.columns([1, 3])
    
    with col1:
        period = st.selectbox(
            "📅 Select time period",
            options=[
                "🔄 Year to Date",
                "🌍 Earth Day Challenge",
                "📊 Last 7 Days",
                "📈 Last 30 Days",
                "📆 This Month",
                "📆 Previous Month",
                "📆 January 2025",
                "📆 February 2025",
                "📆 March 2025",
                "📆 April 2025"
            ],
            index=1
        )
        
        period_text = period.split(" ", 1)[1]  # Remove the emoji prefix
    
    with col2:
        # Fun energy fact
        st.info("**💡 Did You Know?** " + random.choice([
            "A 1°C reduction in room temperature saves up to 8% on energy costs!",
            "Hotels typically spend 6-10% of their operating costs on energy!",
            "LED lights use up to 90% less energy than traditional bulbs!",
            "Only 3-5% of hotel guests choose to reuse towels - which uses a lot of energy!"
        ]))
    
    # Helper function to get month name based on period
    def get_month_name(period_str):
        if "January" in period_str:
            return "January"
        elif "February" in period_str:
            return "February"
        elif "March" in period_str:
            return "March"
        elif "April" in period_str:
            return "April"
        elif "This Month" in period_str:
            return datetime.today().strftime("%B")
        elif "Previous Month" in period_str:
            # Get the first day of current month, then go back one day to get previous month
            first_day_current_month = datetime(today.year, today.month, 1)
            last_day_prev_month = first_day_current_month - timedelta(days=1)
            return last_day_prev_month.strftime("%B")
        else:
            return None
    
    # Set date ranges based on selection
    if period_text == "Last 7 Days":
        period_end = today
        period_start = today - timedelta(days=7)
    elif period_text == "Last 30 Days":
        period_end = today
        period_start = today - timedelta(days=30)
    elif period_text == "Earth Day Challenge":
        period_end = datetime(2025, 4, 22)
        period_start = datetime(2025, 4, 15)
    elif period_text == "This Month":
        period_start = datetime(today.year, today.month, 1)
        period_end = today
    elif period_text == "Previous Month":
        # Get the first day of current month
        first_day_current_month = datetime(today.year, today.month, 1)
        # Then go back one day to get the last day of previous month
        last_day_prev_month = first_day_current_month - timedelta(days=1)
        # Then get the first day of previous month
        period_start = datetime(last_day_prev_month.year, last_day_prev_month.month, 1)
        period_end = last_day_prev_month
    elif period_text == "January 2025":
        period_start = datetime(2025, 1, 1)
        period_end = datetime(2025, 1, 31)
    elif period_text == "February 2025":
        period_start = datetime(2025, 2, 1)
        period_end = datetime(2025, 2, 28)  # Note: 2025 is not a leap year
    elif period_text == "March 2025":
        period_start = datetime(2025, 3, 1)
        period_end = datetime(2025, 3, 31)
    elif period_text == "April 2025":
        period_start = datetime(2025, 4, 1)
        period_end = datetime(2025, 4, 30)
    else:  # Year to Date
        period_end = today
        period_start = datetime(current_year, 1, 1)
    
    # Find days that have data for all hotels in both years
    matched_dates = find_matching_days(data, current_year, previous_year, period_start, period_end)
    
    # Calculate metrics using ONLY the matched days
    metrics = calculate_hotel_metrics(data, matched_dates)
    
    if not metrics:
        st.error("⚠️ No data available for this period.")
        st.stop()
    
    # Calculate overall metrics
    total_kwh_saved = sum(hotel_metrics['kwh_saved'] for hotel_metrics in metrics.values())
    
    # Get month name if it's a monthly comparison
    month_name = get_month_name(period)
    
    if month_name:
        date_text = f"{month_name} {current_year} vs {month_name} {previous_year}"
    else:
        date_text = f"{period_text} {current_year} vs {previous_year}"
    
    # Create 3 big metrics in a row
    metric1, metric2, metric3 = st.columns(3)
    
    with metric1:
        # Add date information
        if len(matched_dates['current_dates']) > 0:
            date_info = f"{matched_dates['current_dates'][0].strftime('%b %d')} - {matched_dates['current_dates'][-1].strftime('%b %d')}"
        else:
            date_info = "No matching days"
        
        st.metric(
            "Total Energy Saved",
            f"{total_kwh_saved:,.0f} kWh",
            f"Comparing {date_text}"
        )
    
    with metric2:
        # Calculate CO2 savings
        co2_saved = total_kwh_saved * ELECTRICITY_FACTOR
        st.metric(
            "CO₂ Emissions Avoided",
            f"{co2_saved:,.0f} kg",
            "Like planting trees!"
        )
    
    with metric3:
        # Calculate cost savings assuming £0.30 per kWh
        cost_saved = total_kwh_saved * 0.30
        st.metric(
            "Money Saved",
            f"£{cost_saved:,.0f}",
            "Better for the budget"
        )
    
    # Explanation about the goal
    st.markdown("""
    ### 🎯 Our Challenge: Save 10% Energy vs Last Year
    
    Each hotel is trying to reduce energy use by 10% compared to the same days last year.
    The hotel that reaches or exceeds 10% first wins the challenge!
    """)
    
    # 1. RACE VISUALIZATION
    race_chart = create_simple_race_bar(metrics)
    st.plotly_chart(race_chart, use_container_width=True)
    
    # Sort hotels by reduction
    sorted_hotels = sorted(metrics.items(), key=lambda x: x[1]['energy_reduction'], reverse=True)
    leader = sorted_hotels[0][0] if sorted_hotels else "None"
    leader_reduction = sorted_hotels[0][1]['energy_reduction'] if sorted_hotels else 0
    
    # Show leader and runner up
    st.markdown(f"**Current Leader:** {hotel_emojis.get(leader, '🏨')} **{leader}** with **{leader_reduction:.1f}%** energy reduction")
    
    # Create two columns for the remaining charts
    col1, col2 = st.columns(2)
    
    # Weekly Pattern Chart
    with col1:
        try:
            weekly_pattern, highest_day, lowest_day = create_weekly_pattern(data, period_start, period_end)
            st.plotly_chart(weekly_pattern, use_container_width=True)
            
            # Add simple insight
            st.markdown(f"**Tip:** Focus on saving energy on **{highest_day}s** when we use the most!")
        except Exception as e:
            st.error("Could not create pattern chart.")
    
    # Tips and Next Steps
    with col2:
        st.markdown("### 💡 Quick Energy-Saving Tips")
        
        # Create three columns for tips
        tip_cols = st.columns(3)
        
        # Add first three tips
        for i in range(3):
            if i < len(energy_tips):
                with tip_cols[i]:
                    st.markdown(f"### {energy_tips[i]['emoji']}")
                    st.markdown(f"**{energy_tips[i]['tip']}**")
        
        # Add more information
        st.markdown("### 🚀 What's Next?")
        st.markdown("""
        1. Share these insights with your team
        2. Focus on high-usage days
        3. Implement at least one tip this week
        4. Check back to see your progress!!
        """)
    
    # Footer info
    st.caption(f"Holiday Inn Hotels Earth Day Challenge | Showing data from {date_info} | {len(matched_dates['current_dates'])} days compared")

if __name__ == "__main__":
    main()