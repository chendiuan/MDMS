import base64
import os
import glob

# Criteria
criteria = {"Eye Height": 20,
            "Eye Width": 200}

# Step 1: Define the directory path and NVMe device
directory_path = r"C:\Users\dchen52\OneDrive - Lenovo\Documents\Kioxia\CD8P Margin"  # Replace with your directory path
nvme_device = "nvme0"  # Specify the NVMe device to process (e.g., "nvme0" or "nvme1")
output_html_path = os.path.join(directory_path, f"Margin_Analysis_Report_{nvme_device}.html")

# Step 2: Find all .txt files in the directory matching the pattern EOM-LaneX-nvmeY.txt
txt_files = glob.glob(os.path.join(directory_path, f"EOM-Lane*-{nvme_device}.txt"))

# Step 3: Process each .txt file and its corresponding .png file
data_entries = []
data_info = {}  # To store Data Information fields (assumed to be consistent across files)
for txt_file in txt_files:
    # Parse the log file
    log_data = {}
    with open(txt_file, "r") as file:
        for line in file:
            key, value = line.strip().split(",", 1)  # Split on the first comma
            log_data[key] = value

    # Extract Lane from the filename
    filename = os.path.basename(txt_file)
    lane = filename.split("-")[1]  # e.g., Lane0

    # Find the corresponding .png file
    image_file_path = os.path.join(directory_path, f"EOM-{lane}-{nvme_device}.png")
    if os.path.exists(image_file_path):
        with open(image_file_path, "rb") as image_file:
            eye_diagram_base64 = base64.b64encode(image_file.read()).decode('utf-8')
    else:
        eye_diagram_base64 = ""  # Handle missing image case
        print(f"Warning: Image file '{image_file_path}' not found.")

    # Calculate Eye Height * Eye Width
    eye_height_width = float(log_data["Eye_Height"]) * float(log_data["Eye_Width"])
    margin_top = float(log_data["Upper_Margin"])
    margin_bottom = float(log_data["Lower_Margin"])
    margin_left = float(log_data["Left_Margin"]) * 1000
    margin_right = float(log_data["Right_Margin"]) * 1000

    # Store Data Information fields (assumed to be the same for all lanes)
    if not data_info:
        data_info = {
            "Viewer_revision": log_data.get("Viewer_revision", "N/A"),
            "Port_Number": log_data.get("Port_Number", "N/A"),
            "Link_Speed": log_data.get("Link_Speed", "N/A"),
            "Phy_identifier": log_data.get("Phy_identifier", "N/A"),
            "Acutual_BER": log_data.get("Acutual_BER", "N/A")
        }

    # Store the data for this lane
    data_entries.append({
        "lane": lane.lower().replace("lane", "lane "),  # Format as "lane 0"
        "log_data": log_data,
        "eye_diagram": eye_diagram_base64,
        "eye_height_width": round(eye_height_width, 1),
        "margin_top": margin_top,
        "margin_bottom": margin_bottom,
        "margin_left": round(margin_left, 1),
        "margin_right": round(margin_right, 1),
        "metrics": {
            "eye_height_width": eye_height_width,
            "margin_top": margin_top,
            "margin_bottom": margin_bottom,
            "margin_left": margin_left,
            "margin_right": margin_right
        }
    })

# Step 4: Find the smallest value for each metric and the corresponding lane
if data_entries:
    min_metrics = {
        "eye_height_width": {"value": float('inf'), "lane": None, "entry": None},
        "margin_top": {"value": float('inf'), "lane": None, "entry": None},
        "margin_bottom": {"value": float('inf'), "lane": None, "entry": None},
        "margin_left": {"value": float('inf'), "lane": None, "entry": None},
        "margin_right": {"value": float('inf'), "lane": None, "entry": None}
    }

    for entry in data_entries:
        metrics = entry["metrics"]
        lane = entry["lane"]
        for metric_name, value in metrics.items():
            if value < min_metrics[metric_name]["value"]:
                min_metrics[metric_name]["value"] = value
                min_metrics[metric_name]["lane"] = lane
                min_metrics[metric_name]["entry"] = entry

    worst_case_entries = list(min_metrics.values())
else:
    worst_case_entries = []
    print("No data entries found for the specified NVMe device.")

# Step 5: Create the HTML content with styling
html_content = """
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
            height: 40px; /* Consistent row height to accommodate images */
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
                <th>Viewer Revision</th>
                <th>Port Number</th>
                <th>Link Speed</th>
                <th>Phy Identifier</th>
                <th>Actual BER</th>
            </tr>
            <tr>
                <td>{Viewer_revision}</td>
                <td>{Port_Number}</td>
                <td>{Link_Speed}</td>
                <td>{Phy_identifier}</td>
                <td>{Acutual_BER}</td>
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
            {worst_case_rows}
        </table>
"""
html_content += f"""
        <!-- Vendor Criteria -->
        <table>
            <tr>
                <th colspan="6" class="title-header">Vendor Criteria</th>
            </tr>
            <tr>
                <th>Eye Height (mV)</th>
                <th>Eye Width (UI)</th>
            </tr>
            <tr>
                <td>{criteria["Eye Height"]}</td>
                <td>{criteria["Eye Width"]}</td>
            </tr>
        </table>
"""
html_content +="""
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
                {complete_data_rows}
            </table>
        </div>
    </div>
</body>
</html>
"""

# Step 6: Generate rows for the "Worst Cases Summary" table
worst_case_row_template = """
            <tr>
                <td>{lane}</td>
                <td>{eye_height_width}</td>
                <td>{margin_top}</td>
                <td>{margin_bottom}</td>
                <td>{margin_left}</td>
                <td>{margin_right}</td>
            </tr>
"""

def format_value(value, is_min):
    if is_min:
        return f'<font>{value}</font>'
    return str(value)

worst_case_rows = ""
if not worst_case_entries:
    worst_case_rows = """
            <tr>
                <td colspan="6">No data available</td>
            </tr>
    """
else:
    processed_metrics = set()
    for metric_name, min_data in min_metrics.items():
        if metric_name in processed_metrics:
            continue
        entry = min_data["entry"]
        if not entry:
            continue

        processed_metrics.add(metric_name)

        eye_height_width = format_value(entry["eye_height_width"], metric_name == "eye_height_width")
        margin_top = format_value(entry["margin_top"], metric_name == "margin_top")
        margin_bottom = format_value(entry["margin_bottom"], metric_name == "margin_bottom")
        margin_left = format_value(entry["margin_left"], metric_name == "margin_left")
        margin_right = format_value(entry["margin_right"], metric_name == "margin_right")

        worst_case_rows += worst_case_row_template.format(
            lane=entry["lane"],
            eye_height_width=eye_height_width,
            margin_top=margin_top,
            margin_bottom=margin_bottom,
            margin_left=margin_left,
            margin_right=margin_right
        )

# Step 7: Generate rows for the "Raw Data" table
complete_data_row_template = """
                <tr>
                    <td>{lane}</td>
                    <td>{Eye_Width} UI</td>
                    <td>{Eye_Height} mV</td>
                    <td>{Left_Margin} UI</td>
                    <td>{Right_Margin} UI</td>
                    <td>{Upper_Margin} mV</td>
                    <td>{Lower_Margin} mV</td>
                    <td><img src="data:image/png;base64,{eye_diagram}" class="eye-diagram" alt="Eye Diagram {lane}"></td>
                </tr>
"""

complete_data_rows = ""
data_entries.sort(key=lambda x: int(x["lane"].split()[-1]))
for entry in data_entries:
    log_data = entry["log_data"]
    complete_data_rows += complete_data_row_template.format(
        lane=entry["lane"],
        Eye_Width=log_data["Eye_Width"],
        Eye_Height=log_data["Eye_Height"],
        Left_Margin=log_data["Left_Margin"],
        Right_Margin=log_data["Right_Margin"],
        Upper_Margin=log_data["Upper_Margin"],
        Lower_Margin=log_data["Lower_Margin"],
        eye_diagram=entry["eye_diagram"]
    )

# Step 8: Format the HTML with the generated rows
html_output = html_content.format(
    nvme_device=nvme_device,
    Viewer_revision=data_info.get("Viewer_revision", "N/A"),
    Port_Number=data_info.get("Port_Number", "N/A"),
    Link_Speed=data_info.get("Link_Speed", "N/A"),
    Phy_identifier=data_info.get("Phy_identifier", "N/A"),
    Acutual_BER=data_info.get("Acutual_BER", "N/A"),
    worst_case_rows=worst_case_rows,
    complete_data_rows=complete_data_rows
)

# Step 9: Write the HTML to the source directory
with open(output_html_path, "w") as html_file:
    html_file.write(html_output)

print(f"HTML report generated as '{output_html_path}'")