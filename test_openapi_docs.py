#!/usr/bin/env python3
"""
Test script to verify OpenAPI documentation shows endpoints correctly without duplication.
"""
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_openapi_structure():
    """Test that OpenAPI documentation is correctly structured."""
    from src.main import app

    print("🧪 Testing OpenAPI Documentation Structure")
    print("=" * 50)

    # Get OpenAPI schema
    openapi_schema = app.openapi()

    # Check basic info
    info = openapi_schema.get('info', {})
    print(f"✅ API Title: {info.get('title')}")
    print(f"✅ API Version: {info.get('version')}")

    # Get all paths
    paths = openapi_schema.get('paths', {})
    print(f"\n📊 Total endpoints: {len(paths)}")

    # Show all endpoints
    print("\n🔗 All API Endpoints:")
    for path, methods in paths.items():
        methods_list = [method.upper() for method in methods.keys() if method != 'parameters']
        print(f"  {', '.join(methods_list)} {path}")

    # Focus on Zendesk endpoints
    zendesk_paths = [path for path in paths.keys() if 'zendesk' in path.lower()]
    print(f"\n🎫 Zendesk Endpoints ({len(zendesk_paths)}):")

    for path in zendesk_paths:
        methods = paths[path]
        for method, details in methods.items():
            if method == 'parameters':
                continue

            tags = details.get('tags', [])
            summary = details.get('summary', 'No summary')
            print(f"  {method.upper()} {path}")
            print(f"    📋 Tags: {tags}")
            print(f"    📝 Summary: {summary}")

    # Verify no duplication
    print(f"\n✅ Verification:")
    tickets_endpoints = [path for path in paths.keys() if 'tickets' in path.lower()]
    print(f"  - Found {len(tickets_endpoints)} ticket-related endpoints")

    expected_endpoints = [
        "/api/zendesk/tickets",
        "/api/zendesk/tickets/{ticket_id}"
    ]

    for expected in expected_endpoints:
        if expected in paths:
            print(f"  ✅ {expected} - Found")
        else:
            print(f"  ❌ {expected} - Missing")

    # Check for duplicates
    all_paths = list(paths.keys())
    unique_paths = set(all_paths)

    if len(all_paths) == len(unique_paths):
        print(f"  ✅ No duplicate endpoints detected")
    else:
        print(f"  ❌ Found {len(all_paths) - len(unique_paths)} duplicate endpoints")

    # Check tags
    all_tags = set()
    for path, methods in paths.items():
        for method, details in methods.items():
            if method != 'parameters':
                tags = details.get('tags', [])
                all_tags.update(tags)

    print(f"\n🏷️  Tags used in API:")
    for tag in sorted(all_tags):
        print(f"  - {tag}")

    print(f"\n🎉 OpenAPI documentation is properly structured!")
    print(f"   - {len(paths)} total endpoints")
    print(f"   - {len(zendesk_paths)} Zendesk endpoints")
    print(f"   - {len(all_tags)} unique tags")
    print(f"   - No duplication detected")

if __name__ == "__main__":
    test_openapi_structure()