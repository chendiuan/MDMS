import re
import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt
import os
import base64
from io import BytesIO

# Input file path (modify this path as needed)
log_file_path = r"C:\Users\dchen52\OneDrive - Lenovo\Documents\NVIDIA\test_11_pex_data_eye_test\pex_data_eye_test_092924_215308.log"

def parse_log_file(log_content):
    devices = []
    data_info = []
    raw_data = defaultdict(lambda: defaultdict(list))

    # Patterns
    pcie_info_pattern = re.compile(r"GPU\s+(\d+)\s+\[3\]\s+\[(.*?)\]\s+:\s+PEX Physical Lane\(0-15\) Y_STATUS\s*=\s*((?:\d+\s*,\s*)*\d+)")
    pex_speed_pattern = re.compile(r"PEX Link Speed\s+:\s+([\d.]+ Gbit/s)")
    pex_width_pattern = re.compile(r"PEX Width, ASLM\s*:\s*(\d+\s+lanes)")

    # Extract global PEX Speed and PEX Width
    pex_speed_match = pex_speed_pattern.search(log_content)
    pex_width_match = pex_width_pattern.search(log_content)
    pex_speed = pex_speed_match.group(1) if pex_speed_match else "Unknown"
    pex_width = f"{pex_width_match.group(1)}" if pex_width_match else "Unknown"

    # Parse GPU lanes
    for match in pcie_info_pattern.finditer(log_content):
        gpu_pos = int(match.group(1))  # GPU position (0-7)
        bus_id = match.group(2)
        y_status_values = [int(v.strip()) for v in match.group(3).split(",") if v.strip().isdigit()]

        if bus_id not in devices:
            devices.append(bus_id)
            data_info.append(
                {
                    "GPU Position": gpu_pos,
                    "Bus ID": bus_id,
                    "Product": "NVIDIA H200 NVL",
                    "PEX Width": pex_width,
                    "PEX Link Speed": pex_speed,
                }
            )

        # Ensure exactly 16 lanes, pad with None if less
        for lane in range(16):
            lane_key = f"Lane {lane}"
            value = y_status_values[lane] if lane < len(y_status_values) else None
            raw_data[bus_id][lane_key].append(value)

    return devices, data_info, raw_data

def get_worst_case_summary(raw_data, data_info):
    worst_case = []
    for bus_id in raw_data:
        gpu_pos = next(d["GPU Position"] for d in data_info if d["Bus ID"] == bus_id)
        min_val = None
        worst_lane = None
        for lane in raw_data[bus_id]:
            values = [v for v in raw_data[bus_id][lane] if v is not None]
            if values:
                lane_min = min(values)
                if min_val is None or lane_min < min_val:
                    min_val = lane_min
                    worst_lane = lane
        if min_val is not None:
            worst_case.append(
                {
                    "GPU Position": gpu_pos,
                    "Bus ID": bus_id,
                    "Worst Lane": worst_lane,
                    "Worst Y_STATUS": min_val,
                }
            )
    return worst_case

def generate_scatter_plot(raw_data, devices, data_info):
    plot_data = []
    for bus_id in devices:
        for lane in range(16):
            lane_key = f"Lane {lane}"
            for idx, value in enumerate(raw_data[bus_id][lane_key]):
                if value is not None:
                    plot_data.append(
                        {
                            "Bus ID": bus_id,
                            "Lane": lane_key,
                            "Y_STATUS": value,
                            "Run": idx + 1,
                        }
                    )

    if not plot_data:
        print("Warning: No data available for scatter plot.")
        return "<p>No data available for scatter plot.</p>"

    df = pd.DataFrame(plot_data)
    
    # Create scatter plot using Matplotlib with increased figure size
    plt.figure(figsize=(12, 6.5))
    
    # Generate unique colors for each Bus ID
    colors = plt.cm.get_cmap('tab10', len(devices))
    for idx, bus_id in enumerate(devices):
        gpu_pos = next(d["GPU Position"] for d in data_info if d["Bus ID"] == bus_id)
        bus_data = df[df['Bus ID'] == bus_id]
        plt.scatter(
            bus_data['Lane'],
            bus_data['Y_STATUS'],
            label=f"GPU {gpu_pos}",
            color=colors(idx),
            alpha=0.6,
            s=50
        )

    plt.xlabel('Lane Number')
    plt.ylabel('FOM')
    plt.legend(title='GPU Position', bbox_to_anchor=(1.05, 1), loc='upper left', borderaxespad=0., frameon=True)
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Save the plot to a bytes buffer and encode as base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', bbox_inches='tight', dpi=300)
    plt.close()
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return f'<img src="data:image/png;base64,{image_base64}" alt="Scatter Plot" />'

def generate_html_report(data_info, worst_case, raw_data, plot_html):
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PCIe Data Visualization Report</title>
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
                display: block;
                margin: 20px 0;
            }}
            .chart {{
                margin-bottom: 20px;
                border: 1px solid #dddddd;
                border-radius: 8px;
                padding: 10px;
                background-color: #fafafa;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.05);
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }}
            table, th, td {{
                border: 1px solid #dddddd;
            }}
            th, td {{
                padding: 10px;
                text-align: center;
                width: calc(100% / 17);
                font-size: 16px;
            }}
            th {{
                background-color: #f0f0f0;
                font-size: 13px;
            }}
            img {{
                max-width: 100%;
                height: auto;
                display: block;
                margin: 0 auto;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>PCIe Data Visualization</h1>
            <table>
                <tr>
                    <th colspan="5">Data Information</th>
                </tr>
                <tr>
                    <th>Bus ID</th>
                    <th>GPU Position</th>
                    <th>Product</th>
                    <th>PEX Width</th>
                    <th>PEX Link Speed</th>
                </tr>
    """
    for info in data_info:
        html_content += f"""
                <tr>
                    <td>{info['GPU Position']}</td>
                    <td>{info['Bus ID']}</td>
                    <td>{info['Product']}</td>
                    <td>{info['PEX Width']}</td>
                    <td>{info['PEX Link Speed']}</td>
                </tr>
        """
    html_content += """
            </table>
            <table>
                <tr>
                    <th colspan="4">Worst Case Summary</th>
                </tr>
                <tr>
                    <th>GPU Position</th>
                    <th>Bus ID</th>
                    <th>Worst Lane</th>
                    <th>Worst Y_STATUS</th>
                </tr>
    """
    for wc in worst_case:
        html_content += f"""
                <tr>
                    <td>{wc['GPU Position']}</td>
                    <td>{wc['Bus ID']}</td>
                    <td>{wc['Worst Lane']}</td>
                    <td>{wc['Worst Y_STATUS']}</td>
                </tr>
        """
    html_content += """
            </table>

            <h2>Chart Summary</h2>
            <div class="chart-container">
                <div class="chart">
    """
    html_content += plot_html
    html_content += """
                </div>
            </div>
            <table>
                <tr>
                    <th colspan="17">Raw Data</th>
                </tr>
                <tr>
                    <th>Bus ID</th>
                    <th>Lane 0</th><th>Lane 1</th><th>Lane 2</th><th>Lane 3</th>
                    <th>Lane 4</th><th>Lane 5</th><th>Lane 6</th><th>Lane 7</th>
                    <th>Lane 8</th><th>Lane 9</th><th>Lane 10</th><th>Lane 11</th>
                    <th>Lane 12</th><th>Lane 13</th><th>Lane 14</th><th>Lane 15</th>
                </tr>
    """
    for bus_id in raw_data:
        row = f"""
                <tr>
                    <td>{bus_id}</td>
        """
        for lane in range(16):
            lane_data = raw_data[bus_id][f"Lane {lane}"]
            formatted_data = ', '.join(str(v) if v is not None else 'N/A' for v in lane_data)
            row += f"<td>{formatted_data}</td>"
        row += "</tr>"
        html_content += row
    html_content += """
            </table>
        </div>
    </body>
    </html>
    """
    return html_content

def main(log_file_content, log_file_path):
    # Use the directory of the input log file
    input_dir = os.path.dirname(log_file_path) or "."
    today = pd.Timestamp.now().strftime("%Y_%m_%d")
    output_html_filename = f"pcie_data_report_{today}.html"
    output_html_path = os.path.join(input_dir, output_html_filename)

    devices, data_info, raw_data = parse_log_file(log_file_content)
    worst_case = get_worst_case_summary(raw_data, data_info)
    plot_html = generate_scatter_plot(raw_data, devices, data_info)
    html_content = generate_html_report(data_info, worst_case, raw_data, plot_html)

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML report generated at {output_html_path}")

if __name__ == "__main__":
    try:
        with open(log_file_path, "r", encoding="utf-8") as f:
            log_content = f.read()
        main(log_content, log_file_path)
    except FileNotFoundError:
        print(f"Error: Log file '{log_file_path}' not found. Please provide the correct path.")