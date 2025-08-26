# Nonsense Word Generator

Generate unique names for characters, online aliases, places, products, pets, brand names, hostnames, database identifiers, or any creative project that needs realistic-sounding but original words.

Two generation methods available:
- **Syllable-based**: Fast generation using phonetic rules (default)
- **Markov chains**: More realistic words trained on dictionary data

## Installation

```bash
git clone https://github.com/j33433/nonsense-word-generator.git
cd nonsense-word-generator
python nonsense_generator.py
```

## Example Output

```bash
# Batch of unique names trained on US name and surname lists
python nonsense_generator.py --name --order=4 --count=5
Karred Giarron
Brigitteny Flemon
Bryann Boerum
Alessie Eddick
Monita Amorond

# Pet names
python nonsense_generator.py --markov --order=3 --count=20 --words=pet
goosey        grizzy        tiggie        tucky         nikey
earley        skers         nestles       kisma         fritty
weave         traven        thorter       jasmindie     spooh
camie         harles        skinne        mercupcake    sierrissy

# Spanish nonsense words
python nonsense_generator.py --markov --words=es --count=20 --order=4
estupiría     sobrevieron   escartuchare  aguarniesest  desvanes
geologizaría  amoradora     enterecerás   corteñarán    vocaba
desbardábamo  trases        marcheareis   apercadentar  varetarais
embotizáremo  pasmañanearí  descaba       enrosa        deslegaré

# Syllable-based simple algorithm
python nonsense_generator.py --single
stearnthep

# Markov chains trained on English words
python nonsense_generator.py --single --markov
aguantly

# Tokens word-word-word
python nonsense_generator.py --token --markov
manize-misation-unequist
```

## Parameters

### Length Control (`--length`)
- `--length=MIN-MAX`: Range (e.g., `5-8`)
- `--length=N`: Exact length (e.g., `10`)

### Markov Chain Options (`--markov`)

**Order (`--order`, default: 2)**
- `1`: Most creative, often unpronounceable
- `2..3`: Good balance
- `4..6`: More realistic

**Word Lists (`--words`, default: "en")**
- Languages: `en`, `es`, `fr`, `de`, `it`, `pt`
- Specialized: `names`, `surnames`

**Cutoff (`--cutoff`, default: 0.1)**
- `0.0`: Include all transitions (most random)
- `0.1`: Filter rare patterns (balanced)
- `0.5`: Conservative, predictable output

## Python API

### Syllable Generator
```python
from syllable_generator import SyllableWordGenerator

generator = SyllableWordGenerator()
word = generator.generate(min_len=6, max_len=12)
words = generator.generate_batch(10, min_len=4, max_len=8)
```

### Markov Generator
```python
from markov_generator import MarkovWordGenerator

generator = MarkovWordGenerator(order=2, cutoff=0.1, words="en")
word = generator.generate(min_len=6, max_len=12)
words = generator.generate_batch(10)
```

## Performance Notes
- First run downloads word lists and builds chains (slower)
- Subsequent runs use cached files (much faster)
- Use `--verbose` to see initialization progress

## License

MIT
