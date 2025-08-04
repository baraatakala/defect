#!/usr/bin/env python3
"""
Add sample reports to test navigation feature
"""
import sqlite3
import json
from datetime import datetime, timedelta
import random

def add_sample_reports():
    """Add sample reports to test navigation features"""
    
    db_path = 'defect_analysis.db'
    print(f"📄 Adding sample reports to {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
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
        
        # Add reports with different timestamps
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
        
        # Get total reports count
        cursor.execute('SELECT COUNT(*) FROM reports')
        total_reports = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(total_defects) FROM reports')
        total_defects = cursor.fetchone()[0] or 0
        
        conn.close()
        
        print("✅ Sample reports added successfully!")
        print(f"\n📊 Database now contains:")
        print(f"   📄 Total Reports: {total_reports}")
        print(f"   🚨 Total Defects: {total_defects}")
        print("\n🎯 Test the navigation features:")
        print("   1. Visit /reports to see all reports")
        print("   2. Click 'View' on any report")
        print("   3. Use Previous/Next navigation buttons")
        print("   4. Use 'View All Reports' to return to history")
        
    except Exception as e:
        print(f"❌ Error adding sample reports: {e}")

if __name__ == '__main__':
    add_sample_reports()
