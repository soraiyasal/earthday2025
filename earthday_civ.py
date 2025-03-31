import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime
import streamlit.components.v1 as components  # Import components for HTML embedding

# Set page config
st.set_page_config(
    page_title="Hotel Energy Dashboard", 
    page_icon="🌍", 
    layout="wide"
)

# Constants
ELECTRICITY_FACTOR = 0.20493  # CO2 emission factor for electricity

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
def calculate_q1_comparison(df, hotel='CIV'):
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
def create_q1_chart(df, comparison, hotel):
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
        
        # Create chart
        fig = px.bar(
            chart_df, 
            x='Month', 
            y='Value', 
            color='Year',
            title=f"Jan - March Comparison: {hotel} ({previous_year} vs {current_year})",
            labels={'Value': 'Energy (kWh)', 'Month': 'Month'},
            barmode='group',
            text_auto=True
        )
        
        # Update layout - FIXED xaxis property
        fig.update_layout(
            xaxis=dict(
                categoryorder='array',
                categoryarray=['Jan', 'Feb', 'Mar']
            ),
            yaxis=dict(
                title='Energy (kWh)',
                tickformat=','
            )
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating Jan-March chart: {str(e)}")
        return None

# Create trend chart with Jan-March highlighted
def create_trend_chart(df, hotel, highlight_q1=True):
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
            
            # Create chart with Jan-March highlighted
            fig = px.line(
                df,
                x='Date',
                y=hotel,
                color='Period',
                markers=True,
                labels={'Date': 'Month', hotel: 'Energy (kWh)'},
                color_discrete_map={
                    'Jan - March': '#2E8B57',  # Green for Jan-March
                    'Other Months': '#A9A9A9'  # Grey for other months
                }
            )
        else:
            # Regular chart without highlighting
            fig = px.line(
                df,
                x='Date',
                y=hotel,
                markers=True,
                labels={'Date': 'Month', hotel: 'Energy (kWh)'}
            )
        
        # Format chart
        fig.update_layout(
            title=f"Monthly Energy Usage: {hotel}",
            xaxis=dict(
                tickformat='%b %Y',
                tickangle=-45
            ),
            yaxis=dict(
                title='Energy (kWh)',
                tickformat=','
            )
        )
        
        return fig
    except Exception as e:
        st.error(f"Error creating trend chart: {str(e)}")
        return None

# Main function
def main():
    # Load CSS for champion section
    st.markdown("""
    <style>
        .champion-container {
            background-color: #ecfdf5;
            border-radius: 0.75rem;
            padding: 1.25rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            display: flex;
            align-items: center;
            gap: 1.25rem;
            border: 1px solid #A7F3D0;
            margin-bottom: 2rem;
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
        .energy-tip {
            background-color: #e0f2fe;
            border-left: 4px solid #0ea5e9;
            padding: 1rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }
        .energy-tip h4 {
            margin-top: 0;
            margin-bottom: 0.5rem;
            color: #0369a1;
        }
        .energy-tip p {
            margin: 0;
            color: #0c4a6e;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
    <div class="header-container">
        <h1 class="header-title">🌍 Comfort Inn Victoria Earth Day Energy Dashboard</h1>
        <p class="header-subtitle">Power Up Initiative | April 2025</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load data
    df = load_data()
    
    if df.empty:
        st.error("No data loaded. Please check your elec.csv file.")
        return
    
    # Sidebar
    with st.sidebar:
        st.title("Dashboard Controls")
        
        # Hotel selection
        hotel_columns = [col for col in df.columns if col not in ['Month', 'Date', 'Year', 'MonthNum', 'MonthName']]
        if hotel_columns:
            selected_hotel = st.selectbox(
                "Select Hotel:",
                hotel_columns,
                index=hotel_columns.index('CIV') if 'CIV' in hotel_columns else 0
            )
        else:
            st.error("No hotel columns found in data")
            return
        
        # Target setting
        reduction_target = st.slider("Reduction Target (%)", 5, 30, 15)
    
    # Calculate Jan-March comparison
    comparison = calculate_q1_comparison(df, selected_hotel)
    
    # Display KPIs
    if comparison:
        # Create KPI metrics
        kpi_cols = st.columns(3)
        
        with kpi_cols[0]:
            direction = "Reduction" if comparison['percent_change'] < 0 else "Increase"
            delta_color = "normal" if comparison['percent_change'] < 0 else "inverse"
            st.metric(
                label=f"Jan - March {comparison['current_year']} vs Jan - March {comparison['previous_year']}",
                value=f"{abs(comparison['percent_change']):.1f}%",
                delta=direction,
                delta_color=delta_color
            )
        
        with kpi_cols[1]:
            st.metric(
                label="Energy Saved (Jan - March)",
                value=f"{comparison['energy_saved']:,.0f} kWh"
            )
        
        with kpi_cols[2]:
            st.metric(
                label="CO₂ Prevented (Jan - March)",
                value=f"{comparison['co2_prevented']:,.0f} kg"
            )
        
        # Progress towards target
        if comparison['percent_change'] < 0:  # Only if there's a reduction
            progress = min(100, abs(comparison['percent_change']) / reduction_target * 100)
            
            st.subheader("Progress Toward Reduction Target")
            
            # Add progress bar
            st.progress(progress / 100)
            
            # Add caption
            st.caption(f"{progress:.1f}% of the {reduction_target}% reduction target achieved")
    
    # Champion Section
    st.markdown("""
    <div class="champion-container">
        <img src="https://ui-avatars.com/api/?name=Emma&background=10B981&color=fff&size=100" class="champion-photo">
        <div class="champion-info">
            <h3>Sufyan, Green Champion</h3>
            <p>"We've made great progress in Jan - March! Let's keep up the momentum! Remember to turn off lights when leaving a room and report any issues with equipment immediately."</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Charts section
    chart_cols = st.columns(2)
    
    # Quick Energy-Saving Reminders (replacing Energy-Saving Tips)
    with chart_cols[0]:
        st.subheader("Quick Energy-Saving Reminders")
        
        tips_cols = st.columns(1)
        
        tips = [
            "💡 Turn off lights in unoccupied areas",
            "🚿 Report leaking taps immediately",
            "🌡️ Keep thermostat at 21-23°C",
            "☀️ Use natural light when possible",
            "🔌 Unplug equipment when not in use",
            "🚶‍♂️ Use stairs for trips under 3 floors"
            # "💻 Enable power-saving on devices",
            # "❄️ Close refrigerator doors completely"
        ]
        
        for tip in tips:
            st.info(tip)
    
    # Jan-March comparison chart
    with chart_cols[1]:
        st.subheader("Jan - March Comparison")
        q1_chart = create_q1_chart(df, comparison, selected_hotel)
        if q1_chart:
            st.plotly_chart(q1_chart, use_container_width=True)
    
    # Add Sli.do interactive widget section
    st.subheader("Earth Day Feedback & Ideas")
    
    # Embed Sli.do using components.html
    components.html(
        """
        <div style="width: 100%; height: 100%;">
            <iframe src="https://wall.sli.do/event/tZFDbXyMj6JiEmMk6TxC7t/?section=113b6cbd-d08f-438e-9050-cac73fb050fb" 
                    frameborder="0" 
                    style="width: 100%; height: 500px;" 
                    allow="camera; microphone; fullscreen; display-capture; autoplay">
            </iframe>
        </div>
        """,
        height=520,
    )
    
    # # Earth Day Information Section
    # st.subheader("Earth Day at CIV")
    
    # st.markdown("""
    # <div style="background-color: #f0fdf4; padding: 1.5rem; border-radius: 0.75rem; border-left: 4px solid #22c55e;">
    #     <h3 style="margin-top: 0; color: #166534;">Join Us for Earth Day 2025!</h3>
    #     <p>CIV is proud to celebrate Earth Day with a series of sustainability initiatives:</p>
    #     <ul>
    #         <li>Tree planting ceremony in the hotel garden at 10:00</li>
    #         <li>Sustainability workshop in the conference room at 14:00</li>
    #         <li>Energy-saving competition between departments</li>
    #         <li>Locally-sourced special menu in the restaurant</li>
    #     </ul>
    #     <p style="margin-bottom: 0;">Together, we can make a difference for our planet!</p>
    # </div>
    # """, unsafe_allow_html=True)
    
    # Footer
    st.markdown("---")
    st.caption("Hotel Power Up Initiative | Last Updated: March 31, 2025")

if __name__ == "__main__":
    main()