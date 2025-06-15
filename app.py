import os
import time
import random
import streamlit as st
from google import genai
from google.genai import types
from dotenv import load_dotenv

# --- 0. Streamlit Page Configuration ---
st.set_page_config(page_title="OSCE Chatbot", page_icon="⚕️")

# --- Main App Title and Subtitle ---
st.title("💊 OSCE Patient Simulator")
st.markdown("### by PharmicoLearn")
# --- END Main App Title and Subtitle ---

# --- 1. Global Constants & Setup ---
load_dotenv() # Load environment variables from .env file

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    st.error("ERROR: GEMINI_API_KEY not found. Please set it in your .env file or Streamlit secrets.")
    st.info("Ensure your .env file is in the same directory as app.py and contains GEMINI_API_KEY='your_key_here'.")
    st.stop()

try:
    client = genai.Client(api_key=API_KEY)
except Exception as e:
    st.error(f"ERROR: Failed to initialize Gemini Client. This could be due to a malformed API key or a network issue: {e}")
    st.exception(e) # Display full traceback
    st.stop()

DISCLAIMER = (
    "**IMPORTANT DISCLAIMER:**\n\n"
    "This OSCE Patient Simulator is for **EDUCATIONAL PRACTICE ONLY**. It is **NOT** a substitute for "
    "professional medical advice, clinical supervision, or official pharmacy guidelines.\n\n"
    "**DO NOT** use this tool for real patient care. Information provided by the AI is for "
    "simulation purposes only and may not be accurate, complete, or even fabricated (AI hallucination).\n\n"
    "Always refer to official sources (e.g., BNF, NICE) and consult qualified professionals "
    "for medical guidance."
)
st.warning(DISCLAIMER)

# --- NEW: App Description/Instructions ---
APP_DESCRIPTION = """
Welcome to your **Pharmacy OSCE Patient Simulator (by PharmicoLearn)**!

This is your personal virtual patient simulator designed specifically for pharmacy students. It's built to help you practice and refine your consultation skills in a safe, simulated environment, preparing you for Objective Structured Clinical Examinations (OSCEs) and real-world practice as an independent prescriber.

---

### How It Works:

1.  **Choose Your Scenario:** Use the **dropdown menu** below to select a specific minor ailment topic (e.g., Respiratory, Pain Management, Dermatology). You can also pick **"Random (select from list)"** for a surprise challenge.
2.  **Start the Consultation:** Click the **"Start Consultation"** button. The AI will immediately present a brief case overview (patient name, age, and reason for visit).
3.  **Be the Pharmacist:** Once the case overview appears, **you** are the pharmacist. Introduce yourself and begin asking the patient (the AI) questions.
4.  **Interact Naturally:** Type your questions and responses into the **input box** at the bottom. The AI will respond as the patient, providing details only when you ask specific questions.
5.  **Conclude & Get Feedback:**
    * The patient (AI) might signal the end of the consultation with a natural closing remark followed by `[END_CONSULTATION]`.
    * Alternatively, you can type **`quit`** into the input box at any time to end the session.
    * Once the consultation ends, you'll immediately receive **concise, actionable feedback** on your performance, including an ideal pathway, strengths, and areas for improvement, assessed from the perspective of an independent prescribing pharmacist.
6.  **Start a New Case:** After receiving feedback, click the **"Start New Consultation"** button to reset the app and begin another practice scenario.

---

"""
# --- END NEW: App Description/Instructions ---


GEMINI_MODEL = "gemini-2.0-flash"

SCENARIO_TOPICS = [
    "Random (select from list)", # Selects a random topic from the list below
    "Respiratory (e.g., cough, cold, flu, asthma)",
    "Dermatological (e.g., skin rash, eczema, fungal infection)",
    "Gastrointestinal (e.g., indigestion, constipation, diarrhea, nausea)",
    "Pain Management (e.g., headache, back pain, minor sprain)",
    "Eye/Ear/Nose/Throat (e.g., sore throat, earache, conjunctivitis)",
    "General Wellbeing (e.g., fatigue, sleep issues, mild anxiety)",
    "Medication Queries (e.g., side effects, missed dose, interaction check)",
    "Paediatric (minor ailments in children, from a parent's perspective)",
    "Women's Health (e.g., period pain, minor thrush, contraception advice)"
]

# --- 2. Helper Functions ---

#@st.cache_data
def load_prompt(filename: str) -> str:
    """
    Reads a text file from the 'prompts' directory and returns its content.
    Provides a default instruction if the file is not found.
    """
    file_path = os.path.join("prompts", filename)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        st.error(f"Error: Prompt file not found at '{file_path}'. Please ensure the 'prompts' folder and file exist.")
        return "You are a helpful assistant. Please respond to user queries."

def generate_content_with_retry(gemini_client_models,
                                model_name: str,
                                contents_to_send: list,
                                config: types.GenerateContentConfig,
                                max_retries: int = 5,
                                initial_delay: int = 1):
    """
    Sends content to the Gemini model with retry logic for temporary API issues.
    Incorporates Streamlit's spinner for better UX.
    Returns the full GenerateContentResponse object.
    """
    delay = initial_delay
    for i in range(max_retries):
        try:
            with st.spinner("Thinking..."):
                response = gemini_client_models.generate_content(
                    model=model_name,
                    contents=contents_to_send,
                    config=config
                )
            return response
        except Exception as e:
            error_message = str(e).lower()
            if "overloaded" in error_message or "503" in error_message or "unavailable" in error_message or "resource_exhausted" in error_message:
                st.warning(f"Model busy/overloaded. Retrying in {delay:.2f} seconds... Error: {e}")
                time.sleep(delay + random.uniform(0, 0.5))
                delay *= 2
            else:
                st.error(f"An unexpected API error occurred: {e}")
                st.exception(e) # Display full traceback
                raise
    raise Exception(f"Failed after {max_retries} retries due to persistent model unavailability.")

# --- Function to Reset App State (called by button's on_click) ---
def reset_app_state_and_rerun():
    st.session_state.clear()
    st.rerun()

# --- 3. Main Streamlit Application Logic ---
def main():
    # The title and subtitle are in the global scope.

    # --- NEW: Display App Description ---
    st.markdown(APP_DESCRIPTION)
    # --- END NEW ---

    # Initialize essential session state variables
    if "consultation_begun" not in st.session_state:
        st.session_state.consultation_begun = False
    if "scenario_generated" not in st.session_state:
        st.session_state.scenario_generated = False
    if "history" not in st.session_state:
        st.session_state.history = []
    if "initial_scenario_message" not in st.session_state:
        st.session_state.initial_scenario_message = ""
    if "consultation_concluded_by_patient" not in st.session_state:
        st.session_state.consultation_concluded_by_patient = False
    if "feedback_generated" not in st.session_state:
        st.session_state.feedback_generated = False
    if "selected_topic" not in st.session_state:
        st.session_state.selected_topic = None


    # --- Topic Selection and Start Consultation Button (Conditional Display) ---
    if not st.session_state.consultation_begun:
        st.subheader("Choose a Scenario Topic:")
        
        selected_option = st.selectbox(
            "Select a topic for your consultation:",
            options=SCENARIO_TOPICS,
            index=0, # Default to the first option ("Random (select from list)")
            key="topic_selector"
        )
        st.session_state.selected_topic = selected_option # Update state immediately on selectbox change

        if st.button("Start Consultation", key="start_consultation_button"):
            st.session_state.consultation_begun = True
            st.rerun() # Forces a rerun, now consultation_begun will be True
    else: # This 'else' block runs once consultation_begun is True
        # --- Initializing History and Generating Scenario (Conditional Display) ---
        if not st.session_state.scenario_generated:
            base_patient_instruction = load_prompt("patient_system_instruction.txt")
            
            # --- MODIFIED: Conditional prompt formatting based on topic selection ---
            final_topic_instruction = ""
            if st.session_state.selected_topic == "Random (select from list)":
                # Select a random topic from the list, excluding the "Random" option itself
                available_topics_for_random = [t for t in SCENARIO_TOPICS if t != "Random (select from list)"]
                if available_topics_for_random:
                    chosen_random_topic = random.choice(available_topics_for_random)
                    final_topic_instruction = "\n\nYour specific ailment for this consultation will be related to: " + chosen_random_topic
                else:
                    # Fallback if somehow the list only contained "Random"
                    final_topic_instruction = "\n\nYour specific ailment for this consultation will be a general minor ailment."
            else:
                # For specific topics, append the chosen topic.
                final_topic_instruction = "\n\nYour specific ailment for this consultation will be related to: " + st.session_state.selected_topic
            
            formatted_instruction = base_patient_instruction + final_topic_instruction
            # --- END MODIFIED ---

            st.session_state.history = [
                types.Content(role="user", parts=[types.Part(text=formatted_instruction)])
            ]

            st.info("Patient (Generating scenario... Please wait)")
            try:
                initial_call_config = types.GenerateContentConfig(
                    temperature=0.8,
                    max_output_tokens=300
                )
                initial_response = client.models.generate_content(
                    model=GEMINI_MODEL,
                    contents=st.session_state.history,
                    config=initial_call_config
                )
                initial_bot_message = initial_response.text
                st.session_state.history.append(types.Content(role="model", parts=[types.Part(text=initial_bot_message)]))
                st.session_state.initial_scenario_message = initial_bot_message
                st.session_state.scenario_generated = True
                st.rerun() # Rerun to display the generated scenario
            except Exception as e:
                st.error(f"Failed to generate initial scenario: {e}")
                st.exception(e) # Display full traceback
                st.stop()
        
        # --- Display Chat History ---
        if st.session_state.scenario_generated and st.session_state.initial_scenario_message:
            with st.chat_message("assistant", avatar="👤"): # Bot's initial message
                st.markdown(st.session_state.initial_scenario_message)

        for i, message in enumerate(st.session_state.history[2:]):
            if message.role == "user":
                with st.chat_message("user", avatar="🧑‍⚕️"): # User messages
                    st.markdown(message.parts[0].text)
            else: # Must be "model" role
                with st.chat_message("assistant", avatar="👤"): # Bot messages
                    st.markdown(message.parts[0].text)

        # --- Interactive Chat Input ---
        if not st.session_state.consultation_concluded_by_patient and not st.session_state.feedback_generated:
            user_input = st.chat_input("Your turn (type 'quit' to end consultation):")

            if user_input:
                if user_input.lower() == "quit":
                    if len(st.session_state.history) <= 2: # System prompt + initial bot message
                        st.warning("Consultation ended early without significant interaction. No feedback generated.")
                        reset_app_state_and_rerun() # Reset immediately for new consultation
                        st.stop()
                    else:
                        st.session_state.consultation_concluded_by_patient = True
                        st.session_state.history.append(types.Content(role="user", parts=[types.Part(text="[CONSULTATION ENDED BY USER]")]))
                        st.success("--- Pharmacist (You) ended the consultation. Generating feedback... ---")
                        st.rerun()
                else:
                    st.session_state.history.append(types.Content(role="user", parts=[types.Part(text=user_input)]))
                    with st.chat_message("user", avatar="🧑‍⚕️"): # User's own input
                        st.markdown(user_input)

                    chat_config = types.GenerateContentConfig(
                        temperature=0.2,
                        max_output_tokens=300
                    )
                    try:
                        response = client.models.generate_content(
                            model=GEMINI_MODEL,
                            contents=st.session_state.history,
                            config=chat_config
                        )
                        reply = response.text

                        END_SIGNAL = '[END_CONSULTATION]'
                        if END_SIGNAL in reply:
                            reply = reply.replace(END_SIGNAL, '').strip()
                            st.session_state.consultation_concluded_by_patient = True
                            st.session_state.history.append(types.Content(role="model", parts=[types.Part(text=reply)]))
                            with st.chat_message("assistant", avatar="👤"): # Bot's final message before feedback
                                st.markdown(reply)
                            st.success("--- Consultation concluded by patient. Generating feedback... ---")
                            st.rerun()
                        else:
                            st.session_state.history.append(types.Content(role="model", parts=[types.Part(text=reply)]))
                            with st.chat_message("assistant", avatar="👤"): # Bot's regular message
                                st.markdown(reply)
                    except Exception as e:
                        st.error(f"Error generating patient response: {e}")
                        st.exception(e) # Display full traceback


        # --- Feedback Generation ---
        if st.session_state.consultation_concluded_by_patient and not st.session_state.feedback_generated:
            st.divider()
            st.subheader("📝 Feedback on your Consultation")

            feedback_prompt_content = load_prompt("feedback_prompt.txt")

            feedback_history = list(st.session_state.history)
            feedback_history.append(types.Content(role="user", parts=[types.Part(text=feedback_prompt_content)]))

            feedback_config = types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=1000
            )
            try:
                feedback_response = generate_content_with_retry(
                    gemini_client_models=client.models,
                    model_name=GEMINI_MODEL,
                    contents_to_send=feedback_history,
                    config=feedback_config
                )
                feedback_text = feedback_response.text

                if feedback_text:
                    st.markdown(feedback_text)
                else:
                    st.warning("Could not generate text feedback.")
                st.session_state.feedback_generated = True
            except Exception as e:
                st.error(f"Error generating feedback: {e}")
                st.exception(e) # Display full traceback

            st.button(
                "Start New Consultation",
                on_click=reset_app_state_and_rerun,
                key="reset_button_feedback_section"
            )

if __name__ == "__main__":
    main()