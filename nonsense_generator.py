#!/usr/bin/env python3
"""Nonsense word generator using Markov chains or syllable-based generation."""

import argparse
from syllable_generator import SyllableWordGenerator
from markov_generator import MarkovWordGenerator, NonsenseWordGenerator


def generate_single_word(args):
    """Generate and print a single word based on arguments."""
    # Parse the length range
    if args.single == "8-12":  # Default range when --single is used without value
        min_len, max_len = 8, 12
    else:
        try:
            if '-' in args.single:
                min_str, max_str = args.single.split('-', 1)
                min_len, max_len = int(min_str), int(max_str)
            else:
                # Single number means exact length
                min_len = max_len = int(args.single)
        except ValueError:
            print(f"Error: Invalid length format '{args.single}'. Use format like '5-8' or '6'")
            return
    
    # Initialize generator
    if args.markov:
        if args.verbose:
            print("Initializing Markov chain generator...")
        gen = MarkovWordGenerator(order=args.order, cutoff=args.cutoff, verbose=args.verbose, language=args.language)
    else:
        if args.verbose:
            print("Initializing syllable-based generator...")
        gen = SyllableWordGenerator()
    
    # Generate and print single word
    word = gen.generate(min_len, max_len)
    print(word)


def generate_batch_demo(args):
    """Generate and display batches of words in demo format."""
    if args.markov:
        if args.verbose:
            print("Initializing Markov chain generator...")
        gen = MarkovWordGenerator(order=args.order, cutoff=args.cutoff, verbose=args.verbose, language=args.language)
        generator_type = f"order-{gen.order} Markov chains ({args.language})"
        extra_info = f"Minimum relative probability cutoff: {gen.cutoff}"
    else:
        if args.verbose:
            print("Initializing syllable-based generator...")
        gen = SyllableWordGenerator()
        generator_type = "syllable components"
        extra_info = ""
    
    print("Words (6-12 chars):")
    words = gen.generate_batch(args.count, 6, 12)
    for i in range(0, len(words), 5):
        print("  ".join(f"{w:<12}" for w in words[i:i+5]))
    
    print("\nWords (4-8 chars):")
    tokens = gen.generate_batch(args.count, 4, 8)
    for i in range(0, len(tokens), 5):
        print("  ".join(f"{t:<12}" for t in tokens[i:i+5]))

    print("\nPhrase:")
    key = "-".join(gen.generate_batch(3, 4, 8))
    print(key)
    
    if args.verbose:
        if hasattr(gen, 'words'):
            print(f"\nGenerated from {len(gen.words)} training words using {generator_type}")
        else:
            print(f"\nGenerated using {generator_type}")
    
        if extra_info:
            print(extra_info)


def main():
    """Demo the generator."""
    parser = argparse.ArgumentParser(description="Generate nonsense words")
    parser.add_argument("--markov", action="store_true", 
                       help="use Markov chain generator (default: syllable-based)")
    parser.add_argument("--order", type=int, default=2,
                       help="Markov chain order (default: 2)")
    parser.add_argument("--cutoff", type=float, default=0.1,
                       help="Markov minimum relative probability cutoff (default: 0.1)")
    parser.add_argument("--language", type=str, default="en", 
                       choices=["en", "es", "fr", "de", "it", "pt"],
                       help="Language for word list (default: en) [Markov only]")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="print detailed initialization messages")
    parser.add_argument("--single", type=str, nargs='?', const="8-12", metavar="MIN-MAX",
                       help="generate a single word with length range (e.g., '5-8', default: '8-12')")
    parser.add_argument("--count", type=int, default=20, metavar="N",
                       help="number of words to generate in batch mode (default: 20)")
    
    args = parser.parse_args()
    
    # Handle single word generation
    if args.single is not None:
        generate_single_word(args)
    else:
        generate_batch_demo(args)

if __name__ == "__main__":
    main()
