# test_policy.py
# Tests only the SEARCH part of the policy RAG (no LLM, no database).
# Run:  python test_policy.py
# For each question it prints the best score and checks that the right chunk was found.

from genai.policy_rag import (save_policy, search_policy, delete_policy,
                              is_policy_question, MIN_SCORE, VECTOR_DB)

TEST_ADMIN = 999                                   # a fake admin, only for this test
PDF_FILE = "rag_docs/sample_store_policy.pdf"

# (question, text that must be inside the top 3 chunks)
QUESTIONS = [
    ("How many days to return a product?", "7 days"),
    ("How long does a refund take?", "5 to 7 working days"),
    ("Is there a warranty on electronics?", "1 year"),
    ("Can I cancel a pending order?", "free of charge"),
    ("Is shipping free?", "1,000"),
    ("How soon must I report a damaged product?", "48 hours"),
]
# this question is NOT in the pdf, so the score should be low
NOT_IN_PDF = "Do you offer gift wrapping?"

print("Vector database:", VECTOR_DB)
print("Saving the policy (the first time it downloads the embedding model)...")
ok, message = save_policy(TEST_ADMIN, "sample_store_policy.pdf", PDF_FILE)
print(message, "\n")

passed = 0
for question, must_have in QUESTIONS:
    hits = search_policy(TEST_ADMIN, question)
    found = any(must_have in h["text"] for h in hits)
    if found:
        passed += 1
    print("PASS" if found else "FAIL", "| best score", round(hits[0]["score"], 2), "|", question)
print("\nSearch test:", passed, "out of", len(QUESTIONS), "passed")

hits = search_policy(TEST_ADMIN, NOT_IN_PDF)
print("\nQuestion that is not in the pdf:", NOT_IN_PDF)
print("Best score:", round(hits[0]["score"], 2), "(MIN_SCORE is", MIN_SCORE, ")")
print("-> the chatbot will say 'not found'" if hits[0]["score"] < MIN_SCORE
      else "-> score is above MIN_SCORE, so the LLM must say NOT_FOUND (increase MIN_SCORE if it answers wrongly)")

# the router: policy question -> policy pdf, sales question -> SQL
print("\nRouter test:")
ROUTER = [("What is the return policy?", True),
          ("How many days to return a product?", True),
          ("Can I cancel a pending order?", True),
          ("How many returned orders do I have?", False),
          ("How many Pending orders do I have?", False),
          ("What is my total revenue?", False)]
for question, expected in ROUTER:
    result = is_policy_question(question)
    print("PASS" if result == expected else "FAIL", "|", question, "->", "policy" if result else "SQL")

delete_policy(TEST_ADMIN)                          # clean up