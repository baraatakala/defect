from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
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

# Enhanced defect categories with more specific keywords
DEFECT_CATEGORIES = {
    'structural': ['crack', 'fracture', 'settlement', 'foundation', 'beam', 'column', 'wall damage', 'structural damage', 'subsidence', 'structural failure', 'load bearing', 'foundation crack'],
    'moisture': ['damp', 'moisture', 'leak', 'water damage', 'mold', 'mould', 'condensation', 'wet rot', 'dry rot', 'water ingress', 'humidity', 'moisture content'],
    'electrical': ['wiring', 'electrical', 'socket', 'switch', 'circuit breaker', 'fuse', 'power', 'electrical fault', 'electrical hazard', 'short circuit', 'electrical panel'],
    'plumbing': ['pipe', 'plumbing', 'drain', 'toilet', 'sink', 'water pressure', 'blockage', 'tap', 'water supply', 'drainage', 'plumbing leak'],
    'roofing': ['roof', 'tile', 'gutter', 'chimney', 'flashing', 'roof leak', 'roof damage', 'slate', 'roof membrane', 'downspout', 'roof structure'],
    'hvac': ['heating', 'ventilation', 'air conditioning', 'hvac', 'boiler', 'radiator', 'vent', 'ahu', 'air handler', 'hvac system', 'climate control'],
    'insulation': ['insulation', 'thermal', 'cold spot', 'draft', 'energy efficiency', 'heat loss', 'thermal bridge', 'insulation gap', 'thermal performance'],
    'pest': ['pest', 'infestation', 'termite', 'rodent', 'insect', 'woodworm', 'beetle', 'pest control', 'pest damage', 'infestation evidence'],
    'safety': ['safety hazard', 'dangerous', 'asbestos', 'lead paint', 'fire safety', 'emergency exit', 'safety risk', 'hazardous material', 'safety concern', 'urgent risk'],
    'cosmetic': ['paint', 'decoration', 'cosmetic', 'appearance', 'finish', 'surface', 'aesthetic', 'painting', 'decorative', 'visual']
}

# Enhanced severity keywords with more specific indicators
SEVERITY_KEYWORDS = {
    'critical': ['urgent risk', 'immediate danger', 'critical', 'dangerous', 'severe', 'major structural', 'safety risk', 'structural failure', 'immediate attention', 'emergency'],
    'high': ['significant', 'major', 'serious', 'extensive', 'widespread', 'important', 'substantial', 'considerable', 'notable'],
    'medium': ['moderate', 'noticeable', 'minor structural', 'visible', 'needs attention', 'attention required', 'should be addressed'],
    'low': ['minor', 'cosmetic', 'superficial', 'small', 'slight', 'minimal', 'aesthetic', 'non-critical']
}

# Initialize app when module is loaded (for gunicorn)
def initialize_app():
    """Initialize the application for production deployment"""
    try:
        # Create upload directory
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        print(f"📁 Upload folder created: {UPLOAD_FOLDER}")
        
        # Initialize database
        init_database()
        print("📊 Database initialized")
        
        # Load analytics
        load_analytics()
        print("📈 Analytics loaded")
        
        print("✅ App initialization complete")
        
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        # Don't fail completely, continue with basic setup
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

def create_sample_data():
    """Create sample reports if database is empty (for demo purposes)"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Check if we already have reports
        cursor.execute('SELECT COUNT(*) FROM reports')
        count = cursor.fetchone()[0]
        
        if count > 0:
            print(f"📊 Database already has {count} reports, skipping sample data creation")
            conn.close()
            return
        
        print("📄 Creating sample reports for demo...")
        
        # Sample reports data
        sample_reports = [
            {
                'filename': 'residential_inspection_001.pdf',
                'file_type': 'pdf',
                'defects': [
                    {'category': 'structural', 'severity': 'high', 'description': 'Foundation crack in basement wall', 'location': 'basement', 'confidence': 0.92},
                    {'category': 'electrical', 'severity': 'medium', 'description': 'Outdated electrical panel needs upgrade', 'location': 'utility room', 'confidence': 0.85},
                    {'category': 'plumbing', 'severity': 'low', 'description': 'Minor leak under kitchen sink', 'location': 'kitchen', 'confidence': 0.78}
                ]
            },
            {
                'filename': 'commercial_building_survey.docx',
                'file_type': 'docx',
                'defects': [
                    {'category': 'hvac', 'severity': 'critical', 'description': 'HVAC system complete failure', 'location': 'main floor', 'confidence': 0.98},
                    {'category': 'safety', 'severity': 'high', 'description': 'Emergency exit blocked by storage', 'location': 'corridor', 'confidence': 0.95},
                    {'category': 'structural', 'severity': 'medium', 'description': 'Ceiling tile water damage', 'location': 'office area', 'confidence': 0.82},
                    {'category': 'electrical', 'severity': 'high', 'description': 'Exposed wiring in ceiling cavity', 'location': 'ceiling space', 'confidence': 0.88}
                ]
            },
            {
                'filename': 'apartment_maintenance_report.txt',
                'file_type': 'txt',
                'defects': [
                    {'category': 'cosmetic', 'severity': 'low', 'description': 'Paint peeling in bathroom', 'location': 'bathroom', 'confidence': 0.65},
                    {'category': 'plumbing', 'severity': 'medium', 'description': 'Low water pressure in shower', 'location': 'bathroom', 'confidence': 0.75}
                ]
            },
            {
                'filename': 'office_building_inspection.pdf',
                'file_type': 'pdf',
                'defects': [
                    {'category': 'structural', 'severity': 'critical', 'description': 'Load-bearing beam showing stress fractures', 'location': 'third floor', 'confidence': 0.96},
                    {'category': 'safety', 'severity': 'critical', 'description': 'Fire alarm system not functional', 'location': 'entire building', 'confidence': 0.99},
                    {'category': 'hvac', 'severity': 'medium', 'description': 'Air conditioning inefficient', 'location': 'upper floors', 'confidence': 0.80},
                    {'category': 'electrical', 'severity': 'low', 'description': 'Some fluorescent lights flickering', 'location': 'office spaces', 'confidence': 0.70},
                    {'category': 'plumbing', 'severity': 'medium', 'description': 'Water pressure issues on upper floors', 'location': 'restrooms', 'confidence': 0.77}
                ]
            },
            {
                'filename': 'warehouse_condition_report.pdf',
                'file_type': 'pdf',
                'defects': [
                    {'category': 'structural', 'severity': 'medium', 'description': 'Metal roof panels showing rust', 'location': 'roof', 'confidence': 0.83},
                    {'category': 'safety', 'severity': 'high', 'description': 'Damaged loading dock safety barriers', 'location': 'loading area', 'confidence': 0.90}
                ]
            }
        ]
        
        # Add reports with timestamps
        from datetime import datetime, timedelta
        import random
        
        for i, report_data in enumerate(sample_reports):
            # Generate timestamps spread over the past month
            days_ago = random.randint(1, 30)
            upload_date = datetime.now() - timedelta(days=days_ago)
            
            # Create analysis data
            defects = report_data['defects']
            severity_dist = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            category_dist = {}
            
            for defect in defects:
                severity_dist[defect['severity']] += 1
                category_dist[defect['category']] = category_dist.get(defect['category'], 0) + 1
            
            analysis_data = {
                'total_defects': len(defects),
                'severity_distribution': severity_dist,
                'category_distribution': category_dist,
                'priority_defects': [d for d in defects if d['severity'] in ['critical', 'high']]
            }
            
            # Insert report
            cursor.execute('''
                INSERT INTO reports (filename, upload_date, file_type, total_defects, analysis_data)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                report_data['filename'],
                upload_date.isoformat(),
                report_data['file_type'],
                len(defects),
                json.dumps(analysis_data)
            ))
            
            report_id = cursor.lastrowid
            
            # Insert defects
            for defect in defects:
                cursor.execute('''
                    INSERT INTO defects (report_id, category, severity, description, location, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    report_id,
                    defect['category'],
                    defect['severity'],
                    defect['description'],
                    defect['location'],
                    defect['confidence']
                ))
        
        conn.commit()
        conn.close()
        
        print("✅ Sample reports created for demo navigation testing")
        
    except Exception as e:
        print(f"❌ Error creating sample data: {e}")

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
    """Enhanced rule-based defect detection with deduplication and filtering"""
    defects = []
    text_lower = text.lower()
    
    # Filter out AI-generated summary sections
    filtered_text = filter_summary_sections(text)
    
    # Split text into sentences for better context
    sentences = re.split(r'[.!?]+', filtered_text)
    
    # Track processed sentences to avoid duplicates
    processed_sentences = set()
    
    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 15:  # Skip very short sentences
            continue
            
        # Skip if we've already processed a very similar sentence
        sentence_key = sentence.lower()[:50]  # First 50 chars as key
        if sentence_key in processed_sentences:
            continue
        processed_sentences.add(sentence_key)
        
        sentence_lower = sentence.lower()
        
        # Check for defect categories
        for category, keywords in DEFECT_CATEGORIES.items():
            for keyword in keywords:
                if keyword in sentence_lower:
                    # Determine severity with enhanced logic
                    severity = determine_severity(sentence_lower)
                    
                    # Enhanced location extraction
                    location = extract_location_enhanced(sentence)
                    
                    # Calculate confidence based on keyword presence and context
                    confidence = calculate_confidence_enhanced(sentence_lower, keyword, category)
                    
                    # Skip low-confidence detections
                    if confidence < 0.4:
                        continue
                    
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
    
    # Deduplicate defects based on similarity
    deduplicated_defects = deduplicate_defects(defects)
    
    return deduplicated_defects

def filter_summary_sections(text):
    """Filter out AI-generated summary sections and metadata"""
    # Remove lines that start with typical AI summary indicators
    lines = text.split('\n')
    filtered_lines = []
    
    skip_patterns = [
        r'🧠\s*(what to expect|ai|detector)',
        r'✅\s*(what it did well|areas)',
        r'⚠️\s*(areas that need)',
        r'📊\s*(analytics|dashboard)',
        r'🏁\s*(verdict|conclusion)',
        r'📈\s*(overall evaluation|metric)',
        r'would you like me to',
        r'ask chatgpt',
        r'this result is',
        r'with slight refinements'
    ]
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Skip lines that match AI summary patterns
        if any(re.search(pattern, line_lower) for pattern in skip_patterns):
            continue
            
        # Skip very short lines or metadata
        if len(line_lower) < 10:
            continue
            
        filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)

def extract_location_enhanced(sentence):
    """Enhanced location extraction with better pattern matching"""
    sentence_lower = sentence.lower()
    
    # More comprehensive location patterns
    location_patterns = [
        # Specific room identifiers
        r'(basement room \d+|room \d+[a-z]?|bedroom \d+|bathroom \d+)',
        r'(corridor \d+[a-z]?|hallway \d+[a-z]?|office \d+[a-z]?)',
        r'(unit \d+[a-z]?|apartment \d+[a-z]?|suite \d+[a-z]?)',
        
        # Equipment/system locations
        r'(rooftop ahu \d+|ahu \d+|boiler room|mechanical room)',
        r'(electrical room|server room|storage room)',
        
        # General areas
        r'(kitchen|bathroom|bedroom|living room|basement|attic|garage)',
        r'(lobby|entrance|stairwell|elevator|parking)',
        
        # Floor references
        r'(ground floor|first floor|second floor|third floor|\d+(st|nd|rd|th) floor)',
        
        # Directional/structural
        r'(north|south|east|west)\s+(wall|side|elevation|facade)',
        r'(front|back|rear)\s+(wall|elevation|entrance)',
        r'(exterior|interior)\s+(wall|surface)',
        
        # Building components
        r'(roof|ceiling|floor|wall|foundation|basement)',
    ]
    
    for pattern in location_patterns:
        match = re.search(pattern, sentence_lower)
        if match:
            return match.group(1).title()
    
    return "Unspecified"

def determine_severity(sentence):
    """Enhanced severity determination with priority scoring"""
    sentence_lower = sentence.lower()
    
    # Severity scoring system
    severity_scores = {
        'critical': 0,
        'high': 0,
        'medium': 0,
        'low': 0
    }
    
    # Score based on severity keywords
    for severity, keywords in SEVERITY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in sentence_lower:
                severity_scores[severity] += 1
    
    # Additional critical indicators
    critical_indicators = ['urgent risk', 'immediate danger', 'safety hazard', 'structural failure']
    if any(indicator in sentence_lower for indicator in critical_indicators):
        severity_scores['critical'] += 2
    
    # Find highest scoring severity
    max_score = max(severity_scores.values())
    if max_score == 0:
        return 'medium'  # default
    
    for severity, score in severity_scores.items():
        if score == max_score:
            return severity
    
    return 'medium'

def calculate_confidence_enhanced(sentence, keyword, category):
    """Enhanced confidence calculation with multiple factors"""
    confidence = 0.4  # base confidence
    
    # Factor 1: Multiple relevant keywords in same sentence
    category_keywords = DEFECT_CATEGORIES.get(category, [])
    keyword_count = sum(1 for kw in category_keywords if kw in sentence)
    confidence += min(keyword_count * 0.08, 0.25)
    
    # Factor 2: Severity indicators
    for severity_keywords in SEVERITY_KEYWORDS.values():
        if any(sev_kw in sentence for sev_kw in severity_keywords):
            confidence += 0.12
            break
    
    # Factor 3: Specific measurements or technical terms
    if re.search(r'\d+\s*(mm|cm|m|inch|inches|feet|ft|%|degrees?|°)', sentence):
        confidence += 0.1
    
    # Factor 4: Action words indicating actual defects
    action_words = ['damaged', 'broken', 'cracked', 'leaking', 'failing', 'deteriorated']
    if any(word in sentence for word in action_words):
        confidence += 0.15
    
    # Factor 5: Location specificity
    if "unspecified" not in extract_location_enhanced(sentence).lower():
        confidence += 0.08
    
    return min(confidence, 0.95)  # Cap at 95%

def deduplicate_defects(defects):
    """Remove duplicate or very similar defects"""
    if not defects:
        return defects
    
    unique_defects = []
    seen_descriptions = set()
    
    for defect in defects:
        # Create a normalized description for comparison
        desc_key = normalize_description(defect['description'])
        
        # Check if we've seen a similar description
        is_duplicate = False
        for seen_desc in seen_descriptions:
            if calculate_similarity(desc_key, seen_desc) > 0.8:
                is_duplicate = True
                break
        
        if not is_duplicate:
            unique_defects.append(defect)
            seen_descriptions.add(desc_key)
    
    return unique_defects

def normalize_description(description):
    """Normalize description for similarity comparison"""
    # Remove common words and punctuation
    import string
    desc = description.lower()
    desc = desc.translate(str.maketrans('', '', string.punctuation))
    
    # Remove common stopwords
    stopwords = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were']
    words = [word for word in desc.split() if word not in stopwords]
    
    return ' '.join(sorted(words))

def calculate_similarity(str1, str2):
    """Calculate similarity between two strings"""
    words1 = set(str1.split())
    words2 = set(str2.split())
    
    if not words1 and not words2:
        return 1.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0

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

# Initialize the application for production deployment
initialize_app()

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
    try:
        # Ensure upload directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        
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
            
            # Save file
            file.save(filepath)
            print(f"✅ File saved: {filepath}")
            
            try:
                # Extract text from file
                print(f"📄 Extracting text from: {filename}")
                extracted_text = extract_text_from_file(filepath)
                
                if not extracted_text.strip():
                    print("❌ No text extracted from file")
                    flash('Could not extract text from file. Please check file format.')
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    return redirect(url_for('home'))
                
                print(f"✅ Text extracted: {len(extracted_text)} characters")
                
                # Detect defects
                print("🔍 Detecting defects...")
                defects = detect_defects_rule_based(extracted_text)
                print(f"✅ Found {len(defects)} defects")
                
                # Analyze defects
                print("📊 Analyzing defects...")
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
                try:
                    print("💾 Storing in database...")
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
                    print("✅ Data stored successfully")
                    
                except Exception as db_error:
                    print(f"❌ Database error: {db_error}")
                    # Continue even if database fails
                
                # Clean up uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
                    print("🗑️ Cleaned up uploaded file")
                
                return render_template('results.html', 
                                     filename=filename,
                                     defects=defects,
                                     analysis=analysis,
                                     analytics=analytics_data)
            
            except Exception as processing_error:
                print(f"❌ Processing error: {processing_error}")
                flash(f'Error processing file: {str(processing_error)}')
                if os.path.exists(filepath):
                    os.remove(filepath)
                return redirect(url_for('home'))
        
        else:
            flash('Invalid file type. Please upload PDF, DOCX, or TXT files.')
            return redirect(url_for('home'))
            
    except Exception as general_error:
        print(f"❌ General error in upload: {general_error}")
        flash(f'Server error: {str(general_error)}')
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

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Handle user feedback for AI training"""
    try:
        data = request.get_json()
        
        # Store feedback in database
        conn = sqlite3.connect('defect_analysis.db')
        cursor = conn.cursor()
        
        # Create feedback table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                defect_text TEXT,
                category TEXT,
                severity TEXT,
                location TEXT,
                confidence REAL,
                feedback_type TEXT,
                user_session TEXT,
                timestamp TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert feedback
        cursor.execute('''
            INSERT INTO ai_feedback 
            (defect_text, category, severity, location, confidence, feedback_type, user_session, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('defect_text', ''),
            data.get('category', ''),
            data.get('severity', ''),
            data.get('location', ''),
            data.get('confidence', 0.0),
            data.get('feedback_type', ''),
            data.get('user_session', 'anonymous'),
            data.get('timestamp', datetime.now().isoformat())
        ))
        
        conn.commit()
        conn.close()
        
        # Update analytics
        update_training_analytics(data.get('feedback_type', ''))
        
        return jsonify({'success': True, 'message': 'Feedback recorded successfully'})
        
    except Exception as e:
        print(f"Error submitting feedback: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/edit-defect', methods=['POST'])
def edit_defect():
    """Handle defect editing for AI training"""
    try:
        data = request.get_json()
        
        # Store edit data in database for training
        conn = sqlite3.connect('defect_analysis.db')
        cursor = conn.cursor()
        
        # Create defect_edits table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS defect_edits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                defect_index INTEGER,
                original_category TEXT,
                new_category TEXT,
                original_severity TEXT,
                new_severity TEXT,
                original_location TEXT,
                new_location TEXT,
                original_description TEXT,
                new_description TEXT,
                user_session TEXT,
                timestamp TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Insert edit data
        cursor.execute('''
            INSERT INTO defect_edits 
            (defect_index, new_category, new_severity, new_location, new_description, user_session, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            data.get('defect_index', 0),
            data.get('category', ''),
            data.get('severity', ''),
            data.get('location', ''),
            data.get('description', ''),
            data.get('user_session', 'anonymous'),
            data.get('timestamp', datetime.now().isoformat())
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Defect edit recorded successfully'})
        
    except Exception as e:
        print(f"Error editing defect: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/training-data')
def get_training_data():
    """Get training data for ML model improvement"""
    try:
        conn = sqlite3.connect('defect_analysis.db')
        cursor = conn.cursor()
        
        # Get feedback data
        cursor.execute('''
            SELECT defect_text, category, severity, location, feedback_type, COUNT(*) as count
            FROM ai_feedback 
            GROUP BY defect_text, category, severity, location, feedback_type
            ORDER BY created_at DESC
        ''')
        feedback_data = cursor.fetchall()
        
        # Get edit data
        cursor.execute('''
            SELECT new_category, new_severity, new_location, new_description, COUNT(*) as count
            FROM defect_edits 
            GROUP BY new_category, new_severity, new_location, new_description
            ORDER BY created_at DESC
        ''')
        edit_data = cursor.fetchall()
        
        conn.close()
        
        return jsonify({
            'feedback_data': feedback_data,
            'edit_data': edit_data,
            'total_feedback': len(feedback_data),
            'total_edits': len(edit_data)
        })
        
    except Exception as e:
        print(f"Error getting training data: {e}")
        return jsonify({'error': str(e)}), 500

def update_training_analytics(feedback_type):
    """Update training analytics with new feedback"""
    try:
        global analytics_data
        
        if 'training_stats' not in analytics_data:
            analytics_data['training_stats'] = {
                'total_feedback': 0,
                'correct_feedback': 0,
                'incorrect_feedback': 0,
                'improvement_rate': 0.0
            }
        
        analytics_data['training_stats']['total_feedback'] += 1
        
        if feedback_type == 'correct':
            analytics_data['training_stats']['correct_feedback'] += 1
        elif feedback_type == 'incorrect':
            analytics_data['training_stats']['incorrect_feedback'] += 1
        
        # Calculate improvement rate
        total = analytics_data['training_stats']['total_feedback']
        correct = analytics_data['training_stats']['correct_feedback']
        analytics_data['training_stats']['improvement_rate'] = (correct / total * 100) if total > 0 else 0
        
        # Save analytics
        save_analytics()
        
    except Exception as e:
        print(f"Error updating training analytics: {e}")

@app.route('/reports')
def reports_history():
    """Show history of all analyzed reports with navigation"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get all reports with their defect counts
        cursor.execute('''
            SELECT r.id, r.filename, r.upload_date, r.file_type, r.total_defects,
                   COUNT(d.id) as actual_defects
            FROM reports r
            LEFT JOIN defects d ON r.id = d.report_id
            GROUP BY r.id, r.filename, r.upload_date, r.file_type, r.total_defects
            ORDER BY r.upload_date DESC
        ''')
        
        reports = []
        for row in cursor.fetchall():
            reports.append({
                'id': row[0],
                'filename': row[1],
                'upload_date': row[2],
                'file_type': row[3],
                'total_defects': row[4] or row[5],  # Use stored count or actual count
                'actual_defects': row[5]
            })
        
        conn.close()
        
        return render_template('reports_history.html', 
                             reports=reports,
                             analytics=analytics_data)
        
    except Exception as e:
        print(f"Error loading reports history: {e}")
        return render_template('reports_history.html', 
                             reports=[],
                             error="Could not load reports history",
                             analytics=analytics_data)

@app.route('/report/<int:report_id>')
def view_report(report_id):
    """View a specific report with navigation controls"""
    try:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        
        # Get report details
        cursor.execute('''
            SELECT id, filename, upload_date, file_type, total_defects, analysis_data
            FROM reports WHERE id = ?
        ''', (report_id,))
        
        report_row = cursor.fetchone()
        if not report_row:
            flash('Report not found', 'error')
            return redirect(url_for('reports_history'))
        
        # Get defects for this report
        cursor.execute('''
            SELECT category, severity, description, location, confidence
            FROM defects WHERE report_id = ?
            ORDER BY severity DESC, confidence DESC
        ''', (report_id,))
        
        defects = []
        for row in cursor.fetchall():
            defects.append({
                'category': row[0],
                'severity': row[1], 
                'description': row[2],
                'location': row[3],
                'confidence': row[4] or 0.5,
                'text': row[2]  # For feedback compatibility
            })
        
        # Get navigation info (previous/next reports)
        cursor.execute('SELECT id FROM reports WHERE id < ? ORDER BY id DESC LIMIT 1', (report_id,))
        prev_report = cursor.fetchone()
        prev_id = prev_report[0] if prev_report else None
        
        cursor.execute('SELECT id FROM reports WHERE id > ? ORDER BY id ASC LIMIT 1', (report_id,))
        next_report = cursor.fetchone()
        next_id = next_report[0] if next_report else None
        
        conn.close()
        
        # Parse analysis data if available
        analysis_data = None
        if report_row[5]:  # analysis_data column
            try:
                analysis_data = json.loads(report_row[5])
            except:
                analysis_data = None
        
        # Create analysis object for template compatibility
        if not analysis_data:
            # Generate analysis from defects
            severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            category_counts = {}
            
            for defect in defects:
                severity_counts[defect['severity']] = severity_counts.get(defect['severity'], 0) + 1
                category_counts[defect['category']] = category_counts.get(defect['category'], 0) + 1
            
            analysis_data = {
                'total_defects': len(defects),
                'severity_distribution': severity_counts,
                'category_distribution': category_counts,
                'priority_defects': [d for d in defects if d['severity'] in ['critical', 'high']],
                'recommendations': generate_recommendations(defects)
            }
        
        return render_template('results.html',
                             filename=report_row[1],
                             analysis=analysis_data,
                             defects=defects,
                             analytics=analytics_data,
                             # Navigation data
                             report_id=report_id,
                             prev_report_id=prev_id,
                             next_report_id=next_id,
                             is_historical=True)
        
    except Exception as e:
        print(f"Error loading report {report_id}: {e}")
        flash('Error loading report', 'error')
        return redirect(url_for('reports_history'))

def generate_recommendations(defects):
    """Generate recommendations based on defects"""
    recommendations = []
    
    # Count defects by category
    categories = {}
    for defect in defects:
        cat = defect['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    # Generate category-specific recommendations
    if categories.get('structural', 0) > 0:
        recommendations.append("Schedule structural engineer inspection for foundation and load-bearing elements")
    
    if categories.get('electrical', 0) > 0:
        recommendations.append("Arrange certified electrician evaluation for electrical safety compliance")
    
    if categories.get('plumbing', 0) > 0:
        recommendations.append("Contact licensed plumber for water system and drainage assessment")
    
    if categories.get('hvac', 0) > 0:
        recommendations.append("Schedule HVAC technician service for heating and cooling system maintenance")
    
    if categories.get('safety', 0) > 0:
        recommendations.append("Address safety hazards immediately to prevent accidents and ensure compliance")
    
    if categories.get('cosmetic', 0) > 0:
        recommendations.append("Plan cosmetic repairs to maintain property value and appearance")
    
    # Add general recommendations
    if len(defects) > 5:
        recommendations.append("Consider comprehensive building inspection due to multiple defects identified")
    
    return recommendations

if __name__ == '__main__':
    # Initialize
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    init_database()
    create_sample_data()  # Create sample reports for demo
    load_analytics()
    
    print("🏗️ Building Defect Detector Starting...")
    print("📊 Database initialized")
    print("📁 Upload folder ready")
    
    # Use Railway's PORT environment variable or default to 5001 for local development
    port = int(os.environ.get('PORT', 5001))
    print(f"🚀 Server starting on port {port}")
    
    app.run(debug=True, host='0.0.0.0', port=port)
