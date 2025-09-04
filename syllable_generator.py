"""Syllable-based nonsense word generator."""

import secrets


class SyllableWordGenerator:
    """Generate pronounceable nonsense words using predefined syllable components."""
    
    def __init__(self, rng=None):
        """Initialize word components."""
        self.rng = rng or secrets
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

    def _choice(self, seq):
        return self.rng.choice(seq)

    def _randbelow(self, n):
        if hasattr(self.rng, "randbelow"):
            return self.rng.randbelow(n)
        return self.rng.randrange(n)

    def _make_syllable(self, position="middle"):
        """Create a syllable with onset, nucleus, and optional coda.
        
        Args:
            position: Syllable position in word ("initial", "middle", or "final")
                     Affects probability of including onset/coda components
                     
        Returns:
            str: Generated syllable
        """
        onset = ""
        nucleus = self._choice(self.nuclei)
        coda = ""
        
        # Initial syllables more likely to have onsets, final more likely to have codas
        if position == "initial" or self._randbelow(10) < 8:
            onset = self._choice(self.onsets)
        
        if position == "final" or self._randbelow(10) < 4:
            coda = self._choice(self.codas)
        
        return onset + nucleus + coda

    def generate(self, min_len=3, max_len=10, prefix=None):
        """Generate a single pronounceable word using syllable components.
        
        Args:
            min_len: Minimum word length
            max_len: Maximum word length
            prefix: Optional prefix to start the word with
            
        Returns:
            str: Generated word within the specified length range
            
        Raises:
            ValueError: If min_len > max_len or min_len < 1
        """
        if min_len > max_len or min_len < 1:
            raise ValueError(f"Invalid length parameters: min_len={min_len}, max_len={max_len}")
        
        base = prefix or ""
        max_attempts = 50  # Prevent infinite recursion
        for attempt in range(max_attempts):
            syllables = []
            length = len(base)
            # 1-4 syllables with equal probability
            num_syllables = self._randbelow(4) + 1
            
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
                
                if length >= min_len:
                    break
            
            word = base + "".join(syllables)
            
            if min_len <= len(word) <= max_len:
                return word
        
        return word if 'word' in locals() else (base or "word")

    def generate_batch(self, count=10, 
                      min_len=3, 
                      max_len=10,
                      prefix=None,
                      max_retries=50):
        """Generate multiple pronounceable words.
        
        Args:
            count: Number of words to generate
            min_len: Minimum word length
            max_len: Maximum word length
            prefix: Ignored (syllable generator doesn't support prefixes)
            
        Returns:
            list: List of generated words
        """
        return [self.generate(min_len, max_len, prefix=prefix) for _ in range(count)]
