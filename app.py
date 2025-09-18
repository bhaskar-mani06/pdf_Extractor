from flask import Flask, render_template, request, jsonify
import pdfplumber

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract_text():
    try:
        # 1) Get uploaded file
        if 'pdf' not in request.files:
            return jsonify({'success': False, 'error': 'No file uploaded'})

        file = request.files['pdf']

        if not file or file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'})
        if not file.filename.lower().endswith('.pdf'):
            return jsonify({'success': False, 'error': 'Please upload a PDF file'})

        all_text = ""
        with pdfplumber.open(file) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                if text:
                    all_text += f"Page {i}\n{text}\n\n"

        return jsonify({'success': True, 'text': all_text.strip()})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
