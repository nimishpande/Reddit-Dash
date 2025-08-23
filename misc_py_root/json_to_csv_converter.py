import json
import csv
import os
from dotenv import load_dotenv

# Load config from .env
load_dotenv()
try:
    MAX_ARRAY = int(os.getenv('MAX_ARRAY', 3))
except Exception:
    MAX_ARRAY = 3
try:
    MAX_DEPTH = int(os.getenv('MAX_DEPTH', 2))
except Exception:
    MAX_DEPTH = 2

# Define scalar fields in desired order
SCALAR_FIELDS = [
    'id', 'inci_name', 'name', 'description', 'regulation', 'reference',
    'cheminical_iupac_name', 'cas', 'einecs_elincs', 'cosmetic_restriction', 'score', 'percentage'
]


def flatten(obj, parent_key='', sep='_', max_array=3, max_depth=2, depth=0):
    """Recursively flatten nested JSON objects and arrays"""
    items = {}
    if depth > max_depth:
        return items
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            items.update(flatten(v, new_key, sep, max_array, max_depth, depth + 1))
    elif isinstance(obj, list):
        for i in range(min(len(obj), max_array)):
            v = obj[i]
            new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
            items.update(flatten(v, new_key, sep, max_array, max_depth, depth + 1))
    else:
        items[parent_key] = obj
    return items


def parse_json_log_file(input_file, output_file):
    """Parse JSON log file and convert to CSV"""
    print(f"Converting {input_file} to {output_file}")
    
    all_records = []
    all_fieldnames = set(SCALAR_FIELDS)
    
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split content by "ID: " to separate different records
    records = content.split('ID: ')[1:]  # Skip the first empty part
    
    for record in records:
        if not record.strip():
            continue
        
        # Extract ID and JSON
        lines = record.strip().split('\n')
        ingredient_id = lines[0].strip()
        
        # Find the JSON part (everything between the first { and the last })
        json_start = -1
        json_end = -1
        brace_count = 0
        
        for i, line in enumerate(lines[1:], 1):
            if '{' in line and json_start == -1:
                json_start = i
            if json_start != -1:
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0:
                    json_end = i
                    break
        
        if json_start == -1 or json_end == -1:
            print(f"Could not find valid JSON for ID {ingredient_id}")
            continue
        
        # Extract the JSON lines
        json_lines = lines[json_start:json_end + 1]
        
        try:
            # Parse the JSON
            json_str = '\n'.join(json_lines)
            data = json.loads(json_str)
            
            # Ensure data is a dictionary
            if not isinstance(data, dict):
                print(f"Warning: Data for ID {ingredient_id} is not a dictionary, skipping...")
                continue
            
            # Flatten the data
            flat_data = flatten(data, '', '_', MAX_ARRAY, MAX_DEPTH, 0)
            
            # Create record with scalar fields first
            record_data = {field: data.get(field, '') for field in SCALAR_FIELDS}
            record_data.update(flat_data)
            
            all_records.append(record_data)
            all_fieldnames.update(record_data.keys())
            
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON for ID {ingredient_id}: {e}")
            continue
        except Exception as e:
            print(f"Unexpected error for ID {ingredient_id}: {e}")
            continue
    
    if not all_records:
        print("No valid records found in the JSON log file")
        return
    
    # Compose the full header in the desired order
    all_fieldnames = list(SCALAR_FIELDS) + [f for f in sorted(all_fieldnames) if f not in SCALAR_FIELDS]
    
    # Write to CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=all_fieldnames)
        writer.writeheader()
        for record in all_records:
            writer.writerow(record)
    
    print(f"Successfully converted {len(all_records)} records to {output_file}")


def main():
    """Main function to convert JSON log files to CSV"""
    # List of JSON log files to convert
    json_files = [
        'ingredient_json_log.txt',
        'magnesium_ascorbyl_json_log.txt',
        'behentrimonium_json_log.txt'
    ]
    
    for json_file in json_files:
        if os.path.exists(json_file):
            output_file = json_file.replace('_json_log.txt', '_from_json.csv')
            parse_json_log_file(json_file, output_file)
        else:
            print(f"File {json_file} not found, skipping...")


if __name__ == "__main__":
    main() 