#!/usr/bin/env python
"""Test enhanced MockGPTGenerator with site-specific queries"""

from chat_interface import ChatInterface

chat = ChatInterface(use_mock=True)

# Test the previously problematic queries
test_queries = [
    "Tell me about Adam's Peak",
    "tell me about Vessagiri",
    "What can you tell me about Dambulla",
    "Describe Mihintale",
    "Tell me about ancient rock fortresses in Sri Lanka"
]

print("=" * 70)
print("TESTING ENHANCED RESPONSE GENERATION")
print("=" * 70)

for query in test_queries:
    result = chat.get_response(query)
    is_specific = "Adam's Peak" in result["response"] or \
                  "Vessagiri" in result["response"] or \
                  "Dambulla" in result["response"] or \
                  "Mihintale" in result["response"] or \
                  "Sigiriya" in result["response"]
    
    status = "[+] SPECIFIC" if is_specific else "[-] GENERIC"
    
    print("\nQuery: " + query)
    print("Status: " + status)
    print("Response: " + result['response'][:180] + "...")
    print("Quality: {:.2f}/1.0".format(result['evaluation']['overall_score']))
    print("-" * 70)

print("\nTest Complete!")

