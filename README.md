# Nonsense Word Generator

Generates pronounceable nonsense words that sound like English but aren't.

## Installation

```bash
git clone https://github.com/j33433/nonsense-word-generator.git
cd nonsense-word-generator
python nonsense_generator.py
```

## Usage

```python
from nonsense_generator import NonsenseWordGenerator

generator = NonsenseWordGenerator()

# Generate 10 words
words = generator.generate_words(10)
print(words)

# Generate words with specific lengths
words = generator.generate_words(5, min_length=6, max_length=12)

# Print in grid format
generator.print_words_in_grid(words)
```

## Example Output

```
declails        excros          atoriers        strogamedings   purivesdayer   
actulistyr      deliecolled     genduckling     wellin          fathructs      
frieverget      sanize          terisk          valvergereing   lowassess      
```

## License

MIT
