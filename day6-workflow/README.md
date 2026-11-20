# Day 6 Challenge: Leave Question Workflow (Python)

A small AI workflow that answers leave questions from a policy, with a human approval before anything is sent.

**Flow:** question -> retrieve policy section -> AI drafts JSON -> human approves (y/n) -> mock API (webhook.site)

## Setup
1. Install Python 3.10+ and run: `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in the company-approved API URL, key and model, plus your webhook.site URL. Never push `.env`.
3. Run one question: `python leave_workflow.py "Can I carry over unused leave?"`
4. Run the 5-question test: `python run_tests.py` (type y or n at each approval). It writes `test_log.csv`.

## Files
- `leave_workflow.py`: the workflow (retrieve, AI step, JSON check, approval, action)
- `run_tests.py`: runs the 5 test questions and saves the log
- `Day6_Leave_Policy.txt`: the sample leave policy
- `.gitignore`: keeps `.env` out of GitHub

## Safety
- The API key is read from the environment, never written in code.
- Approval comes before the action. Rejecting stops everything.
- Out-of-scope questions return "Not found in the leave policy".
