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

Generated from 359039 training words using order-4 Markov chains
```

## Parameters

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

#### Minimum Relative Probability (`--min-prob`, default: 0.1)
Filters out rare character transitions to focus on more common patterns:

- **0.0**: Include all possible transitions (most random)
- **0.1** (default): Only include transitions that are at least 10% as likely as the most common choice
- **0.5**: Only include transitions that are at least 50% as likely (more conservative)
- **1.0**: Only use the single most likely transition (very predictable)

Lower values create more variety but potentially less pronounceable words. Higher values create more predictable, English-like patterns.

#### Word File (`word_file` parameter)
- Path to training word list (downloads automatically if None)
- Uses ~359K English words by default
- Can specify custom word lists for different languages or domains
- Cached as pickle files for fast loading after first run

### Generation Parameters
- `min_len`: Minimum word length (default: 3)
- `max_len`: Maximum word length (default: 10)
- `count`: Number of words to generate in batch (default: 10)
- `verbose`: Show detailed initialization messages (`--verbose` or `-v`)

### Performance Notes
- First run downloads word list and builds chains (slower)
- Subsequent runs use cached pickle files (much faster)
- Higher orders create larger cache files but similar generation speed
- Order 1: ~27 states, Order 2: ~681 states, Order 3: ~9,738 states

## License

MIT
