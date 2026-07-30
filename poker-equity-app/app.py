import streamlit as st
import eval7
import random

st.set_page_config(
    page_title="Texas Hold'em Equity Calculator",
    page_icon="♠️",
    layout="wide"
)

# Custom Styling
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
        margin-top: 4px;
    }
    .red-card { color: #dc2626; }
    .black-card { color: #111827; }
    
    /* Pop-up dialog styling */
    div[data-testid="stDialog"] {
        background-color: #1a2e26;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)

st.title("♠️ Texas Hold'em Equity Calculator")
st.caption("Click any card slot to open the selection modal.")

RANKS = ['A', 'K', 'Q', 'J', 'T', '9', '8', '7', '6', '5', '4', '3', '2']
SUITS = ['s', 'h', 'd', 'c']
SUIT_SYMBOLS = {'s': '♠', 'h': '♥', 'd': '♦', 'c': '♣'}

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

# Function to gather all currently selected cards across players & board
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

# --- CARD PICKER POP-UP MODAL ---
@st.dialog("🃏 Select a Card", width="large")
def open_card_picker(target_slot_key):
    st.write("Chosen cards are **darkened out** and disabled.")
    used_cards = get_used_cards()
    current_val = st.session_state.get(target_slot_key)
    
    suit_labels = {'s': '♠ Spades', 'h': '♥️ Hearts', 'd': '♦️ Diamonds', 'c': '♣ Clubs'}
    
    for suit in SUITS:
        st.caption(suit_labels[suit])
        grid_cols = st.columns(13)
        for r_idx, rank in enumerate(RANKS):
            card_code = f"{rank}{suit}"
            # Card is considered used unless it's the card currently in this slot
            is_used = (card_code in used_cards) and (card_code != current_val)
            
            with grid_cols[r_idx]:
                if is_used:
                    # Blackened/Disabled Button
                    st.button("✖", key=f"dlg_{target_slot_key}_{card_code}", disabled=True)
                else:
                    display_label = f"{rank}{SUIT_SYMBOLS[suit]}"
                    if st.button(display_label, key=f"dlg_{target_slot_key}_{card_code}", use_container_width=True):
                        st.session_state[target_slot_key] = card_code
                        st.rerun()

# --- MAIN INTERFACE SLOTS ---
st.subheader("🃏 Player Hands")
p_cols = st.columns(num_players)
player_hands = []

for i in range(num_players):
    with p_cols[i]:
        st.markdown(f"### Player {i+1}")
        col1, col2 = st.columns(2)
        
        c1_key = f"p{i}_c1"
        c2_key = f"p{i}_c2"
        
        with col1:
            if st.button("Card 1", key=f"btn_{c1_key}"):
                open_card_picker(c1_key)
            st.markdown(format_card_html(st.session_state.get(c1_key)), unsafe_allow_html=True)
            
        with col2:
            if st.button("Card 2", key=f"btn_{c2_key}"):
                open_card_picker(c2_key)
            st.markdown(format_card_html(st.session_state.get(c2_key)), unsafe_allow_html=True)
            
        player_hands.append([st.session_state.get(c1_key), st.session_state.get(c2_key)])

st.markdown("---")
st.subheader("🏟️ Community Board")
b_cols = st.columns(5)
board_cards = []

for idx in range(5):
    with b_cols[idx]:
        label_name = "Flop" if idx < 3 else ("Turn" if idx == 3 else "River")
        chk = st.checkbox(f"Set {label_name} {idx+1}", key=f"use_b_{idx}")
        
        b_key = f"b_{idx}"
        if chk:
            if st.button(f"Pick {label_name}", key=f"btn_{b_key}"):
                open_card_picker(b_key)
            
            card_val = st.session_state.get(b_key)
            if card_val:
                board_cards.append(card_val)
            st.markdown(format_card_html(card_val), unsafe_allow_html=True)

st.markdown("---")

# --- CALCULATOR ENGINE ---
all_selected_cards = [c for hand in player_hands for c in hand if c] + board_cards
missing_player_cards = any(c is None for hand in player_hands for c in hand)

if missing_player_cards:
    st.warning("⚠️ Please assign hole cards to all players.")
elif len(all_selected_cards) != len(set(all_selected_cards)):
    st.error("⚠️ Duplicate card detected! Please reassign unique cards.")
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
            
            total_eq = sum(equities)
            st.success(f"✅ Total Equity Sum: **{total_eq:.2f}%**")
