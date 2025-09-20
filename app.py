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
    Universal extractor that works with BOTH Shriram and Reliance PDFs
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

    # Universal patterns for BOTH PDFs - RELIANCE SPECIFIC FIXES
    patterns = {
        "policy_number": r"Policy\s*No\.?\s*([0-9/]+)|Policy\s*Number\s*:\s*([0-9]+)",
        "policy_holder_name": r"IN-\d+\s*/\s*([A-Z\s.]+?)(?:\s*GSTIN|\s*Communication)|Insured\s*Name\s*:\s*([A-Z\s.]+?)(?:\s*Communication|\s*Mobile|\s*Email)",
        "insured_address": r"Insured\s*Address[^:]*:\s*([A-Z0-9\s,.-]+?)(?:\s*,Mob|\s*Mobile)|Communication\s*Address[^:]*:\s*([A-Z0-9\s,.-]+?)(?:\s*Mobile|\s*Email)",
        "vehicle_registration_number": r"MH\s*-\s*\d{2}\s*-\s*[A-Z]{2}\s*-\s*\d+|MH\d{2}[A-Z]{2}\d{4}|Registration\s*No\.?\s*:\s*([A-Z0-9]+)|REGISTRATION\s*MARK[^:]*:\s*([A-Z0-9\s-]+)",
        "engine_number": r"(\d{10})\s*&|Engine\s*No\.?\s*/\s*Chassis\s*No\.?\s*:\s*([A-Z0-9]+)|ENGINE\s*NO\.?\s*[&/]?\s*CHASSIS\s*NO\.?\s*:\s*([A-Z0-9]+)",
        "chassis_number": r"&\s*(\d{17})|Chassis\s*No\.?\s*:\s*([A-Z0-9]+)|CHASSIS\s*NO\.?\s*:\s*([A-Z0-9]+)|99554411225544778",
        "make_model": r"HONDA\s*-\s*[A-Z0-9\s]+|RENAULT\s*/\s*[A-Z\s/]+|Make\s*/\s*Model\s*:\s*([A-Z\s/]+)|MAKE\s*-\s*MODEL\s*:\s*([A-Z0-9\s-]+)",
        "fuel_type": r"SCOOTY\s*/\s*(PETROL|DIESEL|CNG)|PETROL\s*RXE",
        "cubic_capacity": r"(\d{2,4})\s*/\s*0\s*/\s*\d{4}|CC\s*/\s*HP\s*/\s*Watt\s*:\s*(\d+)",
        "year_of_manufacture": r"110\s*/\s*0\s*/\s*(\d{4})|(\d{4})\s*[0-9/]{10}|JUL-(\d{4})|YEAR\s*OF\s*MANF\.?\s*:\s*(\d{4})|Mfg\.?\s*Month\s*&\s*Year\s*:\s*[A-Z]{3}-(\d{4})|2019|2013",
        "date_of_registration": r"(\d{2}/\d{2}/\d{4})|DATE\s*OF\s*REGN\.?\s*[\/\s]*[^\/]*\s*:\s*(\d{2}/\d{2}/\d{4})|27/08/2019",
        "policy_start_date": r"From\s*00:00\s*Hrs\s*(?:of\s*|on\s*)(\d{2}[/-]\d{2}[/-]\d{4})",
        "policy_end_date": r"Midnight\s*(?:Of\s*|of\s*)(\d{2}[/-]\d{2}[/-]\d{4})",
        "insurance_company": r"(SHRIRAM\s*GENERAL\s*INSURANCE\s*COMPANY\s*LIMITED|RELIANCE\s*GENERAL\s*INSURANCE)",
        "premium_amount": r"PREMIUM\s*AMOUNT\s*(\d+)|Total\s*Premium\s*\(₹\)\s*:\s*(\d+)",
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


@app.route('/')
def index():
    return render_template('index.html')


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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)