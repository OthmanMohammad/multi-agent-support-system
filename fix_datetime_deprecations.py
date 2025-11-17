#!/usr/bin/env python3
"""
Script to fix deprecated datetime.utcnow() usage across the codebase.
Replaces datetime.utcnow() with datetime.now(UTC) and adds UTC import.
"""

import os
import re
from pathlib import Path
from typing import Set, List, Tuple

def check_has_utc_import(content: str) -> bool:
    """Check if file already has UTC import"""
    # Check for various UTC import patterns
    patterns = [
        r'from datetime import.*UTC',
        r'from datetime import \([\s\S]*?UTC',
    ]
    for pattern in patterns:
        if re.search(pattern, content):
            return True
    return False

def get_datetime_import_line(content: str) -> Tuple[int, str]:
    """Find the datetime import line and return (line_number, import_text)"""
    lines = content.split('\n')
    for i, line in enumerate(lines):
        # Match "from datetime import ..."
        if re.match(r'^from datetime import ', line):
            return (i, line)
    return (-1, "")

def add_utc_to_import(import_line: str) -> str:
    """Add UTC to existing datetime import"""
    # Handle different import styles
    if '(' in import_line:
        # Multi-line import: from datetime import (foo, bar)
        if import_line.rstrip().endswith(')'):
            # Single line with parentheses
            import_line = import_line.rstrip()[:-1] + ', UTC)'
        else:
            # Multi-line import (handled separately)
            pass
    else:
        # Single line: from datetime import datetime, timedelta
        import_line = import_line.rstrip() + ', UTC'

    return import_line

def fix_file(filepath: Path) -> bool:
    """Fix datetime deprecations in a single file. Returns True if changes made."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        original_content = content

        # Check if file has datetime.utcnow()
        if 'datetime.utcnow()' not in content:
            return False

        # Replace datetime.utcnow() with datetime.now(UTC)
        content = content.replace('datetime.utcnow()', 'datetime.now(UTC)')

        # Check if UTC import is needed
        if not check_has_utc_import(content):
            # Find and update datetime import
            line_num, import_line = get_datetime_import_line(content)
            if line_num >= 0:
                # Add UTC to import
                new_import = add_utc_to_import(import_line)
                lines = content.split('\n')
                lines[line_num] = new_import
                content = '\n'.join(lines)

        # Only write if changes were made
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True

        return False

    except Exception as e:
        print(f"Error processing {filepath}: {e}")
        return False

def main():
    """Main function to fix all Python files"""
    base_dir = Path("/home/user/multi-agent-support-system")
    src_dir = base_dir / "src"
    tests_dir = base_dir / "tests"
    migrations_dir = base_dir / "migrations"

    # Collect all Python files
    python_files: List[Path] = []

    for directory in [src_dir, tests_dir, migrations_dir]:
        if directory.exists():
            python_files.extend(directory.rglob("*.py"))

    # Filter out __pycache__ and venv
    python_files = [
        f for f in python_files
        if '__pycache__' not in str(f) and 'venv' not in str(f)
    ]

    print(f"Found {len(python_files)} Python files to check")

    fixed_count = 0
    fixed_files: List[str] = []

    for filepath in python_files:
        if fix_file(filepath):
            fixed_count += 1
            fixed_files.append(str(filepath.relative_to(base_dir)))
            print(f"✓ Fixed: {filepath.relative_to(base_dir)}")

    print(f"\n{'='*70}")
    print(f"Summary: Fixed {fixed_count} files")
    print(f"{'='*70}")

    if fixed_files:
        print("\nFixed files:")
        for f in fixed_files[:20]:  # Show first 20
            print(f"  - {f}")
        if len(fixed_files) > 20:
            print(f"  ... and {len(fixed_files) - 20} more")

if __name__ == "__main__":
    main()
