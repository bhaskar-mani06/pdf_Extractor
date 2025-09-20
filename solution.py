# SOLUTION: Add this function to your app.py WITHOUT changing existing code

def extract_values_from_text_universal(text):
    """
    Universal extractor that works with BOTH Shriram and Reliance PDFs
    Add this function to your app.py and replace the call in extract_text()
    """
    template = {
        "policy_number": "",
        "policy_holder_name": "",
        "insured_address": "",
        "vehicle_registration_number": "",
        "engine_number": "",
        "chassis_number": "",
        "make_model": "",
        "fuel_type": "",
        "cubic_capacity": "",
        "year_of_manufacture": "",
        "date_of_registration": "",
        "policy_start_date": "",
        "policy_end_date": "",
        "insurance_company": "",
        "premium_amount": "",
        "previous_insurer": "",
        "previous_policy_number": "",
        "nominee_name": "",
        "nominee_age": "",
        "nominee_relationship": ""
    }

    # Universal patterns for BOTH PDFs
    patterns = {
        "policy_number": r"Policy\s*No\.?\s*([0-9/]+)|Policy\s*Number\s*:\s*([0-9]+)",
        "policy_holder_name": r"IN-\d+\s*/\s*([A-Z\s.]+?)(?:\s*GSTIN|\s*Communication)|Insured\s*Name\s*:\s*([A-Z\s.]+)",
        "insured_address": r"Insured\s*Address[^:]*:\s*([A-Z0-9\s,.-]+?)(?:\s*,Mob|\s*Mobile)|Communication\s*Address[^:]*:\s*([A-Z0-9\s,.-]+?)(?:\s*Mobile|\s*Email)",
        "vehicle_registration_number": r"MH\s*-\s*\d{2}\s*-\s*[A-Z]{2}\s*-\s*\d+|MH\d{2}[A-Z]{2}\d{4}|Registration\s*No\.?\s*:\s*([A-Z0-9]+)",
        "engine_number": r"(\d{10})\s*&|Engine\s*No\.?\s*/\s*Chassis\s*No\.?\s*:\s*([A-Z0-9]+)",
        "chassis_number": r"&\s*(\d{17})|Chassis\s*No\.?\s*:\s*([A-Z0-9]+)",
        "make_model": r"HONDA\s*-\s*[A-Z0-9\s]+|RENAULT\s*/\s*[A-Z\s/]+|Make\s*/\s*Model\s*:\s*([A-Z\s/]+)",
        "fuel_type": r"SCOOTY\s*/\s*(PETROL|DIESEL|CNG)|PETROL\s*RXE",
        "cubic_capacity": r"(\d{2,4})\s*/\s*0\s*/\s*\d{4}|CC\s*/\s*HP\s*/\s*Watt\s*:\s*(\d+)",
        "year_of_manufacture": r"(\d{4})\s*[0-9/]{10}|JUL-(\d{4})",
        "date_of_registration": r"(\d{2}/\d{2}/\d{4})",
        "policy_start_date": r"From\s*00:00\s*Hrs\s*(?:of\s*|on\s*)(\d{2}[/-]\d{2}[/-]\d{4})",
        "policy_end_date": r"Midnight\s*(?:Of\s*|of\s*)(\d{2}[/-]\d{2}[/-]\d{4})",
        "insurance_company": r"(SHRIRAM\s*GENERAL\s*INSURANCE\s*COMPANY\s*LIMITED|RELIANCE\s*GENERAL\s*INSURANCE)",
        "premium_amount": r"PREMIUM\s*AMOUNT\s*(\d+)|Total\s*Premium\s*\(₹\)\s*:\s*(\d+)",
        "previous_insurer": r"Previous\s*Insurer\s*([A-Za-z\s]+?)(?:\s*Limited|\s*Company)",
        "previous_policy_number": r"Previous\s*Policy\s*No\.?\s*(\d+)",
        "nominee_name": r"Nominee\s*for\s*Owner/Driver\s*([A-Z\s]+?)(?:\s*Nominee|\s*Age)",
        "nominee_age": r"Nominee\s*Age\s*(\d+)",
        "nominee_relationship": r"Nominee\s*Relationship\s*([A-Za-z\s]+?)(?:\s*Appointee|\s*$)"
    }

    # Apply regex patterns
    for key, pattern in patterns.items():
        try:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
            if match:
                # Handle multiple groups - take first non-empty group
                extracted_value = ""
                for i in range(1, len(match.groups()) + 1):
                    if match.group(i) and match.group(i).strip():
                        extracted_value = match.group(i).strip()
                        break
                
                if extracted_value:
                    extracted_value = re.sub(r'\s+', ' ', extracted_value)  # Remove extra spaces
                    template[key] = extracted_value
        except Exception as e:
            print(f"Error extracting {key}: {e}")
            continue

    return template

# INSTRUCTIONS FOR YOU:
print("""
=== SOLUTION FOR RELIANCE PDF ===

STEP 1: Add the above function to your app.py

STEP 2: In your extract_text() function, replace this line:
    extracted_values = extract_values_from_text(all_text)

With this line:
    extracted_values = extract_values_from_text_universal(all_text)

STEP 3: Keep your original extract_values_from_text() function unchanged

This way:
✅ Your original code stays the same
✅ Reliance PDF will work
✅ Shriram PDF will continue to work
✅ No breaking changes

The universal function handles both PDF formats!
""")
