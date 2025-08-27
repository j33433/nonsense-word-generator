"""Markov chain-based nonsense word generator."""

import secrets
import urllib.request
import os
import pickle
import hashlib
from collections import defaultdict, Counter
from hunspell import get_hunspell_words


WORD_URLS = {
    "en": "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt",
    "es": "https://raw.githubusercontent.com/JorgeDuenasLerin/diccionario-espanol-txt/master/0_palabras_todas.txt",
    "fr": "https://raw.githubusercontent.com/lorenbrichter/Words/master/Words/fr.txt", 
    "de": "https://raw.githubusercontent.com/lorenbrichter/Words/master/Words/de.txt",
    "it": "https://raw.githubusercontent.com/napolux/paroleitaliane/master/paroleitaliane/280000_parole_italiane.txt",
    "pt": "https://raw.githubusercontent.com/pythonprobr/palavras/master/palavras.txt",
    "names": "https://raw.githubusercontent.com/smashew/NameDatabases/master/NamesDatabases/first%20names/us.txt",
    "surnames": "https://raw.githubusercontent.com/smashew/NameDatabases/master/NamesDatabases/surnames/us.txt",
    "pet": "https://raw.githubusercontent.com/jonathand-cf/wordlist-pets/refs/heads/main/pet-names.txt",
    # Hunspell dictionaries (higher quality, morphologically aware)
    "hunspell-en": "hunspell:en",
    "hunspell-es": "hunspell:es", 
    "hunspell-fr": "hunspell:fr",
    "hunspell-de": "hunspell:de",
    "hunspell-it": "hunspell:it",
    "hunspell-pt": "hunspell:pt",
    "hunspell-ru": "hunspell:ru",
    "hunspell-pl": "hunspell:pl",
    "hunspell-nl": "hunspell:nl",
    "hunspell-sv": "hunspell:sv",
    "hunspell-da": "hunspell:da",
    "hunspell-no": "hunspell:no",
    "hunspell-cs": "hunspell:cs",
    "hunspell-hu": "hunspell:hu",
    "hunspell-tr": "hunspell:tr",
    "hunspell-la": "hunspell:la",
}


class MarkovWordGenerator:
    """Generate pronounceable nonsense words using Markov chains trained on English words."""
    
    def __init__(self, order=2, word_file=None, cutoff=0.1, verbose=False, words="en"):
        """Initialize the Markov chain generator.
        
        Args:
            order: The order of the Markov chain (number of characters to look back)
            word_file: Path to word list file, downloads if None
            cutoff: Minimum probability relative to the most likely choice (0.0-1.0)
            verbose: Print detailed initialization messages
            words: Word list type (en, es, ...) or URL
        """
        self.order = order
        self.cutoff = cutoff
        self.verbose = verbose
        self.word_list_type = words
        self.chains = defaultdict(Counter)
        self.start_chains = Counter()
        
        # Handle custom URLs - use hash for safe filename
        if self._is_url(words):
            url_hash = hashlib.md5(words.encode()).hexdigest()
            safe_words = "url"
            self.word_file = word_file or f"cache/words_{safe_words}_{url_hash}.txt"
            self.cache_file = f"cache/markov_chains_order{order}_{safe_words}_{url_hash}.pkl"
        else:
            safe_words = words.replace(":", "_")
            self.word_file = word_file or f"cache/words_{safe_words}.txt"
            self.cache_file = f"cache/markov_chains_order{order}_{safe_words}.pkl"
        
        self.start_marker = "^" * self.order
        
        self._load_or_build_chains()

    def _is_url(self, text):
        """Check if text is a URL.
        
        Args:
            text: String to check
            
        Returns:
            bool: True if text appears to be a URL
        """
        return text.startswith(('http://', 'https://'))
  
    def _vprint(self, *args, **kwargs):
        """Print only if verbose mode is enabled.
        
        Args:
            *args: Arguments to pass to print()
            **kwargs: Keyword arguments to pass to print()
        """
        if self.verbose:
            print(*args, **kwargs)

    def _download_words(self):
        """Download a word list if it doesn't exist.
        
        Downloads the word list for the specified language/type from the internet
        and saves it to the cache directory. Creates the cache directory if needed.
        Uses atomic downloads to prevent corruption from interrupted transfers.
        
        Raises:
            ValueError: If the word list type is not supported
            RuntimeError: If the download fails
        """
        if os.path.exists(self.word_file):
            return
        
        # Handle Hunspell dictionaries
        if self.word_list_type.startswith("hunspell:"):
            lang_code = self.word_list_type.split(":", 1)[1]
            self._vprint(f"Loading Hunspell dictionary for {lang_code}...")
            words = get_hunspell_words(lang_code, verbose=self.verbose)
            
            # Save words to cache file
            os.makedirs("cache", exist_ok=True)
            with open(self.word_file, 'w', encoding='utf-8') as f:
                for word in sorted(words):
                    f.write(word + '\n')
            self._vprint(f"Cached {len(words)} Hunspell words to {self.word_file}")
            return
        
        # Determine URL to download from
        if self._is_url(self.word_list_type):
            url = self.word_list_type
            display_name = f"custom URL ({url})"
        else:
            if self.word_list_type not in WORD_URLS:
                raise ValueError(f"Unsupported word list: {self.word_list_type}. Supported types: {list(WORD_URLS.keys())}")
            
            url_or_hunspell = WORD_URLS[self.word_list_type]
            if url_or_hunspell.startswith("hunspell:"):
                # Redirect to Hunspell handler
                lang_code = url_or_hunspell.split(":", 1)[1]
                self._vprint(f"Loading Hunspell dictionary for {lang_code}...")
                words = get_hunspell_words(lang_code, verbose=self.verbose)
                
                # Save words to cache file
                os.makedirs("cache", exist_ok=True)
                with open(self.word_file, 'w', encoding='utf-8') as f:
                    for word in sorted(words):
                        f.write(word + '\n')
                self._vprint(f"Cached {len(words)} Hunspell words to {self.word_file}")
                return
            
            url = url_or_hunspell
            display_name = self.word_list_type
        
        os.makedirs("cache", exist_ok=True)
            
        self._vprint(f"Downloading {display_name} word list to {self.word_file}...")
        
        # Use temporary file for atomic download
        temp_file = self.word_file + ".tmp"
        
        try:
            # Clean up any existing temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            urllib.request.urlretrieve(url, temp_file)
            
            # Verify the download has some content
            if os.path.getsize(temp_file) == 0:
                raise RuntimeError("Downloaded file is empty")
            
            # Atomic move - only replace the target file if download succeeded
            os.rename(temp_file, self.word_file)
            self._vprint(f"Downloaded {self.word_file}")
            
        except Exception as e:
            # Clean up temp file on failure
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
            raise RuntimeError(f"Failed to download word list from '{url}': {e}")

    def _process_word_for_chains(self, word):
        """Process a single word to build Markov chains.
        
        Args:
            word: The word to process for chain building
        """
        padded_word = self.start_marker + word + "$"
        
        start_ngram = padded_word[:self.order]
        self.start_chains[start_ngram] += 1
        
        for i in range(len(padded_word) - self.order):
            ngram = padded_word[i:i + self.order]
            next_char = padded_word[i + self.order]
            self.chains[ngram][next_char] += 1

    def _load_and_build_chains(self):
        """Load words from file and build Markov chains in a single pass.
        
        Downloads the word list if necessary, then processes each word to build
        Markov chains without storing all words in memory simultaneously.
        
        Raises:
            RuntimeError: If the word file cannot be loaded or contains no valid words
        """
        self._download_words()
        
        self.word_set = set()
        word_count = 0
        
        try:
            with open(self.word_file, 'r', encoding='utf-8') as f:
                # Batch process: read all content at once and split
                content = f.read().lower()
                words = content.split()
                
                # Only use alphabetic words 2-15 chars (filters noise and extremes)
                valid_words = [w for w in words if w.isalpha() and 2 <= len(w) <= 15]
                
                for word in valid_words:
                    self.word_set.add(word)
                    self._process_word_for_chains(word)
                    word_count += 1
                    
                    if self.verbose and word_count % 50000 == 0:
                        self._vprint(f"Processed {word_count} words...")
                    
            self._vprint(f"Loaded and processed {word_count} words from {self.word_file}")
            self._vprint(f"Built Markov chains with {len(self.chains)} states")
            
            if word_count == 0:
                raise RuntimeError(f"No valid words found in {self.word_file}")
                
        except Exception as e:
            raise RuntimeError(f"Error loading words from {self.word_file}: {e}")
        
        self._save_chains()

    def _load_or_build_chains(self):
        """Load chains from cache or build them if cache doesn't exist or is outdated.
        
        Checks if cached chains exist and are newer than the word file.
        If not, rebuilds the chains from scratch.
        """
        if self._should_rebuild_cache():
            self._vprint("Building Markov chains...")
            self._load_and_build_chains()
        else:
            self._vprint(f"Loading cached chains from {self.cache_file}...")
            self._load_chains()

    def _should_rebuild_cache(self):
        """Check if we need to rebuild the cache.
        
        Returns:
            bool: True if cache doesn't exist or is older than word file
        """
        if not os.path.exists(self.cache_file):
            return True
        
        if os.path.exists(self.word_file):
            word_file_time = os.path.getmtime(self.word_file)
            cache_file_time = os.path.getmtime(self.cache_file)
            # Rebuild cache if word file is newer (user updated word lists)
            if word_file_time > cache_file_time:
                return True
        
        return False

    def _save_chains(self):
        """Save the built chains to a pickle file.
        
        Serializes the Markov chains, start chains, and metadata to a pickle
        file for faster loading in future runs.
        """
        try:
            os.makedirs("cache", exist_ok=True)
            
            cache_data = {
                'chains': dict(self.chains),
                'start_chains': self.start_chains,
                'word_set': self.word_set,
                'order': self.order,
                'word_count': len(self.word_set)
            }
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            self._vprint(f"Saved chains to cache: {self.cache_file}")
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")

    def _load_chains(self):
        """Load chains from pickle file.
        
        Deserializes previously saved Markov chains from cache.
        If loading fails or cache is incompatible, rebuilds chains.
        """
        try:
            with open(self.cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            if cache_data.get('order') != self.order:
                self._vprint("Cache order mismatch, rebuilding...")
                self._load_and_build_chains()
                return
            
            self.chains = defaultdict(Counter)
            for key, counter in cache_data['chains'].items():
                self.chains[key] = counter
            
            self.start_chains = cache_data['start_chains']
            self.word_set = cache_data['word_set']
            
            self._vprint(f"Loaded {len(self.chains)} chain states from cache")
            self._vprint(f"Using {cache_data['word_count']} cached training words")
            
        except Exception as e:
            self._vprint(f"Error loading cache: {e}")
            self._vprint("Rebuilding chains...")
            self._load_and_build_chains()

    def _weighted_choice(self, counter):
        """Choose randomly from a Counter, filtering by relative probability.
        
        Filters out choices that are much less likely than the most probable
        choice based on the cutoff threshold, then makes a weighted random selection.
        
        Args:
            counter: Counter object with items and their frequencies
            
        Returns:
            str: Randomly selected item, or empty string if counter is empty
        """
        if not counter:
            return ""
        
        total = sum(counter.values())
        if total == 0:
            return ""
        max_weight = max(counter.values())
        max_probability = max_weight / total
        
        # This filters out rare transitions to improve word quality
        # by only considering choices within cutoff% of the most likely option
        min_threshold = max_probability * self.cutoff
        filtered_items = []
        filtered_weights = []
        
        for item, weight in counter.items():
            probability = weight / total
            if probability >= min_threshold:
                filtered_items.append(item)
                filtered_weights.append(weight)
        
        if not filtered_items:
            filtered_items = list(counter.keys())
            filtered_weights = list(counter.values())
        
        if len(filtered_items) == 1:
            return filtered_items[0]
        elif len(filtered_items) == 2:
            if secrets.randbelow(filtered_weights[0] + filtered_weights[1]) < filtered_weights[0]:
                return filtered_items[0]
            else:
                return filtered_items[1]
        
        filtered_total = sum(filtered_weights)
        r = secrets.randbelow(filtered_total)
        
        for item, weight in zip(filtered_items, filtered_weights):
            r -= weight
            if r < 0:
                return item
        
        return filtered_items[0]

    def generate(self, min_len=3, max_len=10, max_retries=200):
        """Generate a single word using the Markov chain.
        
        Args:
            min_len: Minimum word length
            max_len: Maximum word length  
            max_retries: Maximum attempts to generate a valid word
            
        Returns:
            str: Generated word that doesn't exist in the training data
            
        Raises:
            ValueError: If min_len > max_len or min_len < 1
        """
        if min_len > max_len or min_len < 1:
            raise ValueError(f"Invalid length parameters: min_len={min_len}, max_len={max_len}")
        
        best_word = ""
        
        for retry in range(max_retries):
            current = self._weighted_choice(self.start_chains)
            word = ""
            
            max_attempts = max_len * 3
            attempts = 0
            
            while attempts < max_attempts:
                attempts += 1
                
                if current not in self.chains:
                    break
                    
                next_char = self._weighted_choice(self.chains[current])
                
                if next_char == "$":
                    if min_len <= len(word) <= max_len:
                        break
                    elif len(word) >= min_len // 2 and attempts > max_attempts // 2:
                        break
                elif next_char != "^":
                    word += next_char
                    if len(word) >= max_len:
                        break
                
                if next_char != "$":
                    current = current[1:] + next_char
            
            if word and word not in self.word_set:
                if min_len <= len(word) <= max_len:
                    return word
                # Keep the word closest to target length range as fallback
                elif not best_word or abs(len(word) - (min_len + max_len) // 2) < abs(len(best_word) - (min_len + max_len) // 2):
                    best_word = word
        
        return best_word if best_word else "word"

    def generate_batch(self, count=10, 
                      min_len=3, 
                      max_len=10):
        """Generate multiple words.
        
        Args:
            count: Number of words to generate
            min_len: Minimum word length
            max_len: Maximum word length
            
        Returns:
            list: List of generated words
        """
        return [self.generate(min_len, max_len) for _ in range(count)]
