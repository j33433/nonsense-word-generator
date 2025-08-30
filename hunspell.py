"""Hunspell dictionary file parser for extracting word lists."""

import os
import urllib.request
import hashlib
import re


def parse_affix_rules(aff_content):
    """Parse Hunspell .aff file content to extract affix rules.
    
    Args:
        aff_content: Content of the .aff file as string
        
    Returns:
        dict: Dictionary mapping flag characters to affix rules
    """
    rules = {}
    lines = aff_content.split('\n')
    
    current_flag = None
    current_rules = []
    
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
            
        parts = line.split()
        if not parts:
            continue
            
        # Start of a new affix rule set
        if parts[0] in ['SFX', 'PFX']:  # Suffix or Prefix
            if current_flag and current_rules:
                rules[current_flag] = current_rules
            
            affix_type = parts[0]
            current_flag = parts[1] if len(parts) > 1 else None
            current_rules = []
            
        elif current_flag and len(parts) >= 4:
            # Individual affix rule: FLAG STRIP ADD CONDITION
            try:
                flag = parts[0]
                strip = parts[1] if parts[1] != '0' else ''
                add = parts[2] if parts[2] != '0' else ''
                condition = parts[3] if len(parts) > 3 else '.'
                
                if flag == current_flag:
                    current_rules.append({
                        'strip': strip,
                        'add': add,
                        'condition': condition,
                        'type': affix_type
                    })
            except (IndexError, ValueError):
                continue
    
    # Don't forget the last rule set
    if current_flag and current_rules:
        rules[current_flag] = current_rules
    
    return rules


def apply_affix_rules(word, flags, affix_rules):
    """Apply affix rules to generate morphological variants.
    
    Args:
        word: Base word
        flags: String of flag characters
        affix_rules: Dictionary of affix rules from parse_affix_rules
        
    Returns:
        set: Set of generated word forms including the original
    """
    variants = {word}
    
    for flag in flags:
        if flag in affix_rules:
            for rule in affix_rules[flag]:
                try:
                    # Check if the condition matches
                    condition = rule['condition']
                    if condition == '.':
                        # Always applies
                        matches = True
                    else:
                        # Simple regex matching - handle basic patterns
                        if condition.startswith('[') and condition.endswith(']'):
                            # Character class like [aeiou]
                            char_class = condition[1:-1]
                            if word and word[-1] in char_class:
                                matches = True
                            else:
                                matches = False
                        elif condition.endswith('$'):
                            # Ends with pattern
                            pattern = condition[:-1]
                            matches = word.endswith(pattern)
                        else:
                            # Simple suffix check
                            matches = word.endswith(condition)
                    
                    if matches:
                        # Apply the transformation
                        strip = rule['strip']
                        add = rule['add']
                        
                        if rule['type'] == 'SFX':  # Suffix
                            if strip and word.endswith(strip):
                                new_word = word[:-len(strip)] + add
                            else:
                                new_word = word + add
                        else:  # Prefix
                            if strip and word.startswith(strip):
                                new_word = add + word[len(strip):]
                            else:
                                new_word = add + word
                        
                        # Only add valid words
                        if new_word.isalpha() and 2 <= len(new_word) <= 20:
                            variants.add(new_word.lower())
                            
                except (IndexError, AttributeError):
                    continue
    
    return variants


def parse_hunspell_dic(file_path, expand_morphology=True):
    """Parse a Hunspell .dic file and extract clean words.
    
    Args:
        file_path: Path to the .dic file
        expand_morphology: If True, attempt to expand morphological forms
        
    Returns:
        set: Set of clean words (with morphological expansion if enabled)
        
    Raises:
        RuntimeError: If the file cannot be read or parsed
    """
    # Try multiple encodings as Hunspell dictionaries can use different encodings
    encodings_to_try = ['utf-8', 'iso-8859-1', 'cp1252', 'utf-8-sig']
    
    lines = None
    for encoding in encodings_to_try:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                lines = f.readlines()
            break
        except UnicodeDecodeError:
            continue
    
    if lines is None:
        raise RuntimeError(f"Could not decode file {file_path} with any of the tried encodings: {encodings_to_try}")
    
    try:
        
        if not lines:
            raise RuntimeError(f"Empty dictionary file: {file_path}")
        
        # Try to find and load corresponding .aff file for morphology
        affix_rules = {}
        if expand_morphology:
            aff_path = file_path.replace('.dic', '.aff')
            if os.path.exists(aff_path):
                try:
                    # Try the same encodings for .aff file
                    aff_content = None
                    for encoding in encodings_to_try:
                        try:
                            with open(aff_path, 'r', encoding=encoding) as aff_file:
                                aff_content = aff_file.read()
                            break
                        except UnicodeDecodeError:
                            continue
                    
                    if aff_content:
                        affix_rules = parse_affix_rules(aff_content)
                except Exception:
                    # If affix parsing fails, continue without morphology
                    pass
        
        # Skip first line (word count) and process remaining lines
        words = set()
        for line in lines[1:]:
            line = line.strip()
            if not line:
                continue
            
            # Split on '/' to separate word from affix flags
            parts = line.split('/', 1)
            word = parts[0].strip()
            flags = parts[1].strip() if len(parts) > 1 else ''
            
            # Only process alphabetic words of reasonable length
            if word.isalpha() and 2 <= len(word) <= 15:
                base_word = word.lower()
                words.add(base_word)
                
                # Apply morphological expansion if we have affix rules
                if expand_morphology and flags and affix_rules:
                    variants = apply_affix_rules(base_word, flags, affix_rules)
                    words.update(variants)
        
        return words
        
    except Exception as e:
        raise RuntimeError(f"Error parsing Hunspell dictionary {file_path}: {e}")


def download_hunspell_dict(url, cache_dir="cache", lang_code=None):
    """Download a Hunspell dictionary from a URL.
    
    Args:
        url: URL to download the .dic file from
        cache_dir: Directory to cache the downloaded file
        lang_code: Language code for more readable filenames (optional)
        
    Returns:
        str: Path to the downloaded .dic file
        
    Raises:
        RuntimeError: If the download fails
    """
    os.makedirs(cache_dir, exist_ok=True)
    
    # Create filename from URL hash, optionally with language code
    url_hash = hashlib.md5(url.encode()).hexdigest()
    if lang_code:
        dic_file = os.path.join(cache_dir, f"hunspell_{lang_code}_{url_hash}.dic")
        aff_file = os.path.join(cache_dir, f"hunspell_{lang_code}_{url_hash}.aff")
    else:
        dic_file = os.path.join(cache_dir, f"hunspell_dict_{url_hash}.dic")
        aff_file = os.path.join(cache_dir, f"hunspell_dict_{url_hash}.aff")
    
    if os.path.exists(dic_file):
        return dic_file
    
    try:
        # Download .dic file
        temp_dic = dic_file + ".tmp"
        if os.path.exists(temp_dic):
            os.remove(temp_dic)
        
        urllib.request.urlretrieve(url, temp_dic)
        
        if os.path.getsize(temp_dic) == 0:
            raise RuntimeError("Downloaded .dic file is empty")
        
        os.rename(temp_dic, dic_file)
        
        # Try to download corresponding .aff file for morphology
        aff_url = url.replace('.dic', '.aff')
        try:
            temp_aff = aff_file + ".tmp"
            if os.path.exists(temp_aff):
                os.remove(temp_aff)
            
            urllib.request.urlretrieve(aff_url, temp_aff)
            
            if os.path.getsize(temp_aff) > 0:
                os.rename(temp_aff, aff_file)
            else:
                os.remove(temp_aff)
                
        except Exception:
            # .aff file download failed, continue without morphology
            if os.path.exists(temp_aff):
                try:
                    os.remove(temp_aff)
                except:
                    pass
        
        return dic_file
        
    except Exception as e:
        # Clean up temp files on failure
        for temp_file in [temp_dic, temp_aff]:
            if 'temp_file' in locals() and os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass
        raise RuntimeError(f"Failed to download Hunspell dictionary from '{url}': {e}")


HUNSPELL_DICT_URLS = {
    "ar": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/ar/ar.dic",
    "bg": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/bg_BG/bg_BG.dic",
    "ca": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/ca/dictionaries/ca.dic",
    "cs": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/cs_CZ/cs_CZ.dic",
    "da": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/da_DK/da_DK.dic",
    "de": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/de/de_DE_frami.dic",
    "el": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/el_GR/el_GR.dic",
    "en": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/en/en_US.dic",
    "en-gb": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/en/en_GB.dic",
    "en-au": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/en/en_AU.dic",
    "en-ca": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/en/en_CA.dic",
    "en-za": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/en/en_ZA.dic",
    "es": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/es/es_ES.dic",
    "et": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/et_EE/et_EE.dic",
    "fr": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/fr_FR/fr.dic",
    "gl": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/gl/gl_ES.dic",
    "he": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/he_IL/he_IL.dic",
    "hr": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/hr_HR/hr_HR.dic",
    "hu": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/hu_HU/hu_HU.dic",
    "id": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/id/id_ID.dic",
    "is": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/is/is.dic",
    "it": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/it_IT/it_IT.dic",
    "ko": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/ko_KR/ko_KR.dic",
    "lt": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/lt_LT/lt.dic",
    "lv": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/lv_LV/lv_LV.dic",
    "nl": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/nl_NL/nl_NL.dic",
    "no": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/no/nb_NO.dic",
    "nn": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/no/nn_NO.dic",
    "pl": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/pl_PL/pl_PL.dic",
    "pt": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/pt_PT/pt_PT.dic",
    "pt-br": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/pt_BR/pt_BR.dic",
    "ro": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/ro/ro_RO.dic",
    "ru": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/ru_RU/ru_RU.dic",
    "sk": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/sk_SK/sk_SK.dic",
    "sl": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/sl_SI/sl_SI.dic",
    "sr": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/sr/sr-Latn.dic",
    "sv": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/sv_SE/sv_SE.dic",
    "th": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/th_TH/th_TH.dic",
    "tr": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/tr_TR/tr_TR.dic",
    "uk": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/uk_UA/uk_UA.dic",
    "vi": "https://raw.githubusercontent.com/LibreOffice/dictionaries/refs/heads/master/vi/vi_VN.dic",
}


def get_hunspell_words(language_or_url, verbose=False, expand_morphology=True):
    """Get words from a Hunspell dictionary by language code or URL.
    
    Args:
        language_or_url: Language code (e.g., 'en', 'es') or direct URL to .dic file
        verbose: Print progress messages
        expand_morphology: If True, expand morphological forms using affix rules
        
    Returns:
        set: Set of clean words from the dictionary
        
    Raises:
        ValueError: If the language code is not supported
        RuntimeError: If download or parsing fails
    """
    def vprint(*args, **kwargs):
        if verbose:
            print(*args, **kwargs)
    
    # Determine if it's a URL or language code
    if language_or_url.startswith(('http://', 'https://')):
        url = language_or_url
        display_name = f"custom URL ({url})"
    else:
        if language_or_url not in HUNSPELL_DICT_URLS:
            available = list(HUNSPELL_DICT_URLS.keys())
            raise ValueError(f"Unsupported language: {language_or_url}. Available: {available}")
        url = HUNSPELL_DICT_URLS[language_or_url]
        display_name = language_or_url
    
    vprint(f"Downloading Hunspell dictionary for {display_name}...")
    # Pass language code for better cache file naming
    lang_for_cache = language_or_url if not language_or_url.startswith(('http://', 'https://')) else None
    dic_file = download_hunspell_dict(url, lang_code=lang_for_cache)
    
    expansion_note = " with morphological expansion" if expand_morphology else ""
    vprint(f"Parsing Hunspell dictionary{expansion_note}: {dic_file}")
    words = parse_hunspell_dic(dic_file, expand_morphology=expand_morphology)
    
    vprint(f"Loaded {len(words)} words from Hunspell dictionary")
    return words
