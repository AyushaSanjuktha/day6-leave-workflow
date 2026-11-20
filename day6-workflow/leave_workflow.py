"""Day 6 Challenge: Leave Question Workflow (Python version).

Flow: question -> retrieve policy section -> AI drafts JSON -> human approval -> mock API.
"""
import json
import os
import re
import sys

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()         
except ImportError:
    pass

POLICY_FILE = "Day6_Leave_Policy.txt"
NOT_FOUND = "Not found in the leave policy"
SKIP = {"the", "and", "for", "can", "what", "how", "who", "does", "will", "when",
        "with", "are", "you", "your", "have", "any", "get", "much", "many",
        "there", "this", "that", "from", "after"}


# ---------- 1. Retrieve ----------
def load_sections(path=POLICY_FILE):
    with open(path, encoding="utf-8") as f:
        policy = f.read()
    parts = re.split(r"\n(?=\d+\.\s)", policy)
    return [p.strip() for p in parts if re.match(r"^\d+\.", p.strip())]


def retrieve(question, sections, top_k=2):
    """Keyword scoring: count question words found in each section."""
    words = [w for w in re.findall(r"[a-z]+", question.lower())
             if len(w) > 2 and w not in SKIP]
    scored = []
    for s in sections:
        text = s.lower()
        score = sum(1 for w in words if w[:5] in text)
        scored.append((score, s))
    scored.sort(key=lambda x: x[0], reverse=True)
    best = [s for score, s in scored if score > 0][:top_k]
    return "\n\n".join(best) if best else "NO MATCHING SECTION"


# ---------- 2. AI step ----------
def build_prompt(question, context):
    return f"""You answer employee leave questions using ONLY the policy text below.

Policy text:
{context}

Question: {question}

Rules:
- If the policy text does not answer the question, set answer to "{NOT_FOUND}", source_section to null and confidence to "low".
- source_section is the number and title of the section you used, for example "7. Carry-over of unused leave".
- confidence is "high", "medium" or "low".
- Do not add anything that is not in the policy text.
- Reply with JSON only, in this format: {{"answer": "...", "source_section": "...", "confidence": "..."}}"""


def mock_llm(prompt):
    """Offline stand-in for testing the flow without an API key."""
    context = prompt.split("Policy text:\n")[1].split("\n\nQuestion:")[0]
    if context.strip() == "NO MATCHING SECTION":
        return json.dumps({"answer": NOT_FOUND, "source_section": None, "confidence": "low"})
    first = context.strip().split("\n\n")[0]
    title, _, body = first.partition("\n")
    return json.dumps({"answer": body.strip(), "source_section": title.strip(), "confidence": "high"})


def call_llm(prompt):
    if os.environ.get("LLM_MODE") == "mock":
        return mock_llm(prompt)
    url = os.environ["LLM_API_URL"]      # e.g. the approved provider's chat completions URL
    key = os.environ["LLM_API_KEY"]      # read from the environment, never typed in code
    model = os.environ["LLM_MODEL"]
    resp = requests.post(
        url,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json={"model": model, "temperature": 0,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=60,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]


# ---------- 3. Validate ----------
def parse_and_validate(raw):
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.M).strip()
    data = json.loads(raw)
    for field in ("answer", "source_section", "confidence"):
        if field not in data:
            raise ValueError(f"missing field: {field}")
    if data["confidence"] not in ("high", "medium", "low"):
        raise ValueError("confidence must be high, medium or low")
    return data


def draft_answer(question, context):
    prompt = build_prompt(question, context)
    for attempt in (1, 2):               # retry once, then stop with an error
        try:
            return parse_and_validate(call_llm(prompt))
        except (ValueError, json.JSONDecodeError) as err:
            print(f"  AI reply was not valid JSON (attempt {attempt}): {err}")
    raise RuntimeError("AI did not return valid JSON after 2 tries")


# ---------- 4. Approval ----------
def ask_approval(question, draft):
    print("\n--- DRAFT FOR APPROVAL ---")
    print(f"Question       : {question}")
    print(f"Answer         : {draft['answer']}")
    print(f"Source section : {draft['source_section']}")
    print(f"Confidence     : {draft['confidence']}")
    return input("Approve? (y/n): ").strip().lower() == "y"


# ---------- 5. Action (mock API) ----------
def send_to_mock_api(question, draft):
    payload = {"question": question, **draft, "status": "approved"}
    url = os.environ.get("WEBHOOK_URL")
    if not url:
        print("WEBHOOK_URL not set: dry run, nothing posted.")
        return False
    resp = requests.post(url, json=payload, timeout=30)
    resp.raise_for_status()
    print(f"Posted to mock API (HTTP {resp.status_code}).")
    return True


def run(question, approve=ask_approval):
    sections = load_sections()
    context = retrieve(question, sections)
    draft = draft_answer(question, context)
    approved = approve(question, draft)
    reached = False
    if approved:
        reached = send_to_mock_api(question, draft)
    else:
        print("Rejected: nothing sent")
    return {"draft": draft, "approved": approved, "reached_api": reached}


if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or input("Leave question: ")
    run(q)
