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
        padding: 10px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 18px;
        text-align: center;
        border: 2px solid #ccc;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        display: inline-block;
        width: 55px;
    }
    .red-card { color: #dc2626; }
    .black-card { color: #111827; }
</style>
""", unsafe_allow_html=True)

st.title("♠️ Texas Hold'em Equity Calculator")
st.caption("Accurate Monte Carlo equity simulation with dynamic card filtering.")

RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
SUITS = ['s', 'h', 'd', 'c']
SUIT_SYMBOLS = {'s': '♠', 'h': '♥️', 'd': '♦️', 'c': '♣️'}

# Generate full 52-card list formatted as strings (e.g., 'As', 'Kd', 'Tc')
ALL_CARDS = [f"{r}{s}" for r in RANKS for s in SUITS]

def format_card_label(card_str):
    if not card_str:
        return ""
    rank, suit = card_str[0], card_str[1]
    return f"{rank}{SUIT_SYMBOLS.get(suit, suit)}"

def format_card_html(card_str):
    if not card_str or len(card_str) < 2:
        return ""
    rank, suit = card_str[0], card_str[1]
    symbol = SUIT_SYMBOLS.get(suit, '')
    color_class = "red-card" if suit in ['h', 'd'] else "black-card"
    return f"<span class='card-box {color_class}'>{rank}{symbol}</span>"

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Simulation Settings")
    num_players = st.slider("Number of Players", min_value=2, max_value=6, value=2)
    iterations = st.select_slider("Monte Carlo Iterations", options=[1000, 5000, 10000, 25000], value=5000)

# Initialize unique cards in session_state if missing
default_card_assignments = ALL_CARDS[: (num_players * 2) + 5]
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
        st.session_state[key] = ALL_CARDS[card_idx % 52]
        card_idx += 1
    if chk_key not in st.session_state:
        st.session_state[chk_key] = False

# Helper function to get available cards for a given selector
def get_available_cards(current_key):
    used_cards = set()
    # Collect currently selected player cards
    for p in range(num_players):
        for c in [1, 2]:
            k = f"p{p}_c{c}"
            if k != current_key and k in st.session_state:
                used_cards.add(st.session_state[k])
    # Collect active board cards
    for b in range(5):
        k = f"b_{b}"
        chk = f"use_b_{b}"
        if k != current_key and st.session_state.get(chk, False) and k in st.session_state:
            used_cards.add(st.session_state[k])
            
    return [card for card in ALL_CARDS if card not in used_cards]

st.subheader("🃏 Player Hands")
p_cols = st.columns(num_players)
player_hands = []

for i in range(num_players):
    with p_cols[i]:
        st.markdown(f"### Player {i+1}")
        
        # Card 1 Selector
        c1_key = f"p{i}_c1"
        c1_options = get_available_cards(c1_key)
        if st.session_state[c1_key] not in c1_options:
            st.session_state[c1_key] = c1_options[0]
        card1 = st.selectbox(
            f"P{i+1} Card 1",
            options=c1_options,
            format_func=format_card_label,
            key=c1_key
        )
        
        # Card 2 Selector
        c2_key = f"p{i}_c2"
        c2_options = get_available_cards(c2_key)
        if st.session_state[c2_key] not in c2_options:
            st.session_state[c2_key] = c2_options[0]
        card2 = st.selectbox(
            f"P{i+1} Card 2",
            options=c2_options,
            format_func=format_card_label,
            key=c2_key
        )
        
        player_hands.append([card1, card2])
        st.markdown(f"{format_card_html(card1)} {format_card_html(card2)}", unsafe_allow_html=True)

st.markdown("---")
st.subheader("🏟️ Community Board Cards")
b_cols = st.columns(5)

board_cards = []
for idx in range(5):
    with b_cols[idx]:
        label = "Flop" if idx < 3 else ("Turn" if idx == 3 else "River")
        use_card = st.checkbox(f"Set {label} {idx+1}", key=f"use_b_{idx}")
        if use_card:
            b_key = f"b_{idx}"
            b_options = get_available_cards(b_key)
            if st.session_state[b_key] not in b_options:
                st.session_state[b_key] = b_options[0]
            b_card = st.selectbox(
                f"{label} {idx+1}",
                options=b_options,
                format_func=format_card_label,
                key=b_key
            )
            board_cards.append(b_card)
            st.markdown(format_card_html(b_card), unsafe_allow_html=True)

st.markdown("---")

# Calculate Button and Monte Carlo Engine
if st.button("🚀 Calculate Equity", type="primary", use_container_width=True):
    with st.spinner(f"Running {iterations:,} Monte Carlo simulations..."):
        # Construct full deck and remove all known active cards
        all_selected_cards = [c for hand in player_hands for c in hand] + board_cards
        full_deck = list(eval7.Deck())
        known_cards = [eval7.Card(c) for c in all_selected_cards]
        
        # Dead cards excluded from draw pool
        deck = [c for c in full_deck if c not in known_cards]
        
        # Convert inputs to eval7 card objects
        eval7_hands = [[eval7.Card(c) for c in hand] for hand in player_hands]
        eval7_board = [eval7.Card(c) for c in board_cards]
        cards_needed = 5 - len(eval7_board)
        
        wins = [0.0] * num_players
        
        # Monte Carlo Loop
        for _ in range(iterations):
            random.shuffle(deck)
            simulated_board = eval7_board + deck[:cards_needed]
            
            # Evaluate hand strengths
            scores = [eval7.evaluate(hand + simulated_board) for hand in eval7_hands]
            max_score = max(scores)
            
            # Split pot distribution
            winners = [i for i, score in enumerate(scores) if score == max_score]
            split_share = 1.0 / len(winners)
            
            for w in winners:
                wins[w] += split_share
        
        equities = [(w / iterations) * 100 for w in wins]
        
        # Display Results
        st.subheader("📊 Equity Results")
        res_cols = st.columns(num_players)
        
        for i in range(num_players):
            with res_cols[i]:
                st.metric(label=f"Player {i+1} Equity", value=f"{equities[i]:.2f}%")
                st.progress(min(1.0, equities[i] / 100.0))
        
        total_eq = sum(equities)
        st.success(f"✅ Total Equity Sum: **{total_eq:.2f}%**")
