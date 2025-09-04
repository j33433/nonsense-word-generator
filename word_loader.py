"""Unified word loading functionality."""

import os
import urllib.request
import urllib.parse
import socket
import ipaddress
from hunspell import get_hunspell_words, HUNSPELL_DICT_URLS
from cache_manager import CacheManager


# Special word lists (non-language dictionaries)
WORD_URLS = {
    "names": "https://raw.githubusercontent.com/smashew/NameDatabases/master/NamesDatabases/first%20names/us.txt",
    "surnames": "https://raw.githubusercontent.com/smashew/NameDatabases/master/NamesDatabases/surnames/us.txt",
    "pet": "https://raw.githubusercontent.com/jonathand-cf/wordlist-pets/refs/heads/main/pet-names.txt",
}

# Add Hunspell dictionaries as default for language codes
for lang_code in HUNSPELL_DICT_URLS.keys():
    WORD_URLS[lang_code] = f"hunspell:{lang_code}"


def parse_length(length_str):
    """Parse length string into min and max values.
    
    Args:
        length_str: Length specification like "5-8" or "10"
        
    Returns:
        tuple: (min_len, max_len)
        
    Raises:
        ValueError: If format is invalid
    """
    if '-' in length_str:
        min_str, max_str = length_str.split('-', 1)
        return int(min_str), int(max_str)
    else:
        length = int(length_str)
        return length, length


def is_url(text):
    """Check if text is a URL.
    
    Args:
        text: String to check
        
    Returns:
        bool: True if text appears to be a URL
    """
    return text.startswith(('http://', 'https://'))


def is_safe_url(url):
    """Check if URL is safe to download from.
    
    Args:
        url: URL to validate
        
    Returns:
        bool: True if URL is considered safe
    """
    try:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            return False
        hostname = parsed.hostname
        if not hostname:
            return False
        # Quick hostname blocks
        if hostname.lower() in ('localhost',):
            return False
        # Resolve host to IPs and ensure all are globally routable
        try:
            addrinfos = socket.getaddrinfo(hostname, None)
        except Exception:
            return False
        if not addrinfos:
            return False
        for ai in addrinfos:
            ip_str = ai[4][0]
            try:
                ip_obj = ipaddress.ip_address(ip_str)
            except ValueError:
                return False
            # Only allow global addresses (reject private, loopback, link-local, multicast, reserved, unspecified)
            if not ip_obj.is_global:
                return False
        return True
    except Exception:
        return False


def load_words(word_source, verbose=False, cache_manager=None):
    """Load words from any source (URL, Hunspell, basic word lists).
    
    Args:
        word_source: Word source identifier (language code, URL, etc.)
        verbose: Print progress messages
        cache_manager: CacheManager instance (creates new one if None)
        
    Returns:
        set: Set of words loaded from the source
        
    Raises:
        ValueError: If word source is not supported
        RuntimeError: If loading fails
    """
    if cache_manager is None:
        cache_manager = CacheManager()
    
    def vprint(*args, **kwargs):
        if verbose:
            print(*args, **kwargs)
    
    # Handle Hunspell dictionaries
    if word_source.startswith("hunspell:"):
        lang_code = word_source.split(":", 1)[1]
        vprint(f"Loading Hunspell dictionary for {lang_code}...")
        return get_hunspell_words(lang_code, verbose=verbose)
    
    # Determine URL and cache info
    if is_url(word_source):
        if not is_safe_url(word_source):
            raise ValueError(f"Unsafe URL: {word_source}")
        url = word_source
        display_name = f"custom URL ({url})"
        url_hash = cache_manager.get_url_hash(url)
        cache_file = cache_manager.get_cache_path(f"words_url_{url_hash}", ".txt")
    else:
        if word_source not in WORD_URLS:
            raise ValueError(f"Unsupported word source: {word_source}. Supported: {list(WORD_URLS.keys())}")
        
        url_or_hunspell = WORD_URLS[word_source]
        if url_or_hunspell.startswith("hunspell:"):
            # Redirect to Hunspell handler
            lang_code = url_or_hunspell.split(":", 1)[1]
            vprint(f"Loading Hunspell dictionary for {lang_code}...")
            return get_hunspell_words(lang_code, verbose=verbose)
        
        url = url_or_hunspell
        display_name = word_source
        safe_source = word_source.replace(":", "_")
        cache_file = cache_manager.get_cache_path(f"words_{safe_source}", ".txt")
    
    # Download if not cached
    if not os.path.exists(cache_file):
        vprint(f"Downloading {display_name} word list...")
        _download_word_file(url, cache_file)
        vprint(f"Downloaded to {cache_file}")
    
    # Load words from file
    try:
        with open(cache_file, 'r', encoding='utf-8') as f:
            content = f.read().lower()
            words = content.split()
            
            # Filter to valid words
            valid_words = {w for w in words if w.isalpha() and 2 <= len(w) <= 15}
            
            vprint(f"Loaded {len(valid_words)} words from {cache_file}")
            return valid_words
            
    except Exception as e:
        raise RuntimeError(f"Error loading words from {cache_file}: {e}")


def _download_word_file(url, target_path):
    """Download a word file from URL.
    
    Args:
        url: URL to download from
        target_path: Local path to save to
        
    Raises:
        RuntimeError: If download fails
    """
    # Additional safety check
    if not is_safe_url(url):
        raise RuntimeError(f"Unsafe URL blocked: {url}")
    
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    
    temp_file = target_path + ".tmp"
    
    try:
        # Clean up any existing temp file
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        # Create request with timeout and size limits
        request = urllib.request.Request(url)
        request.add_header('User-Agent', 'nonsense-word-generator/1.0')
        
        with urllib.request.urlopen(request, timeout=30) as response:
            # Validate final URL after redirects
            final_url = response.geturl()
            if not is_safe_url(final_url):
                raise RuntimeError(f"Unsafe redirect target blocked: {final_url}")
            # Optional content type check
            content_type = response.headers.get('Content-Type', '')
            if content_type and not content_type.startswith('text/'):
                raise RuntimeError(f"Unexpected content type: {content_type}")
            # Check content length
            content_length = response.headers.get('Content-Length')
            if content_length and int(content_length) > 50 * 1024 * 1024:  # 50MB limit
                raise RuntimeError("File too large (>50MB)")
            
            # Download with size limit
            max_size = 50 * 1024 * 1024  # 50MB
            downloaded = 0
            
            with open(temp_file, 'wb') as f:
                os.chmod(temp_file, 0o600)
                while True:
                    chunk = response.read(8192)
                    if not chunk:
                        break
                    downloaded += len(chunk)
                    if downloaded > max_size:
                        raise RuntimeError("File too large (>50MB)")
                    f.write(chunk)
        
        # Verify download
        if os.path.getsize(temp_file) == 0:
            raise RuntimeError("Downloaded file is empty")
        
        # Atomic move with symlink check
        if os.path.islink(target_path):
            raise RuntimeError("Refusing to overwrite symlink at target path")
        os.replace(temp_file, target_path)
        
    except Exception as e:
        # Clean up temp file on failure
        if os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except:
                pass
        raise RuntimeError(f"Failed to download from '{url}': {e}")
