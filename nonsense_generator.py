#!/usr/bin/env python3
"""Nonsense word generator using Markov chains or syllable-based generation."""

import argparse
from syllable_generator import SyllableWordGenerator
from markov_generator import MarkovWordGenerator


def generate_words(args):
    """Generate words based on command line arguments.
    
    Args:
        args: Parsed command line arguments from argparse
    """
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
            min_len, max_len = 5, 8
        elif args.name:
            min_len, max_len = 6, 20
        else:
            # Default for batch mode
            min_len, max_len = 5, 12
    
    # Initialize generator
    if args.markov or args.name:
        if args.verbose:
            print("Initializing Markov chain generator...")
        # For --name mode, use specific word lists
        if args.name:
            # We'll need two generators: one for first names, one for surnames
            first_gen = MarkovWordGenerator(order=args.order, cutoff=args.cutoff, verbose=args.verbose, words="names")
            last_gen = MarkovWordGenerator(order=args.order, cutoff=args.cutoff, verbose=args.verbose, words="surnames")
            gen = (first_gen, last_gen)  # Store as tuple for name generation
        else:
            gen = MarkovWordGenerator(order=args.order, cutoff=args.cutoff, verbose=args.verbose, words=args.words)
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
    elif args.name:
        # Generate and print names using separate generators
        first_gen, last_gen = gen
        for _ in range(args.count):
            first_name = first_gen.generate(min_len, max_len).capitalize()
            last_name = last_gen.generate(min_len, max_len).capitalize()
            print(f"{first_name} {last_name}")
    else:
        # Generate batch of words
        words = gen.generate_batch(args.count, min_len, max_len)
        # Print in grid format, 5 words per row with dynamic alignment
        # Calculate the maximum width needed for the entire grid, with minimum of 12
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
                       choices=["en", "es", "fr", "de", "it", "pt", "names", "surnames"],
                       help="Word list type (default: en) [Markov only]")
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
    parser.add_argument("--count", type=int, default=50, metavar="N",
                       help="number of words/names to generate (default: 50 for batch, 1 for --name)")
    
    args = parser.parse_args()
    
    # Set default count for --name mode
    if args.name and args.count == 50:  # 50 is the default, so user didn't specify --count
        args.count = 1
    
    # Validate that Markov-specific options are only used with --markov or --name
    if not args.markov and not args.name:
        markov_options = []
        if args.order != 2:  # 2 is the default
            markov_options.append("--order")
        if args.cutoff != 0.1:  # 0.1 is the default
            markov_options.append("--cutoff")
        if args.words != "en":  # "en" is the default
            markov_options.append("--words")
        
        if markov_options:
            print(f"Error: {', '.join(markov_options)} can only be used with --markov or --name")
            exit(1)
    
    # Validate that --words is not used with --name (since --name uses fixed word lists)
    if args.name and args.words != "en":
        print("Error: --words cannot be used with --name (names use fixed 'names' and 'surnames' word lists)")
        exit(1)
    
    generate_words(args)

if __name__ == "__main__":
    main()
