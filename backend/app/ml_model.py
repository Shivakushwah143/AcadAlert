import joblib
import numpy as np
import pandas as pd
import os
from dotenv import load_dotenv
from typing import List, Dict
import logging

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RiskPredictor:
    def __init__(self):
        self.model = None
        self.scaler = None
        self.feature_names = [
            'attendance',
            'assignment_submission',
            'internal_marks',
            'participation_score',
            'backlogs',
            'study_hours'
        ]
        self.load_model()
    
    def load_model(self):
        """Load the trained model and scaler"""
        try:
            model_path = os.getenv("MODEL_PATH", "../ml_models/risk_model.pkl")
            scaler_path = os.getenv("SCALER_PATH", "../ml_models/scaler.pkl")
            
            # Try to load model, if not exists, create a dummy model for testing
            if os.path.exists(model_path):
                self.model = joblib.load(model_path)
                self.scaler = joblib.load(scaler_path)
                logger.info("✅ Model loaded successfully")
            else:
                logger.warning("⚠️ Model file not found. Using dummy model for testing.")
                self.model = None
                self.scaler = None
        except Exception as e:
            logger.error(f"❌ Error loading model: {e}")
            self.model = None
            self.scaler = None
    
    def preprocess(self, data: List[Dict]) -> np.ndarray:
        """Convert raw data to model input format"""
        df = pd.DataFrame(data)
        
        # Ensure all required features exist
        for feature in self.feature_names:
            if feature not in df.columns:
                df[feature] = 0
        
        # Select only required features in correct order
        df = df[self.feature_names]
        
        # Handle missing values
        df = df.fillna(df.mean())
        
        if self.scaler:
            # Scale the features
            scaled_data = self.scaler.transform(df)
            return scaled_data
        else:
            # Return raw data if scaler not available
            return df.values
    
    def predict(self, student_data: List[Dict]) -> List[Dict]:
        """Predict risk levels for students"""
        if not self.model:
            # Dummy predictions for testing
            return self._dummy_predict(student_data)
        
        try:
            # Preprocess data
            processed_data = self.preprocess(student_data)
            
            # Get predictions
            predictions = self.model.predict(processed_data)
            probabilities = self.model.predict_proba(processed_data)
            
            # Format results
            results = []
            for i, pred in enumerate(predictions):
                risk_mapping = {0: "LOW", 1: "MEDIUM", 2: "HIGH"}
                risk_level = risk_mapping.get(pred, "MEDIUM")
                risk_score = max(probabilities[i])  # Confidence score
                
                results.append({
                    "risk_level": risk_level,
                    "risk_score": float(risk_score),
                    "student_id": student_data[i].get("student_id", f"STU{i}")
                })
            
            return results
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return self._dummy_predict(student_data)
    
    def _dummy_predict(self, student_data: List[Dict]) -> List[Dict]:
        """Generate dummy predictions for testing when model is not available"""
        results = []
        for i, student in enumerate(student_data):
            # Simple rule-based risk calculation for demo
            risk_score = 0
            if student.get('attendance', 100) < 75:
                risk_score += 0.3
            if student.get('internal_marks', 100) < 60:
                risk_score += 0.3
            if student.get('assignment_submission', 100) < 70:
                risk_score += 0.2
            if student.get('backlogs', 0) > 2:
                risk_score += 0.2
            
            if risk_score > 0.6:
                risk_level = "HIGH"
            elif risk_score > 0.3:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"
            
            results.append({
                "risk_level": risk_level,
                "risk_score": risk_score,
                "student_id": student.get("student_id", f"STU{i}")
            })
        
        return results

# Create a global instance
risk_predictor = RiskPredictor()