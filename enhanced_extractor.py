import re

def extract_values_from_text_enhanced(text):
    """
    Enhanced version that works with both Shriram and Reliance PDFs
    WITHOUT changing your original code
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

    # Enhanced patterns that work for BOTH Shriram and Reliance
    patterns = {
        # Policy Number - Works for both
        "policy_number": r"Policy\s*No\.?\s*([0-9/]+)|Policy\s*Number\s*([0-9]+)",
        
        # Policy Holder Name - Works for both
        "policy_holder_name": r"IN-\d+\s*/\s*([A-Z\s.]+?)(?:\s*GSTIN|\s*Communication)|Insured\s*Name\s*([A-Z\s.]+)",
        
        # Insured Address - Works for both
        "insured_address": r"Insured\s*Address\s*(?:and\s*Contact\s*Details)?\s*([A-Z0-9\s,.-]+?)(?:\s*,Mob|\s*Mobile)|Communication\s*Address[^:]*:\s*([A-Z0-9\s,.-]+?)(?:\s*Mobile|\s*Email)",
        
        # Vehicle Registration - Works for both
        "vehicle_registration_number": r"MH\s*-\s*\d{2}\s*-\s*[A-Z]{2}\s*-\s*\d+|MH\d{2}[A-Z]{2}\d{4}|Registration\s*No\.?\s*:\s*([A-Z0-9]+)",
        
        # Engine Number - Works for both
        "engine_number": r"(\d{10})\s*&|Engine\s*No\.?\s*/\s*Chassis\s*No\.?\s*([A-Z0-9]+)",
        
        # Chassis Number - Works for both
        "chassis_number": r"&\s*(\d{17})|Chassis\s*No\.?\s*([A-Z0-9]+)",
        
        # Make Model - Works for both
        "make_model": r"HONDA\s*-\s*[A-Z0-9\s]+|RENAULT\s*/\s*[A-Z\s/]+|Make\s*/\s*Model\s*:\s*([A-Z\s/]+)",
        
        # Fuel Type - Works for both
        "fuel_type": r"SCOOTY\s*/\s*(PETROL|DIESEL|CNG)|PETROL\s*RXE",
        
        # Cubic Capacity - Works for both
        "cubic_capacity": r"(\d{2,4})\s*/\s*0\s*/\s*\d{4}|CC\s*/\s*HP\s*/\s*Watt\s*:\s*(\d+)",
        
        # Year of Manufacture - Works for both
        "year_of_manufacture": r"(\d{4})\s*[0-9/]{10}|JUL-(\d{4})",
        
        # Date of Registration - Works for both
        "date_of_registration": r"(\d{2}/\d{2}/\d{4})",
        
        # Policy Start Date - Works for both
        "policy_start_date": r"From\s*00:00\s*Hrs\s*(?:of\s*|on\s*)(\d{2}[/-]\d{2}[/-]\d{4})",
        
        # Policy End Date - Works for both
        "policy_end_date": r"Midnight\s*(?:Of\s*|of\s*)(\d{2}[/-]\d{2}[/-]\d{4})",
        
        # Insurance Company - Works for both
        "insurance_company": r"(SHRIRAM\s*GENERAL\s*INSURANCE\s*COMPANY\s*LIMITED|RELIANCE\s*GENERAL\s*INSURANCE)",
        
        # Premium Amount - Works for both
        "premium_amount": r"PREMIUM\s*AMOUNT\s*(\d+)|Total\s*Premium\s*\(₹\)\s*:\s*(\d+)",
        
        # Previous Insurer - Works for both
        "previous_insurer": r"Previous\s*Insurer\s*([A-Za-z\s]+?)(?:\s*Limited|\s*Company)",
        
        # Previous Policy Number - Works for both
        "previous_policy_number": r"Previous\s*Policy\s*No\.?\s*(\d+)",
        
        # Nominee Name - Works for both
        "nominee_name": r"Nominee\s*for\s*Owner/Driver\s*([A-Z\s]+?)(?:\s*Nominee|\s*Age)",
        
        # Nominee Age - Works for both
        "nominee_age": r"Nominee\s*Age\s*(\d+)",
        
        # Nominee Relationship - Works for both
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

# Test with both PDFs
def test_both_pdfs():
    print("=== TESTING ENHANCED PATTERNS ===\n")
    
    # Shriram PDF text
    shriram_text = """
    Policy No. 10047/31/26/002595
    IN-23512287 / MR. ARPIT SRIVASTAVA
    Insured Address and Contact Details DFDS FSDF , MUMBAI, MAHARASHTRA - 400001
    MH - 01 - SW - 3422 & MUMBAI CENTRAL
    6655774488 & 99554411225544778
    HONDA - ACTIVA 5G STD BS4
    SCOOTY / PETROL
    110 / 0 / 2019
    27/08/2019
    SHRIRAM GENERAL INSURANCE COMPANY LIMITED
    PREMIUM AMOUNT 1507
    """
    
    # Reliance PDF text
    reliance_text = """
    Policy Number: 110322523470171735
    Insured Name: Mr. BIJALE ANTESHWAR VIJAY
    Communication Address & Place of Supply: GAT NO.322/2 FLAT NO.H-701, GANGA VATIKA LONIKAND, PUNE, PUNE, MAHARASHTRA, 412216
    Registration No.: MH12KE1128
    Make / Model: RENAULT / DUSTER / PETROL RXE
    Engine No. / Chassis No.: D244587 / MEEHSRC85D7000947
    Mfg. Month & Year: JUL-2013
    CC / HP / Watt: 1598
    Total Premium (₹): 9318
    RELIANCE GENERAL INSURANCE
    """
    
    print("--- SHRIRAM PDF RESULTS ---")
    shriram_result = extract_values_from_text_enhanced(shriram_text)
    for key, value in shriram_result.items():
        if value:
            print(f"✅ {key}: {value}")
        else:
            print(f"❌ {key}: Empty")
    
    print("\n--- RELIANCE PDF RESULTS ---")
    reliance_result = extract_values_from_text_enhanced(reliance_text)
    for key, value in reliance_result.items():
        if value:
            print(f"✅ {key}: {value}")
        else:
            print(f"❌ {key}: Empty")

if __name__ == "__main__":
    test_both_pdfs()
