#!/usr/bin/env python3
"""
Add sample AI training data to Building Defect Detector
This will populate the AI Training & Learning Performance metrics
"""
import sqlite3
import json
from datetime import datetime, timedelta
import random

def add_sample_training_data():
    """Add sample AI feedback and training data to the database"""
    
    # Connect to the database
    db_path = 'defect_analysis.db'
    print(f"📊 Adding sample training data to {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if tables exist, create if needed
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ai_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                defect_text TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                location TEXT NOT NULL,
                confidence REAL NOT NULL,
                feedback_type TEXT NOT NULL,
                user_session TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS defect_edits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                defect_index INTEGER NOT NULL,
                original_category TEXT NOT NULL,
                new_category TEXT NOT NULL,
                original_severity TEXT NOT NULL,
                new_severity TEXT NOT NULL,
                original_location TEXT NOT NULL,
                new_location TEXT NOT NULL,
                original_description TEXT NOT NULL,
                new_description TEXT NOT NULL,
                user_session TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Sample defect texts and data
        sample_defects = [
            {
                'text': 'Crack in bedroom wall near window frame',
                'category': 'structural',
                'severity': 'medium',
                'location': 'bedroom',
                'confidence': 0.85
            },
            {
                'text': 'Water stain on bathroom ceiling tiles',
                'category': 'plumbing',
                'severity': 'high',
                'location': 'bathroom',
                'confidence': 0.92
            },
            {
                'text': 'Peeling paint on exterior wall surface',
                'category': 'cosmetic',
                'severity': 'low',
                'location': 'exterior',
                'confidence': 0.78
            },
            {
                'text': 'Loose electrical outlet in kitchen area',
                'category': 'electrical',
                'severity': 'high',
                'location': 'kitchen',
                'confidence': 0.88
            },
            {
                'text': 'Damaged roof tiles visible from ground',
                'category': 'structural',
                'severity': 'critical',
                'location': 'roof',
                'confidence': 0.95
            },
            {
                'text': 'HVAC unit making unusual noise',
                'category': 'hvac',
                'severity': 'medium',
                'location': 'utility room',
                'confidence': 0.82
            },
            {
                'text': 'Missing safety railing on stairs',
                'category': 'safety',
                'severity': 'critical',
                'location': 'stairway',
                'confidence': 0.98
            },
            {
                'text': 'Window seal deterioration in living room',
                'category': 'structural',
                'severity': 'medium',
                'location': 'living room',
                'confidence': 0.75
            }
        ]
        
        # Add AI feedback data (correct/incorrect predictions)
        feedback_data = []
        for i, defect in enumerate(sample_defects):
            # Generate timestamps over the past 30 days
            days_ago = random.randint(1, 30)
            timestamp = datetime.now() - timedelta(days=days_ago)
            
            # 75% correct feedback, 25% incorrect
            feedback_type = 'correct' if random.random() < 0.75 else 'incorrect'
            
            feedback_data.append((
                defect['text'],
                defect['category'],
                defect['severity'], 
                defect['location'],
                defect['confidence'],
                feedback_type,
                f'user_session_{i % 5}',  # 5 different user sessions
                timestamp.isoformat()
            ))
        
        # Insert feedback data
        cursor.executemany('''
            INSERT INTO ai_feedback 
            (defect_text, category, severity, location, confidence, feedback_type, user_session, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', feedback_data)
        
        # Add some defect edit data
        edit_data = [
            (
                0, 'cosmetic', 'structural', 'low', 'medium', 
                'exterior', 'exterior wall', 
                'Peeling paint on exterior wall surface',
                'Structural crack with peeling paint on exterior wall surface',
                'user_session_1', datetime.now().isoformat()
            ),
            (
                1, 'electrical', 'electrical', 'medium', 'high',
                'kitchen', 'kitchen outlet',
                'Loose electrical outlet in kitchen area', 
                'Dangerous loose electrical outlet in kitchen area - immediate attention required',
                'user_session_2', datetime.now().isoformat()
            ),
            (
                2, 'hvac', 'hvac', 'low', 'medium',
                'utility room', 'HVAC system',
                'HVAC unit making unusual noise',
                'HVAC unit making grinding noise - possible bearing failure',
                'user_session_3', datetime.now().isoformat()
            )
        ]
        
        cursor.executemany('''
            INSERT INTO defect_edits 
            (defect_index, original_category, new_category, original_severity, new_severity,
             original_location, new_location, original_description, new_description, 
             user_session, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', edit_data)
        
        # Commit changes
        conn.commit()
        
        # Get statistics
        cursor.execute('SELECT COUNT(*) FROM ai_feedback')
        total_feedback = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM ai_feedback WHERE feedback_type = "correct"')
        correct_feedback = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM ai_feedback WHERE feedback_type = "incorrect"')
        incorrect_feedback = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM defect_edits')
        total_edits = cursor.fetchone()[0]
        
        accuracy_rate = (correct_feedback / total_feedback * 100) if total_feedback > 0 else 0
        
        print("✅ Sample training data added successfully!")
        print("\n📈 AI Training Metrics:")
        print(f"   👤 User Feedback: {total_feedback}")
        print(f"   ✅ Correct Predictions: {correct_feedback}")
        print(f"   ❌ Incorrect Predictions: {incorrect_feedback}")
        print(f"   📊 Accuracy Rate: {accuracy_rate:.1f}%")
        print(f"   ✏️ Defect Edits: {total_edits}")
        
        conn.close()
        
        print("\n🎯 Now visit the analytics page to see the updated metrics!")
        print("   http://127.0.0.1:5000/analytics")
        
    except Exception as e:
        print(f"❌ Error adding training data: {e}")

if __name__ == '__main__':
    add_sample_training_data()
