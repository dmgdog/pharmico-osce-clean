########################################################################
#                          1. IMPORTS                                  #
########################################################################
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()

########################################################################
#                     2. GLOBAL CONSTANTS & SETUP                      #
########################################################################

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

DISCLAIMER = (
    "\n=======================================================\n"
    "                 IMPORTANT DISCLAIMER                  \n"
    "=======================================================\n"
    "This OSCE Chatbot is for EDUCATIONAL PRACTICE ONLY.     \n"
    "It is NOT a substitute for professional medical advice, \n"
    "clinical supervision, or official pharmacy guidelines. \n"
    "DO NOT use this tool for real patient care. Information \n"
    "provided by the AI is for simulation purposes only and \n"
    "may not be accurate, complete, or up-to-date.          \n"
    "Always refer to official sources (e.g., BNF, NIhiCE) and \n"
    "consult qualified professionals for medical guidance.   \n"
    "=======================================================\n" \
    ""
)
print(DISCLAIMER)

########################################################################
#                         3. HELPER FUNCTIONS                          #
########################################################################

def load_prompt(filename):
    
    file_path = os.path.join("prompts", filename)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Prompt file not found at {file_path}")

        return "Default instruction"
    
########################################################################
#                     4. MAIN APPLICATION LOGIC                        #
########################################################################
# --- Loading patient prompt ---
selected_topic = input("Input your topic: ")
system_instruction = load_prompt("patient_system_instruction.txt")+selected_topic
        

history = [
    types.Content(role="user", parts=[types.Part(text=system_instruction)])
]


print("Patient (Generating scenario...):")


# --- Creating the scenario ---
initial_response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents=history,
    config = types.GenerateContentConfig(
        temperature=0.8,
        max_output_tokens=300
        )
)


initial_bot_message = initial_response.text
print(f"Patient: {initial_bot_message}")
history.append(types.Content(role="model", parts=[types.Part(text=initial_bot_message)]))


consultation_concluded_by_patient = False 


while True:
    user_input = input("You: ").strip()

    if not user_input:
        print("Please type something to continue the consultation")
        continue
    if user_input.lower() == "quit":
        print("\n--- Pharmacist (You) ended the consultation. Application closing. ---") # This is for a direct quit
        break # Exit the loop, ending the application

    history.append(types.Content(role="user", parts=[types.Part(text=user_input)]))

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=history,
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=300
        )
    )

    reply = response.text

    # --- Check for secret keyword and process reply ---
    END_SIGNAL = '[END_CONSULTATION]'
    if END_SIGNAL in reply:
        reply = reply.replace(END_SIGNAL, '').strip()
        print("Patient:", reply) 
        history.append(types.Content(role="model", parts=[types.Part(text=reply)])) 
        print("\n--- Consultation concluded. Application closing. ---")
        consultation_concluded_by_patient = True 
        break # Exit the loop, terminating the application


    print("Patient:", reply) # If no end signal, print as normal

    history.append(types.Content(role="model", parts=[types.Part(text=reply)]))


########################################################################
#                    5. FEEDBACK GENERATION                            #
########################################################################

if consultation_concluded_by_patient == True: 

    print("\n--- Generating Feedback ---")

    feedback_prompt = load_prompt("feedback_prompt.txt")

    history.append(types.Content(role="user", parts=[types.Part(text=feedback_prompt)]))


    feedback_response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=history, 
        config=types.GenerateContentConfig(
            temperature=0.7,    
            max_output_tokens=1000 
        )
    )

    feedback_text = feedback_response.text

    if feedback_text:
        print("Bot (Feedback Text):", feedback_text)
    else:
        print("Bot (Feedback): Could not generate text feedback.")

    print("\n--- Feedback Ended ---")
