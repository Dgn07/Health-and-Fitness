import streamlit as st
import pandas as pd
import datetime
import os
from io import BytesIO
from fpdf import FPDF
import matplotlib.pyplot as plt

# Function to save chart image to disk temporarily
def save_chart_to_file(buf, filename):
    with open(filename, 'wb') as f:
        f.write(buf.getbuffer())

# Load or create data file
data_file = 'progress.csv'
if os.path.exists(data_file):
    df = pd.read_csv(data_file, parse_dates=['Date'])
else:
    df = pd.DataFrame(columns=[
        'Date', 'Breakfast', 'Snack', 'Lunch', 'Dinner', 'Shake', 'Water', 'Exercise', 'Calories', 'Protein', 'Weight'
    ])

# Today's date
today = datetime.date.today()

# Sidebar inputs
st.sidebar.title("🏋️ Daily Tracker")

st.sidebar.header("Personal Info")
age = st.sidebar.number_input("Age", min_value=10, max_value=100, value=27)
sex = st.sidebar.selectbox("Sex", ["Male", "Female"])
height = st.sidebar.number_input("Height (cm)", min_value=100, max_value=250, value=181)
current_weight = st.sidebar.number_input("Current Weight (kg)", min_value=30, max_value=300, value=96)

activity_level = st.sidebar.selectbox(
    "Activity Level",
    ["Sedentary", "Light", "Moderate", "Active"],
    help="Sedentary: Little/no exercise. Light: 1-3 days/week light activity. Moderate: 3-5 days/week moderate activity. Active: 5-7 days/week intense or physical job."
)

# Calculate BMR
if sex == "Male":
    bmr = 10 * current_weight + 6.25 * height - 5 * age + 5
else:
    bmr = 10 * current_weight + 6.25 * height - 5 * age - 161

activity_factors = {
    "Sedentary": 1.2,
    "Light": 1.4,
    "Moderate": 1.6,
    "Active": 1.8
}
activity_factor = activity_factors[activity_level]
maintenance_calories = round(bmr * activity_factor)

# Checkboxes for habits
breakfast = st.sidebar.checkbox("Breakfast")
snack = st.sidebar.checkbox("Snack")
lunch = st.sidebar.checkbox("Lunch")
dinner = st.sidebar.checkbox("Dinner")
shake = st.sidebar.checkbox("Protein Shake")
water = st.sidebar.checkbox("2L Water")
exercise = st.sidebar.checkbox("Exercise")

deficit_goal = st.sidebar.number_input("Daily Calorie Deficit Goal", min_value=0, max_value=2000, step=50, value=500)
calories = st.sidebar.number_input("Calories today", min_value=0, max_value=6000, step=50)
protein = st.sidebar.number_input("Protein today (g)", min_value=0, max_value=300, step=5)
weight = st.sidebar.number_input("Weight today (kg)", min_value=0.0, max_value=300.0, step=0.1, format="%.1f")

deficit = maintenance_calories - calories

if st.sidebar.button("Save today's entry"):
    new_entry = pd.DataFrame([{
        'Date': today,
        'Breakfast': breakfast,
        'Snack': snack,
        'Lunch': lunch,
        'Dinner': dinner,
        'Shake': shake,
        'Water': water,
        'Exercise': exercise,
        'Calories': calories,
        'Protein': protein,
        'Weight': weight
    }])
    df = df[df['Date'] != pd.Timestamp(today)]
    df = pd.concat([df, new_entry], ignore_index=True)
    df.to_csv(data_file, index=False)
    st.success("Saved today's data!")

# Function to create styled PDF with chart files
def create_pdf(dataframe):
    # Generate Calories chart
    plt.figure(figsize=(6, 3))
    plt.plot(dataframe['Date'], dataframe['Calories'], marker='o')
    plt.title('Calories Over Time')
    plt.xlabel('Date')
    plt.ylabel('Calories')
    plt.xticks(rotation=45)
    plt.tight_layout()
    cal_buf = BytesIO()
    plt.savefig(cal_buf, format='png')
    plt.close()

    # Generate Weight chart
    plt.figure(figsize=(6, 3))
    plt.plot(dataframe['Date'], dataframe['Weight'], marker='o', color='green')
    plt.title('Weight Over Time')
    plt.xlabel('Date')
    plt.ylabel('Weight (kg)')
    plt.xticks(rotation=45)
    plt.tight_layout()
    weight_buf = BytesIO()
    plt.savefig(weight_buf, format='png')
    plt.close()

    # Save images temporarily
    save_chart_to_file(cal_buf, "cal_chart.png")
    save_chart_to_file(weight_buf, "weight_chart.png")

    pdf = FPDF()
    pdf.add_page()

    pdf.set_fill_color(70, 130, 180)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 18)
    pdf.cell(0, 15, "Health & Fitness Progress Report", ln=True, align='C', fill=True)

    pdf.ln(5)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 12)

    for index, row in dataframe.tail(7).iterrows():
        deficit_val = maintenance_calories - row['Calories']
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, f"Date: {row['Date'].strftime('%Y-%m-%d')}", ln=True)
        pdf.set_font("Arial", '', 12)
        pdf.cell(0, 8, f"Calories: {row['Calories']} kcal, Protein: {row['Protein']} g, Weight: {row['Weight']} kg", ln=True)
        pdf.cell(0, 8, f"Deficit: {deficit_val} kcal", ln=True)
        pdf.ln(5)

    pdf.image("cal_chart.png", x=10, w=180)
    pdf.ln(5)
    pdf.image("weight_chart.png", x=10, w=180)

    output = BytesIO()
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    output.write(pdf_bytes)
    output.seek(0)
    return output

# Dashboard
st.title("📊 Health & Fitness Dashboard")

st.subheader("Maintenance Calories Calculation")
st.write(f"BMR: {bmr:.0f} kcal/day")
st.write(f"Activity Level: {activity_level} (Factor {activity_factor})")
st.write(f"Maintenance Calories: {maintenance_calories} kcal/day")

if not df.empty:
    df = df.sort_values('Date')
    st.subheader("Last 7 Days")
    st.dataframe(df.tail(7).set_index('Date'))

    st.subheader("Calories over time")
    st.line_chart(df.set_index('Date')['Calories'])

    st.subheader("Weight over time")
    st.line_chart(df.set_index('Date')['Weight'])

    st.subheader("Today's Calorie Deficit")
    st.write(f"Calories Consumed: {calories} kcal")
    st.write(f"Deficit: {deficit} kcal")
    if deficit >= deficit_goal:
        st.success(f"🎉 You met your calorie deficit goal of {deficit_goal} kcal!")
    else:
        st.warning(f"⚠️ You are below your target deficit by {deficit_goal - deficit} kcal.")

    avg_deficit = (maintenance_calories - df['Calories']).mean()
    projected_loss_per_week = (avg_deficit * 7) / 7700 if avg_deficit > 0 else 0
    st.subheader("Projected Weight Loss")
    st.write(f"Average daily deficit: {avg_deficit:.0f} kcal")
    st.write(f"➡️ Projected weight loss: {projected_loss_per_week:.2f} kg/week")

    st.subheader("% Days goals were hit")
    total_days = len(df)
    meal_days = (df[['Breakfast','Snack','Lunch','Dinner']].sum(axis=1) >= 4).sum()
    exercise_days = df['Exercise'].sum()
    water_days = df['Water'].sum()
    st.write(f"✅ Full meals: {meal_days}/{total_days} days")
    st.write(f"💧 Water goal: {water_days}/{total_days} days")
    st.write(f"🏃 Exercise done: {exercise_days}/{total_days} days")

    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name='progress.csv',
        mime='text/csv'
    )

    pdf_file = create_pdf(df)
    st.download_button(
        label="📄 Download Styled PDF Report",
        data=pdf_file,
        file_name='progress_report.pdf',
        mime='application/pdf'
    )
else:
    st.info("No data yet. Use the sidebar to add today's entry.")
