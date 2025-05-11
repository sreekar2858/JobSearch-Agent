"""
Print Python's import path to help debug import issues
"""
import sys
import os

print("Python path:")
for path in sys.path:
    print(f"  - {path}")

print("\nLooking for cover_letter_prompts.py:")
for path in sys.path:
    if os.path.exists(os.path.join(path, "src", "prompts", "cover_letter_prompts.py")):
        print(f"  Found in {os.path.join(path, 'src', 'prompts')}")
        break
else:
    print("  Not found in sys.path")

# Also check if the file exists at the expected location
expected_path = os.path.join(os.getcwd(), "src", "prompts", "cover_letter_prompts.py")
print(f"\nExists at {expected_path}? {os.path.exists(expected_path)}")
