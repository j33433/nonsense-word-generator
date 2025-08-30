#!/usr/bin/env python3
"""Profile the nonsense word generator performance."""

import cProfile
import pstats
import io
import time
import sys
import os
from contextlib import contextmanager

# Import the generators
from syllable_generator import SyllableWordGenerator
from markov_generator import MarkovWordGenerator


@contextmanager
def timer(description):
    """Context manager to time operations."""
    start = time.time()
    yield
    end = time.time()
    print(f"{description}: {end - start:.3f} seconds")


def profile_syllable_generator():
    """Profile the syllable-based generator."""
    print("=" * 60)
    print("PROFILING SYLLABLE GENERATOR")
    print("=" * 60)
    
    # Initialize generator
    with timer("Syllable generator initialization"):
        gen = SyllableWordGenerator()
    
    # Profile single word generation
    pr = cProfile.Profile()
    pr.enable()
    
    with timer("Generate 1000 single words"):
        for _ in range(1000):
            gen.generate(min_len=5, max_len=12)
    
    pr.disable()
    
    # Profile batch generation
    with timer("Generate batch of 1000 words"):
        words = gen.generate_batch(1000, min_len=5, max_len=12)
    
    print(f"Generated {len(words)} words")
    print(f"Sample words: {words[:10]}")
    
    # Show profiling results
    print("\nTop 10 functions by cumulative time:")
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(10)
    print(s.getvalue())


def profile_markov_generator():
    """Profile the Markov chain generator."""
    print("=" * 60)
    print("PROFILING MARKOV GENERATOR")
    print("=" * 60)
    
    # Test different configurations
    configs = [
        {"order": 2, "words": "en", "desc": "Order 2, English"},
        {"order": 3, "words": "en", "desc": "Order 3, English"},
        {"order": 2, "words": "names", "desc": "Order 2, Names"},
    ]
    
    for config in configs:
        print(f"\n--- {config['desc']} ---")
        
        # Initialize generator
        with timer(f"Markov generator initialization ({config['desc']})"):
            gen = MarkovWordGenerator(
                order=config["order"], 
                words=config["words"], 
                verbose=False
            )
        
        # Profile single word generation
        pr = cProfile.Profile()
        pr.enable()
        
        with timer("Generate 100 single words"):
            for _ in range(100):
                gen.generate(min_len=5, max_len=12)
        
        pr.disable()
        
        # Profile batch generation
        with timer("Generate batch of 100 words"):
            words = gen.generate_batch(100, min_len=5, max_len=12)
        
        print(f"Generated {len(words)} words")
        print(f"Sample words: {words[:5]}")
        
        # Show top functions
        print("\nTop 5 functions by cumulative time:")
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats(5)
        print(s.getvalue())


def profile_prefix_suffix_generation():
    """Profile prefix and suffix generation."""
    print("=" * 60)
    print("PROFILING PREFIX/SUFFIX GENERATION")
    print("=" * 60)
    
    # Test prefix generation
    print("\n--- Prefix Generation ---")
    gen = MarkovWordGenerator(order=2, words="en", verbose=False)
    
    with timer("Generate 100 words with prefix 'test'"):
        words = gen.generate_batch(100, min_len=5, max_len=12, prefix="test")
    
    print(f"Generated {len(words)} words with prefix")
    print(f"Sample words: {words[:5]}")
    
    # Test suffix generation
    print("\n--- Suffix Generation ---")
    gen_reverse = MarkovWordGenerator(order=2, words="en", verbose=False, reverse_mode=True)
    
    with timer("Generate 100 words with suffix 'ing'"):
        words = gen_reverse.generate_batch(100, min_len=5, max_len=12, suffix="ing")
    
    print(f"Generated {len(words)} words with suffix")
    print(f"Sample words: {words[:5]}")


def profile_word_loading():
    """Profile word loading performance."""
    print("=" * 60)
    print("PROFILING WORD LOADING")
    print("=" * 60)
    
    from word_loader import load_words
    from cache_manager import CacheManager
    
    cache_manager = CacheManager()
    
    # Test different word sources
    sources = ["en", "names", "surnames", "pet"]
    
    for source in sources:
        print(f"\n--- Loading {source} ---")
        
        with timer(f"Load {source} words"):
            words = load_words(source, verbose=False, cache_manager=cache_manager)
        
        print(f"Loaded {len(words)} words")
        if words:
            sample_words = list(words)[:10]
            print(f"Sample words: {sample_words}")


def profile_cache_performance():
    """Profile cache save/load performance."""
    print("=" * 60)
    print("PROFILING CACHE PERFORMANCE")
    print("=" * 60)
    
    from cache_manager import CacheManager
    from collections import Counter, defaultdict
    
    cache_manager = CacheManager()
    
    # Create test data similar to Markov chains
    test_data = {
        'chains': {},
        'start_chains': Counter(),
        'order': 2,
        'word_count': 50000
    }
    
    # Generate realistic chain data
    print("Generating test chain data...")
    chains = defaultdict(Counter)
    for i in range(10000):  # Simulate 10k chain states
        key = f"test_{i % 1000}"
        for j in range(5):  # 5 transitions per state
            chains[key][f"char_{j}"] = j + 1
    
    test_data['chains'] = dict(chains)
    
    # Test save performance
    cache_file = cache_manager.get_cache_path("test_performance")
    
    with timer("Save large chain data to cache"):
        success = cache_manager.save_data(cache_file, test_data)
    
    print(f"Save successful: {success}")
    
    if success:
        # Test load performance
        with timer("Load large chain data from cache"):
            loaded_data = cache_manager.load_data(cache_file)
        
        print(f"Load successful: {loaded_data is not None}")
        
        if loaded_data:
            print(f"Loaded {len(loaded_data['chains'])} chain states")
    
    # Clean up
    if os.path.exists(cache_file):
        os.remove(cache_file)


def profile_memory_usage():
    """Profile memory usage of generators."""
    print("=" * 60)
    print("PROFILING MEMORY USAGE")
    print("=" * 60)
    
    try:
        import psutil
        process = psutil.Process()
        
        def get_memory_mb():
            return process.memory_info().rss / 1024 / 1024
        
        print(f"Initial memory: {get_memory_mb():.1f} MB")
        
        # Test syllable generator memory
        gen_syllable = SyllableWordGenerator()
        print(f"After syllable generator init: {get_memory_mb():.1f} MB")
        
        # Generate many words
        words = gen_syllable.generate_batch(10000, min_len=5, max_len=12)
        print(f"After generating 10k syllable words: {get_memory_mb():.1f} MB")
        del words, gen_syllable
        
        # Test Markov generator memory
        gen_markov = MarkovWordGenerator(order=2, words="en", verbose=False)
        print(f"After Markov generator init: {get_memory_mb():.1f} MB")
        
        # Generate many words
        words = gen_markov.generate_batch(1000, min_len=5, max_len=12)
        print(f"After generating 1k Markov words: {get_memory_mb():.1f} MB")
        del words, gen_markov
        
        print(f"Final memory: {get_memory_mb():.1f} MB")
        
    except ImportError:
        print("psutil not available - install with 'pip install psutil' for memory profiling")


def main():
    """Run all profiling tests."""
    print("NONSENSE WORD GENERATOR PERFORMANCE PROFILING")
    print("=" * 60)
    
    # Run profiling tests
    profile_syllable_generator()
    profile_markov_generator()
    profile_prefix_suffix_generation()
    profile_word_loading()
    profile_cache_performance()
    profile_memory_usage()
    
    print("\n" + "=" * 60)
    print("PROFILING COMPLETE")
    print("=" * 60)
    
    print("\nPerformance Tips:")
    print("- Syllable generator is fastest for simple word generation")
    print("- Markov chains are slower but produce more realistic words")
    print("- Higher order Markov chains are slower but more realistic")
    print("- First run is slower due to word loading and chain building")
    print("- Subsequent runs use cached data and are much faster")
    print("- Prefix/suffix generation adds overhead but is still fast")


if __name__ == "__main__":
    main()
