
import os
import zipfile
import requests
import tempfile
import subprocess
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil

class RepositoryHandler:
    """Class for handling repository operations"""
    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.extraction_base_dir = os.path.join(os.getcwd(), 'cloned_repo')
        os.makedirs(self.extraction_base_dir, exist_ok=True)
    
    def process_repository(self, repo_path_or_url):
        """Process a repository and return a list of file paths"""
        final_path = ""
        directory_structure = {}
        
        # Clear previous repository contents
        self._clear_extraction_dir()
        
        # Determine the repository type and process it
        if repo_path_or_url.startswith(('http://', 'https://')) and ('github.com' in repo_path_or_url or 'bitbucket.org' in repo_path_or_url or 'gitlab.com' in repo_path_or_url):
            try:
                final_path, directory_structure = self.get_remote_repository(repo_path_or_url)
                if not final_path:
                    raise Exception(f"Failed to process repository URL: {repo_path_or_url}")
            except Exception as e:
                raise Exception(f"Failed to process repository: {str(e)}")
        elif os.path.isfile(repo_path_or_url) and repo_path_or_url.endswith('.zip'):
            # Process ZIP file
            try:
                final_path = self.process_zip_file(repo_path_or_url)
                directory_structure = self._get_directory_structure_parallel(final_path)
            except Exception as e:
                raise Exception(f"Failed to process ZIP file: {str(e)}")
        else:
            # It's a local path
            final_path = repo_path_or_url
            if not os.path.exists(final_path):
                raise Exception(f"Repository path does not exist: {final_path}")
            directory_structure = self._get_directory_structure_parallel(final_path)
        
        # Process files in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            file_futures = {}
            
            # Get all files in the repository
            for root, _, files in os.walk(final_path):
                # Skip certain directories
                if any(excluded in root for excluded in ['.git', 'node_modules', '__pycache__', '.streamlit']):
                    continue
                
                for file in files:
                    # Skip certain files
                    if file.startswith('.') or file.endswith(('.pyc', '.class', '.o')):
                        continue
                    
                    file_path = os.path.join(root, file)
                    future = executor.submit(self._process_file, file_path)
                    file_futures[future] = file_path
            
            # Collect results
            results = []
            for future in concurrent.futures.as_completed(file_futures):
                file_path = file_futures[future]
                try:
                    result = future.result()
                    if result:
                        results.append((file_path, result))
                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")
        
        return final_path, directory_structure, results
    
    def _clear_extraction_dir(self):
        """Clear previous repository contents"""
        try:
            for item in os.listdir(self.extraction_base_dir):
                item_path = os.path.join(self.extraction_base_dir, item)
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path)
                else:
                    os.remove(item_path)
        except Exception as e:
            print(f"Error clearing extraction directory: {str(e)}")
    
    def _clone_repo(self, repo_url):
        """Clone a Git repository and return the path"""
        # Create a destination directory in the extraction base dir
        repo_name = os.path.basename(repo_url.rstrip('/').rstrip('.git'))
        dest_dir = os.path.join(self.extraction_base_dir, repo_name)
        
        try:
            # Clone the repository
            subprocess.run(["git", "clone", "--depth=1", repo_url, dest_dir], 
                          check=True, capture_output=True)
            return dest_dir
        except subprocess.CalledProcessError as e:
            # Clean up the destination directory
            try:
                if os.path.exists(dest_dir):
                    shutil.rmtree(dest_dir)
            except:
                pass
            
            raise Exception(f"Failed to clone repository: {e.stderr.decode('utf-8')}")
    
    def get_remote_repository(self, repo_url, branch_name=None):
        """Get a remote repository (GitHub, GitLab, or Bitbucket) by downloading the ZIP"""
        repo_name = os.path.basename(repo_url.rstrip('/').rstrip('.git'))
        branch_name = branch_name or 'main'  # Default to main, may need to try master as fallback
        
        # First try to clone the repository directly
        try:
            final_path = self._clone_repo(repo_url)
            directory_structure = self._get_directory_structure_parallel(final_path)
            return final_path, directory_structure
        except Exception as e:
            print(f"Git clone failed, trying ZIP download: {str(e)}")
        
        # If git clone fails, try downloading ZIP
        # Determine the appropriate ZIP URL based on the repository type
        if 'github.com' in repo_url:
            # Try main branch first
            zip_url = f'{repo_url}/archive/refs/heads/{branch_name}.zip'
            print(f"Requesting ZIP from GitHub: {zip_url}")
            
            # If main branch fails, try master
            if not self._url_exists(zip_url) and branch_name == 'main':
                branch_name = 'master'
                zip_url = f'{repo_url}/archive/refs/heads/{branch_name}.zip'
                print(f"Main branch not found, trying master: {zip_url}")
                
                # If master also fails, try the default branch
                if not self._url_exists(zip_url):
                    zip_url = f'{repo_url}/archive/HEAD.zip'
                    print(f"Trying default branch: {zip_url}")
        elif 'gitlab.com' in repo_url:
            zip_url = f'{repo_url}/-/archive/{branch_name}/{repo_name}-{branch_name}.zip'
            print(f"Requesting ZIP from GitLab: {zip_url}")
            
            # If main branch fails, try master
            if not self._url_exists(zip_url) and branch_name == 'main':
                branch_name = 'master'
                zip_url = f'{repo_url}/-/archive/{branch_name}/{repo_name}-{branch_name}.zip'
                print(f"Main branch not found, trying master: {zip_url}")
        elif 'bitbucket.org' in repo_url:
            zip_url = f'{repo_url}/get/{branch_name}.zip'
            print(f"Requesting ZIP from Bitbucket: {zip_url}")
            
            # If main branch fails, try master
            if not self._url_exists(zip_url) and branch_name == 'main':
                branch_name = 'master'
                zip_url = f'{repo_url}/get/{branch_name}.zip'
                print(f"Main branch not found, trying master: {zip_url}")
        else:
            raise Exception("Invalid URL: Only GitHub, GitLab, and Bitbucket links are supported.")

        zip_path = os.path.join(self.extraction_base_dir, f'{repo_name}.zip')
        self._download_zip_streaming(zip_url, zip_path)

        final_path = self.process_zip_file(zip_path)
        directory_structure = self._get_directory_structure_parallel(final_path)
        
        return final_path, directory_structure
    
    def _url_exists(self, url):
        """Check if a URL exists and is accessible"""
        try:
            response = requests.head(url)
            return response.status_code == 200
        except Exception:
            return False
    
    def _download_zip_streaming(self, url, local_path):
        """Download the ZIP file using streaming to save memory and improve download speed"""
        try:
            with requests.get(url, stream=True) as response:
                response.raise_for_status()
                with open(local_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
            return True
        except requests.RequestException as error:
            raise Exception(f"An error occurred while downloading the ZIP file: {error}")
    
    def process_zip_file(self, zip_path):
        """Unzip the file and return the path of the unzipped folder"""
        extraction_dir = os.path.join(self.extraction_base_dir, 'extracted')
        os.makedirs(extraction_dir, exist_ok=True)

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extraction_dir)

        return extraction_dir
    
    def _get_directory_structure_parallel(self, path):
        """Get the directory structure as a dictionary using parallel processing"""
        directory_structure = {}

        def process_dir(root_dir):
            """Helper function to gather files in a directory"""
            return {root: files for root, _, files in os.walk(root_dir)}

        with ThreadPoolExecutor() as executor:
            future = executor.submit(process_dir, path)
            directory_structure.update(future.result())

        return directory_structure
    
    def _process_file(self, file_path):
        """Process a single file and return its content"""
        try:
            # Skip files that are too large (>1MB)
            if os.path.getsize(file_path) > 1000000:
                return None
                
            # Determine file type and read accordingly
            _, file_extension = os.path.splitext(file_path)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    if not content or len(content) < 10:  # Skip empty or very small files
                        return None
                    return content
            except UnicodeDecodeError:
                # Binary file - skip
                return None
        except Exception as e:
            print(f"Error in _process_file for {file_path}: {str(e)}")
            return None
    
    def get_directory_structure(self, path):
        """Get the directory structure as a nested dictionary"""
        result = {}
        path = Path(path)
        
        if not path.exists():
            return {}
            
        for item in path.iterdir():
            # Skip hidden files and directories
            if item.name.startswith('.'):
                continue
                
            # Skip excluded directories
            if item.is_dir() and item.name in ['node_modules', '__pycache__', '.streamlit']:
                continue
                
            if item.is_dir():
                # Recursively process subdirectories
                result[item.name] = self.get_directory_structure(item)
            else:
                # Store file with None as value
                result[item.name] = None
                
        return result
