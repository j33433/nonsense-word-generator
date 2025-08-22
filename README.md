# Nonsense Word Generator

Generates pronounceable nonsense words that sound like English but probably aren't.

Two generation methods available:
- **Syllable-based**: Fast generation using phonetic rules (default)
- **Markov chains**: More realistic words trained on English dictionary

## Installation

```bash
git clone https://github.com/j33433/nonsense-word-generator.git
cd nonsense-word-generator
python nonsense_generator.py
```

## Command Line Usage

```bash
# Generate words using syllable-based method (default)
python nonsense_generator.py

# Generate words using Markov chains (more realistic)
python nonsense_generator.py --markov

# Adjust Markov chain parameters
python nonsense_generator.py --markov --order 3 --min-prob 0.05
```

## Python API Usage

### Syllable-based Generator

```python
from syllable_generator import SyllableWordGenerator

generator = SyllableWordGenerator()

# Generate a single word
word = generator.generate()
print(word)  # e.g., "blairthook"

# Generate with specific length
word = generator.generate(min_len=6, max_len=12)
print(word)

# Generate multiple words
words = generator.generate_batch(10, min_len=4, max_len=8)
print(words)
```

### Markov Chain Generator

```python
from markov_generator import MarkovWordGenerator

# Initialize (downloads word list on first run)
generator = MarkovWordGenerator(order=2, min_relative_prob=0.1)

# Generate words
word = generator.generate(min_len=6, max_len=12)
words = generator.generate_batch(10)

# Adjust parameters
generator = MarkovWordGenerator(
    order=3,                    # Look back 3 characters
    min_relative_prob=0.05,     # Include more rare transitions
    word_file="custom_words.txt"  # Use custom word list
)
```

## Example Output

### Syllable-based
```
Words (6-12 chars):
blairthook    groomfleck    spaintwist    cheedlump     frailstomp
pleetgronk    swailbrick    throomcleft   grailsplunk   fleetspark

Words (4-8 chars):
blink         grook         spail         cheed         frail
pleet         swail         throom        grail         fleet

Phrase:
blink-grook-spail
```

### Markov chains
```
Words (6-12 chars):
fromer        posinable     premondrales  bularinarabl  mationtlitho
mankethraver  lialism       unforadion    katicousiter  oversh      

Words (4-8 chars):
excolife      glodines      unding        lustaire      gilesist    
hace          tishilik      woodis        popled        thearin     

Phrase:
bers-unraptiv-anionsio

Generated from 359039 training words using order-2 Markov chains
```

## Parameters

### Markov Chain Parameters
- `order`: Number of previous characters to consider (1-4, default: 2)
- `min_relative_prob`: Filter out rare transitions (0.0-1.0, default: 0.1)
- `word_file`: Path to training word list (downloads automatically if None)

### Generation Parameters
- `min_len`: Minimum word length (default: 3)
- `max_len`: Maximum word length (default: 10)
- `count`: Number of words to generate in batch (default: 10)

## License

MIT
