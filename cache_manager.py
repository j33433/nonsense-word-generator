"""Shared caching functionality for word generators."""

import os
import pickle
import hashlib


class CacheManager:
    """Manages caching for word lists and generated chains."""
    
    def __init__(self, cache_dir="cache"):
        """Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_cache_path(self, cache_key, extension=".pkl"):
        """Get the full path for a cache file.
        
        Args:
            cache_key: Unique identifier for the cached data
            extension: File extension for the cache file
            
        Returns:
            str: Full path to cache file
        """
        return os.path.join(self.cache_dir, f"{cache_key}{extension}")
    
    def should_rebuild(self, cache_path, source_path=None):
        """Check if cache needs to be rebuilt.
        
        Args:
            cache_path: Path to cache file
            source_path: Path to source file (optional)
            
        Returns:
            bool: True if cache should be rebuilt
        """
        if not os.path.exists(cache_path):
            return True
        
        if source_path and os.path.exists(source_path):
            cache_time = os.path.getmtime(cache_path)
            source_time = os.path.getmtime(source_path)
            return source_time > cache_time
        
        return False
    
    def save_data(self, cache_path, data):
        """Save data to cache file.
        
        Args:
            cache_path: Path to cache file
            data: Data to cache
            
        Returns:
            bool: True if save succeeded
        """
        try:
            with open(cache_path, 'wb') as f:
                pickle.dump(data, f)
            return True
        except Exception:
            return False
    
    def load_data(self, cache_path):
        """Load data from cache file.
        
        Args:
            cache_path: Path to cache file
            
        Returns:
            Data from cache file, or None if loading failed
        """
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception:
            return None
    
    def get_url_hash(self, url):
        """Get a hash for a URL to use in cache filenames.
        
        Args:
            url: URL to hash
            
        Returns:
            str: Hash of the URL
        """
        return hashlib.md5(url.encode()).hexdigest()
