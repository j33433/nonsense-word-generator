"""Markov chain-based nonsense word generator."""

import secrets
import urllib.request
import os
import pickle
from collections import defaultdict, Counter


class MarkovWordGenerator:
    """Generate pronounceable nonsense words using Markov chains trained on English words."""
    
    def __init__(self, order=2, word_file=None, cutoff=0.1, verbose=False, words="en"):
        """Initialize the Markov chain generator.
        
        Args:
            order: The order of the Markov chain (number of characters to look back)
            word_file: Path to word list file, downloads if None
            cutoff: Minimum probability relative to the most likely choice (0.0-1.0)
            verbose: Print detailed initialization messages
            words: Word list type (en, es, fr, de, it, pt, names, surnames)
        """
        self.order = order
        self.cutoff = cutoff
        self.verbose = verbose
        self.word_list_type = words
        self.chains = defaultdict(Counter)
        self.start_chains = Counter()
        self.word_file = word_file or f"cache/words_{words}.txt"
        self.cache_file = f"cache/markov_chains_order{order}_{words}.pkl"
        
        # Word list URLs
        self.word_urls = {
            "en": "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt",
            "es": "https://raw.githubusercontent.com/JorgeDuenasLerin/diccionario-espanol-txt/master/0_palabras_todas.txt",
            "fr": "https://raw.githubusercontent.com/lorenbrichter/Words/master/Words/fr.txt", 
            "de": "https://raw.githubusercontent.com/lorenbrichter/Words/master/Words/de.txt",
            "it": "https://raw.githubusercontent.com/napolux/paroleitaliane/master/paroleitaliane/280000_parole_italiane.txt",
            "pt": "https://raw.githubusercontent.com/pythonprobr/palavras/master/palavras.txt",
            "names": "https://raw.githubusercontent.com/smashew/NameDatabases/master/NamesDatabases/first%20names/us.txt",
            "surnames": "https://raw.githubusercontent.com/smashew/NameDatabases/master/NamesDatabases/surnames/us.txt",
        }
        
        self._load_or_build_chains()

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
        
        Raises:
            ValueError: If the word list type is not supported
            RuntimeError: If the download fails
        """
        if os.path.exists(self.word_file):
            return
            
        if self.word_list_type not in self.word_urls:
            raise ValueError(f"Unsupported word list: {self.word_list_type}. Supported types: {list(self.word_urls.keys())}")
        
        # Create cache directory if it doesn't exist
        os.makedirs("cache", exist_ok=True)
            
        self._vprint(f"Downloading {self.word_list_type} word list to {self.word_file}...")
        url = self.word_urls[self.word_list_type]
        
        try:
            urllib.request.urlretrieve(url, self.word_file)
            self._vprint(f"Downloaded {self.word_file}")
        except Exception as e:
            raise RuntimeError(f"Failed to download word list for '{self.word_list_type}': {e}")

    def _process_word_for_chains(self, word):
        """Process a single word to build Markov chains.
        
        Args:
            word: The word to process for chain building
        """
        # Pre-allocate start marker string to avoid repeated concatenation
        start_marker = "^" * self.order
        
        # Add start and end markers
        padded_word = start_marker + word + "$"
        
        # Record starting n-grams
        start_ngram = padded_word[:self.order]
        self.start_chains[start_ngram] += 1
        
        # Build transition chains - use more efficient slicing
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
                for line in f:
                    word = line.strip().lower()
                    if word and word.isalpha() and 2 <= len(word) <= 15:
                        self.word_set.add(word)
                        self._process_word_for_chains(word)
                        word_count += 1
                        
                        # Progress indicator for large files
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
        
        # Check if word file is newer than cache
        if os.path.exists(self.word_file):
            word_file_time = os.path.getmtime(self.word_file)
            cache_file_time = os.path.getmtime(self.cache_file)
            if word_file_time > cache_file_time:
                return True
        
        return False

    def _save_chains(self):
        """Save the built chains to a pickle file.
        
        Serializes the Markov chains, start chains, and metadata to a pickle
        file for faster loading in future runs.
        """
        try:
            # Create cache directory if it doesn't exist
            os.makedirs("cache", exist_ok=True)
            
            cache_data = {
                'chains': dict(self.chains),  # Convert defaultdict to regular dict
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
            
            # Verify the cache is for the same order
            if cache_data.get('order') != self.order:
                self._vprint("Cache order mismatch, rebuilding...")
                self._load_and_build_chains()
                return
            
            # Convert back to defaultdict
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
        
        # Find the maximum probability
        total = sum(counter.values())
        if total == 0:
            return ""
        max_weight = max(counter.values())
        max_probability = max_weight / total
        
        # Filter out choices that are much less likely than the most probable
        min_threshold = max_probability * self.cutoff
        filtered_items = []
        filtered_weights = []
        
        for item, weight in counter.items():
            probability = weight / total
            if probability >= min_threshold:
                filtered_items.append(item)
                filtered_weights.append(weight)
        
        # If filtering removed everything, fall back to original counter
        if not filtered_items:
            filtered_items = list(counter.keys())
            filtered_weights = list(counter.values())
        
        # Fast path for small choices
        if len(filtered_items) == 1:
            return filtered_items[0]
        elif len(filtered_items) == 2:
            # Simple binary choice
            if secrets.randbelow(filtered_weights[0] + filtered_weights[1]) < filtered_weights[0]:
                return filtered_items[0]
            else:
                return filtered_items[1]
        
        # Standard weighted choice for larger sets
        filtered_total = sum(filtered_weights)
        r = secrets.randbelow(filtered_total)
        
        for item, weight in zip(filtered_items, filtered_weights):
            r -= weight
            if r < 0:
                return item
        
        return filtered_items[0]

    def generate(self, min_len=3, max_len=10, max_retries=50):
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
            # Start with a random starting n-gram
            current = self._weighted_choice(self.start_chains)
            word = ""
            
            max_attempts = max_len * 3  # Prevent infinite loops
            attempts = 0
            
            while attempts < max_attempts:
                attempts += 1
                
                if current not in self.chains:
                    break
                    
                next_char = self._weighted_choice(self.chains[current])
                
                if next_char == "$":  # End marker
                    # Accept end if word is in valid range
                    if min_len <= len(word) <= max_len:
                        break
                    # If word is too short and we're close to max attempts, accept it anyway
                    elif len(word) >= min_len // 2 and attempts > max_attempts // 2:
                        break
                    # Otherwise ignore the end marker and continue
                elif next_char != "^":  # Skip start markers
                    word += next_char
                    # Stop if we've reached max length
                    if len(word) >= max_len:
                        break
                    # For very short target lengths, be more aggressive about stopping
                    if min_len <= 4 and len(word) >= min_len and secrets.randbelow(3) == 0:
                        break
                
                # Update current state - only if we have a valid next_char
                if next_char != "$":
                    current = current[1:] + next_char
            
            # Keep track of the best word we've seen
            if word and word not in self.word_set:
                if min_len <= len(word) <= max_len:
                    return word
                elif not best_word or abs(len(word) - (min_len + max_len) // 2) < abs(len(best_word) - (min_len + max_len) // 2):
                    best_word = word
        
        # Return the best word we found, even if it doesn't meet exact requirements
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
