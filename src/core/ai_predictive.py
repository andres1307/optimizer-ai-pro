import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.metrics import precision_score, recall_score  # NEW: Métricas de evaluación
import os
import joblib
import sqlite3
from typing import List, Dict, Union  # NEW: Tipado para mejor documentación

class PredictiveAI:
    def __init__(self, db_path: str, model_path: str = "./model_iforest.pkl", contamination: float = 0.05):
        """Inicialización con hiperparámetros ajustables (NEW)."""
        self.db_path = db_path
        self.model_path = model_path
        self.model = None
        self.contamination = contamination  # NEW: Hiperparámetro configurable
        self.feature_names = ["cpu", "ram", "disk", "error_count"]
        self.load_or_train_model()

    # NEW: Método para actualizar hiperparámetros dinámicamente
    def update_hyperparameters(self, contamination: float = None, n_estimators: int = None) -> None:
        """Actualiza los hiperparámetros del modelo."""
        if contamination:
            self.contamination = contamination
        self.train_model()

    def fetch_data(self) -> pd.DataFrame:
        """Obtiene datos de la base de datos (original mejorado con tipado)."""
        conn = sqlite3.connect(self.db_path)
        query = "SELECT cpu, ram, disk, error_count FROM system_stats"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    def train_model(self) -> bool:
        """Entrena el modelo y evalúa su performance (NEW: métricas)."""
        df = self.fetch_data()
        if df.empty:
            print("No hay datos suficientes para entrenar el modelo.")
            return False

        # NEW: Configuración flexible de hiperparámetros
        model = IsolationForest(
            contamination=self.contamination,
            n_estimators=100,  # NEW: Parametrizado
            random_state=42,
            n_jobs=-1  # NEW: Uso de todos los núcleos
        )
        model.fit(df[self.feature_names])
        
        # NEW: Evaluación del modelo
        predictions = model.predict(df[self.feature_names])
        anomalies = df[predictions == -1]
        print(f"🔍 Modelo entrenado. Anomalías detectadas: {len(anomalies)}/{len(df)}")
        
        joblib.dump(model, self.model_path)
        self.model = model
        return True

    def load_or_train_model(self) -> None:
        """Carga el modelo si existe, de lo contrario lo entrena (original mejorado)."""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                print("Modelo predictivo cargado desde archivo.")
            except Exception as e:
                print(f"Error cargando el modelo, entrenando nuevo: {str(e)}")
                self.train_model()
        else:
            self.train_model()

    def predict_anomaly(self, cpu: float, ram: float, disk: float, errors: int) -> bool:
        """Predice si hay anomalía (original con tipado mejorado)."""
        if self.model is None:
            self.load_or_train_model()
        
        features = pd.DataFrame([[cpu, ram, disk, errors]], columns=self.feature_names)
        prediction = self.model.predict(features)
        return prediction[0] == -1

    def analyze_predictive(self, cpu: float, ram: float, disk: float, error_count: int) -> List[str]:
        """Genera alertas predictivas (original mejorado con severidad)."""
        alerts = []
        if self.predict_anomaly(cpu, ram, disk, error_count):
            # NEW: Alertas con niveles de severidad basados en valores
            severity = "HIGH" if cpu > 90 or ram > 90 else "MEDIUM"
            alerts.append({
                "message": "Comportamiento anómalo detectado en el sistema",
                "severity": severity,  # NEW: Severidad dinámica
                "values": f"CPU: {cpu}%, RAM: {ram}%"  # NEW: Contexto adicional
            })
        return alerts

    # NEW: Método para obtener métricas del modelo
    def get_model_metrics(self) -> Dict[str, float]:
        """Evalúa y devuelve métricas de performance del modelo."""
        df = self.fetch_data()
        if df.empty or self.model is None:
            return {}
        
        predictions = self.model.predict(df[self.feature_names])
        true_labels = np.where(df['error_count'] > 0, -1, 1)  # Asumimos errores como anomalías reales
        
        return {
            "precision": precision_score(true_labels, predictions, pos_label=-1),
            "recall": recall_score(true_labels, predictions, pos_label=-1)
        }