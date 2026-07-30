import streamlit as st
import eval7
import random
from collections import defaultdict

# Page Config
st.set_page_config(
    page_title="Texas Hold'em Equity Engine",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ANTI-GRAVITY UI/UX STYLING ---
st.markdown("""
<style>
    /* Dark Atmospheric Background with Radial Gradient Depth */
    .stApp {
        background: radial-gradient(circle at 50% 20%, #13241e 0%, #080d0b 80%);
        color: #f1f5f9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    
    /* Header Styling */
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.1rem;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #94a3b8;
        margin-bottom: 1.5rem;
    }
    
    /* Anti-Gravity Floating Poker Cards */
    .card-container {
        display: flex;
        justify-content: center;
        align-items: center;
        perspective: 1000px;
    }
    
    .poker-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(12px);
        border-radius: 12px;
        width: 68px;
        height: 96px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: 8px 10px;
        font-weight: 800;
        box-shadow: 
            0 10px 25px -5px rgba(0, 0, 0, 0.6),
            0 8px 10px -6px rgba(0, 0, 0, 0.5),
            inset 0 1px 1px rgba(255, 255, 255, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.4);
        user-select: none;
        margin-top: 6px;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
        cursor: pointer;
    }
    
    .poker-card:hover {
        transform: translateY(-8px) scale(1.05) rotateX(4deg);
        box-shadow: 
            0 20px 35px -10px rgba(56, 189, 248, 0.3),
            0 12px 15px -8px rgba(0, 0, 0, 0.7);
        border-color: #38bdf8;
    }

    .poker-card-empty {
        background: rgba(20, 35, 30, 0.4);
        backdrop-filter: blur(8px);
        border: 2px dashed rgba(56, 189, 248, 0.25);
        border-radius: 12px;
        width: 68px;
        height: 96px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #475569;
        font-size: 1.4rem;
        margin-top: 6px;
        transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    }
    
    .poker-card-empty:hover {
        border-color: rgba(56, 189, 248, 0.6);
        background: rgba(20, 35, 30, 0.7);
        transform: translateY(-4px);
    }

    .card-red { color: #e11d48; }
    .card-black { color: #0f172a; }
    .card-rank { font-size: 1.4rem; line-height: 1; }
    .card-suit { font-size: 1.3rem; align-self: flex-end; line-height: 1; }
    
    /* Floating HUD Panels */
    .hud-card {
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 12px 30px -10px rgba(0, 0, 0, 0.5);
        margin-bottom: 12px;
        transition: transform 0.3s ease;
    }
    
    .hud-card:hover {
        transform: translateY(-4px);
        border-color: rgba(56, 189, 248, 0.3);
    }

    .section-title {
        font-size: 1.05rem;
        font-weight: 700;
        color: #38bdf8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 1.2rem;
        margin-bottom: 0.8rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    
    /* Primary CTA Button Overrides */
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%);
        border: none;
        box-shadow: 0 10px 20px -5px rgba(2, 132, 199, 0.5);
        transition: all 0.25s ease;
    }
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 15px 25px -5px rgba(2, 132, 199, 0.7);
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-title">TEXAS HOLD\'EM EQUITY ENGINE</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Anti-gravity tactile equity & outcome probability engine</div>', unsafe_allow_html=True)

RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
SUITS = ['s', 'h', 'd', 'c']
SUIT_SYMBOLS = {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}
ALL_CARDS = [f"{r}{s}" for r in RANKS for s in SUITS]

def render_card_html(card_str):
    if not card_str or len(card_str) < 2:
        return "<div class='card-container'><div class='poker-card-empty'>+</div></div>"
    rank, suit = card_str[0], card_str[1]
    symbol = SUIT_SYMBOLS.get(suit, '')
    color_class = "card-red" if suit in ['h', 'd'] else "card-black"
    return f"""
    <div class='card-container'>
        <div class='poker-card {color_class}'>
            <div class='card-rank'>{rank}</div>
            <div class='card-suit'>{symbol}</div>
        </div>
    </div>
    """

# Sidebar Control
with st.sidebar:
    st.markdown("### Settings")
    num_players = st.slider("Number of Players", min_value=2, max_value=6, value=2)
    iterations = st.select_slider(
        "Monte Carlo Iterations", 
        options=[1000, 5000, 10000, 25000], 
        value=5000
    )
    st.divider()
    
    st.markdown("### Quick Actions")
    if st.button("Reset Board Cards", use_container_width=True):
        for b in range(5):
            st.session_state[f"b_{b}"] = None
            st.session_state[f"use_b_{b}"] = False
        st.rerun()
        
    if st.button("Reset Everything", type="secondary", use_container_width=True):
        st.session_state.clear()
        st.rerun()

# Initialize Session State
card_idx = 0
for p in range(6):
    for c in [1, 2]:
        key = f"p{p}_c{c}"
        if key not in st.session_state:
            st.session_state[key] = ALL_CARDS[card_idx % 52]
            card_idx += 1

for b in range(5):
    key = f"b_{b}"
    chk_key = f"use_b_{b}"
    if key not in st.session_state:
        st.session_state[key] = None
    if chk_key not in st.session_state:
        st.session_state[chk_key] = False

def get_used_cards():
    used = set()
    for p in range(num_players):
        for c in [1, 2]:
            val = st.session_state.get(f"p{p}_c{c}")
            if val:
                used.add(val)
    for b in range(5):
        if st.session_state.get(f"use_b_{b}"):
            val = st.session_state.get(f"b_{b}")
            if val:
                used.add(val)
    return used

# Card Selection Modal Dialog
@st.dialog("Select Card", width="large")
def open_card_picker(target_slot_key):
    used_cards = get_used_cards()
    current_val = st.session_state.get(target_slot_key)
    suit_names = {'s': 'Spades (♠)', 'h': 'Hearts (♥)', 'd': 'Diamonds (♦)', 'c': 'Clubs (♣)'}
    
    for suit in SUITS:
        st.caption(suit_names[suit])
        grid_cols = st.columns(13)
        for r_idx, rank in enumerate(RANKS):
            card_code = f"{rank}{suit}"
            is_used = (card_code in used_cards) and (card_code != current_val)
            
            with grid_cols[r_idx]:
                if is_used:
                    st.button("✖", key=f"dlg_{target_slot_key}_{card_code}", disabled=True)
                else:
                    display_label = f"{rank}{SUIT_SYMBOLS[suit]}"
                    if st.button(display_label, key=f"dlg_{target_slot_key}_{card_code}", use_container_width=True):
                        st.session_state[target_slot_key] = card_code
                        st.rerun()

# 1. PLAYER HANDS SECTION
st.markdown('<div class="section-title">PLAYER HANDS</div>', unsafe_allow_html=True)
p_cols = st.columns(num_players)
player_hands = []

for i in range(num_players):
    with p_cols[i]:
        st.markdown(f"**Player {i+1}**")
        c1_key = f"p{i}_c1"
        c2_key = f"p{i}_c2"
        
        c1_val = st.session_state.get(c1_key)
        c2_val = st.session_state.get(c2_key)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Slot 1", key=f"btn_{c1_key}", use_container_width=True):
                open_card_picker(c1_key)
            st.markdown(render_card_html(c1_val), unsafe_allow_html=True)
            
        with col2:
            if st.button("Slot 2", key=f"btn_{c2_key}", use_container_width=True):
                open_card_picker(c2_key)
            st.markdown(render_card_html(c2_val), unsafe_allow_html=True)
            
        player_hands.append([c1_val, c2_val])

st.write("")

# 2. COMMUNITY BOARD SECTION
st.markdown('<div class="section-title">COMMUNITY BOARD</div>', unsafe_allow_html=True)
b_cols = st.columns(5)
board_cards = []

for idx in range(5):
    with b_cols[idx]:
        stage_name = "Flop" if idx < 3 else ("Turn" if idx == 3 else "River")
        chk = st.checkbox(f"Set {stage_name}", key=f"use_b_{idx}")
        
        b_key = f"b_{idx}"
        if chk:
            if st.button("Select", key=f"btn_{b_key}", use_container_width=True):
                open_card_picker(b_key)
            card_val = st.session_state.get(b_key)
            if card_val:
                board_cards.append(card_val)
            st.markdown(render_card_html(card_val), unsafe_allow_html=True)
        else:
            st.markdown(render_card_html(None), unsafe_allow_html=True)

st.write("")
st.divider()

# 3. CALCULATOR ENGINE & HAND TYPE ANALYSIS
all_selected_cards = [c for hand in player_hands for c in hand if c] + board_cards
missing_player_cards = any(c is None for hand in player_hands for c in hand)

if missing_player_cards:
    st.info("Assign hole cards for all players to calculate equity.")
elif len(all_selected_cards) != len(set(all_selected_cards)):
    st.error("Duplicate card selection detected. Please review assigned cards.")
else:
    if st.button("Run Equity Simulation", type="primary", use_container_width=True):
        with st.spinner(f"Simulating {iterations:,} Monte Carlo hands..."):
            full_deck = list(eval7.Deck())
            known_cards = [eval7.Card(c) for c in all_selected_cards]
            
            deck = [c for c in full_deck if c not in known_cards]
            
            eval7_hands = [[eval7.Card(c) for c in hand] for hand in player_hands]
            eval7_board = [eval7.Card(c) for c in board_cards]
            cards_needed = 5 - len(eval7_board)
            
            wins = [0.0] * num_players
            hand_types_counts = [defaultdict(int) for _ in range(num_players)]
            
            for _ in range(iterations):
                random.shuffle(deck)
                simulated_board = eval7_board + deck[:cards_needed]
                
                scores = [eval7.evaluate(hand + simulated_board) for hand in eval7_hands]
                max_score = max(scores)
                
                winners = [i for i, score in enumerate(scores) if score == max_score]
                split_share = 1.0 / len(winners)
                
                for w in winners:
                    wins[w] += split_share
                    w_score = scores[w]
                    ht_name = eval7.handtype(w_score)
                    hand_types_counts[w][ht_name] += 1
            
            equities = [(w / iterations) * 100 for w in wins]
            
            st.markdown('<div class="section-title">EQUITY BREAKDOWN</div>', unsafe_allow_html=True)
            res_cols = st.columns(num_players)
            
            for i in range(num_players):
                with res_cols[i]:
                    st.markdown(f"""
                    <div class="hud-card">
                        <h4 style="margin:0; color:#38bdf8;">Player {i+1}</h4>
                        <h2 style="margin:4px 0 12px 0; font-size:2rem; font-weight:800;">{equities[i]:.2f}%</h2>
                    </div>
                    """, unsafe_allow_html=True)
                    st.progress(min(1.0, equities[i] / 100.0))
                    
                    st.caption("Winning Hand Types:")
                    top_hands = dict(hand_types_counts[i])
                    if top_hands:
                        for ht_name, count in sorted(top_hands.items(), key=lambda x: x[1], reverse=True)[:4]:
                            pct = (count / iterations) * 100
                            st.text(f"{ht_name}: {pct:.1f}%")
                    else:
                        st.text("No wins in simulation.")
