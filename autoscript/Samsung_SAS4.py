import re
import os
import base64
from datetime import datetime

# Criteria
criteria = {"Eye Height": ["84.1", "55.8", "37.2"],
            "Eye Width": ["278", "222", "167"]}


# Input file paths
log_file = r'C:\Users\dchen52\OneDrive - Lenovo\Documents\Samsung\PM9D3a\Result_Dev0c_20241213_09h48m41s\Texts\Result_Config_Dev0c_20241213_09h48m41s.txt'
images_dir = r'C:\Users\dchen52\OneDrive - Lenovo\Documents\Samsung\PM9D3a\Result_Dev0c_20241213_09h48m41s\Images'

# Get the directory of the log file for output
output_dir = os.path.dirname(os.path.abspath(log_file))

# Extract device and timestamp from log filename
log_filename = os.path.basename(log_file)
# Example: Result_Config_Dev0c_20241213_09h48m41s.txt
device = log_filename.split('_')[2]  # Dev0c
timestamp = log_filename.split('_')[3].replace('.txt', '')  # 20241213_09h48m41s

# Sample data structure to hold parsed data
data = []

# Read and parse the log file
with open(log_file, 'r') as file:
    content = file.read()
    # Split into sections based on DEVICE INFO
    sections = content.split('=================================================\n')[1:]  # Skip initial separator

    for section in sections:
        device_info = {}
        options = {}
        result_summary = {}

        # Extract DEVICE INFO
        device_lines = section.split('[OPTION]')[0].strip().split('\n')[1:]
        for line in device_lines:
            line = line.strip()
            if not line or '=' not in line:
                continue  # Skip empty or invalid lines silently
            key, value = line.split('=', 1)
            device_info[key.strip()] = value.strip()

        # Extract OPTION
        option_lines = section.split('[OPTION]')[1].split('[RESULT SUMMARY]')[0].strip().split('\n')[1:]
        for line in option_lines:
            line = line.strip()
            if not line or '=' not in line:
                continue  # Skip empty or invalid lines silently
            key, value = line.split('=', 1)
            options[key.strip()] = value.strip()

        # Extract RESULT SUMMARY
        result_lines = section.split('[RESULT SUMMARY]')[1].strip().split('\n')[1:]
        for line in result_lines:
            line = line.strip()
            if not line or '=' not in line:
                continue  # Skip empty or invalid lines silently
            key, value = line.split('=', 1)
            result_summary[key.strip()] = value.strip()

        data.append({
            'device_info': device_info,
            'options': options,
            'result_summary': result_summary
        })

# Function to load and encode image as base64
def load_image_as_base64(lane):
    # Construct the expected image filename
    image_filename = f"{device}_P0_L{lane}_Rep1_{timestamp}_09h48m41s.bmp"
    image_path = os.path.join(images_dir, image_filename)

    try:
        with open(image_path, 'rb') as img_file:
            img_data = img_file.read()
            img_base64 = base64.b64encode(img_data).decode('utf-8')
            return img_base64
    except FileNotFoundError:
        print(f"Image not found for lane {lane}: {image_path}")
        return None

# Generate HTML content
html_content = f"""
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
            font-size: 14px; /* Increased font size for better readability */
        }}
        .complete-data table {{
            table-layout: fixed; /* Ensures columns respect the specified widths */
            width: 100%;
        }}
        .complete-data th, .complete-data td {{
            padding: 10px; /* Increased padding for better spacing */
            text-align: center;
            height: 40px; /* Increased row height to accommodate images */
            vertical-align: middle; /* Center content vertically */
        }}
        .complete-data th {{
            background-color: #f0f0f0;
            color: #333333;
        }}
        /* Specific column widths for Raw Data table */
        .complete-data th:nth-child(1), .complete-data td:nth-child(1) {{ /* Lane */
            width: 5%;
        }}
        .complete-data th:nth-child(2), .complete-data td:nth-child(2) {{ /* Eye Width */
            width: 8%;
        }}
        .complete-data th:nth-child(3), .complete-data td:nth-child(3) {{ /* Eye Height */
            width: 8%;
        }}
        .complete-data th:nth-child(4), .complete-data td:nth-child(4) {{ /* Margin Left */
            width: 8%;
        }}
        .complete-data th:nth-child(5), .complete-data td:nth-child(5) {{ /* Margin Right */
            width: 9%;
        }}
        .complete-data th:nth-child(6), .complete-data td:nth-child(6) {{ /* Margin Top */
            width: 8%;
        }}
        .complete-data th:nth-child(7), .complete-data td:nth-child(7) {{ /* Margin Bottom */
            width: 10%;
        }}
        .complete-data th:nth-child(8), .complete-data td:nth-child(8) {{ /* Eye Diagram */
            width: 44%;
        }}
        .title-header {{
            font-size: 20px;
            font-weight: bold;
        }}
        .eye-diagram {{
            max-width: 200%; /* Ensure the image scales within the cell */
            max-height: 200px; /* Limit the image height to fit the row */
            display: block;
            margin: 0 auto; /* Center the image */
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Margin Analysis Report</h1>

        <!-- Device Information -->
        <table>
            <tr>
                <th colspan="5" class="title-header">Device Information</th>
            </tr>
            <tr>
                <th>Disk Number</th>
                <th>Criteria Mask</th>
                <th>Measurement Level</th>
                <th>FW Version</th>
                <th>Result</th>
            </tr>
            <tr>
                <td>{data[0]['device_info'].get('disk_number', 'N/A')}</td>
                <td>{data[0]['options'].get('criteriaMask', 'N/A')}</td>
                <td>{data[0]['options'].get('measurement_level', 'N/A')}</td>
                <td>{data[0]['device_info'].get('FW_version', 'N/A')}</td>
                <td>{data[0]['result_summary'].get('Pass/Fail', 'N/A')}</td>
            </tr>
        </table>

        <!-- Worst Cases Summary -->
        <table>
            <tr>
                <th colspan="6" class="title-header">Worst Cases Summary</th>
            </tr>
            <tr>
                <th>Lane</th>
                <th>Eye Height * Eye Width</th>
                <th>Margin Top (mV)</th>
                <th>Margin Bottom (mV)</th>
                <th>Margin Left (UI)</th>
                <th>Margin Right (UI)</th>
            </tr>
"""

# Calculate worst cases (find the smallest value for each metric)
worst_cases = []
for i, entry in enumerate(data):
    lane = entry['device_info']['target lane']
    eye_height = float(entry['result_summary']['Eye_height'].split()[0])
    eye_width = float(entry['result_summary']['Eye_width'].split()[0])
    margin_top = float(entry['result_summary']['Margin_top'].split()[0])
    margin_bottom = float(entry['result_summary']['Margin_bottom'].split()[0])
    margin_left = float(entry['result_summary']['Margin_left'].split()[0]) * 1000
    margin_right = float(entry['result_summary']['Margin_right'].split()[0]) * 1000
    worst_cases.append({
        'lane': lane,
        'eye_product': eye_height * eye_width,
        'margin_top': margin_top,
        'margin_bottom': margin_bottom,
        'margin_left': margin_left,
        'margin_right': margin_right,
        'metrics': {
            'eye_product': eye_height * eye_width,
            'margin_top': margin_top,
            'margin_bottom': margin_bottom,
            'margin_left': margin_left,
            'margin_right': margin_right
        }
    })

# Find the smallest value for each metric and the corresponding lane
if worst_cases:
    min_metrics = {
        "eye_product": {"value": float('inf'), "lane": None, "entry": None},
        "margin_top": {"value": float('inf'), "lane": None, "entry": None},
        "margin_bottom": {"value": float('inf'), "lane": None, "entry": None},
        "margin_left": {"value": float('inf'), "lane": None, "entry": None},
        "margin_right": {"value": float('inf'), "lane": None, "entry": None}
    }

    for entry in worst_cases:
        metrics = entry["metrics"]
        lane = entry["lane"]

        for metric_name, value in metrics.items():
            if value < min_metrics[metric_name]["value"]:
                min_metrics[metric_name]["value"] = value
                min_metrics[metric_name]["lane"] = lane
                min_metrics[metric_name]["entry"] = entry

    # Create a list of the worst-case entries (one for each metric)
    worst_case_entries = list(min_metrics.values())
else:
    worst_case_entries = []

# Helper function to format the value (highlight if it's the smallest for this row)
def format_value(value, is_min):
    if is_min:
        return f'<font>{value:.1f}</font>'
    return f"{value:.1f}"

# Generate rows for the "Worst Cases Summary" table
if not worst_case_entries:
    html_content += """
            <tr>
                <td colspan="6">No data available</td>
            </tr>
    """
else:
    processed_metrics = set()  # To avoid duplicates if the same lane has the smallest value for multiple metrics
    for metric_name, min_data in min_metrics.items():
        if metric_name in processed_metrics:
            continue
        entry = min_data["entry"]
        if not entry:
            continue

        processed_metrics.add(metric_name)

        # Determine which value to highlight (the smallest one for this row)
        eye_product = format_value(entry["eye_product"], metric_name == "eye_product")
        margin_top = format_value(entry["margin_top"], metric_name == "margin_top")
        margin_bottom = format_value(entry["margin_bottom"], metric_name == "margin_bottom")
        margin_left = format_value(entry["margin_left"], metric_name == "margin_left")
        margin_right = format_value(entry["margin_right"], metric_name == "margin_right")

        html_content += f"""
            <tr>
                <td>lane {entry['lane']}</td>
                <td>{eye_product}</td>
                <td>{margin_top}</td>
                <td>{margin_bottom}</td>
                <td>{margin_left}</td>
                <td>{margin_right}</td>
            </tr>
        """

html_content += f"""
        </table>

        <table>
        <!-- Vendor Criteria -->
        <table>
            <tr>
                <th colspan="6" class="title-header">Vendor Criteria</th>
            </tr>
            <tr>
                <th>BER</th>
                <th>Eye Height (mV)</th>
                <th>Eye Width (UI)</th>
            </tr>
            <tr>
                <td>1E-4</td>
                <td>{criteria["Eye Height"][0]}</td>
                <td>{criteria["Eye Width"][0]}</td>
            </tr>
            <tr>
                <td>1E-6</td>
                <td>{criteria["Eye Height"][1]}</td>
                <td>{criteria["Eye Width"][1]}</td>
            </tr>
            <tr>
                <td>1E-8</td>
                <td>{criteria["Eye Height"][2]}</td>
                <td>{criteria["Eye Width"][2]}</td>
            </tr>
        </table>

        <!-- Raw Data -->
        <div class="complete-data">
            <h2>Raw Data</h2>
            <table>
                <tr>
                    <th>Lane</th>
                    <th>Eye Width</th>
                    <th>Eye Height</th>
                    <th>Margin Left</th>
                    <th>Margin Right</th>
                    <th>Margin Top</th>
                    <th>Margin Bottom</th>
                    <th>Eye Diagram</th>
                </tr>
"""

# Populate Raw Data table with embedded images
for entry in data:
    lane = entry['device_info']['target lane']
    eye_width = entry['result_summary']['Eye_width']
    eye_height = entry['result_summary']['Eye_height']
    margin_left = entry['result_summary']['Margin_left']
    margin_right = entry['result_summary']['Margin_right']
    margin_top = entry['result_summary']['Margin_top']
    margin_bottom = entry['result_summary']['Margin_bottom']

    # Load and encode the corresponding image
    img_str = load_image_as_base64(lane)

    html_content += f"""
                <tr>
                    <td>{lane}</td>
                    <td>{eye_width}</td>
                    <td>{eye_height}</td>
                    <td>{margin_left}</td>
                    <td>{margin_right}</td>
                    <td>{margin_top}</td>
                    <td>{margin_bottom}</td>
                    <td>{'<img src="data:image/bmp;base64,' + img_str + '" class="eye-diagram" alt="Eye Diagram Lane ' + lane + '">' if img_str else 'N/A'}</td>
                </tr>
    """

html_content += """
            </table>
        </div>
    </div>
</body>
</html>
"""

# Save the HTML file in the same directory as the log file
output_file = os.path.join(output_dir, 'Margin_Analysis_Report.html')
with open(output_file, 'w') as f:
    f.write(html_content)

print(f"HTML report generated as '{output_file}'")