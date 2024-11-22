# --------------------------------------------
# Imports at the top - PyShiny EXPRESS VERSION
# --------------------------------------------

from shiny import reactive, render
from shiny.express import ui
import random
from datetime import datetime
from collections import deque
import pandas as pd
import plotly.express as px
from shinywidgets import render_plotly
from scipy import stats
from faicons import icon_svg
import requests
from bs4 import BeautifulSoup

# --------------------------------------------
# Constants and Reactive Values
# --------------------------------------------

UPDATE_INTERVAL_SECS: int = 30  # Updated to 30 seconds for more frequent readings
DEQUE_SIZE: int = 5
reactive_value_wrapper = reactive.value(deque(maxlen=DEQUE_SIZE))

# --------------------------------------------
# Function to get Australia temperature
# --------------------------------------------

def get_australia_temperature():
    url = "http://www.bom.gov.au/nsw/forecasts/sydney.shtml"
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        temp_elem = soup.find('em', {'class': 'temp'})
        if temp_elem:
            return float(temp_elem.text.strip('°'))
    except:
        pass
    return None

# --------------------------------------------
# Reactive Calculation
# --------------------------------------------

@reactive.calc()
def reactive_calc_combined():
    reactive.invalidate_later(UPDATE_INTERVAL_SECS)

    temp = get_australia_temperature()
    if temp is None:
        temp = round(random.uniform(15, 25), 1)  # Fallback to random temp if fetch fails
    
    # Convert Celsius to Fahrenheit
    temp_fahrenheit = (temp * 1.8) + 32
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    new_dictionary_entry = {"temp": temp_fahrenheit, "timestamp": timestamp}

    reactive_value_wrapper.get().append(new_dictionary_entry)
    deque_snapshot = reactive_value_wrapper.get()
    df = pd.DataFrame(deque_snapshot)

    return deque_snapshot, df, new_dictionary_entry

# --------------------------------------------
# UI Definition
# --------------------------------------------

ui.page_opts(title="PyShiny Express: Live Sydney Temperature", fillable=True)

with ui.sidebar(open="open"):
    ui.h2("Sydney Weather Explorer", class_="text-center")
    ui.p(
        "Real-time temperature readings in Sydney, Australia.",
        class_="text-center",
    )
    ui.hr()
    ui.h6("Links:")
    ui.a(
        "My GitHub Repository",
        href="https://github.com/tsngh/cintel-05-cintel/",
        target="_blank",
    )
    ui.a("PyShiny", href="https://shiny.posit.co/py/", target="_blank")
    ui.a(
        "PyShiny Express",
        href="https://shiny.posit.co/blog/posts/shiny-express/",
        target="_blank",
    )

with ui.layout_columns():
    with ui.value_box(
        showcase=icon_svg("sun"),
        theme="bg-gradient-green-yellow",
    ):
        "Current Temperature"

        @render.text
        def display_temp():
            deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()
            return f"{latest_dictionary_entry['temp']:.1f} °F"

        "in Sydney"

    with ui.card(full_screen=True):
        ui.card_header("Current Date and Time")

        @render.text
        def display_time():
            deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()
            return f"{latest_dictionary_entry['timestamp']}"

with ui.card(full_screen=True):
    ui.card_header("Most Recent Readings")

    @render.data_frame
    def display_df():
        deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()
        pd.set_option('display.width', None)
        return render.DataGrid(df, width="100%")

with ui.card():
    ui.card_header("Chart with Current Trend")

    @render_plotly
    def display_plot():
        deque_snapshot, df, latest_dictionary_entry = reactive_calc_combined()

        if not df.empty:
            df["timestamp"] = pd.to_datetime(df["timestamp"])

            fig = px.scatter(df,
                x="timestamp",
                y="temp",
                title="Temperature Readings with Regression Line",
                labels={"temp": "Temperature (°F)", "timestamp": "Time"},
                color_discrete_sequence=["blue"])

            sequence = range(len(df))
            x_vals = list(sequence)
            y_vals = df["temp"]

            slope, intercept, r_value, p_value, std_err = stats.linregress(x_vals, y_vals)
            df['best_fit_line'] = [slope * x + intercept for x in x_vals]

            fig.add_scatter(x=df["timestamp"], y=df['best_fit_line'], mode='lines', name='Regression Line')
            fig.update_layout(xaxis_title="Time", yaxis_title="Temperature (°F)")

            return fig


