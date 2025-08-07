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
    fig, axs = plt.subplots(3, 1, figsize=(12, 24))
    axs = axs.flatten()

    file_path = str.strip(E_Raw_data.get())
    data = pd.read_csv(file_path)
    unique_lanes = sorted(device_data['LanePCIeNo'].unique())

    # Eye Height (Top & Bottom)
    for i in range(5):
        # Margin Top
        top_values = [device_data.loc[(device_data['LanePCIeNo'] == lane), 'Margin Top (volt)'].iloc[i]
                      if i < len(device_data.loc[(device_data['LanePCIeNo'] == lane), 'Margin Top (volt)'])
                      else None
                      for lane in unique_lanes]
        # Margin Bottom
        bottom_values = [-device_data.loc[(device_data['LanePCIeNo'] == lane), 'Margin Bottom (volt)'].iloc[i]
                         if i < len(device_data.loc[(device_data['LanePCIeNo'] == lane), 'Margin Bottom (volt)'])
                         else None
                         for lane in unique_lanes]

        axs[0].plot(unique_lanes, top_values, marker='o', linestyle='-', linewidth=1.5, label=f'Top Data Group {i + 1}')
        axs[0].scatter(unique_lanes, top_values, color='blue', s=80, zorder=5)

        axs[0].plot(unique_lanes, bottom_values, marker='o', linestyle='-', linewidth=1.5,
                    label=f'Bottom Data Group {i + 1}')
        axs[0].scatter(unique_lanes, bottom_values, color='blue', s=80, zorder=5)

    axs[0].set_title('Eye Height')
    axs[0].set_xlabel('Lane')
    axs[0].set_ylabel('Voltage Margin (mV)')
    axs[0].grid(True)
    axs[0].axhline(y=volt_criteria, color='red', linestyle='--', linewidth=2, label='Criteria')
    axs[0].axhline(y=-volt_criteria, color='red', linestyle='--', linewidth=2)
    axs[0].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # Eye Width (Left & Right Offset)
    for i in range(5):
        left_values = [-device_data.loc[(device_data['LanePCIeNo'] == lane), 'Margin Left Offset'].iloc[i]
                       if i < len(device_data.loc[(device_data['LanePCIeNo'] == lane), 'Margin Left Offset'])
                       else None
                       for lane in unique_lanes]
        right_values = [device_data.loc[(device_data['LanePCIeNo'] == lane), 'Margin Right Offset'].iloc[i]
                        if i < len(device_data.loc[(device_data['LanePCIeNo'] == lane), 'Margin Right Offset'])
                        else None
                        for lane in unique_lanes]

        axs[1].plot(unique_lanes, left_values, marker='o', linestyle='-', linewidth=1.5, label=f'Left Data Group {i + 1}')
        axs[1].scatter(unique_lanes, left_values, color='blue', s=80, zorder=5)

        axs[1].plot(unique_lanes, right_values, marker='o', linestyle='-', linewidth=1.5,
                    label=f'Right Data Group {i + 1}')
        axs[1].scatter(unique_lanes, right_values, color='blue', s=80, zorder=5)

    axs[1].set_title('Eye Width')
    axs[1].set_xlabel('Lane')
    axs[1].set_ylabel('Timing Margin')
    axs[1].grid(True)
    axs[1].axhline(y=offset_criteria, color='red', linestyle='--', linewidth=2, label='Criteria')
    axs[1].axhline(y=-offset_criteria, color='red', linestyle='--', linewidth=2)
    axs[1].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))

    # Eye Diagram for Worst EH, EW, EH*EW, EW Offset
    worst_cases = find_worst_cases(data)
    generate_eye_diagram(axs[2], worst_cases, volt_criteria, offset_criteria)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95], h_pad=10)

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
                    <th colspan="7" class="title-header">Worst Cases Summary</th>
                </tr>
                <tr>
                    <th>Lane</th>
                    <th>Eye High * Eye Width</th>
                    <th>Margin Top (mV)</th>
                    <th>Margin Bottom (mV)</th>
                    <th>Margin Left Offset</th>
                    <th>Margin Right Offset</th>
                    <th>LCBestPreset</th>
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

def find_worst_cases(data):
    worst_cases = []

    # Calculate EH, EW, EH*EW, EW offset for all lanes without considering loops
    data['EH'] = data['Total Volt(volt)'] * 1000  # Convert EW to mV by multiplying by 1000
    data['EW'] = data['Total Phase(UI)']
    data['EH_EW'] = data['EH'] * data['EW']
    data['EW_offset'] = data['Margin Left Offset'] + data['Margin Right Offset']

    # Find the worst values for the entire dataset
    worst_eh = data.loc[data['EH'].idxmin()]
    worst_ew = data.loc[data['EW'].idxmin()]
    worst_eh_ew = data.loc[data['EH_EW'].idxmin()]
    worst_ew_offset = data.loc[data['EW_offset'].idxmin()]

    return {
        'Worst EH': worst_eh,
        'Worst EW': worst_ew,
        'Worst EH*EW': worst_eh_ew,
        'Worst EW Offset': worst_ew_offset
    }

def generate_eye_diagram(ax, worst_cases, offset_criteria, volt_criteria):
    # Extract worst-case values
    worst_eh = worst_cases['Worst EH']
    worst_ew = worst_cases['Worst EW']
    worst_eh_ew = worst_cases['Worst EH*EW']
    worst_ew_offset = worst_cases['Worst EW Offset']

    ax.set_xlim(-20, 20)

    # Diamond Points for Worst EH, EW, EH*EW, EW Offset
    eye_diagrams = [
        {
            'label': f"Criteria",
            'x': [-volt_criteria, 0, volt_criteria, 0, -volt_criteria],
            'y': [0, offset_criteria/1000, 0, -offset_criteria/1000, 0],
            'color': 'red'
        },
        {
            'label': f"Loop {worst_eh['loop']} Lane {worst_eh['LanePCIeNo']} - Worst EH",
            'x': [-worst_eh['Margin Left Offset'], 0, worst_eh['Margin Right Offset'], 0, -worst_eh['Margin Left Offset']],
            'y': [0, worst_eh['Margin Top (volt)'], 0, -worst_eh['Margin Bottom (volt)'], 0],
            'color': 'blue'
        },
        {
            'label': f"Loop {worst_ew['loop']} Lane {worst_ew['LanePCIeNo']} - Worst EW",
            'x': [-worst_ew['Margin Left Offset'], 0, worst_ew['Margin Right Offset'], 0, -worst_ew['Margin Left Offset']],
            'y': [0, worst_ew['Margin Top (volt)'], 0, -worst_ew['Margin Bottom (volt)'], 0],
            'color': 'green'
        },
        {
            'label': f"Loop {worst_eh_ew['loop']} Lane {worst_eh_ew['LanePCIeNo']} - Worst EH*EW",
            'x': [-worst_eh_ew['Margin Left Offset'], 0, worst_eh_ew['Margin Right Offset'], 0, -worst_eh_ew['Margin Left Offset']],
            'y': [0, worst_eh_ew['Margin Top (volt)'], 0, -worst_eh_ew['Margin Bottom (volt)'], 0],
            'color': 'orange'
        },
        {
            'label': f"Loop {worst_ew_offset['loop']} Lane {worst_ew_offset['LanePCIeNo']} - Worst EW Offset",
            'x': [-worst_ew_offset['Margin Left Offset'], 0, worst_ew_offset['Margin Right Offset'], 0, -worst_ew_offset['Margin Left Offset']],
            'y': [0, worst_ew_offset['Margin Top (volt)'], 0, -worst_ew_offset['Margin Bottom (volt)'], 0],
            'color': 'purple'
        }
    ]

    for diagram in eye_diagrams:
        ax.plot(diagram['x'], diagram['y'], marker='o', linewidth=2, label=diagram['label'], color=diagram['color'])
        ax.scatter(diagram['x'], diagram['y'], color=diagram['color'], s=80, zorder=5)

    ax.set_title("Eye Diagrams for Worst Cases")
    ax.set_xlabel('Timing Margin (UI)')
    ax.set_ylabel('Voltage Margin (Volt)')
    ax.legend(loc='upper right')
    ax.grid(True)

def generate_button():
    file_path = str.strip(E_Raw_data.get())
    offset_criteria = float(str.strip(E_offset_cri.get()))
    volt_criteria = float(str.strip(E_volt_cri.get()))

    # Load data
    data = pd.read_csv(file_path)

    df_plot = data[
        ['Bus', 'Device', 'Function', 'LanePCIeNo', 'Total Phase(UI)', 'Total Volt(volt)', 'Margin Top (volt)',
         'Margin Bottom (volt)', 'Margin Left Offset', 'Margin Right Offset', 'LCBestPreset']].copy()
    df_plot['Margin Left Offset'] = df_plot['Margin Left Offset']
    df_plot['Margin Right Offset'] = df_plot['Margin Right Offset']
    df_plot['Margin Top (volt)'] = df_plot['Margin Top (volt)'] * 1000  # Convert to mV
    df_plot['Margin Bottom (volt)'] = df_plot['Margin Bottom (volt)'] * 1000  # Convert to mV
    df_plot['Total Phase(UI)'] = df_plot['Total Phase(UI)']
    df_plot['Total Volt(volt)'] = df_plot['Total Volt(volt)'] * 1000  # Convert EW to mV by multiplying by 1000
    df_plot['EH*EW'] = df_plot['Total Phase(UI)'] * df_plot['Total Volt(volt)']
    df_plot['LCBestPreset'] = df_plot['LCBestPreset']
    df_plot['Bus_Device_Function'] = df_plot.apply(
        lambda row: f"{int(row['Bus'])}:{int(row['Device'])}.{int(row['Function'])}", axis=1)

    # Find worst cases for each margin
    worst_top_lane = df_plot.loc[df_plot['Margin Top (volt)'].idxmin()]
    worst_bottom_lane = df_plot.loc[df_plot['Margin Bottom (volt)'].idxmin()]
    worst_left_lane = df_plot.loc[df_plot['Margin Left Offset'].idxmin()]
    worst_right_lane = df_plot.loc[df_plot['Margin Right Offset'].idxmin()]
    worst_preset_lane = df_plot.loc[df_plot['LCBestPreset'].idxmin()]
    worst_EH_EW_lane = df_plot.loc[df_plot['EH*EW'].idxmin()]

    # Generate a single row for each worst condition
    summary_rows = f"""
    <tr>
        <td>lane {worst_EH_EW_lane['LanePCIeNo']}</font></td>
        <td><font color="orange", size="4"><b>{worst_EH_EW_lane['EH*EW']:.1f}</b></font></td>
        <td>{worst_EH_EW_lane['Margin Top (volt)']:.1f}</td>
        <td>{worst_EH_EW_lane['Margin Bottom (volt)']:.1f}</td>
        <td>{worst_EH_EW_lane['Margin Left Offset']}</td>
        <td>{worst_EH_EW_lane['Margin Right Offset']}</td>
        <td>{worst_EH_EW_lane['LCBestPreset']}</td>
    </tr>
    <tr>
        <td>lane {worst_top_lane['LanePCIeNo']}</td>
        <td>{worst_top_lane['EH*EW']:.1f}</td>
        <td><font color="blue", size="4"><b>{worst_top_lane['Margin Top (volt)']:.1f}</b></font></td>
        <td>{worst_top_lane['Margin Bottom (volt)']:.1f}</td>
        <td>{worst_top_lane['Margin Left Offset']}</td>
        <td>{worst_top_lane['Margin Right Offset']}</td>
        <td>{worst_top_lane['LCBestPreset']}</td>
    </tr>
    <tr>
        <td>lane {worst_bottom_lane['LanePCIeNo']}</td>
        <td>{worst_bottom_lane['EH*EW']:.1f}</td>
        <td>{worst_bottom_lane['Margin Top (volt)']:.1f}</td>
        <td><font color="blue", size="4"><b>{worst_bottom_lane['Margin Bottom (volt)']:.1f}</b></font></td>
        <td>{worst_bottom_lane['Margin Left Offset']}</td>
        <td>{worst_bottom_lane['Margin Right Offset']}</td>
        <td>{worst_bottom_lane['LCBestPreset']}</td>
    </tr>
    <tr>
        <td>lane {worst_left_lane['LanePCIeNo']}</td>
        <td>{worst_left_lane['EH*EW']:.1f}</td>
        <td>{worst_left_lane['Margin Top (volt)']:.1f}</td>
        <td>{worst_left_lane['Margin Bottom (volt)']:.1f}</td>
        <td><font color="green", size="4"><b>{worst_left_lane['Margin Left Offset']}</b></font></td>
        <td>{worst_left_lane['Margin Right Offset']}</td>
        <td>{worst_left_lane['LCBestPreset']}</td>
    </tr>
    <tr>
        <td>lane {worst_right_lane['LanePCIeNo']}</td>
        <td>{worst_right_lane['EH*EW']:.1f}</td>
        <td>{worst_right_lane['Margin Top (volt)']:.1f}</td>
        <td>{worst_right_lane['Margin Bottom (volt)']:.1f}</td>
        <td>{worst_right_lane['Margin Left Offset']}</td>
        <td><font color="green", size="4"><b>{worst_right_lane['Margin Right Offset']}</b></font></td>
        <td>{worst_right_lane['LCBestPreset']}</td>
    </tr>
    """

    unique_info = data[['Bus', 'Device', 'Function', 'BIOS']].drop_duplicates()

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
            <td>{int(row['Bus'])}</td>
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

