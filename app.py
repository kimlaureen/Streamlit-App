import streamlit as st
import plotly.express as px
import time
import random
import pandas as pd

st.set_page_config(page_title="NYC Taxi Payment Method Analysis", page_icon=":taxi:", layout="wide")

# Direct CSV URL for Google Sheets
sheet_url = "https://docs.google.com/spreadsheets/d/1PB_KHJWbgh_48OIalrvQqpPOKEPo2uKdIEDzgizsvIw/edit?usp=sharing"
csv_export_url = sheet_url.replace('/edit?usp=sharing', '/export?format=csv')

@st.cache_data
def load_data():
    try:
        return pd.read_csv(csv_export_url)
    except Exception as e:
        st.error(f"Error fetching data from Google Sheets: {str(e)}")
        # Create mock NYC taxi payment data as fallback
        mock_data = pd.DataFrame({
            'payment': ['credit card', 'cash', 'credit card', 'credit card', 'cash', 
                       'credit card', 'mobile payment', 'credit card', 'cash', 'credit card'] * 20
        })
        return mock_data

# Load data dynamically from Google Sheets
data = load_data()

# Initialize session state variables
if 'start_time' not in st.session_state:
    st.session_state.start_time = None
if 'chart_type' not in st.session_state:
    st.session_state.chart_type = None
if 'experiment_started' not in st.session_state:
    st.session_state.experiment_started = False
if 'response_times' not in st.session_state:
    st.session_state.response_times = []
if 'chart_attempts' not in st.session_state:
    st.session_state.chart_attempts = []
if 'attempt_number' not in st.session_state:
    st.session_state.attempt_number = 0
if 'answered' not in st.session_state:
    st.session_state.answered = False

st.title("NYC Taxi Payment Method Analysis")
st.markdown("What is the most common type of payment in the NYC Taxi Data?")

# Use the loaded data
df = data
payment_counts = df['payment'].value_counts()

def create_bar_chart():
    fig = px.bar(
        payment_counts, 
        x=payment_counts.index, 
        y=payment_counts.values, 
        title='Payment Methods (Bar Chart)',
        labels={'x': 'Payment Type', 'y': 'Number of Rides'}
    )
    return fig

def create_pie_chart():
    fig = px.pie(
        values=payment_counts.values, 
        names=payment_counts.index, 
        title='Payment Methods (Pie Chart)'
    )
    return fig

col1, col2 = st.columns([2, 1])

with col1:
    if not st.session_state.experiment_started:
        if st.button("Start A/B Test"):
            st.session_state.chart_type = random.choice(['bar', 'pie'])
            st.session_state.start_time = time.time()
            st.session_state.experiment_started = True
            st.session_state.chart_attempts.append(st.session_state.chart_type)
            st.session_state.attempt_number += 1
            st.session_state.answered = False

    if st.session_state.experiment_started:
        if st.session_state.chart_type == 'bar':
            st.plotly_chart(create_bar_chart())
        else:
            st.plotly_chart(create_pie_chart())

        if not st.session_state.answered and st.button("I answered the question"):
            end_time = time.time()
            time_taken = end_time - st.session_state.start_time
            st.session_state.response_times.append(time_taken)
            st.session_state.answered = True
            
            st.success(f"Time taken to answer: {time_taken:.2f} seconds")
            
        if st.session_state.answered and st.button("Try Another Chart"):
            st.session_state.chart_type = random.choice(['bar', 'pie'])
            st.session_state.start_time = time.time()
            st.session_state.chart_attempts.append(st.session_state.chart_type)
            st.session_state.attempt_number += 1
            st.session_state.answered = False
            st.rerun()

with col2:
    if st.session_state.experiment_started:
        st.markdown("### Results")
        
        most_common = payment_counts.idxmax()
        st.markdown(f"**Most Common Payment:** {most_common}")
        st.markdown(f"**Total Rides:** {payment_counts[most_common]}")

        if len(st.session_state.response_times) > 0:
            st.markdown("### Response Times")
            
            tracking_df = pd.DataFrame({
                'Attempt': list(range(1, len(st.session_state.response_times) + 1)),
                'Chart Type': st.session_state.chart_attempts[:len(st.session_state.response_times)],
                'Time (seconds)': st.session_state.response_times
            })
            
            st.dataframe(tracking_df)
            
            fig = px.line(
                tracking_df, 
                x='Attempt', 
                y='Time (seconds)', 
                color='Chart Type',
                markers=True,
                title='Answer Time by Chart Type'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Calculate average times by chart type
            avg_times = tracking_df.groupby('Chart Type')['Time (seconds)'].mean().reset_index()
            avg_times['Time (seconds)'] = avg_times['Time (seconds)'].round(2)
            
            # Create a bar chart of average times
            fig_avg = px.bar(
                avg_times,
                x='Chart Type',
                y='Time (seconds)',
                title='Average Answer Time by Chart Type',
                text_auto='.2f'
            )
            st.plotly_chart(fig_avg, use_container_width=True)


if st.session_state.experiment_started and len(st.session_state.response_times) > 1:
    st.markdown("---")
    st.markdown("### Detailed Analysis")
    
    tab1, tab2 = st.tabs(["Response Time Trends", "Chart Type Comparison"])
    
    with tab1:
        tracking_df = pd.DataFrame({
            'Attempt': list(range(1, len(st.session_state.response_times) + 1)),
            'Chart Type': st.session_state.chart_attempts[:len(st.session_state.response_times)],
            'Time (seconds)': st.session_state.response_times
        })
        
        # Add a moving average column if we have enough data
        if len(tracking_df) >= 3:
            tracking_df['Moving Avg (3)'] = tracking_df['Time (seconds)'].rolling(3).mean()
        
        fig_trend = px.line(
            tracking_df,
            x='Attempt',
            y=['Time (seconds)', 'Moving Avg (3)'] if 'Moving Avg (3)' in tracking_df.columns else 'Time (seconds)',
            title='Response Time Trend',
            markers=True
        )
        st.plotly_chart(fig_trend)
    
    with tab2:
        bar_times = [t for t, c in zip(st.session_state.response_times, st.session_state.chart_attempts[:len(st.session_state.response_times)]) if c == 'bar']
        pie_times = [t for t, c in zip(st.session_state.response_times, st.session_state.chart_attempts[:len(st.session_state.response_times)]) if c == 'pie']
        
        comparison_df = pd.DataFrame({
            'Chart Type': ['Bar Chart', 'Pie Chart'],
            'Average Time (s)': [sum(bar_times)/len(bar_times) if bar_times else 0, 
                                sum(pie_times)/len(pie_times) if pie_times else 0],
            'Min Time (s)': [min(bar_times) if bar_times else 0, 
                            min(pie_times) if pie_times else 0],
            'Max Time (s)': [max(bar_times) if bar_times else 0, 
                            max(pie_times) if pie_times else 0],
            'Count': [len(bar_times), len(pie_times)]
        })
        
        st.dataframe(comparison_df)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if bar_times and pie_times:
                fig_box = px.box(
                    pd.DataFrame({
                        'Chart Type': ['Bar'] * len(bar_times) + ['Pie'] * len(pie_times),
                        'Time (seconds)': bar_times + pie_times
                    }),
                    x='Chart Type',
                    y='Time (seconds)',
                    title='Distribution of Answer Times'
                )
                st.plotly_chart(fig_box)
        
        with col2:
            if bar_times and pie_times:
                # Calculate if there's a statistically significant difference
                import scipy.stats as stats
                
                if len(bar_times) >= 3 and len(pie_times) >= 3:
                    t_stat, p_value = stats.ttest_ind(bar_times, pie_times, equal_var=False)
                    
                    st.markdown("### Statistical Analysis")
                    st.markdown(f"**t-statistic:** {t_stat:.4f}")
                    st.markdown(f"**p-value:** {p_value:.4f}")
                    
                    if p_value < 0.05:
                        st.markdown("**Result:** There is a statistically significant difference between the chart types.")
                    else:
                        st.markdown("**Result:** No statistically significant difference detected yet.")
                else:
                    st.markdown("Need at least 3 samples of each chart type for statistical analysis.")


if st.session_state.experiment_started:
    if st.button("Reset All Data"):
        st.session_state.experiment_started = False
        st.session_state.start_time = None
        st.session_state.chart_type = None
        st.session_state.response_times = []
        st.session_state.chart_attempts = []
        st.session_state.attempt_number = 0
        st.session_state.answered = False
        st.rerun()


st.markdown("---")
st.markdown("This is an A/B testing experiment to compare visualization effectiveness.")
