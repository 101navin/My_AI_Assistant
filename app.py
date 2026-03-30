import streamlit as st
import requests
import os
import json
import speech_recognition as sr
from dotenv import load_dotenv
import streamlit.components.v1 as components

# Load API key
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Page config
st.set_page_config(
    page_title="Smart AI Assistant",
    page_icon="🤖",
    layout="wide"
)

# Modern CSS Styling with Stop Button Support
st.markdown("""
<style>
    body { background-color: #0E1117; }
    h1 { text-align: center; color: #00FFAA; font-family: 'sans-serif'; }
    .stChatMessage { border-radius: 10px; padding: 8px; animation: fadeIn 0.5s; }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    .history-item { 
        padding: 5px 10px; 
        margin: 5px 0; 
        background: #1E293B; 
        border-radius: 5px; 
        font-size: 0.8rem; 
        color: #00FFAA;
        border-left: 2px solid #00FFAA;
    }
</style>
""", unsafe_allow_html=True)

# --- Logic Functions ---

def save_chat():
    # Saves to chat_history.json in the current folder
    with open("chat_history.json", "w") as f:
        json.dump(st.session_state.messages, f, indent=4)

def stop_all():
    """Stops browser speech and clears current interaction"""
    stop_js = """
    <script>
    window.speechSynthesis.cancel();
    </script>
    """
    components.html(stop_js, height=0)
    st.session_state.stop_requested = True

def speak_text(text):
    """Triggers browser TTS"""
    safe_text = text.replace('"', '\\"').replace('\n', ' ')
    js_code = f"""
    <script>
    window.speechSynthesis.cancel(); // Clear previous queue
    var msg = new SpeechSynthesisUtterance("{safe_text}");
    window.speechSynthesis.speak(msg);
    </script>
    """
    components.html(js_code, height=0)

def ask_ai(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    data = {
        "model": "llama-3.1-8b-instant",
        "messages": st.session_state.messages + [{"role": "user", "content": prompt}],
        "temperature": 0.7
    }
    try:
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        return result["choices"][0]["message"]["content"] if "choices" in result else "Error: " + str(result)
    except Exception as e:
        return str(e)

# --- State Management ---
if "messages" not in st.session_state:
    if os.path.exists("chat_history.json"):
        with open("chat_history.json", "r") as f:
            st.session_state.messages = json.load(f)
    else:
        st.session_state.messages = []

if "stop_requested" not in st.session_state:
    st.session_state.stop_requested = False

# --- UI Layout ---
st.markdown("<h1>🤖 Smart AI Assistant</h1>", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("⚙️ Controls")
if st.sidebar.button("🛑 STOP RESPONSE", use_container_width=True, type="primary"):
    stop_all()
    st.rerun()

if st.sidebar.button("🎤 Voice Input", use_container_width=True):
    st.session_state.stop_requested = False
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.sidebar.info("Listening...")
        try:
            audio = recognizer.listen(source, timeout=5)
            voice_text = recognizer.recognize_google(audio)
            
            if voice_text:
                st.session_state.messages.append({"role": "user", "content": voice_text})
                ai_reply = ask_ai(voice_text)
                st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                
                # Only speak because this was a voice chat
                speak_text(ai_reply)
                save_chat()
                st.rerun()
        except:
            st.sidebar.error("Could not hear you.")

if st.sidebar.button("🧹 Clear Chat", use_container_width=True):
    st.session_state.messages = []
    save_chat()
    st.rerun()

# Sidebar History View
st.sidebar.markdown("---")
st.sidebar.subheader("📜 Your History")
for msg in reversed(st.session_state.messages):
    if msg["role"] == "user":
        st.sidebar.markdown(f'<div class="history-item">{msg["content"][:30]}...</div>', unsafe_allow_html=True)

# --- Main Chat ---
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

user_input = st.chat_input("Ask anything...", key="main_chat_input")

if user_input:
    st.session_state.stop_requested = False
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    with st.chat_message("user"):
        st.write(user_input)

    ai_reply = ask_ai(user_input)
    
    # Check if user hit stop during generation
    if not st.session_state.stop_requested:
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        with st.chat_message("assistant"):
            st.write(ai_reply)
        # Note: No speak_text() here because this is a text chat
        save_chat()