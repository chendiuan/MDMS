import os
import re
import base64
import numpy as np
import pandas as pd
from io import BytesIO
from datetime import datetime
import matplotlib.pyplot as plt

def parse_log_file(file_path):
    data = {"Initial FOM": [], "Last FOM": [], "RX Errors": [], "TX Errors": [], "Effective ber": []}
    current_loop = None

    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line.startswith("==== Loop"):
                current_loop = line.split("|")[1].strip()
                continue
            elif line.startswith("Depth, pcie index, node"):
                parts = line.split(":")[1].strip().split(", ")
                data["Depth"] = parts[0]
                data["pcie_index"] = parts[1]
                data["node"] = parts[2]
            elif line.startswith("Link Speed Active"):
                data["Link Speed Active"] = line.split(":")[1].strip()
            elif line.startswith("Link Width Active"):
                data["Link Width Active"] = line.split(":")[1].strip()
            elif line.startswith("Initial FOM"):
                fom_values = re.findall(r'\d+', line)
                # Ensure 16 values, pad with nan if less
                fom_values = fom_values[:16] + [None] * (16 - len(fom_values)) if len(fom_values) < 16 else fom_values[:16]
                data["Initial FOM"].append([float(x) if x is not None else float('nan') for x in fom_values])
            elif line.startswith("Last FOM"):
                fom_values = re.findall(r'\d+', line)
                # Ensure 16 values, pad with nan if less
                fom_values = fom_values[:16] + [None] * (16 - len(fom_values)) if len(fom_values) < 16 else fom_values[:16]
                data["Last FOM"].append([float(x) if x is not None else float('nan') for x in fom_values])
            elif line.startswith("RX Errors"):
                data["RX Errors"].append(float(re.search(r'\d+', line).group()))
            elif line.startswith("TX Errors"):
                data["TX Errors"].append(float(re.search(r'\d+', line).group()))
            elif line.startswith("Effective ber"):
                ber_value = float(re.search(r'(\d+\.?\d*)E-(\d+)', line).group().replace('E-', 'e-'))
                data["Effective ber"].append(ber_value)

    return data

def plot_pcie_log_box_and_time(file_path):
    """
    讀取格式為 txt 檔案，包含多個 Loop 的 PCIe 資料。

    產生的 HTML 報告包含：
      1. 三個獨立表格：Data Information、Worst Cases Summary、Vendor Criteria
      2. Worst Cases Summary 顯示所有 16 個 Lane 僅 Initial FOM 與 Last FOM，數值為整數
      3. Box Plot 分為兩張圖：Initial FOM 與 Last FOM，使用 DataFrame 簡化呈現
      4. Time-Domain Metrics 圖表（繪製 RX Errors, TX Errors, Effective ber, FOM Mean）
      - X 軸改為 Minutes (相對第一筆時間的分鐘數)
    報告風格參考 Margin Analysis Report x16.html。
    """

    # ---------- 1) 解析 txt 檔案 ----------
    data = parse_log_file(file_path)

    # 計算最差值
    worst_initial_fom = [min(x) for x in zip(*data["Initial FOM"])]
    worst_last_fom = [min(x) for x in zip(*data["Last FOM"])]
    worst_rx_errors = max(data["RX Errors"])
    worst_tx_errors = max(data["TX Errors"])
    worst_effective_ber = max(data["Effective ber"])

    # 補充 CPU_Utilization
    html_worst = {"CPU_Utilization": 50.2}

    # ---------- 2) 建立三個獨立表格的 HTML ----------
    data_info_html = """
        <table>
            <tr>
                <th colspan="5">Data Information</th>
            </tr>
            <tr>
                <th>Depth</th>
                <th>pcie index</th>
                <th>node</th>
                <th>Link Speed Active</th>
                <th>Link Width Active</th>
            </tr>
            <tr>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
                <td>{}</td>
            </tr>
        </table>
    """.format(data["Depth"], data["pcie_index"], data["node"], data["Link Speed Active"], data["Link Width Active"])

    worst_cases_html = """
        <table>
            <tr>
                <th colspan="17">Worst Cases Summary</th>
            </tr>
            <tr>
                <th>Metric</th>
                <th>Lane 0</th>
                <th>Lane 1</th>
                <th>Lane 2</th>
                <th>Lane 3</th>
                <th>Lane 4</th>
                <th>Lane 5</th>
                <th>Lane 6</th>
                <th>Lane 7</th>
                <th>Lane 8</th>
                <th>Lane 9</th>
                <th>Lane 10</th>
                <th>Lane 11</th>
                <th>Lane 12</th>
                <th>Lane 13</th>
                <th>Lane 14</th>
                <th>Lane 15</th>
            </tr>
    """

    # 添加 Initial FOM 值
    worst_cases_html += "<tr><td>Initial</td>"
    for value in worst_initial_fom:
        worst_cases_html += f"<td>{value:.0f}</td>"
    worst_cases_html += "</tr>"

    # 添加 Last FOM 值
    worst_cases_html += "<tr><td>Last</td>"
    for value in worst_last_fom:
        worst_cases_html += f"<td>{value:.0f}</td>"
    worst_cases_html += "</tr>"

    worst_cases_html += "</table>"

    # 使用變數生成 Vendor Criteria 表格
    vendor_criteria_html = """
        <table>
            <tr>
                <th colspan="17">Vendor Criteria</th>
            </tr>
            <tr>
                <th>Criteria</th>
                <th colspan="4">Gen 3.0</th>
                <th colspan="4">Gen 4.0</th>
                <th colspan="4">Gen 5.0</th>
                <th colspan="4">Gen 6.0</th>
            </tr>
            <tr>
                <th>Pass</th>
                <td colspan="4">{}</td>
                <td colspan="4">{}</td>
                <td colspan="4">{}</td>
                <td colspan="4">{}</td>
            </tr>
            <tr>
                <th>Pending on BER Criteria</th>
                <td colspan="4">{}</td>
                <td colspan="4">{}</td>
                <td colspan="4">{}</td>
                <td colspan="4">{}</td>
            </tr>
            <tr>
                <th>Fail</th>
                <td colspan="4">{}</td>
                <td colspan="4">{}</td>
                <td colspan="4">{}</td>
                <td colspan="4">{}</td>
            </tr>
        </table>
    """.format(G3_CRITERIA_PASS, G4_CRITERIA_PASS, G5_CRITERIA_PASS, G6_CRITERIA_PASS,
               G3_CRITERIA_PENDING, G4_CRITERIA_PENDING, G5_CRITERIA_PENDING, G6_CRITERIA_PENDING,
               G3_CRITERIA_FAIL, G4_CRITERIA_FAIL, G5_CRITERIA_FAIL, G6_CRITERIA_FAIL)

    # ---------- 3) 產生 Box Plot (分為 Initial FOM 與 Last FOM) ----------
    # Convert to DataFrame for Initial FOM
    df_initial = pd.DataFrame(data["Initial FOM"], columns=[f"Lane{i}" for i in range(16)])
    fom_cols_initial = [f"Lane{i}" for i in range(16)]
    data_for_box_initial = [df_initial[col].dropna() for col in fom_cols_initial]
    fig_initial, ax_initial = plt.subplots(figsize=(16, 8))
    box_initial = ax_initial.boxplot(data_for_box_initial, notch=False, patch_artist=True)
    colors = plt.cm.Pastel1(np.linspace(0, 1, len(fom_cols_initial)))
    for patch, color in zip(box_initial['boxes'], colors):
        patch.set_facecolor(color)
    ax_initial.set_xlabel("")
    ax_initial.set_ylabel("")
    ax_initial.set_xticks(range(1, len(fom_cols_initial) + 1))
    ax_initial.set_xticklabels([f"Lane{i}" for i in range(len(fom_cols_initial))], rotation=45)
    ax_initial.grid(True)
    buf_initial = BytesIO()
    fig_initial.savefig(buf_initial, format='png', bbox_inches='tight')
    buf_initial.seek(0)
    boxplot_initial_base64 = base64.b64encode(buf_initial.read()).decode()
    plt.close(fig_initial)

    # Convert to DataFrame for Last FOM
    df_last = pd.DataFrame(data["Last FOM"], columns=[f"Lane{i}" for i in range(16)])
    fom_cols_last = [f"Lane{i}" for i in range(16)]
    data_for_box_last = [df_last[col].dropna() for col in fom_cols_last]
    fig_last, ax_last = plt.subplots(figsize=(16, 8))
    box_last = ax_last.boxplot(data_for_box_last, notch=False, patch_artist=True)
    colors = plt.cm.Pastel1(np.linspace(0, 1, len(fom_cols_last)))
    for patch, color in zip(box_last['boxes'], colors):
        patch.set_facecolor(color)
    ax_last.set_xlabel("")
    ax_last.set_ylabel("")
    ax_last.set_xticks(range(1, len(fom_cols_last) + 1))
    ax_last.set_xticklabels([f"Lane{i}" for i in range(len(fom_cols_last))], rotation=45)
    ax_last.grid(True)
    buf_last = BytesIO()
    fig_last.savefig(buf_last, format='png', bbox_inches='tight')
    buf_last.seek(0)
    boxplot_last_base64 = base64.b64encode(buf_last.read()).decode()
    plt.close(fig_last)

    # ---------- 4) 產生 Time-Domain Metrics 圖表 ----------
    # 計算 Minutes (從每個 Loop 的時間戳)
    timestamps = [pd.to_datetime(re.search(r'\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2}', line).group(), format='%Y-%m-%d_%H-%M-%S') 
                  for line in open(file_path, 'r', encoding='utf-8') 
                  if line.startswith("==== Loop")]
    minutes = [(t - timestamps[0]).total_seconds() / 60 for t in timestamps]

    # 計算 FOM 平均值 (使用每個 Loop 的最小值)
    fom_mean = [sum(min(col) for col in zip(*data["Initial FOM"][i:i+1])) / 16 for i in range(len(data["Initial FOM"]))]

    # 選擇要畫的指標
    time_metrics = ["RX Errors", "TX Errors", "Effective ber", "FOM Mean"]
    fig_time, axes = plt.subplots(nrows=len(time_metrics), ncols=1, figsize=(16, 15), sharex=True)

    # 逐一繪製各指標
    for i, metric in enumerate(time_metrics):
        if metric == "FOM Mean":
            values = fom_mean
        else:
            values = [data[metric][j] for j in range(len(data[metric]))]
        axes[i].plot(minutes, values, label=metric, linewidth=0.8)
        axes[i].set_ylabel(metric)
        axes[i].grid(True)
        axes[i].legend(loc="upper right")

    axes[-1].set_xlabel("Time (minutes)")

    # 調整布局
    fig_time.tight_layout(rect=[0, 0, 1, 0.97])
    buf_time = BytesIO()
    fig_time.savefig(buf_time, format='png', bbox_inches='tight')
    buf_time.seek(0)
    timedomain_base64 = base64.b64encode(buf_time.read()).decode()
    plt.close(fig_time)

    # ---------- 5) 組裝 HTML 報告 ----------
    html_style = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PCIe Data Visualization</title>
        <style>
            body {
                background-color: #f0f8ff;
                color: #333333;
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 0;
            }
            .container {
                max-width: 1200px;
                margin: 40px auto;
                background-color: #ffffff;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
            }
            h1, h2 {
                text-align: center;
                color: #333333;
            }
            h1 {
                margin-bottom: 20px;
            }
            h2 {
                margin-top: 0;
                margin-bottom: 20px;
            }
            .chart-container {
                display: block;
                margin: 20px 0;
            }
            .chart {
                margin-bottom: 20px;
                border: 1px solid #dddddd;
                border-radius: 8px;
                padding: 10px;
                background-color: #fafafa;
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.05);
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }
            table, th, td {
                border: 1px solid #dddddd;
            }
            th, td {
                padding: 10px;
                text-align: center;
                width: calc(100% / 17); /* Uniform width for 17 columns */
                font-size: 16px; /* Adjusted font size for all table cells */
            }
            th {
                background-color: #f0f0f0;
                font-size: 13px; /* Specifically adjusted font size for header (Lane0~15) */
            }
            img {
                max-width: 100%;
                height: auto;
                display: block;
                margin: 0 auto;
            }
        </style>
    </head>
    """

    html_body = f"""
    <body>
        <div class="container">
            <h1>PCIe Data Visualization</h1>
            {data_info_html}
            {worst_cases_html}
            {vendor_criteria_html}
            <div class="chart-container">
                <div class="chart">
                    <h2>Box Plot of Initial FOM</h2>
                    <img src="data:image/png;base64,{boxplot_initial_base64}" alt="Box Plot of Initial FOM"/>
                </div>
                <div class="chart">
                    <h2>Box Plot of Last FOM</h2>
                    <img src="data:image/png;base64,{boxplot_last_base64}" alt="Box Plot of Last FOM"/>
                </div>
                <div class="chart">
                    <h2>Time-Domain Metrics</h2>
                    <img src="data:image/png;base64,{timedomain_base64}" alt="Time-Domain Metrics"/>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

    html_content = html_style + html_body

    # 輸出 HTML 檔案
    current_date = datetime.now().strftime('%Y_%m_%d')
    output_file = os.path.join(
        os.path.dirname(file_path),
        os.path.basename(file_path).rsplit(".", 1)[0] + f"_{current_date}.html"
    )
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML report saved to {output_file}")

# ==============
G3_CRITERIA_PASS = "Last >= 3860"
G4_CRITERIA_PASS = "Last >= 3454"
G5_CRITERIA_PASS = "Last >= 1400"
G6_CRITERIA_PASS = "FBER < 1e-9"
G3_CRITERIA_PENDING = "2509 < Last < 3859"
G4_CRITERIA_PENDING = "2387 < Last < 3453"
G5_CRITERIA_PENDING = "1001 < Last < 1399"
G6_CRITERIA_PENDING = "N/A"
G3_CRITERIA_FAIL = "Last <= 2508"
G4_CRITERIA_FAIL = "Last <= 2386"
G5_CRITERIA_FAIL = "Last <= 1000"
G6_CRITERIA_FAIL = "FBER > 1e-9"

input = r"C:\Users\dchen52\OneDrive - Lenovo\Documents\NVIDIA\mlxlink_logs\mlxlink_full_log.txt"
plot_pcie_log_box_and_time(input)
# ==============