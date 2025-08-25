#!/usr/bin/env python3
"""Nonsense word generator using Markov chains or syllable-based generation."""

import argparse
from syllable_generator import SyllableWordGenerator
from markov_generator import MarkovWordGenerator, NonsenseWordGenerator


def generate_words(args):
    """Generate words based on arguments."""
    # Parse the length range
    if args.length:
        try:
            if '-' in args.length:
                min_str, max_str = args.length.split('-', 1)
                min_len, max_len = int(min_str), int(max_str)
            else:
                # Single number means exact length
                min_len = max_len = int(args.length)
        except ValueError:
            print(f"Error: Invalid length format '{args.length}'. Use format like '5-8' or '6'")
            exit(1)
        
        # Validate length parameters
        if min_len < 1 or max_len < 1 or min_len > max_len:
            print(f"Error: Invalid length range {min_len}-{max_len}. Min must be >= 1 and <= max.")
            exit(1)
    else:
        # Set default length ranges based on mode
        if args.single:
            min_len, max_len = 8, 12
        elif args.token:
            min_len, max_len = 4, 8
        else:
            # Default for batch mode
            min_len, max_len = 3, 10
    
    # Initialize generator
    if args.markov:
        if args.verbose:
            print("Initializing Markov chain generator...")
        gen = MarkovWordGenerator(order=args.order, cutoff=args.cutoff, verbose=args.verbose, language=args.words)
    else:
        if args.verbose:
            print("Initializing syllable-based generator...")
        gen = SyllableWordGenerator()
    
    # Generate words
    if args.single:
        # Generate and print single word
        word = gen.generate(min_len, max_len)
        print(word)
    elif args.token:
        # Generate and print token (triplet joined by dashes)
        words = gen.generate_batch(3, min_len, max_len)
        token = "-".join(words)
        print(token)
    else:
        # Generate batch of words
        words = gen.generate_batch(args.count, min_len, max_len)
        # Print in grid format, 5 words per row
        for i in range(0, len(words), 5):
            row = words[i:i+5]
            print("  ".join(f"{word:<12}" for word in row))


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
                       choices=["en", "es", "fr", "de", "it", "pt", "names", "surnames"],
                       help="Word list type (default: en) [Markov only]")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="print detailed initialization messages")
    parser.add_argument("--single", action="store_true",
                       help="generate a single word")
    parser.add_argument("--token", action="store_true",
                       help="generate a token (triplet of words joined by dashes)")
    parser.add_argument("--batch", action="store_true",
                       help="generate batch of words (default mode)")
    parser.add_argument("--length", type=str, metavar="MIN-MAX",
                       help="word length range (e.g., '5-8' or '10' for exact length)")
    parser.add_argument("--count", type=int, default=50, metavar="N",
                       help="number of words to generate in batch mode (default: 50)")
    
    args = parser.parse_args()
    
    # Validate that Markov-specific options are only used with --markov
    if not args.markov:
        markov_options = []
        if args.order != 2:  # 2 is the default
            markov_options.append("--order")
        if args.cutoff != 0.1:  # 0.1 is the default
            markov_options.append("--cutoff")
        if args.words != "en":  # "en" is the default
            markov_options.append("--words")
        
        if markov_options:
            print(f"Error: {', '.join(markov_options)} can only be used with --markov")
            exit(1)
    
    generate_words(args)

if __name__ == "__main__":
    main()
