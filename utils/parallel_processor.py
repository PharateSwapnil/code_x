import concurrent.futures
import os
from typing import List, Callable, Any, TypeVar, Dict, Optional

T = TypeVar('T')
R = TypeVar('R')

class ParallelProcessor:
    """Utility class for parallel processing operations"""
    
    def __init__(self, max_workers: int = 4):
        """Initialize the parallel processor with max workers"""
        self.max_workers = max_workers

    @staticmethod
    def process_items(items: List[T], 
                      process_func: Callable[[T], R], 
                      max_workers: int = 4) -> List[R]:
        """
        Process a list of items in parallel using ThreadPoolExecutor

        Args:
            items: List of items to process
            process_func: Function to apply to each item
            max_workers: Maximum number of worker threads

        Returns:
            List of results
        """
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_item = {executor.submit(process_func, item): item for item in items}

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    if result is not None:  # Filter out None results
                        results.append(result)
                except Exception as e:
                    print(f"Error processing item {item}: {str(e)}")

        return results

    @staticmethod
    def process_dict_items(items_dict: Dict[str, T], 
                           process_func: Callable[[str, T], R], 
                           max_workers: int = 4) -> Dict[str, R]:
        """
        Process a dictionary of items in parallel using ThreadPoolExecutor

        Args:
            items_dict: Dictionary of items to process
            process_func: Function that takes (key, value) and returns a result
            max_workers: Maximum number of worker threads

        Returns:
            Dictionary of results
        """
        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_key = {
                executor.submit(process_func, key, value): key 
                for key, value in items_dict.items()
            }

            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_key):
                key = future_to_key[future]
                try:
                    result = future.result()
                    if result is not None:  # Filter out None results
                        results[key] = result
                except Exception as e:
                    print(f"Error processing key {key}: {str(e)}")

        return results

    @classmethod
    def process_directory(cls, 
                         directory: str, 
                         file_filter: Optional[Callable[[str], bool]] = None,
                         process_func: Callable[[str], R] = None,
                         recursive: bool = True,
                         max_workers: int = 4,
                         show_progress: bool = True) -> List[R]:
        """
        Process all files in a directory
        Args:
            directory: Directory path to process
            file_filter: Optional function to filter files (return True to process)
            process_func: Function to apply to each file path
            recursive: Whether to recursively process subdirectories
            max_workers: Maximum number of worker threads
            show_progress: Whether to show a progress bar

        Returns:
            List of processed results
        """
        if not os.path.exists(directory) or not os.path.isdir(directory):
            raise ValueError(f"Directory not found: {directory}")

        # Collect files to process
        files_to_process = []
        
        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    file_path = os.path.join(root, file)
                    if file_filter is None or file_filter(file_path):
                        files_to_process.append(file_path)
        else:
            for item in os.listdir(directory):
                file_path = os.path.join(directory, item)
                if os.path.isfile(file_path) and (file_filter is None or file_filter(file_path)):
                    files_to_process.append(file_path)

        # Create a processor instance and process the files
        processor = cls(max_workers=max_workers)
        return processor.process_items(
            items=files_to_process,
            process_func=process_func,
            max_workers=max_workers
        )

    def find_files(self, 
                  directory: str, 
                  extensions: Optional[List[str]] = None,
                  exclude_dirs: Optional[List[str]] = None) -> List[str]:
        """
        Find all files in a directory with specified extensions.

        Args:
            directory: Root directory to search
            extensions: List of file extensions to include (e.g., ['.py', '.js'])
            exclude_dirs: List of directory names to exclude

        Returns:
            List of file paths
        """
        import os
        exclude_dirs = exclude_dirs or ['.git', 'node_modules', '__pycache__', '.streamlit']

        files = []
        for root, dirs, filenames in os.walk(directory):
            # Remove excluded directories
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]

            for filename in filenames:
                # Skip hidden files
                if filename.startswith('.'):
                    continue

                # Check extension if provided
                if extensions and not any(filename.endswith(ext) for ext in extensions):
                    continue

                file_path = os.path.join(root, filename)
                files.append(file_path)

        return files