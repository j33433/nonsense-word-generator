"""Debug output management for verbose and trace messages."""

import sys
from contextlib import contextmanager


class Debug:
    """Manages debug output with print and trace methods."""
    
    def __init__(self, verbose=False, trace=False, output_file=None):
        """Initialize the debug manager.
        
        Args:
            verbose: Enable verbose output
            trace: Enable trace output  
            output_file: File object to write to (default: sys.stderr)
        """
        self.verbose = verbose
        self.trace_enabled = trace
        self.output_file = output_file or sys.stderr
        self._indent_level = 0
        self._indent_str = "  "
    
    def print(self, *args, **kwargs):
        """Print verbose message if verbose mode is enabled.
        
        Args:
            *args: Arguments to pass to print()
            **kwargs: Keyword arguments to pass to print()
        """
        if self.verbose:
            # Add indentation
            if args:
                first_arg = self._indent_str * self._indent_level + str(args[0])
                args = (first_arg,) + args[1:]
            kwargs.setdefault('file', self.output_file)
            print(*args, **kwargs)
    
    def trace(self, *args, **kwargs):
        """Print trace message if trace mode is enabled.
        
        Args:
            *args: Arguments to pass to print()
            **kwargs: Keyword arguments to pass to print()
        """
        if self.trace_enabled:
            # Add indentation
            if args:
                first_arg = self._indent_str * self._indent_level + str(args[0])
                args = (first_arg,) + args[1:]
            kwargs.setdefault('file', self.output_file)
            print(*args, **kwargs)
    
    def both(self, *args, **kwargs):
        """Print message if either verbose or trace mode is enabled.
        
        Args:
            *args: Arguments to pass to print()
            **kwargs: Keyword arguments to pass to print()
        """
        if self.verbose or self.trace_enabled:
            # Add indentation
            if args:
                first_arg = self._indent_str * self._indent_level + str(args[0])
                args = (first_arg,) + args[1:]
            kwargs.setdefault('file', self.output_file)
            print(*args, **kwargs)
    
    @contextmanager
    def indent(self, levels=1):
        """Context manager to temporarily increase indentation.
        
        Args:
            levels: Number of indentation levels to add
        """
        self._indent_level += levels
        try:
            yield
        finally:
            self._indent_level -= levels
    
    def set_indent(self, level):
        """Set the current indentation level.
        
        Args:
            level: New indentation level (0 = no indent)
        """
        self._indent_level = max(0, level)
    
    def generation_attempt(self, attempt_num, context=""):
        """Print a trace header for generation attempts.
        
        Args:
            attempt_num: The attempt number
            context: Additional context string
        """
        if context:
            self.trace(f"\n--- {context} generation attempt {attempt_num} ---")
        else:
            self.trace(f"\n--- Generation attempt {attempt_num} ---")
    
    def state_transition(self, current_state, options, chosen):
        """Print a trace of state transitions with options and choice.
        
        Args:
            current_state: Current state string
            options: List of (item, weight, probability) tuples
            chosen: The chosen item
        """
        if not self.trace_enabled:
            return
            
        option_strs = []
        for item, weight, prob in options:
            char_display = repr(item) if item in ["$", "^"] else item
            option_strs.append(f"{char_display}:{weight}({prob:.2f})")
        
        self.trace(f"'{current_state}' -> {' '.join(option_strs)}")
        
        char_display = repr(chosen) if chosen in ["$", "^"] else chosen
        with self.indent():
            self.trace(f"-> {char_display}")
    
    def word_progress(self, action, char, word, length):
        """Print trace of word building progress.
        
        Args:
            action: Action description (e.g., "Added", "End marker reached")
            char: Character involved (can be None)
            word: Current word state
            length: Current word length
        """
        if char:
            self.trace(f"{action} '{char}' -> word: '{word}' (length: {length})")
        else:
            self.trace(f"{action}. Word: '{word}' (length: {length})")
    
    def result(self, success, word, reason=""):
        """Print trace of generation result.
        
        Args:
            success: Whether generation was successful
            word: The generated word
            reason: Additional reason string
        """
        if success:
            self.trace(f"Valid word generated: '{word}'{' - ' + reason if reason else ''}")
        else:
            self.trace(f"Word rejected: '{word}'{' - ' + reason if reason else ''}")


# Convenience function to create a global debug instance
_global_debug = None

def get_debug():
    """Get the global debug instance."""
    global _global_debug
    if _global_debug is None:
        _global_debug = Debug()
    return _global_debug

def set_global_debug(verbose=False, trace=False, output_file=None):
    """Set the global debug instance with new settings.
    
    Args:
        verbose: Enable verbose output
        trace: Enable trace output
        output_file: File object to write to (default: sys.stderr)
    """
    global _global_debug
    _global_debug = Debug(verbose, trace, output_file)
    return _global_debug
