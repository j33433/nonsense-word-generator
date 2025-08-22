#!/usr/bin/env python3
"""Nonsense word generator using Markov chains or syllable-based generation."""

import secrets
import urllib.request
import os
import argparse
from collections import defaultdict, Counter
from typing import List, Dict, Optional


class SyllableWordGenerator:
    """Generate pronounceable nonsense words using predefined syllable components."""
    
    def __init__(self) -> None:
        """Initialize word components."""
        self.onsets = [
            "b", "c", "d", "f", "g", "h", "j", "k", "l", "m", "n",
            "p", "r", "s", "t", "v", "w", "z",
            "bl", "br", "ch", "cl", "cr", "dr", "fl", "fr",
            "gl", "gr", "pl", "pr", "sc", "sh", "sk", "sl",
            "sm", "sn", "sp", "st", "sw", "th", "tr", "tw"
        ]
        
        self.codas = [
            "b", "d", "f", "g", "k", "l", "m", "n", "p", "r",
            "s", "t", "v", "x", "z",
            "ck", "ct", "ft", "ld", "lf", "lk", "lm", "lp", "lt",
            "mp", "nd", "ng", "nk", "nt", "pt", "rd", "rk", "rm",
            "rn", "rp", "rt", "sk", "sp", "st"
        ]
        
        self.nuclei = [
            "a", "e", "i", "o", "u",
            "ai", "ay", "ea", "ee", "ey", "ie", "oa", "oo", "ou"
        ]

    def _make_syllable(self, position: str = "middle") -> str:
        """Create a syllable."""
        onset = ""
        nucleus = secrets.choice(self.nuclei)
        coda = ""
        
        if position == "initial" or secrets.randbelow(10) < 8:
            onset = secrets.choice(self.onsets)
        
        if position == "final" or secrets.randbelow(10) < 4:
            coda = secrets.choice(self.codas)
        
        return onset + nucleus + coda

    def generate(self, min_len: int = 3, max_len: int = 10) -> str:
        """Generate a single word."""
        if min_len > max_len or min_len < 1:
            raise ValueError("Invalid length parameters")
            
        syllables = []
        length = 0
        num_syllables = secrets.randbelow(4) + 1
        
        for i in range(num_syllables):
            if i == 0:
                syl = self._make_syllable("initial")
            elif i == num_syllables - 1:
                syl = self._make_syllable("final")
            else:
                syl = self._make_syllable("middle")
            
            if length + len(syl) > max_len:
                break
                
            syllables.append(syl)
            length += len(syl)
        
        word = "".join(syllables)
        
        if len(word) < min_len or len(word) > max_len:
            return self.generate(min_len, max_len)
        
        return word

    def generate_batch(self, count: int = 10, 
                      min_len: int = 3, 
                      max_len: int = 10) -> List[str]:
        """Generate multiple words."""
        return [self.generate(min_len, max_len) for _ in range(count)]


class MarkovWordGenerator:
    """Generate pronounceable nonsense words using Markov chains trained on English words."""
    
    def __init__(self, order: int = 2, word_file: Optional[str] = None, min_relative_prob: float = 0.1) -> None:
        """Initialize the Markov chain generator.
        
        Args:
            order: The order of the Markov chain (number of characters to look back)
            word_file: Path to word list file, downloads if None
            min_relative_prob: Minimum probability relative to the most likely choice (0.0-1.0)
        """
        self.order = order
        self.min_relative_prob = min_relative_prob
        self.chains: Dict[str, Counter] = defaultdict(Counter)
        self.start_chains: Counter = Counter()
        self.word_file = word_file or "words.txt"
        
        self._load_words()
        self._build_chains()

    def _download_words(self) -> None:
        """Download a word list if it doesn't exist."""
        if os.path.exists(self.word_file):
            return
            
        print(f"Downloading word list to {self.word_file}...")
        # Using SCOWL (Spell Checker Oriented Word Lists) - common English words
        url = "https://raw.githubusercontent.com/dwyl/english-words/master/words_alpha.txt"
        
        try:
            urllib.request.urlretrieve(url, self.word_file)
            print(f"Downloaded {self.word_file}")
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
        print(f"Created fallback word list: {self.word_file}")

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
            print(f"Loaded {len(self.words)} words from {self.word_file}")
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
        
        print(f"Built Markov chains with {len(self.chains)} states")
        
        # Debug: show top starting patterns and what follows them
        print("Top 10 starting patterns:")
        for ngram, count in self.start_chains.most_common(10):
            print(f"  '{ngram}': {count}")
        
        # Debug: show what characters can follow the start pattern
        start_pattern = "^" * self.order
        if start_pattern in self.chains:
            print(f"\nCharacters that can follow '{start_pattern}':")
            for char, count in self.chains[start_pattern].most_common(20):
                total = sum(self.chains[start_pattern].values())
                prob = count / total
                print(f"  '{char}': {count} ({prob:.3f})")

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
        filtered_counter = Counter()
        
        for item, weight in counter.items():
            probability = weight / total
            if probability >= min_threshold:
                filtered_counter[item] = weight
        
        # If filtering removed everything, fall back to original counter
        if not filtered_counter:
            filtered_counter = counter
        
        filtered_total = sum(filtered_counter.values())
        r = secrets.randbelow(filtered_total)
        
        for item, weight in filtered_counter.items():
            r -= weight
            if r < 0:
                return item
        
        # Fallback
        return secrets.choice(list(filtered_counter.keys()))

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


def main() -> None:
    """Demo the generator."""
    parser = argparse.ArgumentParser(description="Generate nonsense words")
    parser.add_argument("--markov", action="store_true", 
                       help="Use Markov chain generator (default: syllable-based)")
    parser.add_argument("--order", type=int, default=2,
                       help="Markov chain order (default: 2)")
    parser.add_argument("--min-prob", type=float, default=0.1,
                       help="Minimum relative probability threshold (default: 0.1)")
    
    args = parser.parse_args()
    
    if args.markov:
        print("Initializing Markov chain generator...")
        gen = MarkovWordGenerator(order=args.order, min_relative_prob=args.min_prob)
        generator_type = f"order-{gen.order} Markov chains"
        extra_info = f"Minimum relative probability threshold: {gen.min_relative_prob}"
    else:
        print("Initializing syllable-based generator...")
        gen = SyllableWordGenerator()
        generator_type = "syllable components"
        extra_info = ""
    
    print("\nWords (6-12 chars):")
    words = gen.generate_batch(20, 6, 12)
    for i in range(0, len(words), 5):
        print("  ".join(f"{w:<12}" for w in words[i:i+5]))
    
    print("\nWords (4-8 chars):")
    tokens = gen.generate_batch(20, 4, 8)
    for i in range(0, len(tokens), 5):
        print("  ".join(f"{t:<12}" for t in tokens[i:i+5]))

    print("\nPhrase:")
    key = "-".join(gen.generate_batch(3, 4, 8))
    print(key)
    
    if hasattr(gen, 'words'):
        print(f"\nGenerated from {len(gen.words)} training words using {generator_type}")
    else:
        print(f"\nGenerated using {generator_type}")
    
    if extra_info:
        print(extra_info)

if __name__ == "__main__":
    main()
