import numpy as np
import pandas as pd
import os
import base64
from datetime import datetime

#=========================================================================
#=========================================================================

Product = ""
input_file = r"C:\Users\dchen52\OneDrive - Lenovo\Documents\Microchip\Switch_log\2D_Eye_Data_2024-12-26_155157.xlsx"
image_path = r"C:\Users\dchen52\OneDrive - Lenovo\Documents\Microchip\Switch_log\image.png"  # Specified image path

#=========================================================================
#=========================================================================

def parse_excel_data(file_path):
    """Parse data from Excel file with multiple sheets."""
    try:
        xl = pd.ExcelFile(file_path)
        sheets = xl.sheet_names
        eye_metrics = []

        if "Eye Metrics" in sheets:
            df_metrics = pd.read_excel(file_path, sheet_name="Eye Metrics", header=1)
            for _, row in df_metrics.iterrows():
                lane = row.iloc[0]
                if pd.isna(lane) or not str(lane).startswith("Lane #"):
                    continue
                link_speed = (
                    row.iloc[1]
                    if len(row) > 1 and not pd.isna(row.iloc[1])
                    else "Unknown"
                )
                eye_metrics_str = (
                    row.iloc[2] if len(row) > 2 and not pd.isna(row.iloc[2]) else None
                )
                if eye_metrics_str:
                    try:
                        eye_width_ui, eye_height_mv = map(
                            float,
                            eye_metrics_str.replace(" UI x ", " ")
                            .replace(" mV", "")
                            .split(),
                        )
                        eye_metrics.append(
                            {
                                "lane": lane,
                                "link_speed": link_speed,
                                "eye_width_ui": eye_width_ui,
                                "eye_height_mv": eye_height_mv,
                            }
                        )
                    except Exception as e:
                        print(f"Error parsing eye metrics for {lane}: {e}")
                        continue

        lane_data = {}
        raw_data_params = []
        for sheet in sheets:
            if sheet.startswith("Lane #"):
                try:
                    df_lane = pd.read_excel(file_path, sheet_name=sheet, header=1)
                    x_columns = [
                        col for col in df_lane.columns[1:] if "X =" in str(col)
                    ]
                    if not x_columns:
                        continue
                    x_values = [
                        float(col.split("=")[1].strip())
                        for col in x_columns
                        if "=" in col
                    ]
                    y_values = [
                        float(str(y).split("=")[1].strip())
                        for y in df_lane["Bin#"]
                        if pd.notna(y) and "Y =" in str(y)
                    ]
                    if not x_values or not y_values:
                        continue
                    data = df_lane[x_columns].apply(pd.to_numeric, errors="coerce")
                    data = data.dropna(how="all")
                    if data.empty or len(y_values) != data.shape[0]:
                        y_values = y_values[: data.shape[0]]
                    lane_data[sheet] = {
                        "x_values": np.array(x_values),
                        "y_values": np.array(y_values),
                        "data": data.values,
                    }
                    raw_data_params.append(
                        {
                            "lane": sheet,
                            "num_dac": len(y_values),
                            "num_phs": len(x_values),
                            "phs_step_ui": (
                                np.mean(np.diff(x_values)) if len(x_values) > 1 else 0.0
                            ),
                            "dac_step_mv": (
                                np.mean(np.diff(y_values)) if len(y_values) > 1 else 0.0
                            ),
                        }
                    )
                except Exception as e:
                    print(f"Error parsing lane sheet {sheet}: {e}")
                    continue

        if not lane_data:
            print(
                "Warning: No valid Lane sheets found. Proceeding with empty lane_data..."
            )
        return eye_metrics, lane_data, pd.DataFrame(raw_data_params)
    except Exception as e:
        print(f"Failed to parse Excel file {file_path}: {e}")
        raise


def calculate_eye_metrics(lane_data, lane_id, phs_step_ui, dac_step_mv):
    """Calculate eye metrics: up(mV), down(mV), left(uI), right(uI), EH*EW."""
    try:
        data = lane_data["data"]
        threshold = 0.9
        high_quality = data <= threshold

        if not np.any(high_quality):
            center_dac, center_phase = np.unravel_index(np.argmin(data), data.shape)
            up_mv = down_mv = center_dac * dac_step_mv
            left_ui = right_ui = center_phase * phs_step_ui
            eh_ew = 0.0
        else:
            dac_indices, phase_indices = np.where(high_quality)
            dac_min, dac_max = dac_indices.min(), dac_indices.max()
            phase_min, phase_max = phase_indices.min(), phase_indices.max()
            up_mv = dac_max * dac_step_mv
            down_mv = -dac_min * dac_step_mv
            left_ui = -phase_min * phs_step_ui
            right_ui = phase_max * phs_step_ui
            eh_ew = abs((right_ui - left_ui) * (up_mv - down_mv))

        return {
            "lane": lane_id,
            "up(mV)": up_mv,
            "down(mV)": down_mv,
            "left(uI)": left_ui,
            "right(uI)": right_ui,
            "EH*EW": eh_ew,
        }
    except Exception as e:
        print(f"Error calculating eye metrics for {lane_id}: {e}")
        raise


def get_config_info():
    """Return simplified device info."""
    return [("Microchip", Product)]


def generate_html_report(
    margin_df,
    worst_cases,
    raw_data_params,
    output_path,
    config_info,
    eye_metrics,
    lane_data,
):
    """Generate HTML report with Data Information, worst-case lanes, single image, and raw data."""
    current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html_content = f"""<!DOCTYPE html>
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
        h1 {{
            margin-bottom: 20px;
            font-size: 28px;
        }}
        h2 {{
            margin-top: 30px;
            margin-bottom: 15px;
            font-size: 22px;
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
            font-size: 15px;
        }}
        th {{
            background-color: #f0f0f0;
            font-weight: bold;
        }}
        .title-header {{
            font-size: 18px;
            font-weight: bold;
            background-color: #e0e0e0;
        }}
        .image-section {{
            margin-top: 30px;
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
<table><tr><th colspan="2" class="title-header">Data Information</th></tr><tr><th>Vendor</th><th>Device</th></tr>
"""
    for vendor, device in config_info:
        html_data_info += f"<tr><td>{vendor}</td><td>{device}</td></tr>"

    html_worst = """
</table><table><tr><th colspan="6" class="title-header">Worst Cases Summary</th></tr><tr><th>Lane</th><th>EH*EW</th><th>Top (mV)</th><th>Bottom (mV)</th><th>Left (UI)</th><th>Right (UI)</th></tr>
"""
    if not worst_cases.empty:
        for _, row in worst_cases.iterrows():
            lane = row["lane"]
            worst_metric = row["worst_metric"]
            eh_ew = (
                f"<td class='worst-metric'>{row['EH*EW']:.1f}</td>"
                if worst_metric == "EH*EW"
                else f"<td>{row['EH*EW']:.1f}</td>"
            )
            up_mv = (
                f"<td class='worst-metric'>{row['up(mV)']:.1f}</td>"
                if worst_metric == "Top (mV)"
                else f"<td>{row['up(mV)']:.1f}</td>"
            )
            down_mv = (
                f"<td class='worst-metric'>{row['down(mV)']:.1f}</td>"
                if worst_metric == "Bottom (mV)"
                else f"<td>{row['down(mV)']:.1f}</td>"
            )
            left_ui = (
                f"<td class='worst-metric'>{row['left(uI)']:.2f}</td>"
                if worst_metric == "Left (UI)"
                else f"<td>{row['left(uI)']:.2f}</td>"
            )
            right_ui = (
                f"<td class='worst-metric'>{row['right(uI)']:.2f}</td>"
                if worst_metric == "Right (UI)"
                else f"<td>{row['right(uI)']:.2f}</td>"
            )
            html_worst += (
                f"<tr><td>{lane}</td>{eh_ew}{up_mv}{down_mv}{left_ui}{right_ui}</tr>"
            )
    else:
        html_worst += "<tr><td colspan='6'>No worst-case data available</td></tr>"

    html_images = """
</table>
<div class="container">
    <div class="image-section">
        <h2>Eye Diagram</h2>
"""
    if os.path.exists(image_path):
        try:
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()  # Read full file
                # Validate image data length to ensure it's not empty
                if not image_data:
                    raise ValueError("Image data is empty")
                image_base64 = base64.b64encode(image_data).decode("utf-8")
                # Determine MIME type based on file extension
                mime_type = (
                    "image/png" if image_path.lower().endswith(".png") else "image/jpeg"
                )
                html_images += f'<img src="data:{mime_type};base64,{image_base64}" alt="16_lane_eye_diagram" /><br>'
        except Exception as e:
            html_images += f"<p>Failed to load image from {image_path}: {str(e)}. Please ensure the file is not corrupted or update the image_path if the format differs (e.g., .jpg or .jpeg).</p>"
    else:
        html_images += f"<p>Image not found at {image_path}. Please verify the file exists or update the image_path variable to the correct location.</p>"
    html_images += "</div></div>"

    html_rawdata = """
</table><table><tr><th colspan="4" class="title-header">Raw Data</th></tr><tr><th>Lane</th><th>Link Speed</th><th>Eye Width (UI)</th><th>Eye Height (mV)</th></tr>
"""
    if eye_metrics:
        for metric in eye_metrics:
            html_rawdata += f"<tr><td>{metric['lane']}</td><td>{metric['link_speed']}</td><td>{metric['eye_width_ui']:.2f}</td><td>{metric['eye_height_mv']:.1f}</td></tr>"
    else:
        html_rawdata += "<tr><td colspan='4'>No Eye Metrics data available</td></tr>"

    html_footer = """
</table></div></body></html>
"""

    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(
                html_content
                + html_data_info
                + html_worst
                + html_images
                + html_rawdata
                + html_footer
            )
    except Exception as e:
        print(f"Failed to write HTML report to {output_path}: {e}")
        raise


def main(input_file):
    output_dir = os.path.dirname(input_file) or "."

    try:
        eye_metrics, lane_data, raw_data_params = parse_excel_data(input_file)

        all_metrics = []
        config_info = get_config_info()

        phs_step_ui = (
            raw_data_params["phs_step_ui"].mean()
            if not raw_data_params.empty and len(raw_data_params) > 0
            else 0.028
        )
        dac_step_mv = (
            raw_data_params["dac_step_mv"].mean()
            if not raw_data_params.empty and len(raw_data_params) > 0
            else 1.859
        )

        for lane_id in lane_data:
            metrics = calculate_eye_metrics(
                lane_data[lane_id], lane_id, phs_step_ui, dac_step_mv
            )
            all_metrics.append(metrics)

        margin_df = pd.DataFrame(all_metrics)

        worst_cases = []
        if not margin_df.empty:
            worst_eh_ew = margin_df.loc[margin_df["EH*EW"].idxmin()].copy()
            worst_eh_ew["worst_metric"] = "EH*EW"
            worst_cases.append(worst_eh_ew)
            worst_up_mv = margin_df.loc[margin_df["up(mV)"].idxmin()].copy()
            worst_up_mv["worst_metric"] = "Top (mV)"
            worst_cases.append(worst_up_mv)
            worst_down_mv = margin_df.loc[margin_df["down(mV)"].idxmax()].copy()
            worst_down_mv["worst_metric"] = "Bottom (mV)"
            worst_cases.append(worst_down_mv)
            worst_left_ui = margin_df.loc[margin_df["left(uI)"].idxmax()].copy()
            worst_left_ui["worst_metric"] = "Left (UI)"
            worst_cases.append(worst_left_ui)
            worst_right_ui = margin_df.loc[margin_df["right(uI)"].idxmin()].copy()
            worst_right_ui["worst_metric"] = "Right (UI)"
            worst_cases.append(worst_right_ui)

        worst_cases = pd.DataFrame(worst_cases)

        output_filename = f"Margin_Analysis_Report_{datetime.now().strftime('%Y_%m_%d_%H_%M_%S')}.html"
        output_path = os.path.join(output_dir, output_filename)
        generate_html_report(
            margin_df,
            worst_cases,
            raw_data_params,
            output_path,
            config_info,
            eye_metrics,
            lane_data,
        )
        print(f"Report generated at: {output_path}")
    except Exception as e:
        print(f"Error in main process: {e}")
        raise


if __name__ == "__main__":
    main(input_file)
