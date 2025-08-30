#!/usr/bin/env python3
"""Nonsense word generator using Markov chains or syllable-based generation."""

import argparse
from syllable_generator import SyllableWordGenerator
from markov_generator import MarkovWordGenerator
from word_loader import WORD_URLS, parse_length
from hunspell import HUNSPELL_DICT_URLS


def list_word_sources():
    """List all available word sources."""
    print("Basic word lists:")
    basic_lists = {k: v for k, v in WORD_URLS.items() if not k.startswith("hunspell-")}
    for name in sorted(basic_lists.keys()):
        print(f"  {name}")
    
    print()
    print("Hunspell dictionaries (higher quality, morphologically aware):")
    hunspell_lists = {k: v for k, v in WORD_URLS.items() if k.startswith("hunspell-")}
    for name in sorted(hunspell_lists.keys()):
        lang_code = name.replace("hunspell-", "")
        print(f"  {name} ({lang_code})")
    
    print()
    print("You can also use custom URLs starting with http:// or https://")
    print()
    print("Examples:")
    print("  python nonsense_generator.py --markov --words=en")
    print("  python nonsense_generator.py --markov --words=hunspell-es")
    print("  python nonsense_generator.py --markov --words=https://example.com/wordlist.txt")


def validate_args(args):
    """Validate command line arguments.
    
    Args:
        args: Parsed command line arguments from argparse
        
    Returns:
        tuple: (min_len, max_len) validated length parameters
    """
    # Parse and validate length
    if args.length:
        try:
            min_len, max_len = parse_length(args.length)
        except ValueError:
            print(f"Error: Invalid length format '{args.length}'. Use format like '5-8' or '6'")
            exit(1)
        
        if min_len < 1 or max_len < 1 or min_len > max_len:
            print(f"Error: Invalid length range {min_len}-{max_len}. Min must be >= 1 and <= max.")
            exit(1)
    else:
        # Default lengths based on mode
        if args.single:
            min_len, max_len = 8, 12
        elif args.token:
            min_len, max_len = 5, 8
        elif args.name:
            min_len, max_len = 6, 20
        else:
            min_len, max_len = 5, 12
    
    # Validate Markov-only options
    if not args.markov and not args.name:
        markov_options = []
        if args.order != 2:
            markov_options.append("--order")
        if args.cutoff != 0.1:
            markov_options.append("--cutoff")
        if args.words != "en":
            markov_options.append("--words")
        if args.prefix:
            markov_options.append("--prefix")
        if args.suffix:
            markov_options.append("--suffix")
        
        if markov_options:
            print(f"Error: {', '.join(markov_options)} can only be used with --markov or --name")
            exit(1)
    
    # Validate prefix/suffix mutual exclusivity
    if args.prefix and args.suffix:
        print("Error: --prefix and --suffix cannot be used together")
        exit(1)
    
    # Validate word source
    if args.words.startswith(('http://', 'https://')):
        pass  # Custom URL - no validation needed
    elif args.words not in WORD_URLS and not args.name:
        print(f"Error: Unknown word list '{args.words}'. Supported types: {list(WORD_URLS.keys())} or use a URL starting with http:// or https://")
        exit(1)
    
    # Validate name mode restrictions
    if args.name and args.words != "en":
        print("Error: --words cannot be used with --name (names use fixed 'names' and 'surnames' word lists)")
        exit(1)
    
    return min_len, max_len


def generate_words(args):
    """Generate words based on command line arguments.
    
    Args:
        args: Parsed command line arguments from argparse
    """
    min_len, max_len = validate_args(args)
    
    if args.markov or args.name:
        if args.verbose:
            print("Initializing Markov chain generator...")
        
        # Determine if we need reverse mode for suffix generation
        reverse_mode = bool(args.suffix)
        
        if args.name:
            first_gen = MarkovWordGenerator(order=args.order, cutoff=args.cutoff, verbose=args.verbose, words="names", reverse_mode=reverse_mode)
            last_gen = MarkovWordGenerator(order=args.order, cutoff=args.cutoff, verbose=args.verbose, words="surnames", reverse_mode=reverse_mode)
            gen = (first_gen, last_gen)
        else:
            gen = MarkovWordGenerator(order=args.order, cutoff=args.cutoff, verbose=args.verbose, words=args.words, reverse_mode=reverse_mode)
    else:
        if args.verbose:
            print("Initializing syllable-based generator...")
        gen = SyllableWordGenerator()
    
    if args.single:
        if isinstance(gen, MarkovWordGenerator):
            word = gen.generate(min_len, max_len, prefix=args.prefix, suffix=args.suffix)
        else:
            word = gen.generate(min_len, max_len, prefix=args.prefix)
        print(word)
    elif args.token:
        for _ in range(args.count):
            if isinstance(gen, MarkovWordGenerator):
                words = gen.generate_batch(3, min_len, max_len, prefix=args.prefix, suffix=args.suffix)
            else:
                words = gen.generate_batch(3, min_len, max_len, prefix=args.prefix)
            token = "-".join(words)
            print(token)
    elif args.name:
        first_gen, last_gen = gen
        for _ in range(args.count):
            first_name = first_gen.generate(min_len, max_len, prefix=args.prefix, suffix=args.suffix).capitalize()
            last_name = last_gen.generate(min_len, max_len).capitalize()
            print(f"{first_name} {last_name}")
    else:
        if isinstance(gen, MarkovWordGenerator):
            words = gen.generate_batch(args.count, min_len, max_len, prefix=args.prefix, suffix=args.suffix)
        else:
            words = gen.generate_batch(args.count, min_len, max_len, prefix=args.prefix)
        max_width = max(max(len(word) for word in words), 12)
        for i in range(0, len(words), 5):
            row = words[i:i+5]
            print("  ".join(f"{word:<{max_width}}" for word in row))


def main():
    """Demo the generator."""
    parser = argparse.ArgumentParser(description="Generate nonsense words")
    parser.add_argument("--markov", action="store_true", 
                       help="use Markov chain generator (default: syllable-based)")
    parser.add_argument("--order", type=int, default=2,
                       help="Markov chain order (default: 2)")
    parser.add_argument("--cutoff", type=float, default=0.1,
                       help="Markov minimum relative probability cutoff (default: 0.1)")
    parser.add_argument("--words", type=str, default="en", 
                       help="Word list type (default: en) or custom URL [Markov only]")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="print detailed initialization messages")
    parser.add_argument("--single", action="store_true",
                       help="generate a single word")
    parser.add_argument("--token", action="store_true",
                       help="generate a token (triplet of words joined by dashes)")
    parser.add_argument("--name", action="store_true",
                       help="generate a first and last name (e.g., 'Sharrol Kritzen')")
    parser.add_argument("--batch", action="store_true",
                       help="generate batch of words (default mode)")
    parser.add_argument("--length", type=str, metavar="MIN-MAX",
                       help="word length range (e.g., '5-8' or '10' for exact length)")
    parser.add_argument("--count", type=int, default=None, metavar="N",
                       help="number of words/names to generate (default: 50 for batch, 1 for --name)")
    parser.add_argument("--prefix", type=str, metavar="PREFIX",
                       help="start generated words with this prefix [Markov only]")
    parser.add_argument("--suffix", type=str, metavar="SUFFIX",
                       help="end generated words with this suffix [Markov only]")
    parser.add_argument("--list", action="store_true",
                       help="list all available word lists and exit")
    
    args = parser.parse_args()
    
    if args.list:
        list_word_sources()
        return
    
    if args.count is None:
        if args.name or args.token:
            args.count = 1
        else:
            args.count = 50
    
    
    generate_words(args)

if __name__ == "__main__":
    main()
