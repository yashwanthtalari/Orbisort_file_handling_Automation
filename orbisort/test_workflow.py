import os
from core.action_engine import process_file
from database.vector_store import vector_store
from core.search_engine import semantic_search_files


# this is a new comment
def test_workflow():
    print("Testing Orbisort Action Engine with AI capabilities...")

    file1 = r"c:\Users\yashw\Downloads\Applications_built_by_me\Orbisort\orbisort\test_docs\invoice_2023.txt"
    file2 = r"c:\Users\yashw\Downloads\Applications_built_by_me\Orbisort\orbisort\test_docs\tax_return.md"

    print(f"\nProcessing {file1}...")
    new_path1 = process_file(file1)
    print(f"Moved to: {new_path1}")

    print(f"\nProcessing {file2}...")
    new_path2 = process_file(file2)
    print(f"Moved to: {new_path2}")

    print("\nTesting Semantic Search: 'hard drive'")
    results = semantic_search_files("hard drive")
    print(f"Results: {results}")

    print("\nTesting Semantic Search: 'income tax'")
    results = semantic_search_files("income tax")
    print(f"Results: {results}")


if __name__ == "__main__":
    test_workflow()
