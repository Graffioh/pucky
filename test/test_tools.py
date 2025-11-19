#!/usr/bin/env python3
"""Interactive CLI tool to test functions from src.tools."""

import sys
from pathlib import Path

# Add parent directory to path to import src
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.context import grep_search, scan_codebase
from src.edit import edit_file
from src.file import (
    create_directory,
    delete_file,
    read_file,
    write_file,
)
from src.tools import _execute_bash_command


def print_menu():
    """Print the interactive menu."""
    print("\n" + "=" * 60)
    print("🔧 Pucky Tools Tester")
    print("=" * 60)
    print("1. Read file")
    print("2. Write file")
    print("3. Edit file (patch)")
    print("4. Delete file")
    print("5. Create directory")
    print("6. Execute bash command")
    print("7. Scan codebase")
    print("8. Search codebase")
    print("0. Quit")
    print("=" * 60)


def get_input(prompt: str) -> str:
    """Get user input with a prompt."""
    try:
        return input(f"{prompt}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n\nExiting...")
        sys.exit(0)


def test_read_file():
    """Test the read_file function."""
    file_path = get_input("Enter file path")
    if not file_path:
        print("Error: File path cannot be empty")
        return
    print("\n📖 Reading file...")
    result = read_file(file_path)
    print(result)


def test_write_file():
    """Test the write_file function."""
    file_path = get_input("Enter file path")
    if not file_path:
        print("Error: File path cannot be empty")
        return
    print("Enter content (type 'EOF' on a new line to finish):")
    lines = []
    try:
        while True:
            line = input()
            if line == "EOF":
                break
            lines.append(line)
    except (EOFError, KeyboardInterrupt):
        pass
    content = "\n".join(lines)
    print("\n✏️  Writing file...")
    result = write_file(file_path, content)
    print(result)


def test_edit_file():
    """Test the edit_file function."""
    file_path = get_input("Enter file path")
    if not file_path:
        print("Error: File path cannot be empty")
        return
    print("Enter unified diff patch (type 'EOF' on a new line to finish):")
    print("Example patch format:")
    print("  @@ -1,3 +1,4 @@")
    print("   line1")
    print("  -old line")
    print("  +new line")
    print("   line3")
    lines = []
    try:
        while True:
            line = input()
            if line == "EOF":
                break
            lines.append(line)
    except (EOFError, KeyboardInterrupt):
        pass
    patch = "\n".join(lines)
    print("\n🔧 Applying patch...")
    result = edit_file(file_path, patch)
    print(result)


def test_delete_file():
    """Test the delete_file function."""
    file_path = get_input("Enter file path to delete")
    if not file_path:
        print("Error: File path cannot be empty")
        return
    confirm = get_input(f"Are you sure you want to delete '{file_path}'? (yes/no)")
    if confirm.lower() not in ("yes", "y"):
        print("Cancelled.")
        return
    print("\n🗑️  Deleting file...")
    result = delete_file(file_path)
    print(result)


def test_create_directory():
    """Test the create_directory function."""
    dir_path = get_input("Enter directory path")
    if not dir_path:
        print("Error: Directory path cannot be empty")
        return
    print("\n📁 Creating directory...")
    result = create_directory(dir_path)
    print(result)


def test_execute_bash_command():
    """Test the execute_bash_command function."""
    command = get_input("Enter bash command")
    if not command:
        print("Error: Command cannot be empty")
        return
    print(f"\n⚡ Executing command: {command}")
    result = _execute_bash_command(command)
    print(result)


def test_scan_codebase():
    """Test the scan_codebase function."""
    root_path = get_input("Enter root path (default: '.')") or "."
    print(f"\n🗺️  Scanning codebase at: {root_path}")
    result = scan_codebase(root_path)
    print(result)


def test_search_codebase():
    """Test the grep_search function."""
    root_path = get_input("Enter root path (default: '.')") or "."
    query = get_input("Enter search query")
    if not query:
        print("Error: Query cannot be empty")
        return
    max_results = get_input("Enter max results (default: 80)") or "80"
    print(f"\n🔍 Searching for '{query}' in {root_path}...")
    result = grep_search(root_path, query, max_results)
    print(result)


def main():
    """Main interactive loop."""
    print("\nWelcome to Pucky Tools Tester!")
    print("Select a tool to test from the menu below.\n")

    while True:
        print_menu()
        choice = get_input("\nSelect an option (0-8)")

        if choice == "0":
            print("\n👋 Goodbye!")
            break
        elif choice == "1":
            test_read_file()
        elif choice == "2":
            test_write_file()
        elif choice == "3":
            test_edit_file()
        elif choice == "4":
            test_delete_file()
        elif choice == "5":
            test_create_directory()
        elif choice == "6":
            test_execute_bash_command()
        elif choice == "7":
            test_scan_codebase()
        elif choice == "8":
            test_search_codebase()
        else:
            print(f"\n❌ Invalid choice: '{choice}'. Please select 0-8.")

        # Ask if user wants to continue
        if choice != "0":
            continue_choice = get_input("\nPress Enter to continue or 'q' to quit")
            if continue_choice.lower() in ("q", "quit"):
                print("\n👋 Goodbye!")
                break


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\n\n👋 Goodbye!")
        sys.exit(0)
