import nbformat
import pandas as pd
import yaml
import pickle
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path

class FileReader:
    @staticmethod
    def read_text_file(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def read_ipynb_file(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            nb = nbformat.read(f, as_version=4)
            content = []
            for cell in nb.cells:
                if cell.cell_type in ['code', 'markdown']:
                    content.append(cell.source)
            return '\n\n'.join(content)

    @staticmethod
    def read_yaml_file(file_path):
        with open(file_path, 'r') as f:
            return yaml.safe_load(f)

    @staticmethod
    def read_xml_file(file_path):
        tree = ET.parse(file_path)
        return ET.tostring(tree.getroot(), encoding='unicode')

def get_file_reader(file_path):
    file_readers = {
        '.txt': FileReader.read_text_file,
        '.py': FileReader.read_text_file,
        '.js': FileReader.read_text_file,
        '.html': FileReader.read_text_file,
        '.ipynb': FileReader.read_ipynb_file,
        '.yaml': FileReader.read_yaml_file,
        '.yml': FileReader.read_yaml_file,
        '.xml': FileReader.read_xml_file,
    }
    
    suffix = Path(file_path).suffix.lower()
    return file_readers.get(suffix, FileReader.read_text_file)
