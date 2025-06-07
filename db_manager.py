import sqlite3
from typing import List, Tuple, Optional  # NEW: Tipado para claridad

class DataBase:
    def __init__(self, db_path: str):
        """Inicializa la conexión a la base de datos con validación de tipos."""
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self) -> None:
        """Crea las tablas con restricciones de validación mejoradas."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS system_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cpu REAL CHECK (cpu >= 0 AND cpu <= 100),  -- NEW: Validación de rango (cambié # por --)
                ram REAL CHECK (ram >= 0 AND ram <= 100),  -- NEW: Validación de rango
                disk REAL CHECK (disk >= 0 AND disk <= 100),  -- NEW: Validación de rango
                error_count INTEGER,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT,
                severity TEXT CHECK (severity IN ("LOW", "MEDIUM", "HIGH")),  -- NEW: Niveles de alerta (comillas dobles)
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.conn.commit()

    def insert_system_stats(self, cpu: float, ram: float, disk: float, error_count: int) -> None:
        """Inserta estadísticas del sistema con validación de datos."""
        if not all(0 <= x <= 100 for x in (cpu, ram, disk)):  # NEW: Validación adicional
            raise ValueError("Los valores de CPU, RAM y DISK deben estar entre 0 y 100")
        self.cursor.execute('''
            INSERT INTO system_stats(cpu, ram, disk, error_count)
            VALUES (?, ?, ?, ?)
        ''', (cpu, ram, disk, error_count))
        self.conn.commit()

    def insert_alert(self, message: str, severity: str = 'MEDIUM') -> None:  # NEW: Parámetro severity
        """Inserta una alerta con nivel de severidad."""
        self.cursor.execute('''
            INSERT INTO alerts(message, severity) VALUES (?, ?)
        ''', (message, severity))  # NEW: Ahora incluye severity
        self.conn.commit()

    def count_recent_errors(self, hours: int = 1) -> int:  # NEW: Parámetro flexible
        """Cuenta alertas recientes (por defecto, últimas 1 hora)."""
        self.cursor.execute('''
            SELECT COUNT(*) FROM alerts 
            WHERE timestamp >= datetime("now", ?)
        ''', (f'-{hours} hours',))  # NEW: Horas personalizadas
        return self.cursor.fetchone()[0]

    def get_all_alerts(self, limit: Optional[int] = None) -> List[Tuple]:  # NEW: Límite opcional
        """Obtiene todas las alertas, con límite opcional."""
        query = '''
            SELECT timestamp, message, severity FROM alerts  -- NEW: Incluye severity
            ORDER BY timestamp DESC
        '''
        if limit:
            query += f' LIMIT {limit}'  # NEW: Soporte para límite
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def close(self) -> None:
        """Cierra la conexión a la base de datos."""
        self.conn.close()

    # NEW: Métodos adicionales para gráficos (sin afectar lo existente)
    def get_historical_stats(self, days: int = 7) -> List[Tuple]:
        """Obtiene datos históricos para gráficos."""
        self.cursor.execute('''
            SELECT timestamp, cpu, ram, disk 
            FROM system_stats 
            WHERE timestamp >= datetime("now", ?)
            ORDER BY timestamp
        ''', (f'-{days} days',))
        return self.cursor.fetchall()