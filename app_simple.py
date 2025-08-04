from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import json
import re
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'building_defect_detector_2025'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'docx', 'doc'}
ANALYTICS_FILE = 'analytics.json'

# Global analytics
analytics_data = {
    'total_reports': 0,
    'total_defects': 0,
    'reports_today': 0,
    'defect_categories': {},
    'severity_distribution': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0},
    'last_reset': datetime.now().strftime('%Y-%m-%d')
}

# Defect categories and keywords (simplified)
DEFECT_CATEGORIES = {
    'structural': ['crack', 'fracture', 'settlement', 'foundation', 'beam', 'wall', 'structural'],
    'moisture': ['damp', 'moisture', 'leak', 'water', 'mold', 'wet', 'condensation'],
    'electrical': ['electrical', 'wiring', 'socket', 'fuse', 'power', 'circuit'],
    'plumbing': ['pipe', 'plumbing', 'drain', 'toilet', 'water pressure', 'blockage'],
    'roofing': ['roof', 'tile', 'gutter', 'chimney', 'flashing', 'leak'],
    'safety': ['safety', 'hazard', 'dangerous', 'asbestos', 'fire', 'emergency'],
    'cosmetic': ['paint', 'decoration', 'cosmetic', 'appearance', 'finish']
}

SEVERITY_KEYWORDS = {
    'critical': ['urgent', 'immediate', 'critical', 'dangerous', 'severe'],
    'high': ['significant', 'major', 'serious', 'extensive', 'important'],
    'medium': ['moderate', 'noticeable', 'visible', 'needs attention'],
    'low': ['minor', 'cosmetic', 'superficial', 'small', 'slight']
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(filepath):
    """Simple text extraction - works with TXT files immediately"""
    try:
        with open(filepath, 'r', encoding='utf-8') as file:
            return file.read()
    except:
        try:
            with open(filepath, 'r', encoding='latin-1') as file:
                return file.read()
        except:
            return "Error reading file"

def detect_defects_simple(text):
    """Fast rule-based defect detection"""
    defects = []
    sentences = re.split(r'[.!?]+', text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 10:
            continue
        
        sentence_lower = sentence.lower()
        
        for category, keywords in DEFECT_CATEGORIES.items():
            for keyword in keywords:
                if keyword in sentence_lower:
                    # Quick severity detection
                    severity = 'medium'
                    for sev, sev_keywords in SEVERITY_KEYWORDS.items():
                        if any(kw in sentence_lower for kw in sev_keywords):
                            severity = sev
                            break
                    
                    defect = {
                        'category': category,
                        'severity': severity,
                        'description': sentence.strip()[:100] + '...',
                        'location': 'unspecified',
                        'confidence': 0.75
                    }
                    defects.append(defect)
                    break
    
    return defects

def analyze_defects(defects):
    """Quick analysis"""
    if not defects:
        return {
            'total_defects': 0,
            'category_distribution': {},
            'severity_distribution': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0},
            'recommendations': ['No defects detected']
        }
    
    category_dist = {}
    severity_dist = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
    
    for defect in defects:
        category_dist[defect['category']] = category_dist.get(defect['category'], 0) + 1
        severity_dist[defect['severity']] += 1
    
    recommendations = [
        f"Found {len(defects)} defects requiring attention",
        "Review high and critical priority items first",
        "Schedule professional inspection for structural issues",
        "Document all findings for maintenance planning"
    ]
    
    return {
        'total_defects': len(defects),
        'category_distribution': category_dist,
        'severity_distribution': severity_dist,
        'recommendations': recommendations
    }

@app.route('/')
def home():
    return render_template('index.html', analytics=analytics_data)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(url_for('home'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('home'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        try:
            # Extract text
            text = extract_text_from_file(filepath)
            
            if not text or text == "Error reading file":
                flash('Could not read file. Please try a TXT file for now.')
                os.remove(filepath)
                return redirect(url_for('home'))
            
            # Detect defects
            defects = detect_defects_simple(text)
            analysis = analyze_defects(defects)
            
            # Update analytics
            analytics_data['total_reports'] += 1
            analytics_data['reports_today'] += 1
            analytics_data['total_defects'] += len(defects)
            
            # Clean up
            os.remove(filepath)
            
            return render_template('results.html', 
                                 filename=filename,
                                 defects=defects,
                                 analysis=analysis,
                                 analytics=analytics_data)
        
        except Exception as e:
            flash(f'Error processing file: {str(e)}')
            if os.path.exists(filepath):
                os.remove(filepath)
            return redirect(url_for('home'))
    
    flash('Please upload a TXT file (PDF/DOCX support coming soon)')
    return redirect(url_for('home'))

@app.route('/analytics')
def analytics_dashboard():
    return render_template('analytics.html', analytics=analytics_data, recent_reports=[])

if __name__ == '__main__':
    print("🏗️ Building Defect Detector Starting...")
    print("🚀 Quick Demo Version - Upload TXT files to test!")
    print("📍 Access at: http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
