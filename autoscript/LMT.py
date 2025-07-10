import os
import io
import base64
import pandas as pd
import matplotlib.pyplot as plt

# ========= 使用者可修改區 =========
input_folder = r"H:\Astera_retimer\Astera LMT compare RXB\Intel LMT+Kauai+Genoa+P5+Slot12\run5 csv"
ui_criteria = 10  # Timing Margin UI 標準
volt_criteria = 25  # Voltage Margin mV 標準
# =================================

column_map = {
    "Left (%UI)": "Margin Left (UI)",
    "Right (%UI)": "Margin Right (UI)",
    "Up (mV)": "Margin Top (volt)",
    "Down (mV)": "Margin Bottom (volt)",
}

def standardize_columns(df):
    df = df.rename(columns=column_map)
    df["Total Phase(UI)"] = df["Margin Left (UI)"].abs() + df["Margin Right (UI)"].abs()
    df["Total Volt(volt)"] = df["Margin Top (volt)"].abs() + df["Margin Bottom (volt)"].abs()
    return df

def find_worst_cases(data):
    data['EH'] = data['Total Volt(volt)']
    data['EW'] = data['Total Phase(UI)']
    data['EH_EW'] = data['EH'] * data['EW']
    return {
        'Worst EH': data.loc[data['EH'].idxmin()],
        'Worst EW': data.loc[data['EW'].idxmin()],
        'Worst EH*EW': data.loc[data['EH_EW'].idxmin()]
    }

def generate_eye_diagram(ax, worst_cases, ui_criteria, volt_criteria):
    def plot_eye(case, color, label):
        x = [case['Margin Left (UI)'], 0, case['Margin Right (UI)'], 0, case['Margin Left (UI)']]
        y = [0, case['Margin Top (volt)'], 0, case['Margin Bottom (volt)'], 0]
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
    ax.set_ylim(-max_volt - 10, max_volt + 10)
    ax.set_title("Eye Diagrams")
    ax.set_xlabel('Timing Margin (UI)')
    ax.set_ylabel('Voltage Margin (mV)')
    ax.grid(True)

    x_crit = [-ui_criteria, 0, ui_criteria, 0, -ui_criteria]
    y_crit = [0, volt_criteria, 0, -volt_criteria, 0]
    ax.plot(x_crit, y_crit, color='red', linestyle='--', linewidth=2, label='Criteria Eye')
    ax.scatter(x_crit, y_crit, color='red')

    colors = ['blue', 'green', 'orange']
    labels = ['Worst EH', 'Worst EW', 'Worst EH*EW']
    for key, color, label in zip(labels, colors, labels):
        plot_eye(worst_cases[key], color, f"{label} (Lane {worst_cases[key]['Lane']})")

    ax.legend(loc='upper right')

def generate_html(data, eye_diagram_base64, ui_criteria, volt_criteria, output_file):
    summary = find_worst_cases(data)

    charts_html = f'<div class="chart"><img src="data:image/png;base64,{eye_diagram_base64}" /></div>'

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
    <tr><th>Lane</th><th>EH*EW</th><th>Margin Top (mV)</th><th>Margin Bottom (mV)</th><th>Margin Left (UI) (UI)</th><th>Margin Right (UI) (UI)</th></tr>"""

    for case in summary.values():
        html += f"<tr><td>{case['Lane']}</td><td>{case['EH_EW']:.1f}</td>"
        html += f"<td>{case['Margin Top (volt)']:.1f}</td><td>{case['Margin Bottom (volt)']:.1f}</td>"
        html += f"<td>{case['Margin Left (UI)']}</td><td>{case['Margin Right (UI)']}</td></tr>"

    html += f"""</table>
    <table><tr><th colspan="4" class="title-header">Astera Criteria</th></tr>
    <tr><th>Margin Top (mV)</th><th>Margin Bottom (mV)</th><th>Margin Left (UI) (UI)</th><th>Margin Right (UI) (UI)</th></tr>
    <tr><td>{volt_criteria}</td><td>{volt_criteria}</td><td>{ui_criteria}</td><td>{ui_criteria}</td></tr></table>
    <div class="chart-container">{charts_html}</div>
    <div class="raw-table"><div class="title-header">Raw Data</div>{data.to_html(index=False, border=1)}</div></div></body></html>"""

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML report saved to: {output_file}")

# 主流程
all_data = []
for file in os.listdir(input_folder):
    if file.endswith(".csv"):
        path = os.path.join(input_folder, file)
        try:
            df = pd.read_csv(path)
            df = standardize_columns(df)
            all_data.append(df)
        except Exception as e:
            print(f"Error reading {file}: {e}")

if not all_data:
    raise ValueError("No valid CSV files found.")

combined_df = pd.concat(all_data, ignore_index=True)
worst = find_worst_cases(combined_df)

fig, ax = plt.subplots(figsize=(12, 8))
generate_eye_diagram(ax, worst, ui_criteria, volt_criteria)
buf = io.BytesIO()
plt.savefig(buf, format="png")
buf.seek(0)
eye_base64 = base64.b64encode(buf.read()).decode()
plt.close()

output_html_path = os.path.join(input_folder, "combined_margin_report.html")
generate_html(combined_df, eye_base64, ui_criteria, volt_criteria, output_html_path)
