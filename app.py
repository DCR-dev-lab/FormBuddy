import html
import os
import re
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import streamlit as st
from google import genai
from google.genai import types

from prompts import (
    LANGUAGES,
    SUMMARY_REQUEST_PROMPT,
    SYSTEM_PROMPT_TEMPLATE,
    WELCOME_MESSAGE_TEMPLATE,
)

MODEL_NAME = "gemini-3.8-flash"
st.set_page_config(
    page_title="FormBuddy",
    page_icon="📝",
    layout="wide",
)

# Load secrets
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")
SMTP_SERVER = st.secrets.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(st.secrets.get("SMTP_PORT", 587))
SMTP_EMAIL = st.secrets.get("SMTP_EMAIL", "")
SMTP_PASSWORD = st.secrets.get("SMTP_PASSWORD", "")

# Fail early with a clear message instead of crashing later
if not GEMINI_API_KEY:
    st.error("GEMINI_API_KEY is missing. Add it to .streamlit/secrets.toml (or the Secrets panel on Streamlit Cloud).")
    st.stop()

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
GENERIC_ERROR_PREFIX = "Sorry, something went wrong"


@st.cache_resource
def get_gemini_client():
    return genai.Client(api_key=GEMINI_API_KEY)


gemini_client = get_gemini_client()


def render_message(message):
    with st.chat_message(message["role"]):
        if message["kind"] == "text":
            st.markdown(message["content"])
        elif message["kind"] == "image":
            st.image(message["content"], caption="Uploaded Form", use_container_width=True)


def add_message(role, kind, content):
    st.session_state.messages.append({"role": role, "kind": kind, "content": content})
    render_message(st.session_state.messages[-1])


def ask_gemini(parts):
    try:
        response = st.session_state.chat.send_message(parts)
        # .text can be None if the reply was blocked or empty
        return response.text or f"{GENERIC_ERROR_PREFIX}: no answer came back. Try a clearer photo."
    except Exception as error:
        return f"{GENERIC_ERROR_PREFIX} while analyzing: {error}"


def format_summary_for_html(text):
    # Escape HTML characters to prevent breaking markup
    escaped = html.escape(text)
    # Convert **bold** markdown to <b> tags
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    # Convert [ ] checkboxes to HTML checkboxes
    escaped = escaped.replace("[ ]", "☐")
    # Convert newlines to HTML line breaks
    return escaped.replace("\n", "<br>")


def send_email(to_email, user_name, language, summary):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        return False, "Email credentials are not set in secrets.toml (SMTP_EMAIL and SMTP_PASSWORD)."

    to_email = to_email.strip()
    if not EMAIL_PATTERN.match(to_email):
        return False, "That email address doesn't look valid."

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"📝 Form Checklist & Guide - {user_name}"
        msg["From"] = SMTP_EMAIL
        msg["To"] = to_email

        formatted_summary = format_summary_for_html(summary)
        safe_name = html.escape(user_name)
        safe_language = html.escape(language)

        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: auto; padding: 20px;">
            <div style="background-color: #1a365d; color: white; padding: 15px; border-radius: 8px; text-align: center;">
                <h2>📝 FormBuddy</h2>
                <p>Simple Guide & Document Checklist</p>
            </div>
            <div style="padding: 20px; background-color: #f8f9fa; border-radius: 8px; margin-top: 15px;">
                <p><strong>Name:</strong> {safe_name}</p>
                <p><strong>Language:</strong> {safe_language}</p>
                <hr style="border: 0; height: 1px; background: #ddd;">
                <div style="font-size: 15px; line-height: 1.8;">{formatted_summary}</div>
            </div>
            <div style="text-align: center; color: #777; font-size: 12px; margin-top: 20px;">
                <p>💡 Always confirm with the local government office before final submission.</p>
            </div>
        </body>
        </html>
        """
        # Plain-text part first, HTML part last (clients show the last one they support)
        msg.attach(MIMEText(summary, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())

        return True, f"Checklist sent to {to_email}!"
    except Exception as error:
        return False, str(error)


# <-- Onboarding Screen -->

if "onboarded" not in st.session_state:
    st.markdown("<h1 style='text-align: center;'>📝 FormBuddy</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align: center; font-size: 18px;'>Confusing scholarship, ration card, or bank forms made simple — as if explained by a family elder.</p>",
        unsafe_allow_html=True,
    )
    st.divider()

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info(
            "🔒 **Please cover ID numbers (Aadhaar, PAN, bank account) before uploading.** "
            "We ask the AI not to repeat them, but photos are processed by Google Gemini."
        )

        with st.form("onboarding_form"):
            name = st.text_input("Your Name", placeholder="e.g. Ramesh Kumar / Ananya")

            language = st.selectbox(
                "Preferred Language for Explanation",
                options=LANGUAGES,
                index=0,
            )

            email_input = st.text_input(
                "Your Email Address (optional, to receive your checklist)",
                placeholder="name@example.com",
            )

            submitted = st.form_submit_button("Start FormBuddy 🚀", use_container_width=True)

        if submitted:
            if not name.strip():
                st.warning("Please enter your name to continue.")
            elif email_input.strip() and not EMAIL_PATTERN.match(email_input.strip()):
                st.warning("That email address doesn't look valid. Fix it or leave it empty.")
            else:
                st.session_state.name = name.strip()
                st.session_state.language = language
                st.session_state.email = email_input.strip()

                # Build system prompt with chosen language
                system_instruction = SYSTEM_PROMPT_TEMPLATE.format(language=language)

                st.session_state.chat = gemini_client.chats.create(
                    model=MODEL_NAME,
                    config=types.GenerateContentConfig(system_instruction=system_instruction),
                )
                # Start history with the welcome message so it is never skipped
                st.session_state.messages = [
                    {
                        "role": "assistant",
                        "kind": "text",
                        "content": WELCOME_MESSAGE_TEMPLATE.format(name=st.session_state.name),
                    }
                ]
                st.session_state.onboarded = True
                st.rerun()
    st.stop()


# <-- Main Application Interface -->

# Sidebar with User Info & Sample Form
with st.sidebar:
    st.header("👤 Your Profile")
    st.write(f"**Name:** {st.session_state.name}")
    st.write(f"**Language:** {st.session_state.language}")

    if st.session_state.get("email", "").strip():
        st.write(f"**Email:** ✉️ `{st.session_state.email}`")
    else:
        st.write("**Email:** ⚪ *Not added*")

    with st.expander("⚙️ Update Email"):
        edit_email = st.text_input("Email Address", value=st.session_state.get("email", ""), key="edit_email_input")
        if st.button("Save Email", key="btn_save_profile"):
            if edit_email.strip() and not EMAIL_PATTERN.match(edit_email.strip()):
                st.error("That email address doesn't look valid.")
            else:
                st.session_state.email = edit_email.strip()
                st.success("Updated!")
                st.rerun()

    st.info("🔒 Cover ID numbers before uploading. Photos are processed by Google Gemini.")

    st.divider()
    sample_path = os.path.join("samples", "sample_scholarship_form.png")
    if os.path.exists(sample_path):
        st.subheader("⚡ Quick Test")
        st.caption("No form photo right now? Test with our built-in sample scholarship form:")
        if st.button("📄 Try Sample Scholarship Form", use_container_width=True):
            with open(sample_path, "rb") as f:
                sample_bytes = f.read()
            add_message("user", "image", sample_bytes)
            parts = [
                types.Part.from_bytes(data=sample_bytes, mime_type="image/png"),
                (
                    "Please analyze this government/official form: "
                    "1. What is this form for (one simple line)? "
                    "2. Explain field-by-field in simple words as if explaining to an elder. "
                    "3. Warn about sections the applicant should NOT touch or sign (e.g. institution / office use only). "
                    "4. Give a checklist of required documents to attach. "
                    "5. Mention common mistakes to avoid."
                ),
            ]
            with st.spinner("🔍 Reading the sample form..."):
                answer = ask_gemini(parts)
            add_message("assistant", "text", answer)
            st.rerun()

    st.divider()
    st.subheader("💡 Photo Tips")
    st.markdown(
        """
        - Ensure good lighting with no glare.
        - Cover personal ID numbers (Aadhaar/PAN).
        - If blurry, snap another photo in brighter light.
        """
    )

    st.divider()
    if st.button("🔄 Start New Session / Change Language", use_container_width=True):
        st.session_state.clear()
        st.rerun()


# Top Header with Email Button
header_col, action_col = st.columns([5, 2], vertical_alignment="center")

with header_col:
    st.title("📝 FormBuddy")
    st.caption(f"Explaining for **{st.session_state.name}** in **{st.session_state.language}**")

# Messages: [welcome] + at least one question and answer
has_analyzed_form = len(st.session_state.messages) > 2
has_email = bool(st.session_state.get("email", "").strip())
email_disabled = not (has_analyzed_form and has_email)

if not has_email:
    email_help = "⚠️ Add your email in the sidebar (⚙️ Update Email) to enable."
elif not has_analyzed_form:
    email_help = "⚠️ Please analyze a form first before sending a checklist."
else:
    email_help = f"Send your document checklist to {st.session_state.email}."

with action_col:
    if st.button("📩 Send Checklist to Email", disabled=email_disabled, help=email_help, use_container_width=True):
        with st.spinner("Preparing checklist & sending email..."):
            summary = ask_gemini([SUMMARY_REQUEST_PROMPT])
            if summary.startswith(GENERIC_ERROR_PREFIX):
                st.error(summary)
            else:
                success, msg = send_email(
                    st.session_state.email,
                    st.session_state.name,
                    st.session_state.language,
                    summary,
                )
                if success:
                    st.session_state.last_summary = summary
                    st.success(f"Email sent! 📩 Check {st.session_state.email} (and your spam folder).")
                else:
                    st.error(f"Email error: {msg}")

# On-Screen Checklist Preview (if generated)
if st.session_state.get("last_summary"):
    with st.expander("📋 View Generated Action Checklist (Click to Expand)", expanded=True):
        st.markdown(st.session_state.last_summary)
        st.caption("Copy the plain text for WhatsApp, SMS, or Notes:")
        st.code(st.session_state.last_summary, language="text")

st.divider()

# Message History
for message in st.session_state.messages:
    render_message(message)

# Chat Input (Accepts text & photo uploads)
user_input = st.chat_input(
    "Ask a question, or attach a photo of your scholarship, ration card, or bank form...",
    accept_file=True,
    file_type=["jpg", "jpeg", "png", "webp"],
)

if user_input:
    photo = user_input.files[0] if user_input.files else None
    text = user_input.text
    parts = []

    if photo is not None:
        photo_bytes = photo.getvalue()
        add_message("user", "image", photo_bytes)
        parts.append(types.Part.from_bytes(data=photo_bytes, mime_type=photo.type))

    if text:
        add_message("user", "text", text)
        parts.append(text)
    elif photo is not None:
        parts.append(
            "Please analyze this form: "
            "1. What is this form for (one line)? "
            "2. Explain field-by-field in simple words as if explaining to an elder. "
            "3. Warn about sections the applicant must NOT fill or sign (e.g. office use only). "
            "4. Give a checklist of required documents to attach. "
            "5. Mention common mistakes that get forms rejected."
        )

    with st.spinner("🔍 Reading the form and preparing simple instructions..."):
        answer = ask_gemini(parts)

    add_message("assistant", "text", answer)
    st.rerun()
