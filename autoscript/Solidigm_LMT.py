import os
import pandas as pd
import numpy as np
from datetime import datetime
import base64

Criteria = {
    "Top (mV)": "15",
    "Bottom (mV)": "-15",
    "Left (UI)": "-0.15",
    "Right (UI)": "0.15"
}

def load_csv(file_path):
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return None, None

    try:
        config_cols = ['bdf', 'type', 'alias', 'vid', 'did', 'speed', 'width', 'max speed', 'max width', 'model', 'serial number', 'firmware', 'temperature', 'selected']
        config_df = pd.read_csv(file_path, skiprows=2, nrows=4, names=config_cols, header=None, skipinitialspace=True)
        margin_df = pd.read_csv(file_path, skiprows=8, header=0, skipinitialspace=True)
        numeric_columns = ['right', 'left', 'up', 'down', 'right(uI)', 'left(uI)', 'up(mV)', 'down(mV)', 'temperature', 'lane']
        for col in numeric_columns:
            margin_df[col] = pd.to_numeric(margin_df[col], errors='coerce').fillna(0)
        margin_df['lane'] = margin_df['lane'].astype(int)
        required_cols = ['bdf', 'type', 'lane', 'right', 'left', 'up', 'down', 'right(uI)', 'left(uI)', 'up(mV)', 'down(mV)', 'temperature']
        margin_df = margin_df[required_cols]
        return margin_df, config_df
    except Exception as e:
        print(f"Error loading CSV: {e}")
        return None, None

def parse_bdf(bdf_string):
    try:
        parts = bdf_string.strip().split(':')
        bus = parts[1]
        device_function = parts[2].split('.')
        device = device_function[0]
        function = device_function[1]
        return bus, device, function
    except Exception as e:
        print(f"Error parsing BDF string '{bdf_string}': {e}")
        return 'N/A', 'N/A', 'N/A'

def get_bdf_info(config_df):
    devices = []
    if not config_df.empty:
        for _, row in config_df.iterrows():
            if pd.notna(row['bdf']):
                bus, device, function = parse_bdf(row['bdf'])
                devices.append((
                    bus, device, function,
                    row.get('type', 'N/A'),
                    row.get('speed', 'N/A'),
                    row.get('width', 'N/A'),
                    row.get('model', 'N/A'),
                    row.get('serial number', 'N/A'),
                    row.get('firmware', 'N/A')
                ))
    return devices

def calculate_eye_metrics(df):
    df['EH*EW'] = (df['right(uI)'] - df['left(uI)']) * (df['up(mV)'] - df['down(mV)'])
    return df

def get_worst_cases(df):
    worst_cases = []
    if not df.empty:
        # EH*EW: smallest is worst
        worst_eh_ew = df.loc[df['EH*EW'].idxmin()].copy()
        worst_eh_ew['worst_metric'] = 'EH*EW'
        worst_cases.append(worst_eh_ew)
        
        # Top (mV): smallest is worst
        worst_up_mv = df.loc[df['up(mV)'].idxmin()].copy()
        worst_up_mv['worst_metric'] = 'Top (mV)'
        worst_cases.append(worst_up_mv)
        
        # Bottom (mV): largest (least negative) is worst
        worst_down_mv = df.loc[df['down(mV)'].idxmax()].copy()
        worst_down_mv['worst_metric'] = 'Bottom (mV)'
        worst_cases.append(worst_down_mv)
        
        # Left (UI): largest (least negative) is worst
        worst_left_ui = df.loc[df['left(uI)'].idxmax()].copy()
        worst_left_ui['worst_metric'] = 'Left (UI)'
        worst_cases.append(worst_left_ui)
        
        # Right (UI): smallest is worst
        worst_right_ui = df.loc[df['right(uI)'].idxmin()].copy()
        worst_right_ui['worst_metric'] = 'Right (UI)'
        worst_cases.append(worst_right_ui)
    
    return pd.DataFrame(worst_cases)

def generate_html_report(margin_df, worst_cases, output_path, config_df):
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    config_df = config_df.fillna("-")
    devices = get_bdf_info(config_df)
    output_dir = os.path.dirname(output_path)
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif')
    image_files = [f for f in os.listdir(output_dir) if os.path.isfile(os.path.join(output_dir, f)) and f.lower().endswith(image_extensions)]
    image_files.sort()

    html_header = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
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
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            border: 1px solid #dddddd;
            padding: 10px;
            text-align: center;
        }}
        th {{
            background-color: #f0f0f0;
        }}
        .title-header {{
            font-size: 20px;
            font-weight: bold;
        }}
        .image-section {{
            margin-top: 20px;
            text-align: center;
        }}
        .image-section img {{
            max-width: 100%;
            height: auto;
            margin: 10px 0;
            border: 1px solid #dddddd;
            border-radius: 5px;
        }}
        .worst-metric {{
            font-weight: bold;
            color: #ff0000;
        }}
    </style>
</head>
<body>
<div class="container">
<h1>Margin Analysis Report</h1>
"""

    html_data_info = """
<table>
<tr><th colspan="7" class="title-header">Data Information</th></tr>
<tr><th>BDF</th><th>Type</th><th>Speed</th><th>Width</th><th>Model</th><th>Serial Number</th><th>Firmware</th></tr>
"""
    for b, d, f, t, s, w, m, sn, fw in devices:
        html_data_info += f"<tr><td>{b}:{d}.{f}</td><td>{t}</td><td>{s}</td><td>{w}</td><td>{m}</td><td>{sn}</td><td>{fw}</td></tr>"

    html_worst = """
</table>
<table>
<tr><th colspan="6" class="title-header">Worst Cases Summary</th></tr>
<tr><th>Lane</th><th>EH*EW</th><th>Top (mV)</th><th>Bottom (mV)</th><th>Left (UI)</th><th>Right (UI)</th></tr>
"""
    for _, row in worst_cases.iterrows():
        lane = int(row["lane"])
        worst_metric = row["worst_metric"]
        eh_ew = f"<td class='worst-metric'>{row['EH*EW']:.1f}</td>" if worst_metric == "EH*EW" else f"<td>{row['EH*EW']:.1f}</td>"
        up_mv = f"<td class='worst-metric'>{row['up(mV)']:.1f}</td>" if worst_metric == "Top (mV)" else f"<td>{row['up(mV)']:.1f}</td>"
        down_mv = f"<td class='worst-metric'>{row['down(mV)']:.1f}</td>" if worst_metric == "Bottom (mV)" else f"<td>{row['down(mV)']:.1f}</td>"
        left_ui = f"<td class='worst-metric'>{row['left(uI)']:.2f}</td>" if worst_metric == "Left (UI)" else f"<td>{row['left(uI)']:.2f}</td>"
        right_ui = f"<td class='worst-metric'>{row['right(uI)']:.2f}</td>" if worst_metric == "Right (UI)" else f"<td>{row['right(uI)']:.2f}</td>"
        html_worst += f"<tr><td>{lane}</td>{eh_ew}{up_mv}{down_mv}{left_ui}{right_ui}</tr>"

    html_images = """
</table>
<div class="image-section">
<h2>Images</h2>
"""
    if image_files:
        for image in image_files:
            image_path = os.path.join(output_dir, image)
            try:
                with open(image_path, 'rb') as img_file:
                    img_data = base64.b64encode(img_file.read()).decode('utf-8')
                # Determine MIME type based on file extension
                ext = os.path.splitext(image)[1].lower()
                mime_types = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif'
                }
                mime = mime_types.get(ext, 'image/png')
                html_images += f'<img src="data:{mime};base64,{img_data}" alt="{image}" /><br>'
            except Exception as e:
                print(f"Error embedding image {image}: {e}")
                html_images += f"<p>Error embedding image: {image}</p><br>"
    else:
        html_images += "<p>No images found in the directory.</p>"
    html_images += "</div>"

    html_raw = """
<table>
<tr><th colspan="12" class="title-header">Raw Data</th></tr>
<tr><th>BDF</th><th>Type</th><th>Lane</th><th>Right</th><th>Left</th><th>Up</th><th>Down</th><th>Right (uI)</th><th>Left (uI)</th><th>Up (mV)</th><th>Down (mV)</th><th>Temp</th></tr>
"""
    margin_df = margin_df.fillna('-')
    for _, row in margin_df.iterrows():
        lane = int(row['lane'])
        html_raw += f"<tr><td>{row['bdf']}</td><td>{row['type']}</td><td>{lane}</td><td>{row['right']:.1f}</td><td>{row['left']:.1f}</td><td>{row['up']:.1f}</td><td>{row['down']:.1f}</td><td>{row['right(uI)']:.2f}</td><td>{row['left(uI)']:.2f}</td><td>{row['up(mV)']:.1f}</td><td>{row['down(mV)']:.1f}</td><td>{row['temperature']:.1f}</td></tr>"

    html_footer = """
</table>
</div>
</body>
</html>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_header + html_data_info + html_worst + html_images + html_raw + html_footer)

def main(input_csv):
    margin_df, config_df = load_csv(input_csv)
    if margin_df is None or config_df is None:
        return
    margin_df = calculate_eye_metrics(margin_df)
    worst_cases = get_worst_cases(margin_df)
    output_filename = f"Margin_Analysis_Report_{os.path.splitext(os.path.basename(input_csv))[0]}.html"
    output_path = os.path.join(os.path.dirname(input_csv), output_filename)
    generate_html_report(margin_df, worst_cases, output_path, config_df)
    print(f"Report generated at: {output_path}")

if __name__ == "__main__":
    input_csv = r"C:\Users\dchen52\OneDrive - Lenovo\Documents\Solidigm\PCLMT_RESULTS_Ver3\pclmtresult_2025_01_17_19_53_35\pclmtresult_2025_01_17_19_53_35.csv"
    main(input_csv)