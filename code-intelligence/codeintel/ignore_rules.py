import re
from pathlib import Path

def glob_to_regex(pattern: str) -> re.Pattern:
    """Translates a glob pattern to a compiled regex pattern (case-insensitive)."""
    # Normalize slashes
    pattern = pattern.replace('\\', '/')
    
    # If the pattern has no slashes, match it anywhere (like a standard gitignore rule)
    if '/' not in pattern:
        pattern = '**/' + pattern
        
    regex_parts = ['^']
    i = 0
    n = len(pattern)
    while i < n:
        if pattern[i:i+3] == '**/':
            regex_parts.append('(?:.*/)?')
            i += 3
        elif pattern[i:i+2] == '**':
            regex_parts.append('.*')
            i += 2
        elif pattern[i] == '*':
            regex_parts.append('[^/]*')
            i += 1
        elif pattern[i] == '?':
            regex_parts.append('[^/]')
            i += 1
        elif pattern[i] == '/':
            regex_parts.append('/')
            i += 1
        else:
            regex_parts.append(re.escape(pattern[i]))
            i += 1
    regex_parts.append('$')
    return re.compile(''.join(regex_parts), re.IGNORECASE)

class FileFilter:
    def __init__(self, include_patterns: list, exclude_patterns: list):
        self.include_regexes = [glob_to_regex(p) for p in include_patterns]
        self.exclude_regexes = [glob_to_regex(p) for p in exclude_patterns]
        
    def should_include(self, relative_path: str) -> bool:
        """Determines if a relative path should be included based on the rules."""
        # Normalize slashes
        rel_path_normalized = relative_path.replace('\\', '/')
        
        # Must match at least one include pattern
        included = False
        for rx in self.include_regexes:
            if rx.match(rel_path_normalized):
                included = True
                break
                
        if not included:
            return False
            
        # Must not match any exclude pattern
        for rx in self.exclude_regexes:
            if rx.match(rel_path_normalized):
                return False
                
        return True
