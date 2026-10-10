"""
CareerPal - Career Assistant chatbot engine.

A rule-based NLP chatbot (no paid API needed) that provides:
  * career guidance by field
  * CV / resume tips and an automatic CV analyser with a score out of 100
  * interview preparation tips and an interactive MOCK INTERVIEW with
    per-answer scoring and feedback
  * a career-match quiz
  * job search, LinkedIn, salary negotiation, cover letter advice, etc.

Intent matching = keyword + phrase scoring with light stemming and fuzzy
matching (handles typos and speech-recognition errors).
"""

import random
import re
from collections import Counter
from difflib import SequenceMatcher

# --------------------------------------------------------------------------
# Text helpers
# --------------------------------------------------------------------------

STOPWORDS = {
    "a", "an", "the", "i", "me", "my", "mine", "you", "your", "we", "our", "is",
    "are", "am", "was", "were", "be", "been", "do", "does", "did", "to", "for",
    "of", "in", "on", "at", "with", "and", "or", "but", "so", "it", "its", "this",
    "that", "these", "those", "can", "could", "would", "should", "will", "shall",
    "how", "what", "which", "who", "whom", "when", "where", "why", "some", "any",
    "please", "pls", "give", "tell", "about", "get", "have", "has", "had", "just",
    "want", "need", "like", "know", "there", "here", "if", "then", "than", "as",
    "by", "from", "up", "into", "out", "too", "very", "really", "also",
}
ARTICLES = {"a", "an", "the", "my", "your", "our", "some"}


def normalize(text: str) -> str:
    text = text.lower().replace("’", "'")
    text = re.sub(r"[^a-z0-9%'\s]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def stem(word: str) -> str:
    for suf in ("ing", "ed", "s"):
        if len(word) > len(suf) + 2 and word.endswith(suf) and not word.endswith("ss"):
            return word[: -len(suf)]
    return word


def tokens(text: str):
    return [stem(w) for w in normalize(text).split() if w not in STOPWORDS]


def phrase_text(text: str) -> str:
    return " ".join(w for w in normalize(text).split() if w not in ARTICLES)


# --------------------------------------------------------------------------
# Knowledge base (intents)
# --------------------------------------------------------------------------

MAIN_QUICK = ["Start a mock interview", "Review my CV", "Career quiz", "Interview tips"]

WELCOME = (
    "Hi! I'm **CareerPal**, your career assistant. 👋\n"
    "I can help you:\n"
    "- 🎤 **Practise a mock interview** with scored feedback\n"
    "- 📄 **Review your CV** and give it a score out of 100\n"
    "- 🧭 **Find a career that suits you** with a quick quiz\n"
    "- 💡 Give tips on CVs, cover letters, LinkedIn, salary and job search\n"
    "Type a question or press the 🎙 microphone and just talk to me."
)

INTENTS = [
    # ---------------- small talk ----------------
    {
        "tag": "greeting", "weight": 0.6,
        "keywords": ["hello", "hi", "hey", "hiya", "greetings", "salam", "yo"],
        "phrases": ["good morning", "good afternoon", "good evening", "assalamualaikum"],
        "responses": [
            "Hello! 😊 How can I help with your career today?",
            "Hi there! Ready to work on your career goals? You can ask me anything or try a mock interview.",
            "Hey! I'm CareerPal. Want to practise an interview, improve your CV, or explore careers?",
        ],
        "quick": MAIN_QUICK,
    },
    {
        "tag": "goodbye",
        "keywords": ["bye", "goodbye", "farewell", "cya"],
        "phrases": ["see you", "talk later", "that's all", "thats all"],
        "responses": [
            "Good luck with your career journey! 🚀 Come back any time to practise.",
            "Bye! Remember: every application is practice. You've got this! 💪",
        ],
    },
    {
        "tag": "thanks", "weight": 0.6,
        "keywords": ["thanks", "thank", "thx", "appreciate"],
        "phrases": ["thank you"],
        "responses": [
            "You're welcome! Anything else I can help with?",
            "Happy to help! 😊 Want to try a mock interview next?",
        ],
        "quick": MAIN_QUICK,
    },
    {
        "tag": "how_are_you",
        "keywords": [],
        "phrases": ["how are you", "how are you doing", "how's it going", "hows it going", "what's up", "whats up"],
        "responses": [
            "I'm doing great, thanks for asking! 😊 Ready to help with your career. What are you working on?",
            "All good here! How about you — preparing for interviews or job applications?",
        ],
        "quick": MAIN_QUICK,
    },
    {
        "tag": "identity",
        "keywords": ["bot", "careerpal"],
        "phrases": ["who are you", "your name", "what are you", "are you a bot", "are you human"],
        "responses": [
            "I'm **CareerPal**, a career assistant chatbot built with Python and Flask. "
            "I give career guidance, CV feedback and interview practice. I'm a bot, "
            "so for big decisions it's also worth talking to a career counsellor or mentor."
        ],
        "quick": MAIN_QUICK,
    },
    {
        "tag": "help",
        "keywords": ["help", "menu", "feature", "option", "commands"],
        "phrases": ["what can you do", "how do you work", "how to use", "what do you do"],
        "responses": [WELCOME + "\n\nTip: during a mock interview or quiz, say **stop** to leave."],
        "quick": MAIN_QUICK,
    },

    # ---------------- interactive modes ----------------
    {
        "tag": "start_interview", "action": "interview",
        "keywords": ["mock", "practice", "practise", "rehearse", "simulate", "simulation"],
        "phrases": ["mock interview", "practice interview", "practise interview", "interview practice",
                    "start interview", "start mock interview", "practice for interview",
                    "practise for interview", "practice again", "another interview", "interview me"],
    },
    {
        "tag": "start_cv_review", "action": "cv",
        "keywords": ["review", "analyse", "analyze", "check", "rate", "score", "evaluate", "cv", "resume"],
        "phrases": ["review cv", "check cv", "review resume", "analyse cv", "analyze cv", "cv review",
                    "resume review", "rate cv", "check resume", "feedback on cv", "score cv",
                    "analyze resume", "analyse resume"],
    },
    {
        "tag": "start_quiz", "action": "quiz",
        "keywords": ["quiz", "suit", "suits", "match", "personality"],
        "phrases": ["career quiz", "career test", "which career", "what career", "career suits me",
                    "career match", "what job suits me", "don't know what to do", "dont know what to do",
                    "choose career", "what should i study", "which job", "right career"],
    },

    # ---------------- CV & applications ----------------
    {
        "tag": "cv_tips",
        "keywords": ["cv", "resume", "tip", "improve", "write", "format", "template", "ats", "tips"],
        "phrases": ["how to write cv", "improve cv", "cv tips", "resume tips", "applicant tracking",
                    "good cv", "make cv", "write resume"],
        "responses": [
            "**How to write a strong CV** 📄\n"
            "1. **Keep it 1–2 pages**, clean layout, one simple font, no spelling mistakes.\n"
            "2. **Contact details** at the top: name, phone, professional email, LinkedIn/GitHub.\n"
            "3. **Short summary** (2–3 lines): who you are, key skills, what role you want.\n"
            "4. **Experience** in reverse order. Start each bullet with an **action verb** (led, built, improved).\n"
            "5. **Show results with numbers**: \"Increased club membership by 40%\" beats \"Responsible for membership\".\n"
            "6. **Tailor it** to each job: copy key words from the job ad (this also helps pass ATS filters).\n"
            "7. Include **projects, certifications and skills** — especially if you have little work experience.\n"
            "Want me to **review your CV** and give it a score? Just say \"review my CV\"."
        ],
        "quick": ["Review my CV", "Cover letter tips", "Action verbs"],
    },
    {
        "tag": "action_verbs",
        "keywords": ["verb", "verbs", "wording", "words"],
        "phrases": ["action verbs", "power words", "strong words"],
        "responses": [
            "**Strong action verbs for your CV** 💪\n"
            "- Leadership: *led, managed, coordinated, mentored, organised*\n"
            "- Achievement: *achieved, increased, reduced, improved, won*\n"
            "- Technical: *built, developed, designed, automated, analysed*\n"
            "- Communication: *presented, negotiated, trained, wrote, persuaded*\n"
            "Formula: **Action verb + what you did + result**. Example: "
            "\"Developed a Python script that cut report time from 3 hours to 20 minutes.\""
        ],
        "quick": ["Review my CV", "CV tips"],
    },
    {
        "tag": "cover_letter",
        "keywords": ["cover", "letter", "motivation"],
        "phrases": ["cover letter", "motivation letter", "application letter", "covering letter"],
        "responses": [
            "**Cover letter structure** ✉️ (keep it under one page)\n"
            "1. **Opening**: the role you're applying for and one sentence on why you're excited.\n"
            "2. **Why you**: 2–3 achievements that match the job requirements — use numbers.\n"
            "3. **Why them**: show you researched the company (a product, value or recent news).\n"
            "4. **Closing**: thank them and say you'd welcome an interview.\n"
            "Tips: address a real person if possible, don't repeat your CV word for word, "
            "and write a new letter for each company."
        ],
        "quick": ["CV tips", "Job search tips"],
    },

    # ---------------- interviews ----------------
    {
        "tag": "interview_tips",
        "keywords": ["interview", "prepare", "preparation", "nervous", "dress", "wear", "anxious"],
        "phrases": ["job interview", "interview tips", "prepare for interview", "what to wear",
                    "interview preparation", "before interview"],
        "responses": [
            "**Interview preparation checklist** ✅\n"
            "1. **Research the company**: products, values, recent news, competitors.\n"
            "2. **Study the job description** and match each requirement with an example from your experience.\n"
            "3. **Prepare stories with the STAR method** for behavioural questions.\n"
            "4. **Practise out loud** — try my mock interview!\n"
            "5. **Prepare 2–3 questions** to ask the interviewer.\n"
            "6. **Dress one level smarter** than the company's daily dress code.\n"
            "7. Arrive 10 minutes early (or test your camera and mic for online interviews).\n"
            "Nervous? That's normal. Slow breathing and practice reduce anxiety a lot."
        ],
        "quick": ["Start a mock interview", "STAR method", "Questions to ask"],
    },
    {
        "tag": "star_method",
        "keywords": ["star", "behavioral", "behavioural", "situation"],
        "phrases": ["star method", "star technique", "behavioral question", "behavioural question",
                    "star format"],
        "responses": [
            "**The STAR method** ⭐ — use it for \"Tell me about a time when...\" questions:\n"
            "- **S – Situation**: set the scene briefly (where, when).\n"
            "- **T – Task**: what was your responsibility or goal?\n"
            "- **A – Action**: what did *you* do? (say \"I\", not \"we\")\n"
            "- **R – Result**: the outcome, ideally with numbers, and what you learned.\n"
            "Example: \"In my final-year project (S), I had to deliver an app in 6 weeks (T). "
            "I split the work into weekly sprints and set up daily check-ins (A). We delivered "
            "a week early and got an A grade (R).\""
        ],
        "quick": ["Start a mock interview", "Interview tips"],
    },
    {
        "tag": "about_yourself",
        "keywords": ["introduce", "introduction", "pitch"],
        "phrases": ["tell me about yourself", "introduce myself", "self introduction", "elevator pitch",
                    "describe yourself"],
        "responses": [
            "**Answering \"Tell me about yourself\"** 🗣 — use **Present → Past → Future** (about 1 minute):\n"
            "- **Present**: who you are now. \"I'm a final-year Computer Science student specialising in data.\"\n"
            "- **Past**: 1–2 relevant achievements. \"During my internship I built a dashboard used by 30 staff.\"\n"
            "- **Future**: why this role. \"I'm excited to grow as a data analyst, and your company's work in X fits that.\"\n"
            "Avoid your life story, family details or reading your CV aloud."
        ],
        "quick": ["Start a mock interview", "Greatest weakness"],
    },
    {
        "tag": "weakness",
        "keywords": ["weakness", "weaknesses", "strength", "strengths"],
        "phrases": ["greatest weakness", "biggest weakness", "strengths and weaknesses", "my weakness",
                    "greatest strength"],
        "responses": [
            "**Strengths & weaknesses questions** ⚖️\n"
            "- **Strength**: pick one that fits the job and prove it with a short example.\n"
            "- **Weakness**: choose a *real but not critical* weakness, and show what you're doing to improve.\n"
            "Example: \"I used to find public speaking difficult, so I joined the debate club and now "
            "present in class confidently.\"\n"
            "Avoid clichés like \"I'm a perfectionist\" or \"I work too hard\" — interviewers hear them every day."
        ],
        "quick": ["Start a mock interview", "STAR method"],
    },
    {
        "tag": "questions_to_ask",
        "keywords": ["ask"],
        "phrases": ["questions to ask", "ask the interviewer", "ask interviewer", "any questions for us",
                    "questions for interviewer"],
        "responses": [
            "**Good questions to ask the interviewer** ❓\n"
            "- What does a typical day look like in this role?\n"
            "- What would success look like in the first 3 months?\n"
            "- How does the team support learning and development?\n"
            "- What are the biggest challenges the team is facing right now?\n"
            "- What are the next steps in the hiring process?\n"
            "Avoid asking about salary or leave in the first interview unless they bring it up."
        ],
        "quick": ["Interview tips", "Follow-up email"],
    },
    {
        "tag": "follow_up",
        "keywords": ["followup"],
        "phrases": ["thank you email", "follow up", "follow-up", "after interview", "thank you note",
                    "thank-you email", "follow up email"],
        "responses": [
            "**After the interview** 📬\n"
            "- Send a short thank-you email within **24 hours**.\n"
            "- Mention one specific thing you discussed and restate your interest.\n"
            "- If you hear nothing after the promised date, send one polite follow-up after about a week.\n"
            "Template: \"Dear Ms. Tan, thank you for meeting me today about the Junior Analyst role. "
            "I enjoyed learning about your new data platform and I'm even more excited to contribute. "
            "Best regards, Aina.\""
        ],
    },

    # ---------------- job search ----------------
    {
        "tag": "job_search",
        "keywords": ["job", "jobs", "vacancy", "vacancies", "apply", "application", "hiring", "hunt", "portal"],
        "phrases": ["find job", "job search", "looking for job", "where to apply", "job hunting",
                    "find work", "get job"],
        "responses": [
            "**Smart job search strategy** 🔎\n"
            "1. **Target 2–3 job titles** instead of applying to everything.\n"
            "2. Use job portals: **LinkedIn Jobs, Indeed, JobStreet, Glassdoor**, plus company career pages.\n"
            "3. **Network**: ~half of jobs are filled through referrals. Message alumni and attend career fairs.\n"
            "4. **Tailor** your CV for each application.\n"
            "5. Track applications in a spreadsheet (company, date, status, follow-up).\n"
            "6. Aim for quality: 5 tailored applications usually beat 50 generic ones."
        ],
        "quick": ["LinkedIn tips", "Review my CV", "Internship advice"],
    },
    {
        "tag": "internship",
        "keywords": ["internship", "intern", "placement", "trainee", "graduate", "experience"],
        "phrases": ["industrial training", "fresh graduate", "no experience", "first job",
                    "without experience", "entry level"],
        "responses": [
            "**Getting a first job or internship with little experience** 🎓\n"
            "- Highlight **projects**, coursework, final-year project and hackathons.\n"
            "- Count **volunteering, part-time jobs and club roles** — they show teamwork and responsibility.\n"
            "- Earn free **certificates** (Google, Microsoft Learn, Coursera, freeCodeCamp).\n"
            "- Build a **portfolio** (GitHub, Behance or a simple website).\n"
            "- Apply early: many internships open 3–6 months in advance.\n"
            "- Ask your lecturers and university career centre for referrals."
        ],
        "quick": ["Review my CV", "Skills in demand", "Job search tips"],
    },
    {
        "tag": "linkedin",
        "keywords": ["linkedin", "profile", "network", "networking", "connections", "brand"],
        "phrases": ["linkedin profile", "personal brand", "linkedin tips"],
        "responses": [
            "**LinkedIn profile tips** 🔗\n"
            "- Professional **photo** and a simple background banner.\n"
            "- **Headline** that says what you do or want: \"Computer Science Student | Python & Data Analytics\".\n"
            "- **About** section: 3–5 lines about your skills, interests and goals.\n"
            "- Add projects, certificates and volunteering with short results.\n"
            "- Set **Open to Work** (visible to recruiters only if you prefer).\n"
            "- Connect with classmates, lecturers and people in your target companies — add a short note."
        ],
        "quick": ["Job search tips", "Skills in demand"],
    },
    {
        "tag": "salary",
        "keywords": ["salary", "pay", "negotiate", "negotiation", "compensation", "raise", "wage", "offer"],
        "phrases": ["expected salary", "salary expectation", "ask for raise", "job offer",
                    "negotiate salary"],
        "responses": [
            "**Salary negotiation** 💰\n"
            "1. **Research the market rate** for the role and location (Glassdoor, LinkedIn Salary, job ads).\n"
            "2. When asked for expectations, give a **range** with your target near the bottom of it.\n"
            "3. **Let them make the first offer** when possible.\n"
            "4. Negotiate the whole package: bonus, training budget, flexible work, leave.\n"
            "5. Stay polite and justify with value: \"Based on my internship experience and the market range "
            "for this role, I was hoping for X. Is there flexibility?\"\n"
            "6. Get the final offer **in writing**."
        ],
        "quick": ["Interview tips", "Follow-up email"],
    },
    {
        "tag": "career_change",
        "keywords": ["switch", "transition", "pivot", "change"],
        "phrases": ["career change", "change career", "switch career", "change my career", "new field",
                    "change field", "switch field"],
        "responses": [
            "**Changing careers** 🔄\n"
            "1. Identify **transferable skills** (communication, analysis, project management).\n"
            "2. Fill gaps with short courses or certifications.\n"
            "3. Build proof: small projects, freelance work or volunteering in the new field.\n"
            "4. Talk to 3–5 people already in that field (informational interviews).\n"
            "5. Rewrite your CV around the **new** role, not your old job title.\n"
            "Not sure which field? Try my **career quiz**."
        ],
        "quick": ["Career quiz", "Skills in demand"],
    },
    {
        "tag": "skills",
        "keywords": ["skill", "skills", "demand", "future", "trending", "learn", "certification",
                     "course", "upskill", "certificate"],
        "phrases": ["in demand", "soft skills", "skills employers", "what should i learn", "future skills"],
        "responses": [
            "**Skills employers want** 📈\n"
            "**Technical / hard skills**\n"
            "- Data analysis (Excel, SQL, Python, Power BI)\n"
            "- AI tools and digital literacy\n"
            "- Cloud computing and cybersecurity basics\n"
            "- Digital marketing and content creation\n"
            "**Soft skills** (needed in every job)\n"
            "- Communication and presentation\n"
            "- Problem solving and critical thinking\n"
            "- Teamwork, adaptability and time management\n"
            "Pick **one technical skill** relevant to your field and build a small project with it."
        ],
        "quick": ["Career quiz", "Internship advice"],
    },
    {
        "tag": "remote",
        "keywords": ["remote", "hybrid", "freelance", "freelancing", "gig", "wfh", "freelancer"],
        "phrases": ["work from home", "remote job", "remote jobs", "online job", "online jobs"],
        "responses": [
            "**Remote and freelance work** 🏠\n"
            "- Platforms: LinkedIn (filter \"Remote\"), Upwork, Fiverr, We Work Remotely.\n"
            "- Build a portfolio first — clients hire based on proof of work.\n"
            "- Show remote skills: self-discipline, written communication, tools like Slack and Trello.\n"
            "- ⚠️ Beware of scams: never pay to get a job and never share bank PINs or passwords."
        ],
    },
    {
        "tag": "motivation",
        "keywords": ["reject", "rejected", "rejection", "demotivated", "stressed", "stress", "sad",
                     "failed", "fail", "unemployed", "hopeless", "tired", "give", "burnout", "worried"],
        "phrases": ["no response", "keep getting rejected", "lost my job", "burn out", "no one replies",
                    "nobody replies", "give up"],
        "responses": [
            "I'm sorry — job searching can be really tough. 💙 Rejection is normal: most people apply to "
            "many places before getting an offer, and it doesn't define your worth.\n"
            "Some things that help:\n"
            "- Ask for feedback after interviews when possible.\n"
            "- Let me **review your CV** — small fixes can change response rates.\n"
            "- Practise with a **mock interview** to build confidence.\n"
            "- Set small daily goals and take breaks.\n"
            "If stress is affecting your sleep or mood, talking to a friend, family member or your "
            "university counsellor can really help."
        ],
        "quick": ["Review my CV", "Start a mock interview"],
    },

    # ---------------- career fields ----------------
    {
        "tag": "field_tech", "weight": 1.1,
        "keywords": ["software", "programming", "programmer", "developer", "coding", "coder", "computer",
                     "data", "cybersecurity", "ai", "cloud", "web", "tech", "technology"],
        "phrases": ["information technology", "it career", "it job", "machine learning", "computer science",
                    "data science"],
        "responses": [
            "**Careers in Technology** 💻\n"
            "Roles: software developer, data analyst, data scientist, cybersecurity analyst, cloud engineer, "
            "UI/UX designer, AI/ML engineer.\n"
            "**Key skills**: programming (Python, JavaScript, Java), SQL, Git, problem solving.\n"
            "**How to start**:\n"
            "- Build 2–3 portfolio projects and put them on GitHub.\n"
            "- Earn a beginner certification (e.g. AWS Cloud Practitioner, Google Data Analytics).\n"
            "- Practise coding problems (LeetCode, HackerRank) for technical interviews."
        ],
        "quick": ["Start a mock interview", "Skills in demand"],
    },
    {
        "tag": "field_business", "weight": 1.1,
        "keywords": ["business", "marketing", "finance", "accounting", "accountant", "sales", "management",
                     "manager", "economics", "banking", "entrepreneur", "hr"],
        "phrases": ["human resources", "digital marketing", "business analyst"],
        "responses": [
            "**Careers in Business** 📊\n"
            "Roles: business analyst, digital marketer, accountant, financial analyst, HR executive, "
            "sales executive, project manager, entrepreneur.\n"
            "**Key skills**: Excel, communication, data analysis, negotiation, presentation.\n"
            "**How to start**:\n"
            "- Join business or entrepreneurship clubs and case competitions.\n"
            "- Learn Excel and Power BI; consider Google Digital Marketing or HubSpot certificates.\n"
            "- Professional qualifications (ACCA, CFA, CIMA) boost finance careers."
        ],
        "quick": ["Start a mock interview", "Skills in demand"],
    },
    {
        "tag": "field_health", "weight": 1.1,
        "keywords": ["health", "healthcare", "nurse", "nursing", "medical", "medicine", "doctor",
                     "pharmacy", "pharmacist", "clinic", "hospital", "physiotherapy", "psychology",
                     "teacher", "teaching", "education", "counsellor", "social"],
        "phrases": ["social work", "help people"],
        "responses": [
            "**Careers helping people (healthcare & education)** 🩺\n"
            "Roles: nurse, doctor, pharmacist, physiotherapist, psychologist, teacher, counsellor, social worker.\n"
            "**Key skills**: empathy, communication, patience, attention to detail, working under pressure.\n"
            "**How to start**:\n"
            "- Most roles require a specific degree and professional registration — check requirements early.\n"
            "- Volunteer at hospitals, NGOs or tutoring programmes to gain experience.\n"
            "- Shadow a professional for a day to see if the role fits you."
        ],
        "quick": ["Career quiz", "Start a mock interview"],
    },
    {
        "tag": "field_creative", "weight": 1.1,
        "keywords": ["design", "designer", "art", "artist", "creative", "writer", "writing", "media",
                     "video", "photography", "animation", "music", "film", "content"],
        "phrases": ["graphic design", "content creator", "social media"],
        "responses": [
            "**Creative careers** 🎨\n"
            "Roles: graphic designer, UI/UX designer, content creator, copywriter, video editor, "
            "animator, photographer, social media manager.\n"
            "**Key skills**: creativity, tools (Figma, Adobe, Canva, Premiere), storytelling, feedback handling.\n"
            "**How to start**:\n"
            "- Your **portfolio** matters more than grades — build one on Behance or a personal site.\n"
            "- Do small freelance or club projects to get real clients and testimonials.\n"
            "- Combine creativity with a business skill (marketing, UX research) for more job options."
        ],
        "quick": ["Career quiz", "Remote work"],
    },
    {
        "tag": "field_engineering", "weight": 1.1,
        "keywords": ["engineering", "engineer", "mechanical", "electrical", "civil", "chemical",
                     "manufacturing", "robotics"],
        "phrases": ["electrical engineering", "civil engineering", "mechanical engineering"],
        "responses": [
            "**Engineering careers** ⚙️\n"
            "Roles: mechanical, electrical, civil, chemical, manufacturing and robotics engineers.\n"
            "**Key skills**: maths, CAD (AutoCAD, SolidWorks), MATLAB, problem solving, safety standards.\n"
            "**How to start**:\n"
            "- Industrial training/internships are essential — apply early.\n"
            "- Join competitions (robotics, design challenges) and student engineering societies.\n"
            "- Work towards professional engineer registration after graduating."
        ],
        "quick": ["Internship advice", "Start a mock interview"],
    },
]

FALLBACKS = [
    "Hmm, I'm not sure I understood that. 🤔 I'm a career assistant — try asking about CVs, interviews, "
    "job search, salary, or careers in a field like IT or business.",
    "Sorry, I didn't get that. You could say things like **\"Review my CV\"**, **\"Start a mock interview\"** "
    "or **\"What careers suit me?\"**",
]

EXIT_WORDS = {
    "quit", "stop", "exit", "cancel", "end", "menu", "main menu", "stop interview", "end interview",
    "quit interview", "cancel interview", "stop quiz", "cancel quiz", "quit quiz", "stop it",
}

# --------------------------------------------------------------------------
# Mock interview data
# --------------------------------------------------------------------------

GENERAL_QUESTIONS = [
    {"q": "Why do you want to work for our company?", "type": "company",
     "tip": "Mention something specific about the company and connect it to your goals."},
    {"q": "What is your greatest strength?", "type": "general",
     "tip": "Pick one strength relevant to the job and prove it with an example."},
    {"q": "Where do you see yourself in five years?", "type": "general",
     "tip": "Show ambition that fits the company: skills you'll grow and responsibilities you'll take on."},
    {"q": "What is your greatest weakness?", "type": "general",
     "tip": "Give a real weakness and explain what you're doing to improve it."},
]
FIRST_QUESTION = {"q": "Tell me about yourself.", "type": "general",
                  "tip": "Use Present → Past → Future in about one minute."}

BEHAVIORAL_QUESTIONS = [
    {"q": "Tell me about a time you faced a difficult challenge. How did you handle it?", "type": "behavioral",
     "tip": "Use STAR: Situation, Task, Action, Result."},
    {"q": "Describe a situation where you worked in a team to achieve a goal.", "type": "behavioral",
     "tip": "Use STAR and make clear what YOU did in the team."},
    {"q": "Give an example of a time you made a mistake. What did you learn?", "type": "behavioral",
     "tip": "Be honest, focus on how you fixed it and what you learned."},
    {"q": "Tell me about a time you had to meet a tight deadline.", "type": "behavioral",
     "tip": "Use STAR and explain how you prioritised."},
]

ROLE_QUESTIONS = {
    "tech": [
        {"q": "Tell me about a technical project you are proud of.", "type": "behavioral",
         "tip": "Explain the problem, the technologies you used, your role and the result."},
        {"q": "How do you approach debugging a problem you have never seen before?", "type": "role",
         "tip": "Describe a clear step-by-step process: reproduce, isolate, research, test, fix."},
        {"q": "How do you keep your technical skills up to date?", "type": "role",
         "tip": "Mention specific courses, projects, communities or documentation you use."},
    ],
    "business": [
        {"q": "How would you persuade a customer who is not interested in our product?", "type": "role",
         "tip": "Show listening skills: understand their needs first, then connect the product's value."},
        {"q": "Tell me about a time you used data to make a decision.", "type": "behavioral",
         "tip": "Use STAR and mention the numbers or tools you used."},
        {"q": "How do you prioritise when you have many tasks at once?", "type": "role",
         "tip": "Mention a method (to-do lists, urgent vs important) and an example."},
    ],
    "health": [
        {"q": "How would you handle a patient or client who is upset or angry?", "type": "role",
         "tip": "Show empathy, calm communication and following procedures."},
        {"q": "Why did you choose a career in healthcare?", "type": "role",
         "tip": "Share a genuine motivation and a related experience."},
        {"q": "Tell me about a time you worked under pressure.", "type": "behavioral",
         "tip": "Use STAR and show how you stayed calm and accurate."},
    ],
    "general": [
        {"q": "Why should we hire you instead of other candidates?", "type": "role",
         "tip": "Summarise 2–3 strengths that match the job, with proof."},
        {"q": "Tell me about something you achieved during your studies.", "type": "behavioral",
         "tip": "Use STAR and include a measurable result if possible."},
        {"q": "How do you handle criticism or feedback?", "type": "role",
         "tip": "Show you welcome feedback and give an example of improving because of it."},
    ],
}

ROLE_KEYWORDS = {
    "tech": ["software", "it", "tech", "technology", "developer", "programming", "computer", "data",
             "engineer", "engineering", "cyber", "web", "first", "one", "1", "a"],
    "business": ["business", "marketing", "finance", "sales", "account", "accounting", "management",
                 "hr", "economics", "second", "two", "2", "b"],
    "health": ["health", "healthcare", "nurse", "nursing", "medical", "doctor", "pharmacy", "clinic",
               "hospital", "third", "three", "3", "c"],
    "general": ["general", "fresh", "graduate", "any", "other", "student", "fourth", "four", "4", "d"],
}
ROLE_LABELS = {"tech": "Software / IT", "business": "Business / Marketing",
               "health": "Healthcare", "general": "General / Fresh graduate"}

ACTION_VERBS = {
    "led", "managed", "organised", "organized", "coordinated", "created", "built", "developed", "designed",
    "improved", "increased", "reduced", "achieved", "solved", "launched", "implemented", "analysed",
    "analyzed", "planned", "trained", "mentored", "presented", "negotiated", "delivered", "completed",
    "handled", "resolved", "initiated", "established", "streamlined", "automated", "won", "supervised",
    "researched", "collaborated", "volunteered", "taught", "helped", "learned", "learnt", "fixed",
    "decided", "prioritised", "prioritized", "communicated", "worked", "wrote", "programmed", "tested",
}
RESULT_WORDS = {"result", "resulted", "outcome", "increased", "reduced", "improved", "achieved", "won",
                "saved", "grade", "award", "successfully", "success", "finished", "completed", "learned",
                "learnt", "percent"}
SITUATION_WORDS = {"when", "during", "once", "project", "semester", "internship", "year", "last",
                   "situation", "time", "while"}
FILLER_PATTERNS = [r"\bum+\b", r"\buh+\b", r"\berm\b", r"\byou know\b", r"\bbasically\b", r"\bkind of\b",
                   r"\bsort of\b", r"\blike\b"]
NEGATIVE_PATTERNS = [r"\bhate\b", r"\bboring\b", r"\blazy\b", r"\bstupid\b", r"\bterrible\b",
                     r"\bworst\b", r"\bdon'?t know\b", r"\bno idea\b", r"\bdon'?t care\b"]
COMPANY_WORDS = {"company", "mission", "values", "culture", "product", "products", "service", "services",
                 "reputation", "grow", "growth", "innovation", "team", "industry"}

# --------------------------------------------------------------------------
# Career quiz data
# --------------------------------------------------------------------------

QUIZ = [
    ("What do you enjoy most?",
     ["Solving puzzles and working with computers", "Leading people, selling ideas or managing money",
      "Helping, caring for or teaching people", "Creating things: art, design, writing or video"]),
    ("Which school subject did you like best?",
     ["Maths, Computer Science or Physics", "Economics, Business or Accounting",
      "Biology, Psychology or Languages", "Art, Literature or Media"]),
    ("What does your ideal work day look like?",
     ["Building or fixing something technical", "Meetings, negotiating and planning strategy",
      "Working directly with patients, students or clients", "Brainstorming and producing creative work"]),
    ("Which achievement would make you proudest?",
     ["Launching an app used by thousands of people", "Growing a business or leading a team to a target",
      "Improving someone's health or life", "Seeing your design or story admired by many people"]),
]
QUIZ_CATS = ["tech", "business", "people", "creative"]
QUIZ_RESULTS = {
    "tech": ("Technology & Data 💻",
             "software developer, data analyst, cybersecurity analyst, cloud engineer, AI engineer",
             "Learn Python or JavaScript and build a small project this month."),
    "business": ("Business & Management 📊",
                 "business analyst, digital marketer, financial analyst, project manager, entrepreneur",
                 "Master Excel and join a business club or case competition."),
    "people": ("Healthcare, Education & Social Impact 🩺",
               "nurse, psychologist, teacher, counsellor, physiotherapist, HR specialist",
               "Volunteer with an NGO, school or hospital to test the fit."),
    "creative": ("Creative & Media 🎨",
                 "graphic designer, UI/UX designer, content creator, copywriter, video editor",
                 "Start a portfolio on Behance or Instagram with 5 pieces of work."),
}
ORDINALS = {"1": 0, "one": 0, "first": 0, "a": 0, "2": 1, "two": 1, "second": 1, "b": 1, "be": 1, "bee": 1,
            "3": 2, "three": 2, "third": 2, "c": 2, "see": 2, "sea": 2, "4": 3, "four": 3, "for": 3,
            "fourth": 3, "d": 3, "dee": 3}

# --------------------------------------------------------------------------
# CV analyser data
# --------------------------------------------------------------------------

CV_SECTIONS = {
    "Professional summary": ["summary", "objective", "profile", "about me", "career objective"],
    "Education": ["education", "degree", "university", "bachelor", "diploma", "cgpa", "gpa", "college",
                  "foundation", "spm", "a-level", "a level"],
    "Work experience": ["experience", "employment", "work history", "internship", "intern", "worked at"],
    "Skills": ["skills", "competencies", "technical skills", "proficient", "languages"],
    "Projects / achievements": ["project", "projects", "achievement", "achievements", "award", "awards",
                                "certification", "certifications", "certificate", "volunteer",
                                "activities", "leadership"],
}
CV_CLICHES = ["responsible for", "duties included", "hardworking", "hard-working", "team player",
              "go-getter", "think outside the box", "detail-oriented", "detail oriented",
              "self-motivated", "passionate", "result-driven", "results-driven"]


class CareerBot:
    """Stateless engine: conversation state is passed in per user session."""

    def __init__(self, seed=None):
        self.rng = random.Random(seed)
        for intent in INTENTS:
            intent["_kw"] = {stem(k) for k in intent.get("keywords", [])}
            intent["_ph"] = [phrase_text(p) for p in intent.get("phrases", [])]

    # ---------------- public API ----------------
    @staticmethod
    def new_state():
        return {"mode": None, "data": {}, "fallbacks": 0}

    def welcome(self):
        return {"reply": WELCOME, "quick_replies": MAIN_QUICK, "mode": None, "intent": "welcome"}

    def reply(self, message, state):
        result = self._reply(message, state)
        result.setdefault("quick_replies", [])
        result["mode"] = state["mode"]
        return result

    # ---------------- classification ----------------
    def classify(self, message):
        toks = tokens(message)
        ptext = " " + phrase_text(message) + " "
        best, best_score, best_raw = None, 0.0, 0.0
        for intent in INTENTS:
            score = 0.0
            for p in intent["_ph"]:
                if p and (" " + p + " ") in ptext:
                    score += 3
            kw = intent["_kw"]
            for t in toks:
                if t in kw:
                    score += 1
                elif len(t) > 4 and any(len(k) > 4 and SequenceMatcher(None, t, k).ratio() >= 0.85 for k in kw):
                    score += 0.8  # typo / speech-recognition tolerance
            weighted = score * intent.get("weight", 1.0)  # weight only breaks ties between intents
            if weighted > best_score:
                best, best_score, best_raw = intent, weighted, score
        return best, best_raw

    # ---------------- main router ----------------
    def _reply(self, message, state):
        msg = (message or "").strip()[:8000]
        if not msg:
            return {"reply": "I didn't catch that — could you type or say it again?", "quick_replies": MAIN_QUICK}
        norm = normalize(msg)

        if state["mode"] and norm in EXIT_WORDS:
            state["mode"], state["data"] = None, {}
            return {"reply": "No problem — I've stopped that activity. What would you like to do next?",
                    "quick_replies": MAIN_QUICK, "intent": "exit_mode"}

        if state["mode"] == "interview":
            return self._interview_step(msg, state)
        if state["mode"] == "quiz":
            return self._quiz_step(msg, state)
        if state["mode"] == "cv":
            return self._cv_step(msg, state)

        # A long pasted CV outside CV mode -> analyse it directly
        if len(norm.split()) > 120 and sum(1 for k in ("education", "experience", "skills") if k in norm) >= 2:
            return self._cv_report(msg)

        intent, score = self.classify(msg)
        if intent is None or score < 0.8:
            state["fallbacks"] += 1
            text = FALLBACKS[(state["fallbacks"] - 1) % len(FALLBACKS)]
            return {"reply": text, "quick_replies": MAIN_QUICK, "intent": "fallback"}

        state["fallbacks"] = 0
        action = intent.get("action")
        if action == "interview":
            return self._start_interview(state)
        if action == "cv":
            state["mode"] = "cv"
            return {"reply": "Great! 📄 **Paste the text of your CV** below (copy everything from your Word/PDF file) "
                             "and I'll score it and suggest improvements.\nSay **cancel** to go back.",
                    "quick_replies": ["Cancel"], "intent": "start_cv_review"}
        if action == "quiz":
            return self._start_quiz(state)

        return {"reply": self.rng.choice(intent["responses"]), "quick_replies": intent.get("quick", []),
                "intent": intent["tag"]}

    # ---------------- mock interview ----------------
    def _start_interview(self, state):
        state["mode"] = "interview"
        state["data"] = {"step": "role"}
        return {"reply": "Let's do a **mock interview**! 🎤 I'll ask you **5 questions** and score each answer.\n"
                         "Tip: press the 🎙 mic and answer out loud, just like a real interview.\n"
                         "First — **which kind of job are you preparing for?**\n"
                         "1. Software / IT\n2. Business / Marketing\n3. Healthcare\n4. General / Fresh graduate",
                "quick_replies": list(ROLE_LABELS.values()), "intent": "start_interview"}

    def _detect_role(self, msg):
        words = normalize(msg).split()
        best, best_hits = None, 0
        for role, kws in ROLE_KEYWORDS.items():
            hits = sum(1 for w in words if w in kws and w not in ORDINALS)
            if hits > best_hits:
                best, best_hits = role, hits
        if best is None and len(words) <= 3:  # "1", "option b", "the second one"
            order = list(ROLE_KEYWORDS)
            for w in words:
                if w in ORDINALS:
                    return order[ORDINALS[w]]
        return best

    def _interview_step(self, msg, state):
        data = state["data"]
        norm = normalize(msg)

        if data["step"] == "role":
            role = self._detect_role(msg) or "general"
            questions = [FIRST_QUESTION]
            questions += self.rng.sample(GENERAL_QUESTIONS, 1)
            questions += self.rng.sample(ROLE_QUESTIONS[role], 2)
            behavioral = [q for q in BEHAVIORAL_QUESTIONS]
            questions.append(self.rng.choice(behavioral))
            data.update({"step": "answer", "role": role, "questions": questions, "idx": 0,
                         "scores": [], "tips": []})
            intro = f"Great — **{ROLE_LABELS[role]}** interview. Answer as if I'm the interviewer. " \
                    "Say **skip** to skip a question or **stop** to end.\n"
            return {"reply": intro + "\n" + self._question_text(data),
                    "quick_replies": ["Skip", "Stop"], "intent": "interview_question"}

        if norm in {"repeat", "repeat question", "again", "say again", "pardon"}:
            return {"reply": self._question_text(data), "quick_replies": ["Skip", "Stop"],
                    "intent": "interview_question"}

        q = data["questions"][data["idx"]]
        if norm in {"skip", "next", "pass", "skip question", "next question"}:
            feedback = "Skipped. ⏭"
        else:
            score, good, improve = self.evaluate_answer(msg, q["type"])
            data["scores"].append(score)
            data["tips"].extend(improve)
            lines = [f"**Score: {score}/10** {self._stars(score)}"]
            if good:
                lines.append("✅ **What was good**")
                lines += [f"- {g}" for g in good]
            if improve:
                lines.append("🛠 **How to improve**")
                lines += [f"- {i}" for i in improve]
            feedback = "\n".join(lines)

        data["idx"] += 1
        if data["idx"] < len(data["questions"]):
            return {"reply": feedback + "\n---\n" + self._question_text(data),
                    "quick_replies": ["Skip", "Stop"], "intent": "interview_feedback"}

        # interview finished
        summary = self._interview_summary(data)
        state["mode"], state["data"] = None, {}
        return {"reply": feedback + "\n---\n" + summary,
                "quick_replies": ["Practice again", "Review my CV", "STAR method"], "intent": "interview_summary"}

    @staticmethod
    def _stars(score):
        full = int(score / 2 + 0.5)
        return "★" * full + "☆" * (5 - full)

    @staticmethod
    def _question_text(data):
        q = data["questions"][data["idx"]]
        label = {"behavioral": "Behavioural", "role": "Role-specific", "company": "Motivation"}.get(q["type"], "General")
        return (f"**Question {data['idx'] + 1} of {len(data['questions'])}** ({label})\n"
                f"{q['q']}\n*Hint: {q['tip']}*")

    def _interview_summary(self, data):
        scores = data["scores"]
        if not scores:
            return "🏁 **Interview finished.** You skipped all the questions — try again when you're ready!"
        avg = sum(scores) / len(scores)
        label = ("Excellent 🌟" if avg >= 8 else "Good 👍" if avg >= 6.5 else
                 "Fair — keep practising 💪" if avg >= 5 else "Needs more practice 📚")
        lines = [f"🏁 **Interview finished!** Average score: **{avg:.1f}/10** — {label}",
                 f"You answered {len(scores)} of {len(data['questions'])} questions."]
        common = [tip for tip, _ in Counter(data["tips"]).most_common(3)]
        if common:
            lines.append("**Your top focus areas:**")
            lines += [f"- {t}" for t in common]
        else:
            lines.append("Your answers were strong across the board. Great job!")
        lines.append("Practise again tomorrow — confidence grows with repetition.")
        return "\n".join(lines)

    @staticmethod
    def evaluate_answer(answer, qtype):
        """Score an interview answer 1-10 and return (score, strengths, improvements)."""
        lower = answer.lower().replace("’", "'")
        norm = normalize(answer)
        words = norm.split()
        n = len(words)
        score = 5.0
        good, improve = [], []

        # 1. length
        if n < 15:
            score -= 2
            improve.append("Your answer is very short. Aim for about 1–2 minutes (80–200 words) with a concrete example.")
        elif n < 40:
            score -= 0.5
            improve.append("Add more detail — a specific example would make it much stronger.")
        elif n <= 220:
            score += 1
            good.append("Good length: detailed but focused.")
        else:
            score -= 0.5
            improve.append("Quite long — keep answers focused (about 2 minutes spoken).")

        # 2. ownership
        i_count = words.count("i")
        we_count = words.count("we")
        if n >= 15 and i_count >= 2 and i_count >= we_count:
            score += 0.5
            good.append("You described your own actions (\"I ...\"), which shows ownership.")
        elif we_count > i_count:
            improve.append("Say \"I\" more than \"we\" so the interviewer knows what *you* did.")

        # 3. action verbs
        verbs = sorted({w for w in words if w in ACTION_VERBS})
        if verbs:
            score += min(1.5, 0.5 * len(verbs))
            good.append("Strong action verbs: " + ", ".join(verbs[:4]) + ".")
        else:
            improve.append("Use strong action verbs such as *led, built, organised, solved, improved*.")

        # 4. results / numbers
        has_number = bool(re.search(r"\d", answer)) or any(
            w in words for w in ("percent", "twice", "double", "half", "hundred", "thousand"))
        has_result = any(w in RESULT_WORDS for w in words)
        if has_number:
            score += 1
            good.append("You used numbers — measurable results are very convincing.")
        elif has_result:
            score += 0.5
            good.append("You mentioned a result or outcome.")
            improve.append("Quantify the result if you can (e.g. \"reduced errors by 20%\").")
        else:
            improve.append("Mention a clear result, ideally with numbers (e.g. \"served 50 customers a day\").")

        # 5. STAR structure for behavioural questions
        if qtype == "behavioral":
            has_situation = any(w in SITUATION_WORDS for w in words)
            if has_situation and (has_result or has_number) and verbs:
                score += 1
                good.append("Clear STAR structure: situation, action and result. ⭐")
            else:
                improve.append("Structure it with STAR: Situation → Task → Action → Result.")

        # 6. motivation question: company research
        if qtype == "company":
            if sum(1 for w in words if w in COMPANY_WORDS) >= 2:
                score += 1
                good.append("You connected your answer to the company — that shows research.")
            else:
                improve.append("Mention something specific about the company (its products, values or mission).")

        # 7. filler words
        fillers = sum(len(re.findall(p, lower)) for p in FILLER_PATTERNS)
        if fillers >= 3:
            score -= 1
            improve.append(f"Reduce filler words (um, like, basically) — I counted {fillers}. Pausing is fine!")

        # 8. negativity
        if any(re.search(p, lower) for p in NEGATIVE_PATTERNS):
            score -= 1
            improve.append("Avoid negative or unsure language (\"I hate\", \"I don't know\") — stay positive.")

        score = int(round(max(1, min(10, score))))
        return score, good, improve

    # ---------------- career quiz ----------------
    def _start_quiz(self, state):
        state["mode"] = "quiz"
        state["data"] = {"idx": 0, "scores": [0, 0, 0, 0]}
        return {"reply": "Let's find careers that fit you! 🧭 **4 quick questions** — answer A, B, C or D.\n\n"
                         + self._quiz_question(0),
                "quick_replies": ["A", "B", "C", "D"], "intent": "start_quiz"}

    @staticmethod
    def _quiz_question(i):
        q, opts = QUIZ[i]
        lines = [f"**Question {i + 1} of {len(QUIZ)}:** {q}"]
        lines += [f"- **{'ABCD'[j]}** – {o}" for j, o in enumerate(opts)]
        return "\n".join(lines)

    @staticmethod
    def _parse_choice(msg, options):
        words = normalize(msg).split()
        for w in reversed(words):  # "option b", "I choose c"
            if w in ORDINALS and (len(words) <= 3 or len(w) == 1 or w.isdigit()):
                return ORDINALS[w]
        # keyword overlap with option text (works for spoken answers)
        user = set(tokens(msg))
        best, best_hits = None, 0
        for j, o in enumerate(options):
            hits = len(user & set(tokens(o)))
            if hits > best_hits:
                best, best_hits = j, hits
        return best

    def _quiz_step(self, msg, state):
        data = state["data"]
        choice = self._parse_choice(msg, QUIZ[data["idx"]][1])
        if choice is None:
            return {"reply": "Please answer with **A, B, C or D** (or say **stop** to quit).\n\n"
                             + self._quiz_question(data["idx"]),
                    "quick_replies": ["A", "B", "C", "D"], "intent": "quiz_retry"}
        data["scores"][choice] += 1
        data["idx"] += 1
        if data["idx"] < len(QUIZ):
            return {"reply": "Got it! ✔️\n\n" + self._quiz_question(data["idx"]),
                    "quick_replies": ["A", "B", "C", "D"], "intent": "quiz_question"}

        scores = data["scores"]
        top = max(scores)
        winners = [QUIZ_CATS[i] for i, s in enumerate(scores) if s == top]
        state["mode"], state["data"] = None, {}
        lines = ["🎯 **Your career match results**"]
        for cat in winners:
            title, careers, step = QUIZ_RESULTS[cat]
            lines += [f"**{title}**", f"- Careers to explore: {careers}", f"- First step: {step}"]
        if len(winners) > 1:
            lines.append("You matched more than one area — roles that combine them (e.g. UX design, "
                         "health tech, marketing analytics) could be perfect for you.")
        lines.append("Want tips for this field or a mock interview?")
        quick = {"tech": "Careers in IT", "business": "Careers in business",
                 "people": "Careers in healthcare", "creative": "Creative careers"}
        return {"reply": "\n".join(lines),
                "quick_replies": [quick[c] for c in winners][:2] + ["Start a mock interview"],
                "intent": "quiz_result"}

    # ---------------- CV analyser ----------------
    def _cv_step(self, msg, state):
        if len(normalize(msg).split()) < 40:
            return {"reply": "That looks too short to be a full CV. Please **paste your whole CV text** "
                             "(at least a few sections), or say **cancel**.",
                    "quick_replies": ["Cancel"], "intent": "cv_retry"}
        state["mode"], state["data"] = None, {}
        return self._cv_report(msg)

    def _cv_report(self, text):
        score, good, improve = self.analyze_cv(text)
        label = ("Excellent 🌟" if score >= 85 else "Good 👍" if score >= 70 else
                 "Fair 🙂" if score >= 50 else "Needs work 🛠")
        lines = [f"**CV score: {score}/100** — {label}"]
        if good:
            lines.append("✅ **What's working**")
            lines += [f"- {g}" for g in good]
        if improve:
            lines.append("🛠 **What to improve**")
            lines += [f"- {i}" for i in improve]
        lines.append("Fix the top items, paste your CV again and see your score go up! 📈")
        return {"reply": "\n".join(lines), "quick_replies": ["Review my CV", "Action verbs", "Cover letter tips"],
                "intent": "cv_report"}

    @staticmethod
    def analyze_cv(text):
        """Return (score/100, strengths, improvements) for pasted CV text."""
        lower = text.lower()
        words = normalize(text).split()
        n = len(words)
        score = 0
        good, improve = [], []

        # contact details (10)
        has_email = bool(re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", text))
        has_phone = bool(re.search(r"(\+?\d[\d\s-]{7,}\d)", text))
        if has_email and has_phone:
            score += 10
            good.append("Contact details (email and phone) are included.")
        elif has_email or has_phone:
            score += 5
            improve.append("Add both a **phone number and a professional email**.")
        else:
            improve.append("Add your **contact details** (phone, professional email) at the top.")

        # sections (8 each = 40)
        missing = []
        for section, keys in CV_SECTIONS.items():
            if any(re.search(r"\b" + re.escape(k) + r"\b", lower) for k in keys):
                score += 8
            else:
                missing.append(section)
        if missing:
            improve.append("Missing sections: **" + ", ".join(missing) + "**.")
        else:
            good.append("All key sections are present (summary, education, experience, skills, projects).")

        # length (10)
        if 250 <= n <= 900:
            score += 10
            good.append(f"Good length ({n} words — about 1–2 pages).")
        elif n < 250:
            score += 4
            improve.append(f"Your CV is short ({n} words). Add more detail on projects, experience and results.")
        else:
            score += 5
            improve.append(f"Your CV is long ({n} words). Cut it to 1–2 pages and keep only relevant points.")

        # action verbs (15)
        verbs = sorted({w for w in words if w in ACTION_VERBS})
        if len(verbs) >= 6:
            score += 15
            good.append(f"Great use of action verbs ({', '.join(verbs[:5])}...).")
        elif verbs:
            score += 7
            improve.append("Start **more bullet points with action verbs** (led, built, improved, achieved).")
        else:
            improve.append("Start bullet points with **action verbs** (led, built, improved, achieved).")

        # measurable results (12)
        metrics = re.findall(r"\d+\s?%|\b\d{2,}\b|rm\s?\d+|\$\s?\d+", lower)
        metric_count = len([m for m in metrics if not re.fullmatch(r"(19|20)\d{2}", m.strip())])
        if metric_count >= 3:
            score += 12
            good.append("You quantify achievements with numbers — recruiters love this.")
        elif metric_count >= 1:
            score += 6
            improve.append("Add **more numbers**: team size, % improvement, number of users or customers.")
        else:
            improve.append("Add **measurable results** (e.g. \"increased sales by 15%\", \"led a team of 5\").")

        # no first-person pronouns (5)
        pronouns = sum(words.count(p) for p in ("i", "me", "my"))
        if pronouns <= 2:
            score += 5
        else:
            improve.append(f"Remove first-person words (\"I\", \"my\") — found {pronouns}. "
                           "Write \"Built a website\" instead of \"I built a website\".")

        # cliches (5)
        cliches = [c for c in CV_CLICHES if c in lower]
        if not cliches:
            score += 5
        else:
            improve.append("Replace clichés like **" + ", ".join(f'\"{c}\"' for c in cliches[:3]) +
                           "** with proof of what you achieved.")

        # online presence (3)
        if re.search(r"linkedin|github|portfolio|behance", lower):
            score += 3
            good.append("Online profile/portfolio link included.")
        else:
            improve.append("Add a **LinkedIn** (or GitHub/portfolio) link.")

        return min(100, score), good, improve
