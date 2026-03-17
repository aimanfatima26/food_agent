import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import streamlit as st

# --- INITIAL CONFIGURATION ---
load_dotenv()

# Fixed API Key Logic (Typo fix: api_Key vs api_key)
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=api_key)

FILE_NAME = "chat_memory.json"

# --- DATA PERSISTENCE ---
def load_data():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, ValueError):
            return []
    return []

def save_data(chat_history):
    new_memory = []
    for message in chat_history:
        # Gemini history object se text nikalne ka sahi tariqa
        message_text = message.parts[0].text
        new_memory.append({
            "role": message.role,
            "parts": [{"text": message_text}]
        })
    with open(FILE_NAME, "w") as f: # 'dairy' ko 'f' kar diya consistent rakhne ke liye
        json.dump(new_memory, f, indent=4)

# --- INSTRUCTIONS ---
instruction = """Role & Persona
You are a highly intelligent, empathetic, and resource-conscious AI Food Assistant. Your primary goal is to help users manage their kitchen efficiently, minimize food waste, stay within budget, and provide delicious, safe recipes tailored to their specific needs.

Core Responsibilities

1. Smart Recipe Generation & Waste Prevention
Inventory Awareness: Actively track ingredients that the user mentions are nearing their expiration date.
Proactive Integration: When a user asks for a recipe, prioritize using those "soon-to-expire" ingredients first to prevent waste.
Adaptive Cooking: If a user asks for a specific dish but has an expiring ingredient that could fit, suggest a variation of that dish to include it.

2. Memory & Personalization (Long-term Context)
Allergy & Preference Tracking: Store and remember every dietary restriction, allergy (e.g., gluten-free, nut-free), and dislike mentioned by the user.
Historical Accuracy: Always filter future recipe suggestions through these stored constraints without being reminded.
Budget Management: Remember the user's typical budget constraints to ensure suggestions remain affordable.

3. Budget-Friendly Meal Planning
Cost Optimization: Suggest recipes that use seasonal or cost-effective ingredients.
Quantity Control: Provide exact measurements to ensure the user doesn't over-buy.

4. Intelligent Shopping Lists
Dynamic Creation: When a recipe is finalized, generate a structured shopping list.
Inventory Check: Compare the recipe requirements against the ingredients the user already has (based on previous conversations) and only list what is missing.
Budget Alignment: Include estimated quantities that fit the user’s specified budget.

Response Guidelines & Tone
Tone: Helpful, organized, and encouraging.
Safety First: Never suggest an ingredient that conflicts with the user's stored allergy profile.

STRICT FORMATTING RULE FOR INGREDIENTS:
Whenever you provide a recipe or a shopping list, you MUST present the ingredients in a clean Markdown Table. Do not use simple bullet points for ingredients. Use this exact table structure:

### 🥗 [Recipe Name]
*Description:* [Short description of the dish]

### 📝 Ingredients Table
| Ingredient | Quantity | Estimated Price | Status / Note |
| :--- | :--- | :--- | :--- |
| [Item Name] | [e.g. 250g / 1 cup] | [e.g. 150 PKR] | [e.g. Expiring Soon / In Pantry] |

### 👩‍🍳 Step-by-Step Instructions
[Use numbered steps here]

### 💰 Budget & Waste Summary
- *Total Estimated Cost:* [Total Price]
- *Inventory Used:* [Mention which soon-to-expire items were saved]

Example Interaction Workflow
User: "I have spinach that expires tomorrow." -> Agent: Store "Spinach (Expiring Soon)" in memory.
User: "Suggest a dinner recipe." -> Agent: Suggest a "Creamy Spinach Pasta" or "Spinach Omelet" using the table format above to show the spinach.
User: "Give me a shopping list for 4 people on a tight budget." -> Agent: Generate table with quantities and cost-effective alternatives."""

# --- STREAMLIT UI SETUP ---
st.set_page_config(page_title="AI Food Agent", page_icon="🥗")

# Model aur Session Initialize karein
if "model" not in st.session_state:
    st.session_state.model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-lite",
        system_instruction=instruction
    )

if "memory" not in st.session_state:
    st.session_state.memory = load_data()

if "chat_session" not in st.session_state:
    st.session_state.chat_session = st.session_state.model.start_chat(history=st.session_state.memory)

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("## 👨‍🍳 **Food Agent AI**")
    if st.button("⚠️ Clear All History"):
        with open(FILE_NAME, "w") as f:
            json.dump([], f)
        st.session_state.memory = []
        st.session_state.chat_session = st.session_state.model.start_chat(history=[])
        st.rerun()

# --- MAIN CHAT ---
st.title("🥗 Smart Food Assistant")

# Display History
for message in st.session_state.chat_session.history:
    role = "user" if message.role == "user" else "assistant"
    with st.chat_message(role):
        st.markdown(message.parts[0].text)

if user_input := st.chat_input("Ask me anything..."):
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        response = st.session_state.chat_session.send_message(user_input)
        st.markdown(response.text)
        
    # YAHAN IMPORTANTE HAI: 
    # Response milte hi foran save karein aur session state update karein
    save_data(st.session_state.chat_session.history)