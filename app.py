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

# --- CUSTOM CSS FOR MOBILE-FRIENDLY LOOK ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #c9d1d9; }
    /* Make buttons look like app buttons */
    .stButton>button { 
        background-color: #238636; 
        color: white; 
        border: none; 
        width: 100%; 
        padding: 10px;
        border-radius: 8px;
        font-weight: bold;
    }
    .job-card { 
        background-color: #161b22; 
        padding: 15px; 
        border-radius: 12px; 
        border: 1px solid #30363d; 
        margin-bottom: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .job-title { color: #58a6ff; font-weight: bold; font-size: 1.1em; }
    .job-found { color: #238636; font-weight: bold; }
    .no-match { color: #8b949e; font-style: italic; }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR: AUTO-LOGIN LOGIC ---
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Check if keys exist in Secrets (Cloud Storage)
    # This allows you to deploy without typing passwords every time
    default_api_key = st.secrets.get("AZURE_KEY", "")
    default_email_pass = st.secrets.get("EMAIL_PASS", "")
    
    # 1. API Keys Input
    api_key_input = st.text_input("GitHub/Azure API Key", value=default_api_key, type="password")
    
    st.divider()
    
    st.subheader("📧 Email Alerts")
    email_user = st.text_input("Your Gmail", value="gkranthikumar956@gmail.com")
    email_pass = st.text_input("Google App Password", value=default_email_pass, type="password")
    
    if api_key_input:
        st.session_state['api_key'] = api_key_input
    
    st.info("Mobile App Mode: Active v2.1")

# --- MAIN APP LOGIC ---

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are MyShadow, a loyal and strategic personal advisor for a student. Build confidence and provide career advice for a 2026 graduate. Be concise, inspiring, and practical."},
        {"role": "assistant", "content": "I am online. Systems nominal. Ready to assist."}
    ]

# TABS
tab1, tab2 = st.tabs(["💬 Chat", "🕵️ Scout"])

# ==========================================
# TAB 1: ADVISOR CHAT
# ==========================================
with tab1:
    st.title("🛡️ Advisor")
    
    # Display Chat
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("Type here..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        if 'api_key' in st.session_state and st.session_state['api_key']:
            try:
                client = ChatCompletionsClient(
                    endpoint="https://models.inference.ai.azure.com",
                    credential=AzureKeyCredential(st.session_state['api_key']),
                )
                
                with st.spinner("..."):
                    azure_msgs = []
                    for m in st.session_state.messages:
                        if m["role"] == "system": azure_msgs.append(SystemMessage(content=m["content"]))
                        elif m["role"] == "user": azure_msgs.append(UserMessage(content=m["content"]))

                    response = client.complete(
                        messages=azure_msgs,
                        model="gpt-4o",
                        temperature=0.7
                    )
                    reply = response.choices[0].message.content
                
                st.session_state.messages.append({"role": "assistant", "content": reply})
                with st.chat_message("assistant"):
                    st.markdown(reply)
            except Exception as e:
                st.error(f"Connection Error: {e}")
        else:
            st.warning("⚠️ key missing in sidebar")

# ==========================================
# TAB 2: JOB SCOUT
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
                    
                    page_text = soup.get_text(separator=' ', strip=True)[:7000]

                    prompt = f"""
                    Analyze text from {site['name']}. Look for 'Entry Level', 'Junior', 'Intern', '2026 Graduate'.
                    Output format: "FOUND: [Role/Video] | [Company/Channel] | [LINK]"
                    If no match: "NO_MATCH"
                    TEXT: {page_text}
                    """
                    
                    ai_resp = client.complete(messages=[UserMessage(content=prompt)], model="gpt-4o")
                    result = ai_resp.choices[0].message.content

                    if "FOUND:" in result:
                        clean_res = result.replace("FOUND:", "").strip()
                        found_jobs.append(clean_res)
                        results_container.markdown(f"<div class='job-card'><div class='job-title'>✅ {site['name']}</div>{clean_res}</div>", unsafe_allow_html=True)
                
                time.sleep(1)

            except Exception as e:
                st.error(f"Error: {e}")

        status_container.success("Patrol Complete.")
        st.session_state['scanning'] = False
        
        if found_jobs and email_user and email_pass:
            try:
                msg = MIMEMultipart()
                msg['From'] = email_user
                msg['To'] = email_user
                msg['Subject'] = f"🚀 MyShadow Report: {len(found_jobs)} New Matches"
                body = "<h2>Mission Report</h2><ul>" + "".join([f"<li>{j}</li>" for j in found_jobs]) + "</ul>"
                msg.attach(MIMEText(body, 'html'))
                server = smtplib.SMTP('smtp.gmail.com', 587)
                server.starttls()
                server.login(email_user, email_pass)
                server.send_message(msg)
                server.quit()
                st.toast("Email Sent!", icon="📧")
            except Exception:
                st.toast("Email Failed", icon="❌")