import random

class NonsenseWordGenerator:
    def __init__(self):
        # Common prefixes
        self.prefixes = [
            'de', 'ex', 'in', 're', 'un', 'pre', 'con', 'dis', 'pro', 'sub',
            'anti', 'over', 'under', 'out', 'mis', 'non', 'inter', 'super',
            'co', 'counter', 'semi', 'multi', 'bi', 'tri', 'auto', 'micro',
            'mega', 'mini', 'ultra', 'neo', 'pseudo', 'quasi', 'trans',
            'ab', 'ad', 'be', 'com', 'ob', 'per', 'sur', 'syn'
        ]
        
        # Common middle syllables and roots
        self.middle_parts = [
            'cla', 'duc', 'ver', 'tro', 'gam', 'riv', 'tur', 'cal', 'list',
            'col', 'gen', 'well', 'thr', 'fri', 'san', 'ter', 'valv', 'low',
            'rais', 'hair', 'weed', 'man', 'nec', 'poo', 'coal', 'riv', 
            'sher', 'ple', 'dav', 'lar', 'ais', 'mit', 'ort', 'cat', 'koc',
            'bloc', 'part', 'cal', 'grapt', 'smel', 'mull', 'refl', 'ded',
            'dish', 'cash', 'boar', 'kad', 'mass', 'press', 'iti', 'keep',
            'chil', 'boun', 'trig', 'spam', 'flur', 'drot', 'blic', 'nerv',
            'flux', 'glim', 'snarf', 'blim', 'quiv', 'flav', 'grum', 'sniv'
        ]
        
        # Common suffixes
        self.suffixes = [
            'ing', 'ed', 'er', 'est', 'ly', 'tion', 'sion', 'ness', 'ment',
            'able', 'ible', 'ous', 'ful', 'less', 'ward', 'wise', 'like',
            'ship', 'hood', 'dom', 'age', 'ary', 'ory', 'ize', 'ise', 'fy',
            'ate', 'ive', 'ant', 'ent', 'ism', 'ist', 'ity', 'ety', 'acy',
            'al', 'ic', 'ical', 'ous', 'eous', 'ious', 'uous', 'ary', 'ery',
            'ling', 'kin', 'let', 'ette', 'elle', 'ock', 'ook', 'ate', 'ome',
            'oma', 'ics', 'cts', 'get', 'ize', 'isk', 'ing', 'ass', 'ers',
            're', 'es', 'ed', 'ly', 's', 'hs', 'wn', 'ry', 'al', 'ed', 'ly'
        ]
        
        # Short syllables for variety
        self.short_syllables = [
            'a', 'e', 'i', 'o', 'u', 'ay', 'ey', 'oy', 'ow', 'ew',
            'la', 'le', 'li', 'lo', 'lu', 'ra', 're', 'ri', 'ro', 'ru',
            'ta', 'te', 'ti', 'to', 'tu', 'sa', 'se', 'si', 'so', 'su',
            'na', 'ne', 'ni', 'no', 'nu', 'ma', 'me', 'mi', 'mo', 'mu'
        ]
        
        # Vowel combinations for more realistic sounds
        self.vowel_combos = ['ea', 'ie', 'oo', 'ou', 'ue', 'ai', 'ei', 'au', 'aw', 'oy', 'oi']
        
        # Consonant clusters
        self.consonant_clusters = ['st', 'sp', 'sc', 'sk', 'sl', 'sm', 'sn', 'sw', 
                                 'tr', 'tw', 'th', 'sh', 'ch', 'ph', 'gh', 'ck',
                                 'bl', 'br', 'cl', 'cr', 'dr', 'fl', 'fr', 'gl', 
                                 'gr', 'pl', 'pr', 'sc', 'sk', 'sl', 'sm', 'sn',
                                 'sp', 'st', 'sw', 'tr', 'tw', 'wh', 'wr']

    def add_letter_variations(self, word):
        """Add random letter doubling or vowel changes for variety"""
        if random.random() < 0.3:  # 30% chance to modify
            # Double a consonant
            consonants = 'bcdfghjklmnpqrstvwxyz'
            for i, char in enumerate(word):
                if char in consonants and random.random() < 0.1:
                    word = word[:i+1] + char + word[i+1:]
                    break
        
        if random.random() < 0.2:  # 20% chance to add vowel combo
            vowel_combo = random.choice(self.vowel_combos)
            single_vowels = 'aeiou'
            for i, char in enumerate(word):
                if char in single_vowels and random.random() < 0.1:
                    word = word[:i] + vowel_combo + word[i+1:]
                    break
        
        return word

    def generate_word(self, min_length=4, max_length=15):
        """Generate a single nonsense word"""
        word = ""
        target_length = random.randint(min_length, max_length)
        
        # Decide word structure
        structure_type = random.choice(['prefix_middle_suffix', 'middle_suffix', 'prefix_middle', 'compound'])
        
        if structure_type == 'prefix_middle_suffix':
            if random.random() < 0.7:  # 70% chance to use prefix
                word += random.choice(self.prefixes)
            word += random.choice(self.middle_parts)
            if len(word) < target_length - 2:
                word += random.choice(self.middle_parts)
            word += random.choice(self.suffixes)
            
        elif structure_type == 'middle_suffix':
            word += random.choice(self.middle_parts)
            if len(word) < target_length - 3:
                word += random.choice(self.middle_parts)
            word += random.choice(self.suffixes)
            
        elif structure_type == 'prefix_middle':
            word += random.choice(self.prefixes)
            word += random.choice(self.middle_parts)
            if len(word) < target_length:
                word += random.choice(self.middle_parts)
                
        else:  # compound
            word += random.choice(self.middle_parts)
            word += random.choice(self.middle_parts)
            if random.random() < 0.6:
                word += random.choice(self.suffixes)
        
        # Add some short syllables if word is too short
        while len(word) < min_length:
            word += random.choice(self.short_syllables)
        
        # Trim if too long
        if len(word) > max_length:
            word = word[:max_length]
        
        # Add variations
        word = self.add_letter_variations(word)
        
        return word

    def generate_words(self, count=10, min_length=4, max_length=15):
        """Generate multiple nonsense words"""
        words = []
        for _ in range(count):
            word = self.generate_word(min_length, max_length)
            words.append(word)
        return words

    def print_words_in_grid(self, words, columns=5):
        """Print words in a nice grid format"""
        for i in range(0, len(words), columns):
            row = words[i:i+columns]
            print('\t'.join(f"{word:<20s}" for word in row))

# Example usage
if __name__ == "__main__":
    generator = NonsenseWordGenerator()
    
    # Generate a variety of word lengths
    words = []
    words.extend(generator.generate_words(15, 4, 8))    # Short words
    words.extend(generator.generate_words(15, 8, 12))   # Medium words  
    words.extend(generator.generate_words(10, 12, 18))  # Long words
    
    # Shuffle for variety
    random.shuffle(words)
    
    # Print in grid format
    generator.print_words_in_grid(words, 5)
