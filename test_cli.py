#!/usr/bin/env python3
"""Test script for nonsense_generator.py CLI functionality."""

import subprocess
import sys
import re
def run_command(cmd):
    """Run a command and return output and return code."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT", 1


def check_word_length(word, min_len, max_len):
    """Check if word length is within range."""
    return min_len <= len(word) <= max_len


def check_token_format(token):
    """Check if token has correct format (word-word-word)."""
    parts = token.split('-')
    return len(parts) == 3 and all(part.isalpha() for part in parts)


def test_single_mode():
    """Test --single mode with various length parameters."""
    print("Testing --single mode...")
    
    tests = [
        ("python nonsense_generator.py --single", 8, 12),
        ("python nonsense_generator.py --single --length=5-8", 5, 8),
        ("python nonsense_generator.py --single --length=10", 10, 10),
        ("python nonsense_generator.py --single --length=2-4", 2, 4),
        ("python nonsense_generator.py --single --markov", 8, 12),
        ("python nonsense_generator.py --single --markov --length=6-15", 6, 15),
        ("python nonsense_generator.py --single --markov --order=3 --length=4-7", 4, 7),
    ]
    
    for cmd, min_len, max_len in tests:
        output, code = run_command(cmd)
        if code != 0:
            print(f"  FAIL: {cmd} (exit code {code})")
            continue
            
        lines = output.strip().split('\n')
        if len(lines) != 1:
            print(f"  FAIL: {cmd} (expected 1 line, got {len(lines)})")
            continue
            
        word = lines[0].strip()
        if not word.isalpha():
            print(f"  FAIL: {cmd} (non-alphabetic word: '{word}')")
            continue
            
        if not check_word_length(word, min_len, max_len):
            print(f"  FAIL: {cmd} (word '{word}' length {len(word)} not in range {min_len}-{max_len})")
            continue
            
        print(f"  PASS: {cmd} -> '{word}' (len={len(word)})")


def test_token_mode():
    """Test --token mode with various length parameters."""
    print("\nTesting --token mode...")
    
    tests = [
        ("python nonsense_generator.py --token", 4, 8),
        ("python nonsense_generator.py --token --length=3-6", 3, 6),
        ("python nonsense_generator.py --token --length=8", 8, 8),
        ("python nonsense_generator.py --token --markov", 4, 8),
        ("python nonsense_generator.py --token --markov --length=2-5", 2, 5),
        ("python nonsense_generator.py --token --markov --order=3 --length=6-10", 6, 10),
    ]
    
    for cmd, min_len, max_len in tests:
        output, code = run_command(cmd)
        if code != 0:
            print(f"  FAIL: {cmd} (exit code {code})")
            continue
            
        lines = output.strip().split('\n')
        if len(lines) != 1:
            print(f"  FAIL: {cmd} (expected 1 line, got {len(lines)})")
            continue
            
        token = lines[0].strip()
        if not check_token_format(token):
            print(f"  FAIL: {cmd} (invalid token format: '{token}')")
            continue
            
        words = token.split('-')
        all_valid = True
        for word in words:
            if not check_word_length(word, min_len, max_len):
                print(f"  FAIL: {cmd} (word '{word}' length {len(word)} not in range {min_len}-{max_len})")
                all_valid = False
                break
                
        if all_valid:
            lengths = [len(w) for w in words]
            print(f"  PASS: {cmd} -> '{token}' (lengths={lengths})")


def check_name_format(name):
    """Check if name has correct format (Firstname Lastname)."""
    parts = name.split(' ')
    if len(parts) != 2:
        return False
    first, last = parts
    return (first.isalpha() and first[0].isupper() and first[1:].islower() and
            last.isalpha() and last[0].isupper() and last[1:].islower())


def test_name_mode():
    """Test --name mode with various length parameters."""
    print("\nTesting --name mode...")
    
    tests = [
        ("python nonsense_generator.py --name", 6, 20),
        ("python nonsense_generator.py --name --length=3-6", 3, 6),
        ("python nonsense_generator.py --name --length=8", 8, 8),
        ("python nonsense_generator.py --name --order=2 --length=2-5", 2, 5),
        ("python nonsense_generator.py --name --order=3 --length=6-12", 6, 12),
        ("python nonsense_generator.py --name --cutoff=0.05 --length=4-8", 4, 8),
    ]
    
    for cmd, min_len, max_len in tests:
        output, code = run_command(cmd)
        if code != 0:
            print(f"  FAIL: {cmd} (exit code {code})")
            continue
            
        lines = output.strip().split('\n')
        if len(lines) != 1:
            print(f"  FAIL: {cmd} (expected 1 line, got {len(lines)})")
            continue
            
        name = lines[0].strip()
        if not check_name_format(name):
            print(f"  FAIL: {cmd} (invalid name format: '{name}')")
            continue
            
        first, last = name.split(' ')
        all_valid = True
        for word in [first, last]:
            if not check_word_length(word, min_len, max_len):
                print(f"  FAIL: {cmd} (word '{word}' length {len(word)} not in range {min_len}-{max_len})")
                all_valid = False
                break
                
        if all_valid:
            lengths = [len(first), len(last)]
            print(f"  PASS: {cmd} -> '{name}' (lengths={lengths})")


def test_batch_mode():
    """Test batch mode with various parameters."""
    print("\nTesting batch mode...")
    
    tests = [
        ("python nonsense_generator.py", 50, 5, 12),
        ("python nonsense_generator.py --count=10", 10, 5, 12),
        ("python nonsense_generator.py --count=5 --length=4-6", 5, 4, 6),
        ("python nonsense_generator.py --markov --count=8", 8, 5, 12),
        ("python nonsense_generator.py --markov --count=12 --length=2-5", 12, 2, 5),
        ("python nonsense_generator.py --markov --order=3 --count=6 --length=7-12", 6, 7, 12),
    ]
    
    for cmd, expected_count, min_len, max_len in tests:
        output, code = run_command(cmd)
        if code != 0:
            print(f"  FAIL: {cmd} (exit code {code})")
            continue
            
        # Parse grid output - words are separated by spaces, rows by newlines
        words = []
        for line in output.strip().split('\n'):
            if line.strip():
                # Split by whitespace and filter out empty strings
                row_words = [w.strip() for w in line.split() if w.strip()]
                words.extend(row_words)
        
        if len(words) != expected_count:
            print(f"  FAIL: {cmd} (expected {expected_count} words, got {len(words)})")
            continue
            
        all_valid = True
        invalid_words = []
        for word in words:
            if not word.isalpha():
                invalid_words.append(f"'{word}' (non-alphabetic)")
                all_valid = False
            elif not check_word_length(word, min_len, max_len):
                invalid_words.append(f"'{word}' (len={len(word)})")
                all_valid = False
                
        if not all_valid:
            print(f"  FAIL: {cmd} (invalid words: {invalid_words[:3]}{'...' if len(invalid_words) > 3 else ''})")
            continue
            
        lengths = [len(w) for w in words]
        min_actual, max_actual = min(lengths), max(lengths)
        print(f"  PASS: {cmd} -> {len(words)} words (length range: {min_actual}-{max_actual})")


def test_error_cases():
    """Test error handling for invalid parameters."""
    print("\nTesting error cases...")
    
    error_tests = [
        "python nonsense_generator.py --length=invalid",
        "python nonsense_generator.py --length=10-5",  # max < min
        "python nonsense_generator.py --length=0-5",   # min < 1
        "python nonsense_generator.py --single --length=-1",
        "python nonsense_generator.py --markov --words=invalid_language",
        "python nonsense_generator.py --order=3",  # order without --markov or --name
        "python nonsense_generator.py --cutoff=0.05",  # cutoff without --markov or --name
        "python nonsense_generator.py --words=es",  # words without --markov or --name
        "python nonsense_generator.py --order=3 --cutoff=0.05 --words=fr",  # multiple markov options without --markov or --name
        "python nonsense_generator.py --name --words=es",  # --words with --name
    ]
    
    for cmd in error_tests:
        output, code = run_command(cmd)
        if code == 0:
            print(f"  FAIL: {cmd} (should have failed but didn't)")
        else:
            print(f"  PASS: {cmd} (correctly failed with exit code {code})")


def test_markov_parameters():
    """Test Markov-specific parameters."""
    print("\nTesting Markov parameters...")
    
    tests = [
        "python nonsense_generator.py --markov --order=1 --single",
        "python nonsense_generator.py --markov --order=3 --cutoff=0.05 --single",
        "python nonsense_generator.py --markov --words=es --single",
        "python nonsense_generator.py --markov --words=names --single",
        "python nonsense_generator.py --markov --verbose --single",
    ]
    
    for cmd in tests:
        output, code = run_command(cmd)
        if code != 0:
            print(f"  FAIL: {cmd} (exit code {code})")
        else:
            lines = output.strip().split('\n')
            # Find the actual word (last non-verbose line)
            word_line = None
            for line in reversed(lines):
                if line.strip() and not line.startswith(('Initializing', 'Loading', 'Downloaded', 'Built', 'Loaded', 'Saved')):
                    word_line = line.strip()
                    break
            
            if word_line and word_line.replace('-', '').replace(' ', '').isalpha():
                print(f"  PASS: {cmd} -> '{word_line}'")
            else:
                print(f"  FAIL: {cmd} (no valid word found in output)")


def test_length_ranges():
    """Test specific length ranges to verify min-max functionality."""
    print("\nTesting length ranges...")
    
    # Test various ranges with multiple samples
    ranges = [
        (2, 3),
        (2, 8), 
        (5, 5),  # exact length
        (10, 15),
        (1, 20),
    ]
    
    for min_len, max_len in ranges:
        print(f"  Testing range {min_len}-{max_len}:")
        
        # Test with syllable generator
        cmd = f"python nonsense_generator.py --count=20 --length={min_len}-{max_len}"
        output, code = run_command(cmd)
        
        if code == 0:
            words = []
            for line in output.strip().split('\n'):
                if line.strip():
                    row_words = [w.strip() for w in line.split() if w.strip()]
                    words.extend(row_words)
            
            if words:
                lengths = [len(w) for w in words if w.isalpha()]
                if lengths:
                    actual_min, actual_max = min(lengths), max(lengths)
                    in_range = all(min_len <= l <= max_len for l in lengths)
                    print(f"    Syllable: {len(lengths)} words, range {actual_min}-{actual_max}, valid: {in_range}")
                else:
                    print(f"    Syllable: No valid words found")
            else:
                print(f"    Syllable: No words parsed from output")
        else:
            print(f"    Syllable: Failed with exit code {code}")
        
        # Test with Markov generator
        cmd = f"python nonsense_generator.py --markov --count=20 --length={min_len}-{max_len}"
        output, code = run_command(cmd)
        
        if code == 0:
            words = []
            for line in output.strip().split('\n'):
                if line.strip() and not line.startswith(('Initializing', 'Loading', 'Downloaded', 'Built', 'Loaded', 'Saved')):
                    row_words = [w.strip() for w in line.split() if w.strip()]
                    words.extend(row_words)
            
            if words:
                lengths = [len(w) for w in words if w.isalpha()]
                if lengths:
                    actual_min, actual_max = min(lengths), max(lengths)
                    in_range = all(min_len <= l <= max_len for l in lengths)
                    print(f"    Markov:   {len(lengths)} words, range {actual_min}-{actual_max}, valid: {in_range}")
                else:
                    print(f"    Markov:   No valid words found")
            else:
                print(f"    Markov:   No words parsed from output")
        else:
            print(f"    Markov:   Failed with exit code {code}")


def main():
    """Run all tests."""
    print("Testing nonsense_generator.py CLI functionality")
    print("=" * 50)
    
    test_single_mode()
    test_token_mode()
    test_name_mode()
    test_batch_mode()
    test_error_cases()
    test_markov_parameters()
    test_length_ranges()
    
    print("\n" + "=" * 50)
    print("Testing complete!")


if __name__ == "__main__":
    main()
