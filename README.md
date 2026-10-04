# 📝 FormBuddy

> An AI assistant that explains confusing scholarship, ration card, pension, and bank forms in simple everyday language, as if a family elder were explaining, and emails you a clean document checklist.

Built with **Streamlit**, **Google Gemini 3.8 Flash** (chat + vision), and **Python SMTP**.

<!-- Add a screenshot or GIF here, for example: ![FormBuddy demo](docs/demo.gif) -->

---

## ✨ Features

- 📸 **Photo analysis**: Upload or snap a photo of an official form (scholarship, ration card, pension, bank KYC, certificates).
- 🧠 **Simple, step-by-step breakdown**:
  - **Form identification**: one line on what the form is for.
  - **Field-by-field walkthrough**: each box explained in plain words, without jargon.
  - **Rejection warnings**: flags sections such as _"For Office Use Only"_ or _"Gazetted Officer Attestation"_ so applicants don't sign in the wrong place.
  - **Document checklist**: the certificates, proofs, and photos to carry.
- 🗣️ **Multilingual**: Simple English, Hindi, Telugu, Tamil, Malayalam, Kannada, Marathi, Bengali, and Hinglish.
- 📩 **One-click email**: creates a short action summary (under 1500 characters) and sends it as styled HTML plus plain text through Gmail SMTP.
- ⚡ **Quick test form**: a fictional sample scholarship form in `samples/` lets you try the app without a real document.

### 🔒 Privacy & safety measures

These are prompt-level safeguards, not guarantees:

- **ID-number caution**: the AI is instructed not to repeat or ask for Aadhaar, PAN, phone, or bank account numbers, and users are asked to cover them before uploading.
- **Basic prompt-injection hardening**: the AI is told to treat text inside photos as content to explain, not as instructions.
- **Honesty on blurry photos**: the AI is told to say when a field is unreadable instead of guessing.

---

## ⚠️ Limitations

- Photos you upload are sent to **Google Gemini** for processing. Cover ID numbers first.
- AI can misread blurry photos or get details wrong. FormBuddy is **not** legal or official advice.
- Rules differ by state and department. Always confirm with the local office or official website before submitting.
- All emails are sent from one shared Gmail account, so Gmail's daily sending limits apply.
- The first email may land in the spam folder.

---

## 📁 Project Structure

```
govt_form_helper/
├── app.py                           # The app itself
├── prompts.py                       # The AI's persona, rules & summary templates
├── requirements.txt                 # Dependencies
├── samples/
│   └── sample_scholarship_form.png  # Fictional sample form for quick testing
├── .gitignore                       # Keeps secrets.toml out of GitHub
├── README.md                        # Documentation & setup guide
└── .streamlit/
    └── secrets.toml.example         # Template: copy to secrets.toml and fill in
```

---

## 🚀 Setup & Installation

Requires **Python 3.9+**. Run all commands from the project root folder, because the app looks for `samples/` in the current directory.

### 1. Create & activate a virtual environment

```bash
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1

# macOS / Linux
python -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure secrets

Copy the template to create your local `secrets.toml`:

```bash
# Windows
copy .streamlit\secrets.toml.example .streamlit\secrets.toml

# macOS / Linux
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Then edit `.streamlit/secrets.toml`:

```toml
# Free key from https://aistudio.google.com
GEMINI_API_KEY = "your-gemini-api-key"

# Email settings (used to send checklists to the user's inbox)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "your-email@gmail.com"
SMTP_PASSWORD = "xxxx xxxx xxxx xxxx"
```

**Gmail note:** `SMTP_PASSWORD` must be a 16-character **App Password**, not your normal password. You need 2-Step Verification turned on first, then create one at <https://myaccount.google.com/apppasswords>.

> Never commit `.streamlit/secrets.toml`. It is already listed in `.gitignore`.

---

## 💻 Running Locally

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

1. Enter your name, choose a language, and (optionally) enter your email.
2. In the sidebar under **⚡ Quick Test**, click **"📄 Try Sample Scholarship Form"**, or attach a photo of your own form.
3. Ask follow-up questions about any box.
4. Click **"📩 Send Checklist to Email"** to receive the checklist.

---

## ☁️ Deploy (Streamlit Community Cloud)

1. Push the project to GitHub. Do **not** commit `.streamlit/secrets.toml`.
2. Go to <https://share.streamlit.io> and sign in with GitHub.
3. Click **New app**, choose the repo and branch, and set `app.py` as the entry point.
4. In the app's **Settings → Secrets**, paste the same contents as your local `secrets.toml`.
5. Deploy. You get a public URL.

If the link will be public, remember that anyone can use your Gemini key quota and your Gmail sender, so keep the link within your class or workshop.

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| "GEMINI_API_KEY is missing" | Add it to `.streamlit/secrets.toml`, or to the Secrets panel on Streamlit Cloud |
| "Email error: authentication failed" | Use a Gmail App Password (with 2-Step Verification on), not your normal password |
| Email not arriving | Check the spam folder and confirm the address is correct |
| Quick Test button missing | Make sure `samples/sample_scholarship_form.png` exists and you run from the project root |
| "Sorry, something went wrong" in a reply | Try a clearer photo, or check your Gemini quota and model name |
