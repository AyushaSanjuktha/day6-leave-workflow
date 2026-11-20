"""Runs the 5 test questions and writes test_log.csv.

Usage:
  python run_tests.py            -> you type y or n for each approval
  python run_tests.py --auto     -> approves Q1-Q4 and rejects Q5 automatically (demo)
"""
import csv
import sys

from leave_workflow import run

TESTS = [
    ("Can I carry over unused leave?", "7"),
    ("Who approves my leave if my manager is on leave?", "4"),
    ("Can I take half a day of sick leave?", "3"),
    ("How many days in advance must I apply for casual leave?", "2"),
    ("What's the canteen menu today?", "Not found"),
]

auto = "--auto" in sys.argv
rows = []
for i, (question, correct) in enumerate(TESTS, start=1):
    print(f"\n===== Test {i}: {question}")
    decide = (lambda q, d, i=i: i <= 4) if auto else None
    result = run(question, approve=decide) if decide else run(question)
    draft = result["draft"]
    cited = draft["source_section"] or "Not found"
    cited_num = cited.split(".")[0] if cited != "Not found" else "Not found"
    rows.append({
        "#": i,
        "question": question,
        "correct_section": correct,
        "section_cited": cited,
        "correct": "Yes" if cited_num == correct else "No",
        "approved_or_rejected": "Approved" if result["approved"] else "Rejected",
        "reached_mock_api": "Yes" if result["reached_api"] else "No",
    })

with open("test_log.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
print("\nSaved test_log.csv")
