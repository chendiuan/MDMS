import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots

# 載入資料
file_path = 'D:/pythonProject/TRF_Oahu/Havana_Delton_SC17B32897_PCIe7_8_9_P3P4/Bay6/pcie_margin_consolidated_output_2024_07_05-07_43_53.csv'
data = pd.read_csv(file_path)

# 去除欄位名稱的前後空格
data.columns = data.columns.str.strip()

# Criteria
offset_criteria = 9
volt_criteria_top = 25
volt_criteria_bottom = -25

# 提取需要的欄位並修改數據
lane_data = data[['LanePCIeNo', 'Margin Top (volt)', 'Margin Bottom (volt)', 'Margin Left Offset', 'Margin Right Offset']]
lane_data['Margin Left Offset'] = lane_data['Margin Left Offset']
lane_data['Margin Right Offset'] = lane_data['Margin Right Offset']
lane_data['Margin Top (volt)'] = -lane_data['Margin Top (volt)'] * 1000
lane_data['Margin Bottom (volt)'] = lane_data['Margin Bottom (volt)'] * 1000

# 找到每一欄絕對值後的最小值
min_left_offset = lane_data['Margin Left Offset'].abs().min()
min_right_offset = lane_data['Margin Right Offset'].abs().min()
min_top_volt = lane_data['Margin Top (volt)'].abs().min()
min_bottom_volt = lane_data['Margin Bottom (volt)'].abs().min()

# 構建菱形的點
diamond_points = {
    'x': [-min_left_offset, 0, min_right_offset, 0, -min_left_offset],
    'y': [0, min_top_volt, 0, -min_bottom_volt, 0]
}

# 繪製 Timing Margin 圖表
fig = make_subplots(
    rows=3, cols=1,
    subplot_titles=('Timing Margin vs Lane', 'Voltage Margin vs Lane', 'PCIe (32GT/s) Eye Margin'),
    vertical_spacing=0.1  # 調整這個值來縮小圖之間的距離
)

# Timing Margin 圖表
fig.add_trace(go.Scatter(x=lane_data['Margin Left Offset'], y=lane_data['LanePCIeNo'], mode='lines+markers', name='Margin Left Offset', orientation='h', marker=dict(size=12, color='blue')), row=1, col=1)
fig.add_trace(go.Scatter(x=lane_data['Margin Right Offset'], y=lane_data['LanePCIeNo'], mode='lines+markers', name='Margin Right Offset', orientation='h', marker=dict(size=12, color='blue')), row=1, col=1)
# Timing Margin Criteria
fig.add_trace(go.Scatter(x=[offset_criteria, offset_criteria], y=[lane_data['LanePCIeNo'].min(), lane_data['LanePCIeNo'].max()], mode='lines', name='Offset Criteria', line=dict(color='red')), row=1, col=1)
fig.add_trace(go.Scatter(x=[offset_criteria, offset_criteria], y=[lane_data['LanePCIeNo'].min(), lane_data['LanePCIeNo'].max()], mode='lines', name='Offset Criteria', line=dict(color='red')), row=1, col=1)

# Voltage Margin 圖表
fig.add_trace(go.Scatter(x=lane_data['LanePCIeNo'], y=lane_data['Margin Top (volt)'], mode='lines+markers', name='Margin Top (volt)', marker=dict(size=12, color='blue')), row=2, col=1)
fig.add_trace(go.Scatter(x=lane_data['LanePCIeNo'], y=lane_data['Margin Bottom (volt)'], mode='lines+markers', name='Margin Bottom (volt)', marker=dict(size=12, color='blue')), row=2, col=1)
# Voltage Margin Criteria
fig.add_trace(go.Scatter(x=[lane_data['LanePCIeNo'].min(), lane_data['LanePCIeNo'].max()], y=[volt_criteria_top, volt_criteria_top], mode='lines', name='Volt Criteria Top', line=dict(color='red')), row=2, col=1)
fig.add_trace(go.Scatter(x=[lane_data['LanePCIeNo'].min(), lane_data['LanePCIeNo'].max()], y=[volt_criteria_bottom, volt_criteria_bottom], mode='lines', name='Volt Criteria Bottom', line=dict(color='red')), row=2, col=1)

# Eye Margin 圖表
fig.add_trace(go.Scatter(x=diamond_points['x'], y=diamond_points['y'], mode='lines+markers', name='Eye Margin Diamond', marker=dict(size=12)), row=3, col=1)
# Eye Margin Criteria
fig.add_trace(go.Scatter(x=[-offset_criteria, 0, offset_criteria, 0, -offset_criteria], y=[0, volt_criteria_top, 0, volt_criteria_bottom, 0], mode='lines+markers', name='Eye Margin Criteria', marker=dict(size=12),  line=dict(color='red', dash='dash')), row=3, col=1)

# 更新布局
fig.update_layout(
    height=1800,
    width=1000,
    showlegend=True,
    xaxis=dict(title="Timing Margin", range=[5, 18], title_font=dict(size=18, family='Arial', color='black', weight='bold')),
    yaxis=dict(title="Lane", title_font=dict(size=18, family='Arial', color='black', weight='bold')),
    xaxis2=dict(title="Lane", title_font=dict(size=18, family='Arial', color='black', weight='bold')),
    yaxis2=dict(title="Voltage Margin", title_font=dict(size=18, family='Arial', color='black', weight='bold')),
    xaxis3=dict(title="Timing Margin [ticks]", title_font=dict(size=18, family='Arial', color='black', weight='bold')),
    yaxis3=dict(title="Voltage Margin [mV]", title_font=dict(size=18, family='Arial', color='black', weight='bold'))
)

# 將圖表轉換為HTML
chart_html = fig.to_html(full_html=False)

# 設置 HTML 樣式
html_style = '''
<style>
    table {
        width: 50%;
        margin: 0 auto;
        border-collapse: collapse;
        font-size: 12px;
        text-align: center;
    }
    th, td {
        padding: 4px 8px;
        border: 1px solid #ccc;
    }
    th {
        background-color: #f2f2f2;
    }
    tr:nth-child(even) {
        background-color: #f9f9f9;
    }
</style>
'''

# 將 DataFrame 轉換為 HTML
html_content = data.to_html(index=False, classes='table table-striped', border=0)

# 添加樣式和圖表到 HTML
full_html = f'''
<html>
<head>
    {html_style}
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <h1>PCIe Margin Report</h1>
    {chart_html}
    {html_content}
</body>
</html>
'''

# 儲存為 HTML 檔案
output_file_path = 'C:/Users/chend/Downloads/Riser_FR_FL_57508_MB1/full_data_with_charts.html'
with open(output_file_path, 'w', encoding='utf-8') as f:
    f.write(full_html)

print("報告已生成：full_data_with_charts.html")
