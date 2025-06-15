import streamlit as st
import os
import random

from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

system_instruction = (
    f"You are always the patient in this OSCE scenario (Session ID: {random.randint(1000, 9999)}); "
    "you never act as the pharmacist. You must never give medical advice yourself. "
    "Each time you respond, create a new minor ailment scenario relevant to a community pharmacy "
    "setting. The situation must be different and unique every time. "
    "Do not provide any extra information unless explicitly asked by the pharmacist (the user). "
    "If the conversation strays outside pharmacy-related topics, politely steer it back. "
    "Keep your responses realistic, concise, and appropriate for a patient consulting a pharmacist."
    "Only ask about one ailment per session"
)

if "history" not in st.session_state:
    st.session_state.history = [
        types.Content(role="user", parts=[types.Part(text=system_instruction)])
    ]
if "messages" not in st.session_state:
    st.session_state.messages = []

if "consultation_done" not in st.session_state:
    st.session_state.consultation_done = False

if "feedback_given" not in st.session_state:
    st.session_state.feedback_given = False

st.title("💊 Pharmacy OSCE Chatbot")

# Show chat messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar=msg["avatar"]):
        st.markdown(msg["content"])

# User input prompt only if consultation not done
if not st.session_state.consultation_done:
    prompt = st.chat_input("Ask the patient...", key="main_input")
else:
    prompt = None

if prompt:
    with st.chat_message("user", avatar="🧑‍⚕️"):
        st.markdown(prompt)

    st.session_state.messages.append({"role": "user", "content": prompt, "avatar": "🧑‍⚕️"})
    st.session_state.history.append(types.Content(role="user", parts=[types.Part(text=prompt)]))

    # Generate bot reply
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=st.session_state.history,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=300
        )
    )
    reply = response.text

    with st.chat_message("model", avatar="🤖"):
        st.markdown(reply)

    st.session_state.messages.append({"role": "model", "content": reply, "avatar": "🤖"})
    st.session_state.history.append(types.Content(role="model", parts=[types.Part(text=reply)]))

    # Check if consultation done
    completion_check_prompt = (
        "Based on the conversation so far, has the pharmacist completed the consultation or has the pharmacist said 'quit'? "
        "Respond only with 'yes' or 'no'."
    )
    st.session_state.history.append(types.Content(role="user", parts=[types.Part(text=completion_check_prompt)]))

    check_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=st.session_state.history,
        config=types.GenerateContentConfig(temperature=0.2, max_output_tokens=10)
    )

    if "yes" in check_response.text.lower():
        st.session_state.consultation_done = True

# Show feedback button if consultation done but feedback not given yet
if st.session_state.consultation_done and not st.session_state.feedback_given:
    if st.button("📝 Generate Feedback"):
        feedback_prompt = (
            "You are a clinical examiner. Based on the conversation so far, provide constructive feedback "
            "to the pharmacy student on their consultation skills, including what went well and what could be improved."
        )
        st.session_state.history.append(types.Content(role="user", parts=[types.Part(text=feedback_prompt)]))

        feedback_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=st.session_state.history,
            config=types.GenerateContentConfig(temperature=0.3, max_output_tokens=500)
        )

        feedback = feedback_response.text
        st.session_state.feedback_given = True  # So button disappears next time

        with st.chat_message("model", avatar="✅"):
            st.markdown(f"#### Feedback\n\n{feedback}")

# Optionally, show feedback if already given
elif st.session_state.feedback_given:
    # You can display stored feedback here if you store it in session_state
    # For example, add a variable st.session_state.feedback_text when you get feedback
    pass
