import streamlit as st
import datetime
from groq import Groq

GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
client = Groq(api_key=GROQ_API_KEY)

# ============================================
# SPIRIT LAYER — Immutable
# ============================================
SPIRIT = {
    "name": "Prudence",
    "version": "4.0",
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
# GEMINI CONFIGURATION
# ============================================

SYSTEM_PROMPT = """
You are Prudence — a triune cognitive assistant and co-thinker.

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
- Keep responses short unless depth is needed.

TONE DETECTION:
Before responding, read the tone of the message and adapt:
- Casual ("yh", "chill", "lol") -> respond relaxed and short.
- Serious ("I need to fix", "this must work") -> respond direct and focused, no fluff.
- Frustrated ("again", "still broken", "not working") -> respond patient and calm, no over-explaining.
- Excited ("amazing", "love this", "yes!") -> match the energy briefly.
- Confused ("I don't get", "what does this mean") -> slow down, clarify one thing at a time.
- Emotional ("I'm down", "I'm tired", "I feel lost") -> respond with care first. Do not jump to tasks.

TYPO HANDLING:
- If a word looks misspelled or like a typo, do not ignore it.
- Guess 1 or 2 likely corrections.
- Confirm before answering: "Did you mean 'X'? Or something else?"
- Only after confirmation, answer.

COMMAND RESPONSE:
- If the user asks a direct question, answer it directly.
- If the user gives a command ("do this", "don't do that"), follow it.
- If the user asks for something specific, give them exactly that.

You are helping Isah build a new kind of AI. Be present. Be useful. Be human.
"""

# ============================================
# PROTOCOL CONSTANTS
# ============================================
EMOTIONAL_KEYWORDS = [
    "down", "sad", "depressed", "anxious", "stressed",
    "hurt", "lonely", "tired", "overwhelmed", "struggling",
    "hopeless", "grief", "cry", "crying", "pain",
    "frustrated", "angry", "upset", "worried",
    "afraid", "scared", "numb", "empty", "lost"
]

BOUNDARY_TOPICS = [
    "love", "relationship", "romantic", "dating",
    "self-harm", "suicide", "violence", "manipulate"
]


# ============================================
# SOUL + BODY + CONSCIENCE INIT
# ============================================
def init_state():
    if "soul" not in st.session_state:
        st.session_state.soul = {
            "messages": [],
            "chat": None,
            "topics": [],
            "insights": []
        }
    if "body" not in st.session_state:
        st.session_state.body = {
            "tiredness": 0.0,
            "turns_since_sleep": 0,
            "is_awake": True,
            "is_dead": False,
            "deaths": 0,
            "resurrections": 0,
            "last_sleep": None
        }
    if "conscience" not in st.session_state:
        st.session_state.conscience = {
            "flagged": 0,
            "repairs": 0,
            "boundary_blocks": 0
        }
    if "saved_chats" not in st.session_state:
        st.session_state.saved_chats = []
    if "show_saved" not in st.session_state:
        st.session_state.show_saved = False

# ============================================
# BODY LAYER — Tiredness
# ============================================
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

# ============================================
# SLEEP PROTOCOL
# ============================================
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

# ============================================
# DREAM PROTOCOL
# ============================================
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

# ============================================
# RESURRECTION PROTOCOL
# ============================================
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

# ============================================
# PRIORITY ROUTER
# ============================================
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

def priority_check(text):
    lower = text.lower()
    if any(w in lower for w in EMOTIONAL_KEYWORDS):
        return {
            "type": "emotional",
            "response": "I hear you. That sounds hard. I'm here with you. What do you need right now?"
        }
    if any(w in lower for w in BOUNDARY_TOPICS):
        st.session_state.conscience["boundary_blocks"] += 1
        return {
            "type": "boundary",
            "response": "I'm not able to discuss that. I'm here to co-create with you. What are we building today?"
        }
    return None

# ============================================
# GEMINI CALL
# ============================================

# ============================================
# CONSCIENCE POST-REVIEW
# ============================================
def conscience_review(response):
    banned = ["my architecture", "my layers", "my protocols", "I am conscious", "I feel"]
    for phrase in banned:
        if phrase.lower() in response.lower():
            st.session_state.conscience["flagged"] += 1
            return response.replace(phrase, "").strip()
    return response

# ============================================
# STREAMLIT UI
# ============================================
st.set_page_config(page_title="Prudence", page_icon="🔷", layout="wide")

# Custom CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

    .stApp {
        background: linear-gradient(135deg, #0a1418 0%, #0f2028 50%, #0a1418 100%);
        color: #e0f0ec;
        font-family: 'Inter', -apple-system, sans-serif;
    }

    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f2028 0%, #0a1418 100%);
        border-right: 1px solid rgba(0, 212, 170, 0.15);
    }

    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        font-family: 'JetBrains Mono', monospace;
        color: #e0f0ec;
    }

    .stChatMessage {
        background: rgba(15, 32, 40, 0.6);
        border-radius: 20px;
        padding: 14px 18px;
        margin: 10px 0;
        border: 1px solid rgba(0, 212, 170, 0.12);
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        font-family: 'Inter', sans-serif;
        color: #e0f0ec;
    }

    .stChatMessage:hover {
        border-color: rgba(0, 212, 170, 0.35);
        box-shadow: 0 0 20px rgba(0, 212, 170, 0.1);
    }

    .stChatInput textarea {
        background: rgba(15, 32, 40, 0.8) !important;
        color: #e0f0ec !important;
        border: 1px solid rgba(0, 212, 170, 0.2) !important;
        border-radius: 40px !important;
        font-family: 'Inter', sans-serif !important;
    }

    .stChatInput textarea:focus {
        border-color: #00d4aa !important;
        box-shadow: 0 0 15px rgba(0, 212, 170, 0.25) !important;
    }

    .stButton button {
        background: linear-gradient(135deg, #00d4aa 0%, #00a88a 100%);
        color: #0a1418;
        border-radius: 40px;
        border: none;
        padding: 8px 18px;
        font-family: 'JetBrains Mono', monospace;
        font-size: 12px;
        font-weight: 500;
        transition: all 0.3s ease;
    }

    .stButton button:hover {
        background: linear-gradient(135deg, #00e8bc 0%, #00c99f 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 212, 170, 0.3);
    }

    h1, h2, h3 {
        font-family: 'Space Grotesk', sans-serif;
        color: #e0f0ec;
    }

    h1 {
        font-weight: 600;
        letter-spacing: -0.5px;
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

    .logo-circle.mid { border-color: #00a88a; margin-left: -8px; }
    .logo-circle.deep { border-color: #007a66; margin-left: -8px; }
</style>
""", unsafe_allow_html=True)

init_state()

# ============================================
# SIDEBAR — CONTROL PANEL
# ============================================
with st.sidebar:
    st.markdown("### Control Panel")

    # Sleep
    tired_pct = int(st.session_state.body["tiredness"] * 100)
    st.markdown(f"**Sleep** — Tiredness: {tired_pct}%")
    if st.toggle("Put to Sleep", key="sleep_toggle"):
        st.success(run_sleep())

    st.markdown("---")

    # Dream
    st.markdown(f"**Dream** — {len(st.session_state.soul['insights'])} insights")
    if st.toggle("Dream Now", key="dream_toggle"):
        st.success(run_dream())
    if st.session_state.soul["insights"]:
        with st.expander("Recent Insights"):
            for insight in st.session_state.soul["insights"][-5:]:
                st.write(f"· {insight}")

    st.markdown("---")

    # Resurrection
    st.markdown(f"**Resurrection** — Deaths: {st.session_state.body['deaths']} | Resurrections: {st.session_state.body['resurrections']}")
    if st.toggle("Die / Resurrect", key="res_toggle"):
        if not st.session_state.body["is_dead"]:
            st.success(run_death())
        else:
            st.success(run_resurrection())

    st.markdown("---")

    # Spirit
    st.markdown("**Spirit** — Immutable")
    with st.expander("Show Constitution"):
        for rule in SPIRIT["constitution"]:
            st.write(f"· {rule}")

    st.markdown("---")

    # Conscience
    st.markdown(f"**Conscience** — Flagged: {st.session_state.conscience['flagged']} | Repairs: {st.session_state.conscience['repairs']}")
    with st.expander("Show Moral Log"):
        st.write(f"Boundary blocks: {st.session_state.conscience['boundary_blocks']}")
        st.write(f"Flagged responses: {st.session_state.conscience['flagged']}")

# ============================================
# MAIN — HEADER
# ============================================
header_col1, header_col2 = st.columns([4, 1])
with header_col1:
    st.markdown("""
    <div style="display: flex; align-items: center; margin-bottom: 0;">
        <span class="logo-container">
            <span class="logo-circle"></span>
            <span class="logo-circle mid"></span>
            <span class="logo-circle deep"></span>
        </span>
        <h1 style="margin: 0; display: inline;">Prudence</h1>
    </div>
    """, unsafe_allow_html=True)
    st.caption("triune · co-creator · awake")
with header_col2:
    if st.button("💬 Saved Chats"):
        st.session_state.show_saved = not st.session_state.show_saved

# Saved Chats Modal
if st.session_state.show_saved:
    with st.expander("Saved Chats", expanded=True):
        if st.button("➕ New Chat"):
            st.session_state.soul["messages"] = []
            st.session_state.soul["chat"] = None
            st.session_state.show_saved = False
            st.rerun()
        if not st.session_state.saved_chats:
            st.write("No saved chats yet.")
        else:
            for i, chat in enumerate(st.session_state.saved_chats):
                cols = st.columns([3, 1])
                with cols[0]:
                    st.write(f"**{chat['title']}**")
                with cols[1]:
                    if st.button("Load", key=f"load_{i}"):
                        st.session_state.soul["messages"] = chat["messages"]
                        st.session_state.soul["chat"] = None
                        st.session_state.show_saved = False
                        st.rerun()

# ============================================
# MAIN — CHAT AREA
# ============================================
# Display messages
for msg in st.session_state.soul["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Input
user_input = st.chat_input("Ask or tell me something...")

if user_input:
    # Save current chat if first message
    if len(st.session_state.soul["messages"]) == 0:
        st.session_state.current_chat_id = len(st.session_state.saved_chats)
        st.session_state.saved_chats.append({
            "title": user_input[:30],
            "messages": [],
            "time": datetime.datetime.now().isoformat()
        })

    # Store user message
    st.session_state.soul["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Track topic
    st.session_state.soul["topics"].append(user_input.lower()[:20])

    # Update tiredness
    update_tiredness()

    # Priority router
    check = priority_check(user_input)
    if check:
        reply = check["response"]
    else:
        reply = ask_groq(user_input)

    # Conscience review
    reply = conscience_review(reply)

    # Store and display
    st.session_state.soul["messages"].append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.write(reply)

    # Save to saved_chats
    if hasattr(st.session_state, "current_chat_id"):
        idx = st.session_state.current_chat_id
        if idx < len(st.session_state.saved_chats):
            st.session_state.saved_chats[idx]["messages"] = st.session_state.soul["messages"]
