from flask import Flask, render_template, request, send_file, jsonify
import os, json
from werkzeug.utils import secure_filename
from glob import glob

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'py','json','txt','csv'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/projects')
def api_projects():
    with open('data/projects.json','r',encoding='utf8') as f:
        return jsonify(json.load(f))

@app.route('/api/reports/<vendor>/<project>')
def api_reports(vendor,project):
    folder = f'reports/{vendor}/{project}'
    files = [os.path.basename(f) for f in glob(f'{folder}/*.json') if os.path.isfile(f)]
    return jsonify(files)

@app.route('/api/report_json/<vendor>/<project>/<fname>')
def api_report_json(vendor,project,fname):
    path = f'reports/{vendor}/{project}/{fname}'
    with open(path,'r',encoding='utf8') as f:
        return jsonify(json.load(f))

@app.route('/api/scripts')
def api_scripts():
    return jsonify([f for f in os.listdir('autoscript') if f.endswith('.py')])

@app.route('/api/generate_report', methods=['POST'])
def api_generate_report():
    script = request.form.get('script')
    eye_height = request.form.get('eye_height')
    eye_width = request.form.get('eye_width')
    files = request.files.getlist('files')
    uploaded_files = []
    for file in files:
        if file and '.' in file.filename:
            fname = secure_filename(file.filename)
            fpath = os.path.join(UPLOAD_FOLDER, fname)
            file.save(fpath)
            uploaded_files.append(fpath)
    # 範例: 只產生靜態報告 (你可以改為呼叫 script 執行)
    report_path = os.path.join('reports', f'generated_report_{script}.html')
    with open(report_path, 'w', encoding='utf8') as f:
        f.write(f'<html><body><h1>Report for {script}</h1><p>Eye Height: {eye_height}</p><p>Eye Width: {eye_width}</p><p>Files: {", ".join(uploaded_files)}</p></body></html>')
    return send_file(report_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
