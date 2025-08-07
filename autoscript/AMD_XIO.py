###########################################################################################
##                                 Copyright ©, 2024, by                                 ##
##                         Lenovo Internal. All Rights Reserved.                         ##
##                                      Margin Team                                      ##
##                                                                                       ##
##                                                      Dean Chen (dchen52@lenovo.com)   ##
###########################################################################################
import os
import io
import sys
import base64
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from tkinter import *
from tkinter import messagebox
from tkinter.filedialog import askopenfilename, asksaveasfilename
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

sys.dont_write_bytecode = True
cur_dir = os.path.dirname(os.path.abspath(__file__))
root_folder = os.path.dirname(cur_dir)

copyright = f"Dean Chen (dchen52@lenovo.com)"


def generate_plots(device_data, device, volt_criteria, offset_criteria):
    fig, axs = plt.subplots(5, 1, figsize=(12, 22))
    axs = axs.flatten()

    unique_lanes = sorted(device_data['LanePCIeNo'].unique())

    # Margin Top (mV)
    for i in range(5):
        values = [device_data.loc[(device_data['LanePCIeNo'] == lane), 'Margin Top (volt)'].iloc[i]
                  if i < len(device_data.loc[(device_data['LanePCIeNo'] == lane), 'Margin Top (volt)'])
                  else None
                  for lane in unique_lanes]
        axs[0].plot(unique_lanes, values, marker='o', linestyle='-', linewidth=1.5, label=f'Data Group {i + 1}')
        axs[0].scatter(unique_lanes, values, color='blue', s=80, zorder=5)
    axs[0].set_title('Margin Top (mV)')
    axs[0].set_xlabel('Lane')
    axs[0].set_ylabel('Margin Top (mV)')
    axs[0].grid(True)
    axs[0].axhline(y=volt_criteria, color='red', linestyle='--', linewidth=2)
    axs[0].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # Margin Bottom (mV)
    for i in range(5):
        values = [device_data.loc[(device_data['LanePCIeNo'] == lane), 'Margin Bottom (volt)'].iloc[i]
                  if i < len(device_data.loc[(device_data['LanePCIeNo'] == lane), 'Margin Bottom (volt)'])
                  else None
                  for lane in unique_lanes]
        axs[1].plot(unique_lanes, values, marker='o', linestyle='-', linewidth=1.5, label=f'Data Group {i + 1}')
        axs[1].scatter(unique_lanes, values, color='blue', s=80, zorder=5)
    axs[1].set_title('Margin Bottom (mV)')
    axs[1].set_xlabel('Lane')
    axs[1].set_ylabel('Margin Bottom (mV)')
    axs[1].grid(True)
    axs[1].axhline(y=volt_criteria, color='red', linestyle='--', linewidth=2)
    axs[1].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # Margin Left Offset
    for i in range(5):
        values = [device_data.loc[(device_data['LanePCIeNo'] == lane), 'Margin Left Offset'].iloc[i]
                  if i < len(device_data.loc[(device_data['LanePCIeNo'] == lane), 'Margin Left Offset'])
                  else None
                  for lane in unique_lanes]
        axs[2].plot(unique_lanes, values, marker='o', linestyle='-', linewidth=1.5, label=f'Data Group {i + 1}')
        axs[2].scatter(unique_lanes, values, color='blue', s=80, zorder=5)
    axs[2].set_title('Margin Left Offset')
    axs[2].set_xlabel('Lane')
    axs[2].set_ylabel('Margin Left Offset')
    axs[2].grid(True)
    axs[2].axhline(y=offset_criteria, color='red', linestyle='--', linewidth=2)
    axs[2].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # Margin Right Offset
    for i in range(5):
        values = [device_data.loc[(device_data['LanePCIeNo'] == lane), 'Margin Right Offset'].iloc[i]
                  if i < len(device_data.loc[(device_data['LanePCIeNo'] == lane), 'Margin Right Offset'])
                  else None
                  for lane in unique_lanes]
        axs[3].plot(unique_lanes, values, marker='o', linestyle='-', linewidth=1.5, label=f'Data Group {i + 1}')
        axs[3].scatter(unique_lanes, values, color='blue', s=80, zorder=5)
    axs[3].set_title('Margin Right Offset')
    axs[3].set_xlabel('Lane')
    axs[3].set_ylabel('Margin Right Offset')
    axs[3].grid(True)
    axs[3].axhline(y=offset_criteria, color='red', linestyle='--', linewidth=2)
    axs[3].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # Eye Margin
    worst_lane_top = device_data.loc[device_data['Margin Top (volt)'].idxmin(), 'LanePCIeNo']
    worst_lane_bottom = device_data.loc[device_data['Margin Bottom (volt)'].idxmin(), 'LanePCIeNo']
    worst_lane_left = device_data.loc[device_data['Margin Left Offset'].idxmin(), 'LanePCIeNo']
    worst_lane_right = device_data.loc[device_data['Margin Right Offset'].idxmin(), 'LanePCIeNo']

    worst_lane = min(
        [worst_lane_top, worst_lane_bottom, worst_lane_left, worst_lane_right],
        key=lambda lane: sum([
            device_data.loc[device_data['LanePCIeNo'] == lane, 'Margin Top (volt)'].min(),
            device_data.loc[device_data['LanePCIeNo'] == lane, 'Margin Bottom (volt)'].min(),
            device_data.loc[device_data['LanePCIeNo'] == lane, 'Margin Left Offset'].min(),
            device_data.loc[device_data['LanePCIeNo'] == lane, 'Margin Right Offset'].min(),
        ])
    )

    min_left_offset = device_data.loc[device_data['LanePCIeNo'] == worst_lane, 'Margin Left Offset'].min()
    min_right_offset = device_data.loc[device_data['LanePCIeNo'] == worst_lane, 'Margin Right Offset'].min()
    min_top_volt = device_data.loc[device_data['LanePCIeNo'] == worst_lane, 'Margin Top (volt)'].min()
    min_bottom_volt = device_data.loc[device_data['LanePCIeNo'] == worst_lane, 'Margin Bottom (volt)'].min()

    # Determine symmetric X-axis range
    axs[4].set_xlim(-20, 20)

    # Diamond Points for Worst Lane
    diamond_points = {
        'x': [-min_left_offset, 0, min_right_offset, 0, -min_left_offset],
        'y': [0, min_top_volt, 0, -min_bottom_volt, 0]
    }

    axs[4].plot(diamond_points['x'], diamond_points['y'], marker='o', linewidth=2, label=f'Lane {worst_lane}')
    axs[4].scatter(diamond_points['x'], diamond_points['y'], color='blue', s=80, zorder=5)
    axs[4].plot([-offset_criteria, 0, offset_criteria, 0, -offset_criteria],
                [0, volt_criteria, 0, -volt_criteria, 0], 'r--', linewidth=2)
    axs[4].set_title('Eye Diagram')
    axs[4].set_xlabel('Timing Margin')
    axs[4].set_ylabel('Voltage Margin(mV)')
    axs[4].legend(loc='upper right')
    axs[4].grid(True)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    img_data = io.BytesIO()
    plt.savefig(img_data, format='png')
    plt.close(fig)
    img_data.seek(0)
    img_base64 = base64.b64encode(img_data.read()).decode()

    return img_base64


def html_generate(table_rows, summary_rows, criteria_rows, charts_html, complete_data_html):
    html_str = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Margin Analysis Report</title>
        <style>
            body {{
                background-color: #f0f8ff;
                color: #333333;
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 1200px;
                margin: 40px auto;
                background-color: #ffffff;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
            }}
            h1, h2 {{
                text-align: center;
                color: #333333;
            }}
            h1 {{
                margin-bottom: 20px;
            }}
            h2 {{
                margin-top: 0;
                margin-bottom: 20px;
            }}
            .chart-container {{
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
            }}
            .chart {{
                margin: 20px;
                border: 1px solid #dddddd;
                border-radius: 8px;
                padding: 10px;
                background-color: #fafafa;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.05);
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
                background-color: #ffffff;
            }}
            table, th, td {{
                border: 1px solid #dddddd;
            }}
            th, td {{
                padding: 15px;
                text-align: center;
            }}
            th {{
                background-color: #f0f0f0;
                color: #333333;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            tr:hover {{
                background-color: #f1f1f1;
            }}
            .complete-data {{
                margin-top: 40px;
                overflow-x: auto;
                font-size: 12px; /* Raw Data font size */
            }}
            .complete-data table, .complete-data th, .complete-data td {{
                border: 1px solid #dddddd;
            }}
            .complete-data th, .complete-data td {{
                padding: 5px;
                text-align: center;
                height: 5px; /* Raw Data table height */
            }}
            .complete-data th {{
                background-color: #f0f0f0;
                color: #333333;
            }}
            .complete-data th {{
                width: 25%; /* Raw Data table width */
            }}
            .title-header {{
                font-size: 20px;
                font-weight: bold;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Margin Analysis Report</h1>
            <table>
                <tr>
                    <th colspan="4" class="title-header">Data Information</th>
                </tr>
                <tr>
                    <th>Bus</th>
                    <th>Device</th>
                    <th>Function</th>
                    <th>BIOS</th>
                </tr>
                {}
            </table>
            <table>
                <tr>
                    <th colspan="6" class="title-header">Worst Cases Summary</th>
                </tr>
                <tr>
                    <th>Lane</th>
                    <th>Margin Top (mV)</th>
                    <th>Margin Bottom (mV)</th>
                    <th>Margin Left Offset</th>
                    <th>Margin Right Offset</th>
                    <th>LCLocalPreset</th>
                </tr>
                {}
            </table>
            <table>
                <tr>
                    <th colspan="4" class="title-header">AMD Criteria</th>
                </tr>
                <tr>
                    <th>Margin Top (mV)</th>
                    <th>Margin Bottom (mV)</th>
                    <th>Margin Left Offset</th>
                    <th>Margin Right Offset</th>
                </tr>
                {}
            </table>
            <div class="chart-container">
                {}
            </div>
            <div class="complete-data">
                <h2>Raw Data</h2>
                {}
            </div>
        </div>
    </body>
    </html>
    """
    html_output = html_str.format(table_rows, summary_rows, criteria_rows, charts_html, complete_data_html)
    return html_output

def browse():
    filename = askopenfilename(title="Result Directory",
                               filetypes=[("Margin Result", "*.csv"), ("all files", "*.*")])
    if filename:
        E_Raw_data.delete(0, END)
        E_Raw_data.insert(0, filename)

def html_output(file_path, full_html):
    output_file_path = os.path.splitext(file_path)[0] + '.html'
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(full_html)

def generate_button():
    file_path = str.strip(E_Raw_data.get())
    offset_criteria = float(str.strip(E_offset_cri.get()))
    volt_criteria = float(str.strip(E_volt_cri.get()))

    # Load data
    data = pd.read_csv(file_path)

    df_plot = data[
        [' Bus', 'Device', 'Function', 'LanePCIeNo', 'Margin Top (volt)', 'Margin Bottom (volt)', 'Margin Left Offset',
         ' Margin Right Offset', 'LCLocalPreset']].copy()
    df_plot['Margin Left Offset'] = df_plot['Margin Left Offset']
    df_plot['Margin Right Offset'] = df_plot[' Margin Right Offset']
    df_plot['Margin Top (volt)'] = df_plot['Margin Top (volt)'] * 1000  # Convert to mV
    df_plot['Margin Bottom (volt)'] = df_plot['Margin Bottom (volt)'] * 1000  # Convert to mV
    df_plot['LCLocalPreset'] = df_plot['LCLocalPreset']
    df_plot['Bus_Device_Function'] = df_plot.apply(
        lambda row: f"{int(row[' Bus'])}:{int(row['Device'])}.{int(row['Function'])}", axis=1)

    # Find worst cases for each margin
    worst_top_lane = df_plot.loc[df_plot['Margin Top (volt)'].idxmin()]
    worst_bottom_lane = df_plot.loc[df_plot['Margin Bottom (volt)'].idxmin()]
    worst_left_lane = df_plot.loc[df_plot['Margin Left Offset'].idxmin()]
    worst_right_lane = df_plot.loc[df_plot['Margin Right Offset'].idxmin()]
    worst_preset_lane = df_plot.loc[df_plot['LCLocalPreset'].idxmin()]

    # Generate a single row for each worst condition
    summary_rows = f"""
    <tr>
        <td>lane {worst_top_lane['LanePCIeNo']}</td>
        <td>{worst_top_lane['Margin Top (volt)']:.5f}</td>
        <td>{worst_top_lane['Margin Bottom (volt)']:.5f}</td>
        <td>{worst_top_lane['Margin Left Offset']}</td>
        <td>{worst_top_lane['Margin Right Offset']}</td>
        <td>{worst_preset_lane['LCLocalPreset']}</td>
    </tr>
    <tr>
        <td>lane {worst_bottom_lane['LanePCIeNo']}</td>
        <td>{worst_bottom_lane['Margin Top (volt)']:.5f}</td>
        <td>{worst_bottom_lane['Margin Bottom (volt)']:.5f}</td>
        <td>{worst_bottom_lane['Margin Left Offset']}</td>
        <td>{worst_bottom_lane['Margin Right Offset']}</td>
        <td>{worst_preset_lane['LCLocalPreset']}</td>
    </tr>
    <tr>
        <td>lane {worst_left_lane['LanePCIeNo']}</td>
        <td>{worst_left_lane['Margin Top (volt)']:.5f}</td>
        <td>{worst_left_lane['Margin Bottom (volt)']:.5f}</td>
        <td>{worst_left_lane['Margin Left Offset']}</td>
        <td>{worst_left_lane['Margin Right Offset']}</td>
        <td>{worst_preset_lane['LCLocalPreset']}</td>
    </tr>
    <tr>
        <td>lane {worst_right_lane['LanePCIeNo']}</td>
        <td>{worst_right_lane['Margin Top (volt)']:.5f}</td>
        <td>{worst_right_lane['Margin Bottom (volt)']:.5f}</td>
        <td>{worst_right_lane['Margin Left Offset']}</td>
        <td>{worst_right_lane['Margin Right Offset']}</td>
        <td>{worst_preset_lane['LCLocalPreset']}</td>
    </tr>
    """

    unique_info = data[[' Bus', 'Device', 'Function', 'BIOS']].drop_duplicates()

    table_rows = ""
    charts_html = ""
    criteria_rows = f"""
    <tr>
        <td>{volt_criteria}</td>
        <td>{volt_criteria}</td>
        <td>{offset_criteria}</td>
        <td>{offset_criteria}</td>
    </tr>
    """

    table_rows = ""
    for _, row in unique_info.iterrows():
        table_rows += f"""
        <tr>
            <td>{int(row[' Bus'])}</td>
            <td>{int(row['Device'])}</td>
            <td>{int(row['Function'])}</td>
            <td>{row['BIOS']}</td>
        </tr>
        """

    unique_devices = df_plot['Bus_Device_Function'].unique()
    charts_html = ""
    for device in unique_devices:
        device_data = df_plot[df_plot['Bus_Device_Function'] == device]
        img_base64 = generate_plots(device_data, device, volt_criteria, offset_criteria)
        chart_html = f'<div class="chart"><img src="data:image/png;base64,{img_base64}" /></div>'
        charts_html += chart_html

    complete_data_html = data.to_html(index=False)

    # Generate the full HTML content
    full_html = html_generate(
        table_rows,
        summary_rows,
        criteria_rows,
        charts_html,
        complete_data_html
    )

    # Write the full HTML content to the output file
    html_output(file_path, full_html)



# main script
rootframe = Tk()
rootframe.title("Visualized Margin Result")
rootframe.wm_geometry("%dx%d+%d+%d" % (640, 230, 200, 100))
rootframe.resizable(0, 0)
# Raw Data Path
Log_Label = LabelFrame(rootframe, text=" Raw Data Path ", font=("arial", 10), height=75, width=600)
Log_Label.place(x=20, y=10)
# Raw Data Folder
E_Raw_data = Entry(rootframe, width=65, font=("arial", 10))
E_Raw_data.place(x=35, y=40)
B_Raw_data = Button(rootframe, text=" Browse.. ", command=browse, pady=2, width=8, font=("arial", 12, "bold"))
B_Raw_data.place(x=515, y=30)
# Criteria
Criteria_Label = LabelFrame(rootframe, text=" AMD Criteria ", font=("arial", 10), height=115, width=300)
Criteria_Label.place(x=20, y=90)
# Volt Margin
L_volt_cri = Label(rootframe, text="Volt Margin (mV) :", height=2, font=("arial", 10))
L_volt_cri.place(x=35, y=120)
E_volt_cri = Entry(rootframe, width=15, font=("arial", 10))
E_volt_cri.insert(0, "25")
E_volt_cri.place(x=170, y=130)
# Timing Margin
L_offset_cri = Label(rootframe, text="Timing Margin :", height=2, font=("arial", 10))
L_offset_cri.place(x=35, y=150)
E_offset_cri = Entry(rootframe, width=15, font=("arial", 10))
E_offset_cri.insert(0, "9")
E_offset_cri.place(x=170, y=160)
# Generate Button
B_Generate = Button(rootframe, text="Generate", command=generate_button, pady=10, width=10, font=("arial", 14, "bold"))
B_Generate.place(x=420, y=125)

rootframe.mainloop()

