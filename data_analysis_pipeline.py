#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Data Analysis Pipeline
=====================
A comprehensive pipeline for data extraction, transformation, analysis, and visualization.
This module orchestrates the entire data workflow from raw Excel files to interactive dashboards.
"""

import os
import json
import logging
from datetime import datetime
import pandas as pd
import numpy as np
import sqlite3
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

# Local imports
from analise_avancada import AnalisadorAvancado
from debug_excel import AnalisadorExcel
from database_manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("analysis_pipeline.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class DataAnalysisPipeline:
    """
    Comprehensive data analysis pipeline that orchestrates the entire workflow
    from data extraction to visualization and reporting.
    """
    
    def __init__(self, config_file=None):
        """
        Initialize the data analysis pipeline.
        
        Args:
            config_file (str, optional): Path to configuration file. Defaults to None.
        """
        self.config = self._load_config(config_file)
        self.db_manager = DatabaseManager('analise_historica.db')
        self.analisador = AnalisadorAvancado()
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create output directories if they don't exist
        os.makedirs('output/reports', exist_ok=True)
        os.makedirs('output/dashboards', exist_ok=True)
        os.makedirs('output/data', exist_ok=True)
        
        logger.info("Data Analysis Pipeline initialized")
    
    def _load_config(self, config_file):
        """Load configuration from a JSON file."""
        default_config = {
            "input_files": {
                "julio": "(JULIO) LISTAS INDIVIDUAIS.xlsx",
                "leandro": "(LEANDRO_ADRIANO) LISTAS INDIVIDUAIS.xlsx"
            },
            "analysis_settings": {
                "store_history": True,
                "history_limit": 10,
                "generate_predictions": True,
                "confidence_threshold": 0.7
            },
            "visualization_settings": {
                "theme": "plotly",
                "color_palette": "Set1",
                "include_annotations": True
            },
            "output_settings": {
                "dashboard_filename": "dashboard_atividades.html",
                "save_intermediate_data": True,
                "export_formats": ["html", "json", "csv"]
            }
        }
        
        if config_file and os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    user_config = json.load(f)
                    # Merge user config with default config
                    for key, value in user_config.items():
                        if key in default_config and isinstance(value, dict):
                            default_config[key].update(value)
                        else:
                            default_config[key] = value
                logger.info(f"Configuration loaded from {config_file}")
            except Exception as e:
                logger.error(f"Error loading config file: {str(e)}")
        
        return default_config
    
    def run_pipeline(self):
        """Execute the complete data analysis pipeline."""
        logger.info("Starting data analysis pipeline")
        
        try:
            # Step 1: Extract data from Excel files
            self._extract_data()
            
            # Step 2: Transform and clean data
            self._transform_data()
            
            # Step 3: Analyze data
            self._analyze_data()
            
            # Step 4: Generate visualizations and dashboard
            self._generate_visualizations()
            
            # Step 5: Store results in database
            self._store_results()
            
            # Step 6: Generate reports
            self._generate_reports()
            
            logger.info("Data analysis pipeline completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Pipeline execution failed: {str(e)}")
            return False
    
    def _extract_data(self):
        """Extract data from source Excel files."""
        logger.info("Extracting data from Excel files")
        
        try:
            # Process Julio's group data
            julio_file = self.config["input_files"]["julio"]
            logger.info(f"Processing {julio_file}")
            self.analisador.analisar_arquivo(julio_file)
            
            # Process Leandro's group data
            leandro_file = self.config["input_files"]["leandro"]
            logger.info(f"Processing {leandro_file}")
            self.analisador.analisar_arquivo(leandro_file)
            
            # Save extracted data if configured
            if self.config["output_settings"]["save_intermediate_data"]:
                self._save_intermediate_data("extracted")
                
            logger.info("Data extraction completed")
            
        except Exception as e:
            logger.error(f"Data extraction failed: {str(e)}")
            raise
    
    def _transform_data(self):
        """Transform and clean the extracted data."""
        logger.info("Transforming and cleaning data")
        
        # Additional data transformations can be implemented here
        # For now, we're relying on the transformations in analisar_arquivo
        
        # Save transformed data if configured
        if self.config["output_settings"]["save_intermediate_data"]:
            self._save_intermediate_data("transformed")
            
        logger.info("Data transformation completed")
    
    def _analyze_data(self):
        """Perform advanced analysis on the data."""
        logger.info("Performing data analysis")
        
        try:
            # Run correlation analysis
            self.analisador.analisar_correlacoes()
            
            # Detect bottlenecks
            self.analisador.detectar_gargalos()
            
            # Analyze trends
            self.analisador.analisar_tendencias()
            
            # Save analysis results if configured
            if self.config["output_settings"]["save_intermediate_data"]:
                self._save_intermediate_data("analyzed")
                
            logger.info("Data analysis completed")
            
        except Exception as e:
            logger.error(f"Data analysis failed: {str(e)}")
            raise
    
    def _generate_visualizations(self):
        """Generate visualizations and dashboard."""
        logger.info("Generating visualizations and dashboard")
        
        try:
            # Generate the HTML dashboard
            self.analisador.gerar_dashboard_html()
            
            # Copy dashboard to timestamped version for history
            dashboard_file = self.config["output_settings"]["dashboard_filename"]
            if os.path.exists(dashboard_file):
                timestamped_file = f"output/dashboards/dashboard_{self.timestamp}.html"
                with open(dashboard_file, 'r', encoding='utf-8') as src:
                    with open(timestamped_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
                logger.info(f"Dashboard saved to {timestamped_file}")
            
            logger.info("Visualizations and dashboard generated")
            
        except Exception as e:
            logger.error(f"Visualization generation failed: {str(e)}")
            raise
    
    def _store_results(self):
        """Store analysis results in the database."""
        logger.info("Storing results in database")
        
        try:
            # Store summary metrics for Julio's group
            for colaborador, metricas in self.analisador.metricas_julio.items():
                if metricas:
                    self.db_manager.store_metrics(
                        colaborador=colaborador,
                        grupo="Julio",
                        data=datetime.now(),
                        total_registros=metricas.get('total_registros', 0),
                        taxa_eficiencia=metricas.get('taxa_eficiencia', 0),
                        tendencia=metricas.get('tendencia', {}).get('direcao', 'estável')
                    )
            
            # Store summary metrics for Leandro's group
            for colaborador, metricas in self.analisador.metricas_leandro.items():
                if metricas:
                    self.db_manager.store_metrics(
                        colaborador=colaborador,
                        grupo="Leandro",
                        data=datetime.now(),
                        total_registros=metricas.get('total_registros', 0),
                        taxa_eficiencia=metricas.get('taxa_eficiencia', 0),
                        tendencia=metricas.get('tendencia', {}).get('direcao', 'estável')
                    )
            
            logger.info("Results stored in database")
            
        except Exception as e:
            logger.error(f"Database storage failed: {str(e)}")
            raise
    
    def _generate_reports(self):
        """Generate summary reports."""
        logger.info("Generating reports")
        
        try:
            # Generate JSON report
            report_data = {
                "timestamp": datetime.now().isoformat(),
                "summary": {
                    "julio": {
                        "total_colaboradores": len(self.analisador.metricas_julio),
                        "total_registros": sum(m.get('total_registros', 0) for m in self.analisador.metricas_julio.values() if m)
                    },
                    "leandro": {
                        "total_colaboradores": len(self.analisador.metricas_leandro),
                        "total_registros": sum(m.get('total_registros', 0) for m in self.analisador.metricas_leandro.values() if m)
                    }
                },
                "detalhes": {
                    "julio": {colab: metrics for colab, metrics in self.analisador.metricas_julio.items() if metrics},
                    "leandro": {colab: metrics for colab, metrics in self.analisador.metricas_leandro.items() if metrics}
                }
            }
            
            # Save JSON report
            report_file = f"output/reports/report_{self.timestamp}.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Report saved to {report_file}")
            
        except Exception as e:
            logger.error(f"Report generation failed: {str(e)}")
            raise
    
    def _save_intermediate_data(self, stage):
        """Save intermediate data for debugging and auditing."""
        try:
            filename = f"output/data/{stage}_data_{self.timestamp}.json"
            data = {
                "stage": stage,
                "timestamp": datetime.now().isoformat(),
                "metricas_julio": {k: v for k, v in self.analisador.metricas_julio.items() if v},
                "metricas_leandro": {k: v for k, v in self.analisador.metricas_leandro.items() if v}
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                
            logger.info(f"Intermediate {stage} data saved to {filename}")
            
        except Exception as e:
            logger.warning(f"Failed to save intermediate data: {str(e)}")

if __name__ == "__main__":
    # Run the pipeline
    pipeline = DataAnalysisPipeline()
    success = pipeline.run_pipeline()
    
    if success:
        print("\n✅ Pipeline executed successfully!")
        print(f"Dashboard generated: {pipeline.config['output_settings']['dashboard_filename']}")
        print(f"Reports saved in: output/reports/")
    else:
        print("\n❌ Pipeline execution failed. Check the logs for details.")
