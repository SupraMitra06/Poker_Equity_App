import streamlit as st
import eval7
import random

st.set_page_config(
    page_title="Texas Hold'em Equity Calculator",
    page_icon="♠️",
    layout="wide"
)

# Custom Styling for Card Matrix and Active Slot Highlights
st.markdown("""
<style>
    .stApp {
        background-color: #0d3b2e;
        color: #ffffff;
    }
    .card-box {
        background-color: #ffffff;
        color: #1a1a1a;
        padding: 6px 10px;
        border-radius: 8px;
        font-weight: 800;
        font-size: 18px;
        font-family: 'Courier New', Courier, monospace;
        text-align: center;
        border: 2px solid #ccc;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 60px;
        height: 45px;
        margin: 2px;
    }
    .red-card { color: #dc2626; }
    .black-card { color: #111827; }
    
    /* Styling Streamlit Buttons in the Grid */
    div.stButton > button {
        width: 100%;
        height: 45px;
        font-weight: bold;
        font-size: 16px;
        border-radius: 6px;
    }
</style>
""", unsafe_allow_html=True)

st.title("♠️ Texas Hold'em Equity Calculator")
st.caption("Visual Card Selection Grid Matrix powered by eval7 Monte Carlo logic.")

RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
SUITS = ['s', 'h', 'd', 'c']
SUIT_SYMBOLS = {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}

# Full 52-card list formatted as strings
ALL_CARDS = [f"{r}{s}" for r in RANKS for s in SUITS]

def format_card_html(card_str):
    if not card_str or len(card_str) < 2:
        return "<div class='card-box' style='background-color:#2a5043; color:#a0aec0;'>?</div>"
    rank, suit = card_str[0], card_str[1]
    symbol = SUIT_SYMBOLS.get(suit, '')
    color_class = "red-card" if suit in ['h', 'd'] else "black-card"
    return f"<div class='card-box {color_class}'>{rank}{symbol}</div>"

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Simulation Settings")
    num_players = st.slider("Number of Players", min_value=2, max_value=6, value=2)
    iterations = st.select_slider("Monte Carlo Iterations", options=[1000, 5000, 10000, 25000], value=5000)

# Initialize Session States
if "active_target" not in st.session_state:
    st.session_state.active_target = "p0_c1"

# Initialize default card assignments
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

# Gather list of all currently assigned/used cards
used_cards = set()
for p in range(num_players):
    for c in [1, 2]:
        val = st.session_state.get(f"p{p}_c{c}")
        if val:
            used_cards.add(val)

for b in range(5):
    if st.session_state.get(f"use_b_{b}"):
        val = st.session_state.get(f"b_{b}")
        if val:
            used_cards.add(val)

# Helper function to handle slot selection
def set_active_slot(slot_key):
    st.session_state.active_target = slot_key

# --- 1. SELECTION SLOTS INTERFACE ---
st.subheader("🎯 Active Card Slots (Click a slot to assign next card)")

# Player Slots
p_cols = st.columns(num_players)
player_hands = []

for i in range(num_players):
    with p_cols[i]:
        st.markdown(f"**Player {i+1}**")
        c1_key = f"p{i}_c1"
        c2_key = f"p{i}_c2"
        
        col1, col2 = st.columns(2)
        with col1:
            is_active1 = st.session_state.active_target == c1_key
            label1 = "👉 Card 1" if is_active1 else "Card 1"
            st.button(label1, key=f"btn_{c1_key}", on_click=set_active_slot, args=(c1_key,), type="primary" if is_active1 else "secondary")
            st.markdown(format_card_html(st.session_state.get(c1_key)), unsafe_allow_html=True)
            
        with col2:
            is_active2 = st.session_state.active_target == c2_key
            label2 = "👉 Card 2" if is_active2 else "Card 2"
            st.button(label2, key=f"btn_{c2_key}", on_click=set_active_slot, args=(c2_key,), type="primary" if is_active2 else "secondary")
            st.markdown(format_card_html(st.session_state.get(c2_key)), unsafe_allow_html=True)
            
        player_hands.append([st.session_state.get(c1_key), st.session_state.get(c2_key)])

st.markdown("---")

# Board Slots
st.markdown("**Community Board**")
b_cols = st.columns(5)
board_cards = []

for idx in range(5):
    with b_cols[idx]:
        label_name = "Flop" if idx < 3 else ("Turn" if idx == 3 else "River")
        chk = st.checkbox(f"Set {label_name} {idx+1}", key=f"use_b_{idx}")
        
        b_key = f"b_{idx}"
        if chk:
            is_active = st.session_state.active_target == b_key
            b_label = f"👉 {label_name}" if is_active else label_name
            st.button(b_label, key=f"btn_{b_key}", on_click=set_active_slot, args=(b_key,), type="primary" if is_active else "secondary")
            
            card_val = st.session_state.get(b_key)
            if card_val:
                board_cards.append(card_val)
            st.markdown(format_card_html(card_val), unsafe_allow_html=True)

st.markdown("---")

# --- 2. 52-CARD GRID MATRIX ---
st.subheader("🃏 Deck Matrix (Click a card to assign to active slot)")

def select_card_from_grid(card_code):
    target_slot = st.session_state.active_target
    if target_slot:
        st.session_state[target_slot] = card_code

# Display Cards in a 4-row (Suits) by 13-column (Ranks) Matrix
suit_labels = {'s': '♠ Spades', 'h': '♥️ Hearts', 'd': '♦️ Diamonds', 'c': '♣ Clubs'}

for suit in SUITS:
    st.markdown(f"**{suit_labels[suit]}**")
    grid_cols = st.columns(13)
    for r_idx, rank in enumerate(RANKS):
        card_code = f"{rank}{suit}"
        is_used = card_code in used_cards
        
        with grid_cols[r_idx]:
            display_label = f"{rank}{SUIT_SYMBOLS[suit]}"
            if is_used:
                # Blackened out/Disabled button for chosen cards
                st.button(f"✖", key=f"grid_{card_code}", disabled=True, help=f"{card_code} is already chosen")
            else:
                st.button(
                    display_label,
                    key=f"grid_{card_code}",
                    on_click=select_card_from_grid,
                    args=(card_code,),
                    use_container_width=True
                )

st.markdown("---")

# --- 3. MONTE CARLO EQUITY CALCULATOR ---
all_selected_cards = [c for hand in player_hands for c in hand if c] + board_cards

# Verify completeness
missing_player_cards = any(c is None for hand in player_hands for c in hand)

if missing_player_cards:
    st.warning("⚠️ Please assign hole cards to all players using the deck matrix above.")
elif len(all_selected_cards) != len(set(all_selected_cards)):
    st.error("⚠️ Duplicate card detected! Please reset duplicate slots.")
else:
    if st.button("🚀 Calculate Equity", type="primary", use_container_width=True):
        with st.spinner(f"Running {iterations:,} Monte Carlo simulations..."):
            full_deck = list(eval7.Deck())
            known_cards = [eval7.Card(c) for c in all_selected_cards]
            
            deck = [c for c in full_deck if c not in known_cards]
            
            eval7_hands = [[eval7.Card(c) for c in hand] for hand in player_hands]
            eval7_board = [eval7.Card(c) for c in board_cards]
            cards_needed = 5 - len(eval7_board)
            
            wins = [0.0] * num_players
            
            for _ in range(iterations):
                random.shuffle(deck)
                simulated_board = eval7_board + deck[:cards_needed]
                
                scores = [eval7.evaluate(hand + simulated_board) for hand in eval7_hands]
                max_score = max(scores)
                
                winners = [i for i, score in enumerate(scores) if score == max_score]
                split_share = 1.0 / len(winners)
                
                for w in winners:
                    wins[w] += split_share
            
            equities = [(w / iterations) * 100 for w in wins]
            
            st.subheader("📊 Equity Results")
            res_cols = st.columns(num_players)
            
            for i in range(num_players):
                with res_cols[i]:
                    st.metric(label=f"Player {i+1} Equity", value=f"{equities[i]:.2f}%")
                    st.progress(min(1.0, equities[i] / 100.0))
            
