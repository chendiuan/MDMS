import pandas as pd
import json
import os
import re

def normalize_field_name(name):
    """Normalize column names to JSON field names (lowercase, replace spaces with underscores, handle newlines)."""
    if not isinstance(name, str):
        return "-"
    name = name.strip().replace('\n', ' ').lower()  # Replace newlines with space
    name = re.sub(r'\s+', '_', name)  # Replace multiple spaces with single underscore
    name = re.sub(r'[^\w]', '', name)  # Remove non-alphanumeric characters
    return name if name else "-"

def create_json_structure(sheet_name, df):
    """Create JSON structure based on sheet data, keeping only unmarked fields."""
    # Normalize sheet name for IDs
    sheet_id = normalize_field_name(sheet_name).replace('_', '-')
    table_id = f"{sheet_id}-table"
    
    # Define fields to keep (based on unmarked columns in the first Excel screenshot)
    expected_fields = [
        'end_device', 'source', 'mcio_cable', 'new_cable', 'power_cable',
        'awg', 'length', 'loss', 'to', 'slot', 'report'
    ]
    
    # Process each row
    content = []
    for _, row in df.iterrows():
        row_dict = {}
        for field in expected_fields:
            # Try to find matching column
            normalized_cols = {normalize_field_name(col): col for col in df.columns}
            col_key = next((k for k in normalized_cols if k == field), None)
            if col_key:
                value = row[normalized_cols[col_key]]
                # Handle NaN, None, or empty values
                if pd.isna(value) or value is None or (isinstance(value, str) and not value.strip()):
                    row_dict[field] = None  # Use null for JSON compatibility
                else:
                    # Convert numbers to strings to avoid JSON serialization issues
                    row_dict[field] = str(value).strip()
            else:
                row_dict[field] = None  # Use null for missing fields
        content.append(row_dict)  # Append all rows, even if some fields are None
    
    # Create JSON structure only if there is content
    if not content:
        return None
    
    json_data = {
        "tablists": [
            {
                "id": sheet_id,
                "tabs": [
                    {
                        "id": table_id,
                        "content": content
                    }
                ]
            }
        ]
    }
    return json_data

def excel_to_json(excel_file):
    """Convert each Excel sheet to a separate JSON file in the same directory as the input file."""
    try:
        # Get the directory of the input Excel file
        input_dir = os.path.dirname(os.path.abspath(excel_file)) if excel_file else os.getcwd()
        
        # Read Excel file
        xls = pd.ExcelFile(excel_file)
        
        # Process each sheet
        for sheet_name in xls.sheet_names:
            # Read sheet into DataFrame
            df = pd.read_excel(xls, sheet_name=sheet_name, dtype=str)
            
            # Create JSON structure
            json_data = create_json_structure(sheet_name, df)
            
            # Write to JSON file only if there is data to write
            if json_data:
                output_file = os.path.join(input_dir, f"{sheet_name}.json")
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, ensure_ascii=False)
                print(f"Generated JSON file: {output_file}")
            else:
                print(f"No valid data to generate JSON for sheet: {sheet_name}")
                
    except FileNotFoundError:
        print(f"Error: Excel file '{excel_file}' not found.")
    except Exception as e:
        print(f"Error processing Excel file: {str(e)}")

if __name__ == "__main__":
    excel_file = r"H:\OneDrive_2025-06-22\Test Plan\ARM-Tasmania\EV_Margin-Tasmania Test Plan.xlsx"
    #excel_file = r"H:\OneDrive_2025-06-22\Test Plan\Intel-BHS-Suzuka\Suzuka_EV_Margin_Test_Plan_20250528.xlsx"
    excel_to_json(excel_file)