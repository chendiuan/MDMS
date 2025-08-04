import os
import io
import base64
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import re

# ========= 使用者可修改區 =========
input_folder = r"C:\Users\dchen52\OneDrive - Lenovo\Desktop\Monaco data\swapp_data\Ferrari_slot_4"  # Update to your folder path
ui_criteria = 5  # Timing Margin UI 標準
volt_criteria = 50  # Voltage Margin mV 標準
# =================================

def parse_txt_file(filepath):
    """Parse a single .txt file and extract margin data."""
    data = {
        'Lane': None,
        'Margin Left (UI)': None,
        'Margin Right (UI)': None,
        'Margin Top (volt)': None,
        'Margin Bottom (volt)': None,
        'Mmaxtimingoffset': None,
        'Mnumtimingsteps': None,
        'Mmaxvoltageoffset': None,
        'Mnumvoltagesteps': None
    }
    
    # Extract lane number from filename or content
    filename = os.path.basename(filepath)
    lane_match = re.search(r'lane(\d+)', filename, re.IGNORECASE)
    if lane_match:
        data['Lane'] = int(lane_match.group(1))
    
    with open(filepath, 'r') as f:
        content = f.read()
        # Extract lane from header if not in filename
        if data['Lane'] is None:
            header_match = re.search(r'Data for Lane (\d+)', content)
            if header_match:
                data['Lane'] = int(header_match.group(1))
        
        # Parse margin data
        right_ui = re.search(r'Right Side UI\s*=\s*([\d.]+)%', content)
        left_ui = re.search(r'Left Side UI\s*=\s*([\d.]+)%', content)
        up_volt = re.search(r'Up voltage\s*=\s*([\d.]+)mV', content)
        down_volt = re.search(r'Down voltage\s*=\s*([\d.]+)mV', content)
        max_timing = re.search(r'Mmaxtimingoffset\s*(\d+)', content)
        num_timing = re.search(r'Mnumtimingsteps\s*(\d+)', content)
        max_volt = re.search(r'Mmaxvoltageoffset\s*(\d+)', content)
        num_volt = re.search(r'Mnumvoltagesteps\s*(\d+)', content)
        
        if right_ui:
            data['Margin Right (UI)'] = float(right_ui.group(1))
        if left_ui:
            data['Margin Left (UI)'] = float(left_ui.group(1))
        if up_volt:
            data['Margin Top (volt)'] = float(up_volt.group(1)) / 1000  # Convert mV to volts
        if down_volt:
            data['Margin Bottom (volt)'] = float(down_volt.group(1)) / 1000  # Convert mV to volts
        if max_timing:
            data['Mmaxtimingoffset'] = int(max_timing.group(1))
        if num_timing:
            data['Mnumtimingsteps'] = int(num_timing.group(1))
        if max_volt:
            data['Mmaxvoltageoffset'] = int(max_volt.group(1))
        if num_volt:
            data['Mnumvoltagesteps'] = int(num_volt.group(1))
    
    return data

def standardize_columns(df):
    """Calculate total phase and voltage for the DataFrame."""
    df["Total Phase(UI)"] = df["Margin Left (UI)"].abs() + df["Margin Right (UI)"].abs()
    df["Total Volt(volt)"] = df["Margin Top (volt)"].abs() + df["Margin Bottom (volt)"].abs()
    return df

def find_worst_cases(data):
    """Identify worst-case values for each metric."""
    data['ML'] = data['Margin Left (UI)']
    data['MR'] = data['Margin Right (UI)']
    data['MT'] = data['Margin Top (volt)']
    data['MB'] = data['Margin Bottom (volt)']
    data['EH'] = data['Total Volt(volt)']
    data['EW'] = data['Total Phase(UI)']
    data['EH_EW'] = data['EH'] * data['EW']
    return {
        'Worst ML': data.loc[data['ML'].idxmin()],
        'Worst MR': data.loc[data['MR'].idxmin()],
        'Worst MT': data.loc[data['MT'].idxmin()],
        'Worst MB': data.loc[data['MB'].idxmin()],
        'Worst EH*EW': data.loc[data['EH_EW'].idxmin()]
    }

def generate_eye_diagram(ax, worst_cases, ui_criteria, volt_criteria):
    """Generate eye diagram for worst-case scenarios with Margin Left as negative."""
    def plot_eye(case, color, label):
        x = [-case['Margin Left (UI)'], 0, case['Margin Right (UI)'], 0, -case['Margin Left (UI)']]  # Ensure Left is negative
        y = [0, case['Margin Top (volt)'], 0, -case['Margin Bottom (volt)'], 0]  # Bottom is negative
        ax.plot(x, y, marker='o', label=label, color=color)
        ax.scatter(x, y, color=color)

    max_ui = max(
        max(abs(case['Margin Left (UI)']), abs(case['Margin Right (UI)']))
        for case in worst_cases.values()
    )
    max_volt = max(
        max(abs(case['Margin Top (volt)']), abs(case['Margin Bottom (volt)']))
        for case in worst_cases.values()
    )

    ax.set_xlim(-max_ui - 10, max_ui + 10)
    ax.set_ylim(-max_volt - 0.01, max_volt + 0.01)  # In volts
    ax.set_title("Eye Diagrams")
    ax.set_xlabel('Timing Margin (UI)')
    ax.set_ylabel('Voltage Margin (Volt)')
    ax.grid(True)

    x_crit = [-ui_criteria, 0, ui_criteria, 0, -ui_criteria]
    y_crit = [0, volt_criteria / 1000, 0, -volt_criteria / 1000, 0]  # Convert mV to volts
    ax.plot(x_crit, y_crit, color='red', linestyle='--', linewidth=2, label='Criteria Eye')
    ax.scatter(x_crit, y_crit, color='red')

    colors = ['blue', 'green', 'orange', 'tomato', 'purple']
    labels = ['Worst ML', 'Worst MR', 'Worst MT', 'Worst MB', 'Worst EH*EW']
    for key, color, label in zip(labels, colors, labels):
        plot_eye(worst_cases[key], color, f"{label} (Lane {worst_cases[key]['Lane']})")

    ax.legend(loc='upper right')

def generate_eh_ew_plots(data, volt_criteria, ui_criteria):
    """Generate EH and EW plots for all lanes."""
    fig, axs = plt.subplots(2, 1, figsize=(12, 16))
    axs = axs.flatten()

    unique_lanes = sorted(data['Lane'].unique())

    # Eye Height (Top & Bottom)
    top_values = [data.loc[data['Lane'] == lane, 'Margin Top (volt)'].iloc[0]
                  if len(data.loc[data['Lane'] == lane, 'Margin Top (volt)']) > 0
                  else np.nan
                  for lane in unique_lanes]
    bottom_values = [-data.loc[data['Lane'] == lane, 'Margin Bottom (volt)'].abs().iloc[0]
                     if len(data.loc[data['Lane'] == lane, 'Margin Bottom (volt)']) > 0
                     else np.nan
                     for lane in unique_lanes]

    axs[0].plot(unique_lanes, top_values, marker='o', linestyle='-', linewidth=1.5, label='Top Margin')
    axs[0].scatter(unique_lanes, top_values, color='blue', s=80, zorder=5)
    axs[0].plot(unique_lanes, bottom_values, marker='o', linestyle='-', linewidth=1.5, label='Bottom Margin')
    axs[0].scatter(unique_lanes, bottom_values, color='blue', s=80, zorder=5)

    axs[0].set_title('Eye Height')
    axs[0].set_xlabel('Lane')
    axs[0].set_ylabel('Voltage Margin (Volt)')
    axs[0].grid(True)
    axs[0].axhline(y=volt_criteria / 1000, color='red', linestyle='--', linewidth=2, label='Criteria')  # Convert mV to volts
    axs[0].axhline(y=-volt_criteria / 1000, color='red', linestyle='--', linewidth=2)
    axs[0].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    axs[0].legend()

    # Eye Width (Left & Right Offset)
    left_values = [-data.loc[data['Lane'] == lane, 'Margin Left (UI)'].abs().iloc[0]
                   if len(data.loc[data['Lane'] == lane, 'Margin Left (UI)']) > 0
                   else np.nan
                   for lane in unique_lanes]
    right_values = [data.loc[data['Lane'] == lane, 'Margin Right (UI)'].iloc[0]
                    if len(data.loc[data['Lane'] == lane, 'Margin Right (UI)']) > 0
                    else np.nan
                    for lane in unique_lanes]

    axs[1].plot(unique_lanes, left_values, marker='o', linestyle='-', linewidth=1.5, label='Left Margin')
    axs[1].scatter(unique_lanes, left_values, color='blue', s=80, zorder=5)
    axs[1].plot(unique_lanes, right_values, marker='o', linestyle='-', linewidth=1.5, label='Right Margin')
    axs[1].scatter(unique_lanes, right_values, color='blue', s=80, zorder=5)

    axs[1].set_title('Eye Width')
    axs[1].set_xlabel('Lane')
    axs[1].set_ylabel('Timing Margin (UI)')
    axs[1].grid(True)
    axs[1].axhline(y=ui_criteria, color='red', linestyle='--', linewidth=2, label='Criteria')
    axs[1].axhline(y=-ui_criteria, color='red', linestyle='--', linewidth=2)
    axs[1].xaxis.set_major_locator(ticker.MaxNLocator(integer=True))
    axs[1].legend()

    plt.tight_layout(rect=[0, 0.03, 1, 0.95], h_pad=10)

    img_data = io.BytesIO()
    plt.savefig(img_data, format='png')
    plt.close(fig)
    img_data.seek(0)
    img_base64 = base64.b64encode(img_data.read()).decode()
    return img_base64

def generate_html(data, eye_diagram_base64, eh_ew_base64, ui_criteria, volt_criteria, output_file):
    """Generate HTML report with summary, criteria, plots, and raw data sorted by Lane."""
    summary = find_worst_cases(data)

    charts_html = f'<div class="chart"><img src="data:image/png;base64,{eh_ew_base64}" /></div>'
    charts_html += f'<div class="chart"><img src="data:image/png;base64,{eye_diagram_base64}" /></div>'

    # Filter raw data to include only original columns
    raw_data_columns = ['Lane', 'Margin Left (UI)', 'Margin Right (UI)', 'Margin Top (volt)', 
                        'Margin Bottom (volt)', 'Mmaxtimingoffset', 'Mnumtimingsteps', 
                        'Mmaxvoltageoffset', 'Mnumvoltagesteps']
    raw_data = data[raw_data_columns].copy()
    # Sort by Lane in ascending order
    raw_data = raw_data.sort_values(by='Lane', ascending=True)
    # Convert voltage columns to mV for display
    raw_data['Margin Top (volt)'] = raw_data['Margin Top (volt)'] * 1000
    raw_data['Margin Bottom (volt)'] = raw_data['Margin Bottom (volt)'] * 1000
    # Rename columns for display
    raw_data = raw_data.rename(columns={'Margin Top (volt)': 'Margin Top (mV)', 
                                        'Margin Bottom (volt)': 'Margin Bottom (mV)'})

    html = f"""<!DOCTYPE html>
    <html><head><meta charset="UTF-8"><title>Margin Analysis Report</title>
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
            h1 {{
                text-align: center;
                color: #333333;
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
            .title-header {{
                font-size: 20px;
                font-weight: bold;
                background-color: #f0f0f0;
                padding: 10px;
                text-align: center;
                border: 1px solid #dddddd;
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
            .eye-diagram {{
                text-align: center;
                margin-top: 40px;
                margin-bottom: 40px;
            }}
            .eye-diagram img {{
                max-width: 1000px;
                height: auto;
                border: 1px solid #ccc;
                background: white;
                padding: 5px;
            }}
            .raw-table {{
                margin-top: 40px;
                overflow-x: auto;
                font-size: 12px;
            }}
            .raw-table table, .raw-table th, .raw-table td {{
                border: 1px solid #dddddd;
            }}
            .raw-table th, .raw-table td {{
                padding: 5px;
                text-align: center;
                height: 5px;
            }}
            .raw-table th {{
                background-color: #f0f0f0;
                color: #333333;
            }}
        </style>
    </head><body><div class="container"><h1>Margin Analysis Report</h1>
    <table><tr><th colspan="6" class="title-header">Worst Cases Summary</th></tr>
    <tr><th>Lane</th><th>EH*EW</th><th>Margin Top (mV)</th><th>Margin Bottom (mV)</th><th>Margin Left (UI)</th><th>Margin Right (UI)</th></tr>"""

    # Generate table rows with red bold highlighting for worst-case values
    for key in ['Worst EH*EW', 'Worst MT', 'Worst MB', 'Worst ML', 'Worst MR']:
        case = summary[key]
        lane = case['Lane']
        eh_ew = f"<font color=\"red\" size=\"4\"><b>{case['EH_EW']:.1f}</b></font>" if key == 'Worst EH*EW' else f"{case['EH_EW']:.1f}"
        mt = f"<font color=\"red\" size=\"4\"><b>{case['Margin Top (volt)'] * 1000:.1f}</b></font>" if key == 'Worst MT' else f"{case['Margin Top (volt)'] * 1000:.1f}"
        mb = f"<font color=\"red\" size=\"4\"><b>{case['Margin Bottom (volt)'] * 1000:.1f}</b></font>" if key == 'Worst MB' else f"{case['Margin Bottom (volt)'] * 1000:.1f}"
        ml = f"<font color=\"red\" size=\"4\"><b>{case['Margin Left (UI)']:.1f}</b></font>" if key == 'Worst ML' else f"{case['Margin Left (UI)']:.1f}"
        mr = f"<font color=\"red\" size=\"4\"><b>{case['Margin Right (UI)']:.1f}</b></font>" if key == 'Worst MR' else f"{case['Margin Right (UI)']:.1f}"
        html += f"<tr><td>Lane {lane}</td><td>{eh_ew}</td><td>{mt}</td><td>{mb}</td><td>{ml}</td><td>{mr}</td></tr>"

    html += f"""</table>
    <table><tr><th colspan="4" class="title-header">Broadcom Criteria</th></tr>
    <tr><th>Margin Top (mV)</th><th>Margin Bottom (mV)</th><th>Margin Left (UI)</th><th>Margin Right (UI)</th></tr>
    <tr><td>{volt_criteria}</td><td>{volt_criteria}</td><td>{ui_criteria}</td><td>{ui_criteria}</td></tr></table>
    <div class="chart-container">{charts_html}</div>
    <div class="raw-table"><div class="title-header">Raw Data</div>{raw_data.to_html(index=False, border=1)}</div></div></body></html>"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML report saved to: {output_file}")

# 主流程
all_data = []
for file in os.listdir(input_folder):
    if file.endswith(".txt"):
        path = os.path.join(input_folder, file)
        try:
            data_row = parse_txt_file(path)
            all_data.append(data_row)
        except Exception as e:
            print(f"Error reading {file}: {e}")

if not all_data:
    raise ValueError("No valid .txt files found.")

combined_df = pd.DataFrame(all_data)
combined_df = standardize_columns(combined_df)

# Ensure numeric columns
for col in ['Margin Left (UI)', 'Margin Right (UI)', 'Margin Top (volt)', 'Margin Bottom (volt)', 
            'Total Phase(UI)', 'Total Volt(volt)', 'Mmaxtimingoffset', 'Mnumtimingsteps', 
            'Mmaxvoltageoffset', 'Mnumvoltagesteps']:
    if col in combined_df.columns:
        combined_df[col] = pd.to_numeric(combined_df[col], errors='coerce')

worst = find_worst_cases(combined_df)

fig, ax = plt.subplots(figsize=(12, 8))
generate_eye_diagram(ax, worst, ui_criteria, volt_criteria)
buf = io.BytesIO()
plt.savefig(buf, format="png")
buf.seek(0)
eye_base64 = base64.b64encode(buf.read()).decode()
plt.close()

eh_ew_base64 = generate_eh_ew_plots(combined_df, volt_criteria, ui_criteria)

output_html_path = os.path.join(input_folder, "combined_margin_report.html")
generate_html(combined_df, eye_base64, eh_ew_base64, ui_criteria, volt_criteria, output_html_path)