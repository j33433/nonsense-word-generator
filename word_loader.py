"""Unified word loading functionality."""

import os
import urllib.request
import urllib.parse
from hunspell import get_hunspell_words, HUNSPELL_DICT_URLS
from cache_manager import CacheManager
from net_utils import is_safe_url, download_file
from constants import WORD_MIN_LEN, WORD_MAX_LEN


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




def load_words(word_source, verbose=False, cache_manager=None, expand_morphology=True):
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
        return get_hunspell_words(lang_code, verbose=verbose, expand_morphology=expand_morphology)
    
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
            return get_hunspell_words(lang_code, verbose=verbose, expand_morphology=expand_morphology)
        
        url = url_or_hunspell
        display_name = word_source
        safe_source = word_source.replace(":", "_")
        cache_file = cache_manager.get_cache_path(f"words_{safe_source}", ".txt")
    
    # Download if not cached
    if not os.path.exists(cache_file):
        vprint(f"Downloading {display_name} word list...")
        download_file(url, cache_file)
        vprint(f"Downloaded to {cache_file}")
    
    # Load words from file
    try:
        valid_words = set()
        with open(cache_file, 'r', encoding='utf-8') as f:
            for line in f:
                for w in line.lower().split():
                    if w.isalpha() and WORD_MIN_LEN <= len(w) <= WORD_MAX_LEN:
                        valid_words.add(w)
        vprint(f"Loaded {len(valid_words)} words from {cache_file}")
        return valid_words
    except Exception as e:
        raise RuntimeError(f"Error loading words from {cache_file}: {e}")


