import os
import streamlit as st
from google import genai
from google.genai import types # Import types just in case client errors rely on it
from dotenv import load_dotenv

# --- 0. Streamlit Page Configuration ---
st.set_page_config(page_title="OSCE Chatbot Diagnostic", layout="centered")

# --- 1. Global Setup & Critical Diagnostics ---
st.header("App Initialization Diagnostics")

# Load environment variables
try:
    load_dotenv()
    st.success("STEP 1: Loaded .env file successfully.")
except Exception as e:
    st.error(f"ERROR: STEP 1: Failed to load .env file. Please ensure it exists and is correctly formatted.")
    st.exception(e) # Display full traceback
    st.stop() # Stop execution if .env loading fails

# API Key Check
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    st.error("ERROR: STEP 2: GEMINI_API_KEY not found. Please set it in your .env file or Streamlit secrets.")
    st.info("Ensure your .env file is in the same directory as app.py and contains GEMINI_API_KEY='your_key_here'.")
    st.stop() # Stop execution if API Key is missing
else:
    st.success("STEP 2: API Key found.")
    st.write(f"API Key starts with: `{API_KEY[:5]}...`")

# Gemini Client Initialization
try:
    client = genai.Client(api_key=API_KEY)
    st.success("STEP 3: Gemini Client initialized successfully.")

    # Try a very basic model access to confirm the client is genuinely working
    try:
        # Use a common, broadly available model name for this test
        test_model_info = client.models.get("gemini-2.0-flash") # Using gemini-2.0-flash as it's the one you use
        st.success(f"STEP 4: Successfully accessed Gemini model: `{test_model_info.name}`. API connection is good!")
    except Exception as e:
        st.error(f"ERROR: STEP 4: Client initialized, but failed to access a test model. This often means your API key is invalid, region-restricted, or has insufficient permissions for this model: {e}")
        st.exception(e) # Display full traceback
        st.stop() # Stop execution if model access fails

except Exception as e:
    st.error(f"ERROR: STEP 3: Failed to initialize Gemini Client. This could be due to a malformed API key, a network issue, or a very specific library version conflict: {e}")
    st.exception(e) # Display full traceback
    st.stop() # Stop execution if Client fails to initialize

# --- End of Critical Diagnostics ---

# Disclaimer (will only show if all steps above passed)
DISCLAIMER = (
    "**IMPORTANT DISCLAIMER:**\n"
    "This OSCE Chatbot is for **EDUCATIONAL PRACTICE ONLY**. It is NOT a substitute for "
    "professional medical advice, clinical supervision, or official pharmacy guidelines. "
    "DO NOT use this tool for real patient care. Information provided by the AI is for "
    "simulation purposes only and may not be accurate, complete, or up-to-date. "
    "Always refer to official sources (e.g., BNF, NICE) and consult qualified professionals "
    "for medical guidance."
)

st.warning(DISCLAIMER)

st.write("If you see this message and all the green 'STEP' messages above, your core setup (API key, client, model access) is working perfectly. The topic selection should then appear below this.")

# --- The rest of your app's main logic (main function, helper functions, etc.) would go here ---
# For now, we'll just put a placeholder for main() to keep this diagnostic minimal.
# When this diagnostic works, we will paste your full app.py code back in.

# Placeholder for SCENARIO_TOPICS (needed if main() is called)
SCENARIO_TOPICS = ["Placeholder Topic"] # Minimal list for this diagnostic

# Stub for main() function just so script runs
def main():
    st.write("DEBUG: Entered main() function - this means the main app logic will run next.")
    # In the actual app.py, the rest of your main function's code starts here
    # For now, we'll stop to keep it diagnostic:
    # st.stop() # Uncomment this if you want to stop here after diagnostics

if __name__ == "__main__":
    main()