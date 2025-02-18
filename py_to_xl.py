import os
import json
import pandas as pd
import shutil

# Set directories
json_directory = "./output"  
excel_directory = "./cleaned_xl_files"  

# Ensure output directory exists
os.makedirs(excel_directory, exist_ok=True)

# Function to extract required data
def process_json_file(json_path):
    with open(json_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    
    msa_name = data.get("msa_name", "Unknown_MSA").replace(",", "").replace(" ", "_")  # Clean filename
    records = []

    for entry in data.get("results", []):
        npi_number = entry.get("number")
        np_type = entry.get("enumeration_type")
        description = entry.get("taxonomies", [{}])[0].get("desc", "")

        # Get Name (Personal or Authorized)
        basic_info = entry.get("basic", {})
        if "organization_name" in basic_info:
            name = basic_info.get("organization_name", "")
        else:
            first = basic_info.get("first_name", "")
            middle = basic_info.get("middle_name", "")
            last = basic_info.get("last_name", "")
            name = " ".join(filter(None, [first, middle, last]))  # Combine name parts

        # Get Office Verified Number
        office_number = basic_info.get("authorized_official_telephone_number", "")

        # Get Address (Prefer Organization, else Personal)
        addresses = entry.get("addresses", [])
        org_address = next((a for a in addresses if a.get("address_purpose") == "LOCATION"), None)
        personal_address = next((a for a in addresses if a.get("address_purpose") == "MAILING"), None)
        address = org_address if org_address else personal_address
        
        full_address = (
            f"{address.get('address_1', '')}, {address.get('city', '')}, {address.get('state', '')}, {address.get('postal_code', '')}"
            if address else ""
        )

        records.append([npi_number, name, np_type, description, office_number, full_address])

    return msa_name, records

# Process all JSON files
for filename in os.listdir(json_directory):
    if filename.endswith(".json"):
        json_path = os.path.join(json_directory, filename)
        msa_name, extracted_data = process_json_file(json_path)

        if extracted_data:
            output_file = os.path.join(excel_directory, f"{msa_name}.xlsx")
            df = pd.DataFrame(extracted_data, columns=["NPI Number", "Name", "Type", "Description", "Office Verified Number", "Address"])
            df.to_excel(output_file, index=False)
            print(f"✅ Saved: {output_file}")

print("Process completed!")
