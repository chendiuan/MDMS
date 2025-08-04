import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import LogNorm
import pandas as pd
from datetime import datetime
import io
import base64
import os

def read_ber_bin(file_path):
    """
    讀取檔案並 reshape 成 (4, 52, 64)。
    確認檔案大小為 26624 bytes，等於 13312 個 16 位數。
    """
    with open(file_path, 'rb') as f:
        file_size = os.path.getsize(file_path)
        print(f"File size: {file_size} bytes")
        if file_size != 26624:
            print("Warning: File size does not match expected 26624 bytes!")
        header = f.read(256)
        hex_data = [hex(b)[2:].zfill(2) for b in header]
        print("Hexadecimal data (first 256 bytes):")
        for i in range(0, len(hex_data), 16):
            print(' '.join(hex_data[i:i+16]))

    # 完整讀取所有數值，不要跳過
    arr = np.fromfile(file_path, dtype=np.uint16).astype(np.float32)
    print("Total data size =", arr.size)  # 預期為 13312
    if arr.size != 13312:
        print("Warning: Data size does not match expected 13312 values!")
    
    # 直接 reshape 成 (4, 52, 64)
    data = arr.reshape(4, 52, 64)
    print("data.shape =", data.shape)
    return data


def generate_axes():
    """
    定義軸範圍：
      - Voltage 軸: 52 點，從 -60 到 +60
      - PI 軸: 63 點，從 -20 到 +60 (調整為 63 點)
    """
    voltage_axis = np.linspace(-60, 60, 52)
    pi_axis = np.linspace(-20, 60, 63)  # 調整為 63 點
    return voltage_axis, pi_axis

def plot_eye_no_transpose(lane_data, voltage_axis, pi_axis, lane_idx):
    """
    恢復為熱圖，使用 viridis 色盤。
    不做任何 transpose。
    lane_data.shape = (52, 63) → row=0..51, col=0..62
    預期 row=Voltage, col=PI。
    這裡用 origin='upper'，extent=[x_min, x_max, y_max, y_min]，
    讓 row=0 對應 y=+60 (圖上方)，row=51 對應 y=-60 (圖下方)。
    同時 x 軸從 -20 到 +60。
    返回 base64 編碼的圖片。
    """
    fig = plt.figure(figsize=(4,3))  # 縮小圖片尺寸
    plt.imshow(
        lane_data,
        norm=LogNorm(vmin=1, vmax=1023),
        extent=[pi_axis[0], pi_axis[-1],  # -20, +60
                voltage_axis[0], voltage_axis[-1]],  # -60, +60
        origin='upper',  # row=0 在圖的最上方
        aspect='auto',
        cmap='viridis'
    )
    cbar = plt.colorbar()
    cbar.set_label("Bit Error Count")
    cbar.set_ticks([1, 5, 10, 50, 100, 500, 1023])
    cbar.set_ticklabels([1, 5, 10, 50, 100, 500, 1023])

    plt.title(f"PCle BER Eye Window - Lane {lane_idx}")
    plt.xlabel("PI (UI/64)")
    plt.ylabel("Voltage (mV)")
    plt.grid(True)
    
    # 將圖片轉為 base64
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=300, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig)
    return img_base64

def get_device_info():
    """
    Return simplified device info.
    """
    return [('Micron', 'PEye NVMe1')]

def generate_html_report(raw_data_params, output_path, config_info, images):
    """
    Generate HTML report with device information, raw data parameters, and embedded eye diagram images.
    """
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    html_header = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Micron Eye Diagram Analysis Report</title>
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
        h1, h2, h3 {{
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
            max-width: 600px;  /* 限制圖片最大寬度 */
            height: auto;
            margin: 10px 0;
            border: 1px solid #dddddd;
            border-radius: 5px;
        }}
    </style>
</head>
<body>
<div class="container">
<h1>Micron Eye Diagram Analysis Report</h1>
<p><strong>Generated on:</strong> {current_date}</p>
"""

    html_data_info = """
<table>
<tr><th colspan="2" class="title-header">Device Information</th></tr>
<tr><th>Vendor</th><th>Device</th></tr>
"""
    for vendor, device in config_info:
        html_data_info += f"<tr><td>{vendor}</td><td>{device}</td></tr>"

    html_raw = """
</table>
<table>
<tr><th colspan="3" class="title-header">Raw Data Parameters</th></tr>
<tr><th>Lane</th><th>Number of Voltage Points</th><th>Number of PI Points</th></tr>
"""
    for _, row in raw_data_params.iterrows():
        lane = int(row['lane'])
        html_raw += f"<tr><td>{lane}</td><td>{row['num_voltage']}</td><td>{row['num_pi']}</td></tr>"

    html_images = """
</table>
<div class="image-section">
<h2>Eye Diagram Images</h2>
"""
    if images:
        for lane_idx, (no_transpose, _, _) in images.items():
            html_images += f'<h3>Lane {lane_idx}</h3>'
            html_images += f'<img src="data:image/png;base64,{no_transpose}" alt="Lane {lane_idx} No Transpose" /><br>'
    else:
        html_images += "<p>No images generated.</p>"
    html_images += "</div>"

    html_footer = """
</div>
</body>
</html>
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_header + html_data_info + html_raw + html_images + html_footer)
    print(f"Report generated at: {output_path}")

def main(file_path):
    data = read_ber_bin(file_path)  # (4, 52, 63)
    voltage_axis, pi_axis = generate_axes()
    output_dir = os.path.dirname(file_path)
    raw_data_params = []
    config_info = get_device_info()
    images = {}

    for lane_idx in range(4):
        lane_data = data[lane_idx]  # shape=(52,63)
        num_voltage, num_pi = lane_data.shape
        raw_data_params.append({
            'lane': lane_idx,
            'num_voltage': num_voltage,
            'num_pi': num_pi
        })

        # Generate base64-encoded images, only No Transpose
        no_transpose_img = plot_eye_no_transpose(lane_data, voltage_axis, pi_axis, lane_idx)
        images[lane_idx] = (no_transpose_img, None, None)

    raw_data_params = pd.DataFrame(raw_data_params)
    output_filename = f"Micron_Eye_Diagram_Analysis_Report_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.html"
    output_path = os.path.join(output_dir, output_filename)
    generate_html_report(raw_data_params, output_path, config_info, images)

if __name__ == "__main__":
    file_path = r"C:\Users\dchen52\OneDrive - Lenovo\Documents\Micron\Micron_7450_Margin_Data\PEye_NVMe1.bin"
    main(file_path)