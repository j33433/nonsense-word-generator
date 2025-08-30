"""Markov chain-based nonsense word generator."""

import secrets
from collections import defaultdict, Counter
from cache_manager import CacheManager
from word_loader import load_words, WORD_URLS


class MarkovWordGenerator:
    """Generate pronounceable nonsense words using Markov chains trained on English words."""
    
    def __init__(self, order=2, cutoff=0.1, verbose=False, words="en", reverse_mode=False):
        """Initialize the Markov chain generator.
        
        Args:
            order: The order of the Markov chain (number of characters to look back)
            cutoff: Minimum probability relative to the most likely choice (0.0-1.0)
            verbose: Print detailed initialization messages
            words: Word list type (en, es, ...) or URL
            reverse_mode: If True, train on reversed words for suffix generation
        """
        self.order = order
        self.cutoff = cutoff
        self.verbose = verbose
        self.word_list_type = words
        self.reverse_mode = reverse_mode
        self.chains = defaultdict(Counter)
        self.start_chains = Counter()
        self.cache_manager = CacheManager()
        
        # Generate cache key
        safe_words = words.replace(":", "_").replace("/", "_").replace(".", "_")
        if len(safe_words) > 50:  # Handle long URLs
            safe_words = f"url_{self.cache_manager.get_url_hash(words)}"
        
        reverse_suffix = "_reversed" if reverse_mode else ""
        self.cache_file = self.cache_manager.get_cache_path(f"markov_chains_order{order}_{safe_words}{reverse_suffix}")
        self.start_marker = "^" * self.order
        
        self._load_or_build_chains()
  
    def _vprint(self, *args, **kwargs):
        """Print only if verbose mode is enabled.
        
        Args:
            *args: Arguments to pass to print()
            **kwargs: Keyword arguments to pass to print()
        """
        if self.verbose:
            print(*args, **kwargs)

    def _process_word_for_chains(self, word):
        """Process a single word to build Markov chains.
        
        Args:
            word: The word to process for chain building
        """
        # Reverse word if in reverse mode for suffix generation
        if self.reverse_mode:
            word = word[::-1]
        
        padded_word = self.start_marker + word + "$"
        
        start_ngram = padded_word[:self.order]
        self.start_chains[start_ngram] += 1
        
        for i in range(len(padded_word) - self.order):
            ngram = padded_word[i:i + self.order]
            next_char = padded_word[i + self.order]
            self.chains[ngram][next_char] += 1

    def _load_and_build_chains(self):
        """Load words and build Markov chains.
        
        Raises:
            RuntimeError: If word loading fails or contains no valid words
        """
        self._vprint("Loading words...")
        self.word_set = load_words(self.word_list_type, verbose=self.verbose, cache_manager=self.cache_manager)
        
        if not self.word_set:
            raise RuntimeError("No valid words found")
        
        self._vprint("Building Markov chains...")
        word_count = 0
        for word in self.word_set:
            self._process_word_for_chains(word)
            word_count += 1
            
            if self.verbose and word_count % 50000 == 0:
                self._vprint(f"Processed {word_count} words...")
        
        self._vprint(f"Built Markov chains with {len(self.chains)} states from {word_count} words")
        self._save_chains()

    def _load_or_build_chains(self):
        """Load chains from cache or build them if cache doesn't exist."""
        if self.cache_manager.should_rebuild(self.cache_file):
            self._vprint("Building Markov chains...")
            self._load_and_build_chains()
        else:
            self._vprint(f"Loading cached chains from {self.cache_file}...")
            self._load_chains()

    def _save_chains(self):
        """Save the built chains to cache."""
        cache_data = {
            'chains': dict(self.chains),
            'start_chains': self.start_chains,
            'word_set': self.word_set,
            'order': self.order,
            'reverse_mode': self.reverse_mode,
            'word_count': len(self.word_set)
        }
        
        if self.cache_manager.save_data(self.cache_file, cache_data):
            self._vprint(f"Saved chains to cache: {self.cache_file}")
        else:
            print("Warning: Could not save cache")

    def _load_chains(self):
        """Load chains from cache."""
        cache_data = self.cache_manager.load_data(self.cache_file)
        
        if (cache_data is None or 
            cache_data.get('order') != self.order or 
            cache_data.get('reverse_mode') != self.reverse_mode):
            self._vprint("Cache invalid or parameters mismatch, rebuilding...")
            self._load_and_build_chains()
            return
        
        self.chains = defaultdict(Counter)
        for key, counter in cache_data['chains'].items():
            self.chains[key] = counter
        
        self.start_chains = cache_data['start_chains']
        self.word_set = cache_data['word_set']
        
        self._vprint(f"Loaded {len(self.chains)} chain states from cache")
        self._vprint(f"Using {cache_data['word_count']} cached training words")

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

    def generate(self, min_len=3, max_len=10, max_retries=200, prefix=None, suffix=None):
        """Generate a single word using the Markov chain.
        
        Args:
            min_len: Minimum word length
            max_len: Maximum word length  
            max_retries: Maximum attempts to generate a valid word
            prefix: Optional prefix to start the word with
            suffix: Optional suffix to end the word with (mutually exclusive with prefix)
            
        Returns:
            str: Generated word that doesn't exist in the training data
            
        Raises:
            ValueError: If min_len > max_len or min_len < 1, or both prefix and suffix provided
        """
        if min_len > max_len or min_len < 1:
            raise ValueError(f"Invalid length parameters: min_len={min_len}, max_len={max_len}")
        
        if prefix and suffix:
            raise ValueError("Cannot specify both prefix and suffix")
        
        if prefix:
            return self.generate_with_prefix(prefix, min_len, max_len, max_retries)
        
        if suffix:
            return self.generate_with_suffix(suffix, min_len, max_len, max_retries)
        
        # Try generating words, with simple fallback after half the retries
        for retry in range(max_retries):
            current = self._weighted_choice(self.start_chains)
            word = ""
            
            # Relax constraints after half the retries
            if retry > max_retries // 2:
                target_min = max(1, min_len - 2)
                target_max = max_len + 3
            else:
                target_min, target_max = min_len, max_len
            
            max_attempts = max_len * 3
            attempts = 0
            
            while attempts < max_attempts:
                attempts += 1
                
                if current not in self.chains:
                    break
                    
                next_char = self._weighted_choice(self.chains[current])
                
                if next_char == "$":
                    if target_min <= len(word) <= target_max and word not in self.word_set:
                        # Reverse the word if we're in reverse mode
                        return word[::-1] if self.reverse_mode else word
                    break
                elif next_char != "^":
                    word += next_char
                    if len(word) >= target_max:
                        break
                
                if next_char != "$":
                    current = current[1:] + next_char
        
        return "word"  # Fallback

    def generate_with_prefix(self, prefix, min_len=3, max_len=10, max_retries=200):
        """Generate a single word starting with the given prefix using the Markov chain.
        
        Args:
            prefix: String to start the word with
            min_len: Minimum word length
            max_len: Maximum word length  
            max_retries: Maximum attempts to generate a valid word
            
        Returns:
            str: Generated word starting with prefix that doesn't exist in the training data
            
        Raises:
            ValueError: If min_len > max_len or min_len < 1
        """
        if min_len > max_len or min_len < 1:
            raise ValueError(f"Invalid length parameters: min_len={min_len}, max_len={max_len}")
        
        if not prefix:
            return self.generate(min_len, max_len, max_retries)
        
        prefix = prefix.lower()
        best_word = ""
        
        for retry in range(max_retries):
            word = prefix
            
            # Initialize the current state based on the prefix
            if len(prefix) >= self.order:
                # Use the last 'order' characters of the prefix as the current state
                current = prefix[-self.order:]
            else:
                # Pad the prefix with start markers to reach the required order
                padded_prefix = self.start_marker + prefix
                if len(padded_prefix) >= self.order:
                    current = padded_prefix[-self.order:]
                else:
                    # If still too short, pad more with start markers
                    current = (self.start_marker * self.order + prefix)[-self.order:]
            
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
        
        return best_word if best_word else prefix

    def generate_with_suffix(self, suffix, min_len=3, max_len=10, max_retries=200):
        """Generate a single word ending with the given suffix using the Markov chain.
        
        Args:
            suffix: String to end the word with
            min_len: Minimum word length
            max_len: Maximum word length  
            max_retries: Maximum attempts to generate a valid word
            
        Returns:
            str: Generated word ending with suffix that doesn't exist in the training data
            
        Raises:
            ValueError: If min_len > max_len or min_len < 1, or not in reverse mode
        """
        if not self.reverse_mode:
            raise ValueError("Suffix generation requires reverse_mode=True")
        
        if min_len > max_len or min_len < 1:
            raise ValueError(f"Invalid length parameters: min_len={min_len}, max_len={max_len}")
        
        if not suffix:
            return self.generate(min_len, max_len, max_retries)
        
        # In reverse mode, the suffix becomes a prefix for the reversed word
        reversed_suffix = suffix.lower()[::-1]
        best_word = ""
        
        for retry in range(max_retries):
            word = reversed_suffix
            
            # Initialize the current state based on the reversed suffix
            if len(reversed_suffix) >= self.order:
                # Use the last 'order' characters of the reversed suffix as the current state
                current = reversed_suffix[-self.order:]
            else:
                # Pad the reversed suffix with start markers to reach the required order
                padded_suffix = self.start_marker + reversed_suffix
                if len(padded_suffix) >= self.order:
                    current = padded_suffix[-self.order:]
                else:
                    # If still too short, pad more with start markers
                    current = (self.start_marker * self.order + reversed_suffix)[-self.order:]
            
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
            
            # Reverse the generated word to get the final result
            final_word = word[::-1]
            
            if final_word and final_word not in self.word_set:
                if min_len <= len(final_word) <= max_len:
                    return final_word
                # Keep the word closest to target length range as fallback
                elif not best_word or abs(len(final_word) - (min_len + max_len) // 2) < abs(len(best_word) - (min_len + max_len) // 2):
                    best_word = final_word
        
        return best_word if best_word else suffix

    def generate_batch(self, count=10, 
                      min_len=3, 
                      max_len=10,
                      prefix=None,
                      suffix=None):
        """Generate multiple words.
        
        Args:
            count: Number of words to generate
            min_len: Minimum word length
            max_len: Maximum word length
            prefix: Optional prefix to start each word with
            suffix: Optional suffix to end each word with (mutually exclusive with prefix)
            
        Returns:
            list: List of generated words
        """
        return [self.generate(min_len, max_len, prefix=prefix, suffix=suffix) for _ in range(count)]

    def generate_batch_with_prefix(self, prefix, count=10, 
                                  min_len=3, 
                                  max_len=10):
        """Generate multiple words starting with the given prefix.
        
        Args:
            prefix: String to start each word with
            count: Number of words to generate
            min_len: Minimum word length
            max_len: Maximum word length
            
        Returns:
            list: List of generated words starting with prefix
        """
        return self.generate_batch(count, min_len, max_len, prefix=prefix)
