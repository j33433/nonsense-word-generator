#!/usr/bin/env python3
"""Nonsense word generator using Markov chains or syllable-based generation."""

import argparse
from syllable_generator import SyllableWordGenerator
from markov_generator import MarkovWordGenerator, NonsenseWordGenerator


def main() -> None:
    """Demo the generator."""
    parser = argparse.ArgumentParser(description="Generate nonsense words")
    parser.add_argument("--markov", action="store_true", 
                       help="Use Markov chain generator (default: syllable-based)")
    parser.add_argument("--order", type=int, default=2,
                       help="Markov chain order (default: 2)")
    parser.add_argument("--min-prob", type=float, default=0.1,
                       help="Minimum relative probability threshold (default: 0.1)")
    
    args = parser.parse_args()
    
    if args.markov:
        print("Initializing Markov chain generator...")
        gen = MarkovWordGenerator(order=args.order, min_relative_prob=args.min_prob)
        generator_type = f"order-{gen.order} Markov chains"
        extra_info = f"Minimum relative probability threshold: {gen.min_relative_prob}"
    else:
        print("Initializing syllable-based generator...")
        gen = SyllableWordGenerator()
        generator_type = "syllable components"
        extra_info = ""
    
    print("\nWords (6-12 chars):")
    words = gen.generate_batch(20, 6, 12)
    for i in range(0, len(words), 5):
        print("  ".join(f"{w:<12}" for w in words[i:i+5]))
    
    print("\nWords (4-8 chars):")
    tokens = gen.generate_batch(20, 4, 8)
    for i in range(0, len(tokens), 5):
        print("  ".join(f"{t:<12}" for t in tokens[i:i+5]))

    print("\nPhrase:")
    key = "-".join(gen.generate_batch(3, 4, 8))
    print(key)
    
    if hasattr(gen, 'words'):
        print(f"\nGenerated from {len(gen.words)} training words using {generator_type}")
    else:
        print(f"\nGenerated using {generator_type}")
    
    if extra_info:
        print(extra_info)

if __name__ == "__main__":
    main()
