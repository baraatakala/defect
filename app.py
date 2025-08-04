from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import os
import json
import pickle
import re
import string
from datetime import datetime
from werkzeug.utils import secure_filename
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
import sqlite3

# File processing imports
try:
    import PyPDF2
    import fitz  # PyMuPDF
    from docx import Document
    import spacy
    
    # Try to load spacy model with better error handling
    nlp = None
    try:
        nlp = spacy.load("en_core_web_sm")
        print("✅ SpaCy model loaded successfully")
    except OSError:
        print("⚠️ SpaCy model not found. Will try to download...")
        try:
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], 
                         check=True, capture_output=True)
            nlp = spacy.load("en_core_web_sm")
            print("✅ SpaCy model downloaded and loaded")
        except Exception as e:
            print(f"❌ Could not download spaCy model: {e}")
            print("Will use basic text processing without spaCy")
            nlp = None
            
except ImportError as e:
    print(f"❌ Some dependencies missing: {e}")
    print("Please install: pip install PyPDF2 PyMuPDF python-docx spacy")
    nlp = None

app = Flask(__name__)
app.secret_key = 'building_defect_detector_2025'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt'}
DATABASE = 'defect_analysis.db'
ANALYTICS_FILE = 'analytics.json'

# Global variables
model = None
vectorizer = None
analytics_data = {
    'total_reports': 0,
    'total_defects': 0,
    'reports_today': 0,
    'defect_categories': {},
    'severity_distribution': {'low': 0, 'medium': 0, 'high': 0, 'critical': 0},
    'last_reset': datetime.now().strftime('%Y-%m-%d')
}

# Defect categories and keywords
DEFECT_CATEGORIES = {
    'structural': ['crack', 'fracture', 'settlement', 'foundation', 'beam', 'column', 'wall', 'structural damage', 'subsidence'],
    'moisture': ['damp', 'moisture', 'leak', 'water damage', 'mold', 'mould', 'condensation', 'wet rot', 'dry rot'],
    'electrical': ['wiring', 'electrical', 'socket', 'switch', 'circuit', 'fuse', 'power', 'electrical fault'],
    'plumbing': ['pipe', 'plumbing', 'drain', 'toilet', 'sink', 'water pressure', 'blockage', 'tap'],
    'roofing': ['roof', 'tile', 'gutter', 'chimney', 'flashing', 'leak', 'roof damage', 'slate'],
    'hvac': ['heating', 'ventilation', 'air conditioning', 'hvac', 'boiler', 'radiator', 'vent'],
    'insulation': ['insulation', 'thermal', 'cold spot', 'draft', 'energy efficiency', 'heat loss'],
    'pest': ['pest', 'infestation', 'termite', 'rodent', 'insect', 'woodworm', 'beetle'],
    'safety': ['safety', 'hazard', 'dangerous', 'asbestos', 'lead paint', 'fire safety', 'emergency exit'],
    'cosmetic': ['paint', 'decoration', 'cosmetic', 'appearance', 'finish', 'surface']
}

SEVERITY_KEYWORDS = {
    'critical': ['urgent', 'immediate', 'critical', 'dangerous', 'severe', 'major structural', 'safety risk'],
    'high': ['significant', 'major', 'serious', 'extensive', 'widespread', 'important'],
    'medium': ['moderate', 'noticeable', 'minor structural', 'visible', 'needs attention'],
    'low': ['minor', 'cosmetic', 'superficial', 'small', 'slight', 'minimal']
}

def init_database():
    """Initialize SQLite database for storing reports and analysis"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create reports table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            file_type TEXT,
            total_defects INTEGER,
            analysis_data TEXT
        )
    ''')
    
    # Create defects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS defects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER,
            category TEXT,
            severity TEXT,
            description TEXT,
            location TEXT,
            confidence REAL,
            FOREIGN KEY (report_id) REFERENCES reports (id)
        )
    ''')
    
    conn.commit()
    conn.close()

def load_analytics():
    """Load analytics data from file"""
    global analytics_data
    try:
        if os.path.exists(ANALYTICS_FILE):
            with open(ANALYTICS_FILE, 'r') as f:
                analytics_data = json.load(f)
        
        # Reset daily counter if new day
        today = datetime.now().strftime('%Y-%m-%d')
        if analytics_data.get('last_reset') != today:
            analytics_data['reports_today'] = 0
            analytics_data['last_reset'] = today
            save_analytics()
    except Exception as e:
        print(f"Error loading analytics: {e}")

def save_analytics():
    """Save analytics data to file"""
    try:
        with open(ANALYTICS_FILE, 'w') as f:
            json.dump(analytics_data, f)
    except Exception as e:
        print(f"Error saving analytics: {e}")

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_file(filepath):
    """Extract text from uploaded file based on file type"""
    text = ""
    file_ext = filepath.rsplit('.', 1)[1].lower()
    
    try:
        if file_ext == 'pdf':
            # Try PyMuPDF first (better for complex PDFs)
            try:
                doc = fitz.open(filepath)
                for page in doc:
                    text += page.get_text()
                doc.close()
            except:
                # Fallback to PyPDF2
                with open(filepath, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        text += page.extract_text()
        
        elif file_ext in ['docx', 'doc']:
            doc = Document(filepath)
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
        
        elif file_ext == 'txt':
            with open(filepath, 'r', encoding='utf-8') as file:
                text = file.read()
    
    except Exception as e:
        print(f"Error extracting text from {filepath}: {e}")
        text = ""
    
    return text

def preprocess_text(text):
    """Preprocess text for analysis"""
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def detect_defects_rule_based(text):
    """Rule-based defect detection using keywords and patterns"""
    defects = []
    text_lower = text.lower()
    
    # Split text into sentences for better context
    sentences = re.split(r'[.!?]+', text)
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 10:  # Skip very short sentences
            continue
        
        sentence_lower = sentence.lower()
        
        # Check for defect categories
        for category, keywords in DEFECT_CATEGORIES.items():
            for keyword in keywords:
                if keyword in sentence_lower:
                    # Determine severity
                    severity = 'medium'  # default
                    for sev, sev_keywords in SEVERITY_KEYWORDS.items():
                        for sev_keyword in sev_keywords:
                            if sev_keyword in sentence_lower:
                                severity = sev
                                break
                    
                    # Extract location if possible
                    location = extract_location(sentence)
                    
                    # Calculate confidence based on keyword presence and context
                    confidence = calculate_confidence(sentence_lower, keyword, category)
                    
                    defect = {
                        'category': category,
                        'severity': severity,
                        'description': sentence.strip(),
                        'location': location,
                        'confidence': confidence,
                        'keyword_matched': keyword
                    }
                    defects.append(defect)
                    break  # Avoid duplicate detections for same sentence
    
    return defects

def extract_location(sentence):
    """Extract location information from sentence"""
    location_patterns = [
        r'(room \d+|bedroom \d+|bathroom \d+)',
        r'(kitchen|bathroom|bedroom|living room|basement|attic|garage)',
        r'(ground floor|first floor|second floor|third floor)',
        r'(north|south|east|west)\s+(wall|side)',
        r'(front|back|rear)\s+(wall|elevation)',
        r'(roof|ceiling|floor|wall)',
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, sentence.lower())
        if match:
            return match.group(1)
    
    return "unspecified"

def calculate_confidence(sentence, keyword, category):
    """Calculate confidence score for defect detection"""
    confidence = 0.5  # base confidence
    
    # Increase confidence for multiple relevant keywords
    category_keywords = DEFECT_CATEGORIES.get(category, [])
    keyword_count = sum(1 for kw in category_keywords if kw in sentence)
    confidence += min(keyword_count * 0.1, 0.3)
    
    # Increase confidence for severity indicators
    for severity_keywords in SEVERITY_KEYWORDS.values():
        if any(sev_kw in sentence for sev_kw in severity_keywords):
            confidence += 0.1
            break
    
    # Increase confidence for specific measurements or technical terms
    if re.search(r'\d+\s*(mm|cm|m|inch|inches|feet|ft)', sentence):
        confidence += 0.1
    
    return min(confidence, 0.95)  # Cap at 95%

def analyze_defects(defects):
    """Analyze detected defects and generate insights"""
    if not defects:
        return {
            'total_defects': 0,
            'category_distribution': {},
            'severity_distribution': {},
            'priority_defects': [],
            'recommendations': []
        }
    
    # Count by category
    category_dist = {}
    severity_dist = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
    
    for defect in defects:
        category = defect['category']
        severity = defect['severity']
        
        category_dist[category] = category_dist.get(category, 0) + 1
        severity_dist[severity] += 1
    
    # Identify priority defects (high confidence + high severity)
    priority_defects = [
        defect for defect in defects 
        if defect['severity'] in ['high', 'critical'] and defect['confidence'] > 0.7
    ]
    
    # Generate recommendations
    recommendations = generate_recommendations(category_dist, severity_dist)
    
    return {
        'total_defects': len(defects),
        'category_distribution': category_dist,
        'severity_distribution': severity_dist,
        'priority_defects': priority_defects[:5],  # Top 5 priority
        'recommendations': recommendations
    }

def generate_recommendations(category_dist, severity_dist):
    """Generate maintenance recommendations based on defect analysis"""
    recommendations = []
    
    # Critical/High severity recommendations
    if severity_dist['critical'] > 0:
        recommendations.append("⚠️ URGENT: Address critical defects immediately for safety")
    
    if severity_dist['high'] > 0:
        recommendations.append("🔴 HIGH: Schedule professional inspection for major defects")
    
    # Category-specific recommendations
    if category_dist.get('structural', 0) > 0:
        recommendations.append("🏗️ Structural: Consult structural engineer for assessment")
    
    if category_dist.get('moisture', 0) > 0:
        recommendations.append("💧 Moisture: Investigate sources and improve ventilation")
    
    if category_dist.get('electrical', 0) > 0:
        recommendations.append("⚡ Electrical: Have qualified electrician inspect wiring")
    
    if category_dist.get('safety', 0) > 0:
        recommendations.append("🛡️ Safety: Address safety hazards as priority")
    
    # General recommendations
    recommendations.append("📋 Document all repairs and maintain regular inspection schedule")
    recommendations.append("💰 Budget for medium/low priority items in maintenance plan")
    
    return recommendations

@app.route('/')
def home():
    """Serve the homepage"""
    return render_template('index.html', analytics=analytics_data)

@app.route('/health')
def health_check():
    """Health check endpoint for Railway"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'Building Defect Detector'
    }), 200

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handle file upload and analysis"""
    if 'file' not in request.files:
        flash('No file selected')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected')
        return redirect(url_for('home'))
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        try:
            # Extract text from file
            extracted_text = extract_text_from_file(filepath)
            
            if not extracted_text.strip():
                flash('Could not extract text from file. Please check file format.')
                os.remove(filepath)  # Clean up
                return redirect(url_for('home'))
            
            # Detect defects
            defects = detect_defects_rule_based(extracted_text)
            
            # Analyze defects
            analysis = analyze_defects(defects)
            
            # Update analytics
            analytics_data['total_reports'] += 1
            analytics_data['reports_today'] += 1
            analytics_data['total_defects'] += analysis['total_defects']
            
            # Update category counts
            for category, count in analysis['category_distribution'].items():
                analytics_data['defect_categories'][category] = analytics_data['defect_categories'].get(category, 0) + count
            
            # Update severity distribution
            for severity, count in analysis['severity_distribution'].items():
                analytics_data['severity_distribution'][severity] += count
            
            save_analytics()
            
            # Store in database
            conn = sqlite3.connect(DATABASE)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO reports (filename, file_type, total_defects, analysis_data)
                VALUES (?, ?, ?, ?)
            ''', (filename, filepath.rsplit('.', 1)[1].lower(), analysis['total_defects'], json.dumps(analysis)))
            
            report_id = cursor.lastrowid
            
            # Store individual defects
            for defect in defects:
                cursor.execute('''
                    INSERT INTO defects (report_id, category, severity, description, location, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (report_id, defect['category'], defect['severity'], 
                     defect['description'], defect['location'], defect['confidence']))
            
            conn.commit()
            conn.close()
            
            # Clean up uploaded file
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
    
    else:
        flash('Invalid file type. Please upload PDF, DOCX, or TXT files.')
        return redirect(url_for('home'))

@app.route('/analytics')
def analytics_dashboard():
    """Display analytics dashboard"""
    # Get recent reports from database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT filename, upload_date, total_defects 
        FROM reports 
        ORDER BY upload_date DESC 
        LIMIT 10
    ''')
    recent_reports = cursor.fetchall()
    
    conn.close()
    
    return render_template('analytics.html', 
                         analytics=analytics_data,
                         recent_reports=recent_reports)

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API endpoint for defect analysis"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type'}), 400
        
        # Save temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Extract and analyze
        text = extract_text_from_file(filepath)
        defects = detect_defects_rule_based(text)
        analysis = analyze_defects(defects)
        
        # Clean up
        os.remove(filepath)
        
        return jsonify({
            'filename': filename,
            'total_defects': len(defects),
            'defects': defects,
            'analysis': analysis
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Initialize
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    init_database()
    load_analytics()
    
    print("🏗️ Building Defect Detector Starting...")
    print("📊 Database initialized")
    print("📁 Upload folder ready")
    print("🚀 Server starting on http://localhost:5000")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
