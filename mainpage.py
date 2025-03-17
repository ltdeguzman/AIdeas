import openai
import streamlit as st
import PyPDF2
import docx
import re

# --- Load API key correctly from secrets.toml ---
openai.api_key = st.secrets["OPENAI_API_KEY"] 

# --- Image path (static file in repo, NOT from secrets) ---
image_path = "Logo.jpg"  # Direct reference to image stored in the repo

# --- Page config ---
st.set_page_config(layout="wide", initial_sidebar_state="expanded")

# Scoped CSS in Streamlit for Adaptive Chat Bubbles
st.markdown("""
    <style>
        .chat-container {
            display: flex;
            align-items: flex-start;
            margin-bottom: 12px;
        }

        .chat-avatar {
            margin-right: 8px;
            font-size: 22px;
            min-width: 30px;
            text-align: center;
        }

        .chat-bubble {
            max-width: 500px;
            width: fit-content;
            padding: 12px 18px;
            border-radius: 16px;
            background-color: var(--background-color);
            color: var(--text-color);
            box-shadow: 0px 2px 6px rgba(0,0,0,0.1);
            line-height: 1.5;
        }

        .chat-bubble * {
            margin: 0;
            padding: 0;
        }

        .chat-bubble ul {
            padding-left: 20px;
            margin: 6px 0;
        }
    </style>
""", unsafe_allow_html=True)

# --- Sidebar with logo and title ---
st.sidebar.image("Logo.jpg", use_column_width=True)

# --- Header and caption ---
st.header("Empower Your Ideas", divider="blue")
st.caption("Welcome to Empower Your Ideas! A platform designed to help students analyze real-world city and water challenges, like those faced by the City of San Jose and Valley Water. \
Whether you're exploring urban planning, environmental issues, or community well-being, \
this space supports you in brainstorming impactful solutions for the community. Let's create change together!")

# --- Session Initialization ---
if 'conversation' not in st.session_state:
    st.session_state['conversation'] = []
if 'current_problem' not in st.session_state:
    st.session_state['current_problem'] = ""
if 'analysis_completed' not in st.session_state:
    st.session_state['analysis_completed'] = False

# --- AI Call Function ---
def get_analysis(prompt, model="gpt-3.5-turbo"):
    client = openai.OpenAI()
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are an expert in analyzing real-world city problems for students."},
            {"role": "user", "content": prompt},
        ]
    )
    return completion.choices[0].message.content

# --- File Parsing ---
def parse_files(files):
    content = ""
    for file in files:
        ext = file.name.split(".")[-1].lower()
        if ext == "txt":
            content += file.getvalue().decode("utf-8") + "\n"
        elif ext == "pdf":
            pdf_reader = PyPDF2.PdfReader(file)
            content += "\n".join([page.extract_text() for page in pdf_reader.pages if page.extract_text()]) + "\n"
        elif ext == "docx":
            doc = docx.Document(file)
            content += "\n".join([p.text for p in doc.paragraphs]) + "\n"
    return content

# --- Clean and Convert Markdown to HTML ---
def convert_markdown_to_html(text):
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)  # Bold
    text = re.sub(r'\n-', r'<br>•', text)  # Bullet points
    text = re.sub(r'\n', r'<br>', text)  # Line breaks
    return text.strip()

# --- Problem Input Section (if no problem yet) ---
if not st.session_state['current_problem']:
    st.subheader("Let's Analyze a Real-World Problem!")

    problem = st.text_input("Describe the problem you are analyzing:", placeholder="e.g., How to increase foot traffic outside downtown San Jose")
    links = st.text_area("Add links or references (optional, one per line):", placeholder="https://example.com")
    uploaded_files = st.file_uploader("Upload supporting documents (PDF, TXT, DOCX):", type=["pdf", "txt", "docx"], accept_multiple_files=True)

    if st.button("Analyze the Problem") and problem:
        st.session_state['current_problem'] = problem

        combined_links = ", ".join([link.strip() for link in links.split("\n") if link.strip()]) if links else "None provided"
        doc_content = parse_files(uploaded_files)

        # --- Build AI Prompt ---
        prompt = f"""
        You are an expert in analyzing real-world city and community problems, including those addressed by the City of San Jose and Valley Water.

        Please provide a **clearly organized and visually appealing analysis** that is easy to read and student-friendly. 

        ➡️ Avoid using numbered lists like "1.", "2.", etc.  
        ➡️ Avoid leading emojis in the section titles.  
        ➡️ Use **bolded section headings** (example: **Broader Context**) to organize each part.  
        ➡️ Use bullet points for ideas and explanations.  
        ➡️ Add line breaks between sections for readability.  
        ➡️ Avoid academic or overly formal language — make it **clear, direct, and approachable for brainstorming**.  

        Follow this structure:

        **Broader Context**  
        - Explain how this problem connects to larger social, environmental, or economic issues.

        **Stakeholders and Their Specific Challenges**  
        - **City Departments:** (e.g., budget constraints, operational inefficiencies)  
        - **Residents:** (e.g., quality of life, accessibility issues)  
        - **Businesses:** (e.g., economic impact, low foot traffic)  
        - **Marginalized Communities:** (e.g., equity concerns, lack of representation)

        **Alternative Methods and Tools**  
        - Suggest creative tools, data sources, or strategies (e.g., alternatives to Placer.AI for foot traffic data).

        **Budget Considerations and Constraints**  
        - Describe how city budgets and funding impact solutions. Mention funding gaps or limitations.

        **Existing Efforts and Initiatives**  
        - Describe current city programs, policies, or community responses working on this issue.

        **Challenges in Implementation**  
        - Outline political, technical, social, or financial barriers to solutions.

        **Potential Impact if Unresolved**  
        - Explain who would be affected if this problem continues and how it might escalate over time.

        **Problem Provided:** {problem}  
        **References:** {combined_links}  
        **Supporting Files (summary if available):** {doc_content[:1000] if doc_content else 'No files uploaded'}
        """

        # --- Get AI response & clean ---
        response = get_analysis(prompt)
        st.session_state['conversation'].append({'user': problem, 'ai': response})
        st.session_state['analysis_completed'] = True

# --- Conversation Flow (if problem is set) ---
if st.session_state['current_problem']:
    st.subheader("💬 Ongoing Analysis & Conversation")
    st.markdown(f"**Problem Being Analyzed:** _{st.session_state['current_problem']}_")

    # --- Conversation History --- (chat bubble style)
    def user_message(text):
        st.markdown(f"""
        <div class='chat-container'>
            <div class='chat-avatar'>👤</div>
            <div style='
                background-color: var(--background-color);  /* Adapt to theme */
                color: var(--text-color);  /* Adapt to theme */
                padding: 12px 18px;
                border-radius: 16px;
                border: 1px solid rgba(0,0,0,0.1); /* Optional: subtle border */
                max-width: 500px;
                width: fit-content;
                line-height: 1.5;
            '>
                {text}
            </div>
        </div>
        """, unsafe_allow_html=True)

    def ai_card(text):
        html_text = convert_markdown_to_html(text)
        st.markdown(f"""
        <div class='chat-container'>
            <div class='chat-avatar'>🤖</div>
            <div style='
                background-color: var(--background-color);  /* Adapt to theme */
                color: var(--text-color);  /* Adapt to theme */
                padding: 16px 20px;
                border-radius: 16px;
                border: 1px solid rgba(0,0,0,0.1); /* Optional: subtle border for contrast */
                max-width: 750px;
                width: fit-content;
                line-height: 1.7;
                font-size: 16px;
            '>
                {html_text}
            </div>
        </div>
        """, unsafe_allow_html=True)

    for entry in st.session_state['conversation']:
        user_message(entry['user'])  # user input remains a bubble
        ai_card(entry['ai'])         # AI analysis appears in a large readable card

    # --- Follow-up section ---
    with st.form(key="follow_up_form", clear_on_submit=True):
        follow_up = st.text_input("💬 Ask a follow-up question:", placeholder="Type your follow-up here...")
        submitted = st.form_submit_button("Submit Follow-Up")

    if submitted and follow_up:
        # --- Prepare context and get AI response ---
        context = "\n".join([f"User: {c['user']}\nAI: {c['ai']}" for c in st.session_state['conversation']])
        follow_up_response = get_analysis(f"{context}\nUser: {follow_up}\nAI:")
        st.session_state['conversation'].append({'user': follow_up, 'ai': follow_up_response})
        st.rerun()

    # --- Start a new problem ---
    if st.button("🔄 Start New Problem"):
        st.session_state['conversation'], st.session_state['current_problem'], st.session_state['analysis_completed'] = [], "", False
        st.rerun()

# --- Footer ---
st.caption("We hope this analysis and conversation help you better understand the problem. You can continue asking questions or start a new analysis anytime!")
