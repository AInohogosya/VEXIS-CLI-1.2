"""
Multi-Format Code Block Handler for VEXIS-CLI-3

Supports detection, extraction, and removal of code blocks in multiple formats:
- Markdown: ```language ... ``` (existing)
- VEXIS:    ```vexis ... ``` (structured custom commands)
- XML:     <code> ... </code>
- BBCode:  [code] ... [/code]
- Custom:  ---code--- ... ---end-code---
- HTML:    <pre><code> ... </code></pre>
"""

import re
from typing import Optional, List, Tuple
from enum import Enum


class CodeBlockFormat(Enum):
    MARKDOWN = "markdown"
    VEXIS = "vexis"
    XML = "xml"
    BBCODE = "bbcode"
    CUSTOM_DELIMITER = "custom_delimiter"
    HTML = "html"


# Regex patterns for each supported code block format
# More specific patterns (HTML <pre><code>) must come before less specific ones (XML <code>)
CODE_BLOCK_PATTERNS: List[Tuple[CodeBlockFormat, str]] = [
    # VEXIS: ```vexis ... ```
    (CodeBlockFormat.VEXIS, r'```vexis\s*\n?(.*?)```'),
    # Markdown: ```language ... ```
    (CodeBlockFormat.MARKDOWN, r'```(?:\w+)?\s*\n?(.*?)```'),
    # HTML: <pre><code> ... </code></pre> (must precede XML to avoid partial match)
    (CodeBlockFormat.HTML, r'<pre><code[^>]*>\s*\n?(.*?)</code></pre>'),
    # XML: <code> ... </code>
    (CodeBlockFormat.XML, r'<code[^>]*>\s*\n?(.*?)</code>'),
    # BBCode: [code] ... [/code]
    (CodeBlockFormat.BBCODE, r'\[code\]\s*\n?(.*?)\[/code\]'),
    # Custom delimiter: ---code--- ... ---end-code---
    (CodeBlockFormat.CUSTOM_DELIMITER, r'---code---\s*\n?(.*?)---end-code---'),
]

# Pattern to detect the *start* of any code block (for validation checks)
# HTML <pre><code> must be checked before <code> to avoid false positives
CODE_BLOCK_START_PATTERNS: List[re.Pattern] = [
    re.compile(r'```vexis'),     # VEXIS
    re.compile(r'```'),           # Markdown
    re.compile(r'<pre><code\b'),  # HTML pre/code (must precede XML)
    re.compile(r'<code\b'),       # XML
    re.compile(r'\[code\]'),      # BBCode
    re.compile(r'---code---'),    # Custom delimiter
]


def _compile_all_patterns() -> List[Tuple[CodeBlockFormat, re.Pattern]]:
    """Compile all code block regex patterns with DOTALL flag."""
    return [
        (fmt, re.compile(patt, re.DOTALL))
        for fmt, patt in CODE_BLOCK_PATTERNS
    ]


_COMPILED_PATTERNS = _compile_all_patterns()


def extract_code_block(text: str) -> Optional[str]:
    """
    Extract the last code block from text in any supported format.
    If multiple code blocks are present, the last one is used.

    Args:
        text: Text containing code blocks in any supported format

    Returns:
        Extracted code block content or None if not found
    """
    if not text:
        return None

    best_match = None
    best_end = -1

    for fmt, pattern in _COMPILED_PATTERNS:
        matches = list(re.finditer(pattern, text))
        if matches:
            last_match = matches[-1]
            match_end = last_match.end()
            if match_end > best_end:
                best_end = match_end
                best_match = last_match.group(1).strip()

    return best_match


def extract_all_code_blocks(text: str) -> List[Tuple[str, CodeBlockFormat]]:
    """
    Extract all code blocks from text with their formats.

    Args:
        text: Text containing code blocks

    Returns:
        List of (content, format) tuples in order of appearance
    """
    if not text:
        return []

    results: List[Tuple[int, str, CodeBlockFormat]] = []

    for fmt, pattern in _COMPILED_PATTERNS:
        for match in re.finditer(pattern, text):
            results.append((match.start(), match.group(1).strip(), fmt))

    results.sort(key=lambda x: x[0])
    return [(content, fmt) for _, content, fmt in results]


def has_code_block(text: str) -> bool:
    """
    Check if text contains a code block in any supported format.

    Args:
        text: Text to check

    Returns:
        True if any code block format is detected
    """
    if not text:
        return False

    for start_pattern in CODE_BLOCK_START_PATTERNS:
        if start_pattern.search(text):
            return True

    return False


def remove_code_blocks(text: str) -> str:
    """
    Remove all code blocks from text, keeping only plain text.

    Args:
        text: Text containing code blocks

    Returns:
        Text with all code blocks removed
    """
    if not text:
        return text

    result = text

    for fmt, pattern in _COMPILED_PATTERNS:
        result = pattern.sub('', result)

    result = re.sub(r'\n\s*\n\s*\n', '\n\n', result)
    result = re.sub(r'\n\n\n+', '\n\n', result)
    return result.strip()


def detect_format(text: str) -> Optional[CodeBlockFormat]:
    """
    Detect which code block format is used in the text.
    Returns the first detected format (compiled patterns are ordered
    by specificity, so HTML <pre><code> is detected before XML <code>).

    Args:
        text: Text to analyze

    Returns:
        Detected CodeBlockFormat or None if no code block found
    """
    if not text:
        return None

    for fmt, pattern in _COMPILED_PATTERNS:
        if pattern.search(text):
            return fmt

    return None


def detect_all_formats(text: str) -> List[CodeBlockFormat]:
    """
    Detect all code block formats present in the text.

    Args:
        text: Text to analyze

    Returns:
        List of CodeBlockFormat values detected
    """
    if not text:
        return []

    detected = []
    for fmt, pattern in _COMPILED_PATTERNS:
        if pattern.search(text):
            detected.append(fmt)

    return detected


def get_format_description(fmt: CodeBlockFormat) -> str:
    """Get a human-readable description of a code block format."""
    descriptions = {
        CodeBlockFormat.VEXIS: "VEXIS (```vexis ... ```)",
        CodeBlockFormat.MARKDOWN: "Markdown (```language ... ```)",
        CodeBlockFormat.XML: "XML (<code> ... </code>)",
        CodeBlockFormat.BBCODE: "BBCode ([code] ... [/code])",
        CodeBlockFormat.CUSTOM_DELIMITER: "Custom delimiter (---code--- ... ---end-code---)",
        CodeBlockFormat.HTML: "HTML (<pre><code> ... </code></pre>)",
    }
    return descriptions.get(fmt, fmt.value)
