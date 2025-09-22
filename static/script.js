document.addEventListener('DOMContentLoaded', () => {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const extractBtn = document.getElementById('extractBtn');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const textContent = document.getElementById('textContent');
    const jsonContent = document.getElementById('jsonContent');
    const summary = document.getElementById('summary');
    const error = document.getElementById('error');
    const errorMessage = document.getElementById('errorMessage');

    let selectedFile = null;

    // Drag and drop functionality
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.classList.remove('drag-over');
        if (e.dataTransfer.files.length) {
            handleFile(e.dataTransfer.files[0]);
        }
    });

    uploadArea.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) {
            handleFile(e.target.files[0]);
        }
    });

    function handleFile(file) {
        if (!file.name.toLowerCase().endsWith('.pdf')) {
            showError('Please select a PDF file.');
            return;
        }
        selectedFile = file;
        fileName.textContent = file.name;
        fileInfo.style.display = 'block';
        error.style.display = 'none';
        results.style.display = 'none';
    }

    extractBtn.addEventListener('click', () => {
        if (!selectedFile) return showError('Please select a PDF file first.');
        extractText(selectedFile);
    });

    async function extractText(file) {
        try {
            loading.style.display = 'block';
            results.style.display = 'none';
            error.style.display = 'none';
            extractBtn.disabled = true;

            const formData = new FormData();
            formData.append('pdf', file);
            
            // Determine which endpoint to use based on filename
            let endpoint = '/extract'; // Default universal extractor
            if (file.name.toLowerCase().includes('kotak')) {
                endpoint = '/extract-kotak';
            } else if (file.name.toLowerCase().includes('sbi')) {
                endpoint = '/extract-sbi';
            }
            
            const res = await fetch(endpoint, { method: 'POST', body: formData });
            const data = await res.json();

            if (!res.ok || !data.success) {
                throw new Error(data.error || 'Failed to extract data');
            }

            // Show summary
            summary.innerHTML = `
                <div class="summary-card">
                    <h3>Extraction Summary</h3>
                    <div class="summary-stats">
                        <div class="stat">
                            <span class="stat-label">File:</span>
                            <span class="stat-value">${file.name}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Text Length:</span>
                            <span class="stat-value">${data.text_length.toLocaleString()} characters</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Fields Extracted:</span>
                            <span class="stat-value">${data.filled_fields}/${data.total_fields}</span>
                        </div>
                        <div class="stat">
                            <span class="stat-label">Success Rate:</span>
                            <span class="stat-value">${Math.round((data.filled_fields/data.total_fields)*100)}%</span>
                        </div>
                    </div>
                </div>
            `;

            // Show extracted text (full text)
            textContent.innerHTML = `
                <div class="text-preview">
                    <h4>Complete PDF Text (${data.text_length.toLocaleString()} characters):</h4>
                    <pre>${data.text}</pre>
                </div>
            `;

            // Show extracted JSON data
            const extractedJson = data.extracted_json || {};
            const filledFields = Object.entries(extractedJson).filter(([key, value]) => value && value.trim());
            const emptyFields = Object.entries(extractedJson).filter(([key, value]) => !value || !value.trim());

            jsonContent.innerHTML = `
                <div class="json-section">
                    <h4>✅ Successfully Extracted Fields (${filledFields.length}):</h4>
                    <div class="json-filled">
                        <pre>${JSON.stringify(Object.fromEntries(filledFields), null, 2)}</pre>
                    </div>
                </div>
                ${emptyFields.length > 0 ? `
                <div class="json-section">
                    <h4>⚠️ Empty Fields (${emptyFields.length}):</h4>
                    <div class="json-empty">
                        <pre>${JSON.stringify(Object.fromEntries(emptyFields), null, 2)}</pre>
                    </div>
                </div>
                ` : ''}
                <div class="json-section">
                    <h4>📋 Complete JSON Data:</h4>
                    <div class="json-complete">
                        <pre>${JSON.stringify(extractedJson, null, 2)}</pre>
                    </div>
                </div>
            `;

            results.style.display = 'block';
        } catch (err) {
            showError(err.message);
        } finally {
            loading.style.display = 'none';
            extractBtn.disabled = false;
        }
    }

    function showError(message) {
        errorMessage.textContent = message;
        error.style.display = 'block';
        results.style.display = 'none';
    }
});