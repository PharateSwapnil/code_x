import nbformat
import pandas as pd
import yaml
import pickle
import sqlite3
import json
import csv
import xml.etree.ElementTree as ET
from pathlib import Path
import os
import logging

logger = logging.getLogger(__name__)

class FileReader:
    @staticmethod
    def read_text_file(file_path):
        """Read text-based files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding if UTF-8 fails
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Could not read {file_path} as text: {str(e)}")
                return f"[Error reading file: {os.path.basename(file_path)}]"
        except Exception as e:
            logger.warning(f"Error reading {file_path}: {str(e)}")
            return f"[Error reading file: {os.path.basename(file_path)}]"

    @staticmethod
    def read_ipynb_file(file_path):
        """Read Jupyter notebook files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                nb = nbformat.read(f, as_version=4)
                content = []
                for cell in nb.cells:
                    if cell.cell_type in ['code', 'markdown']:
                        content.append(f"[{cell.cell_type.upper()}]\n{cell.source}")
                return '\n\n'.join(content)
        except Exception as e:
            logger.warning(f"Error reading notebook {file_path}: {str(e)}")
            return f"[Error reading notebook: {os.path.basename(file_path)}]"

    @staticmethod
    def read_yaml_file(file_path):
        """Read YAML files"""
        try:
            with open(file_path, 'r') as f:
                data = yaml.safe_load(f)
                return yaml.dump(data, default_flow_style=False)
        except Exception as e:
            logger.warning(f"Error reading YAML {file_path}: {str(e)}")
            return FileReader.read_text_file(file_path)  # Fall back to text

    @staticmethod
    def read_json_file(file_path):
        """Read JSON files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return json.dumps(data, indent=2)
        except Exception as e:
            logger.warning(f"Error reading JSON {file_path}: {str(e)}")
            return FileReader.read_text_file(file_path)  # Fall back to text

    @staticmethod
    def read_csv_file(file_path):
        """Read CSV files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                if len(rows) > 20:  # Limit large CSV files
                    return '\n'.join([','.join(row) for row in rows[:20]]) + "\n[...additional rows truncated...]"
                return '\n'.join([','.join(row) for row in rows])
        except Exception as e:
            logger.warning(f"Error reading CSV {file_path}: {str(e)}")
            return FileReader.read_text_file(file_path)  # Fall back to text

    @staticmethod
    def read_xml_file(file_path):
        """Read XML files"""
        try:
            tree = ET.parse(file_path)
            return ET.tostring(tree.getroot(), encoding='unicode')
        except Exception as e:
            logger.warning(f"Error reading XML {file_path}: {str(e)}")
            return FileReader.read_text_file(file_path)  # Fall back to text

    @staticmethod
    def read_markdown_file(file_path):
        """Read Markdown files"""
        return FileReader.read_text_file(file_path)

def get_file_reader(file_path):
    """Get the appropriate file reader based on file extension"""
    file_readers = {
        # Code files
        '.py': FileReader.read_text_file,
        '.js': FileReader.read_text_file,
        '.ts': FileReader.read_text_file,
        '.jsx': FileReader.read_text_file,
        '.tsx': FileReader.read_text_file,
        '.java': FileReader.read_text_file,
        '.c': FileReader.read_text_file,
        '.cpp': FileReader.read_text_file,
        '.h': FileReader.read_text_file,
        '.cs': FileReader.read_text_file,
        '.go': FileReader.read_text_file,
        '.rb': FileReader.read_text_file,
        '.php': FileReader.read_text_file,
        '.swift': FileReader.read_text_file,
        '.kt': FileReader.read_text_file,
        
        # Web files
        '.html': FileReader.read_text_file,
        '.css': FileReader.read_text_file,
        '.scss': FileReader.read_text_file,
        '.less': FileReader.read_text_file,
        
        # Data files
        '.json': FileReader.read_json_file,
        '.ipynb': FileReader.read_ipynb_file,
        '.yaml': FileReader.read_yaml_file,
        '.yml': FileReader.read_yaml_file,
        '.xml': FileReader.read_xml_file,
        '.csv': FileReader.read_csv_file,
        
        # Text files
        '.txt': FileReader.read_text_file,
        '.md': FileReader.read_markdown_file,
        '.rst': FileReader.read_text_file,
        
        # Config files
        '.toml': FileReader.read_text_file,
        '.ini': FileReader.read_text_file,
        '.cfg': FileReader.read_text_file,
        '.conf': FileReader.read_text_file,
    }
    
    suffix = Path(file_path).suffix.lower()
    return file_readers.get(suffix, FileReader.read_text_file)
