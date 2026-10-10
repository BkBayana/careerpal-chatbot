"""
Automated demonstration: sends many different questions to the Flask app
(through Flask's test client, exactly like the web page does) and checks that
the chatbot answers each one with the right intent.

Run:  python demo_test.py
Output: prints the conversation and saves it to demo_transcript.md
"""

from app import app

SAMPLE_CV = """Aina Binti Ahmad
aina.ahmad@email.com | +60 12-345 6789 | linkedin.com/in/aina-ahmad

SUMMARY
Final-year Computer Science student with a passion for data analytics, seeking a junior data analyst role.

EDUCATION
Bachelor of Computer Science, Universiti Example, CGPA 3.65 (2022 - 2026)

EXPERIENCE
Data Analytics Intern, ABC Retail Sdn Bhd (Jun - Sep 2025)
- Developed a Power BI dashboard used by 30 managers to track weekly sales.
- Automated a monthly Excel report, reducing preparation time by 70%.
- Analysed 50,000 customer transactions to identify top-selling product categories.

PROJECTS
- Built a Python web app that predicts student dropout risk with 85% accuracy.
- Led a team of 4 to win 2nd place in a university hackathon.

SKILLS
Python, SQL, Power BI, Excel, Flask, communication, teamwork

ACTIVITIES
Treasurer, Computing Society - managed a budget of RM 5,000 and organised 3 workshops.
"""

GOOD_ANSWER = (
    "I am a final-year computer science student. During my internship last year I developed a dashboard "
    "for the sales team and automated a weekly report, which reduced the preparation time by 70 percent. "
    "I also led a team of four in a hackathon where we built an app and won second place. "
    "I'm now looking for a junior developer role where I can keep learning and contribute to real products."
)
BEHAVIORAL_ANSWER = (
    "During my final year project last semester, our team was two weeks behind schedule. My task was to get "
    "the backend finished. I organised the remaining work into daily goals, I fixed the database issues first "
    "and I coordinated with my teammates every morning. As a result we completed the project on time and "
    "received an A grade, and I learned how important planning is."
)

SCRIPT = [
    ("Small talk", ["Hello!", "Who are you?", "What can you do?"]),
    ("Career guidance by field", ["I'm interested in a career in software development",
                                  "What jobs can I do with a business degree?"]),
    ("CV & applications", ["How do I write a good CV?", "Give me some action verbs",
                           "How should I structure a cover letter?"]),
    ("Interview preparation", ["How do I prepare for a job interview?", "What is the STAR method?",
                               "How do I answer tell me about yourself?", "What is a good answer for my greatest weakness?",
                               "What questions should I ask the interviewer?"]),
    ("Job search & growth", ["Where can I find a job?", "I have no experience, how do I get an internship?",
                             "How to negotiate salary?", "What skills are in demand?",
                             "Tips for my linkedin profile", "I keep getting rejected and feel demotivated"]),
    ("Typo / speech-recognition tolerance", ["how do i improv my resum", "intervew tipps please"]),
    ("Out-of-scope question", ["What's the weather on Mars?"]),
    ("Feature: CV review (score /100)", ["Review my CV", SAMPLE_CV]),
    ("Feature: career quiz", ["Career quiz", "A", "the first one", "C", "Launching an app used by thousands"]),
    ("Feature: mock interview with scoring", ["Start a mock interview", "Software / IT", GOOD_ANSWER,
                                              "um I don't know, I like like basically money",
                                              BEHAVIORAL_ANSWER, "skip", "stop"]),
    ("Goodbye", ["Thanks a lot!", "Bye"]),
]

EXPECTED = {
    "Hello!": "greeting", "Who are you?": "identity", "What can you do?": "help",
    "I'm interested in a career in software development": "field_tech",
    "What jobs can I do with a business degree?": "field_business",
    "How do I write a good CV?": "cv_tips", "Give me some action verbs": "action_verbs",
    "How should I structure a cover letter?": "cover_letter",
    "How do I prepare for a job interview?": "interview_tips", "What is the STAR method?": "star_method",
    "How do I answer tell me about yourself?": "about_yourself",
    "What is a good answer for my greatest weakness?": "weakness",
    "What questions should I ask the interviewer?": "questions_to_ask",
    "Where can I find a job?": "job_search", "I have no experience, how do I get an internship?": "internship",
    "How to negotiate salary?": "salary", "What skills are in demand?": "skills",
    "Tips for my linkedin profile": "linkedin", "I keep getting rejected and feel demotivated": "motivation",
    "how do i improv my resum": "cv_tips", "intervew tipps please": "interview_tips",
    "What's the weather on Mars?": "fallback", "Review my CV": "start_cv_review", SAMPLE_CV: "cv_report",
    "Career quiz": "start_quiz", "Start a mock interview": "start_interview",
    "Thanks a lot!": "thanks", "Bye": "goodbye",
}


def main():
    client = app.test_client()
    out = ["# CareerPal – demonstration transcript\n",
           "Generated automatically by `demo_test.py` through the Flask `/api/chat` endpoint.\n"]
    passed = failed = 0
    welcome = client.get("/api/welcome").get_json()
    out.append("**CareerPal:**\n\n" + welcome["reply"] + "\n")

    for section, messages in SCRIPT:
        out.append(f"\n## {section}\n")
        for msg in messages:
            data = client.post("/api/chat", json={"message": msg}).get_json()
            shown = msg if msg != SAMPLE_CV else SAMPLE_CV[:90].replace("\n", " ") + " … *(full CV pasted)*"
            exp = EXPECTED.get(msg)
            ok = exp is None or data.get("intent") == exp
            passed += ok
            failed += not ok
            status = "" if exp is None else (" ✅" if ok else f" ❌ expected {exp}, got {data.get('intent')}")
            out.append(f"**You:** {shown}\n\n**CareerPal** _(intent: {data.get('intent')}){status}_:\n\n"
                       f"{data['reply']}\n\n---\n")
    summary = f"\n**Intent checks passed: {passed}/{passed + failed}**\n"
    out.append(summary)
    text = "\n".join(out)
    with open("demo_transcript.md", "w", encoding="utf-8") as f:
        f.write(text)
    print(text)
    return failed


if __name__ == "__main__":
    raise SystemExit(1 if main() else 0)
