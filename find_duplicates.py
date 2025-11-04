"""
Script to find duplicate endpoint definitions in app.py
"""
import re

def find_duplicate_endpoints():
    """Find all duplicate endpoint definitions"""
    
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all endpoint definitions
    endpoint_pattern = r"endpoint='([^']+)'"
    endpoints = re.findall(endpoint_pattern, content)
    
    # Count occurrences
    endpoint_counts = {}
    for endpoint in endpoints:
        endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
    
    # Find duplicates
    duplicates = {k: v for k, v in endpoint_counts.items() if v > 1}
    
    if duplicates:
        print("="*80)
        print("DUPLICATE ENDPOINTS FOUND")
        print("="*80)
        for endpoint, count in sorted(duplicates.items()):
            print(f"{endpoint}: {count} occurrences")
        print("="*80)
        print(f"\nTotal duplicates: {len(duplicates)}")
        print(f"Total endpoints: {len(endpoint_counts)}")
    else:
        print("✓ No duplicate endpoints found")
    
    return duplicates

if __name__ == "__main__":
    find_duplicate_endpoints()
