#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database Manager
===============
Handles all database operations for storing and retrieving analysis results.
Provides a clean interface for data persistence across analysis runs.
"""

import sqlite3
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Manages database operations for the analytics system.
    Handles schema creation, data storage, and retrieval.
    """
    
    def __init__(self, db_path):
        """
        Initialize the database manager.
        
        Args:
            db_path (str): Path to the SQLite database file
        """
        self.db_path = db_path
        self._initialize_db()
    
    def _initialize_db(self):
        """Create the database schema if it doesn't exist."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create metrics table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS metricas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                colaborador TEXT NOT NULL,
                grupo TEXT NOT NULL,
                data TIMESTAMP NOT NULL,
                total_registros INTEGER NOT NULL,
                taxa_eficiencia REAL NOT NULL,
                tendencia TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create analysis_history table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS analise_historica (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TIMESTAMP NOT NULL,
                grupo TEXT NOT NULL,
                metricas TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create configuration table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS configuracoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chave TEXT UNIQUE NOT NULL,
                valor TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def store_metrics(self, colaborador, grupo, data, total_registros, taxa_eficiencia, tendencia):
        """
        Store metrics for a collaborator.
        
        Args:
            colaborador (str): Name of the collaborator
            grupo (str): Group name (Julio or Leandro)
            data (datetime): Date of the analysis
            total_registros (int): Total number of records
            taxa_eficiencia (float): Efficiency rate
            tendencia (str): Trend direction
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            INSERT INTO metricas (colaborador, grupo, data, total_registros, taxa_eficiencia, tendencia)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (colaborador, grupo, data.isoformat(), total_registros, taxa_eficiencia, tendencia))
            
            conn.commit()
            logger.info(f"Metrics stored for {colaborador} in group {grupo}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store metrics: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def store_analysis_history(self, data, grupo, metricas):
        """
        Store a complete analysis history entry.
        
        Args:
            data (datetime): Date of the analysis
            grupo (str): Group name
            metricas (dict): Metrics data
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Convert metrics to JSON string
            metricas_json = json.dumps(metricas, ensure_ascii=False)
            
            cursor.execute('''
            INSERT INTO analise_historica (data, grupo, metricas)
            VALUES (?, ?, ?)
            ''', (data.isoformat(), grupo, metricas_json))
            
            conn.commit()
            logger.info(f"Analysis history stored for group {grupo}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store analysis history: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_metrics_history(self, colaborador=None, grupo=None, start_date=None, end_date=None, limit=10):
        """
        Retrieve metrics history with optional filters.
        
        Args:
            colaborador (str, optional): Filter by collaborator name
            grupo (str, optional): Filter by group name
            start_date (datetime, optional): Start date for filtering
            end_date (datetime, optional): End date for filtering
            limit (int, optional): Maximum number of records to return
        
        Returns:
            list: List of metrics records
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            cursor = conn.cursor()
            
            query = "SELECT * FROM metricas WHERE 1=1"
            params = []
            
            if colaborador:
                query += " AND colaborador = ?"
                params.append(colaborador)
            
            if grupo:
                query += " AND grupo = ?"
                params.append(grupo)
            
            if start_date:
                query += " AND data >= ?"
                params.append(start_date.isoformat())
            
            if end_date:
                query += " AND data <= ?"
                params.append(end_date.isoformat())
            
            query += " ORDER BY data DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            results = [dict(row) for row in cursor.fetchall()]
            
            logger.info(f"Retrieved {len(results)} metrics records")
            return results
            
        except Exception as e:
            logger.error(f"Failed to retrieve metrics history: {str(e)}")
            return []
        finally:
            if conn:
                conn.close()
    
    def get_efficiency_trend(self, colaborador, days=30):
        """
        Get efficiency trend data for a collaborator over time.
        
        Args:
            colaborador (str): Collaborator name
            days (int, optional): Number of days to look back
        
        Returns:
            dict: Trend data with dates and efficiency values
        """
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT data, taxa_eficiencia 
            FROM metricas 
            WHERE colaborador = ? 
            AND data >= date('now', ?) 
            ORDER BY data ASC
            ''', (colaborador, f'-{days} days'))
            
            results = [dict(row) for row in cursor.fetchall()]
            
            # Format the results
            trend_data = {
                "dates": [row["data"] for row in results],
                "efficiency": [row["taxa_eficiencia"] for row in results]
            }
            
            return trend_data
            
        except Exception as e:
            logger.error(f"Failed to retrieve efficiency trend: {str(e)}")
            return {"dates": [], "efficiency": []}
        finally:
            if conn:
                conn.close()
    
    def get_group_comparison(self):
        """
        Get comparison data between Julio and Leandro groups.
        
        Returns:
            dict: Comparison metrics between groups
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get average efficiency by group
            cursor.execute('''
            SELECT grupo, AVG(taxa_eficiencia) as avg_eficiencia
            FROM metricas
            GROUP BY grupo
            ''')
            
            efficiency_results = cursor.fetchall()
            efficiency_by_group = {row[0]: row[1] for row in efficiency_results}
            
            # Get total records by group
            cursor.execute('''
            SELECT grupo, SUM(total_registros) as total
            FROM metricas
            GROUP BY grupo
            ''')
            
            total_results = cursor.fetchall()
            total_by_group = {row[0]: row[1] for row in total_results}
            
            # Compile the comparison data
            comparison = {
                "efficiency": efficiency_by_group,
                "total_records": total_by_group
            }
            
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to retrieve group comparison: {str(e)}")
            return {"efficiency": {}, "total_records": {}}
        finally:
            if conn:
                conn.close()
    
    def save_configuration(self, key, value):
        """
        Save a configuration value.
        
        Args:
            key (str): Configuration key
            value (any): Configuration value (will be converted to JSON)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Convert value to JSON if it's not a string
            if not isinstance(value, str):
                value = json.dumps(value)
            
            cursor.execute('''
            INSERT OR REPLACE INTO configuracoes (chave, valor, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (key, value))
            
            conn.commit()
            logger.info(f"Configuration saved: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
    
    def get_configuration(self, key, default=None):
        """
        Get a configuration value.
        
        Args:
            key (str): Configuration key
            default (any, optional): Default value if key not found
        
        Returns:
            any: Configuration value
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT valor FROM configuracoes WHERE chave = ?
            ''', (key,))
            
            result = cursor.fetchone()
            
            if result:
                value = result[0]
                try:
                    # Try to parse as JSON
                    return json.loads(value)
                except:
                    # Return as is if not JSON
                    return value
            else:
                return default
            
        except Exception as e:
            logger.error(f"Failed to retrieve configuration: {str(e)}")
            return default
        finally:
            if conn:
                conn.close()
