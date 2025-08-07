import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO
import os

def plot_pcie_log_box_and_time(file_path):
    """
    讀取格式為：
      TIME, FOM, CPU Utilization, RX_Error, TX_Error, CPU Power, Memory Power, BER, Card Tmp
    其中 FOM 欄位包含16個以空白區隔的數值（對應 Lane0~Lane15）。

    產生的 HTML 報告包含：
      1. 最差值表格（FOM: 取最小值；其他欄位: 取最大值）
      2. Box Plot (各 FOM_Lane 的數值)
      3. Time-Domain Metrics 圖表（繪製 CPU Utilization、RX_Error、TX_Error、CPU Power、Memory_Power、BER、Card_Tmp、FOM 平均值）
      - X 軸改為 Minutes (相對第一筆時間的分鐘數)
    報告風格參考 Margin Analysis Report x16.html，且將圖表整合於同一區塊中。
    """

    # ---------- 1) 讀取原始資料 ----------
    # 定義原始欄位名稱（共9項）
    col_names = ["TIME", "FOM", "CPU_Utilization", "RX_Error", "TX_Error",
                 "CPU_Power", "Memory_Power", "BER", "Card_Tmp"]

    # 檔案內各項以逗號分隔，且無標頭，因此使用 header=None
    df = pd.read_csv(file_path, header=None, names=col_names)

    # 處理 TIME 欄位（去除空白後轉為 datetime）
    # 若您的時間格式不同，請自行調整 format
    df["TIME"] = pd.to_datetime(df["TIME"].str.strip(), format='%Y-%m-%d %H:%M:%S', errors='coerce')

    # ---------- 2) 處理 FOM 欄位 (16 條 Lane) ----------
    # FOM 欄位包含16個數值，數值之間以空白區隔
    fom_split = df["FOM"].str.strip().str.split(r"\s+", expand=True)
    # 設定 FOM 欄位名稱為 Lane_0 ~ Lane_15
    fom_cols = [f"Lane_{i}" for i in range(fom_split.shape[1])]
    fom_split.columns = fom_cols

    # 轉為數值型態
    fom_split = fom_split.apply(pd.to_numeric, errors='coerce')

    # 將原本 FOM 欄位移除，並與新產生的 16 個 FOM 欄位合併
    df.drop("FOM", axis=1, inplace=True)
    df = pd.concat([df, fom_split], axis=1)

    # 為了方便後續處理，將欄位重新排序為：TIME, Lane_0~Lane_15, 其他項目
    other_cols = ["CPU_Utilization", "RX_Error", "TX_Error", "CPU_Power",
                  "Memory_Power", "BER", "Card_Tmp"]
    df = df[["TIME"] + fom_cols + other_cols]

    # 將其他欄位去除空白後轉為數值
    for col in other_cols:
        df[col] = pd.to_numeric(df[col].astype(str).str.strip(), errors='coerce')

    # ---------- 3) 依照 TIME 排序 & 計算最差值 (Worst) ----------
    # (a) 先排序，確保第一筆是最早時間
    df.sort_values("TIME", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # (b) 計算最差值
    #   - FOM (Lane_x): 取最小值
    #   - 其他項目: 取最大值
    worst_cases = []
    for col in fom_cols:
        if df[col].dropna().empty:
            continue
        idx = df[col].idxmin()
        worst_cases.append({
            "Metric": col,
            "Worst Value": df.loc[idx, col],
            "Timestamp": df.loc[idx, "TIME"]
        })
    for col in other_cols:
        if df[col].dropna().empty:
            continue
        idx = df[col].idxmax()
        worst_cases.append({
            "Metric": col,
            "Worst Value": df.loc[idx, col],
            "Timestamp": df.loc[idx, "TIME"]
        })

    # 建立最差值表格的 HTML
    worst_rows_html = ""
    for wc in worst_cases:
        worst_rows_html += f"""
            <tr>
                <td>{wc['Metric']}</td>
                <td>{wc['Worst Value']}</td>
                <td>{wc['Timestamp']}</td>
            </tr>
        """
    worst_table_html = f"""
        <table>
            <tr>
                <th colspan="3" style="font-size:18px;">Worst Cases Summary</th>
            </tr>
            <tr>
                <th>Metric</th>
                <th>Worst Value</th>
                <th>Timestamp</th>
            </tr>
            {worst_rows_html}
        </table>
    """

    # ---------- 4) 產生 Box Plot (Lane_0 ~ Lane_15) ----------
    data_for_box = [df[col].dropna() for col in fom_cols]
    fig_box, ax_box = plt.subplots(figsize=(16, 8))
    box = ax_box.boxplot(data_for_box, notch=True, patch_artist=True)

    # 設定顏色
    colors = plt.cm.Pastel1(np.linspace(0, 1, len(fom_cols)))
    for patch, color in zip(box['boxes'], colors):
        patch.set_facecolor(color)

    ax_box.set_xlabel("")
    ax_box.set_ylabel("")
    ax_box.set_xticks(range(1, len(fom_cols) + 1))
    ax_box.set_xticklabels([f"Lane{i}" for i in range(len(fom_cols))])
    ax_box.grid(True)

    # Box Plot -> Base64
    buf_box = BytesIO()
    fig_box.savefig(buf_box, format='png', bbox_inches='tight')
    buf_box.seek(0)
    boxplot_base64 = base64.b64encode(buf_box.read()).decode()
    plt.close(fig_box)

    # ---------- 5) 產生 Time-Domain Metrics 圖表 ----------
    # (a) 先計算每筆資料相對於第一筆時間的 Minutes
    df["Minutes"] = (df["TIME"] - df["TIME"].iloc[0]).dt.total_seconds() / 60

    # (b) 計算 FOM 平均值
    df["FOM_Mean"] = df[fom_cols].mean(axis=1)

    # (c) 選擇要畫的指標：包含其他項目與 FOM_Mean
    time_metrics = ["CPU_Utilization", "RX_Error", "TX_Error",
                    "CPU_Power", "Memory_Power", "BER", "Card_Tmp", "FOM_Mean"]
    fig_time, axes = plt.subplots(nrows=len(time_metrics), ncols=1, figsize=(16, 15), sharex=True)

    # 逐一繪製各指標，以 Minutes 作為 X 軸
    for i, metric in enumerate(time_metrics):
        if metric not in df.columns:
            continue
        axes[i].plot(df["Minutes"], df[metric], label=metric, linewidth=0.8)
        axes[i].set_ylabel(metric)
        axes[i].grid(True)
        axes[i].legend(loc="upper right")

    # 最後一個 subplot 的 X 軸標籤改成「Time (minutes)」
    axes[-1].set_xlabel("Time (minutes)")

    # 調整布局，將圖表轉為 Base64
    fig_time.tight_layout(rect=[0, 0, 1, 0.97])
    buf_time = BytesIO()
    fig_time.savefig(buf_time, format='png', bbox_inches='tight')
    buf_time.seek(0)
    timedomain_base64 = base64.b64encode(buf_time.read()).decode()
    plt.close(fig_time)

    # ---------- 6) 組裝 HTML 報告 ----------
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
            }
            th {
                background-color: #f0f0f0;
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
            {worst_table_html}
            <div class="chart-container">
                <div class="chart">
                    <h2>Box Plot of FOM</h2>
                    <img src="data:image/png;base64,{boxplot_base64}" alt="Box Plot"/>
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

    # 輸出 HTML 檔案（副檔名同檔名，但改為 .html）
    output_file = os.path.join(
        os.path.dirname(file_path),
        os.path.basename(file_path).rsplit(".", 1)[0] + ".html"
    )
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"HTML report saved to {output_file}")


# ======= 範例呼叫 =======
plot_pcie_log_box_and_time("D:\\pythonProject\\c53_PCIeDevA_20231127074125.log")
