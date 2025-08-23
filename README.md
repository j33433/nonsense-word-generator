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

# Generate a single word with default length (8-12 characters)
python nonsense_generator.py --single

# Generate a single word with specific length range
python nonsense_generator.py --single=5-8

# Generate a single word with exact length
python nonsense_generator.py --single=10

# Combine single word generation with Markov chains
python nonsense_generator.py --single=6-15 --markov --order 3

# Control batch size (default: 20 words per category)
python nonsense_generator.py --count=10
python nonsense_generator.py --count=5 --markov

# Adjust Markov chain parameters
python nonsense_generator.py --markov --order 3 --cutoff 0.05

# Generate words based on other languages
python nonsense_generator.py --markov --language es  # Spanish
python nonsense_generator.py --markov --language fr  # French
python nonsense_generator.py --markov --language de  # German

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

### Syllable-based
```
Words (6-12 chars):
shiledoolp    bresofreelp   staychenk     tweetwayg     dravoaft    
chaieheamp    jailfnoord    teesciflie    lurieeyoast   lepras      
flouglart     spousk        treybliielf   zeysmept      breendheart 
sheacttrilf   heyshuscoux   neehaiayeyrn  vaiuzeeb      tousnont    

Words (4-8 chars):
flayskee      feclex        reejoult      gleapcom      smeepot     
juskund       jourk         mook          healk         vibreyd     
scang         sealdtre      blong         braip         dulost      
lealf         boopoct       cliespe       chaye         geypugle    

Phrase:
waft-croufrie-crerdack
```

### Markov chains (Order 4)
```
Words (6-12 chars):
mantitricial  signomy       unlustrepine  tabernal      demonotum   
megalise      isosteres     unseerhood    laureleasure  unconfect   
gyrodically   refrankness   aspatter      insonaniming  untuneducerl
buchable      unally        orthodontall  reimburity    unmouthoric 

Words (4-8 chars):
ascency       pandolin      menormal      tankroll      sepalook    
nondefin      splendra      phaenous      lening        carpitch    
glissal       langorat      lynchio       overtedn      serpetum    
coenus        subdelet      sprucell      unmercal      evaporan    

Phrase:
vialism-unstally-nonversa
```

## Parameters

### Single Word Generation (`--single`)
Generate a single word instead of the default batch demo output.

- `--single`: Use default length range of 8-12 characters
- `--single=MIN-MAX`: Specify length range (e.g., `--single=5-8`)  
- `--single=N`: Generate word with exact length N (e.g., `--single=10`)

Examples:
```bash
python nonsense_generator.py --single                   # 8-12 chars
python nonsense_generator.py --single=4-6               # 4-6 chars
python nonsense_generator.py --single=15                # exactly 15 chars
python nonsense_generator.py --single=10-20 --markov    # 10-20 chars, Markov
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

#### Language (`--language`, default: "en")
Specifies which language's word list to download and use for training:

- **en, es, fr, de, it, pt**

Each language creates separate cache files for fast loading after first run.

#### Word File (`word_file` parameter)
- Path to custom training word list (overrides language parameter)
- Downloads automatically based on language if None
- Can specify custom word lists for different languages or domains
- Cached as pickle files for fast loading after first run

### Generation Parameters
- `min_len`: Minimum word length (default: 3)
- `max_len`: Maximum word length (default: 10)
- `count`: Number of words to generate in batch mode (`--count=N`, default: 20)
- `verbose`: Show detailed initialization messages (`--verbose` or `-v`)
- `single`: Generate single word with specified length range instead of batch demo

**Note**: `--order`, `--cutoff`, and `--language` parameters only apply when using `--markov`.

### Batch Mode (`--count`)
Controls how many words are generated in each category when running the default demo:

```bash
python nonsense_generator.py --count=10    # Generate 10 words per category
python nonsense_generator.py --count=5     # Generate 5 words per category  
python nonsense_generator.py --count=30    # Generate 30 words per category
```

The demo shows two categories: "Words (6-12 chars)" and "Words (4-8 chars)", plus a 3-word phrase.

### Performance Notes
- First run downloads word list and builds chains (slower)
- Subsequent runs use cached pickle files (much faster)
- Higher orders create larger cache files but similar generation speed

## License

MIT
