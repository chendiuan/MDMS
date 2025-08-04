import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import re
import os
import base64
from datetime import datetime

def parse_eye_vals(file_path):
    """Parse m_eye_vals and axis params from file"""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Extract m_eye_vals data
    eye_vals_section = re.search(r'\[3\] m_eye_vals,.*?(?=End of Data)', content, re.DOTALL)
    if not eye_vals_section:
        raise ValueError(f"Could not find m_eye_vals section in {file_path}")
    
    # Extract num_ptn, num_dac, num_phs
    num_ptn = int(re.search(r'num_ptn,\s*(\d+)', eye_vals_section.group()).group(1))
    num_dac = int(re.search(r'num_dac,\s*(\d+)', eye_vals_section.group()).group(1))
    num_phs = int(re.search(r'num_phs,\s*(\d+)', eye_vals_section.group()).group(1))
    
    # Extract phs_step_ui and dac_step_mv
    axis_params_section = re.search(r'\[2\] Axis Params,.*?(?=\[3\] m_eye_vals,)', content, re.DOTALL)
    if not axis_params_section:
        raise ValueError(f"Could not find Axis Params section in {file_path}")
    phs_step_ui = float(re.search(r'phs_step_ui,\s*([\d\.]+)', axis_params_section.group()).group(1))
    dac_step_mv = float(re.search(r'dac_step_mv,\s*([\d\.]+)', axis_params_section.group()).group(1))
    
    print(f"File: {file_path}, num_ptn={num_ptn}, num_dac={num_dac}, num_phs={num_phs}, phs_step_ui={phs_step_ui}, dac_step_mv={dac_step_mv}")
    
    # Initialize data array
    expected_shape = (num_ptn, num_dac, num_phs)
    eye_data = np.zeros(expected_shape)
    
    # Parse data lines
    pattern_lines = re.findall(r'(\d+),\s*(\d+),\s*([\d\.\s,-]+?)(?=\n\d+,\s*\d+,|\n\s*$)', eye_vals_section.group(), re.MULTILINE)
    for line_idx, line in enumerate(pattern_lines):
        pattern_idx = int(line[0])
        dac_idx = int(line[1])
        raw_values = line[2].strip().split(',')
        values = []
        for x in raw_values:
            x = x.strip()
            if x:
                try:
                    values.append(float(x))
                except ValueError:
                    print(f"Warning: Could not convert '{x}' to float in {file_path}, pattern {pattern_idx}, dac {dac_idx}. Skipping...")
                    continue
        
        if len(values) != num_phs:
            print(f"Warning: Expected {num_phs} values, got {len(values)} in {file_path}, pattern {pattern_idx}, dac {dac_idx}. Adjusting...")
            if len(values) < num_phs:
                values.extend([0.0] * (num_phs - len(values)))
            else:
                values = values[:num_phs]
        
        if pattern_idx < expected_shape[0] and dac_idx < expected_shape[1]:
            eye_data[pattern_idx, dac_idx, :] = values
        else:
            print(f"Warning: Invalid indices (pattern={pattern_idx}, dac={dac_idx}) in {file_path}. Skipping...")
    
    print(f"Parsed eye_data shape for {file_path}: {eye_data.shape}")
    return eye_data, num_ptn, num_dac, num_phs, phs_step_ui, dac_step_mv

def calculate_eye_metrics(eye_data, phs_step_ui, dac_step_mv, lane_id):
    """Calculate eye metrics: up(mV), down(mV), left(uI), right(uI), EH*EW"""
    combined_data = np.min(eye_data, axis=0)  # Shape: (num_dac, num_phs)
    threshold = 0.9  # Signal quality threshold for eye boundaries
    high_quality = combined_data >= threshold
    
    if not np.any(high_quality):
        print(f"Warning: No data above threshold {threshold} for Lane {lane_id}. Using fallback metrics.")
        center_dac, center_phase = np.unravel_index(np.argmax(combined_data), combined_data.shape)
        up_mv = down_mv = center_dac * dac_step_mv
        left_ui = right_ui = center_phase * phs_step_ui
        eh_ew = 0.0
        return {
            'lane': lane_id,
            'up(mV)': up_mv,
            'down(mV)': -down_mv,
            'left(uI)': -left_ui,
            'right(uI)': right_ui,
            'EH*EW': eh_ew
        }
    
    # Find eye boundaries
    dac_indices, phase_indices = np.where(high_quality)
    dac_min, dac_max = dac_indices.min(), dac_indices.max()
    phase_min, phase_max = phase_indices.min(), phase_indices.max()
    
    # Convert to mV and UI
    up_mv = (dac_max * dac_step_mv)
    down_mv = -(dac_min * dac_step_mv)
    left_ui = -(phase_min * phs_step_ui)
    right_ui = (phase_max * phs_step_ui)
    eh_ew = (right_ui - left_ui) * (up_mv - down_mv)
    
    print(f"Lane {lane_id} boundaries: dac_min={dac_min}, dac_max={dac_max}, phase_min={phase_min}, phase_max={phase_max}")
    return {
        'lane': lane_id,
        'up(mV)': up_mv,
        'down(mV)': down_mv,
        'left(uI)': left_ui,
        'right(uI)': right_ui,
        'EH*EW': eh_ew
    }

def create_lane_eye_diagram(eye_data, lane_id, output_dir):
    """Create centered eye diagram for a single lane, save to output directory"""
    combined_data = np.min(eye_data, axis=0)
    print(f"Lane {lane_id} combined data shape: {combined_data.shape}")
    
    high_quality = combined_data >= 0.9
    if np.any(high_quality):
        center_dac, center_phase = np.mean(np.where(high_quality), axis=1).astype(int)
    else:
        center_dac, center_phase = np.unravel_index(np.argmax(combined_data), combined_data.shape)
    print(f"Lane {lane_id} eye center: DAC={center_dac}, Phase={center_phase}")
    
    dac_window = 50
    phase_window = 25
    dac_min = max(0, center_dac - dac_window)
    dac_max = min(combined_data.shape[0], center_dac + dac_window + 1)
    phase_min = max(0, center_phase - phase_window)
    phase_max = min(combined_data.shape[1], center_phase + phase_window + 1)
    
    cropped_data = combined_data[dac_min:dac_max, phase_min:phase_max]
    print(f"Lane {lane_id} cropped data shape: {cropped_data.shape}")
    
    plt.figure(figsize=(10, 6))
    plt.imshow(cropped_data, 
               cmap='viridis', 
               interpolation='nearest',
               aspect='auto',
               extent=[phase_min, phase_max, dac_max, dac_min])
    plt.colorbar(label='Signal Quality (Min, 0 to 1)')
    plt.title(f'Centered Eye Diagram - Lane {lane_id}, All Patterns')
    plt.xlabel('Phase Step')
    plt.ylabel('DAC Step')
    plt.gca().invert_yaxis()
    
    output_path = os.path.join(output_dir, f'lane_{lane_id}_eye_diagram.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Saved centered eye diagram for Lane {lane_id} to {output_path}")
    return output_path

def save_eye_vals_to_csv(eye_data, lane_id, output_dir):
    """Save m_eye_vals data to CSV for a given lane"""
    num_ptn, num_dac, num_phs = eye_data.shape
    data = []
    for ptn in range(num_ptn):
        for dac in range(num_dac):
            row = [lane_id, ptn, dac] + eye_data[ptn, dac, :].tolist()
            data.append(row)
    columns = ['lane', 'pattern', 'dac'] + [f'phase_{i}' for i in range(num_phs)]
    df = pd.DataFrame(data, columns=columns)
    output_path = os.path.join(output_dir, f'lane_{lane_id}_eye_vals.csv')
    df.to_csv(output_path, index=False)
    print(f"Saved m_eye_vals for Lane {lane_id} to {output_path}")

def get_bdf_info():
    """Return simplified device info"""
    return [('SanDisk', 'DC SN861')]

def generate_html_report(margin_df, worst_cases, raw_data_params, output_path, config_info):
    """Generate HTML report with simplified Data Information, worst-case lanes, and raw log params"""
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    output_dir = os.path.dirname(output_path)
    image_extensions = ('.png', '.jpg', '.jpeg', '.gif')
    image_files = [f for f in os.listdir(output_dir) if f.startswith('lane_') and f.lower().endswith(image_extensions)]
    image_files.sort()

    html_header = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>SanDisk Margin Analysis Report</title>
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
<h1>SanDisk Margin Analysis Report</h1>
"""

    html_data_info = """
<table>
<tr><th colspan="2" class="title-header">Data Information</th></tr>
<tr><th>Vendor</th><th>Device</th></tr>
"""
    for vendor, device in config_info:
        html_data_info += f"<tr><td>{vendor}</td><td>{device}</td></tr>"

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
                html_images += f'<img src="data:image/png;base64,{img_data}" alt="{image}" /><br>'
            except Exception as e:
                print(f"Warning: Could not embed image {image}: {e}")
                html_images += f'<p>Error embedding {image}: {e}</p><br>'
    else:
        html_images += "<p>No images found in the directory.</p>"
    html_images += "</div>"

    html_raw = """
<table>
<tr><th colspan="6" class="title-header">Raw Data</th></tr>
<tr><th>Lane</th><th>num_ptn</th><th>num_dac</th><th>num_phs</th><th>phs_step_ui</th><th>dac_step_mv</th></tr>
"""
    for _, row in raw_data_params.iterrows():
        lane = int(row['lane'])
        html_raw += f"<tr><td>{lane}</td><td>{row['num_ptn']}</td><td>{row['num_dac']}</td><td>{row['num_phs']}</td><td>{row['phs_step_ui']:.3f}</td><td>{row['dac_step_mv']:.3f}</td></tr>"

    html_footer = """
</table>
</div>
</body>
</html>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_header + html_data_info + html_worst + html_images + html_raw + html_footer)

def main(input_dir):
    file_paths = [os.path.join(input_dir, f'sandisk{lane}.txt') for lane in range(4)]
    output_dir = input_dir
    
    all_metrics = []
    raw_data_params = []
    config_info = get_bdf_info()  # Single device info for all lanes
    
    for lane_id, file_path in enumerate(file_paths):
        if not os.path.exists(file_path):
            print(f"File {file_path} not found, skipping...")
            continue
        print(f"Processing {file_path}...")
        eye_data, num_ptn, num_dac, num_phs, phs_step_ui, dac_step_mv = parse_eye_vals(file_path)
        metrics = calculate_eye_metrics(eye_data, phs_step_ui, dac_step_mv, lane_id)
        all_metrics.append(metrics)
        raw_data_params.append({
            'lane': lane_id,
            'num_ptn': num_ptn,
            'num_dac': num_dac,
            'num_phs': num_phs,
            'phs_step_ui': phs_step_ui,
            'dac_step_mv': dac_step_mv
        })
        create_lane_eye_diagram(eye_data, lane_id, output_dir)
        save_eye_vals_to_csv(eye_data, lane_id, output_dir)
    
    if not all_metrics:
        print("No valid data processed. Exiting...")
        return
    
    margin_df = pd.DataFrame(all_metrics)
    raw_data_params = pd.DataFrame(raw_data_params)
    
    # Find worst-case lanes for each metric
    worst_cases = []
    if not margin_df.empty:
        # EH*EW: smallest is worst
        worst_eh_ew = margin_df.loc[margin_df['EH*EW'].idxmin()].copy()
        worst_eh_ew['worst_metric'] = 'EH*EW'
        worst_cases.append(worst_eh_ew)
        
        # Top (mV): smallest is worst
        worst_up_mv = margin_df.loc[margin_df['up(mV)'].idxmin()].copy()
        worst_up_mv['worst_metric'] = 'Top (mV)'
        worst_cases.append(worst_up_mv)
        
        # Bottom (mV): largest (least negative) is worst
        worst_down_mv = margin_df.loc[margin_df['down(mV)'].idxmax()].copy()
        worst_down_mv['worst_metric'] = 'Bottom (mV)'
        worst_cases.append(worst_down_mv)
        
        # Left (UI): largest (least negative) is worst
        worst_left_ui = margin_df.loc[margin_df['left(uI)'].idxmax()].copy()
        worst_left_ui['worst_metric'] = 'Left (UI)'
        worst_cases.append(worst_left_ui)
        
        # Right (UI): smallest is worst
        worst_right_ui = margin_df.loc[margin_df['right(uI)'].idxmin()].copy()
        worst_right_ui['worst_metric'] = 'Right (UI)'
        worst_cases.append(worst_right_ui)
    
    # Combine into DataFrame (keep all five, even if duplicates)
    worst_cases = pd.DataFrame(worst_cases)
    
    output_filename = f"SanDisk_Margin_Analysis_Report_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.html"
    output_path = os.path.join(output_dir, output_filename)
    generate_html_report(margin_df, worst_cases, raw_data_params, output_path, config_info)
    print(f"Report generated at: {output_path}")

if __name__ == "__main__":
    input_dir = r'C:\Users\dchen52\OneDrive - Lenovo\Documents\SanDisk'
    main(input_dir)