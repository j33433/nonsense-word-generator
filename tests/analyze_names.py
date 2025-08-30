#!/usr/bin/env python3
"""Analyze correlation between first and last name lengths."""

import sys
import statistics

def parse_names(text):
    """Parse names from text and return list of (first_len, last_len) tuples."""
    names = []
    for line in text.strip().split('\n'):
        line = line.strip()
        if line and ' ' in line:
            parts = line.split(' ', 1)
            if len(parts) == 2:
                first, last = parts
                if first.isalpha() and last.isalpha():
                    names.append((len(first), len(last)))
    return names

def compute_correlation(pairs):
    """Compute Pearson correlation coefficient between two variables."""
    if len(pairs) < 2:
        return 0.0
    
    x_values = [pair[0] for pair in pairs]
    y_values = [pair[1] for pair in pairs]
    
    n = len(pairs)
    x_mean = statistics.mean(x_values)
    y_mean = statistics.mean(y_values)
    
    # Calculate correlation coefficient
    numerator = sum((x - x_mean) * (y - y_mean) for x, y in pairs)
    x_variance = sum((x - x_mean) ** 2 for x in x_values)
    y_variance = sum((y - y_mean) ** 2 for y in y_values)
    
    if x_variance == 0 or y_variance == 0:
        return 0.0
    
    denominator = (x_variance * y_variance) ** 0.5
    return numerator / denominator

def main():
    """Analyze name length correlation."""
    # Load names from file
    try:
        with open('names.txt', 'r', encoding='utf-8') as f:
            sample_names = f.read()
    except FileNotFoundError:
        print("Error: names.txt file not found")
        print("Please create a names.txt file with one name per line in format 'Firstname Lastname'")
        return
    except Exception as e:
        print(f"Error reading names.txt: {e}")
        return
    
    # Parse names and compute statistics
    name_pairs = parse_names(sample_names)
    
    if not name_pairs:
        print("No valid names found")
        return
    
    first_lengths = [pair[0] for pair in name_pairs]
    last_lengths = [pair[1] for pair in name_pairs]
    
    print(f"Analyzed {len(name_pairs)} names")
    print()
    
    print("First name lengths:")
    print(f"  Range: {min(first_lengths)}-{max(first_lengths)}")
    print(f"  Mean: {statistics.mean(first_lengths):.1f}")
    print(f"  Median: {statistics.median(first_lengths)}")
    
    print()
    print("Last name lengths:")
    print(f"  Range: {min(last_lengths)}-{max(last_lengths)}")
    print(f"  Mean: {statistics.mean(last_lengths):.1f}")
    print(f"  Median: {statistics.median(last_lengths)}")
    
    print()
    correlation = compute_correlation(name_pairs)
    print(f"Correlation coefficient: {correlation:.3f}")
    
    if correlation > 0.7:
        print("Strong positive correlation - first and last names tend to have similar lengths")
    elif correlation > 0.3:
        print("Moderate positive correlation - some tendency for similar lengths")
    elif correlation > -0.3:
        print("Weak correlation - lengths are mostly independent")
    elif correlation > -0.7:
        print("Moderate negative correlation - longer first names tend to have shorter last names")
    else:
        print("Strong negative correlation - first and last names tend to have opposite lengths")
    
    print()
    print("Length distribution:")
    length_pairs = {}
    for first_len, last_len in name_pairs:
        key = f"{first_len}-{last_len}"
        length_pairs[key] = length_pairs.get(key, 0) + 1
    
    # Show most common length combinations
    sorted_pairs = sorted(length_pairs.items(), key=lambda x: x[1], reverse=True)
    print("Most common first-last length combinations:")
    for combo, count in sorted_pairs[:10]:
        first_len, last_len = combo.split('-')
        print(f"  {first_len:>2} - {last_len:<2} : {count:>2} occurrences")

if __name__ == "__main__":
    main()
