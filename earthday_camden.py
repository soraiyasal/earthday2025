# import streamlit as st
# import pandas as pd
# import numpy as np
# import plotly.express as px
# import plotly.graph_objects as go
# from datetime import datetime, timedelta
# import sqlite3
# import random

# # Set the specific hotel for this dashboard
# HOTEL_NAME = "Westin"  # Change this for each hotel's dashboard

# # MPAN to Hotel mapping
# mpan_to_hotel = {
#     "2500021277783": "Westin", 
#     "1200051315859": "Camden", 
#     "2500021281362": "Canopy",
#     "1200052502710": "EH", 
#     "1050000997145": "St Albans"
# }

# # Get MPAN for this hotel
# def get_hotel_mpan(hotel_name):
#     for mpan, hotel in mpan_to_hotel.items():
#         if hotel == hotel_name:
#             return mpan
#     return None

# HOTEL_MPAN = get_hotel_mpan(HOTEL_NAME)

# # Electricity factors
# ELECTRICITY_FACTOR = 0.20493  # 2024/2025 factor

# # Load data from SQLite database
# @st.cache_data(show_spinner=False)
# def load_data():
#     try:
#         conn = sqlite3.connect('electricity_data.db')
        
#         # If we have a valid MPAN for this hotel, filter by it
#         if HOTEL_MPAN:
#             query = f"""
#             SELECT strftime('%Y-%m-%d %H:%M:%S', Date) as Date,
#                    [Total Usage],
#                    "00:00","00:30","01:00","01:30","02:00","02:30","03:00","03:30",
#                    "04:00","04:30","05:00","05:30","06:00","06:30","07:00","07:30",
#                    "08:00","08:30","09:00","09:30","10:00","10:30","11:00","11:30",
#                    "12:00","12:30","13:00","13:30","14:00","14:30","15:00","15:30",
#                    "16:00","16:30","17:00","17:30","18:00","18:30","19:00","19:30",
#                    "20:00","20:30","21:00","21:30","22:00","22:30","23:00","23:30"
#             FROM hh_data
#             WHERE [Meter Point] = '{HOTEL_MPAN}'
#             ORDER BY Date
#             """
#         else:
#             # If no MPAN is found, load data without filtering
#             query = """
#             SELECT strftime('%Y-%m-%d %H:%M:%S', Date) as Date,
#                    [Meter Point],
#                    [Total Usage],
#                    "00:00","00:30","01:00","01:30","02:00","02:30","03:00","03:30",
#                    "04:00","04:30","05:00","05:30","06:00","06:30","07:00","07:30",
#                    "08:00","08:30","09:00","09:30","10:00","10:30","11:00","11:30",
#                    "12:00","12:30","13:00","13:30","14:00","14:30","15:00","15:30",
#                    "16:00","16:30","17:00","17:30","18:00","18:30","19:00","19:30",
#                    "20:00","20:30","21:00","21:30","22:00","22:30","23:00","23:30"
#             FROM hh_data
#             ORDER BY Date
#             """
        
#         # Load the data with explicit date handling
#         data = pd.read_sql_query(query, conn)
        
#         # Convert Date column to datetime explicitly
#         data['Date'] = pd.to_datetime(data['Date'])
        
#         # If we didn't filter by MPAN, filter the data after loading
#         if not HOTEL_MPAN and 'Meter Point' in data.columns:
#             # Convert Meter Point to string for proper comparison
#             data["Meter Point"] = data["Meter Point"].astype(str)
            
#             # Create a hotel column
#             data["Hotel"] = data["Meter Point"].map(mpan_to_hotel)
            
#             # Filter for this hotel
#             data = data[data["Hotel"] == HOTEL_NAME]
        
#         # Ensure numeric values for time columns and Total Usage
#         time_cols = [f"{str(hour).zfill(2)}:{minute}" 
#                     for hour in range(24) 
#                     for minute in ['00', '30']]
#         for col in time_cols + ['Total Usage']:
#             data[col] = pd.to_numeric(data[col], errors='coerce').fillna(0)
        
#         # Extract year from date for easier filtering
#         data['Year'] = data['Date'].dt.year
        
#         return data
        
#     except Exception as e:
#         st.error(f"Error: {str(e)}")
#         # Return simulated data if database fails
#         return generate_simulated_data()
#     finally:
#         if 'conn' in locals():
#             conn.close()

# # Generate simulated data for testing or when database fails
# def generate_simulated_data():
#     # Create date range for the last 2 years
#     end_date = datetime.today()
#     start_date = end_date - timedelta(days=365*2)
#     dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
#     # Generate realistic usage data with seasonal patterns and year-over-year improvement
#     base_usage = 200  # Base kWh per day
    
#     # Create data with seasonal patterns and weekday/weekend variation
#     usage_data = []
#     for date in dates:
#         # Seasonal factor (higher in winter, lower in summer)
#         month = date.month
#         season_factor = 1.0 + 0.3 * np.cos((month - 1) * np.pi / 6)
        
#         # Weekend factor (higher on weekends)
#         weekend_factor = 1.2 if date.weekday() >= 5 else 1.0
        
#         # Year factor (current year uses less energy than previous)
#         year_factor = 0.85 if date.year == datetime.today().year else 1.0
        
#         # Combine factors with random noise
#         daily_usage = base_usage * season_factor * weekend_factor * year_factor * random.uniform(0.9, 1.1)
        
#         usage_data.append(daily_usage)
    
#     # Create dataframe
#     data = pd.DataFrame({
#         'Date': dates,
#         'Total Usage': usage_data,
#         'Year': [d.year for d in dates]
#     })
    
#     # Add time columns (not used in this view, but included for compatibility)
#     time_cols = [f"{str(hour).zfill(2)}:{minute}" 
#                 for hour in range(24) 
#                 for minute in ['00', '30']]
    
#     for col in time_cols:
#         data[col] = 0
    
#     return data

# # Get compare dates from previous year
# def get_comparative_period(current_start, current_end):
#     # Get same period from last year
#     days_diff = (current_end - current_start).days
#     last_year_end = current_end - pd.DateOffset(years=1)
#     last_year_start = last_year_end - timedelta(days=days_diff)
    
#     return last_year_start, last_year_end

# # Generate hourly usage data 
# def generate_hourly_data(data):
#     time_cols = [f"{str(hour).zfill(2)}:{minute}" 
#                 for hour in range(24) 
#                 for minute in ['00', '30']]
    
#     # Calculate average usage for each half-hour slot
#     hourly_usage = data[time_cols].mean().reset_index()
#     hourly_usage.columns = ['time', 'usage']
    
#     # Convert time to hour label
#     hourly_usage['hour'] = hourly_usage['time'].apply(lambda x: int(x.split(':')[0]))
#     hourly_usage['label'] = hourly_usage['hour'].apply(lambda x: f"{x}:00")
    
#     return hourly_usage

# # Get KPIs for the comparison period
# def get_comparison_kpis(data, current_start, current_end, compare_start, compare_end):
#     # Filter for current period
#     current_data = data[(data['Date'] >= current_start) & (data['Date'] <= current_end)]
    
#     # Filter for comparison period
#     compare_data = data[(data['Date'] >= compare_start) & (data['Date'] <= compare_end)]
    
#     # Calculate metrics
#     current_total = current_data['Total Usage'].sum()
#     compare_total = compare_data['Total Usage'].sum()
    
#     # Handle edge case where compare_total is 0
#     if compare_total == 0:
#         percent_change = 0
#     else:
#         percent_change = ((current_total - compare_total) / compare_total) * 100
    
#     # Calculate daily averages
#     current_daily_avg = current_data['Total Usage'].mean()
#     compare_daily_avg = compare_data['Total Usage'].mean()
    
#     # Calculate CO2 impact
#     co2_saved = (compare_total - current_total) * ELECTRICITY_FACTOR
    
#     return {
#         'current_total': current_total,
#         'compare_total': compare_total,
#         'percent_change': percent_change,
#         'current_daily_avg': current_daily_avg,
#         'compare_daily_avg': compare_daily_avg,
#         'co2_saved': max(0, co2_saved),  # Only positive values for CO2 saved
#         'kwh_saved': max(0, compare_total - current_total)
#     }

# # Main dashboard
# def main():
#     # Page config
#     st.set_page_config(
#         page_title=f"{HOTEL_NAME} - Earth Day 2025", 
#         page_icon="🌍", 
#         layout="wide"
#     )
    
#     # Load custom CSS
#     st.markdown("""
#     <style>
#         /* Main header styling */
#         .header-container {
#             background-color: #065f46;
#             padding: 1.2rem;
#             border-radius: 0.75rem;
#             color: white;
#             text-align: center;
#             margin-bottom: 2rem;
#             box-shadow: 0 4px 6px rgba(0,0,0,0.1);
#         }
#         .header-title {
#             font-size: 2.5rem;
#             font-weight: 700;
#             margin: 0;
#             color: white;
#         }
#         .header-subtitle {
#             font-size: 1.2rem;
#             margin: 0;
#             opacity: 0.9;
#         }
        
#         # /* KPI section container */
#         # .kpi-section {
#         #     margin-bottom: 2rem;
#         #     background-color: #f9fafb;
#         #     padding: 1.5rem;
#         #     border-radius: 0.75rem;
#         #     box-shadow: 0 4px 12px rgba(0,0,0,0.05);
#         # }
        

#         .card {
#             background-color: white;
#             border-radius: 0.75rem;
#             padding: 1.5rem;
#             box-shadow: 0 4px 12px rgba(0,0,0,0.08);
#             border: 1px solid #f0f0f0;
#             margin-bottom: 1rem;
#             transition: transform 0.2s, box-shadow 0.2s;
#             height: 200px; /* Fixed height for all cards */
#             display: flex;
#             flex-direction: column;
#             justify-content: space-between; /* Distribute space evenly */
#         }
#         .card:hover {
#             transform: translateY(-2px);
#             box-shadow: 0 6px 16px rgba(0,0,0,0.1);
#         }
#         /* Custom metric styling */
#         .metric-label {
#             font-size: 1rem;
#             color: #6B7280;
#             margin-bottom: 0.5rem;
#         }
#         .metric-value {
#             font-size: 2.25rem;
#             font-weight: 700;
#             color: #1F2937;
#             margin: 0.6rem 0;
#         }
#         .metric-delta {
#             font-size: 0.95rem;
#             color: #059669; /* Green for positive change */
#             font-weight: 600; /* Make the text bolder */
#             padding: 0.25rem 0.5rem;
#             background-color: #ECFDF5; /* Light green background */
#             border-radius: 0.5rem;
#             display: inline-block; /* Ensure the background only covers the text */
#         }
#         .metric-delta.negative {
#             color: #dc2626; /* Red for negative change */
#             background-color: #FEE2E2; /* Light red background */
#         }
#         .metric-caption {
#             font-size: 0.9rem;
#             color: #6B7280;
#             margin-top: 0.5rem;
#         }
#         /* Charts row styling */
#         .charts-section {
#             margin-bottom: 2rem;
#             display: flex;
#             gap: 1.5rem;
#         }
        
#         /* Section styling */
#         # .section-container {
#         #     background-color: white;
#         #     border-radius: 0.75rem;
#         #     padding: 1.25rem;
#         #     box-shadow: 0 4px 12px rgba(0,0,0,0.08);
#         #     margin-bottom: 1.5rem;
#         #     border: 1px solid #f0f0f0;
#         # }
#         .section-title {
#             font-size: 1.25rem;
#             font-weight: 600;
#             margin-top: 0;
#             margin-bottom: 1rem;
#             color: #1F2937;
#         }
        
#         /* Champion styling */
#         .champion-container {
#             background-color: #ecfdf5;
#             border-radius: 0.75rem;
#             padding: 1.25rem;
#             box-shadow: 0 4px 12px rgba(0,0,0,0.08);
#             display: flex;
#             align-items: center;
#             gap: 1.25rem;
#             border: 1px solid #A7F3D0;
#         }
#         .champion-info {
#             flex: 1;
#         }
#         .champion-info h3 {
#             margin-top: 0;
#             margin-bottom: 0.5rem;
#             color: #065f46;
#         }
#         .champion-info p {
#             margin: 0;
#             line-height: 1.5;
#             color: #065f46;
#         }
#         .champion-photo {
#             width: 100px;
#             height: 100px;
#             border-radius: 50%;
#             object-fit: cover;
#             border: 3px solid #059669;
#             box-shadow: 0 4px 8px rgba(5, 150, 105, 0.2);
#         }
        
#         /* Challenge progress */
#         # .progress-container {
#         #     background-color: #f9fafb;
#         #     border-radius: 0.75rem;
#         #     padding: 1.25rem;
#         #     box-shadow: 0 4px 12px rgba(0,0,0,0.08);
#         #     margin-bottom: 1.5rem;
#         #     border: 1px solid #f0f0f0;
#         # }
#         # .progress-container h3 {
#         #     color: #1F2937;
#         #     margin-top: 0;
#         #     margin-bottom: 0.75rem;
#         # }
#         .progress-bar-bg {
#             height: 24px;
#             background-color: #e5e7eb;
#             border-radius: 9999px;
#             margin: 0.75rem 0;
#             overflow: hidden;
#         }
#         .progress-bar {
#             height: 24px;
#             background-color: #059669;
#             border-radius: 9999px;
#             display: flex;
#             align-items: center;
#             justify-content: center;
#             color: white;
#             font-weight: bold;
#             transition: width 1s ease-in-out;
#         }
        
#         /* Energy tips */
#         .tips-section {
#             background-color: #f0fdf4;
#             padding: 1.5rem;
#             border-radius: 0.75rem;
#             margin-bottom: 2rem;
#             box-shadow: 0 4px 12px rgba(0,0,0,0.08);
#             border: 1px solid #A7F3D0;
#         }
#         .tips-section h3 {
#             margin-top: 0;
#             margin-bottom: 0.75rem;
#             color: #065f46;
#             font-size: 1.25rem;
#             font-weight: 600;
#         }
#         .tips-container {
#             display: flex;
#             flex-wrap: wrap;
#             gap: 0.75rem;
#             margin-top: 0.75rem;
#         }
#         .tip-chip {
#             background-color: white;
#             padding: 0.5rem 1rem;
#             border-radius: 9999px;
#             font-size: 0.9rem;
#             white-space: nowrap;
#             box-shadow: 0 2px 4px rgba(0,0,0,0.05);
#             border: 1px solid #d1fae5;
#             transition: transform 0.2s;
#         }
#         .tip-chip:hover {
#             transform: translateY(-2px);
#             box-shadow: 0 4px 6px rgba(0,0,0,0.1);
#             background-color: #ecfdf5;
#         }
        
#         /* Chart container */
#         # .chart-container {
#         #     background-color: white;
#         #     border-radius: 0.75rem;
#         #     padding: 1.25rem;
#         #     box-shadow: 0 4px 12px rgba(0,0,0,0.08);
#         #     margin-bottom: 1.5rem;
#         #     border: 1px solid #f0f0f0;
#         #     height: 100%;
#         # }
        
#         /* Footer */
#         .footer {
#             text-align: center;
#             margin-top: 2.5rem;
#             color: #9CA3AF;
#             font-size: 0.8rem;
#             padding-bottom: 1rem;
#         }
        
#         /* Fix for Streamlit's default margins */
#         .block-container {
#             padding-top: 1rem;
#             padding-bottom: 1rem;
#             max-width: 1200px; /* Adjust as needed */
#         }
        
#         /* Fix for plot background */
#         .js-plotly-plot .plotly .main-svg
#             background-color: transparent !important;
#         }
        
#         /* Responsive fixes for small screens */
#         @media (max-width: 768px) {
#             .kpi-value {
#                 font-size: 1.75rem;
#             }
#             .kpi-label {
#                 font-size: 0.8rem;
#             }
#             .champion-container {
#                 flex-direction: column;
#                 text-align: center;
#             }
#             .champion-photo {
#                 margin-bottom: 0.75rem;
#             }
#             .charts-section {
#                 flex-direction: column;
#             }
#         }
#     </style>
#     """, unsafe_allow_html=True)
    
#     # Header
#     # Header
#     st.markdown("""
#     <div class="header-container">
#         <h1 class="header-title"> 🌍 {0} Celebrates Earth Day</h1>
#         <p class="header-subtitle">Our Planet, Our Power | April 14-21, 2025</p>
#     </div>
#     """.format(HOTEL_NAME), unsafe_allow_html=True)
#     # Load data
#     data = load_data()
    
#     if len(data) == 0:
#         st.warning(f"No data found for {HOTEL_NAME}. Please check your hotel name and MPAN mapping.")
#         st.stop()
    
#     # Define time periods
#     today = datetime.today()
    
#     # For Earth Day challenge
#     challenge_start = datetime(2025, 4, 14)
#     challenge_end = datetime(2025, 4, 21)
    
#     # For current view (last 30 days by default)
#     current_end = today
#     current_start = today - timedelta(days=30)
    
#     # Get comparison period (same days last year)
#     compare_start, compare_end = get_comparative_period(current_start, current_end)
    
#     # Calculation section
#     with st.sidebar:
#         st.subheader(f"{HOTEL_NAME} Hotel")
        
#         # Time period selector
#         period = st.selectbox(
#             "Select Time Period:",
#             [
#                 "Last 30 Days", 
#                 "Last 7 Days", 
#                 "Year to Date", 
#                 "Earth Day Challenge Period"
#             ]
#         )
        
#         if period == "Last 7 Days":
#             current_end = today
#             current_start = today - timedelta(days=7)
#         elif period == "Year to Date":
#             current_end = today
#             current_start = datetime(today.year, 1, 1)
#         elif period == "Earth Day Challenge Period":
#             # Use either actual dates if we're past Earth Day 2025 or projected dates
#             if today > challenge_end:
#                 current_start = challenge_start
#                 current_end = challenge_end
#             else:
#                 # If we're before the challenge, use the dates from last year + a projected 15% improvement
#                 current_start = challenge_start - timedelta(days=365)
#                 current_end = challenge_end - timedelta(days=365)
#                 st.info("Showing projected data for upcoming Earth Day Challenge")
        
#         # Recalculate comparison period
#         compare_start, compare_end = get_comparative_period(current_start, current_end)
        
#         # Display date ranges for clarity
#         st.caption(f"Current: {current_start.strftime('%b %d, %Y')} - {current_end.strftime('%b %d, %Y')}")
#         st.caption(f"Compare: {compare_start.strftime('%b %d, %Y')} - {compare_end.strftime('%b %d, %Y')}")
    
#     # Get KPIs for the selected periods
#     kpis = get_comparison_kpis(data, current_start, current_end, compare_start, compare_end)
    
#     # KPI section with improved container
# # KPI section using st.metric


#     # KPI section using custom HTML metrics inside cards
#     # KPI section using custom HTML metrics inside cards
#     st.markdown('<div class="kpi-section">', unsafe_allow_html=True)
#     kpi_cols = st.columns(4)

#     with kpi_cols[0]:
#         # For percent change, negative is bad (increase in usage), positive is good (reduction in usage)
#         change_color = "negative" if kpis['percent_change'] > 0 else ""
#         st.markdown(f"""
#         <div class="card">
#             <div>
#                 <p class="metric-label">📊 COMPARED TO LAST YEAR</p>
#                 <p class="metric-value">{abs(kpis['percent_change']):.1f}%</p>
#                 <p class="metric-delta {change_color}">{"INCREASE" if kpis['percent_change'] > 0 else "REDUCTION"}</p>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

#     with kpi_cols[1]:
#         # Energy saved is always positive and good
#         st.markdown(f"""
#         <div class="card">
#             <div>
#                 <p class="metric-label">💡 ENERGY SAVED</p>
#                 <p class="metric-value">{kpis['kwh_saved']:,.0f} kWh</p>
#                 <p class="metric-delta">VS SAME PERIOD LAST YEAR</p>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

#     with kpi_cols[2]:
#         # CO₂ prevented is always positive and good
#         st.markdown(f"""
#         <div class="card">
#             <div>
#                 <p class="metric-label">🌍 CO₂ PREVENTED</p>
#                 <p class="metric-value">{kpis['co2_saved']:,.0f} kg</p>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

#     with kpi_cols[3]:
#         # For daily average, negative change is bad (increase), positive is good (reduction)
#         daily_change = ((kpis['current_daily_avg'] - kpis['compare_daily_avg']) / kpis['compare_daily_avg']) * 100
#         change_color = "negative" if daily_change > 0 else ""
#         st.markdown(f"""
#         <div class="card">
#             <div>
#                 <p class="metric-label">📅 DAILY AVERAGE</p>
#                 <p class="metric-value">{kpis['current_daily_avg']:,.0f} kWh</p>
#                 <p class="metric-delta {change_color}">{abs(daily_change):.1f}% vs last year</p>
#             </div>
#         </div>
#         """, unsafe_allow_html=True)

#     st.markdown('</div>', unsafe_allow_html=True)

#     st.markdown('<div class="section-container">', unsafe_allow_html=True)
#     st.markdown('<h3 class="section-title">Green Champion</h3>', unsafe_allow_html=True)

#     st.markdown("""
#     <div class="champion-container">
#         <img src="https://ui-avatars.com/api/?name=Jekarerina+Gayatri&background=10B981&color=fff&size=100" class="champion-photo">
#         <div class="champion-info">
#             <h3>Jekaterina & Gayatri</h3>
#             <p>"Let's outperform our target! Find me at reception for energy-saving tips."</p>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)
#     st.markdown('</div>', unsafe_allow_html=True)

#     # Earth Day Challenge Section
#     st.markdown('<div class="progress-container">', unsafe_allow_html=True)
#     st.markdown('<h3>Earth Day Challenge</h3>', unsafe_allow_html=True)

#     # Calculate challenge progress values
#     days_until = (challenge_start - today).days
    
#     if days_until > 0:
#         # Before challenge
#         progress_pct = 0
#         progress_label = f"Starts in {days_until} days"
#     elif days_until <= 0 and days_until > -8:
#         # During challenge
#         day_of_challenge = abs(days_until) + 1
#         progress_pct = min(100, (day_of_challenge / 8) * 100)
#         progress_label = f"Day {day_of_challenge} of 8"
#     else:
#         # After challenge
#         progress_pct = 100
#         progress_label = "Challenge Complete"

#     # # Progress bar
#     # st.markdown(f"""
#     # <div class="progress-bar-bg">
#     #     # <div class="progress-bar" style="width: {progress_pct}%;">{progress_label}</div>
#     # </div>
#     # """, unsafe_allow_html=True)
#     # st.markdown('</div>', unsafe_allow_html=True)

#     # Energy-saving tips with improved layout
#     st.markdown("""
#     <div class="tips-section">
#         <h3>Quick Energy-Saving Tips</h3>
#         <div class="tips-container">
#             <div class="tip-chip">💡 Turn off lights when leaving</div>
#             <div class="tip-chip">🚿 Shorter showers save water & energy</div>
#             <div class="tip-chip">🌡️ Keep thermostat at optimal 21-23°C</div>
#             <div class="tip-chip">☀️ Use natural light during daytime</div>
#             <div class="tip-chip">🔌 Unplug chargers when not in use</div>
#             <div class="tip-chip">🚶‍♂️ Take stairs instead of elevator</div>
#             <div class="tip-chip">🧺 Re-use towels to reduce laundry</div>
#             <div class="tip-chip">💧 Report water leaks immediately</div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

#     # Update the charts layout with improved container
#     st.markdown('<div class="charts-section">', unsafe_allow_html=True)
#     chart_cols = st.columns(2)  # Two columns for side-by-side layout

#     # Year-over-Year Comparison Graph (Left Column)
#     with chart_cols[0]:
#         st.markdown('<div class="chart-container">', unsafe_allow_html=True)
#         st.markdown('<h3 class="section-title">Year-over-Year Comparison</h3>', unsafe_allow_html=True)
        
#         # Filter data for the selected periods
#         current_period_data = data[(data['Date'] >= current_start) & (data['Date'] <= current_end)]
#         compare_period_data = data[(data['Date'] >= compare_start) & (data['Date'] <= compare_end)]
        
#         # Normalize dates to be able to plot them on the same x-axis
#         current_period_data = current_period_data.copy()
#         compare_period_data = compare_period_data.copy()
        
#         # Create day index (0 to n) for both periods
#         current_period_data['Day_Index'] = (current_period_data['Date'] - current_start).dt.days
#         compare_period_data['Day_Index'] = (compare_period_data['Date'] - compare_start).dt.days
        
#         # Create a date range for the x-axis
#         day_count = (current_end - current_start).days + 1
#         day_range = [current_start + timedelta(days=i) for i in range(day_count)]
        
#         # Create plot
#         fig = go.Figure()
        
#         # Add current period line
#         fig.add_trace(go.Scatter(
#             x=current_period_data['Day_Index'], 
#             y=current_period_data['Total Usage'],
#             name=f'This Year',
#             line=dict(color='#059669', width=3),
#             hovertemplate='%{y:.0f} kWh'
#         ))
        
#         # Add comparison period line
#         fig.add_trace(go.Scatter(
#             x=compare_period_data['Day_Index'], 
#             y=compare_period_data['Total Usage'],
#             name=f'Last Year',
#             line=dict(color='#6B7280', width=2, dash='dash'),
#             hovertemplate='%{y:.0f} kWh'
#         ))
        
#         # Add shaded area for the difference
#         # Only include if we have data for both periods
#         if not current_period_data.empty and not compare_period_data.empty:
#             # Merge on day index
#             merged_data = pd.merge(
#                 current_period_data[['Day_Index', 'Total Usage']],
#                 compare_period_data[['Day_Index', 'Total Usage']],
#                 on='Day_Index',
#                 how='inner',
#                 suffixes=('_current', '_compare')
#             )
            
#             # Only add the saving area if current usage is less than comparison
#             if kpis['percent_change'] < 0:
#                 fig.add_trace(go.Scatter(
#                     x=merged_data['Day_Index'],
#                     y=merged_data['Total Usage_compare'],
#                     fill=None,
#                     mode='lines',
#                     line=dict(width=0),
#                     showlegend=False,
#                     hoverinfo='skip'
#                 ))
                
#                 fig.add_trace(go.Scatter(
#                     x=merged_data['Day_Index'],
#                     y=merged_data['Total Usage_current'],
#                     fill='tonexty',
#                     mode='lines',
#                     line=dict(width=0),
#                     fillcolor='rgba(5, 150, 105, 0.2)',
#                     name='Energy Saved',
#                     hoverinfo='skip'
#                 ))
        
#         # Configure x-axis with actual dates instead of indices
#         date_labels = [date.strftime("%b %d") for date in day_range]
#         tick_indices = list(range(0, day_count, max(1, day_count // 10)))  # Show about 10 ticks
        
#         fig.update_layout(
#             xaxis=dict(
#                 tickmode='array',
#                 tickvals=tick_indices,
#                 ticktext=[date_labels[i] for i in tick_indices],
#                 title='Date',
#                 gridcolor='#f0f0f0'
#             ),
#             yaxis=dict(
#                 title='Energy Usage (kWh)',
#                 gridcolor='#f0f0f0'
#             ),
#             legend=dict(
#                 orientation='h',
#                 yanchor='bottom',
#                 y=1.02,
#                 xanchor='right',
#                 x=1,
#                 bgcolor='rgba(255,255,255,0.8)',
#                 bordercolor='#f0f0f0',
#                 borderwidth=1
#             ),
#             margin=dict(l=20, r=20, t=10, b=30),
#             height=450,  # Increased height
#             plot_bgcolor='rgba(0,0,0,0)',
#             paper_bgcolor='rgba(0,0,0,0)',
#             hovermode='x unified'
#         )
        
#         st.plotly_chart(fig, use_container_width=True)
#         st.markdown('</div>', unsafe_allow_html=True)

#     # Peak Energy Hours Graph (Right Column)
#     with chart_cols[1]:
#         st.markdown('<div class="chart-container">', unsafe_allow_html=True)
#         st.markdown('<h3 class="section-title">Peak Energy Hours</h3>', unsafe_allow_html=True)
        
#         try:
#             # Generate hourly data
#             hourly_data = generate_hourly_data(data)
            
#             # Find top 3 peak hours
#             top_hours = hourly_data.nlargest(3, 'usage')

#             # Create hourly chart
#             hour_fig = px.bar(
#                 hourly_data,
#                 x='label',
#                 y='usage',
#                 color='usage',
#                 color_continuous_scale='Viridis',
#                 labels={'usage': 'Energy (kWh)', 'label': 'Hour'}
#             )
            
#             # Show only every 3rd hour to avoid crowding
#             show_labels = hourly_data['label'].iloc[::3].tolist()
#             hour_fig.update_layout(
#                 coloraxis_showscale=False,
#                 height=450,  # Match height with the other graph
#                 margin=dict(l=20, r=20, t=10, b=30),
#                 plot_bgcolor='rgba(0,0,0,0)',
#                 paper_bgcolor='rgba(0,0,0,0)',
#                 xaxis=dict(
#                     tickmode='array',
#                     tickvals=show_labels,
#                     ticktext=show_labels,
#                     title='Hour',
#                     gridcolor='#f0f0f0'
#                 ),
#                 yaxis=dict(
#                     title='Energy (kWh)',
#                     gridcolor='#f0f0f0'
#                 ),
#                 hoverlabel=dict(
#                     bgcolor="white",
#                     font_size=12
#                 )
#             )
            
#             st.plotly_chart(hour_fig, use_container_width=True)
            
#             # Show peak hours
#             st.markdown(f"""
#             <div style="text-align: center;">
#                 <p><strong>Peak hours:</strong> {', '.join(top_hours['label'].tolist())}</p>
#                 <p>Help us reduce energy during these times!</p>
#             </div>
#             """, unsafe_allow_html=True)
            
#         except Exception:
#             st.info("Hourly data not available")
        
#         st.markdown('</div>', unsafe_allow_html=True)
#     st.markdown('</div>', unsafe_allow_html=True)

#     # Footer with minimal text
#     st.markdown("""
#     <div class="footer">
#         {0} Earth Day Challenge 2025 | Last Updated: {1}
#     </div>
#     """.format(HOTEL_NAME, datetime.now().strftime("%b %d, %Y")), unsafe_allow_html=True)

# if __name__ == "__main__":
#     main()



import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import random
import streamlit.components.v1 as components  # Import components for HTML embedding

# Set the specific hotel for this dashboard
HOTEL_NAME = "Camden"  # Change this for each hotel's dashboard

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
        
        # Load the data with explicit date handling
        data = pd.read_sql_query(query, conn)
        
        # Convert Date column to datetime explicitly
        data['Date'] = pd.to_datetime(data['Date'])
        
        # If we didn't filter by MPAN, filter the data after loading
        if not HOTEL_MPAN and 'Meter Point' in data.columns:
            # Convert Meter Point to string for proper comparison
            data["Meter Point"] = data["Meter Point"].astype(str)
            
            # Create a hotel column
            data["Hotel"] = data["Meter Point"].map(mpan_to_hotel)
            
            # Filter for this hotel
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

# Get compare dates from previous year
def get_comparative_period(current_start, current_end):
    # Get same period from last year
    days_diff = (current_end - current_start).days
    last_year_end = current_end - pd.DateOffset(years=1)
    last_year_start = last_year_end - timedelta(days=days_diff)
    
    return last_year_start, last_year_end

# Generate hourly usage data 
def generate_hourly_data(data):
    time_cols = [f"{str(hour).zfill(2)}:{minute}" 
                for hour in range(24) 
                for minute in ['00', '30']]
    
    # Calculate average usage for each half-hour slot
    hourly_usage = data[time_cols].mean().reset_index()
    hourly_usage.columns = ['time', 'usage']
    
    # Convert time to hour label
    hourly_usage['hour'] = hourly_usage['time'].apply(lambda x: int(x.split(':')[0]))
    hourly_usage['label'] = hourly_usage['hour'].apply(lambda x: f"{x}:00")
    
    return hourly_usage

# Get KPIs for the comparison period
def get_comparison_kpis(data, current_start, current_end, compare_start, compare_end):
    # Filter for current period
    current_data = data[(data['Date'] >= current_start) & (data['Date'] <= current_end)]
    
    # Filter for comparison period
    compare_data = data[(data['Date'] >= compare_start) & (data['Date'] <= compare_end)]
    
    # Calculate metrics
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
    
    return {
        'current_total': current_total,
        'compare_total': compare_total,
        'percent_change': percent_change,
        'current_daily_avg': current_daily_avg,
        'compare_daily_avg': compare_daily_avg,
        'co2_saved': max(0, co2_saved),  # Only positive values for CO2 saved
        'kwh_saved': max(0, compare_total - current_total)
    }

# Main dashboard
def main():
    # Page config
    st.set_page_config(
        page_title=f"{HOTEL_NAME} - Earth Day 2025", 
        page_icon="🌍", 
        layout="wide"
    )
    
    # Load custom CSS
    st.markdown("""
    <style>
        /* Main header styling */
        .header-container {
            background-color: #065f46;
            padding: 1.2rem;
            border-radius: 0.75rem;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .header-title {
            font-size: 2.5rem;
            font-weight: 700;
            margin: 0;
            color: white;
        }
        .header-subtitle {
            font-size: 1.2rem;
            margin: 0;
            opacity: 0.9;
        }
        
        # /* KPI section container */
        # .kpi-section {
        #     margin-bottom: 2rem;
        #     background-color: #f9fafb;
        #     padding: 1.5rem;
        #     border-radius: 0.75rem;
        #     box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        # }
        

        .card {
            background-color: white;
            border-radius: 0.75rem;
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            border: 1px solid #f0f0f0;
            margin-bottom: 1rem;
            transition: transform 0.2s, box-shadow 0.2s;
            height: 200px; /* Fixed height for all cards */
            display: flex;
            flex-direction: column;
            justify-content: space-between; /* Distribute space evenly */
        }
        .card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(0,0,0,0.1);
        }
        /* Custom metric styling */
        .metric-label {
            font-size: 1rem;
            color: #6B7280;
            margin-bottom: 0.5rem;
        }
        .metric-value {
            font-size: 2.25rem;
            font-weight: 700;
            color: #1F2937;
            margin: 0.6rem 0;
        }
        .metric-delta {
            font-size: 0.95rem;
            color: #059669; /* Green for positive change */
            font-weight: 600; /* Make the text bolder */
            padding: 0.25rem 0.5rem;
            background-color: #ECFDF5; /* Light green background */
            border-radius: 0.5rem;
            display: inline-block; /* Ensure the background only covers the text */
        }
        .metric-delta.negative {
            color: #dc2626; /* Red for negative change */
            background-color: #FEE2E2; /* Light red background */
        }
        .metric-caption {
            font-size: 0.9rem;
            color: #6B7280;
            margin-top: 0.5rem;
        }
        /* Charts row styling */
        .charts-section {
            margin-bottom: 2rem;
            display: flex;
            gap: 1.5rem;
        }
        
        /* Section styling */
        # .section-container {
        #     background-color: white;
        #     border-radius: 0.75rem;
        #     padding: 1.25rem;
        #     box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        #     margin-bottom: 1.5rem;
        #     border: 1px solid #f0f0f0;
        # }
        .section-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-top: 0;
            margin-bottom: 1rem;
            color: #1F2937;
        }
        
        /* Champion styling */
        .champion-container {
            background-color: #ecfdf5;
            border-radius: 0.75rem;
            padding: 1.25rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            display: flex;
            align-items: center;
            gap: 1.25rem;
            border: 1px solid #A7F3D0;
        }
        .champion-info {
            flex: 1;
        }
        .champion-info h3 {
            margin-top: 0;
            margin-bottom: 0.5rem;
            color: #065f46;
        }
        .champion-info p {
            margin: 0;
            line-height: 1.5;
            color: #065f46;
        }
        .champion-photo {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            object-fit: cover;
            border: 3px solid #059669;
            box-shadow: 0 4px 8px rgba(5, 150, 105, 0.2);
        }
        
        /* Challenge progress */
        # .progress-container {
        #     background-color: #f9fafb;
        #     border-radius: 0.75rem;
        #     padding: 1.25rem;
        #     box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        #     margin-bottom: 1.5rem;
        #     border: 1px solid #f0f0f0;
        # }
        # .progress-container h3 {
        #     color: #1F2937;
        #     margin-top: 0;
        #     margin-bottom: 0.75rem;
        # }
        .progress-bar-bg {
            height: 24px;
            background-color: #e5e7eb;
            border-radius: 9999px;
            margin: 0.75rem 0;
            overflow: hidden;
        }
        .progress-bar {
            height: 24px;
            background-color: #059669;
            border-radius: 9999px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            transition: width 1s ease-in-out;
        }
        
        /* Energy tips */
        .tips-section {
            background-color: #f0fdf4;
            padding: 1.5rem;
            border-radius: 0.75rem;
            margin-bottom: 2rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            border: 1px solid #A7F3D0;
        }
        .tips-section h3 {
            margin-top: 0;
            margin-bottom: 0.75rem;
            color: #065f46;
            font-size: 1.25rem;
            font-weight: 600;
        }
        .tips-container {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-top: 0.75rem;
        }
        .tip-chip {
            background-color: white;
            padding: 0.5rem 1rem;
            border-radius: 9999px;
            font-size: 0.9rem;
            white-space: nowrap;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            border: 1px solid #d1fae5;
            transition: transform 0.2s;
        }
        .tip-chip:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            background-color: #ecfdf5;
        }
        
        /* Chart container */
        # .chart-container {
        #     background-color: white;
        #     border-radius: 0.75rem;
        #     padding: 1.25rem;
        #     box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        #     margin-bottom: 1.5rem;
        #     border: 1px solid #f0f0f0;
        #     height: 100%;
        # }
        
        /* Slido container styling */
        # .slido-container {
        #     background-color: white;
        #     border-radius: 0.75rem;
        #     padding: 1.25rem;
        #     box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        #     margin-bottom: 1.5rem;
        #     border: 1px solid #f0f0f0;
        # }
        
        /* Footer */
        .footer {
            text-align: center;
            margin-top: 2.5rem;
            color: #9CA3AF;
            font-size: 0.8rem;
            padding-bottom: 1rem;
        }
        
        /* Fix for Streamlit's default margins */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            max-width: 1200px; /* Adjust as needed */
        }
        
        /* Fix for plot background */
        .js-plotly-plot .plotly .main-svg
            background-color: transparent !important;
        }
        
        /* Responsive fixes for small screens */
        @media (max-width: 768px) {
            .kpi-value {
                font-size: 1.75rem;
            }
            .kpi-label {
                font-size: 0.8rem;
            }
            .champion-container {
                flex-direction: column;
                text-align: center;
            }
            .champion-photo {
                margin-bottom: 0.75rem;
            }
            .charts-section {
                flex-direction: column;
            }
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    # Header
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title"> 🌍 {0} Celebrates Earth Day</h1>
        <p class="header-subtitle">Our Planet, Our Power | April 14-21, 2025</p>
    </div>
    """.format(HOTEL_NAME), unsafe_allow_html=True)
    # Load data
    data = load_data()
    
    if len(data) == 0:
        st.warning(f"No data found for {HOTEL_NAME}. Please check your hotel name and MPAN mapping.")
        st.stop()
    
    # Define time periods
    today = datetime.today()
    
    # For Earth Day challenge
    challenge_start = datetime(2025, 4, 14)
    challenge_end = datetime(2025, 4, 21)
    
    # For current view (last 30 days by default)
    current_end = today
    current_start = today - timedelta(days=30)
    
    # Get comparison period (same days last year)
    compare_start, compare_end = get_comparative_period(current_start, current_end)
    
    # Calculation section
    with st.sidebar:
        st.subheader(f"{HOTEL_NAME} Hotel")
        
        # Time period selector
        period = st.selectbox(
            "Select Time Period:",
            [
                "Last 30 Days", 
                "Last 7 Days", 
                "Year to Date", 
                "Earth Day Challenge Period"
            ]
        )
        
        if period == "Last 7 Days":
            current_end = today
            current_start = today - timedelta(days=7)
        elif period == "Year to Date":
            current_end = today
            current_start = datetime(today.year, 1, 1)
        elif period == "Earth Day Challenge Period":
            # Use either actual dates if we're past Earth Day 2025 or projected dates
            if today > challenge_end:
                current_start = challenge_start
                current_end = challenge_end
            else:
                # If we're before the challenge, use the dates from last year + a projected 15% improvement
                current_start = challenge_start - timedelta(days=365)
                current_end = challenge_end - timedelta(days=365)
                st.info("Showing projected data for upcoming Earth Day Challenge")
        
        # Recalculate comparison period
        compare_start, compare_end = get_comparative_period(current_start, current_end)
        
        # Display date ranges for clarity
        st.caption(f"Current: {current_start.strftime('%b %d, %Y')} - {current_end.strftime('%b %d, %Y')}")
        st.caption(f"Compare: {compare_start.strftime('%b %d, %Y')} - {compare_end.strftime('%b %d, %Y')}")
    
    # Get KPIs for the selected periods
    kpis = get_comparison_kpis(data, current_start, current_end, compare_start, compare_end)
    
    # KPI section with improved container
# KPI section using st.metric


    # KPI section using custom HTML metrics inside cards
    # KPI section using custom HTML metrics inside cards
    st.markdown('<div class="kpi-section">', unsafe_allow_html=True)
    kpi_cols = st.columns(4)

    with kpi_cols[0]:
        # For percent change, negative is bad (increase in usage), positive is good (reduction in usage)
        change_color = "negative" if kpis['percent_change'] > 0 else ""
        st.markdown(f"""
        <div class="card">
            <div>
                <p class="metric-label">📊 COMPARED TO LAST YEAR</p>
                <p class="metric-value">{abs(kpis['percent_change']):.1f}%</p>
                <p class="metric-delta {change_color}">{"INCREASE" if kpis['percent_change'] > 0 else "REDUCTION"}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_cols[1]:
        # Energy saved is always positive and good
        st.markdown(f"""
        <div class="card">
            <div>
                <p class="metric-label">💡 ENERGY SAVED</p>
                <p class="metric-value">{kpis['kwh_saved']:,.0f} kWh</p>
                <p class="metric-delta">VS SAME PERIOD LAST YEAR</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_cols[2]:
        # CO₂ prevented is always positive and good
        st.markdown(f"""
        <div class="card">
            <div>
                <p class="metric-label">🌍 CO₂ PREVENTED</p>
                <p class="metric-value">{kpis['co2_saved']:,.0f} kg</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with kpi_cols[3]:
        # For daily average, negative change is bad (increase), positive is good (reduction)
        daily_change = ((kpis['current_daily_avg'] - kpis['compare_daily_avg']) / kpis['compare_daily_avg']) * 100
        change_color = "negative" if daily_change > 0 else ""
        st.markdown(f"""
        <div class="card">
            <div>
                <p class="metric-label">📅 DAILY AVERAGE</p>
                <p class="metric-value">{kpis['current_daily_avg']:,.0f} kWh</p>
                <p class="metric-delta {change_color}">{abs(daily_change):.1f}% vs last year</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Add Sli.do interactive widget section
    st.markdown('<div class="slido-container">', unsafe_allow_html=True)
    st.markdown('<h3 class="section-title">Earth Day Feedback & Ideas</h3>', unsafe_allow_html=True)
    
    # Embed Sli.do using components.html
    # The height parameter controls how tall the embedded frame will be
    components.html(
        """
        <div style="width: 100%; height: 100%;">
            <iframe src="https://wall.sli.do/event/k3BNqspDMjNrJBFQo6hYB9?section=add2f103-1df8-43b9-88a1-ceb98e276740" 
                    frameborder="0" 
                    style="width: 100%; height: 500px;" 
                    allow="camera; microphone; fullscreen; display-capture; autoplay">
            </iframe>
        </div>
        """,
        height=520,
    )
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-container">', unsafe_allow_html=True)
    st.markdown('<h3 class="section-title">Green Champion</h3>', unsafe_allow_html=True)

    st.markdown("""
    <div class="champion-container">
        <img src="https://ui-avatars.com/api/?name=Chinmay&background=10B981&color=fff&size=100" class="champion-photo">
        <div class="champion-info">
            <h3>Chinmay</h3>
            <p>"Let's outperform our target! Find me at reception for energy-saving tips."</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Earth Day Challenge Section
    st.markdown('<div class="progress-container">', unsafe_allow_html=True)
    st.markdown('<h3>Earth Day Challenge</h3>', unsafe_allow_html=True)

    # Calculate challenge progress values
    days_until = (challenge_start - today).days
    
    if days_until > 0:
        # Before challenge
        progress_pct = 0
        progress_label = f"Starts in {days_until} days"
    elif days_until <= 0 and days_until > -8:
        # During challenge
        day_of_challenge = abs(days_until) + 1
        progress_pct = min(100, (day_of_challenge / 8) * 100)
        progress_label = f"Day {day_of_challenge} of 8"
    else:
        # After challenge
        progress_pct = 100
        progress_label = "Challenge Complete"

    # # Progress bar
    # st.markdown(f"""
    # <div class="progress-bar-bg">
    #     # <div class="progress-bar" style="width: {progress_pct}%;">{progress_label}</div>
    # </div>
    # """, unsafe_allow_html=True)
    # st.markdown('</div>', unsafe_allow_html=True)

    # Energy-saving tips with improved layout
    st.markdown("""
    <div class="tips-section">
        <h3>Quick Energy-Saving Tips</h3>
        <div class="tips-container">
            <div class="tip-chip">💡 Turn off lights when leaving</div>
            <div class="tip-chip">🚿 Shorter showers save water & energy</div>
            <div class="tip-chip">🌡️ Keep thermostat at optimal 21-23°C</div>
            <div class="tip-chip">☀️ Use natural light during daytime</div>
            <div class="tip-chip">🔌 Unplug chargers when not in use</div>
            <div class="tip-chip">🚶‍♂️ Take stairs instead of elevator</div>
            <div class="tip-chip">🧺 Re-use towels to reduce laundry</div>
            <div class="tip-chip">💧 Report water leaks immediately</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Update the charts layout with improved container
    st.markdown('<div class="charts-section">', unsafe_allow_html=True)
    chart_cols = st.columns(2)  # Two columns for side-by-side layout

    # Year-over-Year Comparison Graph (Left Column)
    with chart_cols[0]:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-title">Year-over-Year Comparison</h3>', unsafe_allow_html=True)
        
        # Filter data for the selected periods
        current_period_data = data[(data['Date'] >= current_start) & (data['Date'] <= current_end)]
        compare_period_data = data[(data['Date'] >= compare_start) & (data['Date'] <= compare_end)]
        
        # Normalize dates to be able to plot them on the same x-axis
        current_period_data = current_period_data.copy()
        compare_period_data = compare_period_data.copy()
        
        # Create day index (0 to n) for both periods
        current_period_data['Day_Index'] = (current_period_data['Date'] - current_start).dt.days
        compare_period_data['Day_Index'] = (compare_period_data['Date'] - compare_start).dt.days
        
        # Create a date range for the x-axis
        day_count = (current_end - current_start).days + 1
        day_range = [current_start + timedelta(days=i) for i in range(day_count)]
        
        # Create plot
        fig = go.Figure()
        
        # Add current period line
        fig.add_trace(go.Scatter(
            x=current_period_data['Day_Index'], 
            y=current_period_data['Total Usage'],
            name=f'This Year',
            line=dict(color='#059669', width=3),
            hovertemplate='%{y:.0f} kWh'
        ))
        
        # Add comparison period line
        fig.add_trace(go.Scatter(
            x=compare_period_data['Day_Index'], 
            y=compare_period_data['Total Usage'],
            name=f'Last Year',
            line=dict(color='#6B7280', width=2, dash='dash'),
            hovertemplate='%{y:.0f} kWh'
        ))
        
        # Add shaded area for the difference
        # Only include if we have data for both periods
        if not current_period_data.empty and not compare_period_data.empty:
            # Merge on day index
            merged_data = pd.merge(
                current_period_data[['Day_Index', 'Total Usage']],
                compare_period_data[['Day_Index', 'Total Usage']],
                on='Day_Index',
                how='inner',
                suffixes=('_current', '_compare')
            )
            
            # Only add the saving area if current usage is less than comparison
            if kpis['percent_change'] < 0:
                fig.add_trace(go.Scatter(
                    x=merged_data['Day_Index'],
                    y=merged_data['Total Usage_compare'],
                    fill=None,
                    mode='lines',
                    line=dict(width=0),
                    showlegend=False,
                    hoverinfo='skip'
                ))
                
                fig.add_trace(go.Scatter(
                    x=merged_data['Day_Index'],
                    y=merged_data['Total Usage_current'],
                    fill='tonexty',
                    mode='lines',
                    line=dict(width=0),
                    fillcolor='rgba(5, 150, 105, 0.2)',
                    name='Energy Saved',
                    hoverinfo='skip'
                ))
        
        # Configure x-axis with actual dates instead of indices
        date_labels = [date.strftime("%b %d") for date in day_range]
        tick_indices = list(range(0, day_count, max(1, day_count // 10)))  # Show about 10 ticks
        
        fig.update_layout(
            xaxis=dict(
                tickmode='array',
                tickvals=tick_indices,
                ticktext=[date_labels[i] for i in tick_indices],
                title='Date',
                gridcolor='#f0f0f0'
            ),
            yaxis=dict(
                title='Energy Usage (kWh)',
                gridcolor='#f0f0f0'
            ),
            legend=dict(
                orientation='h',
                yanchor='bottom',
                y=1.02,
                xanchor='right',
                x=1,
                bgcolor='rgba(255,255,255,0.8)',
                bordercolor='#f0f0f0',
                borderwidth=1
            ),
            margin=dict(l=20, r=20, t=10, b=30),
            height=450,  # Increased height
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    # Peak Energy Hours Graph (Right Column)
    with chart_cols[1]:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<h3 class="section-title">Peak Energy Hours</h3>', unsafe_allow_html=True)
        
        try:
            # Generate hourly data
            hourly_data = generate_hourly_data(data)
            
            # Find top 3 peak hours
            top_hours = hourly_data.nlargest(3, 'usage')

            # Create hourly chart
            hour_fig = px.bar(
                hourly_data,
                x='label',
                y='usage',
                color='usage',
                color_continuous_scale='Viridis',
                labels={'usage': 'Energy (kWh)', 'label': 'Hour'}
            )
            
            # Show only every 3rd hour to avoid crowding
            show_labels = hourly_data['label'].iloc[::3].tolist()
            hour_fig.update_layout(
                coloraxis_showscale=False,
                height=450,  # Match height with the other graph
                margin=dict(l=20, r=20, t=10, b=30),
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(
                    tickmode='array',
                    tickvals=show_labels,
                    ticktext=show_labels,
                    title='Hour',
                    gridcolor='#f0f0f0'
                ),
                yaxis=dict(
                    title='Energy (kWh)',
                    gridcolor='#f0f0f0'
                ),
                hoverlabel=dict(
                    bgcolor="white",
                    font_size=12
                )
            )
            
            st.plotly_chart(hour_fig, use_container_width=True)
            
            # Show peak hours
            st.markdown(f"""
            <div style="text-align: center;">
                <p><strong>Peak hours:</strong> {', '.join(top_hours['label'].tolist())}</p>
                <p>Help us reduce energy during these times!</p>
            </div>
            """, unsafe_allow_html=True)
            
        except Exception:
            st.info("Hourly data not available")
        
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Footer with minimal text
    st.markdown("""
    <div class="footer">
        {0} Earth Day Challenge 2025 | Last Updated: {1}
    </div>
    """.format(HOTEL_NAME, datetime.now().strftime("%b %d, %Y")), unsafe_allow_html=True)

if __name__ == "__main__":
    main()


