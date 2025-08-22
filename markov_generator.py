"""Markov chain-based nonsense word generator."""

import secrets
import urllib.request
import os
import pickle
from collections import defaultdict, Counter
from typing import List, Dict, Optional


class MarkovWordGenerator:
    """Generate pronounceable nonsense words using Markov chains trained on English words."""
    
    def __init__(self, order: int = 2, word_file: Optional[str] = None, min_relative_prob: float = 0.1, verbose: bool = False) -> None:
        """Initialize the Markov chain generator.
        
        Args:
            order: The order of the Markov chain (number of characters to look back)
            word_file: Path to word list file, downloads if None
            min_relative_prob: Minimum probability relative to the most likely choice (0.0-1.0)
            verbose: Print detailed initialization messages
        """
        self.order = order
        self.min_relative_prob = min_relative_prob
        self.verbose = verbose
        self.chains: Dict[str, Counter] = defaultdict(Counter)
        self.start_chains: Counter = Counter()
        self.word_file = word_file or "words.txt"
        self.cache_file = f"markov_chains_order{order}.pkl"
        
        self._load_words()
        self._load_or_build_chains()

    def _vprint(self, *args, **kwargs) -> None:
        """Print only if verbose mode is enabled."""
        if self.verbose:
            print(*args, **kwargs)

    def _download_words(self) -> None:
        """Download a word list if it doesn't exist."""
        if os.path.exists(self.word_file):
            return
            
        self._vprint(f"Downloading word list to {self.word_file}...")
        # Using SCOWL (Spell Checker Oriented Word Lists) - common English words
        url = "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"
        
        try:
            urllib.request.urlretrieve(url, self.word_file)
            self._vprint(f"Downloaded {self.word_file}")
        except Exception as e:
            print(f"Failed to download word list: {e}")
            # Fallback to a smaller built-in list
            self._create_fallback_wordlist()

    def _create_fallback_wordlist(self) -> None:
        """Create a small fallback word list if download fails."""
        fallback_words = [
            "the", "and", "for", "are", "but", "not", "you", "all", "can", "had", "her", "was", "one", "our", "out", "day", "get", "has", "him", "his", "how", "man", "new", "now", "old", "see", "two", "way", "who", "boy", "did", "its", "let", "put", "say", "she", "too", "use",
            "about", "after", "again", "before", "being", "could", "every", "first", "found", "great", "group", "house", "large", "light", "little", "long", "made", "make", "many", "most", "move", "much", "name", "never", "night", "number", "other", "part", "place", "right", "same", "seem", "small", "sound", "still", "such", "take", "than", "that", "their", "there", "these", "they", "thing", "think", "this", "those", "three", "time", "very", "water", "well", "were", "what", "where", "which", "while", "with", "work", "world", "would", "write", "year", "young"
        ]
        
        with open(self.word_file, 'w') as f:
            for word in fallback_words:
                f.write(word + '\n')
        self._vprint(f"Created fallback word list: {self.word_file}")

    def _load_words(self) -> None:
        """Load words from file, downloading if necessary."""
        self._download_words()
        
        self.words = []
        try:
            with open(self.word_file, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip().lower()
                    if word and word.isalpha() and 2 <= len(word) <= 15:
                        self.words.append(word)
            self._vprint(f"Loaded {len(self.words)} words from {self.word_file}")
        except Exception as e:
            print(f"Error loading words: {e}")
            self.words = ["hello", "world", "python", "code"]
        
        # Create a set for fast dictionary lookup
        self.word_set = set(self.words)

    def _build_chains(self) -> None:
        """Build Markov chains from the word list."""
        for word in self.words:
            # Add start marker
            padded_word = "^" * self.order + word + "$"
            
            # Record starting n-grams
            start_ngram = padded_word[:self.order]
            if start_ngram not in self.start_chains:
                self.start_chains[start_ngram] = 0
            self.start_chains[start_ngram] += 1
            
            # Build transition chains
            for i in range(len(padded_word) - self.order):
                ngram = padded_word[i:i + self.order]
                next_char = padded_word[i + self.order]
                self.chains[ngram][next_char] += 1
        
        self._vprint(f"Built Markov chains with {len(self.chains)} states")
        self._save_chains()

    def _load_or_build_chains(self) -> None:
        """Load chains from cache or build them if cache doesn't exist or is outdated."""
        if self._should_rebuild_cache():
            self._vprint("Building Markov chains...")
            self._build_chains()
        else:
            self._vprint(f"Loading cached chains from {self.cache_file}...")
            self._load_chains()

    def _should_rebuild_cache(self) -> bool:
        """Check if we need to rebuild the cache."""
        if not os.path.exists(self.cache_file):
            return True
        
        # Check if word file is newer than cache
        if os.path.exists(self.word_file):
            word_file_time = os.path.getmtime(self.word_file)
            cache_file_time = os.path.getmtime(self.cache_file)
            if word_file_time > cache_file_time:
                return True
        
        return False

    def _save_chains(self) -> None:
        """Save the built chains to a pickle file."""
        try:
            cache_data = {
                'chains': dict(self.chains),  # Convert defaultdict to regular dict
                'start_chains': self.start_chains,
                'word_set': self.word_set,
                'order': self.order,
                'word_count': len(self.words)
            }
            with open(self.cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            self._vprint(f"Saved chains to cache: {self.cache_file}")
        except Exception as e:
            print(f"Warning: Could not save cache: {e}")

    def _load_chains(self) -> None:
        """Load chains from pickle file."""
        try:
            with open(self.cache_file, 'rb') as f:
                cache_data = pickle.load(f)
            
            # Verify the cache is for the same order
            if cache_data.get('order') != self.order:
                self._vprint("Cache order mismatch, rebuilding...")
                self._build_chains()
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
            self._build_chains()

    def _weighted_choice(self, counter: Counter) -> str:
        """Choose randomly from a Counter, filtering by relative probability to the most likely choice."""
        if not counter:
            return ""
        
        # Find the maximum probability
        total = sum(counter.values())
        max_weight = max(counter.values())
        max_probability = max_weight / total
        
        # Filter out choices that are much less likely than the most probable
        min_threshold = max_probability * self.min_relative_prob
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
        
        # Simple weighted selection
        filtered_total = sum(filtered_weights)
        r = secrets.randbelow(filtered_total)
        
        for item, weight in zip(filtered_items, filtered_weights):
            r -= weight
            if r < 0:
                return item
        
        # Final fallback
        return secrets.choice(filtered_items)

    def generate(self, min_len: int = 3, max_len: int = 10, max_retries: int = 10) -> str:
        """Generate a single word using the Markov chain."""
        if min_len > max_len or min_len < 1:
            raise ValueError("Invalid length parameters")
        
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
                    break
                elif next_char != "^":  # Skip start markers
                    word += next_char
                    if len(word) >= max_len:
                        break
                
                # Update current state
                current = current[1:] + next_char
            
            # If word is too short or too long, try again (with limit)
            if len(word) < min_len or len(word) > max_len:
                if attempts < max_attempts // 2:
                    continue  # Try generating a new word
                else:
                    # Fallback: truncate or pad
                    if len(word) > max_len:
                        word = word[:max_len]
                    elif len(word) < min_len and word:
                        # Try to extend with common endings
                        while len(word) < min_len:
                            word += secrets.choice("aeiou")
            
            # Check if the generated word is in the dictionary
            if word and word not in self.word_set:
                return word
        
        # If we couldn't generate a non-dictionary word after max_retries, return anyway
        return word if word else "word"

    def generate_batch(self, count: int = 10, 
                      min_len: int = 3, 
                      max_len: int = 10) -> List[str]:
        """Generate multiple words."""
        return [self.generate(min_len, max_len) for _ in range(count)]


# Keep the old class name for compatibility
NonsenseWordGenerator = MarkovWordGenerator
