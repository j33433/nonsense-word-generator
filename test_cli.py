#!/usr/bin/env python3
"""Test script for nonsense_generator.py CLI functionality."""

import subprocess
import sys
import re
import os
import shutil


def cleanup_cache():
    """Remove cache directory and all its contents."""
    if os.path.exists("cache"):
        shutil.rmtree("cache")
        print("Cleaned up cache directory")


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
        ("python nonsense_generator.py --token", 5, 8),
        ("python nonsense_generator.py --token --length=3-6", 3, 6),
        ("python nonsense_generator.py --token --length=8", 8, 8),
        ("python nonsense_generator.py --token --markov", 5, 8),
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
        ("python nonsense_generator.py --name", 6, 20, 1),
        ("python nonsense_generator.py --name --length=3-6", 3, 6, 1),
        ("python nonsense_generator.py --name --length=8", 8, 8, 1),
        ("python nonsense_generator.py --name --order=2 --length=2-5", 2, 5, 1),
        ("python nonsense_generator.py --name --order=3 --length=6-12", 6, 12, 1),
        ("python nonsense_generator.py --name --cutoff=0.05 --length=4-8", 4, 8, 1),
        ("python nonsense_generator.py --name --count=3", 6, 20, 3),
        ("python nonsense_generator.py --name --count=5 --length=4-7", 4, 7, 5),
    ]
    
    for cmd, min_len, max_len, expected_count in tests:
        output, code = run_command(cmd)
        if code != 0:
            print(f"  FAIL: {cmd} (exit code {code})")
            continue
            
        lines = output.strip().split('\n')
        if len(lines) != expected_count:
            print(f"  FAIL: {cmd} (expected {expected_count} lines, got {len(lines)})")
            continue
            
        all_valid = True
        for i, line in enumerate(lines):
            name = line.strip()
            if not check_name_format(name):
                print(f"  FAIL: {cmd} (invalid name format on line {i+1}: '{name}')")
                all_valid = False
                break
                
            first, last = name.split(' ')
            for word in [first, last]:
                if not check_word_length(word, min_len, max_len):
                    print(f"  FAIL: {cmd} (word '{word}' length {len(word)} not in range {min_len}-{max_len})")
                    all_valid = False
                    break
            if not all_valid:
                break
                
        if all_valid:
            if expected_count == 1:
                first, last = lines[0].split(' ')
                lengths = [len(first), len(last)]
                print(f"  PASS: {cmd} -> '{lines[0]}' (lengths={lengths})")
            else:
                print(f"  PASS: {cmd} -> {expected_count} names generated")


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
        "python nonsense_generator.py --suffix=ing",  # suffix without --markov or --name
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
        "python nonsense_generator.py --markov --words=https://raw.githubusercontent.com/jneidel/animal-names/refs/heads/master/animals-common.txt --single",
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


def test_prefix_functionality():
    """Test prefix functionality with Markov chains."""
    print("\nTesting prefix functionality...")
    
    tests = [
        ("python nonsense_generator.py --markov --prefix=steve --single", "steve"),
        ("python nonsense_generator.py --markov --prefix=joe --single", "joe"),
        ("python nonsense_generator.py --markov --prefix=test --single", "test"),
        ("python nonsense_generator.py --markov --words=names --prefix=james --single", "james"),
        ("python nonsense_generator.py --markov --prefix=cat --count=5", "cat"),
        ("python nonsense_generator.py --markov --prefix=dog --token", "dog"),
        ("python nonsense_generator.py --name --prefix=alex", "alex"),
    ]
    
    for cmd, expected_prefix in tests:
        output, code = run_command(cmd)
        if code != 0:
            print(f"  FAIL: {cmd} (exit code {code})")
            continue
            
        lines = output.strip().split('\n')
        # Find the actual output (last non-verbose line)
        result_lines = []
        for line in lines:
            if line.strip() and not line.startswith(('Initializing', 'Loading', 'Downloaded', 'Built', 'Loaded', 'Saved')):
                result_lines.append(line.strip())
        
        if not result_lines:
            print(f"  FAIL: {cmd} (no output found)")
            continue
            
        all_valid = True
        for line in result_lines:
            if "--token" in cmd:
                # For token mode, check each word in the token
                words = line.split('-')
                for word in words:
                    if not word.lower().startswith(expected_prefix.lower()):
                        print(f"  FAIL: {cmd} (word '{word}' doesn't start with '{expected_prefix}')")
                        all_valid = False
                        break
            elif "--name" in cmd:
                # For name mode, check first name only
                parts = line.split(' ')
                if len(parts) >= 1:
                    first_name = parts[0].lower()
                    if not first_name.startswith(expected_prefix.lower()):
                        print(f"  FAIL: {cmd} (first name '{parts[0]}' doesn't start with '{expected_prefix}')")
                        all_valid = False
                else:
                    print(f"  FAIL: {cmd} (invalid name format: '{line}')")
                    all_valid = False
            elif "--count=" in cmd:
                # For batch mode, check each word
                words = []
                for batch_line in result_lines:
                    row_words = [w.strip() for w in batch_line.split() if w.strip()]
                    words.extend(row_words)
                
                for word in words:
                    if not word.lower().startswith(expected_prefix.lower()):
                        print(f"  FAIL: {cmd} (word '{word}' doesn't start with '{expected_prefix}')")
                        all_valid = False
                        break
                break  # Only check once for batch mode
            else:
                # For single mode, check the word directly
                if not line.lower().startswith(expected_prefix.lower()):
                    print(f"  FAIL: {cmd} (word '{line}' doesn't start with '{expected_prefix}')")
                    all_valid = False
            
            if not all_valid:
                break
                
        if all_valid:
            if len(result_lines) == 1:
                print(f"  PASS: {cmd} -> '{result_lines[0]}'")
            else:
                print(f"  PASS: {cmd} -> {len(result_lines)} results with prefix '{expected_prefix}'")


def test_suffix_functionality():
    """Test suffix functionality with Markov chains."""
    print("\nTesting suffix functionality...")
    
    tests = [
        ("python nonsense_generator.py --markov --suffix=ing --single", "ing"),
        ("python nonsense_generator.py --markov --suffix=tion --single", "tion"),
        ("python nonsense_generator.py --markov --suffix=ly --single", "ly"),
        ("python nonsense_generator.py --markov --suffix=ed --single", "ed"),
        ("python nonsense_generator.py --markov --words=names --suffix=son --single", "son"),
        ("python nonsense_generator.py --markov --suffix=er --count=5", "er"),
        ("python nonsense_generator.py --markov --suffix=ing --token", "ing"),
        ("python nonsense_generator.py --name --suffix=ton", "ton"),
    ]
    
    for cmd, expected_suffix in tests:
        output, code = run_command(cmd)
        if code != 0:
            print(f"  FAIL: {cmd} (exit code {code})")
            continue
            
        lines = output.strip().split('\n')
        # Find the actual output (last non-verbose line)
        result_lines = []
        for line in lines:
            if line.strip() and not line.startswith(('Initializing', 'Loading', 'Downloaded', 'Built', 'Loaded', 'Saved')):
                result_lines.append(line.strip())
        
        if not result_lines:
            print(f"  FAIL: {cmd} (no output found)")
            continue
            
        all_valid = True
        for line in result_lines:
            if "--token" in cmd:
                # For token mode, check each word in the token
                words = line.split('-')
                for word in words:
                    if not word.lower().endswith(expected_suffix.lower()):
                        print(f"  FAIL: {cmd} (word '{word}' doesn't end with '{expected_suffix}')")
                        all_valid = False
                        break
            elif "--name" in cmd:
                # For name mode, check first name only
                parts = line.split(' ')
                if len(parts) >= 1:
                    first_name = parts[0].lower()
                    if not first_name.endswith(expected_suffix.lower()):
                        print(f"  FAIL: {cmd} (first name '{parts[0]}' doesn't end with '{expected_suffix}')")
                        all_valid = False
                else:
                    print(f"  FAIL: {cmd} (invalid name format: '{line}')")
                    all_valid = False
            elif "--count=" in cmd:
                # For batch mode, check each word
                words = []
                for batch_line in result_lines:
                    row_words = [w.strip() for w in batch_line.split() if w.strip()]
                    words.extend(row_words)
                
                for word in words:
                    if not word.lower().endswith(expected_suffix.lower()):
                        print(f"  FAIL: {cmd} (word '{word}' doesn't end with '{expected_suffix}')")
                        all_valid = False
                        break
                break  # Only check once for batch mode
            else:
                # For single mode, check the word directly
                if not line.lower().endswith(expected_suffix.lower()):
                    print(f"  FAIL: {cmd} (word '{line}' doesn't end with '{expected_suffix}')")
                    all_valid = False
            
            if not all_valid:
                break
                
        if all_valid:
            if len(result_lines) == 1:
                print(f"  PASS: {cmd} -> '{result_lines[0]}'")
            else:
                print(f"  PASS: {cmd} -> {len(result_lines)} results with suffix '{expected_suffix}'")


def test_prefix_suffix_mutual_exclusivity():
    """Test that prefix and suffix cannot be used together."""
    print("\nTesting prefix/suffix mutual exclusivity...")
    
    error_tests = [
        "python nonsense_generator.py --markov --prefix=test --suffix=ing --single",
        "python nonsense_generator.py --markov --prefix=cat --suffix=ly --count=5",
        "python nonsense_generator.py --name --prefix=john --suffix=son",
    ]
    
    for cmd in error_tests:
        output, code = run_command(cmd)
        if code == 0:
            print(f"  FAIL: {cmd} (should have failed but didn't)")
        else:
            print(f"  PASS: {cmd} (correctly failed with exit code {code})")


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
    
    # Clean up cache before running tests
    cleanup_cache()
    
    test_single_mode()
    test_token_mode()
    test_name_mode()
    test_batch_mode()
    test_error_cases()
    test_markov_parameters()
    test_prefix_functionality()
    test_suffix_functionality()
    test_prefix_suffix_mutual_exclusivity()
    test_length_ranges()
    
    print("\n" + "=" * 50)
    print("Testing complete!")


if __name__ == "__main__":
    main()
