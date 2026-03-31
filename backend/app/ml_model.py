import logging
import os
from typing import Dict, List

import joblib
import numpy as np
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _normalize_risk_label(value: str) -> str:
    normalized = value.strip().lower()
    if normalized == "moderate":
        return "MEDIUM"
    if normalized == "high":
        return "HIGH"
    if normalized == "low":
        return "LOW"
    return value.upper()


class RiskPredictor:
    def __init__(self):
        self.classifier = None
        self.preprocessor = None
        self.label_encoder = None
        self.feature_config = None
        self.load_model()

    def load_model(self) -> None:
        try:
            classifier_path = os.getenv("CLASSIFIER_PATH", "../models/classifier.joblib")
            preprocessor_path = os.getenv(
                "PREPROCESSOR_PATH", "../models/preprocessor.joblib"
            )
            label_encoder_path = os.getenv(
                "LABEL_ENCODER_PATH", "../models/label_encoder.joblib"
            )
            feature_config_path = os.getenv(
                "FEATURE_CONFIG_PATH", "../models/feature_config.joblib"
            )

            if os.path.exists(classifier_path):
                self.classifier = joblib.load(classifier_path)
                self.preprocessor = joblib.load(preprocessor_path)
                self.label_encoder = joblib.load(label_encoder_path)
                self.feature_config = joblib.load(feature_config_path)
                logger.info("Model artifacts loaded successfully")
            else:
                logger.warning("Model artifacts not found. Using dummy model for testing.")
                self.classifier = None
        except Exception as exc:
            logger.error("Error loading model artifacts: %s", exc)
            self.classifier = None

    def _build_features(self, data: List[Dict]) -> pd.DataFrame:
        df = pd.DataFrame(data)

        base_features = [
            "attendance_percentage",
            "internal_marks",
            "assignment_submission_rate",
            "semester",
        ]
        for feature in base_features:
            if feature not in df.columns:
                df[feature] = 0

        df["engagement_score"] = (
            df["attendance_percentage"] * 0.6
            + df["assignment_submission_rate"] * 0.4
        )
        df["performance_index"] = df["internal_marks"] - df["engagement_score"]
        df["multiple_risk_flags"] = (
            (df["attendance_percentage"] < 75).astype(int)
            + (df["internal_marks"] < 60).astype(int)
            + (df["assignment_submission_rate"] < 70).astype(int)
        )

        all_features = (
            self.feature_config.get("all_features", base_features)
            if self.feature_config
            else base_features
        )

        df = df[all_features].fillna(df.mean(numeric_only=True))
        return df

    def predict(self, student_data: List[Dict]) -> List[Dict]:
        if not self.classifier:
            return self._dummy_predict(student_data)

        try:
            features = self._build_features(student_data)

            if self.preprocessor:
                features = self.preprocessor.transform(features)

            predictions = self.classifier.predict(features)
            probabilities = self.classifier.predict_proba(features)

            results = []
            for i, pred in enumerate(predictions):
                if self.label_encoder:
                    label = self.label_encoder.inverse_transform([pred])[0]
                else:
                    label = str(pred)

                risk_level = _normalize_risk_label(str(label))
                risk_score = float(max(probabilities[i]))

                results.append(
                    {
                        "risk_level": risk_level,
                        "risk_score": risk_score,
                        "student_id": student_data[i].get("student_id", f"STU{i}"),
                    }
                )

            return results
        except Exception as exc:
            logger.error("Prediction error: %s", exc)
            return self._dummy_predict(student_data)

    def _dummy_predict(self, student_data: List[Dict]) -> List[Dict]:
        results = []
        for i, student in enumerate(student_data):
            risk_score = 0

            if student.get("attendance_percentage", 100) < 75:
                risk_score += 0.35
            if student.get("internal_marks", 100) < 60:
                risk_score += 0.35
            if student.get("assignment_submission_rate", 100) < 70:
                risk_score += 0.3

            if risk_score > 0.6:
                risk_level = "HIGH"
            elif risk_score > 0.3:
                risk_level = "MEDIUM"
            else:
                risk_level = "LOW"

            results.append(
                {
                    "risk_level": risk_level,
                    "risk_score": risk_score,
                    "student_id": student.get("student_id", f"STU{i}"),
                }
            )

        return results


risk_predictor = RiskPredictor()
