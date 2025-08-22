"""Syllable-based nonsense word generator."""

import secrets
from typing import List


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
