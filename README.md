# PDF Text Extractor (Flask)

Minimal web app to extract text from PDF files with drag-and-drop upload.

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Open: http://localhost:5000

## Project structure
- app.py: Flask server and PDF extraction
- templates/index.html: UI markup
- static/style.css: Styles
- static/script.js: Minimal JS

## Push to GitHub
1. Initialize git and commit:
```bash
git init
git add .
git commit -m "Initial commit: minimal PDF extractor"
```
2. Create a repo on GitHub, then add remote and push:
```bash
git branch -M main
git remote add origin https://github.com/<your-username>/<repo>.git
git push -u origin main
```
