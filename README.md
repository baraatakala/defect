# Building Defect Detector - AI Powered Building Survey Analysis

🏗️ **AI Application Building Challenge - Decoding Data Science Academy**

An intelligent web application that analyzes building survey reports to automatically detect and classify construction defects using Natural Language Processing (NLP) and Machine Learning techniques.

## 🚀 Features

### Core Functionality
- **Multi-Format File Support**: Upload PDF, DOCX, DOC, or TXT building survey reports
- **AI-Powered Analysis**: Automatic text extraction and defect detection using NLP
- **Smart Classification**: Categorizes defects into 10 main types (structural, moisture, electrical, etc.)
- **Risk Assessment**: Prioritizes defects by severity (critical, high, medium, low)
- **Location Detection**: Identifies where defects are located within the building
- **Confidence Scoring**: Provides confidence levels for each detected defect

### Interactive Dashboard
- **Visual Analytics**: Charts showing defect distribution and severity levels
- **Real-time Statistics**: Track total reports, defects detected, and daily activity
- **Detailed Reports**: Comprehensive analysis with actionable recommendations
- **Historical Data**: View past reports and track patterns over time

### Professional Features
- **Maintenance Recommendations**: AI-generated suggestions based on defect analysis
- **Priority System**: Urgent, high, medium, and low priority classifications
- **Export Capabilities**: Print-friendly reports for documentation
- **API Access**: RESTful API for integration with other systems

## 🎯 Target Audience

- **Civil Engineers & Building Inspectors**: Streamline technical audits and defect reporting
- **Property Consultants & Facility Managers**: Enhance property assessments and maintenance planning
- **Government Bodies & Regulatory Authorities**: Improve compliance tracking and oversight
- **Real Estate Professionals**: Support property evaluations and due diligence

## 🛠️ Technical Stack

### Backend
- **Framework**: Flask (Python)
- **NLP Processing**: spaCy, NLTK
- **File Processing**: PyPDF2, PyMuPDF, python-docx
- **Machine Learning**: scikit-learn (TF-IDF + Classification)
- **Database**: SQLite for data storage
- **API**: RESTful endpoints for programmatic access

### Frontend
- **UI Framework**: Bootstrap 5
- **Charts**: Chart.js for interactive visualizations
- **Icons**: Font Awesome
- **Responsive Design**: Mobile-friendly interface

### AI/ML Components
- **Text Extraction**: Handles PDF, DOCX, and text formats
- **Preprocessing**: Text cleaning and normalization
- **Feature Engineering**: TF-IDF vectorization with custom defect keywords
- **Classification**: Rule-based system with ML enhancement capability
- **Confidence Scoring**: Algorithmic confidence calculation

## 📁 Project Structure

```
building_defect_detector/
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── models/                # ML models and data
├── templates/             # HTML templates
│   ├── index.html         # Main upload page
│   ├── results.html       # Analysis results page
│   └── analytics.html     # Dashboard page
├── static/
│   └── style.css          # Custom CSS styling
├── uploads/               # Temporary file storage
└── sample_data/
    └── sample_building_survey.txt  # Test data
```

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Step 1: Clone/Download Project
```bash
git clone <repository-url>
cd building_defect_detector
```

### Step 2: Create Virtual Environment (Recommended)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Download spaCy Model
```bash
python -m spacy download en_core_web_sm
```

### Step 5: Run the Application
```bash
python app.py
```

Visit `http://localhost:5000` in your browser to access the application.

## 📊 How It Works

### 1. Upload Report
- Users upload building survey reports in PDF, DOCX, or text format
- Files are temporarily stored and processed securely

### 2. Text Extraction
- Advanced parsing extracts text from various document formats
- Handles complex layouts and formatting

### 3. AI Analysis
- NLP algorithms identify defect-related patterns in the text
- Classifies defects into predefined categories
- Determines severity levels based on contextual keywords

### 4. Results & Visualization
- Generates comprehensive analysis reports
- Creates interactive charts and visualizations
- Provides actionable maintenance recommendations

## 🔧 Defect Categories

The system identifies defects in these categories:

1. **Structural** - Cracks, foundation issues, settlement
2. **Moisture** - Damp, leaks, water damage, mold
3. **Electrical** - Wiring issues, safety hazards, faults
4. **Plumbing** - Pipe issues, drainage, water pressure
5. **Roofing** - Roof damage, tiles, guttering, flashing
6. **HVAC** - Heating, ventilation, air conditioning
7. **Insulation** - Thermal performance, energy efficiency
8. **Pest** - Infestations, woodworm, termites
9. **Safety** - Fire safety, asbestos, hazards
10. **Cosmetic** - Paint, decoration, minor finishes

## 📈 Severity Levels

- **Critical**: Urgent safety risks requiring immediate attention
- **High**: Significant issues needing professional assessment
- **Medium**: Noticeable problems requiring scheduled maintenance
- **Low**: Minor issues for planned maintenance

## 🧪 Testing

Use the provided sample data to test the system:

1. Start the application
2. Upload `sample_data/sample_building_survey.txt`
3. Review the analysis results and dashboard

## 🔌 API Usage

### Analyze Report Endpoint
```http
POST /api/analyze
Content-Type: multipart/form-data

file: [building_survey_file]
```

### Response Format
```json
{
    "filename": "survey_report.pdf",
    "total_defects": 15,
    "defects": [...],
    "analysis": {
        "category_distribution": {...},
        "severity_distribution": {...},
        "recommendations": [...]
    }
}
```

## 📋 Features Roadmap

### Current Release (v1.0)
- ✅ Multi-format file upload
- ✅ Rule-based defect detection
- ✅ Interactive dashboard
- ✅ Visual analytics
- ✅ Export capabilities

### Future Enhancements
- 🔄 Machine learning model training with labeled data
- 🔄 Advanced NLP using transformer models (BERT/GPT)
- 🔄 Integration with BIM systems
- 🔄 Mobile app development
- 🔄 Multi-language support
- 🔄 Real-time collaboration features

## 🤝 Contributing

This project was developed as part of the Decoding Data Science Academy AI Application Building Challenge. Contributions and improvements are welcome!

## 📄 License

This project is developed for educational purposes as part of the DDS Academy AI Challenge.

## 👥 Team

**Student Project** - Building Defect Detector Development Team
- Instructor Review Required
- Part of AI Application Building Challenge 2025

## 📞 Support

For questions or support regarding this AI application challenge project, please refer to the course materials or contact the academy instructors.

---

**Built with ❤️ for the Decoding Data Science Academy AI Application Building Challenge**
