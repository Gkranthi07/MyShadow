import streamlit as st
import requests
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="MyShadow", page_icon="🛡️", layout="wide")

# --- CUSTOM CSS FOR "NEAT & EFFECTIVE" UI ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    
    /* Global Button Style (Green Accent) */
    .stButton>button { 
        background-color: #238636; 
        color: white; 
        border: none; 
        padding: 10px;
        border-radius: 8px;
        font-weight: bold;
        transition: 0.2s;
    }
    .stButton>button:hover {
        background-color: #2ea043;
    }

    /* Chat Message Bubble Styling */
    .stChatMessage {
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 12px;
    }
    
    /* Job Card Styling */
    .job-card { 
        background-color: #161b22; 
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid #30363d; 
        margin-bottom: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .job-title { color: #58a6ff; font-weight: bold; font-size: 1.1em; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: SETTINGS ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    default_api_key = st.secrets.get("AZURE_KEY", "")
    default_email_pass = st.secrets.get("EMAIL_PASS", "")
    
    api_key_input = st.text_input("GitHub/Azure API Key", value=default_api_key, type="password")
    
    st.divider()
    
    st.subheader("📧 Email Alerts")
    email_user = st.text_input("Your Gmail", value="gkranthikumar956@gmail.com")
    email_pass = st.text_input("Google App Password", value=default_email_pass, type="password")
    
    if api_key_input:
        st.session_state['api_key'] = api_key_input
    
    st.info("System v2.3: Interface Upgrade")

# --- MAIN APP LOGIC ---

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are MyShadow, a loyal and strategic personal advisor for a student. Build confidence and provide career advice for a 2026 graduate. Be concise, inspiring, and practical."},
        {"role": "assistant", "content": "I am online. Systems nominal. Ready to assist."}
    ]

# TABS
tab1, tab2 = st.tabs(["💬 Advisor Chat", "🕵️ Job Scout"])

# ==========================================
# TAB 1: ADVISOR CHAT (Refined Framework)
# ==========================================
with tab1:
    # Header with Reset Action
    c1, c2 = st.columns([6, 1])
    with c1:
        st.title("🛡️ Advisor")
        st.caption("Your personal career strategist & confidence booster.")
    with c2:
        if st.button("🧹 Clear", help="Wipe memory and start fresh", use_container_width=True):
            st.session_state.messages = [
                {"role": "system", "content": "You are MyShadow..."},
                {"role": "assistant", "content": "Memory wiped. Ready for new instructions."}
            ]
            st.rerun()

    # 1. Render History
    for message in st.session_state.messages:
        if message["role"] != "system":
            # Distinct Avatars
            avatar = "👤" if message["role"] == "user" else "🛡️"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(message["content"])

    # 2. Suggestions (Only if chat is empty/short)
    if len(st.session_state.messages) < 3:
        st.markdown("#### 💡 Quick Actions")
        col_a, col_b, col_c = st.columns(3)
        if col_a.button("🚀 Boost my confidence"):
            st.session_state.messages.append({"role": "user", "content": "I'm feeling low and doubt my skills. Give me a confidence boost."})
            st.rerun()
        if col_b.button("📅 2026 Grad Plan"):
            st.session_state.messages.append({"role": "user", "content": "Create a roadmap for a 2026 graduate to get a job at a top tech company."})
            st.rerun()
        if col_c.button("📝 Resume Tips"):
            st.session_state.messages.append({"role": "user", "content": "What are the top 3 things I should have on my resume as a fresher?"})
            st.rerun()

    # 3. Chat Input
    prompt = st.chat_input("Ask for advice, motivation, or strategy...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.rerun()

    # 4. AI Response Logic (Triggers if last message was user)
    if st.session_state.messages[-1]["role"] == "user":
        if 'api_key' in st.session_state and st.session_state['api_key']:
            try:
                client = ChatCompletionsClient(
                    endpoint="https://models.inference.ai.azure.com",
                    credential=AzureKeyCredential(st.session_state['api_key']),
                )
                
                with st.chat_message("assistant", avatar="🛡️"):
                    with st.spinner("Analyzing..."):
                        azure_msgs = []
                        for m in st.session_state.messages:
                            if m["role"] == "system": azure_msgs.append(SystemMessage(content=m["content"]))
                            elif m["role"] == "user": azure_msgs.append(UserMessage(content=m["content"]))
                            elif m["role"] == "assistant": azure_msgs.append(UserMessage(content=m["content"])) # Azure SDK often treats history as User messages for simplicity in some models, but 'AssistantMessage' is proper. For this specific SDK, sticking to basic flow.

                        response = client.complete(
                            messages=azure_msgs,
                            model="gpt-4o",
                            temperature=0.7
                        )
                        reply = response.choices[0].message.content
                        st.markdown(reply)
                
                st.session_state.messages.append({"role": "assistant", "content": reply})
            
            except Exception as e:
                st.error(f"Connection Error: {e}")
        else:
            st.warning("⚠️ key missing in sidebar")


# ==========================================
# TAB 2: JOB SCOUT (Unchanged)
# ==========================================
with tab2:
    st.title("🕵️ Scout")
    
    if st.button("🚀 Start Patrol"):
        if 'api_key' not in st.session_state:
            st.error("Missing API Key!")
        else:
            st.session_state['scanning'] = True

    if st.session_state.get('scanning'):
        status_container = st.empty()
        results_container = st.container()

        target_sites = [
            {"name": "WeWorkRemotely", "url": "https://weworkremotely.com/categories/remote-back-end-programming-jobs"},
            {"name": "LinkedIn (India)", "url": "https://www.linkedin.com/jobs/search?keywords=software%20engineer%20intern&location=India&f_TPR=r86400&trk=public_jobs_jobs-search-bar_search-submit"},
            {"name": "YT: Off-Campus 2026", "url": "https://www.youtube.com/results?search_query=off-campus+hiring+for+2026+batch&sp=CAI%253D"},
            {"name": "YT: OnlineStudy4u", "url": "https://www.youtube.com/@OnlineStudy4u/videos"},
            {"name": "YT: KN ACADEMY", "url": "https://www.youtube.com/@KNACADEMY/videos"},
            {"name": "YT: Hire Me Plz", "url": "https://www.youtube.com/@HireMePlz/videos"},
            {"name": "YT: Online Learning", "url": "https://www.youtube.com/@OnlineLearning/videos"}
        ]

        client = ChatCompletionsClient(
            endpoint="https://models.inference.ai.azure.com",
            credential=AzureKeyCredential(st.session_state['api_key']),
        )

        found_jobs = []

        for site in target_sites:
            status_container.info(f"Scanning {site['name']}...")
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
                response = requests.get(site['url'], headers=headers, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        if a.get_text(strip=True):
                            a.replace_with(f"{a.get_text(strip=True)} ({a['href']})")
                    for tag in soup(["script", "style", "nav", "footer"]):
                        tag.decompose()
                    
                    page_text = soup.get_text(separator=' ', strip=True)[:25000]

                    prompt = f"""
                    Analyze text from {site['name']}. Look for 'Entry Level', 'Junior', 'Intern', '2026 Graduate'.
                    Output format: "FOUND: [Role/Video] | [Company/Channel] | [LINK]"
                    If no match: "NO_MATCH"
                    TEXT: {page_text}
                    """
                    
                    ai_resp = client.complete(messages=[UserMessage(content=prompt)], model="
