# Nonsense Word Generator

Generates pronounceable nonsense words that sound like real words but probably aren't.

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
# Generate batch of words using syllable-based method (default: 50 words)
python nonsense_generator.py

# Generate batch using Markov chains (more realistic)
python nonsense_generator.py --markov

# Generate a single word with default length (8-12 characters)
python nonsense_generator.py --single

# Generate a single word with specific length range
python nonsense_generator.py --single --length=5-8

# Generate a single word with exact length
python nonsense_generator.py --single --length=10

# Combine single word generation with Markov chains
python nonsense_generator.py --single --length=6-15 --markov --order 3

# Generate a token (triplet joined by dashes)
python nonsense_generator.py --token

# Generate token with specific length
python nonsense_generator.py --token --length=4-6 --markov

# Control batch size (default: 50 words)
python nonsense_generator.py --count=100
python nonsense_generator.py --count=25 --markov

# Adjust Markov chain parameters
python nonsense_generator.py --markov --order 3 --cutoff 0.05

# Generate words based on other languages or domains
python nonsense_generator.py --markov --words es          # Spanish
python nonsense_generator.py --markov --words fr          # French
python nonsense_generator.py --markov --words de          # German
python nonsense_generator.py --markov --words names       # US first names
python nonsense_generator.py --markov --words surnames    # US last names

# Verbose output shows initialization details
python nonsense_generator.py --verbose --markov
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
generator = MarkovWordGenerator(order=2, cutoff=0.1, language="en")

# Generate words
word = generator.generate(min_len=6, max_len=12)
words = generator.generate_batch(10)

# Adjust parameters
generator = MarkovWordGenerator(
    order=3,                      # Look back 3 characters
    cutoff=0.05,                  # Include more rare transitions
    language="es",                # Use Spanish word list
    word_file="custom_words.txt"  # Use custom word list (overrides language)
)
```

## Example Output

### Syllable-based (batch mode)
```bash
python nonsense_generator.py --count=10
```
```
shiledoolp
bresofreelp
staychenk
tweetwayg
dravoaft
chaieheamp
jailfnoord
teesciflie
lurieeyoast
lepras
```

### Markov chains (batch mode)
```bash
python nonsense_generator.py --markov --count=10
```
```
mantitricial
signomy
unlustrepine
tabernal
demonotum
megalise
isosteres
unseerhood
laureleasure
unconfect
```

### Single word generation
```bash
# Syllable-based single word
python nonsense_generator.py --single
blairthook

# Markov chain single word
python nonsense_generator.py --single --markov
refrankness

# Names
python nonsense_generator.py --markov --words names --single=4-8
lendrida

# Surnames  
python nonsense_generator.py --markov --words surnames --single=5-10
mcgard
```


## Parameters

### Generation Modes

#### Single Word Generation (`--single`)
Generate a single word instead of batch output.

```bash
python nonsense_generator.py --single                   # 8-12 chars (default)
python nonsense_generator.py --single --length=4-6      # 4-6 chars
python nonsense_generator.py --single --length=15       # exactly 15 chars
python nonsense_generator.py --single --length=10-20 --markov  # 10-20 chars, Markov
```

#### Token Generation (`--token`)
Generate a triplet of words joined by dashes (useful for passwords, identifiers, etc.).

```bash
python nonsense_generator.py --token                    # 4-8 chars per word (default)
python nonsense_generator.py --token --length=3-6       # 3-6 chars per word
python nonsense_generator.py --token --markov           # Using Markov chains
```

#### Batch Generation (default)
Generate multiple words in a grid format.

```bash
python nonsense_generator.py                           # 50 words, 3-10 chars (default)
python nonsense_generator.py --count=20                # 20 words
python nonsense_generator.py --length=5-8 --count=30   # 30 words, 5-8 chars each
```

### Length Control (`--length`)
The `--length` parameter applies to all generation modes:

- `--length=MIN-MAX`: Specify length range (e.g., `--length=5-8`)
- `--length=N`: Generate words with exact length N (e.g., `--length=10`)

Examples:
```bash
python nonsense_generator.py --single --length=6-12
python nonsense_generator.py --token --length=4-6
python nonsense_generator.py --count=25 --length=3-5
```

### Markov Chain Parameters

#### Order (`--order`, default: 2)
Controls how many previous characters the generator looks at when choosing the next character. This dramatically affects the style of generated words:

- **Order 1**: Looks at only 1 previous character
  - Most random and creative output
  - Often produces unpronounceable combinations like "qxzaeiou"
  - Good for abstract/alien-sounding words
  - Example: `usurizauttae`, `plllinathest`

- **Order 2** (recommended): Looks at 2 previous characters  
  - Good balance of creativity and pronounceability
  - Follows basic English letter patterns
  - Most versatile for general use
  - Example: `badysishelli`, `rericality`

- **Order 3**: Looks at 3 previous characters
  - More realistic and English-like output
  - Better follows common trigrams and syllable patterns
  - Less variety, more conservative word choices
  - Example: `unreculene`, `lancephaging`

- **Order 4+**: Looks at 4+ previous characters
  - Very conservative, almost copying real word fragments
  - May produce words too similar to dictionary words
  - Least creative but most "realistic"

#### Cutoff (`--cutoff`, default: 0.1)
Filters out rare character transitions to focus on more common patterns:

- **0.0**: Include all possible transitions (most random)
- **0.1** (default): Only include transitions that are at least 10% as likely as the most common choice
- **0.5**: Only include transitions that are at least 50% as likely (more conservative)

Lower values create more variety but potentially less pronounceable words. Higher values create more predictable, English-like patterns.

#### Word List Type (`--words`, default: "en")
Specifies which word list to download and use for training:

**Languages:**
- **en**: English dictionary words
- **es**: Spanish words  
- **fr**: French words
- **de**: German words
- **it**: Italian words
- **pt**: Portuguese words

**Specialized Domains:**
- **names**: US first names (generates name-like nonsense)
- **surnames**: US last names/surnames (generates surname-like nonsense)

Each language/domain creates separate cache files for fast loading after first run.

#### Word File (`word_file` parameter)
- Path to custom training word list (overrides language parameter)
- Downloads automatically based on language if None
- Can specify custom word lists for different languages or domains
- Cached as pickle files for fast loading after first run

### Generation Parameters
- `min_len`: Minimum word length (default: 3)
- `max_len`: Maximum word length (default: 10)
- `count`: Number of words to generate in batch mode (`--count=N`, default: 50)
- `verbose`: Show detailed initialization messages (`--verbose` or `-v`)
- `single`: Generate single word with specified length range instead of batch demo

**Note**: `--order`, `--cutoff`, and `--words` parameters only apply when using `--markov`.

### Validation and Error Handling
The CLI includes comprehensive validation:

- Length parameters must be positive integers with min ≤ max
- Markov-specific options (`--order`, `--cutoff`, `--words`) require `--markov`
- Invalid parameters exit with proper error codes

```bash
# These will fail with helpful error messages:
python nonsense_generator.py --order=3          # Error: --order requires --markov
python nonsense_generator.py --length=10-5      # Error: Invalid range
python nonsense_generator.py --length=invalid   # Error: Invalid format
```

### Performance Notes
- First run downloads word list and builds chains (slower)
- Subsequent runs use cached pickle files (much faster)
- Higher orders create larger cache files but similar generation speed

## License

MIT
