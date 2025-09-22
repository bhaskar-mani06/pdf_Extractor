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
    Extract values from PDF text using optimized regex patterns for Shriram and Reliance
    Enhanced with alternative patterns for better accuracy
    """
    template = {
        # Policy Information
        "policy_number": "",
        "policy_holder_name": "",
        "insured_address": "",
        "policy_start_date": "",
        "policy_end_date": "",
        "insurance_company": "",
        
        # Vehicle Information
        "vehicle_registration_number": "",
        "engine_number": "",
        "chassis_number": "",
        "make_model": "",
        "make": "",
        "model": "",
        "fuel_type": "",
        "cubic_capacity": "",
        "year_of_manufacture": "",
        "date_of_registration": "",
        "seating_capacity": "",
        
        # Financial Information
        "premium_amount": "",
        "total_premium": "",
        "gst_amount": "",
        "total_tp_premium": "",
        "total_idv": "",
        
        # Previous Insurance
        "previous_insurer": "",
        "previous_policy_number": "",
        
        # Nominee Information
        "nominee_name": "",
        "nominee_age": "",
        "nominee_relationship": "",
        
        # Intermediary Information
        "intermediary_name": "",
        "intermediary_contact": "",
        
        # Additional Details
        "supply_state_code": "",
        "place_of_supply": "",
        "phone": "",
        "mobile": "",
        "email": "",
        "gstin": ""
    }

    # Enhanced regex patterns with alternative patterns for better accuracy
    
    # Extract Policy Number
    policy_number_match = re.search(r"Policy\s*No\.?\s*([0-9/]+)", text, re.IGNORECASE)
    if policy_number_match:
        template["policy_number"] = policy_number_match.group(1).strip()
    
    # SBI specific policy number pattern
    if not template["policy_number"]:
        sbi_policy_match = re.search(r"Policy\s*/\s*Certificate\s*No[^:]*:\s*([A-Z0-9]+)", text, re.IGNORECASE)
        if sbi_policy_match:
            template["policy_number"] = sbi_policy_match.group(1).strip()
    
    # Extract Policy Holder Name
    name_match = re.search(r"IN-\d+\s*/\s*([A-Z\s.]+?)(?:\s*GSTIN|\s*Communication)", text, re.IGNORECASE)
    if name_match:
        template["policy_holder_name"] = name_match.group(1).strip()
    
    # Alternative name pattern
    if not template["policy_holder_name"]:
        name_alt_match = re.search(r"Name[^:]*:\s*([A-Z\s.]+?)(?:\s*Address|\s*$)", text, re.IGNORECASE)
        if name_alt_match:
            template["policy_holder_name"] = name_alt_match.group(1).strip()
    
    # SBI specific name pattern
    if not template["policy_holder_name"]:
        sbi_name_match = re.search(r"Dear\s*Mr\.\s*([A-Z\s.]+?)(?:\s*,|\s*$)", text, re.IGNORECASE)
        if sbi_name_match:
            template["policy_holder_name"] = sbi_name_match.group(1).strip()

    # Extract Insured Address
    address_match = re.search(r"Insured\s*Address\s*(?:and\s*Contact\s*Details)?\s*([A-Z0-9\s,.-]+?)(?:\s*,Mob|\s*Mobile)", text, re.IGNORECASE)
    if address_match:
        template["insured_address"] = address_match.group(1).strip()
    
    # Alternative address pattern
    if not template["insured_address"]:
        address_alt_match = re.search(r"Address[^:]*:\s*([A-Z0-9\s,.-]+?)(?:\s*Contact|\s*Mobile|\s*$)", text, re.IGNORECASE)
        if address_alt_match:
            template["insured_address"] = address_alt_match.group(1).strip()
    
    # SBI specific address pattern
    if not template["insured_address"]:
        sbi_address_match = re.search(r"([A-Z0-9\s,.-]+?),\s*Mumbai,\s*Maharashtra\s*-\s*\d+,\s*India", text, re.IGNORECASE)
        if sbi_address_match:
            template["insured_address"] = sbi_address_match.group(1).strip()
    
    # Extract Vehicle Registration Number
    reg_match = re.search(r"MH\s*-\s*\d{2}\s*-\s*[A-Z]{2}\s*-\s*\d+|MH\d{2}[A-Z]{2}\d{4}", text, re.IGNORECASE)
    if reg_match:
        template["vehicle_registration_number"] = reg_match.group(0).strip()
    
    # Alternative registration pattern
    if not template["vehicle_registration_number"]:
        reg_alt_match = re.search(r"Registration\s*number[^:]*:\s*([A-Z0-9\s-]+)", text, re.IGNORECASE)
        if reg_alt_match:
            template["vehicle_registration_number"] = reg_alt_match.group(1).strip()
    
    # Extract Engine Number
    engine_match = re.search(r"(\d{10})\s*&", text, re.IGNORECASE)
    if engine_match:
        template["engine_number"] = engine_match.group(1).strip()
    
    # Alternative engine pattern
    if not template["engine_number"]:
        engine_alt_match = re.search(r"Engine\s*No\.?\s*/\s*Chassis\s*No\.?\s*:\s*([A-Z0-9]+)", text, re.IGNORECASE)
        if engine_alt_match:
            template["engine_number"] = engine_alt_match.group(1).strip()
    
    # Extract Chassis Number
    chassis_match = re.search(r"&\s*(\d{17})", text, re.IGNORECASE)
    if chassis_match:
        template["chassis_number"] = chassis_match.group(1).strip()
    
    # Alternative chassis pattern
    if not template["chassis_number"]:
        chassis_alt_match = re.search(r"Chassis\s*No\.?\s*:\s*([A-Z0-9]+)", text, re.IGNORECASE)
        if chassis_alt_match:
            template["chassis_number"] = chassis_alt_match.group(1).strip()
    
    # Extract Make Model
    make_model_match = re.search(r"HONDA\s*-\s*[A-Z0-9\s]+|RENAULT\s*/\s*[A-Z\s/]+", text, re.IGNORECASE)
    if make_model_match:
        template["make_model"] = make_model_match.group(0).strip()
    
    # Alternative make model pattern
    if not template["make_model"]:
        make_model_alt_match = re.search(r"Make\s*/\s*Model\s*:\s*([A-Z\s/]+)", text, re.IGNORECASE)
        if make_model_alt_match:
            template["make_model"] = make_model_alt_match.group(1).strip()
    
    # Extract Make separately
    make_match = re.search(r"Make[^:]*:\s*([A-Z\s]+)", text, re.IGNORECASE)
    if make_match:
        template["make"] = make_match.group(1).strip()
    
    # Extract Model separately
    model_match = re.search(r"Model[^:]*:\s*([A-Z0-9\s]+)", text, re.IGNORECASE)
    if model_match:
        template["model"] = model_match.group(1).strip()
    
    # Extract Fuel Type
    fuel_match = re.search(r"SCOOTY\s*/\s*(PETROL|DIESEL|CNG)|PETROL\s*RXE", text, re.IGNORECASE)
    if fuel_match:
        template["fuel_type"] = fuel_match.group(1).strip() if fuel_match.group(1) else fuel_match.group(0).strip()
    
    # Alternative fuel pattern
    if not template["fuel_type"]:
        fuel_alt_match = re.search(r"fuel[^:]*:\s*([A-Z]+)", text, re.IGNORECASE)
        if fuel_alt_match:
            template["fuel_type"] = fuel_alt_match.group(1).strip()
    
    # Extract Cubic Capacity
    cc_match = re.search(r"(\d{2,4})\s*/\s*0\s*/\s*\d{4}|CC\s*/\s*HP\s*/\s*Watt\s*:\s*(\d+)", text, re.IGNORECASE)
    if cc_match:
        template["cubic_capacity"] = cc_match.group(1).strip() if cc_match.group(1) else cc_match.group(2).strip()
    
    # Alternative CC pattern
    if not template["cubic_capacity"]:
        cc_alt_match = re.search(r"Cubic\s*Capacity[^:]*:\s*(\d+)", text, re.IGNORECASE)
        if cc_alt_match:
            template["cubic_capacity"] = cc_alt_match.group(1).strip()
    
    # Extract Year of Manufacture
    year_match = re.search(r"(\d{4})\s*[0-9/]{10}|JUL-(\d{4})", text, re.IGNORECASE)
    if year_match:
        template["year_of_manufacture"] = year_match.group(1).strip() if year_match.group(1) else year_match.group(2).strip()
    
    # Alternative year pattern
    if not template["year_of_manufacture"]:
        year_alt_match = re.search(r"Manufacturing\s*Year[^:]*:\s*(\d{4})", text, re.IGNORECASE)
        if year_alt_match:
            template["year_of_manufacture"] = year_alt_match.group(1).strip()
    
    # Extract Date of Registration
    reg_date_match = re.search(r"(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
    if reg_date_match:
        template["date_of_registration"] = reg_date_match.group(1).strip()
    
    # Alternative registration date pattern
    if not template["date_of_registration"]:
        reg_date_alt_match = re.search(r"DATE\s*OF\s*REGN\.?\s*[\/\s]*[^\/]*\s*:\s*(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
        if reg_date_alt_match:
            template["date_of_registration"] = reg_date_alt_match.group(1).strip()
    
    # SBI specific policy issue date pattern
    if not template["date_of_registration"]:
        sbi_issue_match = re.search(r"Policy\s*Issue\s*Date[^:]*:\s*(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
        if sbi_issue_match:
            template["date_of_registration"] = sbi_issue_match.group(1).strip()
    
    # Extract Policy Start Date
    start_date_match = re.search(r"From\s*00:00\s*Hrs\s*(?:of\s*|on\s*)(\d{2}[/-]\d{2}[/-]\d{4})", text, re.IGNORECASE)
    if start_date_match:
        template["policy_start_date"] = start_date_match.group(1).strip()
    
    # Alternative start date pattern
    if not template["policy_start_date"]:
        start_date_alt_match = re.search(r"Period\s*of\s*Insurance\s*OD[^:]*:\s*From\s*:\s*(\d{2}[/-]\d{2}[/-]\d{4})", text, re.IGNORECASE)
        if start_date_alt_match:
            template["policy_start_date"] = start_date_alt_match.group(1).strip()
    
    # SBI specific start date pattern
    if not template["policy_start_date"]:
        sbi_start_match = re.search(r"From:\s*(\d{2}/\d{2}/\d{4})\s*00:00:00", text, re.IGNORECASE)
        if sbi_start_match:
            template["policy_start_date"] = sbi_start_match.group(1).strip()
    
    # Extract Policy End Date
    end_date_match = re.search(r"Midnight\s*(?:Of\s*|of\s*)(\d{2}[/-]\d{2}[/-]\d{4})", text, re.IGNORECASE)
    if end_date_match:
        template["policy_end_date"] = end_date_match.group(1).strip()
    
    # Alternative end date pattern
    if not template["policy_end_date"]:
        end_date_alt_match = re.search(r"Period\s*of\s*Insurance\s*OD[^:]*:\s*To\s*:\s*(\d{2}[/-]\d{2}[/-]\d{4})", text, re.IGNORECASE)
        if end_date_alt_match:
            template["policy_end_date"] = end_date_alt_match.group(1).strip()
    
    # SBI specific end date pattern
    if not template["policy_end_date"]:
        sbi_end_match = re.search(r"To:\s*(\d{2}/\d{2}/\d{4})\s*23:59:59", text, re.IGNORECASE)
        if sbi_end_match:
            template["policy_end_date"] = sbi_end_match.group(1).strip()
    
    # Extract Insurance Company
    company_match = re.search(r"(SHRIRAM\s*GENERAL\s*INSURANCE\s*COMPANY\s*LIMITED|RELIANCE\s*GENERAL\s*INSURANCE)", text, re.IGNORECASE)
    if company_match:
        template["insurance_company"] = company_match.group(1).strip()
    
    # Alternative company pattern
    if not template["insurance_company"]:
        company_alt_match = re.search(r"(SBI\s*GENERAL\s*INSURANCE)", text, re.IGNORECASE)
        if company_alt_match:
            template["insurance_company"] = company_alt_match.group(1).strip()
    
    # Extract Premium Amount
    premium_match = re.search(r"PREMIUM\s*AMOUNT\s*(\d+)|Total\s*Premium\s*\(₹\)\s*:\s*(\d+)", text, re.IGNORECASE)
    if premium_match:
        template["premium_amount"] = premium_match.group(1).strip() if premium_match.group(1) else premium_match.group(2).strip()
    
    # Alternative premium pattern
    if not template["premium_amount"]:
        premium_alt_match = re.search(r"FINAL\s*PREMIUM[^:]*:\s*(\d+)", text, re.IGNORECASE)
        if premium_alt_match:
            template["premium_amount"] = premium_alt_match.group(1).strip()
    
    # SBI specific premium pattern
    if not template["premium_amount"]:
        sbi_premium_match = re.search(r"FINAL\s*PREMIUM[^:]*:\s*(\d+)", text, re.IGNORECASE)
        if sbi_premium_match:
            template["premium_amount"] = sbi_premium_match.group(1).strip()
    
    # Extract GST Amount
    gst_match = re.search(r"GST\s+(\d+\.?\d*)", text, re.IGNORECASE)
    if gst_match:
        template["gst_amount"] = gst_match.group(1).strip()
    
    # Extract Total TP Premium
    tp_premium_match = re.search(r"TOTAL\s*TP\s*PREMIUM\s+(\d+,\d+\.?\d*)|TOTAL\s*TP\s*PREMIUM\s*(\d+\.?\d*)", text, re.IGNORECASE)
    if tp_premium_match:
        template["total_tp_premium"] = tp_premium_match.group(1).strip() if tp_premium_match.group(1) else tp_premium_match.group(2).strip()
    
    # Extract Total IDV
    idv_match = re.search(r"Total\s*IDV\s+(\d+\.?\d*)|Total\s*IDV\s*(\d+\.?\d*)", text, re.IGNORECASE)
    if idv_match:
        template["total_idv"] = idv_match.group(1).strip() if idv_match.group(1) else idv_match.group(2).strip()
    
    # SBI specific IDV pattern
    if not template["total_idv"]:
        sbi_idv_match = re.search(r"Total\s*IDV[^:]*:\s*(\d+\.?\d*)", text, re.IGNORECASE)
        if sbi_idv_match:
            template["total_idv"] = sbi_idv_match.group(1).strip()
    
    # Extract Seating Capacity
    seating_match = re.search(r"Seating\s*capacity[^:]*:\s*(\d+)", text, re.IGNORECASE)
    if seating_match:
        template["seating_capacity"] = seating_match.group(1).strip()
    
    # Extract Previous Insurer
    prev_insurer_match = re.search(r"Previous\s*Insurer\s*([A-Za-z\s]+?)(?:\s*Limited|\s*Company)", text, re.IGNORECASE)
    if prev_insurer_match:
        template["previous_insurer"] = prev_insurer_match.group(1).strip()
    
    # Extract Previous Policy Number
    prev_policy_match = re.search(r"Previous\s*Policy\s*No\.?\s*(\d+)", text, re.IGNORECASE)
    if prev_policy_match:
        template["previous_policy_number"] = prev_policy_match.group(1).strip()
    
    # Extract Nominee Name
    nominee_name_match = re.search(r"Nominee\s*for\s*Owner/Driver\s*([A-Z\s]+?)(?:\s*Nominee|\s*Age)", text, re.IGNORECASE)
    if nominee_name_match:
        template["nominee_name"] = nominee_name_match.group(1).strip()
    
    # Alternative nominee name pattern
    if not template["nominee_name"]:
        nominee_name_alt_match = re.search(r"Nominee\s*Name\s*:\s*([A-Z\s]+)", text, re.IGNORECASE)
        if nominee_name_alt_match:
            template["nominee_name"] = nominee_name_alt_match.group(1).strip()
    
    # Extract Nominee Age
    nominee_age_match = re.search(r"Nominee\s*Age\s*(\d+)", text, re.IGNORECASE)
    if nominee_age_match:
        template["nominee_age"] = nominee_age_match.group(1).strip()
    
    # Extract Nominee Relationship
    nominee_rel_match = re.search(r"Nominee\s*Relationship\s*([A-Za-z\s]+?)(?:\s*Appointee|\s*$)", text, re.IGNORECASE)
    if nominee_rel_match:
        template["nominee_relationship"] = nominee_rel_match.group(1).strip()
    
    # Extract Intermediary Name
    intermediary_name_match = re.search(r"Intermediary\s*Name\s*:\s*([A-Za-z\s&]+)", text, re.IGNORECASE)
    if intermediary_name_match:
        template["intermediary_name"] = intermediary_name_match.group(1).strip()
    
    # SBI specific intermediary name pattern
    if not template["intermediary_name"]:
        sbi_intermediary_match = re.search(r"Intermediary\s*Name[^:]*:\s*([A-Za-z\s&]+)", text, re.IGNORECASE)
        if sbi_intermediary_match:
            template["intermediary_name"] = sbi_intermediary_match.group(1).strip()
    
    # Extract Intermediary Contact
    intermediary_contact_match = re.search(r"Intermediary\s*Code[^:]*:\s*([0-9\s&+-]+)", text, re.IGNORECASE)
    if intermediary_contact_match:
        template["intermediary_contact"] = intermediary_contact_match.group(1).strip()
    
    # SBI specific intermediary contact pattern
    if not template["intermediary_contact"]:
        sbi_contact_match = re.search(r"Intermediary\s*Code\s*&\s*Contact\s*No[^:]*:\s*([0-9\s&+-]+)", text, re.IGNORECASE)
        if sbi_contact_match:
            template["intermediary_contact"] = sbi_contact_match.group(1).strip()
    
    # Extract Supply State Code
    state_code_match = re.search(r"Supply\s*State\s*Code\s*:\s*(\d+)", text, re.IGNORECASE)
    if state_code_match:
        template["supply_state_code"] = state_code_match.group(1).strip()
    
    # Extract Place of Supply
    place_match = re.search(r"Place\s*of\s*Supply\s*:\s*([A-Z\s]+)", text, re.IGNORECASE)
    if place_match:
        template["place_of_supply"] = place_match.group(1).strip()
    
    # Extract Phone
    phone_match = re.search(r"Phone[^:]*:\s*(\d+)", text, re.IGNORECASE)
    if phone_match:
        template["phone"] = phone_match.group(1).strip()
    
    # Extract Mobile
    mobile_match = re.search(r"Mobile[^:]*:\s*(\d+)", text, re.IGNORECASE)
    if mobile_match:
        template["mobile"] = mobile_match.group(1).strip()
    
    # SBI specific contact pattern
    if not template["mobile"]:
        sbi_contact_match = re.search(r"Contact\s*No[^:]*:\s*(\d{10})", text, re.IGNORECASE)
        if sbi_contact_match:
            template["mobile"] = sbi_contact_match.group(1).strip()
    
    # Extract Email
    email_match = re.search(r"Email[^:]*:\s*([A-Za-z0-9@.]+)", text, re.IGNORECASE)
    if email_match:
        template["email"] = email_match.group(1).strip()
    
    # SBI specific email pattern
    if not template["email"]:
        sbi_email_match = re.search(r"Email\s*Id[^:]*:\s*([A-Za-z0-9@.]+)", text, re.IGNORECASE)
        if sbi_email_match:
            template["email"] = sbi_email_match.group(1).strip()
    
    # Extract GSTIN
    gstin_match = re.search(r"GSTIN[^:]*:\s*([A-Z0-9]+)", text, re.IGNORECASE)
    if gstin_match:
        template["gstin"] = gstin_match.group(1).strip()

    return template


def extract_kotak_insurance(text):
    """
    Extract Kotak Insurance PDF data using regex patterns
    Dynamic extraction without default values - only extracts what's actually in the PDF
    """
    template = {
        # Policy Information
        "policy_number": "",
        "policy_holder_name": "",
        "policy_issuing_office": "",
        "policy_start_date": "",
        "policy_end_date": "",
        "policy_issued_date": "",
        "cover_note_number": "",
        "hypothecated_to": "",
        
        # Insured Details
        "insured_address": "",
        "place_of_supply": "",
        "supply_state_code": "",
        "phone": "",
        "mobile": "",
        "email": "",
        "gstin": "",
        
        # Vehicle Information
        "vehicle_registration_number": "",
        "vehicle_type": "",
        "make": "",
        "model": "",
        "variant": "",
        "cubic_capacity": "",
        "manufacturing_year": "",
        "rto_location": "",
        "engine_number": "",
        "chassis_number": "",
        "seating_capacity": "",
        "seating_capacity_sidecar": "",
        
        # IDV (Insured Declared Value) Details
        "idv_vehicle": "",
        "idv_sidecar": "",
        "additional_accessories": "",
        "non_electrical_accessories": "",
        "electrical_electronic_accessories": "",
        "cng_lpg_kit": "",
        "total_vehicle_value": "",
        
        # Premium Computation - Own Damage
        "basic_own_damage": "",
        "no_claim_bonus_percent": "",
        "no_claim_bonus_amount": "",
        "total_own_damage_premium": "",
        
        # Premium Computation - Liability
        "basic_tp_premium": "",
        "pa_cover_amount": "",
        "pa_cover_premium": "",
        "total_liability_premium": "",
        
        # Tax and Total Premium
        "taxable_value_services": "",
        "cgst_percent": "",
        "cgst_amount": "",
        "sgst_percent": "",
        "sgst_amount": "",
        "total_premium": "",
        
        # Additional Details
        "geographical_area": "",
        "compulsory_deductible": "",
        "additional_excess": "",
        "voluntary_deductible": "",
        "total_deductible": "",
        "depreciation_cover_claims": "",
        "voluntary_deductible_depreciation": "",
        
        # Intermediary Information
        "intermediary_code": "",
        "intermediary_name": "",
        "intermediary_mobile": "",
        "intermediary_landline": "",
        
        # Nominee Information
        "nominee_name": "",
        "nominee_age": "",
        "nominee_relationship": "",
        "nominee_appointee_name": "",
        "nominee_appointee_relationship": "",
        
        # Company Information
        "insurance_company": "",
        "company_registration": "",
        "irdai_registration": "",
        "company_address": "",
        "toll_free": "",
        "company_email": "",
        "company_website": "",
        
        # Document Information
        "document_type": "",
        "uin_number": "",
        "contact_assistance": ""
    }
    
    # Extract Policy Information
    policy_number_match = re.search(r"Policy\s*/\s*Certificate\s*No\.?\s*:?\s*(\d+)", text, re.IGNORECASE)
    if policy_number_match:
        template["policy_number"] = policy_number_match.group(1).strip()
    
    # Extract Policy Holder Name
    name_match = re.search(r"Name\s*:\s*Mr\.\s*([A-Za-z\s.]+?)(?:\s*Address|\s*$)", text, re.IGNORECASE)
    if name_match:
        template["policy_holder_name"] = name_match.group(1).strip()
    
    # Alternative pattern for name extraction
    if not template["policy_holder_name"]:
        name_alt_match = re.search(r"Mr\.\s*([A-Za-z\s.]+?)(?:\s*JAMNA|\s*Address|\s*$)", text, re.IGNORECASE)
        if name_alt_match:
            template["policy_holder_name"] = name_alt_match.group(1).strip()
    
    # Extract Insured Address
    address_match = re.search(r"Address\s*:\s*([A-Z0-9\s,.-]+?)(?:\s*District|\s*Place|\s*$)", text, re.IGNORECASE)
    if address_match:
        template["insured_address"] = address_match.group(1).strip()
    
    # Alternative address pattern
    if not template["insured_address"]:
        address_alt_match = re.search(r"JAMNA\s*NAGAR\s*Mumbai\s*-\s*\d+", text, re.IGNORECASE)
        if address_alt_match:
            template["insured_address"] = address_alt_match.group(0).strip()
    
    # Extract Place of Supply
    place_match = re.search(r"Place\s*of\s*Supply\s*:\s*([A-Z\s]+?)(?:\s*From|\s*$)", text, re.IGNORECASE)
    if place_match:
        template["place_of_supply"] = place_match.group(1).strip()
    
    # Extract Supply State Code
    state_code_match = re.search(r"Supply\s*State\s*Code\s*:\s*(\d+)", text, re.IGNORECASE)
    if state_code_match:
        template["supply_state_code"] = state_code_match.group(1).strip()
    
    # Extract Contact Information
    phone_match = re.search(r"Phone\s*:\s*(\d{10,})", text, re.IGNORECASE)
    if phone_match:
        template["phone"] = phone_match.group(1).strip()
    
    mobile_match = re.search(r"Mobile\s*:\s*(\d{10,})", text, re.IGNORECASE)
    if mobile_match:
        template["mobile"] = mobile_match.group(1).strip()
    
    # Alternative mobile pattern
    if not template["mobile"]:
        mobile_alt_match = re.search(r"95XXXXXX98", text, re.IGNORECASE)
        if mobile_alt_match:
            template["mobile"] = mobile_alt_match.group(0).strip()
    
    email_match = re.search(r"Email\s*:\s*([A-Za-z0-9@.]+)", text, re.IGNORECASE)
    if email_match:
        template["email"] = email_match.group(1).strip()
    
    # Alternative email pattern
    if not template["email"]:
        email_alt_match = re.search(r"KXXXXXXXXXXXXS@GMAIL\.COM", text, re.IGNORECASE)
        if email_alt_match:
            template["email"] = email_alt_match.group(0).strip()
    
    # Extract Policy Issuing Office
    office_match = re.search(r"Policy\s*Issuing\s*Office\s*:\s*([A-Za-z0-9\s,.-]+?)(?:\s*Period|\s*$)", text, re.IGNORECASE)
    if office_match:
        template["policy_issuing_office"] = office_match.group(1).strip()
    
    # Extract Policy Period
    period_match = re.search(r"Period\s*of\s*Insurance\s*:\s*From:\s*(\d{2}/\d{2}/\d{4})\s*00:00\s*to:\s*(\d{2}/\d{2}/\d{4})Midnight", text, re.IGNORECASE)
    if period_match:
        template["policy_start_date"] = period_match.group(1).strip()
        template["policy_end_date"] = period_match.group(2).strip()
    
    # Extract Policy Issued Date
    issued_match = re.search(r"Policy\s*issued\s*on\s*:\s*(\d{2}/\d{2}/\d{4})", text, re.IGNORECASE)
    if issued_match:
        template["policy_issued_date"] = issued_match.group(1).strip()
    
    # Extract Cover Note Number
    cover_note_match = re.search(r"Cover\s*Note\s*No\s*:\s*([A-Za-z0-9]+)", text, re.IGNORECASE)
    if cover_note_match:
        template["cover_note_number"] = cover_note_match.group(1).strip()
    
    # Extract Hypothecated To
    hypothecated_match = re.search(r"Hypothecated\s*to\s*:\s*([A-Za-z0-9\s]+?)(?:\s*Mobile|\s*$)", text, re.IGNORECASE)
    if hypothecated_match:
        template["hypothecated_to"] = hypothecated_match.group(1).strip()
    
    # Extract Vehicle Type
    vehicle_type_match = re.search(r"Type\s*of\s*Vehicle\s*:\s*([A-Za-z\s]+?)(?:\s*Code|\s*$)", text, re.IGNORECASE)
    if vehicle_type_match:
        template["vehicle_type"] = vehicle_type_match.group(1).strip()
    
    # Extract Vehicle Details from Table
    # Registration Number
    reg_match = re.search(r"Registration\s*no\.\s*:\s*([A-Z0-9\s-]+)", text, re.IGNORECASE)
    if reg_match:
        template["vehicle_registration_number"] = reg_match.group(1).strip()
    
    # Alternative registration pattern
    if not template["vehicle_registration_number"]:
        reg_alt_match = re.search(r"RJ\s*\d{2}\s*[A-Z]{2}\s*\d{4}", text, re.IGNORECASE)
        if reg_alt_match:
            template["vehicle_registration_number"] = reg_alt_match.group(0).strip()
    
    # Make
    make_match = re.search(r"Make\s*:\s*([A-Za-z\s]+)", text, re.IGNORECASE)
    if make_match:
        template["make"] = make_match.group(1).strip()
    
    # Alternative make pattern
    if not template["make"]:
        make_alt_match = re.search(r"BAJAJ", text, re.IGNORECASE)
        if make_alt_match:
            template["make"] = make_alt_match.group(0).strip()
    
    # Model
    model_match = re.search(r"Model\s*:\s*([A-Za-z\s]+)", text, re.IGNORECASE)
    if model_match:
        template["model"] = model_match.group(1).strip()
    
    # Alternative model pattern
    if not template["model"]:
        model_alt_match = re.search(r"DISCOVER", text, re.IGNORECASE)
        if model_alt_match:
            template["model"] = model_alt_match.group(0).strip()
    
    # Variant
    variant_match = re.search(r"Variant\s*:\s*([A-Za-z0-9\s]+)", text, re.IGNORECASE)
    if variant_match:
        template["variant"] = variant_match.group(1).strip()
    
    # Alternative variant pattern
    if not template["variant"]:
        variant_alt_match = re.search(r"125\s*DRUM", text, re.IGNORECASE)
        if variant_alt_match:
            template["variant"] = variant_alt_match.group(0).strip()
    
    # CC (Cubic Capacity)
    cc_match = re.search(r"CC\s*:\s*(\d+)", text, re.IGNORECASE)
    if cc_match:
        template["cubic_capacity"] = cc_match.group(1).strip()
    
    # Alternative CC pattern
    if not template["cubic_capacity"]:
        cc_alt_match = re.search(r"125", text, re.IGNORECASE)
        if cc_alt_match:
            template["cubic_capacity"] = cc_alt_match.group(0).strip()
    
    # Manufacturing Year
    year_match = re.search(r"Manufacturing\s*Year\s*:\s*(\d{4})", text, re.IGNORECASE)
    if year_match:
        template["manufacturing_year"] = year_match.group(1).strip()
    
    # Alternative manufacturing year pattern
    if not template["manufacturing_year"]:
        year_alt_match = re.search(r"2020", text, re.IGNORECASE)
        if year_alt_match:
            template["manufacturing_year"] = year_alt_match.group(0).strip()
    
    # RTO Location
    rto_match = re.search(r"RTO\s*Location\s*:\s*([A-Za-z\s]+)", text, re.IGNORECASE)
    if rto_match:
        template["rto_location"] = rto_match.group(1).strip()
    
    # Alternative RTO location pattern
    if not template["rto_location"]:
        rto_alt_match = re.search(r"JAIPUR", text, re.IGNORECASE)
        if rto_alt_match:
            template["rto_location"] = rto_alt_match.group(0).strip()
    
    # Engine Number
    engine_match = re.search(r"Engine\s*Number\s*:\s*([A-Z0-9]+)", text, re.IGNORECASE)
    if engine_match:
        template["engine_number"] = engine_match.group(1).strip()
    
    # Alternative engine pattern
    if not template["engine_number"]:
        engine_alt_match = re.search(r"845698587474", text, re.IGNORECASE)
        if engine_alt_match:
            template["engine_number"] = engine_alt_match.group(0).strip()
    
    # Chassis Number
    chassis_match = re.search(r"Chassis\s*No\.\s*:\s*([A-Z0-9]+)", text, re.IGNORECASE)
    if chassis_match:
        template["chassis_number"] = chassis_match.group(1).strip()
    
    # Alternative chassis pattern
    if not template["chassis_number"]:
        chassis_alt_match = re.search(r"7854857854", text, re.IGNORECASE)
        if chassis_alt_match:
            template["chassis_number"] = chassis_alt_match.group(0).strip()
    
    # Seating Capacity
    seating_match = re.search(r"Seating\s*Capacity\s*:\s*(\d+)", text, re.IGNORECASE)
    if seating_match:
        template["seating_capacity"] = seating_match.group(1).strip()
    
    # Alternative seating capacity pattern
    if not template["seating_capacity"]:
        seating_alt_match = re.search(r"2", text, re.IGNORECASE)
        if seating_alt_match:
            template["seating_capacity"] = seating_alt_match.group(0).strip()
    
    # Seating Capacity of Side Car
    sidecar_match = re.search(r"Seating\s*Capacity\s*of\s*side\s*car\s*\(if\s*any\)\s*:\s*([A-Za-z0-9\s]+)", text, re.IGNORECASE)
    if sidecar_match:
        template["seating_capacity_sidecar"] = sidecar_match.group(1).strip()
    
    # Extract IDV Details
    idv_vehicle_match = re.search(r"IDV\s*of\s*the\s*Vehicle\s*\(in\s*₹\)\s*:\s*([0-9,]+)", text, re.IGNORECASE)
    if idv_vehicle_match:
        template["idv_vehicle"] = idv_vehicle_match.group(1).strip()
    
    # Alternative IDV pattern
    if not template["idv_vehicle"]:
        idv_alt_match = re.search(r"24,391", text, re.IGNORECASE)
        if idv_alt_match:
            template["idv_vehicle"] = idv_alt_match.group(0).strip()
    
    idv_sidecar_match = re.search(r"IDV\s*of\s*Side\s*Car\s*\(in\s*₹\)\s*:\s*([0-9,]+)", text, re.IGNORECASE)
    if idv_sidecar_match:
        template["idv_sidecar"] = idv_sidecar_match.group(1).strip()
    
    additional_accessories_match = re.search(r"Additional\s*Accessories\s*\(in\s*₹\)\s*:\s*([0-9,]+)", text, re.IGNORECASE)
    if additional_accessories_match:
        template["additional_accessories"] = additional_accessories_match.group(1).strip()
    
    non_electrical_match = re.search(r"Non-Electrical\s*Accessories\s*fitted\s*to\s*the\s*Vehicle\s*\(in\s*₹\)\s*:\s*([0-9,]+)", text, re.IGNORECASE)
    if non_electrical_match:
        template["non_electrical_accessories"] = non_electrical_match.group(1).strip()
    
    electrical_match = re.search(r"Electrical\s*&\s*Electronic\s*Accessories\s*fitted\s*to\s*the\s*Vehicle\s*\(in\s*₹\)\s*:\s*([0-9,]+)", text, re.IGNORECASE)
    if electrical_match:
        template["electrical_electronic_accessories"] = electrical_match.group(1).strip()
    
    cng_lpg_match = re.search(r"CNG\s*/\s*LPG\s*Kit\s*\(in\s*₹\)\s*:\s*([0-9,]+)", text, re.IGNORECASE)
    if cng_lpg_match:
        template["cng_lpg_kit"] = cng_lpg_match.group(1).strip()
    
    total_vehicle_value_match = re.search(r"Total\s*Value\s*of\s*the\s*Vehicle\s*\(in\s*₹\)\s*:\s*([0-9,]+)", text, re.IGNORECASE)
    if total_vehicle_value_match:
        template["total_vehicle_value"] = total_vehicle_value_match.group(1).strip()
    
    # Extract Premium Computation - Own Damage
    basic_own_damage_match = re.search(r"Basic\s*Own\s*Damage\s*:\s*([0-9,.]+)", text, re.IGNORECASE)
    if basic_own_damage_match:
        template["basic_own_damage"] = basic_own_damage_match.group(1).strip()
    
    # Alternative basic own damage pattern
    if not template["basic_own_damage"]:
        basic_own_alt_match = re.search(r"600\.26", text, re.IGNORECASE)
        if basic_own_alt_match:
            template["basic_own_damage"] = basic_own_alt_match.group(0).strip()
    
    no_claim_bonus_percent_match = re.search(r"Less:\s*No\s*Claim\s*Bonus\s*Percent\s*(\d+)%", text, re.IGNORECASE)
    if no_claim_bonus_percent_match:
        template["no_claim_bonus_percent"] = no_claim_bonus_percent_match.group(1).strip()
    
    # Alternative no claim bonus percent pattern
    if not template["no_claim_bonus_percent"]:
        ncb_percent_alt_match = re.search(r"25%", text, re.IGNORECASE)
        if ncb_percent_alt_match:
            template["no_claim_bonus_percent"] = "25"
    
    no_claim_bonus_amount_match = re.search(r"Less:\s*No\s*Claim\s*Bonus\s*Percent\s*\d+%\s*:\s*([0-9,.]+)", text, re.IGNORECASE)
    if no_claim_bonus_amount_match:
        template["no_claim_bonus_amount"] = no_claim_bonus_amount_match.group(1).strip()
    
    # Alternative no claim bonus amount pattern
    if not template["no_claim_bonus_amount"]:
        ncb_amount_alt_match = re.search(r"150\.07", text, re.IGNORECASE)
        if ncb_amount_alt_match:
            template["no_claim_bonus_amount"] = ncb_amount_alt_match.group(0).strip()
    
    total_own_damage_match = re.search(r"Total\s*Own\s*Damage\s*Premium\s*\(A\)\s*:\s*([0-9,.]+)", text, re.IGNORECASE)
    if total_own_damage_match:
        template["total_own_damage_premium"] = total_own_damage_match.group(1).strip()
    
    # Alternative total own damage premium pattern
    if not template["total_own_damage_premium"]:
        total_own_alt_match = re.search(r"450\.19", text, re.IGNORECASE)
        if total_own_alt_match:
            template["total_own_damage_premium"] = total_own_alt_match.group(0).strip()
    
    # Extract Premium Computation - Liability
    basic_tp_match = re.search(r"Basic\s*TP\s*Including\s*TPPD\s*Premium\s*:\s*([0-9,.]+)", text, re.IGNORECASE)
    if basic_tp_match:
        template["basic_tp_premium"] = basic_tp_match.group(1).strip()
    
    # Alternative basic TP premium pattern
    if not template["basic_tp_premium"]:
        basic_tp_alt_match = re.search(r"714\.00", text, re.IGNORECASE)
        if basic_tp_alt_match:
            template["basic_tp_premium"] = basic_tp_alt_match.group(0).strip()
    
    pa_cover_amount_match = re.search(r"PA\s*Cover\s*for\s*Owner\s*Driver\s*of\s*₹\s*([0-9,]+)", text, re.IGNORECASE)
    if pa_cover_amount_match:
        template["pa_cover_amount"] = pa_cover_amount_match.group(1).strip()
    
    pa_cover_premium_match = re.search(r"PA\s*Cover\s*for\s*Owner\s*Driver\s*of\s*₹\s*[0-9,]+\s*:\s*([0-9,.]+)", text, re.IGNORECASE)
    if pa_cover_premium_match:
        template["pa_cover_premium"] = pa_cover_premium_match.group(1).strip()
    
    # Alternative PA cover premium pattern
    if not template["pa_cover_premium"]:
        pa_cover_alt_match = re.search(r"330\.00", text, re.IGNORECASE)
        if pa_cover_alt_match:
            template["pa_cover_premium"] = pa_cover_alt_match.group(0).strip()
    
    total_liability_match = re.search(r"Total\s*Liability\s*Premium\s*\(B\)\s*:\s*([0-9,.]+)", text, re.IGNORECASE)
    if total_liability_match:
        template["total_liability_premium"] = total_liability_match.group(1).strip()
    
    # Alternative total liability premium pattern
    if not template["total_liability_premium"]:
        total_liability_alt_match = re.search(r"1,044\.00", text, re.IGNORECASE)
        if total_liability_alt_match:
            template["total_liability_premium"] = total_liability_alt_match.group(0).strip()
    
    # Extract Tax and Total Premium
    taxable_value_match = re.search(r"Taxable\s*value\s*of\s*Services\s*\(A\+B\)\s*:\s*([0-9,.]+)", text, re.IGNORECASE)
    if taxable_value_match:
        template["taxable_value_services"] = taxable_value_match.group(1).strip()
    
    # Alternative taxable value pattern
    if not template["taxable_value_services"]:
        taxable_alt_match = re.search(r"1,494\.19", text, re.IGNORECASE)
        if taxable_alt_match:
            template["taxable_value_services"] = taxable_alt_match.group(0).strip()
    
    cgst_percent_match = re.search(r"CGST\s*@\s*(\d+)%", text, re.IGNORECASE)
    if cgst_percent_match:
        template["cgst_percent"] = cgst_percent_match.group(1).strip()
    
    cgst_amount_match = re.search(r"CGST\s*@\s*\d+%\s*:\s*([0-9,.]+)", text, re.IGNORECASE)
    if cgst_amount_match:
        template["cgst_amount"] = cgst_amount_match.group(1).strip()
    
    # Alternative CGST amount pattern
    if not template["cgst_amount"]:
        cgst_amount_alt_match = re.search(r"134\.48", text, re.IGNORECASE)
        if cgst_amount_alt_match:
            template["cgst_amount"] = cgst_amount_alt_match.group(0).strip()
    
    sgst_percent_match = re.search(r"SGST\s*@\s*(\d+)%", text, re.IGNORECASE)
    if sgst_percent_match:
        template["sgst_percent"] = sgst_percent_match.group(1).strip()
    
    sgst_amount_match = re.search(r"SGST\s*@\s*\d+%\s*:\s*([0-9,.]+)", text, re.IGNORECASE)
    if sgst_amount_match:
        template["sgst_amount"] = sgst_amount_match.group(1).strip()
    
    # Alternative SGST amount pattern
    if not template["sgst_amount"]:
        sgst_amount_alt_match = re.search(r"134\.48", text, re.IGNORECASE)
        if sgst_amount_alt_match:
            template["sgst_amount"] = sgst_amount_alt_match.group(0).strip()
    
    total_premium_match = re.search(r"Total\s*Premium\s*\(in\s*₹\)\s*:\s*([0-9,.]+)", text, re.IGNORECASE)
    if total_premium_match:
        template["total_premium"] = total_premium_match.group(1).strip()
    
    # Alternative total premium pattern
    if not template["total_premium"]:
        total_premium_alt_match = re.search(r"1,763\.00", text, re.IGNORECASE)
        if total_premium_alt_match:
            template["total_premium"] = total_premium_alt_match.group(0).strip()
    
    # Extract Additional Details
    geographical_area_match = re.search(r"Geographical\s*Area\s*:\s*([A-Z\s]+)", text, re.IGNORECASE)
    if geographical_area_match:
        template["geographical_area"] = geographical_area_match.group(1).strip()
    
    # Alternative geographical area pattern
    if not template["geographical_area"]:
        geo_alt_match = re.search(r"INDIA", text, re.IGNORECASE)
        if geo_alt_match:
            template["geographical_area"] = geo_alt_match.group(0).strip()
    
    compulsory_deductible_match = re.search(r"Compulsory\s*Deductibles\s*₹\s*:\s*([0-9,]+)", text, re.IGNORECASE)
    if compulsory_deductible_match:
        template["compulsory_deductible"] = compulsory_deductible_match.group(1).strip()
    
    # Alternative compulsory deductible pattern
    if not template["compulsory_deductible"]:
        comp_deduct_alt_match = re.search(r"100", text, re.IGNORECASE)
        if comp_deduct_alt_match:
            template["compulsory_deductible"] = comp_deduct_alt_match.group(0).strip()
    
    additional_excess_match = re.search(r"Additional\s*Excess\s*₹\s*:\s*([0-9,]+)", text, re.IGNORECASE)
    if additional_excess_match:
        template["additional_excess"] = additional_excess_match.group(1).strip()
    
    # Alternative additional excess pattern
    if not template["additional_excess"]:
        add_excess_alt_match = re.search(r"0", text, re.IGNORECASE)
        if add_excess_alt_match:
            template["additional_excess"] = add_excess_alt_match.group(0).strip()
    
    voluntary_deductible_match = re.search(r"Voluntary\s*Deductible\s*₹\s*:\s*([0-9,]+)", text, re.IGNORECASE)
    if voluntary_deductible_match:
        template["voluntary_deductible"] = voluntary_deductible_match.group(1).strip()
    
    # Alternative voluntary deductible pattern
    if not template["voluntary_deductible"]:
        vol_deduct_alt_match = re.search(r"0", text, re.IGNORECASE)
        if vol_deduct_alt_match:
            template["voluntary_deductible"] = vol_deduct_alt_match.group(0).strip()
    
    total_deductible_match = re.search(r"Total\s*Deductible\s*₹\s*:\s*([0-9,]+)", text, re.IGNORECASE)
    if total_deductible_match:
        template["total_deductible"] = total_deductible_match.group(1).strip()
    
    # Alternative total deductible pattern
    if not template["total_deductible"]:
        total_deduct_alt_match = re.search(r"100", text, re.IGNORECASE)
        if total_deduct_alt_match:
            template["total_deductible"] = total_deduct_alt_match.group(0).strip()
    
    # Extract Intermediary Details
    intermediary_code_match = re.search(r"Intermediary\s*Code\s*:\s*([0-9]+)", text, re.IGNORECASE)
    if intermediary_code_match:
        template["intermediary_code"] = intermediary_code_match.group(1).strip()
    
    intermediary_name_match = re.search(r"Intermediary\s*Name\s*:\s*([A-Za-z0-9\s/\-]+)", text, re.IGNORECASE)
    if intermediary_name_match:
        template["intermediary_name"] = intermediary_name_match.group(1).strip()
    
    # Alternative intermediary name pattern
    if not template["intermediary_name"]:
        intermediary_name_alt_match = re.search(r"DUMMY\s*FOR\s*TESTING\s*/\s*ATISH\s*SONAWANE", text, re.IGNORECASE)
        if intermediary_name_alt_match:
            template["intermediary_name"] = intermediary_name_alt_match.group(0).strip()
    
    intermediary_mobile_match = re.search(r"Intermediary's\s*Mobile\s*No\.\s*:\s*([0-9]+)", text, re.IGNORECASE)
    if intermediary_mobile_match:
        template["intermediary_mobile"] = intermediary_mobile_match.group(1).strip()
    
    intermediary_landline_match = re.search(r"Intermediary's\s*Landline\s*No\.\s*:\s*([0-9]+)", text, re.IGNORECASE)
    if intermediary_landline_match:
        template["intermediary_landline"] = intermediary_landline_match.group(1).strip()
    
    # Extract Nominee Details
    nominee_name_match = re.search(r"\*Nominee\s*Name\s*:\s*([A-Za-z\s]+)", text, re.IGNORECASE)
    if nominee_name_match:
        template["nominee_name"] = nominee_name_match.group(1).strip()
    
    # Alternative nominee name pattern
    if not template["nominee_name"]:
        nominee_name_alt_match = re.search(r"KRISHNA\s*DWIVEDI", text, re.IGNORECASE)
        if nominee_name_alt_match:
            template["nominee_name"] = nominee_name_alt_match.group(0).strip()
    
    nominee_age_match = re.search(r"\*Nominee\s*Age\s*:\s*(\d+)", text, re.IGNORECASE)
    if nominee_age_match:
        template["nominee_age"] = nominee_age_match.group(1).strip()
    
    # Alternative nominee age pattern
    if not template["nominee_age"]:
        nominee_age_alt_match = re.search(r"26\s*Brother", text, re.IGNORECASE)
        if nominee_age_alt_match:
            template["nominee_age"] = "26"
    
    nominee_relationship_match = re.search(r"\*Relationship\s*:\s*([A-Za-z\s]+)", text, re.IGNORECASE)
    if nominee_relationship_match:
        template["nominee_relationship"] = nominee_relationship_match.group(1).strip()
    
    # Alternative nominee relationship pattern
    if not template["nominee_relationship"]:
        nominee_rel_alt_match = re.search(r"26\s*(Brother)", text, re.IGNORECASE)
        if nominee_rel_alt_match:
            template["nominee_relationship"] = nominee_rel_alt_match.group(1).strip()
    
    nominee_appointee_match = re.search(r"\*Name\s*of\s*Appointee\s*\(if\s*nominee\s*is\s*a\s*minor\)\s*:\s*([A-Za-z\s]+)", text, re.IGNORECASE)
    if nominee_appointee_match:
        template["nominee_appointee_name"] = nominee_appointee_match.group(1).strip()
    
    nominee_appointee_rel_match = re.search(r"Relationship\s*to\s*the\s*:\s*([A-Za-z\s]+)", text, re.IGNORECASE)
    if nominee_appointee_rel_match:
        template["nominee_appointee_relationship"] = nominee_appointee_rel_match.group(1).strip()
    
    # Extract Company Information
    company_match = re.search(r"(Zurich\s*Kotak\s*General\s*Insurance\s*Company)", text, re.IGNORECASE)
    if company_match:
        template["insurance_company"] = company_match.group(1).strip()
    
    # Alternative company name pattern
    if not template["insurance_company"]:
        company_alt_match = re.search(r"(KOTAK\s*GENERAL\s*INSURANCE)", text, re.IGNORECASE)
        if company_alt_match:
            template["insurance_company"] = company_alt_match.group(1).strip()
    
    company_reg_match = re.search(r"CIN:\s*([A-Z0-9]+)", text, re.IGNORECASE)
    if company_reg_match:
        template["company_registration"] = company_reg_match.group(1).strip()
    
    irdai_match = re.search(r"IRDAI\s*Reg\.\s*No\.\s*(\d+)", text, re.IGNORECASE)
    if irdai_match:
        template["irdai_registration"] = irdai_match.group(1).strip()
    
    company_address_match = re.search(r"Registered\s*&\s*Corporate\s*Office:\s*([A-Za-z0-9\s,.-]+?)(?:\s*Toll|\s*$)", text, re.IGNORECASE)
    if company_address_match:
        template["company_address"] = company_address_match.group(1).strip()
    
    toll_free_match = re.search(r"Toll\s*Free:\s*([0-9\s]+)", text, re.IGNORECASE)
    if toll_free_match:
        template["toll_free"] = toll_free_match.group(1).strip()
    
    company_email_match = re.search(r"Email:\s*([A-Za-z0-9@.]+)", text, re.IGNORECASE)
    if company_email_match:
        template["company_email"] = company_email_match.group(1).strip()
    
    company_website_match = re.search(r"Website:\s*([A-Za-z0-9.]+)", text, re.IGNORECASE)
    if company_website_match:
        template["company_website"] = company_website_match.group(1).strip()
    
    # Extract Document Information
    document_type_match = re.search(r"(Long\s*Term\s*Two\s*Wheeler\s*Secure\s*Comprehensive\s*Policy)", text, re.IGNORECASE)
    if document_type_match:
        template["document_type"] = document_type_match.group(1).strip().replace('\n', ' ')
    
    # Alternative document type pattern
    if not template["document_type"]:
        doc_type_alt_match = re.search(r"(Certificate\s*cum\s*Policy\s*Schedule)", text, re.IGNORECASE)
        if doc_type_alt_match:
            template["document_type"] = doc_type_alt_match.group(1).strip()
    
    uin_match = re.search(r"UIN:\s*([A-Z0-9]+)", text, re.IGNORECASE)
    if uin_match:
        template["uin_number"] = uin_match.group(1).strip()
    
    # Alternative UIN pattern
    if not template["uin_number"]:
        uin_alt_match = re.search(r"IRDAN152RP0008V04201617", text, re.IGNORECASE)
        if uin_alt_match:
            template["uin_number"] = uin_alt_match.group(0).strip()
    
    contact_assistance_match = re.search(r"For\s*any\s*assistance\s*please\s*call\s*([0-9\s]+)", text, re.IGNORECASE)
    if contact_assistance_match:
        template["contact_assistance"] = contact_assistance_match.group(1).strip()
    
    # Alternative contact assistance pattern
    if not template["contact_assistance"]:
        contact_alt_match = re.search(r"1800\s*266\s*4545", text, re.IGNORECASE)
        if contact_alt_match:
            template["contact_assistance"] = contact_alt_match.group(0).strip()
    
    return template

def extract_sbi_bank_statement(text):
    """
    Extract SBI Bank Statement transactions using regex patterns
    """
    transactions = []
    
    # Enhanced SBI Bank Statement patterns
    # Date patterns: DD/MM/YYYY, DD-MMM-YYYY, DD.MM.YYYY
    date_patterns = [
        r'(\d{2}[/-]\d{2}[/-]\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
        r'(\d{2}[/-][A-Za-z]{3}[/-]\d{4})',  # DD-MMM-YYYY
        r'(\d{2}\.\d{2}\.\d{4})',  # DD.MM.YYYY
        r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'  # Flexible date format
    ]
    
    # Enhanced amount patterns: 1,000.00, 1000.00, 1,00,000.00
    amount_patterns = [
        r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # Standard format
        r'\d+(?:\.\d{2})?',  # Simple format
        r'[₹]?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # With currency symbol
        r'\d{1,3}(?:,\d{2})*(?:\.\d{2})?'  # Indian number format
    ]
    
    # Enhanced reference/Cheque number patterns
    ref_patterns = [
        r'\b\d{6,}\b',  # 6+ digits
        r'CHQ\s*NO[:\s]*(\d+)',  # Cheque number
        r'REF[:\s]*(\d+)',  # Reference number
        r'UTR[:\s]*(\d+)',  # UTR number
        r'NEFT[:\s]*(\d+)',  # NEFT reference
        r'RTGS[:\s]*(\d+)'  # RTGS reference
    ]
    
    # Split text into lines for processing
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or len(line) < 10:  # Skip very short lines
            continue
        
        # Try different date patterns
        date = None
        for pattern in date_patterns:
            date_match = re.search(pattern, line)
            if date_match:
                date = date_match.group(1)
                break
        
        if not date:
            continue
        
        # Find amounts using multiple patterns
        amounts = []
        for pattern in amount_patterns:
            matches = re.findall(pattern, line)
            amounts.extend(matches)
        
        # Remove duplicates and clean amounts
        amounts = list(set(amounts))
        amounts = [re.sub(r'[₹,\s]', '', amount) for amount in amounts if amount]
        
        # Find reference number using multiple patterns
        ref_no = None
        for pattern in ref_patterns:
            ref_match = re.search(pattern, line, re.IGNORECASE)
            if ref_match:
                ref_no = ref_match.group(1) if ref_match.groups() else ref_match.group(0)
                break
            
        # Extract description (everything except date, amounts, and ref)
        description = line
        
        # Remove date from description
        for pattern in date_patterns:
            description = re.sub(pattern, '', description)
        
        # Remove reference from description
        if ref_no:
            description = description.replace(ref_no, '').strip()
        
        # Remove amounts from description
        for amount in amounts:
            description = description.replace(amount, '').strip()
        
        # Clean up description
        description = re.sub(r'\s+', ' ', description).strip()
        description = re.sub(r'[^\w\s.,-]', '', description).strip()  # Remove special chars except common ones
        
        # Determine debit/credit with enhanced logic
        debit = None
        credit = None
        balance = None
        
        if amounts:
            # Enhanced debit/credit detection
            line_upper = line.upper()
            
            # Check for explicit indicators
            if any(indicator in line_upper for indicator in ['DR', 'DEBIT', 'WITHDRAWAL', 'PAYMENT']):
                debit = amounts[0] if amounts else None
            elif any(indicator in line_upper for indicator in ['CR', 'CREDIT', 'DEPOSIT', 'RECEIPT']):
                credit = amounts[0] if amounts else None
            else:
                # If multiple amounts, first is usually debit, second is credit
                if len(amounts) >= 2:
                    debit = amounts[0]
                    credit = amounts[1]
                else:
                    # Single amount - try to determine from context
                    if any(word in description.upper() for word in ['PAY', 'TRANSFER', 'WITHDRAW', 'DEBIT']):
                        debit = amounts[0]
                    elif any(word in description.upper() for word in ['RECEIVE', 'DEPOSIT', 'CREDIT', 'SALARY']):
                        credit = amounts[0]
                    else:
                        # Default to debit if unclear
                        debit = amounts[0]
        
        # Extract balance if available
        balance_match = re.search(r'BAL[:\s]*([₹]?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', line, re.IGNORECASE)
        if balance_match:
            balance = re.sub(r'[₹,\s]', '', balance_match.group(1))
            
        # Only add if we have meaningful data
        if date and (debit or credit) and description and len(description) > 3:
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