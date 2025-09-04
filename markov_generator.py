"""Markov chain-based nonsense word generator."""

import secrets
from collections import defaultdict, Counter
from errors import GenerationError
from cache_manager import CacheManager
from word_loader import load_words
from debug import Debug


class MarkovWordGenerator:
    """Generate pronounceable nonsense words using Markov chains trained on English words."""
    
    SCHEMA_VERSION = 1
    def __init__(self, order=2, cutoff=0.1, verbose=False, words="en", reverse_mode=False, trace=False, morphology=True, rng=None):
        """Initialize the Markov chain generator.
        
        Args:
            order: The order of the Markov chain (number of characters to look back)
            cutoff: Minimum probability relative to the most likely choice (0.0-1.0)
            verbose: Print detailed initialization messages
            words: Word list type (en, es, ...) or URL
            reverse_mode: If True, train on reversed words for suffix generation
            trace: If True, show character-by-character generation trace
        """
        self.order = order
        self.cutoff = cutoff
        self.word_list_type = words
        self.reverse_mode = reverse_mode
        self.trace = trace
        self.dbg = Debug(verbose, trace)
        self.chains = defaultdict(Counter)
        self.start_chains = Counter()
        self.cache_manager = CacheManager()
        self.morphology = morphology
        self.rng = rng or secrets
        
        # Generate cache key
        safe_words = words.replace(":", "_").replace("/", "_").replace(".", "_")
        if len(safe_words) > 50:  # Handle long URLs
            safe_words = f"url_{self.cache_manager.get_url_hash(words)}"
        cache_key = self.cache_manager.build_cache_key("markov_chains", {
            "order": order,
            "words": safe_words,
            "reverse": reverse_mode,
            "schema": self.SCHEMA_VERSION
        })
        self.cache_file = self.cache_manager.get_cache_path(cache_key)
        self.start_marker = "^" * self.order
        
        self._load_or_build_chains()
  

    def _process_word_for_chains(self, word):
        """Process a single word to build Markov chains.
        
        Args:
            word: The word to process for chain building
        """
        # Reverse word if in reverse mode for suffix generation
        if self.reverse_mode:
            word = word[::-1]
        
        padded_word = self.start_marker + word + "$"
        
        self.start_chains[padded_word[:self.order]] += 1
        
        for i in range(len(padded_word) - self.order):
            ngram = padded_word[i:i + self.order]
            next_char = padded_word[i + self.order]
            self.chains[ngram][next_char] += 1

    def _load_and_build_chains(self):
        """Load words and build Markov chains.
        
        Raises:
            RuntimeError: If word loading fails or contains no valid words
        """
        self.dbg.print("Loading words...")
        self.word_set = load_words(self.word_list_type, verbose=self.dbg.verbose, cache_manager=self.cache_manager, expand_morphology=self.morphology)
        
        if not self.word_set:
            raise RuntimeError("No valid words found")
        
        self.dbg.print("Building Markov chains...")
        word_count = 0
        for word in self.word_set:
            self._process_word_for_chains(word)
            word_count += 1
            
            if word_count % 50000 == 0:
                self.dbg.print(f"Processed {word_count} words...")
        
        self.dbg.print(f"Built Markov chains with {len(self.chains)} states from {word_count} words")
        self._save_chains()

    def _load_or_build_chains(self):
        """Load chains from cache or build them if cache doesn't exist."""
        if self.cache_manager.should_rebuild(self.cache_file):
            self.dbg.print("Building Markov chains...")
            self._load_and_build_chains()
        else:
            self.dbg.print(f"Loading cached chains from {self.cache_file}...")
            self._load_chains()

    def _save_chains(self):
        """Save the built chains to cache."""
        cache_data = {
            'chains': dict(self.chains),
            'start_chains': self.start_chains,
            'order': self.order,
            'reverse_mode': self.reverse_mode,
            'word_count': len(self.word_set),
            'schema_version': self.SCHEMA_VERSION
        }
        
        if self.cache_manager.save_data(self.cache_file, cache_data):
            self.dbg.print(f"Saved chains to cache: {self.cache_file}")
        else:
            self.dbg.print("Warning: Could not save cache")



    def _load_chains(self):
        """Load chains from cache."""
        cache_data = self.cache_manager.load_data(self.cache_file)
        
        if (cache_data is None or 
            cache_data.get('order') != self.order or 
            cache_data.get('reverse_mode') != self.reverse_mode or
            cache_data.get('schema_version') != self.SCHEMA_VERSION):
            self.dbg.print("Cache invalid or parameters mismatch, rebuilding...")
            self._load_and_build_chains()
            return
        
        self.chains = defaultdict(Counter)
        for key, counter in cache_data['chains'].items():
            self.chains[key] = counter
        
        self.start_chains = cache_data['start_chains']
        
        # Load word set fresh from word_loader (it's already cached there)
        self.word_set = load_words(self.word_list_type, verbose=False, cache_manager=self.cache_manager, expand_morphology=self.morphology)
        
        self.dbg.print(f"Loaded {len(self.chains)} chain states from cache")
        self.dbg.print(f"Using {cache_data['word_count']} cached training words")

    def _randbelow(self, n):
        """Random integer in [0, n) using injected RNG."""
        if hasattr(self.rng, "randbelow"):
            return self.rng.randbelow(n)
        # Fallback for random.Random
        return self.rng.randrange(n)

    def _choice(self, seq):
        """Random choice using injected RNG."""
        return self.rng.choice(seq)

    def _weighted_choice(self, counter, context=""):
        """Choose randomly from a Counter, filtering by relative probability.
        
        Filters out choices that are much less likely than the most probable
        choice based on the cutoff threshold, then makes a weighted random selection.
        
        Args:
            counter: Counter object with items and their frequencies
            context: Context string for trace output (current n-gram)
            
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
        items_weights = [(item, weight) for item, weight in counter.items() if (weight / total) >= min_threshold]
        if not items_weights:
            items_weights = list(counter.items())
        items, weights = zip(*items_weights)
        r = self._randbelow(sum(weights))
        for item, weight in zip(items, weights):
            r -= weight
            if r < 0:
                chosen = item
                break
        else:
            chosen = items[0]
        
        # Show trace information if enabled
        if context:
            options = [(item, weight, weight / total) for item, weight in zip(items, weights)]
            self.dbg.state_transition(context, options, chosen)
        
        return chosen

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
            return self.generate_with_prefix_and_suffix(prefix, suffix, min_len, max_len, max_retries)
        
        if prefix:
            return self.generate_with_prefix(prefix, min_len, max_len, max_retries)
        
        if suffix:
            return self.generate_with_suffix(suffix, min_len, max_len, max_retries)
        
        # Try generating words, with simple fallback after half the retries
        for retry in range(max_retries):
            self.dbg.generation_attempt(retry + 1)
            
            # Always start fresh from start_chains - no need to reset entire chain state
            current = self._weighted_choice(self.start_chains, "START")
            word = ""
            
            self.dbg.trace(f"Initial state: '{current}'")
            
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
                    self.dbg.trace(f"No transitions found for '{current}' - stopping")
                    break
                    
                next_char = self._weighted_choice(self.chains[current], current)
                
                if next_char == "$":
                    self.dbg.word_progress("End marker reached", None, word, len(word))
                    if target_min <= len(word) <= target_max and word not in self.word_set:
                        final_word = word[::-1] if self.reverse_mode else word
                        self.dbg.result(True, final_word)
                        return final_word
                    self.dbg.result(False, word, f"length {len(word)} not in range {target_min}-{target_max} or exists in training data")
                    break
                elif next_char != "^":
                    word += next_char
                    self.dbg.word_progress("Added", next_char, word, len(word))
                    if len(word) >= target_max:
                        self.dbg.trace(f"Maximum length {target_max} reached - stopping")
                        break
                
                if next_char != "$":
                    current = current[1:] + next_char
                    if next_char != "^":
                        self.dbg.trace(f"New state: '{current}'")
        
        # Raise a helpful exception with suggestions
        tips = [
            "Try adjusting parameters:",
            f"  - Decrease --cutoff (current: {self.cutoff}) to allow more character transitions",
            f"  - Try a lower --order (current: {self.order}) for more flexibility",
            f"  - Widen length range (current: {min_len}-{max_len})",
            f"  - Try a different word list (current: {self.word_list_type})"
        ]
        if prefix:
            tips.append(f"  - Use a shorter or different prefix (current: '{prefix}')")
        if suffix:
            tips.append(f"  - Use a shorter or different suffix (current: '{suffix}')")
        message = "Error: Could not generate a valid word after {} attempts.\n{}".format(
            max_retries, "\n".join(tips)
        )
        raise GenerationError(message)

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
                # self.start_marker is already 'order' characters long (e.g., '^^' for order=2)
                current = (self.start_marker + prefix)[-self.order:]
            
            self.dbg.generation_attempt(retry + 1, "Prefix")
            self.dbg.trace(f"Prefix: '{prefix}', Initial state: '{current}'")
            
            max_attempts = max_len * 3
            attempts = 0
            
            while attempts < max_attempts:
                attempts += 1
                
                if current not in self.chains:
                    self.dbg.trace(f"No transitions found for '{current}' - stopping")
                    break
                    
                next_char = self._weighted_choice(self.chains[current], current)
                
                if next_char == "$":
                    self.dbg.word_progress("End marker reached", None, word, len(word))
                    if min_len <= len(word) <= max_len:
                        break
                    elif len(word) >= min_len // 2 and attempts > max_attempts // 2:
                        self.dbg.trace("Accepting shorter word due to retry limit")
                        break
                elif next_char != "^":
                    word += next_char
                    self.dbg.word_progress("Added", next_char, word, len(word))
                    if len(word) >= max_len:
                        self.dbg.trace(f"Maximum length {max_len} reached - stopping")
                        break
                
                if next_char != "$":
                    current = current[1:] + next_char
                    if next_char != "^":
                        self.dbg.trace(f"New state: '{current}'")
            
            if word and word not in self.word_set:
                if min_len <= len(word) <= max_len:
                    self.dbg.result(True, word, "with prefix")
                    return word
                # Keep the word closest to target length range as fallback
                elif not best_word or abs(len(word) - (min_len + max_len) // 2) < abs(len(best_word) - (min_len + max_len) // 2):
                    best_word = word
                    self.dbg.trace(f"Keeping as best candidate: '{word}'")
        
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
                # self.start_marker is already 'order' characters long (e.g., '^^' for order=2)
                current = (self.start_marker + reversed_suffix)[-self.order:]
            
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

    def generate_with_prefix_and_suffix(self, prefix, suffix, min_len=3, max_len=10, max_retries=200):
        """Generate a word with both prefix and suffix using bidirectional generation.
        
        This uses a clever trick: generate a word in reverse mode that starts with the 
        reversed suffix and ends with the reversed prefix, then reverse the entire result.
        
        Args:
            prefix: String to start the word with
            suffix: String to end the word with
            min_len: Minimum word length
            max_len: Maximum word length  
            max_retries: Maximum attempts to generate a valid word
            
        Returns:
            str: Generated word with both prefix and suffix
            
        Raises:
            ValueError: If min_len > max_len or min_len < 1
        """
        if min_len > max_len or min_len < 1:
            raise ValueError(f"Invalid length parameters: min_len={min_len}, max_len={max_len}")
        
        if not prefix or not suffix:
            if prefix:
                return self.generate_with_prefix(prefix, min_len, max_len, max_retries)
            elif suffix:
                return self.generate_with_suffix(suffix, min_len, max_len, max_retries)
            else:
                return self.generate(min_len, max_len, max_retries)
        
        prefix = prefix.lower()
        suffix = suffix.lower()
        
        # Check if prefix + suffix alone would exceed max_len
        if len(prefix) + len(suffix) > max_len:
            # Fallback: just use prefix
            return self.generate_with_prefix(prefix, min_len, max_len, max_retries)
        
        # Create or use reverse-mode generator
        if not self.reverse_mode:
            # Create a temporary reverse-mode generator
            reverse_gen = MarkovWordGenerator(
                order=self.order, 
                cutoff=self.cutoff, 
                verbose=False, 
                words=self.word_list_type, 
                reverse_mode=True,
                trace=self.trace
            )
        else:
            reverse_gen = self
        
        reversed_suffix = suffix[::-1]
        reversed_prefix = prefix[::-1]
        best_word = ""
        
        # Try to generate a word that starts with reversed_suffix and ends with reversed_prefix
        for retry in range(max_retries):
            self.dbg.generation_attempt(retry + 1, "Prefix+Suffix")
            self.dbg.trace(f"Prefix: '{prefix}', Suffix: '{suffix}', Target middle length: {min_len - len(prefix) - len(suffix)}-{max_len - len(prefix) - len(suffix)}")
            self.dbg.trace(f"Current word so far: '{prefix}' (will add middle, then '{suffix}')")
            
            # Determine a likely join character after the prefix in forward direction
            if len(prefix) >= self.order:
                forward_state = prefix[-self.order:]
            else:
                forward_state = (self.start_marker + prefix)[-self.order:]
            join_char = ""
            if forward_state in self.chains:
                join_char = self._weighted_choice(self.chains[forward_state], forward_state)
            
            # Generate with reversed suffix as prefix
            temp_word = reverse_gen.generate_with_prefix(
                reversed_suffix, 
                min_len, 
                max_len, 
                max_retries=50  # Fewer retries per attempt since we have outer retry loop
            )
            
            # Check if it naturally ends with reversed prefix
            if temp_word.endswith(reversed_prefix):
                final_word = temp_word[::-1]
                if final_word not in self.word_set and min_len <= len(final_word) <= max_len:
                    self.dbg.result(True, final_word, "with prefix and suffix")
                    return final_word
                elif not best_word or abs(len(final_word) - (min_len + max_len) // 2) < abs(len(best_word) - (min_len + max_len) // 2):
                    best_word = final_word
            
            # Alternative: try to force the connection by truncating and appending
            if len(temp_word) > len(reversed_suffix):
                # Remove the reversed_suffix part and attempt a join that respects the forward chain's next-char
                middle_part = temp_word[len(reversed_suffix):]
                # Only allow forced join if we have a predicted join_char and a non-empty middle that matches it
                if join_char and middle_part and middle_part[-1] == join_char:
                    if len(middle_part) + len(reversed_suffix) + len(reversed_prefix) <= max_len:
                        forced_word = reversed_suffix + middle_part + reversed_prefix
                        final_word = forced_word[::-1]
                        if (final_word not in self.word_set and 
                            min_len <= len(final_word) <= max_len and
                            final_word.startswith(prefix) and 
                            final_word.endswith(suffix)):
                            self.dbg.result(True, final_word, "with prefix and suffix")
                            return final_word
                        elif not best_word or abs(len(final_word) - (min_len + max_len) // 2) < abs(len(best_word) - (min_len + max_len) // 2):
                            best_word = final_word
        
        # Final fallback: simple concatenation with minimal middle
        if not best_word:
            middle = "a" if len(prefix) + len(suffix) + 1 <= max_len else ""
            best_word = prefix + middle + suffix
        
        return best_word

    def generate_batch(self, count=10, 
                      min_len=3, 
                      max_len=10,
                      prefix=None,
                      suffix=None,
                      max_retries=200):
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
        return [self.generate(min_len, max_len, max_retries=max_retries, prefix=prefix, suffix=suffix) for _ in range(count)]

