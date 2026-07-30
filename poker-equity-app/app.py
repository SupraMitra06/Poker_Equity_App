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
st.caption("Accurate Monte Carlo equity simulation powered by eval7.")

RANKS = ['2', '3', '4', '5', '6', '7', '8', '9', 'T', 'J', 'Q', 'K', 'A']
SUITS = ['s', 'h', 'd', 'c']
SUIT_SYMBOLS = {'s': '♠', 'h': '♥️', 'd': '♦️', 'c': '♣️'}

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

st.subheader("🃏 Player Hands")
p_cols = st.columns(num_players)
player_hands = []

for i in range(num_players):
    with p_cols[i]:
        st.markdown(f"### Player {i+1}")
        c1_rank = st.selectbox(f"P{i+1} Card 1 Rank", RANKS, index=(i*2) % 13, key=f"p{i}_c1_r")
        c1_suit = st.selectbox(f"P{i+1} Card 1 Suit", SUITS, index=i % 4, key=f"p{i}_c1_s")
        
        c2_rank = st.selectbox(f"P{i+1} Card 2 Rank", RANKS, index=(i*2+1) % 13, key=f"p{i}_c2_r")
        c2_suit = st.selectbox(f"P{i+1} Card 2 Suit", SUITS, index=(i+1) % 4, key=f"p{i}_c2_s")
        
        card1 = f"{c1_rank}{c1_suit}"
        card2 = f"{c2_rank}{c2_suit}"
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
            b_rank = st.selectbox(f"Rank {idx+1}", RANKS, index=(idx+3) % 13, key=f"b_{idx}_r")
            b_suit = st.selectbox(f"Suit {idx+1}", SUITS, index=idx % 4, key=f"b_{idx}_s")
            b_card = f"{b_rank}{b_suit}"
            board_cards.append(b_card)
            st.markdown(format_card_html(b_card), unsafe_allow_html=True)

st.markdown("---")

# Verify no duplicate cards selected
all_selected_cards = [c for hand in player_hands for c in hand] + board_cards
if len(all_selected_cards) != len(set(all_selected_cards)):
    st.error("⚠️ Duplicate cards detected in player hands or community board! Please select unique cards.")
else:
    if st.button("🚀 Calculate Real Equity", type="primary", use_container_width=True):
        with st.spinner(f"Running {iterations:,} Monte Carlo simulations..."):
            # Build eval7 deck
            deck = [eval7.Card(c) for c in eval7.Deck()]
            
            # Known cards to remove from deck
            known_cards = [eval7.Card(c) for c in all_selected_cards]
            for card in known_cards:
                deck.remove(card)
            
            # Setup player hands & board
            eval7_hands = [[eval7.Card(c) for c in hand] for hand in player_hands]
            eval7_board = [eval7.Card(c) for c in board_cards]
            cards_needed = 5 - len(eval7_board)
            
            # Equity tracking counters
            wins = [0.0] * num_players
            
            for _ in range(iterations):
                random.shuffle(deck)
                simulated_board = eval7_board + deck[:cards_needed]
                
                # Evaluate scores (higher score = better hand)
                scores = [eval7.evaluate(hand + simulated_board) for hand in eval7_hands]
                max_score = max(scores)
                
                # Identify winners and handle ties (split pots)
                winners = [i for i, score in enumerate(scores) if score == max_score]
                split_share = 1.0 / len(winners)
                
                for w in winners:
                    wins[w] += split_share
            
            # Calculate percentages
            equities = [(w / iterations) * 100 for w in wins]
            
            # Display results
            st.subheader("📊 Equity Results")
            res_cols = st.columns(num_players)
            
            for i in range(num_players):
                with res_cols[i]:
                    st.metric(label=f"Player {i+1} Equity", value=f"{equities[i]:.2f}%")
                    st.progress(min(1.0, equities[i] / 100.0))
            
            total_eq = sum(equities)
            st.success(f"✅ Total Equity Sum: **{total_eq:.2f}%**")
