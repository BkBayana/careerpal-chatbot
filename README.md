# CareerPal – Career Assistant Chatbot (Flask Web App with Voice)

**Application area:** 4. Career Assistant Chatbot

## The real-world problem
Students and fresh graduates often have no one to practise interviews with, don't know why their CV gets
rejected, and are unsure which career fits them. Career counsellors are busy and only available in office
hours. **CareerPal** is available 24/7 in the browser: you can *talk* to it, practise a real mock interview
out loud, and get instant, scored feedback.

## Features
| Feature | What it does |
|---|---|
| 🎤 **Mock interview** | Asks 5 questions (general, motivation, role-specific, behavioural) for 4 job areas and **scores every answer out of 10**: length, "I"-ownership, action verbs, numbers/results, STAR structure, company research, filler words (um, like…), negative language. Ends with an average score and your top 3 focus areas. |
| 📄 **CV analyser** | Paste your CV → **score out of 100** with checks for contact details, 5 key sections, length, action verbs, measurable results, first-person pronouns, clichés and LinkedIn/GitHub link. |
| 🧭 **Career quiz** | 4 questions → matching career areas, example jobs and a first step. |
| 💡 **Knowledge base** | 30 intents: CV tips, action verbs, cover letters, interview prep, STAR method, "tell me about yourself", strengths/weaknesses, questions to ask, follow-up email, job search, internships, LinkedIn, salary negotiation, career change, in-demand skills, remote work, motivation after rejection, careers by field (IT, business, healthcare/education, creative, engineering). |
| 🎙 **Voice input** | Click the mic and speak (Web Speech API). Your speech appears live in the box and is sent automatically. |
| 🔊 **Voice output** | Every reply is read aloud (speechSynthesis). Choose the voice and speed; toggle auto-read; replay any message with "🔊 Listen". |
| 🧠 **Robust NLP** | Keyword + phrase scoring, light stemming and **fuzzy matching**, so typos and speech-recognition mistakes ("intervew tipps") still work. Per-user conversation state (sessions). |
| 📱 **Responsive UI** | Quick-reply buttons, feature shortcuts, typing indicator, dark mode, works on phones. |

## Project structure
```
careerpal/
├── app.py              # Flask web server + REST API (/api/chat, /api/welcome, /api/reset)
├── chatbot.py          # Chatbot engine: intents, NLP matching, interview/CV/quiz logic
├── templates/index.html
├── static/style.css
├── static/script.js    # Chat UI, voice input & voice output
├── demo_test.py        # Automated demo: 38 test messages through the Flask API
├── demo_transcript.md  # Output of the demo (full conversation)
├── screenshots/        # Screenshots of the running web app
└── requirements.txt
```

## How to run
```bash
pip install -r requirements.txt
python app.py
```
Open **http://127.0.0.1:5000** in **Google Chrome or Microsoft Edge** and allow microphone access.

> Voice input needs Chrome/Edge (Web Speech API) and works on `localhost` or HTTPS.
> Voice output works in all modern browsers. If voice is unavailable you can still type.

Run the automated demonstration:
```bash
python demo_test.py        # prints the conversation and writes demo_transcript.md
```

## How it works
1. The browser converts speech to text (`SpeechRecognition`) and sends it with `fetch()` to `POST /api/chat`.
2. Flask finds the user's conversation state (by session cookie) and calls `CareerBot.reply()`.
3. The bot either continues an active activity (interview / quiz / CV review) or classifies the intent and answers.
4. The JSON reply (`reply`, `quick_replies`, `intent`, `mode`) is rendered in the chat and read aloud with `speechSynthesis`.

## Demo script (for the presentation)
1. Say: *"Hello"* → *"What can you do?"*
2. Say: *"What is the STAR method?"* (voice reply is read aloud)
3. Click **Mock interview** → choose **Software / IT** → answer the questions **by voice**; show a good and a weak answer and compare the scores.
4. Click **CV review** and paste a CV → show the score and suggestions.
5. Click **Career quiz** → answer A/B/C/D → show the results.
6. Type with a typo: *"intervew tipps"* → still understood. Ask something off-topic → polite fallback.

## Possible improvements
- Upload a PDF/DOCX CV directly · store interview history per user · add Malay/other languages · connect an LLM API for free-form answers.
