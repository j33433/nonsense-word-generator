#!/usr/bin/env python3
"""Nonsense word generator using Markov chains or syllable-based generation."""

import sys
import argparse
from syllable_generator import SyllableWordGenerator
from markov_generator import MarkovWordGenerator
from word_loader import WORD_URLS, parse_length
from hunspell import HUNSPELL_DICT_URLS


def list_word_sources():
    """List all available word sources."""
    # Separate language dictionaries from special lists
    language_lists = {}
    special_lists = {}
    
    for name, url in WORD_URLS.items():
        if url.startswith("hunspell:"):
            language_lists[name] = url
        else:
            special_lists[name] = url
    
    print("Language dictionaries (Hunspell - high quality, morphologically aware):")
    for name in sorted(language_lists.keys()):
        print(f"  {name}")
    
    print()
    print("Special word lists:")
    for name in sorted(special_lists.keys()):
        print(f"  {name}")
    
    print()
    print("You can also use custom URLs starting with http:// or https://")
    print()
    print("Examples:")
    print("  python nonsense_generator.py --markov --words=en")
    print("  python nonsense_generator.py --markov --words=es")
    print("  python nonsense_generator.py --markov --words=https://example.com/wordlist.txt")


def validate_args(args):
    """Validate command line arguments.
    
    Args:
        args: Parsed command line arguments from argparse
        
    Returns:
        tuple: (min_len, max_len) validated length parameters
    """
    # Auto-enable Markov mode if Markov-specific options are used
    if (args.order != 2 or args.cutoff != 0.1 or args.words != "en" or 
        args.prefix or args.suffix):
        args.markov = True
    
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
            print("Initializing Markov chain generator...", file=sys.stderr)
        
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
            print("Initializing syllable-based generator...", file=sys.stderr)
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
            # Generate names with retry logic to ensure length constraints are met
            max_retries = 50
            best_first = ""
            best_last = ""
            
            for retry in range(max_retries):
                first_name = first_gen.generate(min_len, max_len, prefix=args.prefix, suffix=args.suffix).capitalize()
                last_name = last_gen.generate(min_len, max_len).capitalize()
                
                # Check if both names meet the length constraints
                if (min_len <= len(first_name) <= max_len and 
                    min_len <= len(last_name) <= max_len):
                    print(f"{first_name} {last_name}")
                    break
                    
                # Keep track of best candidates for fallback
                if not best_first or abs(len(first_name) - (min_len + max_len) // 2) < abs(len(best_first) - (min_len + max_len) // 2):
                    best_first = first_name
                if not best_last or abs(len(last_name) - (min_len + max_len) // 2) < abs(len(best_last) - (min_len + max_len) // 2):
                    best_last = last_name
            else:
                # Fallback with best candidates that are closest to target length
                print(f"{best_first} {best_last}")
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
                       help="use Markov chain generator (default: syllable-based, auto-enabled by Markov options)")
    parser.add_argument("--order", type=int, default=2,
                       help="Markov chain order (default: 2, auto-enables Markov mode)")
    parser.add_argument("--cutoff", type=float, default=0.1,
                       help="Markov minimum relative probability cutoff (default: 0.1, auto-enables Markov mode)")
    parser.add_argument("--words", type=str, default="en", 
                       help="Word list type (default: en) or custom URL (auto-enables Markov mode)")
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
                       help="start generated words with this prefix (auto-enables Markov mode)")
    parser.add_argument("--suffix", type=str, metavar="SUFFIX",
                       help="end generated words with this suffix (auto-enables Markov mode)")
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
