"""
Building Defect Detector - Training Script
This script demonstrates how to train a machine learning model for defect classification
when labeled training data becomes available.
"""

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
import pickle
import os

# Sample training data for demonstration
# In a real scenario, this would come from labeled building survey reports
SAMPLE_TRAINING_DATA = [
    # Structural defects
    ("Visible crack in the main supporting wall extending vertically", "structural", "high"),
    ("Foundation settlement detected in southwest corner", "structural", "critical"),
    ("Minor hairline cracks in plaster around window frame", "structural", "low"),
    ("Significant structural movement evident in load-bearing beam", "structural", "critical"),
    
    # Moisture defects  
    ("Damp patches visible on north-facing wall with high moisture readings", "moisture", "high"),
    ("Water ingress through roof causing ceiling damage", "moisture", "high"),
    ("Minor condensation issues in bathroom area", "moisture", "medium"),
    ("Severe mold growth due to persistent water leak", "moisture", "critical"),
    
    # Electrical defects
    ("Exposed electrical wiring poses immediate safety hazard", "electrical", "critical"),
    ("Outdated fuse box requires upgrade to current standards", "electrical", "high"),
    ("Loose electrical socket in kitchen area", "electrical", "medium"),
    ("Electrical installation generally satisfactory", "electrical", "low"),
    
    # Plumbing defects
    ("Major water leak in upstairs bathroom affecting ceiling below", "plumbing", "high"),
    ("Poor water pressure throughout property", "plumbing", "medium"),
    ("Minor dripping tap in utility room", "plumbing", "low"),
    ("Blocked drainage system causing backup", "plumbing", "high"),
    
    # Roofing defects
    ("Missing roof tiles allowing water penetration", "roofing", "high"),
    ("Damaged flashing around chimney area", "roofing", "medium"),
    ("Guttering requires cleaning and minor repairs", "roofing", "low"),
    ("Severe roof damage with immediate water ingress risk", "roofing", "critical"),
    
    # HVAC defects
    ("Boiler approaching end of service life", "hvac", "medium"),
    ("Inadequate ventilation causing condensation", "hvac", "medium"),
    ("Heating system not functioning in bedroom areas", "hvac", "high"),
    ("Air conditioning unit requires servicing", "hvac", "low"),
    
    # Safety defects
    ("No smoke alarms installed throughout property", "safety", "critical"),
    ("Potential asbestos materials in roof structure", "safety", "high"),
    ("Unsafe stair railings require immediate attention", "safety", "critical"),
    ("Fire exit blocked by stored materials", "safety", "high"),
    
    # Cosmetic defects
    ("Paint work requires refreshing throughout", "cosmetic", "low"),
    ("Minor scuff marks on walls", "cosmetic", "low"),
    ("Wallpaper peeling in hallway area", "cosmetic", "low"),
    ("Kitchen tiles show signs of wear", "cosmetic", "low"),
]

def create_training_dataset():
    """Create a training dataset from sample data"""
    data = []
    labels_category = []
    labels_severity = []
    
    for text, category, severity in SAMPLE_TRAINING_DATA:
        data.append(text)
        labels_category.append(category)
        labels_severity.append(severity)
    
    return data, labels_category, labels_severity

def train_category_classifier():
    """Train a classifier for defect categories"""
    print("Training defect category classifier...")
    
    # Get training data
    texts, categories, severities = create_training_dataset()
    
    # Create TF-IDF vectorizer with custom parameters for building defects
    vectorizer = TfidfVectorizer(
        max_features=1000,
        stop_words='english',
        ngram_range=(1, 2),  # Include bigrams for better context
        min_df=1,
        max_df=0.8
    )
    
    # Transform texts to feature vectors
    X = vectorizer.fit_transform(texts)
    y = categories
    
    # Split data for validation
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    # Train Random Forest classifier
    rf_classifier = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        class_weight='balanced'
    )
    rf_classifier.fit(X_train, y_train)
    
    # Evaluate the model
    train_score = rf_classifier.score(X_train, y_train)
    test_score = rf_classifier.score(X_test, y_test)
    
    print(f"Category Classifier Performance:")
    print(f"Training Accuracy: {train_score:.3f}")
    print(f"Testing Accuracy: {test_score:.3f}")
    
    # Cross-validation
    cv_scores = cross_val_score(rf_classifier, X, y, cv=3)
    print(f"Cross-validation Score: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
    
    return rf_classifier, vectorizer

def train_severity_classifier():
    """Train a classifier for defect severity levels"""
    print("\nTraining defect severity classifier...")
    
    # Get training data
    texts, categories, severities = create_training_dataset()
    
    # Create separate vectorizer for severity
    vectorizer = TfidfVectorizer(
        max_features=800,
        stop_words='english',
        ngram_range=(1, 2),
        min_df=1
    )
    
    # Transform texts to feature vectors
    X = vectorizer.fit_transform(texts)
    y = severities
    
    # Split data for validation
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.3, random_state=42, stratify=y
    )
    
    # Train Logistic Regression classifier
    lr_classifier = LogisticRegression(
        random_state=42,
        class_weight='balanced',
        max_iter=1000
    )
    lr_classifier.fit(X_train, y_train)
    
    # Evaluate the model
    train_score = lr_classifier.score(X_train, y_train)
    test_score = lr_classifier.score(X_test, y_test)
    
    print(f"Severity Classifier Performance:")
    print(f"Training Accuracy: {train_score:.3f}")
    print(f"Testing Accuracy: {test_score:.3f}")
    
    # Cross-validation
    cv_scores = cross_val_score(lr_classifier, X, y, cv=3)
    print(f"Cross-validation Score: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")
    
    return lr_classifier, vectorizer

def save_models(category_model, category_vectorizer, severity_model, severity_vectorizer):
    """Save trained models and vectorizers"""
    os.makedirs('models', exist_ok=True)
    
    # Save category classifier
    with open('models/category_classifier.pkl', 'wb') as f:
        pickle.dump(category_model, f)
    
    with open('models/category_vectorizer.pkl', 'wb') as f:
        pickle.dump(category_vectorizer, f)
    
    # Save severity classifier
    with open('models/severity_classifier.pkl', 'wb') as f:
        pickle.dump(severity_model, f)
    
    with open('models/severity_vectorizer.pkl', 'wb') as f:
        pickle.dump(severity_vectorizer, f)
    
    print("\nModels saved successfully!")
    print("- models/category_classifier.pkl")
    print("- models/category_vectorizer.pkl") 
    print("- models/severity_classifier.pkl")
    print("- models/severity_vectorizer.pkl")

def test_models():
    """Test the trained models with sample predictions"""
    print("\nTesting trained models...")
    
    # Load models
    with open('models/category_classifier.pkl', 'rb') as f:
        category_model = pickle.load(f)
    
    with open('models/category_vectorizer.pkl', 'rb') as f:
        category_vectorizer = pickle.load(f)
    
    with open('models/severity_classifier.pkl', 'rb') as f:
        severity_model = pickle.load(f)
    
    with open('models/severity_vectorizer.pkl', 'rb') as f:
        severity_vectorizer = pickle.load(f)
    
    # Test samples
    test_samples = [
        "Large crack in the basement wall requires urgent attention",
        "Minor paint peeling in the hallway area",
        "Electrical wiring exposed creating safety hazard",
        "Roof tiles missing causing water ingress"
    ]
    
    print("\nSample Predictions:")
    print("-" * 50)
    
    for sample in test_samples:
        # Predict category
        cat_features = category_vectorizer.transform([sample])
        category_pred = category_model.predict(cat_features)[0]
        category_proba = category_model.predict_proba(cat_features)[0].max()
        
        # Predict severity
        sev_features = severity_vectorizer.transform([sample])
        severity_pred = severity_model.predict(sev_features)[0]
        severity_proba = severity_model.predict_proba(sev_features)[0].max()
        
        print(f"Text: {sample}")
        print(f"Category: {category_pred} (confidence: {category_proba:.2f})")
        print(f"Severity: {severity_pred} (confidence: {severity_proba:.2f})")
        print("-" * 50)

def main():
    """Main training pipeline"""
    print("Building Defect Detector - Model Training")
    print("=" * 50)
    
    # Train classifiers
    category_model, category_vectorizer = train_category_classifier()
    severity_model, severity_vectorizer = train_severity_classifier()
    
    # Save models
    save_models(category_model, category_vectorizer, severity_model, severity_vectorizer)
    
    # Test models
    test_models()
    
    print("\nTraining completed successfully!")
    print("You can now use these models in the main application for enhanced accuracy.")

if __name__ == "__main__":
    main()
