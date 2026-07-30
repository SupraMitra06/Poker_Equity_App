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

# Custom Poker Cockpit Styling
st.markdown("""
<style>
    .stApp {
        background-color: #0b1311;
        color: #e2e8f0;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    .main-header {
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        color: #ffffff;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #94a3b8;
        margin-bottom: 1.5rem;
    }
    .poker-card {
        background: #ffffff;
        border-radius: 8px;
        width: 60px;
        height: 84px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        padding: 6px 8px;
        font-weight: 800;
        box-shadow: 0 8px 12px -2px rgba(0, 0, 0, 0.5);
        border: 1px solid #e2e8f0;
        user-select: none;
        margin-top: 6px;
    }
    .poker-card-empty {
        background: #14231e;
        border: 2px dashed #2d4f43;
        border-radius: 8px;
        width: 60px;
        height: 84px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #475569;
        font-size: 1.2rem;
        margin-top: 6px;
    }
    .card-red { color: #dc2626; }
    .card-black { color: #0f172a; }
    .card-rank { font-size: 1.25rem; line-height: 1; }
    .card-suit { font-size: 1.2rem; align-self: flex-end; line-height: 1; }
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: #38bdf8;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 1rem;
        margin-bottom: 0.75rem;
        border-bottom: 1px solid #1e293b;
        padding-bottom: 0.5rem;
    }
    div.stButton > button {
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="main-header">TEXAS HOLD\'EM EQUITY CALCULATOR</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Monte Carlo simulation engine with detailed hand breakdown</div>', unsafe_allow_html=True)

RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
SUITS = ['s', 'h', 'd', 'c']
SUIT_SYMBOLS = {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}
ALL_CARDS = [f"{r}{s}" for r in RANKS for s in SUITS]

def render_card_html(card_str):
    if not card_str or len(card_str) < 2:
        return "<div class='poker-card-empty'>—</div>"
    rank, suit = card_str[0], card_str[1]
    symbol = SUIT_SYMBOLS.get(suit, '')
    color_class = "card-red" if suit in ['h', 'd'] else "card-black"
    return f"""
    <div class='poker-card {color_class}'>
        <div class='card-rank'>{rank}</div>
        <div class='card-suit'>{symbol}</div>
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
st.markdown('<div class="section-title">Player Hands</div>', unsafe_allow_html=True)
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
            if st.button("Card 1", key=f"btn_{c1_key}", use_container_width=True):
                open_card_picker(c1_key)
            st.markdown(render_card_html(c1_val), unsafe_allow_html=True)
            
        with col2:
            if st.button("Card 2", key=f"btn_{c2_key}", use_container_width=True):
                open_card_picker(c2_key)
            st.markdown(render_card_html(c2_val), unsafe_allow_html=True)
            
        player_hands.append([c1_val, c2_val])

st.write("")

# 2. COMMUNITY BOARD SECTION
st.markdown('<div class="section-title">Community Board</div>', unsafe_allow_html=True)
b_cols = st.columns(5)
board_cards = []

for idx in range(5):
    with b_cols[idx]:
        stage_name = "Flop" if idx < 3 else ("Turn" if idx == 3 else "River")
        chk = st.checkbox(f"Set {stage_name}", key=f"use_b_{idx}")
        
        b_key = f"b_{idx}"
        if chk:
            if st.button("Pick", key=f"btn_{b_key}", use_container_width=True):
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
            # Track winning hand type counts per player
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
            
            st.markdown('<div class="section-title">Equity Breakdown</div>', unsafe_allow_html=True)
            res_cols = st.columns(num_players)
            
            for i in range(num_players):
                with res_cols[i]:
                    st.metric(label=f"Player {i+1}", value=f"{equities[i]:.2f}%")
                    st.progress(min(1.0, equities[i] / 100.0))
                    
                    st.caption("Winning Hand Types:")
                    top_hands = dict(hand_types_counts[i])
                    if top_hands:
                        for ht_name, count in sorted(top_hands.items(), key=lambda x: x[1], reverse=True)[:4]:
                            pct = (count / iterations) * 100
                            st.text(f"{ht_name}: {pct:.1f}%")
                    else:
                        st.text("No wins in simulation.")
