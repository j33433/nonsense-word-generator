# Nonsense Word Generator

Generates pronounceable nonsense words that sound like English but probably aren't.

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

# Generate a single word
word = generator.generate()
print(word)

# Generate a single word with specific length
word = generator.generate(min_len=6, max_len=12)
print(word)

# Generate multiple words
words = generator.generate_batch(10)
print(words)

# Generate multiple words with specific lengths
words = generator.generate_batch(5, min_len=6, max_len=12)
print(words)
```

## Example Output

```
Words (6-12 chars):
nieoumpzi     bairpoat      froocthikcra  twaybismea    ceelaiftraip
tweeicheenk   stipekel      maisnaund     bleaoutousk   mustremp
rayptslaijai  heeeazielp    graygloo      souslaoslais  giseafdroomp
lidrieayrm    reysliest     zapaygadz     sparmgeep     crayfleand

Words (4-8 chars):
vetvourk      bleempai      praink        sefeen        shai
thetway       spelk         haycru        rouctay       roualf
hoogai        cled          baiayn        claylt        sciem
floaspox      shent         layfrus       froop         stey

Phrase:
sloold-troo-chespoa
```

## License

MIT
