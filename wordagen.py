#!/usr/bin/env python3
"""Nonsense word generator using Markov chains or syllable-based generation."""

import sys
import argparse
from syllable_generator import SyllableWordGenerator
from markov_generator import MarkovWordGenerator
from word_loader import WORD_URLS, parse_length
from errors import GenerationError


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
    print("  python wordagen.py --markov --words=en")
    print("  python wordagen.py --markov --words=es")
    print("  python wordagen.py --markov --words=https://example.com/wordlist.txt")


def validate_args(args):
    """Validate command line arguments.
    
    Args:
        args: Parsed command line arguments from argparse
        
    Returns:
        tuple: (min_len, max_len) validated length parameters
    """
    # Auto-enable Markov mode if Markov-specific options are used
    args.markov = args.markov or any([
        args.order != 2, args.cutoff != 0.1, args.words != "en",
        bool(args.prefix), bool(args.suffix), args.trace
    ])
    
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
    
    # Validate word source
    if args.words.startswith(('http://', 'https://')):
        pass  # Custom URL - no validation needed
    elif args.words not in WORD_URLS and not args.name:
        print(f"Error: Unknown word list '{args.words}'. Supported types: {list(WORD_URLS.keys())} or use a URL starting with http:// or https://")
        exit(1)
    
    # Validate name mode restrictions
    if args.name and args.words != "en":
        print("Error: --name cannot be combined with --words. Name mode uses fixed 'names' and 'surnames' lists.")
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
            first_gen = MarkovWordGenerator(order=args.order, cutoff=args.cutoff, verbose=args.verbose, words="names", reverse_mode=reverse_mode, trace=args.trace, morphology=args.morphology)
            last_gen = MarkovWordGenerator(order=args.order, cutoff=args.cutoff, verbose=args.verbose, words="surnames", reverse_mode=reverse_mode, trace=args.trace, morphology=args.morphology)
            gen = (first_gen, last_gen)
        else:
            gen = MarkovWordGenerator(order=args.order, cutoff=args.cutoff, verbose=args.verbose, words=args.words, reverse_mode=reverse_mode, trace=args.trace, morphology=args.morphology)
    else:
        if args.verbose:
            print("Initializing syllable-based generator...", file=sys.stderr)
        gen = SyllableWordGenerator()
    
    gen_kwargs = {"prefix": args.prefix}
    if isinstance(gen, MarkovWordGenerator):
        gen_kwargs["suffix"] = args.suffix
    try:
        if args.single:
            print(gen.generate(min_len, max_len, **gen_kwargs))
        elif args.token:
            for _ in range(args.count):
                words = gen.generate_batch(3, min_len, max_len, **gen_kwargs)
                print("-".join(words))
        elif args.name:
            first_gen, last_gen = gen
            for _ in range(args.count):
                # Generate names with retry logic to ensure length constraints are met
                max_retries = 50
                best_first = ""
                best_last = ""
                center = (min_len + max_len) // 2
                def closer(best, cand):
                    return (not best) or abs(len(cand) - center) < abs(len(best) - center)
                
                for retry in range(max_retries):
                    first_name = first_gen.generate(min_len, max_len, prefix=args.prefix, suffix=args.suffix).capitalize()
                    last_name = last_gen.generate(min_len, max_len, prefix=args.prefix, suffix=args.suffix).capitalize()
                    
                    # Check if both names meet the length constraints
                    if (min_len <= len(first_name) <= max_len and 
                        min_len <= len(last_name) <= max_len):
                        print(f"{first_name} {last_name}")
                        break
                        
                    # Keep track of best candidates for fallback
                    if closer(best_first, first_name):
                        best_first = first_name
                    if closer(best_last, last_name):
                        best_last = last_name
                else:
                    # Fallback with best candidates that are closest to target length
                    print(f"{best_first} {best_last}")
        else:
            words = gen.generate_batch(args.count, min_len, max_len, **gen_kwargs)
            max_width = max(max(len(word) for word in words), 12)
            for i in range(0, len(words), 5):
                row = words[i:i+5]
                print("  ".join(f"{word:<{max_width}}" for word in row))
    except GenerationError as e:
        print(str(e), file=sys.stderr)
        sys.exit(1)


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
                       help="Word list type (default: en) or custom URL (auto-enables Markov mode). Cannot be used with --name")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="print detailed initialization messages")
    parser.add_argument("--single", action="store_true",
                       help="generate a single word")
    parser.add_argument("--token", action="store_true",
                       help="generate a token (triplet of words joined by dashes)")
    parser.add_argument("--name", action="store_true",
                       help="generate a first and last name (e.g., 'Sharrol Kritzen'); uses fixed 'names' and 'surnames' lists; cannot be combined with --words")
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
    parser.add_argument("--trace", action="store_true",
                       help="show character-by-character generation trace (Markov mode only)")
    parser.add_argument("--list", action="store_true",
                       help="list all available word lists and exit")
    morph_group = parser.add_mutually_exclusive_group()
    morph_group.add_argument("--morphology", dest="morphology", action="store_true", default=True,
                       help="enable Hunspell morphological expansion (default)")
    morph_group.add_argument("--no-morphology", dest="morphology", action="store_false",
                       help="disable Hunspell morphological expansion")
    
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
