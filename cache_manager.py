"""Shared caching functionality for word generators."""

import os
import json
import hashlib
import re
import tempfile
import glob


class CacheManager:
    """Manages caching for word lists and generated chains."""
    
    def __init__(self, cache_dir="cache"):
        """Initialize cache manager.
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
    
    def get_cache_path(self, cache_key, extension=".json"):
        """Get the full path for a cache file.
        
        Args:
            cache_key: Unique identifier for the cached data
            extension: File extension for the cache file
            
        Returns:
            str: Full path to cache file
        """
        # Sanitize cache_key to prevent path traversal
        safe_key = re.sub(r'[^\w\-_.]', '_', cache_key)
        safe_key = safe_key.replace('..', '_')
        return os.path.join(self.cache_dir, f"{safe_key}{extension}")
    
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
            # Convert Counter objects to regular dicts for JSON serialization
            serializable_data = self._make_serializable(data)
            cache_dir = os.path.dirname(cache_path) or "."
            os.makedirs(cache_dir, exist_ok=True)
            temp_path = cache_path + ".tmp"
            with open(temp_path, 'w', encoding='utf-8') as f:
                # Restrictive permissions
                try:
                    os.chmod(temp_path, 0o600)
                except Exception:
                    pass
                json.dump(serializable_data, f)
            # Refuse to overwrite a symlink
            if os.path.islink(cache_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
                return False
            os.replace(temp_path, cache_path)
            return True
        except Exception:
            # Best-effort cleanup
            try:
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
            return False
    
    def load_data(self, cache_path):
        """Load data from cache file.
        
        Args:
            cache_path: Path to cache file
            
        Returns:
            Data from cache file, or None if loading failed
        """
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # Convert back to Counter objects if needed
            return self._restore_counters(data)
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
    
    def _make_serializable(self, data):
        """Convert data to JSON-serializable format.
        
        Args:
            data: Data that may contain Counter objects
            
        Returns:
            JSON-serializable version of data
        """
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if hasattr(value, 'items'):  # Counter or dict
                    result[key] = dict(value)
                elif isinstance(value, set):
                    result[key] = list(value)
                else:
                    result[key] = value
            return result
        elif isinstance(data, set):
            return list(data)
        return data
    
    def _restore_counters(self, data):
        """Restore Counter objects from JSON data.
        
        Args:
            data: Data loaded from JSON
            
        Returns:
            Data with Counter objects restored
        """
        from collections import Counter, defaultdict
        
        if isinstance(data, dict) and 'chains' in data:
            # This is Markov chain data
            restored = data.copy()
            if 'chains' in restored:
                chains = defaultdict(Counter)
                for key, counter_dict in restored['chains'].items():
                    chains[key] = Counter(counter_dict)
                restored['chains'] = chains
            if 'start_chains' in restored:
                restored['start_chains'] = Counter(restored['start_chains'])
            return restored
        return data

    def build_cache_key(self, kind, params):
        """Normalize and build a cache key string from kind and parameters."""
        def _sanitize(v):
            s = str(v)
            s = re.sub(r'[^\w\-_.]', '_', s)
            s = s.replace('..', '_')
            return s
        parts = [kind]
        for k in sorted(params.keys()):
            parts.append(f"{_sanitize(k)}={_sanitize(params[k])}")
        return "_".join(parts)

    def list_cache(self, pattern=None):
        """List cached files, optionally filtered by a glob pattern."""
        if not os.path.isdir(self.cache_dir):
            return []
        if pattern:
            return sorted(glob.glob(os.path.join(self.cache_dir, pattern)))
        return sorted(os.path.join(self.cache_dir, f) for f in os.listdir(self.cache_dir))

    def clear_cache(self, pattern=None):
        """Clear cache files. If pattern is provided, only matching files are removed."""
        paths = self.list_cache(pattern)
        removed = 0
        for p in paths:
            try:
                os.remove(p)
                removed += 1
            except Exception:
                pass
        return removed
