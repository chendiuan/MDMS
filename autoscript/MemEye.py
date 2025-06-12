###########################################################################################
##                                 Copyright ©, 2024, by                                 ##
##                         Lenovo Internal. All Rights Reserved.                         ##
##                                      Margin Team                                      ##
##                                                                                       ##
##                                                      Dean Chen (dchen52@lenovo.com)   ##
###########################################################################################
import os
import sys
import json
from tkinter import *
from tkinter import filedialog

sys.dont_write_bytecode = True
cur_dir = os.path.dirname(os.path.abspath(__file__))
root_folder = os.path.dirname(cur_dir)

copyright = f"Dean Chen (dchen52@lenovo.com)"

def generate_html(results):
    html_str = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MemEye Analysis Report</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                background-color: #f0f8ff;
                color: #333;
                margin: 0;
                padding: 20px;
            }
            .container {
                max-width: 1200px;
                margin: 40px auto;
                background-color: #ffffff;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 0 15px rgba(0, 0, 0, 0.1);
                text-align: center;
            }
            h1 {
                text-align: center;
                font-size: 32px;
                font-weight: bold;
            }
            h2 {
                text-align: center;
                font-size: 24px;
                font-weight: bold;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
            }
            th, td {
                border: 1px solid #dddddd;
                padding: 15px;
                text-align: center;
            }
            th {
                background-color: #f0f0f0;
                font-weight: bold;
            }
            tr:nth-child(even) {
                background-color: #f9f9f9;
            }
            .title-header {
                font-size: 20px;
                font-weight: bold;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>MemEye Analysis Report</h1>
            <table>
                <tr>
                    <th colspan="5" class="title-header">Details</th>
                </tr>
                <tr>
                    <th>BIOS</th>
                    <th>Frequency</th>
                    <th>DIMM Type</th>
                    <th>Manufacturer</th>
                    <th>Size</th>
                </tr>
    """
    for result in results:
        for device in result.get("Memory Devices", []):
            html_str += f"""
                <tr>
                    <td>{result.get('BIOS Version', '')}</td>
                    <td>{result.get('Frequency', '')}</td>
                    <td>{result.get('Dimm Type', '')}</td>
                    <td>{device.get('Manufacturer', '')}</td>
                    <td>{device.get('Size', '')}</td>
                    </tr>
                """
            break
    html_str += """
            </table>
            <table>
                <tr>
                    <th colspan="7" class="title-header">Data Information</th>
                </tr>
                <tr>
                    <th>Test Type</th>
                    <th>Min Verf Offset (mV)</th>
                    <th>Max Verf Offset (mV)</th>
                    <th>Total Verf (mV)</th>
                    <th>Min Delay (UI)</th>
                    <th>Max Delay (UI)</th>
                    <th>Total Delay (UI)</th>
                </tr>
    """
    verf_read = float(str.strip(V_read_cri.get()))
    verf_write = float(str.strip(V_write_cri.get()))
    verf_ca = float(str.strip(V_ca_cri.get()))
    verf_cs = float(str.strip(V_cs_cri.get()))
    delay_read = str.strip(D_read_cri.get())
    delay_write = str.strip(D_write_cri.get())
    delay_ca = str.strip(D_ca_cri.get())
    delay_cs = str.strip(D_cs_cri.get())
    test_type_counts = {}
    for result in results:
        test_type = result.get('Test Type', '')
        if test_type:
            test_type_counts[test_type] = test_type_counts.get(test_type, 0) + 1

    processed_types = {}

    for result in results:
        test_type = result.get('Test Type', '')
        min_verf = float(result.get('1D Output', {}).get('Min Vref Offset', 0))
        max_verf = float(result.get('1D Output', {}).get('Max Vref Offset', 0))
        total_verf = round(abs(min_verf) + abs(max_verf), 2)
        first_delay = float(result.get('1D Output', {}).get('First Delay', 0))
        last_delay = float(result.get('1D Output', {}).get('Last Delay', 0))
        total_delay = abs(first_delay) + abs(last_delay)
        rowspan = test_type_counts.get(test_type, 1)

        if test_type not in processed_types:
            html_str += f"""
                <tr>
                    <td rowspan='{rowspan}'>{test_type}</td>
                    <td>{min_verf}</td>
                    <td>{max_verf}</td>
                    <td>{total_verf}</td>
                    <td>{first_delay}</td>
                    <td>{last_delay}</td>
                    <td>{total_delay}</td>
                </tr>
            """
            processed_types[test_type] = True
        else:
            html_str += f"""
                <tr>
                    <td>{min_verf}</td>
                    <td>{max_verf}</td>
                    <td>{total_verf}</td>
                    <td>{first_delay}</td>
                    <td>{last_delay}</td>
                    <td>{total_delay}</td>
                </tr>
            """
    html_str += f"""
            </table>
            <table>
                <tr>
                    <th colspan="5" class="title-header">AMD Criteria</th>
                </tr>
                <tr>
                    <th></th>
                    <th>Cross Read</th>
                    <th>Cross Write</th>
                    <th>Cross CA Fast</th>
                    <th>Cross CS Fast</th>
                </tr>
                <tr>
                    <td>Verf (mV)</td>
                    <td>{verf_read}</td>
                    <td>{verf_write}</td>
                    <td>{verf_ca}</td>
                    <td>{verf_cs}</td>
                </tr>
                <tr>
                    <td>Delay (UI)</td>
                    <td>{delay_read}</td>
                    <td>{delay_write}</td>
                    <td>{delay_ca}</td>
                    <td>{delay_cs}</td>
                </tr>
    """
    html_str += f"""
            </table>
            <table>
                <tr>
                    <th colspan="4" class="title-header">Memory Device</th>
                </tr>
                <tr>
                    <th>Locator</th>
                    <th>MemoryInfo</th>
                    <th>Part Number</th>
                    <th>Serial Number</th>
                </tr>
    """
    for result in results:
        for device in result.get("Memory Devices", []):
            html_str += f"""
                <tr>
                    <td>{device.get('Locator', '')}</td>
                    <td>{device.get('MemoryInfo', '')}</td>
                    <td>{device.get('Part Number', '')}</td>
                    <td>{device.get('Serial Number', '')}</td>
                </tr>
            """
    html_str += """
            </table>
        </div>
    </body>
    </html>
    """
    return html_str

def extract_data_from_json(file_path, seen_devices, seen_values):
    with open(file_path, 'r', encoding='utf-8') as file:
        content = json.load(file)

    test_type = content.get("output", {}).get("test type")
    if not test_type or "Error" in test_type:
        print(f"Skipping file {file_path} due to error test type: {test_type}")
        return None
    frequency = content.get("output", {}).get("frequency")
    dimm_type = content.get("output", {}).get("dimmtype")

    bios_version = None
    for item in content.get("DMI_Details", []):
        if item.get("Type", "").strip() == "BIOS Information":
            bios_version = item.get("Version:", None)
            break

    key_tuple = (frequency, dimm_type, bios_version)
    if key_tuple in seen_values or all(v is None or v == "" for v in key_tuple):
        frequency = dimm_type = bios_version = None
    else:
        seen_values.add(key_tuple)

    memory_devices = []
    for item in content.get("DMI_Details", []):
        if item.get("Type", "").strip() == "Memory Device":
            memory_device = (
                item.get("Locator:", None),
                item.get("Manufacturer:", None),
                item.get("MemoryInfo:", None),
                item.get("Part Number:", None),
                item.get("Serial Number:", None),
                item.get("Size:", None)
            )
            if memory_device not in seen_devices and any(v is not None and v != "" for v in memory_device):
                seen_devices.add(memory_device)
                memory_devices.append(
                    {k: v for k, v in zip(["Locator", "Manufacturer", "MemoryInfo", "Part Number", "Serial Number", "Size"], memory_device) if
                     v is not None and v != ""})

    output_data = {
        "Test Type": test_type,
        "1D Output": {k: v for k, v in {
            "First Delay": content.get("output", {}).get("1d_output", [{}])[0].get("delay"),
            "Max Vref Offset": content.get("output", {}).get("1d_output", [{}])[1].get("Max Vref offset(mV)"),
            "Min Vref Offset": content.get("output", {}).get("1d_output", [{}])[1].get("Min Vref offset(mV)"),
            "Last Delay": content.get("output", {}).get("1d_output", [{}])[2].get("delay")
        }.items() if v is not None and v != ""},
        "Frequency": frequency if frequency is not None and frequency != "" else None,
        "Dimm Type": dimm_type if dimm_type is not None and dimm_type != "" else None,
        "BIOS Version": bios_version if bios_version is not None and bios_version != "" else None
    }

    if memory_devices:
        output_data["Memory Devices"] = memory_devices

    return {k: v for k, v in output_data.items() if v is not None and v != ""}

def scan_directory_for_results(directory):
    results = []
    seen_devices = set()
    seen_values = set()

    for root, _, files in os.walk(directory):
        for file in files:
            if "result" in file.lower() and file.endswith(".txt"):
                file_path = os.path.join(root, file)
                extracted_data = extract_data_from_json(file_path, seen_devices, seen_values)
                if extracted_data:
                    results.append(extracted_data)
    return results

def html_output(file_path, full_html):
    output_file_path = os.path.splitext(file_path)[0] + '.html'
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(full_html)

def browse():
    filename = filedialog.askdirectory(title="Select Result Directory")
    if filename:
        E_Raw_data.delete(0, END)
        E_Raw_data.insert(0, filename)

def generate_button():
    file_path = str.strip(E_Raw_data.get())
    results = scan_directory_for_results(file_path)
    full_html = generate_html(results)
    html_output(file_path, full_html)


# main script
rootframe = Tk()
rootframe.title("MemEye Result Analyzer")
rootframe.wm_geometry("%dx%d+%d+%d" % (640, 280, 200, 100))
rootframe.resizable(0, 0)
# Raw Data Path
Log_Label = LabelFrame(rootframe, text=" Raw Data Path ", font=("arial", 10), height=75, width=600)
Log_Label.place(x=20, y=10)
# Raw Data Folder
E_Raw_data = Entry(rootframe, width=65, font=("arial", 10))
E_Raw_data.place(x=35, y=40)
B_Raw_data = Button(rootframe, text=" Browse.. ", command=browse, pady=2, width=8, font=("arial", 12, "bold"))
B_Raw_data.place(x=515, y=30)
# Verf Criteria
Criteria_Label = LabelFrame(rootframe, text=" Verf Criteria ", font=("arial", 10), height=175, width=225)
Criteria_Label.place(x=20, y=90)
# Cross Read
V_read_cri = Label(rootframe, text="Cross Read :", height=2, font=("arial", 10))
V_read_cri.place(x=30, y=120)
V_read_cri = Entry(rootframe, width=8, font=("arial", 10))
V_read_cri.insert(0, "20.8")
V_read_cri.place(x=165, y=130)
# Cross Write
V_write_cri = Label(rootframe, text="Cross Write :", height=2, font=("arial", 10))
V_write_cri.place(x=30, y=150)
V_write_cri = Entry(rootframe, width=8, font=("arial", 10))
V_write_cri.insert(0, "27.5")
V_write_cri.place(x=165, y=160)
# Cross CA Fast
V_ca_cri = Label(rootframe, text="Cross CA Fast :", height=2, font=("arial", 10))
V_ca_cri.place(x=30, y=180)
V_ca_cri = Entry(rootframe, width=8, font=("arial", 10))
V_ca_cri.insert(0, "55")
V_ca_cri.place(x=165, y=190)
# Cross CS Fast
V_cs_cri = Label(rootframe, text="Cross CS Fast :", height=2, font=("arial", 10))
V_cs_cri.place(x=30, y=210)
V_cs_cri = Entry(rootframe, width=8, font=("arial", 10))
V_cs_cri.insert(0, "55")
V_cs_cri.place(x=165, y=220)
# Delay Criteria
Criteria_Label = LabelFrame(rootframe, text=" Delay Criteria ", font=("arial", 10), height=175, width=225)
Criteria_Label.place(x=250, y=90)
# Cross Read
D_read_cri = Label(rootframe, text="Cross Read :", height=2, font=("arial", 10))
D_read_cri.place(x=260, y=120)
D_read_cri = Entry(rootframe, width=8, font=("arial", 10))
D_read_cri.insert(0, "6")
D_read_cri.place(x=395, y=130)
# Cross Write
D_write_cri = Label(rootframe, text="Cross Write :", height=2, font=("arial", 10))
D_write_cri.place(x=260, y=150)
D_write_cri = Entry(rootframe, width=8, font=("arial", 10))
D_write_cri.insert(0, "5")
D_write_cri.place(x=395, y=160)
# Cross CA Fast
D_ca_cri = Label(rootframe, text="Cross CA Fast :", height=2, font=("arial", 10))
D_ca_cri.place(x=260, y=180)
D_ca_cri = Entry(rootframe, width=8, font=("arial", 10))
D_ca_cri.insert(0, "8")
D_ca_cri.place(x=395, y=190)
# Cross CS Fast
D_cs_cri = Label(rootframe, text="Cross CS Fast :", height=2, font=("arial", 10))
D_cs_cri.place(x=260, y=210)
D_cs_cri = Entry(rootframe, width=8, font=("arial", 10))
D_cs_cri.insert(0, "8")
D_cs_cri.place(x=395, y=220)
# Generate Button
B_Generate = Button(rootframe, text="Generate", command=generate_button, pady=10, width=10, font=("arial", 14, "bold"))
B_Generate.place(x=490, y=150)

rootframe.mainloop()
