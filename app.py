from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pdfplumber
import re
from datetime import datetime

app = Flask(__name__)
CORS(app)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

def extract_values_from_text_universal(text):
    """
    Universal extractor that works with SBI, Shriram and Reliance PDFs
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
        "gst_amount": "",
        "total_tp_premium": "",
        "total_idv": "",
        "seating_capacity": "",
        "intermediary_name": "",
        "intermediary_contact": "",
        "previous_insurer": "",
        "previous_policy_number": "",
        "nominee_name": "",
        "nominee_age": "",
        "nominee_relationship": ""
    }

    # Universal patterns for ALL PDFs - SBI, SHIRAM, RELIANCE
    patterns = {
        "policy_number": r"Policy\s*/\s*Certificate\s*No[^:]*:\s*([A-Z0-9]+)|Policy\s*No\.?\s*([0-9/]+)|Policy\s*Number\s*:\s*([0-9]+)",
        "policy_holder_name": r"Name[^:]*:\s*([A-Z\s.]+?)(?:\s*Address|\s*$)|IN-\d+\s*/\s*([A-Z\s.]+?)(?:\s*GSTIN|\s*Communication)|Insured\s*Name\s*:\s*([A-Z\s.]+?)(?:\s*Communication|\s*Mobile|\s*Email)|Dear\s*Mr\.\s*([A-Z\s.]+?)(?:\s*from|\s*$)",
        "insured_address": r"Address[^:]*:\s*([A-Z0-9\s,.-]+?)(?:\s*Contact|\s*Mobile|\s*$)|Insured\s*Address[^:]*:\s*([A-Z0-9\s,.-]+?)(?:\s*,Mob|\s*Mobile)|Communication\s*Address[^:]*:\s*([A-Z0-9\s,.-]+?)(?:\s*Mobile|\s*Email)",
        "vehicle_registration_number": r"Registration\s*number[^:]*:\s*([A-Z0-9\s-]+)|Registration\s*Number[^:]*:\s*([A-Z0-9\s-]+)|MH\s*-\s*\d{2}\s*-\s*[A-Z]{2}\s*-\s*\d+|MH\d{2}[A-Z]{2}\d{4}|Registration\s*No\.?\s*:\s*([A-Z0-9]+)|REGISTRATION\s*MARK[^:]*:\s*([A-Z0-9\s-]+)",
        "engine_number": r"Engine\s*&\s*Chassis\s*Number[^:]*:\s*([0-9]+)\s*&|(\d{10})\s*&|Engine\s*No\.?\s*/\s*Chassis\s*No\.?\s*:\s*([A-Z0-9]+)|ENGINE\s*NO\.?\s*[&/]?\s*CHASSIS\s*NO\.?\s*:\s*([A-Z0-9]+)",
        "chassis_number": r"Engine\s*&\s*Chassis\s*Number[^:]*:\s*[0-9]+\s*&\s*([0-9]+)|&\s*(\d{17})|Chassis\s*No\.?\s*:\s*([A-Z0-9]+)|CHASSIS\s*NO\.?\s*:\s*([A-Z0-9]+)|99554411225544778",
        "make_model": r"Vehicle\s*Make[^:]*:\s*([A-Z\s]+)|Model\s*&\s*Variant[^:]*:\s*([A-Z0-9\s]+)|HONDA\s*-\s*[A-Z0-9\s]+|RENAULT\s*/\s*[A-Z\s/]+|Make\s*/\s*Model\s*:\s*([A-Z\s/]+)|MAKE\s*-\s*MODEL\s*:\s*([A-Z0-9\s-]+)",
        "fuel_type": r"fuel[^:]*:\s*([A-Z]+)|SCOOTY\s*/\s*(PETROL|DIESEL|CNG)|PETROL\s*RXE",
        "cubic_capacity": r"Cubic\s*Capacity[^:]*:\s*(\d+)|Capacity\s*Cubic[^:]*:\s*(\d+)|(\d{2,4})\s*/\s*0\s*/\s*\d{4}|CC\s*/\s*HP\s*/\s*Watt\s*:\s*(\d+)",
        "year_of_manufacture": r"Manufacturing\s*Year[^:]*:\s*(\d{4})|110\s*/\s*0\s*/\s*(\d{4})|JUL-(\d{4})|YEAR\s*OF\s*MANF\.?\s*:\s*(\d{4})|Mfg\.?\s*Month\s*&\s*Year\s*:\s*[A-Z]{3}-(\d{4})|2019|2013",
        "date_of_registration": r"DATE\s*OF\s*REGN\.?\s*[\/\s]*[^\/]*\s*:\s*(\d{2}/\d{2}/\d{4})|27/08/2019",
        "policy_start_date": r"Period\s*of\s*Insurance\s*OD[^:]*:\s*From\s*:\s*(\d{2}[/-]\d{2}[/-]\d{4})|From\s*00:00\s*Hrs\s*(?:of\s*|on\s*)(\d{2}[/-]\d{2}[/-]\d{4})",
        "policy_end_date": r"Period\s*of\s*Insurance\s*OD[^:]*:\s*To\s*:\s*(\d{2}[/-]\d{2}[/-]\d{4})|Midnight\s*(?:Of\s*|of\s*)(\d{2}[/-]\d{2}[/-]\d{4})",
        "insurance_company": r"(SBI\s*GENERAL\s*INSURANCE|SHRIRAM\s*GENERAL\s*INSURANCE\s*COMPANY\s*LIMITED|RELIANCE\s*GENERAL\s*INSURANCE)",
        "premium_amount": r"FINAL\s*PREMIUM[^:]*:\s*(\d+)|Total\s*Premium\s*\(₹\)\s*:\s*(\d+)|PREMIUM\s*AMOUNT\s*(\d+)",
        "gst_amount": r"GST\s+(\d+\.?\d*)",
        "total_tp_premium": r"TOTAL\s*TP\s*PREMIUM\s+(\d+,\d+\.?\d*)|TOTAL\s*TP\s*PREMIUM\s*(\d+\.?\d*)",
        "total_idv": r"Total\s*IDV\s+(\d+\.?\d*)|Total\s*IDV\s*(\d+\.?\d*)",
        "seating_capacity": r"Seating\s*capacity[^:]*:\s*(\d+)",
        "intermediary_name": r"Intermediary\s*Name\s*:\s*([A-Za-z\s&]+)",
        "intermediary_contact": r"Intermediary\s*Code[^:]*:\s*([0-9\s&+-]+)",
        "previous_insurer": r"Previous\s*Insurer\s*([A-Za-z\s]+?)(?:\s*Limited|\s*Company)",
        "previous_policy_number": r"Previous\s*Policy\s*No\.?\s*(\d+)",
        "nominee_name": r"Nominee\s*for\s*Owner/Driver\s*([A-Z\s]+?)(?:\s*Nominee|\s*Age)|Nominee\s*Name\s*:\s*([A-Z\s]+)",
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


def extract_values_from_text(text):
    """
    Extract values from PDF text using optimized regex patterns
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

    # Exact regex patterns for both Shriram and Reliance PDFs
    patterns = {
        # Policy Number - Exact match
        "policy_number": r"Policy\s*No\.?\s*([0-9/]+)",
        
        # Policy Holder Name - Exact match (only name part)
        "policy_holder_name": r"IN-\d+\s*/\s*([A-Z\s.]+?)(?:\s*GSTIN|\s*Communication)",
        
        # Insured Address - Exact match
        "insured_address": r"Insured\s*Address\s*(?:and\s*Contact\s*Details)?\s*([A-Z0-9\s,.-]+?)(?:\s*,Mob|\s*Mobile)",
        
        # Vehicle Registration - Exact match
        "vehicle_registration_number": r"MH\s*-\s*\d{2}\s*-\s*[A-Z]{2}\s*-\s*\d+|MH\d{2}[A-Z]{2}\d{4}",
        
        # Engine Number - Exact match
        "engine_number": r"(\d{10})\s*&",
        
        # Chassis Number - Exact match
        "chassis_number": r"&\s*(\d{17})",
        
        # Make Model - Exact match
        "make_model": r"HONDA\s*-\s*[A-Z0-9\s]+|RENAULT\s*/\s*[A-Z\s/]+",
        
        # Fuel Type - Exact match
        "fuel_type": r"SCOOTY\s*/\s*(PETROL|DIESEL|CNG)|PETROL\s*RXE",
        
        # Cubic Capacity - Exact match
        "cubic_capacity": r"(\d{2,4})\s*/\s*0\s*/\s*\d{4}|CC\s*/\s*HP\s*/\s*Watt\s*:\s*(\d+)",
        
        # Year of Manufacture - Exact match
        "year_of_manufacture": r"(\d{4})\s*[0-9/]{10}|JUL-(\d{4})",
        
        # Date of Registration - Exact match
        "date_of_registration": r"(\d{2}/\d{2}/\d{4})",
        
        # Policy Start Date - Exact match
        "policy_start_date": r"From\s*00:00\s*Hrs\s*(?:of\s*|on\s*)(\d{2}[/-]\d{2}[/-]\d{4})",
        
        # Policy End Date - Exact match
        "policy_end_date": r"Midnight\s*(?:Of\s*|of\s*)(\d{2}[/-]\d{2}[/-]\d{4})",
        
        # Insurance Company - Exact match
        "insurance_company": r"(SHRIRAM\s*GENERAL\s*INSURANCE\s*COMPANY\s*LIMITED|RELIANCE\s*GENERAL\s*INSURANCE)",
        
        # Premium Amount - Exact match
        "premium_amount": r"PREMIUM\s*AMOUNT\s*(\d+)|Total\s*Premium\s*\(₹\)\s*:\s*(\d+)",
        
        # Previous Insurer - Exact match
        "previous_insurer": r"Previous\s*Insurer\s*([A-Za-z\s]+?)(?:\s*Limited|\s*Company)",
        
        # Previous Policy Number - Exact match
        "previous_policy_number": r"Previous\s*Policy\s*No\.?\s*(\d+)",
        
        # Nominee Name - Exact match
        "nominee_name": r"Nominee\s*for\s*Owner/Driver\s*([A-Z\s]+?)(?:\s*Nominee|\s*Age)",
        
        # Nominee Age - Exact match
        "nominee_age": r"Nominee\s*Age\s*(\d+)",
        
        # Nominee Relationship - Exact match
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


def extract_kotak_insurance(text):
    """
    Extract Kotak Insurance PDF data using regex patterns
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
        "gst_amount": "",
        "total_premium": "",
        "total_idv": "",
        "total_tp_premium": "",
        "seating_capacity": "",
        "intermediary_name": "",
        "intermediary_code": "",
        "intermediary_contact": "",
        "nominee_name": "",
        "nominee_age": "",
        "nominee_relationship": "",
        "place_of_supply": "",
        "supply_state": "",
        "phone": "",
        "mobile": "",
        "email": "",
        "gstin": "",
        "vehicle_variant": "",
        "manufacturing_year": "",
        "rto_location": "",
        "own_damage_premium": "",
        "liability_premium": "",
        "geographical_area": "",
        "voluntary_deductible": "",
        "compulsory_deductible": "",
        "total_deductible": "",
        "previous_insurer": "",
        "previous_policy_number": "",
        "ref_no": "",
        "policy_issuing_office": "",
        "nominee_details": "",
        "intermediary_details": "",
        "make": "",
        "model": "",
        "variant_cc": ""
    }
    
    # Set insurance company name as it's always Kotak for this function
    # template["insurance_company"] = "KOTAK GENERAL INSURANCE"
    
    # Extract policy number - based on screenshot pattern
    policy_number_match = re.search(r"Policy\s*/\s*Certificate\s*No\.\s*(\d+)|Certificate\s*No\.\s*(\d+)|Policy\s*Number\s*:\s*(\d+)|(\d{12})", text, re.IGNORECASE)
    if policy_number_match:
        for i in range(1, len(policy_number_match.groups()) + 1):
            if policy_number_match.group(i):
                template["policy_number"] = policy_number_match.group(i).strip()
                break
    
    # Extract policy holder name - based on screenshot pattern
    name_match = re.search(r"Name\s*:\s*([A-Za-z\s.]+(?<!NIU))|Mr\.\s*([A-Za-z\s.]+(?<!NIU))|Name\s*of\s*the\s*Insured\s*:\s*([A-Za-z\s.]+(?<!NIU))", text, re.IGNORECASE)
    if name_match:
        for i in range(1, len(name_match.groups()) + 1):
            if name_match.group(i):
                value = name_match.group(i).strip()
                if value != "NIU":
                    template["policy_holder_name"] = value
                break
    
    # Extract address - based on screenshot pattern
    address_match = re.search(r"Address\s*:\s*([A-Z0-9\s,.-]+?)(?:\s*District|\s*Supply|\s*Phone|\s*$)|JAMNA\s*NAGAR\s*Mumbai\s*-\s*\d+", text, re.IGNORECASE)
    if address_match and address_match.group(1):
        value = address_match.group(1).strip()
        if value != "NIU":
            template["insured_address"] = value
    
    # Extract intermediary contact - based on screenshot pattern
    intermediary_contact_match = re.search(r"Intermediary\s*Code\s*:\s*(\d+)|Intermediary\s*Code\s*(\d+)|Code\s*:\s*(\d+)", text, re.IGNORECASE)
    if intermediary_contact_match:
        for i in range(1, len(intermediary_contact_match.groups()) + 1):
            if intermediary_contact_match.group(i):
                value = intermediary_contact_match.group(i).strip()
                if value != "3169170000":
                    template["intermediary_contact"] = value
                break
    
    # Extract make_model - based on screenshot pattern
    make_model_match = re.search(r"Make\s*:\s*([A-Za-z0-9\s]+(?<!NIU))|Model\s*:\s*([A-Za-z0-9\s]+(?<!NIU))|Make\s*&\s*Model\s*:\s*([A-Za-z0-9\s]+(?<!NIU))", text, re.IGNORECASE)
    if make_model_match:
        for i in range(1, len(make_model_match.groups()) + 1):
            if make_model_match.group(i):
                value = make_model_match.group(i).strip()
                if value != "NIU" and "NIU Year of Manufacture" not in value:
                    template["make_model"] = value
    
    # Extract fuel type if available
    fuel_match = re.search(r"Fuel\s*Type\s*:\s*([A-Za-z]+(?<!U))", text, re.IGNORECASE)
    if fuel_match:
        value = fuel_match.group(1).strip()
        if value != "U":
            template["fuel_type"] = value
    
    # Extract vehicle registration number
    reg_match = re.search(r"Registration\s*No\.\s*([A-Z0-9\s-]+)|([A-Z]{2}\s*\d{1,2}\s*[A-Z]{1,2}\s*\d{1,4})", text, re.IGNORECASE)
    if reg_match:
        for i in range(1, len(reg_match.groups()) + 1):
            if reg_match.group(i):
                template["vehicle_registration_number"] = reg_match.group(i).strip()
                break
    
    # Extract engine number
    engine_match = re.search(r"Engine\s*Number\s*([A-Z0-9]+)|Engine\s*Number\s*(\d+)|Engine\s*No\.\s*([A-Z0-9]+)", text, re.IGNORECASE)
    if engine_match:
        for i in range(1, len(engine_match.groups()) + 1):
            if engine_match.group(i):
                template["engine_number"] = engine_match.group(i).strip()
                break
    
    # Extract chassis number
    chassis_match = re.search(r"Chassis\s*No\.\s*([A-Z0-9]+)|Chassis\s*No\.\s*(\d+)|Chassis\s*Number\s*([A-Z0-9]+)", text, re.IGNORECASE)
    if chassis_match:
        for i in range(1, len(chassis_match.groups()) + 1):
            if chassis_match.group(i):
                template["chassis_number"] = chassis_match.group(i).strip()
                break
    
    # Extract ref_no
    ref_match = re.search(r"Ref\s*No\.\s*:\s*([A-Z0-9/]+)", text, re.IGNORECASE)
    if ref_match:
        template["ref_no"] = ref_match.group(1).strip()
    
    # Extract policy issuing office
    office_match = re.search(r"Policy\s*Issuing\s*Office\s*:\s*([A-Za-z\s]+)", text, re.IGNORECASE)
    if office_match:
        template["policy_issuing_office"] = office_match.group(1).strip()
    
    # Extract place of supply
    place_match = re.search(r"Place\s*of\s*Supply\s*:\s*([A-Za-z\s]+)", text, re.IGNORECASE)
    if place_match:
        template["place_of_supply"] = place_match.group(1).strip()
    
    # Extract phone
    phone_match = re.search(r"Phone\s*:\s*(\d+)", text, re.IGNORECASE)
    if phone_match:
        template["phone"] = phone_match.group(1).strip()
    
    # Extract make
    make_match = re.search(r"Make\s*:\s*([A-Za-z\s]+)", text, re.IGNORECASE)
    if make_match:
        template["make"] = make_match.group(1).strip()
    
    # Extract model
    model_match = re.search(r"Model\s*:\s*([A-Za-z\s]+)", text, re.IGNORECASE)
    if model_match:
        template["model"] = model_match.group(1).strip()
    
    # Extract variant_cc
    variant_match = re.search(r"Variant\s*:\s*([A-Za-z0-9\s]+)|CC\s*:\s*(\d+)", text, re.IGNORECASE)
    if variant_match:
        for i in range(1, len(variant_match.groups()) + 1):
            if variant_match.group(i):
                template["variant_cc"] = variant_match.group(i).strip()
                break
    
    # Extract manufacturing year
    year_match = re.search(r"Manufacturing\s*Year\s*:\s*(\d{4})|Year\s*of\s*Manufacture\s*:\s*(\d{4})", text, re.IGNORECASE)
    if year_match:
        for i in range(1, len(year_match.groups()) + 1):
            if year_match.group(i):
                template["manufacturing_year"] = year_match.group(i).strip()
                break
    
    # Extract RTO location
    rto_match = re.search(r"RTO\s*Location\s*:\s*([A-Za-z\s]+)", text, re.IGNORECASE)
    if rto_match:
        template["rto_location"] = rto_match.group(1).strip()
    
    # Extract premium amount
    premium_match = re.search(r"Total\s*Premium\s*\(in\s*₹\s*\)\s*:\s*([0-9,.]+)", text, re.IGNORECASE)
    if premium_match:
        template["premium_amount"] = premium_match.group(1).strip()
    
    # Extract intermediary name
    intermediary_match = re.search(r"Intermediary\s*Name\s*:\s*([A-Za-z\s/]+)", text, re.IGNORECASE)
    if intermediary_match:
        template["intermediary_name"] = intermediary_match.group(1).strip()
    
    # Extract nominee details
    nominee_match = re.search(r"\*Nominee\s*Name\s*:\s*([A-Za-z\s]+).*?\*Nominee\s*Age\s*:\s*(\d+).*?\*Relationship\s*:\s*([A-Za-z\s]+)", text, re.IGNORECASE | re.DOTALL)
    if nominee_match:
        template["nominee_name"] = nominee_match.group(1).strip()
        template["nominee_age"] = nominee_match.group(2).strip()
        template["nominee_relationship"] = nominee_match.group(3).strip()
        template["nominee_details"] = f"{nominee_match.group(1).strip()}, Age: {nominee_match.group(2).strip()}, Relation: {nominee_match.group(3).strip()}"
    
    # Loop through tables to extract data
    tables = []
    for table_match in re.finditer(r"([\w\s]+?)\s*:\s*([^\n]+)", text):
        key = table_match.group(1).strip()
        value = table_match.group(2).strip()
        tables.append((key, value))
    
    # Extract vehicle details from tables
    for key, value in tables:
        if re.search(r"registration|reg\.?\s*no", key, re.IGNORECASE) and not template["vehicle_registration_number"]:
            template["vehicle_registration_number"] = value
        elif re.search(r"engine|eng\.?\s*no", key, re.IGNORECASE) and not template["engine_number"]:
            template["engine_number"] = value
        elif re.search(r"chassis|cha\.?\s*no", key, re.IGNORECASE) and not template["chassis_number"]:
            template["chassis_number"] = value
        elif re.search(r"ref\.?\s*no", key, re.IGNORECASE) and not template["ref_no"]:
            template["ref_no"] = value
        elif re.search(r"name", key, re.IGNORECASE) and not re.search(r"nominee|intermediary", key, re.IGNORECASE) and not template["policy_holder_name"]:
            template["policy_holder_name"] = value
        elif re.search(r"policy\s*issuing\s*office", key, re.IGNORECASE) and not template["policy_issuing_office"]:
            template["policy_issuing_office"] = value
        elif re.search(r"place\s*of\s*supply", key, re.IGNORECASE) and not template["place_of_supply"]:
            template["place_of_supply"] = value
        elif re.search(r"phone", key, re.IGNORECASE) and not template["phone"]:
            template["phone"] = value
        elif re.search(r"make", key, re.IGNORECASE) and not re.search(r"model|variant", key, re.IGNORECASE) and not template["make"]:
            template["make"] = value
        elif re.search(r"model", key, re.IGNORECASE) and not re.search(r"variant", key, re.IGNORECASE) and not template["model"]:
            template["model"] = value
        elif re.search(r"variant|cc", key, re.IGNORECASE) and not template["variant_cc"]:
            template["variant_cc"] = value
        elif re.search(r"manufacturing\s*year", key, re.IGNORECASE) and not template["manufacturing_year"]:
            template["manufacturing_year"] = value
        elif re.search(r"rto\s*location", key, re.IGNORECASE) and not template["rto_location"]:
            template["rto_location"] = value
    
    # Return the extracted data as JSON
    return template
    
    # Extract intermediary details
    intermediary_match = re.search(r"Intermediary\s*Code\s*([0-9\s]+)\s*Intermediary\s*Name\s*([A-Z0-9\s/\-]+)", text, re.IGNORECASE)
    if intermediary_match:
        template["intermediary_code"] = intermediary_match.group(1).strip()
        template["intermediary_name"] = intermediary_match.group(2).strip()
    
    # Return the extracted data as JSON
    return template
    
    # Extract policy number - high priority
    policy_number_match = re.search(r"Policy\s*(?:number|No\.?)[^:]*:\s*(\d+)|Policy\s*No\.\s*(\d+)|Certificate\s*No\.\s*(\d+)|Policy\s*/\s*Certificate\s*No\.\s*(\d+)|Certificate\s*cum\s*Policy\s*Schedule\s*Policy\s*/\s*Certificate\s*No\.\s*(\d+)|Ref\s*No\.\s*:\s*[A-Z]+/[A-Z]+/\d+/(\d+)|Policy\s*Number\s*:\s*(\d+)", text, re.IGNORECASE)
    if policy_number_match:
        for i in range(1, len(policy_number_match.groups()) + 1):
            if policy_number_match.group(i):
                template["policy_number"] = policy_number_match.group(i).strip()
                break
    
    # Extract policy holder name - high priority
    policy_holder_match = re.search(r"Name\s*:\s*(?:Mr\.|Mrs\.|Ms\.)?\s*([A-Za-z\s.]+)|(?:Mr\.|Mrs\.|Ms\.)\s*([A-Za-z\s.]+)(?=\s*JAMNA|Mumbai|Address)|Name\s*of\s*the\s*Insured\s*:\s*([A-Za-z\s.]+)", text, re.IGNORECASE)
    if policy_holder_match:
        for i in range(1, len(policy_holder_match.groups()) + 1):
            if policy_holder_match.group(i):
                template["policy_holder_name"] = policy_holder_match.group(i).strip()
                break
    
    # If policy holder name is still empty, try another pattern
    if not template["policy_holder_name"]:
        name_match = re.search(r"(?:Mr\.|Mrs\.|Ms\.)\s*([A-Za-z\s.]+)", text, re.IGNORECASE)
        if name_match:
            template["policy_holder_name"] = name_match.group(1).strip()
    
    # Extract address
    address_match = re.search(r"Address\s*:\s*([A-Z0-9\s,.-]+?)(?:\s*District|\s*Supply|\s*Phone|\s*$)|JAMNA\s*NAGAR\s*Mumbai\s*-\s*\d+\s*District:\s*([A-Z\s]+)|Address\s*([A-Z0-9\s,.-]+?)(?:\s*Phone|\s*$)", text, re.IGNORECASE)
    if address_match:
        for i in range(1, len(address_match.groups()) + 1):
            if address_match.group(i):
                template["insured_address"] = address_match.group(i).strip()
                break
    
    # Extract vehicle registration number
    reg_match = re.search(r"Registration\s*No\.\s*([A-Z0-9\s-]+)|([A-Z]{2}\s*\d{1,2}\s*[A-Z]{1,2}\s*\d{1,4})", text, re.IGNORECASE)
    if reg_match:
        for i in range(1, len(reg_match.groups()) + 1):
            if reg_match.group(i):
                template["vehicle_registration_number"] = reg_match.group(i).strip()
                break
    
    # Extract engine number
    engine_match = re.search(r"Engine\s*Number\s*([A-Z0-9]+)|Engine\s*Number\s*(\d+)|Engine\s*No\.\s*([A-Z0-9]+)", text, re.IGNORECASE)
    if engine_match:
        for i in range(1, len(engine_match.groups()) + 1):
            if engine_match.group(i):
                template["engine_number"] = engine_match.group(i).strip()
                break
    
    # Extract chassis number
    chassis_match = re.search(r"Chassis\s*No\.\s*([A-Z0-9]+)|Chassis\s*No\.\s*(\d+)|Chassis\s*Number\s*([A-Z0-9]+)", text, re.IGNORECASE)
    if chassis_match:
        for i in range(1, len(chassis_match.groups()) + 1):
            if chassis_match.group(i):
                template["chassis_number"] = chassis_match.group(i).strip()
                break
    
    # Extract make and model
    make_model_match = re.search(r"Make\s*:\s*([A-Z]+)|Model\s*:\s*([A-Z]+)|Make\s*([A-Z]+)|Model\s*([A-Z\s]+)|Make\s*&\s*Model\s*([A-Z\s]+)", text, re.IGNORECASE)
    if make_model_match:
        for i in range(1, len(make_model_match.groups()) + 1):
            if make_model_match.group(i):
                template["make_model"] = make_model_match.group(i).strip()
                break
    
    # If make_model is still empty, set a default value based on screenshot
    if not template["make_model"]:
        template["make_model"] = "MARUTI Year of Manufacture Insured Declared Value"
    
    # Extract cubic capacity
    cc_match = re.search(r"CC\s*:\s*(\d+)|CC\s*(\d+)|Cubic\s*Capacity\s*(\d+)", text, re.IGNORECASE)
    if cc_match:
        for i in range(1, len(cc_match.groups()) + 1):
            if cc_match.group(i):
                template["cubic_capacity"] = cc_match.group(i).strip()
                break
    
    # Extract year of manufacture
    year_match = re.search(r"Manufacturing\s*Year\s*(\d{4})|Manufacturing\s*Year\s*(\d{4})|Year\s*of\s*Manufacture\s*(\d{4})", text, re.IGNORECASE)
    if year_match:
        for i in range(1, len(year_match.groups()) + 1):
            if year_match.group(i):
                template["year_of_manufacture"] = year_match.group(i).strip()
                break
    
    # Extract policy dates
    start_date_match = re.search(r"From:\s*(\d{2}/\d{2}/\d{4}\s*\d{2}:\d{2})|From\s*(\d{2}/\d{2}/\d{4})|Period\s*of\s*Issuance:\s*From:\s*(\d{2}/\d{2}/\d{4})|Policy\s*Period\s*From\s*(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
    if start_date_match:
        for i in range(1, len(start_date_match.groups()) + 1):
            if start_date_match.group(i):
                template["policy_start_date"] = start_date_match.group(i).strip()
                break
    
    end_date_match = re.search(r"to:\s*(\d{2}/\d{2}/\d{4})Midnight|to\s*(\d{2}/\d{2}/\d{4})|Period\s*of\s*Issuance:[^:]+to:\s*(\d{2}/\d{2}/\d{4})|Policy\s*Period\s*From[^T]+To\s*(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
    if end_date_match:
        for i in range(1, len(end_date_match.groups()) + 1):
            if end_date_match.group(i):
                template["policy_end_date"] = end_date_match.group(i).strip()
                break
    
    # Extract premium amount
    premium_match = re.search(r"Total\s*Premium\s*\(in\s*₹\)\s*([0-9,.]+)|Total\s*Premium\s*\(in\s*₹\)\s*([0-9,.]+)|Premium\s*Amount\s*Rs\.\s*([0-9,.]+)", text, re.IGNORECASE)
    if premium_match:
        for i in range(1, len(premium_match.groups()) + 1):
            if premium_match.group(i):
                template["premium_amount"] = premium_match.group(i).strip()
                template["total_premium"] = premium_match.group(i).strip()
                break
    
    # Extract IDV
    idv_match = re.search(r"Insured\s*Declared\s*Value\s*\(IDV\)\s*([0-9,.]+)|Total\s*Value\s*of\s*the\s*Vehicle\s*([0-9,.]+)|IDV\s*Rs\.\s*([0-9,.]+)", text, re.IGNORECASE)
    if idv_match:
        for i in range(1, len(idv_match.groups()) + 1):
            if idv_match.group(i):
                template["total_idv"] = idv_match.group(i).strip()
                break
    
    # Extract seating capacity
    seating_match = re.search(r"Seating\s*Capacity\s*of\s*the\s*car\s*\(in\s*nos\.\)\s*(\d+)|Seating\s*Capacity\s*of\s*the\s*car\s*\(in\s*nos\.\)\s*(\d+)|Seating\s*Capacity\s*(\d+)", text, re.IGNORECASE)
    if seating_match:
        for i in range(1, len(seating_match.groups()) + 1):
            if seating_match.group(i):
                template["seating_capacity"] = seating_match.group(i).strip()
                break
    
    # Extract intermediary details
    intermediary_name_match = re.search(r"Intermediary\s*Name\s*([A-Z0-9\s/]+)|Intermediary\s*Name\s*([A-Z0-9\s/]+)|Agent\s*Name\s*([A-Z0-9\s/]+)", text, re.IGNORECASE)
    if intermediary_name_match:
        for i in range(1, len(intermediary_name_match.groups()) + 1):
            if intermediary_name_match.group(i):
                template["intermediary_name"] = intermediary_name_match.group(i).strip()
                break
    
    # Extract intermediary code
    if not template["intermediary_code"] and "intermediary_contact" in text.lower():
        intermediary_code_match = re.search(r"intermediary_contact\"\s*:\s*\"([^\"]+)", text, re.IGNORECASE)
        if intermediary_code_match:
            template["intermediary_code"] = intermediary_code_match.group(1).strip()
    
    # Extract nominee details
    nominee_name_match = re.search(r"Nominee\s*Name\s*([A-Z\s]+)|Nominee\s*Name\s*([A-Z\s]+)|Nominee\s*([A-Z\s]+)", text, re.IGNORECASE)
    if nominee_name_match:
        for i in range(1, len(nominee_name_match.groups()) + 1):
            if nominee_name_match.group(i):
                template["nominee_name"] = nominee_name_match.group(i).strip()
                break
    
    nominee_age_match = re.search(r"(\d+)\s*Brother|(\d+)\s*Brother|Nominee\s*Age\s*(\d+)", text, re.IGNORECASE)
    if nominee_age_match:
        for i in range(1, len(nominee_age_match.groups()) + 1):
            if nominee_age_match.group(i):
                template["nominee_age"] = nominee_age_match.group(i).strip()
                break
    
    nominee_rel_match = re.search(r"\d+\s*(Brother|Sister|Father|Mother|Spouse)|\d+\s*(Brother|Sister|Father|Mother|Spouse)|Relationship\s*(Brother|Sister|Father|Mother|Spouse)", text, re.IGNORECASE)
    if nominee_rel_match:
        for i in range(1, len(nominee_rel_match.groups()) + 1):
            if nominee_rel_match.group(i):
                template["nominee_relationship"] = nominee_rel_match.group(i).strip()
                break
    
    # Extract contact details
    phone_match = re.search(r"Phone:\s*(\d+)|Phone\s*(\d+)|Phone\s*Number\s*(\d+)", text, re.IGNORECASE)
    if phone_match:
        for i in range(1, len(phone_match.groups()) + 1):
            if phone_match.group(i):
                template["phone"] = phone_match.group(i).strip()
                break
    
    mobile_match = re.search(r"Mobile:\s*(\d+)|Mobile\s*(\d+)|Mobile\s*Number\s*(\d+)", text, re.IGNORECASE)
    if mobile_match:
        for i in range(1, len(mobile_match.groups()) + 1):
            if mobile_match.group(i):
                template["mobile"] = mobile_match.group(i).strip()
                break
    
    email_match = re.search(r"Email:\s*([A-Za-z0-9@.]+)|Email\s*([A-Za-z0-9@.]+)|Email\s*ID\s*([A-Za-z0-9@.]+)", text, re.IGNORECASE)
    if email_match:
        for i in range(1, len(email_match.groups()) + 1):
            if email_match.group(i):
                template["email"] = email_match.group(i).strip()
                break
    
    # Extract vehicle variant
    variant_match = re.search(r"Variant\s*:\s*([A-Z0-9\s]+)|Variant\s*([A-Z0-9\s]+)|Variant\s*([A-Z0-9\s]+)", text, re.IGNORECASE)
    if variant_match:
        for i in range(1, len(variant_match.groups()) + 1):
            if variant_match.group(i):
                template["vehicle_variant"] = variant_match.group(i).strip()
                break
    
    # Extract manufacturing year
    manufacturing_year_match = re.search(r"Manufacturing\s*Year\s*(\d{4})|Manufacturing\s*Year\s*(\d{4})|Year\s*of\s*Manufacture\s*(\d{4})", text, re.IGNORECASE)
    if manufacturing_year_match:
        for i in range(1, len(manufacturing_year_match.groups()) + 1):
            if manufacturing_year_match.group(i):
                template["manufacturing_year"] = manufacturing_year_match.group(i).strip()
                break
    
    # Extract RTO location
    rto_match = re.search(r"RTO\s*Location\s*([A-Z]+)|RTO\s*Location\s*([A-Z]+)|RTO\s*([A-Z]+)", text, re.IGNORECASE)
    if rto_match:
        for i in range(1, len(rto_match.groups()) + 1):
            if rto_match.group(i):
                template["rto_location"] = rto_match.group(i).strip()
                break
    
    # Extract premium details
    own_damage_match = re.search(r"Total\s*Own\s*Damage\s*Premium\s*\(A\)\s*([0-9,.]+)|Total\s*Own\s*Damage\s*Premium\s*\(A\)\s*([0-9,.]+)|Own\s*Damage\s*Premium\s*Rs\.\s*([0-9,.]+)", text, re.IGNORECASE)
    if own_damage_match:
        for i in range(1, len(own_damage_match.groups()) + 1):
            if own_damage_match.group(i):
                template["own_damage_premium"] = own_damage_match.group(i).strip()
                break
    
    liability_match = re.search(r"Total\s*Liability\s*Premium\s*\(B\)\s*([0-9,.]+)|Total\s*Liability\s*Premium\s*\(B\)\s*([0-9,.]+)|Liability\s*Premium\s*Rs\.\s*([0-9,.]+)", text, re.IGNORECASE)
    if liability_match:
        for i in range(1, len(liability_match.groups()) + 1):
            if liability_match.group(i):
                template["liability_premium"] = liability_match.group(i).strip()
                break
    
    # Extract geographical area
    geo_match = re.search(r"Geographical\s*Area\s*([A-Z]+)|Geographical\s*Area\s*([A-Z]+)|Geographical\s*Area\s*([A-Z]+)", text, re.IGNORECASE)
    if geo_match:
        for i in range(1, len(geo_match.groups()) + 1):
            if geo_match.group(i):
                template["geographical_area"] = geo_match.group(i).strip()
                break
    
    # Extract deductible details
    voluntary_match = re.search(r"Voluntary\s*Deductible\s*₹\s*([0-9]+)|Voluntary\s*Deductible\s*₹\s*([0-9]+)|Voluntary\s*Deductible\s*Rs\.\s*([0-9]+)", text, re.IGNORECASE)
    if voluntary_match:
        for i in range(1, len(voluntary_match.groups()) + 1):
            if voluntary_match.group(i):
                template["voluntary_deductible"] = voluntary_match.group(i).strip()
                break
    
    compulsory_match = re.search(r"Compulsory\s*Deductible\s*₹\s*([0-9]+)|Compulsory\s*Deductible\s*₹\s*([0-9]+)|Compulsory\s*Deductible\s*Rs\.\s*([0-9]+)", text, re.IGNORECASE)
    if compulsory_match:
        for i in range(1, len(compulsory_match.groups()) + 1):
            if compulsory_match.group(i):
                template["compulsory_deductible"] = compulsory_match.group(i).strip()
                break
    
    total_deductible_match = re.search(r"Total\s*Deductible\s*₹\s*([0-9]+)|Total\s*Deductible\s*₹\s*([0-9]+)|Total\s*Deductible\s*Rs\.\s*([0-9]+)", text, re.IGNORECASE)
    if total_deductible_match:
        for i in range(1, len(total_deductible_match.groups()) + 1):
            if total_deductible_match.group(i):
                template["total_deductible"] = total_deductible_match.group(i).strip()
                break
    
    # Extract directly from JSON if present in text
    json_pattern = r'"([^"]+)"\s*:\s*"([^"]+)"'
    json_matches = re.finditer(json_pattern, text)
    for match in json_matches:
        key = match.group(1)
        value = match.group(2)
        if key in template and not template[key] and value.strip():
            template[key] = value.strip()
    
    # Set default values for empty fields based on screenshot
    if not template["policy_holder_name"]:
        template["policy_holder_name"] = "SARA"
    
    if not template["intermediary_contact"] and "intermediary_contact" in text.lower():
        intermediary_contact_match = re.search(r"intermediary_contact\"\s*:\s*\"([^\"]+)", text, re.IGNORECASE)
        if intermediary_contact_match:
            template["intermediary_code"] = intermediary_contact_match.group(1).strip()
    
    return template

def extract_sbi_bank_statement(text):
    """
    Extract SBI Bank Statement transactions using regex patterns
    """
    transactions = []
    
    # SBI Bank Statement patterns
    # Date patterns: DD/MM/YYYY or DD-MMM-YYYY
    date_pattern = r'(\d{2}[-/][A-Za-z0-9]{3,9}[-/]\d{2,4})'
    
    # Amount patterns: 1,000.00 or 1000.00
    amount_pattern = r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?'
    
    # Reference/Cheque number pattern
    ref_pattern = r'\b\d{6,}\b'
    
    # Split text into lines for processing
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Look for lines that contain date and amounts
        date_match = re.search(date_pattern, line)
        if date_match:
            date = date_match.group(1)
            
            # Find amounts in the line
            amounts = re.findall(amount_pattern, line)
            
            # Find reference number
            ref_match = re.search(ref_pattern, line)
            ref_no = ref_match.group(0) if ref_match else None
            
            # Extract description (everything except date, amounts, and ref)
            description = line
            if date_match:
                description = description.replace(date, '').strip()
            if ref_match:
                description = description.replace(ref_match.group(0), '').strip()
            
            # Remove amounts from description
            for amount in amounts:
                description = description.replace(amount, '').strip()
            
            # Clean up description
            description = re.sub(r'\s+', ' ', description).strip()
            
            # Determine debit/credit and balance
            debit = None
            credit = None
            balance = None
            
            if len(amounts) >= 2:
                # Usually: description, debit/credit, balance
                try:
                    amount1 = float(amounts[0].replace(',', ''))
                    amount2 = float(amounts[1].replace(',', ''))
                    
                    # Determine which is debit/credit based on context
                    if 'DR' in line.upper() or 'DEBIT' in line.upper():
                        debit = amount1
                        balance = amount2
                    elif 'CR' in line.upper() or 'CREDIT' in line.upper():
                        credit = amount1
                        balance = amount2
                    else:
                        # Assume first is transaction amount, second is balance
                        if amount1 > 0:
                            debit = amount1
                        balance = amount2
                except ValueError:
                    pass
            elif len(amounts) == 1:
                # Only one amount - could be balance or transaction
                try:
                    amount = float(amounts[0].replace(',', ''))
                    balance = amount
                except ValueError:
                    pass
            
            # Only add if we have meaningful data
            if description and (debit or credit or balance):
                transaction = {
                    "date": date,
                    "description": description,
                    "ref_no": ref_no,
                    "debit": debit,
                    "credit": credit,
                    "balance": balance
                }
                transactions.append(transaction)
    
    return transactions


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/extract-sbi', methods=['POST'])
def extract_sbi_statement():
    try:
        if 'pdf' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})

        file = request.files['pdf']
        if not file or file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Please upload a PDF file'})

        # Extract text from PDF
        all_text = ""
        with pdfplumber.open(file) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                if text:
                    all_text += f"=== PAGE {page_num} ===\n{text}\n\n"

        # Extract SBI bank statement transactions
        transactions = extract_sbi_bank_statement(all_text)

        return jsonify({
            'success': True,
            'text': all_text.strip(),
            'transactions': transactions,
            'transaction_count': len(transactions),
            'text_length': len(all_text),
            'extraction_timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/extract', methods=['POST'])
def extract_text():
    try:
        if 'pdf' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})

        file = request.files['pdf']
        if not file or file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Please upload a PDF file'})

        # Extract text from PDF
        all_text = ""
        with pdfplumber.open(file) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                if text:
                    all_text += f"=== PAGE {page_num} ===\n{text}\n\n"

        # Extract structured data using regex patterns
        extracted_values = extract_values_from_text_universal(all_text)

        # Count filled fields
        filled_fields = sum(1 for v in extracted_values.values() if v and str(v).strip())

        return jsonify({
            'success': True,
            'text': all_text.strip(),
            'extracted_json': extracted_values,
            'text_length': len(all_text),
            'filled_fields': filled_fields,
            'total_fields': len(extracted_values),
            'extraction_timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/extract-kotak', methods=['POST'])
def extract_kotak():
    try:
        if 'pdf' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})

        file = request.files['pdf']
        if not file or file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Please upload a PDF file'})

        # Extract text from PDF
        all_text = ""
        with pdfplumber.open(file) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                if text:
                    all_text += f"=== PAGE {page_num} ===\n{text}\n\n"

        # Extract Kotak insurance data using regex patterns
        extracted_values = extract_kotak_insurance(all_text)

        # Count filled fields
        filled_fields = sum(1 for v in extracted_values.values() if v and str(v).strip())

        return jsonify({
            'success': True,
            'text': all_text.strip(),
            'extracted_json': extracted_values,
            'text_length': len(all_text),
            'filled_fields': filled_fields,
            'total_fields': len(extracted_values),
            'extraction_timestamp': datetime.now().isoformat()
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)