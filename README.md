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

## Quick Start

```bash
# Generate 50 words (default)
python nonsense_generator.py

# Generate a single word
python nonsense_generator.py --single

# Generate using Markov chains (more realistic)
python nonsense_generator.py --markov --single

# Generate a name
python nonsense_generator.py --name
```

## Generation Modes

### Single Word (`--single`)
```bash
python nonsense_generator.py --single --markov                   # 8-12 chars (default)
ingenetershi

python nonsense_generator.py --single --markov --length=4-6      # 4-6 chars
inaman

python nonsense_generator.py --single --markov --length=15       # exactly 15 chars
aemputorronsten
```

### Token (`--token`)
Generate triplets joined by dashes (useful for passwords/identifiers):
```bash
python nonsense_generator.py --token --markov                    # word-word-word
manize-misation-unequist

python nonsense_generator.py --token --markov --length=3-6       # shorter words
unt-ovelom-brif
```

### Name (`--name`)
Generate properly capitalized first and last names (always uses Markov chains):
```bash
python nonsense_generator.py --name
Emaria Fretzeke

python nonsense_generator.py --name --order=3                    # higher quality
Phylindsay Valing
```

### Batch (default)
Generate multiple words in grid format:
```bash
python nonsense_generator.py --markov --count=20
waticidailim  scarabia      cocharivines  haderiling    nerance     
sphymberater  seming        unterm        perondis      recropormato
muncheadders  impton        phaemels      feagoutomon   prailogishit
mothee        unards        bearks        calentantrap  muncormass  

python nonsense_generator.py --markov --length=5-8 --count=15 --order=4
semier        escaria       stardina      grievine      embles
enthood       exclaime      arbita        charoman      estudien
outstudi      semipter      deconfer      impedino      euplocer
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

## Example Output

```bash
# Syllable-based fast algo
python nonsense_generator.py --single
stearnthep

# Markov chains
python nonsense_generator.py --single --markov
aguantly

# Names
python nonsense_generator.py --name --order=3
Floriam Gabating

# Batch Markov
python nonsense_generator.py --markov --count=5
exidigic      clograge      matition      bogiancy      aling

# Spanish words
python nonsense_generator.py --markov --words=es --count=20 --order=4
estupiría     sobrevieron   escartuchare  aguarniesest  desvanes
geologizaría  amoradora     enterecerás   corteñarán    vocaba
desbardábamo  trases        marcheareis   apercadentar  varetarais
embotizáremo  pasmañanearí  descaba       enrosa        deslegaré   

# Batch of names
python nonsense_generator.py --name --order=4 --count=5
Karred Giarron
Brigitteny Flemon
Bryann Boerum
Alessie Eddick
Monita Amorond
```

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
