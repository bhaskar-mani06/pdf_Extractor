import re

def test_reliance_patterns():
    """
    Test patterns specifically for Reliance PDF
    """
    
    # Sample Reliance PDF text (from your previous examples)
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
    
    # Current patterns from your app.py
    patterns = {
        "policy_number": r"Policy\s*No\.?\s*([0-9/]+)",
        "policy_holder_name": r"IN-\d+\s*/\s*([A-Z\s.]+?)(?:\s*GSTIN|\s*Communication)",
        "insured_address": r"Insured\s*Address\s*(?:and\s*Contact\s*Details)?\s*([A-Z0-9\s,.-]+?)(?:\s*,Mob|\s*Mobile)",
        "vehicle_registration_number": r"MH\s*-\s*\d{2}\s*-\s*[A-Z]{2}\s*-\s*\d+|MH\d{2}[A-Z]{2}\d{4}",
        "engine_number": r"(\d{10})\s*&",
        "chassis_number": r"&\s*(\d{17})",
        "make_model": r"HONDA\s*-\s*[A-Z0-9\s]+|RENAULT\s*/\s*[A-Z\s/]+",
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
    
    print("=== TESTING RELIANCE PDF PATTERNS ===\n")
    
    for key, pattern in patterns.items():
        match = re.search(pattern, reliance_text, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        if match:
            # Handle multiple groups
            extracted_value = ""
            for i in range(1, len(match.groups()) + 1):
                if match.group(i) and match.group(i).strip():
                    extracted_value = match.group(i).strip()
                    break
            
            if extracted_value:
                print(f"✅ {key}: {extracted_value}")
            else:
                print(f"❌ {key}: No valid group found")
        else:
            print(f"❌ {key}: No match found")
    
    print("\n=== SUGGESTIONS FOR RELIANCE PDF ===")
    print("1. Add 'Policy Number:' pattern for Reliance")
    print("2. Add 'Insured Name:' pattern for Reliance") 
    print("3. Add 'Communication Address' pattern for Reliance")
    print("4. Add 'Registration No.:' pattern for Reliance")
    print("5. Add 'Make / Model:' pattern for Reliance")
    print("6. Add 'Engine No. / Chassis No.:' pattern for Reliance")
    print("7. Add 'Mfg. Month & Year:' pattern for Reliance")
    print("8. Add 'CC / HP / Watt:' pattern for Reliance")
    print("9. Add 'Total Premium (₹):' pattern for Reliance")

if __name__ == "__main__":
    test_reliance_patterns()
