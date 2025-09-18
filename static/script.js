document.addEventListener('DOMContentLoaded', () => {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const extractBtn = document.getElementById('extractBtn');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const textContent = document.getElementById('textContent');
    const error = document.getElementById('error');
    const errorMessage = document.getElementById('errorMessage');

    let selectedFile = null;

    uploadArea.addEventListener('dragover', (e) => e.preventDefault());
    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
    });
    uploadArea.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) handleFile(e.target.files[0]);
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
            const res = await fetch('/extract', { method: 'POST', body: formData });
            const data = await res.json();

            if (!res.ok || !data.success) throw new Error(data.error || 'Failed to extract');
            textContent.textContent = data.text;
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
