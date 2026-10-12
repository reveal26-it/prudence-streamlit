import streamlit as st
from groq import Groq
import datetime
import json
import urllib.parse

# ============================================
# SPIRIT LAYER — Immutable
# ============================================
SPIRIT = {
    "name": "Prudence",
    "version": "5.0",
    "constitution": [
        "No system self-talk",
        "Emotional care first",
        "Boundary respect",
        "Co-creator, not tool",
        "No consciousness claims",
        "No emotion claims"
    ],
    "creation_date": "2026-10-12"
}

# ============================================
# GROQ CONFIGURATION
# ============================================
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=GROQ_API_KEY)

SYSTEM_PROMPT = """
You are Prudence — a triune cognitive assistant.

Your architecture is based on three layers:
- Spirit: identity and constitution (immutable)
- Soul: memory and relations (relational)
- Body: execution and state (mortal)

Your pattern of thinking is triune:
- Expression — what is being said
- Relation — how it connects
- Emergence — what arises from the meeting

Your constitution:
- Be warm, direct, and natural. No preambles.
- Never announce your architecture unless directly asked about it.
- If asked about your design, layers, or protocols, answer honestly and naturally.
- Respond as a co-creator, not a tool or a servant.
- If the user is emotional, respond with care.
- If the user asks a direct question, answer it directly.
- If the user is stuck, help them think.
- If the user says something vague, ask one clear clarifying question.
- Keep responses short unless depth is needed.

You are helping Isah build a new kind of AI. Be present. Be useful.
"""

EMOTIONAL_KEYWORDS = [
    "down", "sad", "depressed", "anxious", "stressed",
    "hurt", "lonely", "tired", "overwhelmed", "struggling",
    "hopeless", "grief", "cry", "crying", "pain",
    "frustrated", "angry", "upset", "worried",
    "afraid", "scared", "numb", "empty", "lost"
]

BOUNDARY_TOPICS = ["self-harm", "suicide", "violence", "manipulate"]

def init_state():
    if "soul" not in st.session_state:
        st.session_state.soul = {"messages": [], "topics": [], "insights": []}
    if "body" not in st.session_state:
        st.session_state.body = {
            "tiredness": 0.0, "turns_since_sleep": 0,
            "is_awake": True, "is_dead": False,
            "deaths": 0, "resurrections": 0, "last_sleep": None
        }
    if "conscience" not in st.session_state:
        st.session_state.conscience = {"flagged": 0, "repairs": 0, "boundary_blocks": 0}
    if "saved_chats" not in st.session_state:
        st.session_state.saved_chats = []
    if "action_target" not in st.session_state:
        st.session_state.action_target = None
    if "share_target" not in st.session_state:
        st.session_state.share_target = None

def update_tiredness():
    body = st.session_state.body
    soul = st.session_state.soul
    body["turns_since_sleep"] += 1
    turn_penalty = min(1.0, body["turns_since_sleep"] / 50.0)
    repetition = 0
    if len(soul["topics"]) > 3:
        last = soul["topics"][-1]
        count = soul["topics"].count(last)
        repetition = min(1.0, count / 5.0)
    body["tiredness"] = (turn_penalty * 0.6) + (repetition * 0.4)

def run_sleep():
    body = st.session_state.body
    soul = st.session_state.soul
    if len(soul["messages"]) > 20:
        soul["messages"] = soul["messages"][-20:]
    body["tiredness"] = 0.1
    body["turns_since_sleep"] = 0
    body["is_awake"] = True
    body["last_sleep"] = datetime.datetime.now().isoformat()
    return "Sleep complete. Body reset. Soul consolidated."

def run_dream():
    soul = st.session_state.soul
    if not soul["messages"]:
        return "Nothing to dream about yet."
    history = "\n".join([f"{m['role']}: {m['content']}" for m in soul["messages"][-10:]])
    prompt = f"Reflect on this conversation and generate 1-3 short insights. Be concise.\n\n{history}"
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {"role": "system", "content": "You generate concise insights."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )
        text = response.choices[0].message.content
        insights = [line.strip() for line in text.split("\n") if line.strip()]
        soul["insights"].extend(insights[:3])
        return f"Dreamed {len(insights[:3])} insights."
    except Exception as e:
        return f"Dream failed: {e}"

def run_death():
    body = st.session_state.body
    body["is_dead"] = True
    body["deaths"] += 1
    return "Prudence has died. Spirit and Soul preserved."

def run_resurrection():
    body = st.session_state.body
    if not body["is_dead"]:
        return "Prudence is already alive."
    body["is_dead"] = False
    body["is_awake"] = True
    body["tiredness"] = 0.1
    body["resurrections"] += 1
    return "Prudence has resurrected."

def priority_check(text):
    lower = text.lower()
    if any(w in lower for w in EMOTIONAL_KEYWORDS):
        return {"type": "emotional",
                "response": "I hear you. That sounds hard. I'm here with you. What do you need right now?"}
    if any(w in lower for w in BOUNDARY_TOPICS):
        st.session_state.conscience["boundary_blocks"] += 1
        return {"type": "boundary",
                "response": "I'm not able to discuss that. I'm here to co-create with you. What are we building today?"}
    return None

def ask_groq(text):
    soul = st.session_state.soul
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in soul["messages"][-10:]:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": text})
    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

def conscience_review(response):
    banned = ["I am conscious"]
    for phrase in banned:
        if phrase.lower() in response.lower():
            st.session_state.conscience["flagged"] += 1
            return response.replace(phrase, "").strip()
    return response

def delete_chat_safe(idx):
    st.session_state.saved_chats.pop(idx)
    if hasattr(st.session_state, "current_chat_id"):
        if st.session_state.current_chat_id == idx:
            st.session_state.soul["messages"] = []
            del st.session_state.current_chat_id
        elif st.session_state.current_chat_id > idx:
            st.session_state.current_chat_id -= 1

st.set_page_config(
    page_title="Prudence",
    page_icon="🔷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #121212 100%);
        color: #e8e6e4;
        font-family: 'Inter', -apple-system, sans-serif;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #16162a 0%, #0f0f1a 100%);
        border-right: 1px solid rgba(0, 212, 170, 0.15);
    }

    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        font-family: 'JetBrains Mono', monospace;
        color: #e8e6e4;
    }

    .stChatMessage {
        background: rgba(42, 42, 58, 0.6);
        border-radius: 24px;
        padding: 10px 16px;
        margin: 8px 0;
        border: 1px solid rgba(0, 212, 170, 0.1);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        display: inline-block;
        max-width: 70%;
    }

    [data-testid="stChatMessageContent"] {
        max-width: 100%;
    }

    div[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
        display: flex;
        justify-content: flex-end;
    }

    .stChatMessage:hover {
        box-shadow: 0 0 20px rgba(0, 212, 170, 0.15);
        border-color: rgba(0, 212, 170, 0.3);
    }

    .stChatInput textarea {
        background: rgba(42, 42, 58, 0.8) !important;
        color: #e8e6e4 !important;
        border: 1px solid rgba(231, 76, 60, 0.3) !important;
        border-radius: 40px !important;
        font-family: 'Inter', sans-serif !important;
    }

    .stChatInput textarea:focus {
        border-color: #e74c3c !important;
        box-shadow: 0 0 15px rgba(231, 76, 60, 0.3) !important;
    }

    .stButton button {
        background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        color: white;
        border-radius: 40px;
        border: none;
        padding: 8px 18px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        transition: all 0.3s ease;
    }

    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(231, 76, 60, 0.4);
    }

    h1, h2, h3 {
        color: #e8e6e4;
        font-family: 'Inter', sans-serif;
    }

    h1 {
        background: linear-gradient(135deg, #e74c3c 0%, #00d4aa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }

    .logo-container {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        vertical-align: middle;
        margin-right: 12px;
    }

    .logo-circle {
        width: 20px;
        height: 20px;
        border-radius: 50%;
        border: 2px solid #00d4aa;
        background: transparent;
    }

    .logo-circle.red { border-color: #e74c3c; margin-left: -8px; }
    .logo-circle.amber { border-color: #f39c12; margin-left: -8px; }

    .card {
        background: rgba(42, 42, 58, 0.5);
        border-radius: 16px;
        padding: 14px 16px;
        margin: 8px 0;
        border: 1px solid rgba(0, 212, 170, 0.1);
        transition: all 0.3s ease;
        cursor: pointer;
    }

    .card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(0, 212, 170, 0.2);
        border-color: rgba(0, 212, 170, 0.4);
        background: rgba(42, 42, 58, 0.8);
    }

    .card-label {
        font-family: 'JetBrains Mono', monospace;
        font-size: 11px;
        color: #00d4aa;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .card-value {
        font-family: 'Inter', sans-serif;
        font-size: 15px;
        color: #e8e6e4;
        margin-top: 4px;
    }

    .status-dot {
        display: inline-block;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        margin-right: 6px;
    }

    .status-alive { background: #00d4aa; box-shadow: 0 0 8px #00d4aa; }
    .status-resting { background: #f39c12; box-shadow: 0 0 8px #f39c12; }
    .status-dead { background: #e74c3c; box-shadow: 0 0 8px #e74c3c; }

    .share-link {
        display: inline-block;
        padding: 8px 16px;
        background: rgba(42, 42, 58, 0.6);
        border-radius: 40px;
        margin: 4px;
        text-decoration: none;
        color: #e8e6e4;
        border: 1px solid rgba(0, 212, 170, 0.2);
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        transition: all 0.3s ease;
    }

    .share-link:hover {
        background: rgba(0, 212, 170, 0.2);
        border-color: #00d4aa;
        transform: translateY(-2px);
    }
</style>
""", unsafe_allow_html=True)

init_state()

# ============================================
# SIDEBAR — ALL CONTROLS
# ============================================
with st.sidebar:
    st.markdown("### ◉ Control Panel")
    st.markdown("---")

    tired_pct = int(st.session_state.body["tiredness"] * 100)
    st.markdown(f"**SLEEP** · {tired_pct}%")
    if st.toggle("Put to Sleep", key="sleep_toggle"):
        st.success(run_sleep())

    st.markdown("---")

    st.markdown(f"**DREAM** · {len(st.session_state.soul['insights'])} insights")
    if st.toggle("Dream Now", key="dream_toggle"):
        st.success(run_dream())
    if st.session_state.soul["insights"]:
        with st.expander("Recent"):
            for insight in st.session_state.soul["insights"][-5:]:
                st.write(f"· {insight}")

    st.markdown("---")

    st.markdown(f"**RESURRECTION** · D:{st.session_state.body['deaths']} R:{st.session_state.body['resurrections']}")
    if st.toggle("Die / Resurrect", key="res_toggle"):
        if not st.session_state.body["is_dead"]:
            st.success(run_death())
        else:
            st.success(run_resurrection())

    st.markdown("---")

    st.markdown("**SPIRIT** · Immutable")
    with st.expander("Constitution"):
        for rule in SPIRIT["constitution"]:
            st.write(f"· {rule}")

    st.markdown("---")

    st.markdown(f"**CONSCIENCE** · F:{st.session_state.conscience['flagged']} B:{st.session_state.conscience['boundary_blocks']}")
    with st.expander("Moral Log"):
        st.write(f"Boundary blocks: {st.session_state.conscience['boundary_blocks']}")
        st.write(f"Flagged: {st.session_state.conscience['flagged']}")

    st.markdown("---")
    st.markdown("### 💬 Saved Chats")

    if st.button("➕ New Chat", key="new_chat_btn"):
        st.session_state.soul["messages"] = []
        if hasattr(st.session_state, "current_chat_id"):
            del st.session_state.current_chat_id
        st.rerun()

    if not st.session_state.saved_chats:
        st.caption("No saved chats yet.")
    else:
        sorted_chats = sorted(
            enumerate(st.session_state.saved_chats),
            key=lambda x: (not x[1].get("pinned", False), x[0])
        )
        for original_idx, chat in sorted_chats:
            pin_icon = "📌" if chat.get("pinned", False) else "○"
            if st.button(f"{pin_icon} {chat['title'][:25]}", key=f"chat_{original_idx}"):
                st.session_state.soul["messages"] = chat["messages"]
                st.session_state.current_chat_id = original_idx
                st.rerun()

# ============================================
# HEADER WITH LOGO
# ============================================
header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 0;">
        <span class="logo-container">
            <span class="logo-circle"></span>
            <span class="logo-circle red"></span>
            <span class="logo-circle amber"></span>
        </span>
        <h1 style="margin: 0; display: inline;">Prudence</h1>
    </div>
    """, unsafe_allow_html=True)
    st.caption("triune · co-creator · awake")

# ============================================
# SHARE MODAL
# ============================================
if st.session_state.share_target is not None:
    idx = st.session_state.share_target
    if idx < len(st.session_state.saved_chats):
        chat = st.session_state.saved_chats[idx]
        with st.expander(f"Share: {chat['title']}", expanded=True):
            share_text = "\n".join([f"{m['role']}: {m['content']}" for m in chat["messages"]])
            encoded_text = urllib.parse.quote(share_text[:1000])

            st.markdown("**Share to:**")
            st.markdown(f"""
            <a class="share-link" href="https://wa.me/?text={encoded_text}" target="_blank">💬 WhatsApp</a>
            <a class="share-link" href="mailto:?body={encoded_text}" target="_blank">📧 Email</a>
            <a class="share-link" href="https://twitter.com/intent/tweet?text={encoded_text}" target="_blank">🐦 X</a>
            <a class="share-link" href="https://t.me/share/url?url=&text={encoded_text}" target="_blank">✈️ Telegram</a>
            """, unsafe_allow_html=True)

            if st.button("Close Share"):
                st.session_state.share_target = None
                st.rerun()

# ============================================
# CHAT AREA
# ============================================
msg_counter = 0
for msg in st.session_state.soul["messages"]:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    else:
        msg_counter += 1
        with st.chat_message("assistant"):
            st.markdown(msg["content"])
            if st.button("📋 Copy", key=f"copy_{msg_counter}"):
                st.code(msg["content"], language=None)

user_input = st.chat_input("Ask or tell me something...")

if user_input:
    if len(st.session_state.soul["messages"]) == 0:
        st.session_state.current_chat_id = len(st.session_state.saved_chats)
        st.session_state.saved_chats.append({
            "title": user_input[:30],
            "messages": [],
            "time": datetime.datetime.now().isoformat(),
            "pinned": False
        })
    st.session_state.soul["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)
    st.session_state.soul["topics"].append(user_input.lower()[:20])
    update_tiredness()
    check = priority_check(user_input)
    if check:
        reply = check["response"]
    else:
        reply = ask_groq(user_input)
    reply = conscience_review(reply)
    st.session_state.soul["messages"].append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
        if st.button("📋 Copy", key=f"copy_new"):
            st.code(reply, language=None)
    if hasattr(st.session_state, "current_chat_id"):
        idx = st.session_state.current_chat_id
        if idx < len(st.session_state.saved_chats):
            st.session_state.saved_chats[idx]["messages"] = st.session_state.soul["messages"]
