import React, { useState, useEffect, useRef, useMemo } from "react";

/* ============================================================
   1. CORE ENGINE & BITWISE / MONTE CARLO WEB WORKER (BLOB)
   ============================================================ */

const WORKER_CODE = `
const RANKS = ["2","3","4","5","6","7","8","9","T","J","Q","K","A"];
const SUITS = ["s","h","d","c"];

function fullDeck() {
  const deck = [];
  for (let r = 2; r <= 14; r++) {
    for (const s of SUITS) deck.push({ rank: r, suit: s });
  }
  return deck;
}

function sameCard(a, b) {
  return a.rank === b.rank && a.suit === b.suit;
}

function evaluate5(cards) {
  const ranks = cards.map((c) => c.rank).sort((a, b) => b - a);
  const suits = cards.map((c) => c.suit);
  const isFlush = suits.every((s) => s === suits[0]);

  const counts = {};
  for (const r of ranks) counts[r] = (counts[r] || 0) + 1;
  const countEntries = Object.entries(counts)
    .map(([r, c]) => [Number(r), c])
    .sort((a, b) => b[1] - a[1] || b[0] - a[0]);

  const uniqueRanks = [...new Set(ranks)];
  let isStraight = false;
  let straightHigh = 0;
  if (uniqueRanks.length >= 5) {
    for (let i = 0; i <= uniqueRanks.length - 5; i++) {
      if (uniqueRanks[i] - uniqueRanks[i + 4] === 4) {
        isStraight = true;
        straightHigh = uniqueRanks[i];
        break;
      }
    }
  }
  if (!isStraight && [14, 5, 4, 3, 2].every((r) => uniqueRanks.includes(r))) {
    isStraight = true;
    straightHigh = 5;
  }

  if (isFlush && isStraight) return [8, straightHigh];
  if (countEntries[0][1] === 4) return [7, countEntries[0][0], countEntries[1][0]];
  if (countEntries[0][1] === 3 && countEntries[1][1] >= 2) return [6, countEntries[0][0], countEntries[1][0]];
  if (isFlush) return [5, ...ranks];
  if (isStraight) return [4, straightHigh];
  if (countEntries[0][1] === 3) return [3, countEntries[0][0], ...countEntries.slice(1).map((e) => e[0])];
  if (countEntries[0][1] === 2 && countEntries[1][1] === 2) {
    const pairs = [countEntries[0][0], countEntries[1][0]].sort((a, b) => b - a);
    return [2, ...pairs, countEntries[2][0]];
  }
  if (countEntries[0][1] === 2) return [1, countEntries[0][0], ...countEntries.slice(1).map((e) => e[0])];
  return [0, ...ranks];
}

function compareHand(a, b) {
  const len = Math.max(a.length, b.length);
  for (let i = 0; i < len; i++) {
    const av = a[i] ?? 0;
    const bv = b[i] ?? 0;
    if (av !== bv) return av - bv;
  }
  return 0;
}

function* combosGen(arr, k, start = 0, prefix = []) {
  if (prefix.length === k) {
    yield prefix;
    return;
  }
  for (let i = start; i <= arr.length - (k - prefix.length); i++) {
    yield* combosGen(arr, k, i + 1, [...prefix, arr[i]]);
  }
}

function evaluate7(cards) {
  let best = null;
  for (const combo of combosGen(cards, 5)) {
    const val = evaluate5(combo);
    if (!best || compareHand(val, best) > 0) best = val;
  }
  return best;
}

self.onmessage = function (e) {
  const { players, board, usedCards, id } = e.data;
  const deck = fullDeck().filter((c) => !usedCards.some((u) => sameCard(u, c)));
  const missing = 5 - board.length;
  const numPlayers = players.length;

  const winTally = new Array(numPlayers).fill(0);
  const tieTally = new Array(numPlayers).fill(0);
  const handDist = Array.from({ length: numPlayers }, () => new Array(9).fill(0));

  const isPreflop = missing === 5;
  const MAX_SAMPLES = isPreflop ? 30000 : 0;

  if (isPreflop) {
    // Monte Carlo sampling for fast response (<30ms)
    for (let i = 0; i < MAX_SAMPLES; i++) {
      // In-place Fisher-Yates sample for missing cards
      const extra = [];
      const deckCopy = [...deck];
      for (let m = 0; m < missing; m++) {
        const idx = Math.floor(Math.random() * deckCopy.length);
        extra.push(deckCopy[idx]);
        deckCopy[idx] = deckCopy[deckCopy.length - 1];
        deckCopy.pop();
      }

      const fullBoard = [...board, ...extra];
      const results = players.map((p) => evaluate7([...p, ...fullBoard]));

      let bestVal = results[0];
      for (let p = 0; p < numPlayers; p++) {
        handDist[p][results[p][0]]++;
        if (compareHand(results[p], bestVal) > 0) bestVal = results[p];
      }

      const winners = [];
      for (let p = 0; p < numPlayers; p++) {
        if (compareHand(results[p], bestVal) === 0) winners.push(p);
      }

      if (winners.length === 1) {
        winTally[winners[0]]++;
      } else {
        winners.forEach((w) => tieTally[w]++);
      }
    }

    const wins = winTally.map((w) => (w / MAX_SAMPLES) * 100);
    const ties = tieTally.map((t) => (t / MAX_SAMPLES) * 100);
    const equities = wins.map((w, i) => w + ties[i] / 2);
    const distributions = handDist.map((dist) => dist.map((c) => (c / MAX_SAMPLES) * 100));

    self.postMessage({ id, equities, wins, ties, distributions, isMonteCarlo: true });
  } else {
    // Exact Enumeration for Postflop (Flop: 990 combos, Turn: 44 combos, River: 1 combo)
    let totalCombos = 0;
    for (const extra of combosGen(deck, missing)) {
      totalCombos++;
      const fullBoard = [...board, ...extra];
      const results = players.map((p) => evaluate7([...p, ...fullBoard]));

      let bestVal = results[0];
      for (let p = 0; p < numPlayers; p++) {
        handDist[p][results[p][0]]++;
        if (compareHand(results[p], bestVal) > 0) bestVal = results[p];
      }

      const winners = [];
      for (let p = 0; p < numPlayers; p++) {
        if (compareHand(results[p], bestVal) === 0) winners.push(p);
      }

      if (winners.length === 1) {
        winTally[winners[0]]++;
      } else {
        winners.forEach((w) => tieTally[w]++);
      }
    }

    const wins = winTally.map((w) => (w / totalCombos) * 100);
    const ties = tieTally.map((t) => (t / totalCombos) * 100);
    const equities = wins.map((w, i) => w + ties[i] / 2);
    const distributions = handDist.map((dist) => dist.map((c) => (c / totalCombos) * 100));

    self.postMessage({ id, equities, wins, ties, distributions, isMonteCarlo: false });
  }
};
`;

const RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"];
const SUITS = ["s", "h", "d", "c"];
const SUIT_SYMBOL = { s: "♠", h: "♥", d: "♦", c: "♣" };
const SUIT_COLOR = { s: "#1a1a1a", c: "#1a1a1a", h: "#c0392b", d: "#c0392b" };

const HAND_CATEGORY_NAMES = [
  "High Card", "Pair", "Two Pair", "Three of a Kind", 
  "Straight", "Flush", "Full House", "Four of a Kind", "Straight Flush"
];

const PLAYER_COLORS = [
  "#e0b84f", "#5fb3b3", "#e08a5f", "#8f9ff3",
  "#7fca7f", "#f26d9a", "#c9a0ff", "#f2d16d"
];

function fullDeck() {
  const deck = [];
  for (let r = 2; r <= 14; r++) {
    for (const s of SUITS) deck.push({ rank: r, suit: s });
  }
  return deck;
}

function cardId(c) {
  return `${RANKS[c.rank - 2]}${c.suit}`;
}

/* ============================================================
   2. UI COMPONENTS
   ============================================================ */

function Card({ card, size = "md" }) {
  const dims = size === "sm" ? { w: 34, h: 48, fs: 14 } : { w: 52, h: 72, fs: 20 };
  if (!card) {
    return (
      <div
        style={{
          width: dims.w,
          height: dims.h,
          borderRadius: 6,
          border: "2px dashed rgba(255,255,255,0.25)",
        }}
      />
    );
  }
  return (
    <div
      style={{
        width: dims.w,
        height: dims.h,
        borderRadius: 6,
        background: "#fdfdfa",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        boxShadow: "0 2px 4px rgba(0,0,0,0.4)",
        color: SUIT_COLOR[card.suit],
        fontWeight: 700,
        lineHeight: 1,
        fontSize: dims.fs,
        fontFamily: "'Georgia', serif",
      }}
    >
      <div>{RANKS[card.rank - 2]}</div>
      <div style={{ fontSize: dims.fs * 0.9 }}>{SUIT_SYMBOL[card.suit]}</div>
    </div>
  );
}

function CardPicker({ availableIds, onPick, onClose }) {
  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.65)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 50,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: "#0f2e22",
          border: "1px solid #2f5c46",
          borderRadius: 10,
          padding: 16,
          maxWidth: 440,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: "grid", gridTemplateColumns: "repeat(13, 1fr)", gap: 4 }}>
          {SUITS.map((s) =>
            RANKS.map((rLabel, ri) => {
              const rank = ri + 2;
              const id = `${rLabel}${s}`;
              const disabled = !availableIds.has(id);
              return (
                <button
                  key={id}
                  disabled={disabled}
                  onClick={() => onPick({ rank, suit: s })}
                  style={{
                    width: 28,
                    height: 32,
                    fontSize: 11,
                    borderRadius: 4,
                    border: "1px solid #2f5c46",
                    background: disabled ? "#173327" : "#fdfdfa",
                    color: disabled ? "#3a5c4e" : SUIT_COLOR[s],
                    cursor: disabled ? "not-allowed" : "pointer",
                    fontWeight: 700,
                  }}
                >
                  {rLabel}{SUIT_SYMBOL[s]}
                </button>
              );
            })
          )}
        </div>
        <div style={{ marginTop: 12, textAlign: "center" }}>
          <button onClick={onClose} style={btnGhost}>Cancel</button>
        </div>
      </div>
    </div>
  );
}

function HandRangeModal({ onSelectCombo, onClose }) {
  const matrixRanks = [...RANKS].reverse();

  const handleCellClick = (r1Idx, r2Idx) => {
    const r1 = 14 - r1Idx;
    const r2 = 14 - r2Idx;
    
    if (r1 === r2) {
      // Pair -> e.g. Ah Ad
      onSelectCombo([{ rank: r1, suit: "h" }, { rank: r2, suit: "d" }]);
    } else if (r1Idx < r2Idx) {
      // Suited -> e.g. Ah Kh
      onSelectCombo([{ rank: r1, suit: "h" }, { rank: r2, suit: "h" }]);
    } else {
      // Offsuit -> e.g. Ah Ks
      onSelectCombo([{ rank: r1, suit: "h" }, { rank: r2, suit: "s" }]);
    }
  };

  return (
    <div
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.7)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 60,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: "#0d261c",
          border: "1px solid #2f5c46",
          borderRadius: 12,
          padding: 20,
          maxWidth: 540,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ fontSize: 14, fontWeight: 700, marginBottom: 12, color: "#e8f3ec" }}>
          Select Starting Hand Matrix (13 x 13)
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(13, 1fr)", gap: 2 }}>
          {matrixRanks.map((r1Label, r1Idx) =>
            matrixRanks.map((r2Label, r2Idx) => {
              const isPair = r1Idx === r2Idx;
              const isSuited = r1Idx < r2Idx;
              const label = isPair ? `${r1Label}${r2Label}` : isSuited ? `${r1Label}${r2Label}s` : `${r2Label}${r1Label}o`;
              const bg = isPair ? "#4a3b10" : isSuited ? "#1d4734" : "#24332c";

              return (
                <button
                  key={label}
                  onClick={() => handleCellClick(r1Idx, r2Idx)}
                  style={{
                    height: 32,
                    fontSize: 10,
                    borderRadius: 3,
                    border: "1px solid rgba(255,255,255,0.08)",
                    background: bg,
                    color: "#e8f3ec",
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  {label}
                </button>
              );
            })
          )}
        </div>
        <div style={{ marginTop: 14, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontSize: 11, color: "#8fb5a2" }}>
            Gold = Pairs | Green = Suited | Dark = Offsuit
          </span>
          <button onClick={onClose} style={btnGhost}>Close</button>
        </div>
      </div>
    </div>
  );
}

/* ============================================================
   3. MAIN CALCULATOR COMPONENT
   ============================================================ */

export default function PokerEquity() {
  const [numPlayers, setNumPlayers] = useState(3);
  const [playerCards, setPlayerCards] = useState(Array.from({ length: 3 }, () => [null, null]));
  const [board, setBoard] = useState([null, null, null, null, null]);
  const [picker, setPicker] = useState(null); 
  const [rangeModalPi, setRangeModalPi] = useState(null);

  const [calcResult, setCalcResult] = useState(null);
  const [computing, setComputing] = useState(false);

  const workerRef = useRef(null);
  const reqId = useRef(0);

  // Initialize Web Worker via Blob
  useEffect(() => {
    const blob = new Blob([WORKER_CODE], { type: "application/javascript" });
    workerRef.current = new Worker(URL.createObjectURL(blob));

    workerRef.current.onmessage = (e) => {
      if (e.data.id === reqId.current) {
        setCalcResult(e.data);
        setComputing(false);
      }
    };

    return () => workerRef.current.terminate();
  }, []);

  function resizePlayers(n) {
    setNumPlayers(n);
    setPlayerCards((prev) => Array.from({ length: n }, (_, i) => prev[i] || [null, null]));
    setCalcResult(null);
  }

  const usedCards = useMemo(() => {
    const cards = [];
    playerCards.forEach((pc) => pc.forEach((c) => c && cards.push(c)));
    board.forEach((c) => c && cards.push(c));
    return cards;
  }, [playerCards, board]);

  const availableIds = useMemo(() => {
    const used = new Set(usedCards.map(cardId));
    const s = new Set();
    fullDeck().forEach((c) => {
      const id = cardId(c);
      if (!used.has(id)) s.add(id);
    });
    return s;
  }, [usedCards]);

  function assignCard(card) {
    if (!picker) return;
    if (picker.type === "player") {
      setPlayerCards((prev) => {
        const next = prev.map((pc) => [...pc]);
        next[picker.pi][picker.si] = card;
        return next;
      });
    } else {
      setBoard((prev) => {
        const next = [...prev];
        next[picker.si] = card;
        return next;
      });
    }
    setPicker(null);
  }

  const allHoleCardsFilled = playerCards.every((pc) => pc[0] && pc[1]);
  const boardFilledCount = board.filter(Boolean).length;
  const boardContiguous = board.every((c, i) => c || board.slice(i).every((x) => !x));

  // Trigger non-blocking worker calculations
  useEffect(() => {
    const currentReq = ++reqId.current;

    if (!allHoleCardsFilled || !boardContiguous) {
      setCalcResult(null);
      setComputing(false);
      return;
    }

    setComputing(true);
    workerRef.current.postMessage({
      id: currentReq,
      players: playerCards,
      board: board.filter(Boolean),
      usedCards
    });
  }, [playerCards, board, allHoleCardsFilled, boardContiguous, usedCards]);

  return (
    <div
      style={{
        minHeight: 600,
        background: "radial-gradient(ellipse at 50% 0%, #123d2c 0%, #08211a 70%)",
        color: "#e8f3ec",
        fontFamily: "'Helvetica Neue', Arial, sans-serif",
        padding: 20,
        borderRadius: 12,
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 22, letterSpacing: 0.5 }}>Poker Equity Calculator</h2>
          <div style={{ fontSize: 12, color: "#8fb5a2", marginTop: 2 }}>
            Monte Carlo & Exact Enumeration Engine
          </div>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <label style={{ fontSize: 12, color: "#8fb5a2" }}>Players</label>
          <select
            value={numPlayers}
            onChange={(e) => resizePlayers(Number(e.target.value))}
            style={{ background: "#0f2e22", color: "#e8f3ec", border: "1px solid #2f5c46", borderRadius: 6, padding: "4px 8px" }}
          >
            {[2, 3, 4, 5, 6, 7, 8].map((n) => (
              <option key={n} value={n}>{n}</option>
            ))}
          </select>
          <button onClick={() => { setPlayerCards(Array.from({ length: numPlayers }, () => [null, null])); setBoard([null, null, null, null, null]); }} style={btnGhost}>
            Reset All
          </button>
        </div>
      </div>

      {/* Community Board */}
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8, marginBottom: 22, background: "rgba(0,0,0,0.2)", padding: 14, borderRadius: 10 }}>
        <div style={{ fontSize: 12, color: "#8fb5a2", fontWeight: 600 }}>COMMUNITY BOARD</div>
        <div style={{ display: "flex", gap: 10 }}>
          {board.map((c, i) => (
            <div key={i} onClick={() => setPicker({ type: "board", si: i })} style={{ cursor: "pointer" }}>
              <Card card={c} />
            </div>
          ))}
        </div>
        <button onClick={() => setBoard([null, null, null, null, null])} style={btnGhost}>Clear Board</button>
      </div>

      {/* Players Section */}
      <div style={{ display: "grid", gridTemplateColumns: `repeat(${Math.min(numPlayers, 4)}, 1fr)`, gap: 14 }}>
        {playerCards.map((pc, pi) => {
          const eq = calcResult?.equities?.[pi];
          const winPct = calcResult?.wins?.[pi];
          const tiePct = calcResult?.ties?.[pi];
          const dist = calcResult?.distributions?.[pi];

          return (
            <div
              key={pi}
              style={{
                background: "rgba(255,255,255,0.04)",
                border: `1px solid ${PLAYER_COLORS[pi % PLAYER_COLORS.length]}55`,
                borderRadius: 10,
                padding: 12,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <span style={{ fontSize: 13, color: PLAYER_COLORS[pi % PLAYER_COLORS.length], fontWeight: 700 }}>
                  Player {pi + 1}
                </span>
                <button
                  onClick={() => setRangeModalPi(pi)}
                  style={{ ...btnGhost, fontSize: 10, padding: "2px 6px" }}
                >
                  Matrix Grid
                </button>
              </div>

              {/* Cards */}
              <div style={{ display: "flex", gap: 8, marginBottom: 10 }}>
                {[0, 1].map((si) => (
                  <div key={si} onClick={() => setPicker({ type: "player", pi, si })} style={{ cursor: "pointer" }}>
                    <Card card={pc[si]} size="sm" />
                  </div>
                ))}
              </div>

              {/* Equity Stats */}
              <div style={{ fontSize: 14, fontWeight: 700, color: "#fff", marginBottom: 2 }}>
                Equity: {eq !== undefined ? `${eq.toFixed(1)}%` : "—"}
              </div>
              <div style={{ fontSize: 11, color: "#8fb5a2", marginBottom: 6 }}>
                Win: {winPct !== undefined ? `${winPct.toFixed(1)}%` : "—"} | Tie: {tiePct !== undefined ? `${tiePct.toFixed(1)}%` : "—"}
              </div>

              {/* Progress Bar */}
              <div style={{ height: 6, background: "rgba(255,255,255,0.08)", borderRadius: 3, overflow: "hidden", marginBottom: 12 }}>
                <div
                  style={{
                    height: "100%",
                    width: `${eq || 0}%`,
                    background: PLAYER_COLORS[pi % PLAYER_COLORS.length],
                    transition: "width 0.2s ease",
                  }}
                />
              </div>

              {/* Hand Type Outcome Distribution Chart */}
              {dist && (
                <div style={{ borderTop: "1px solid rgba(255,255,255,0.08)", paddingTop: 8 }}>
                  <div style={{ fontSize: 10, color: "#8fb5a2", marginBottom: 4, fontWeight: 600 }}>OUTCOME DISTRIBUTION</div>
                  {HAND_CATEGORY_NAMES.map((name, catIdx) => {
                    const pct = dist[catIdx];
                    if (pct < 0.1) return null;
                    return (
                      <div key={name} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 10, marginBottom: 2 }}>
                        <span style={{ width: 80, color: "#cfe8db", whiteSpace: "nowrap", overflow: "hidden" }}>{name}</span>
                        <div style={{ flex: 1, height: 4, background: "rgba(255,255,255,0.05)", borderRadius: 2 }}>
                          <div style={{ height: "100%", width: `${pct}%`, background: PLAYER_COLORS[pi % PLAYER_COLORS.length] }} />
                        </div>
                        <span style={{ width: 32, textAlign: "right", color: "#8fb5a2" }}>{pct.toFixed(0)}%</span>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Calculation Banner */}
      {computing && (
        <div style={{ marginTop: 16, fontSize: 12, color: "#e0b84f", textAlign: "center" }}>
          ⚡ Calculating equities across combinations in Web Worker thread...
        </div>
      )}

      {/* Modals */}
      {picker && (
        <CardPicker
          availableIds={availableIds}
          onPick={assignCard}
          onClose={() => setPicker(null)}
        />
      )}

      {rangeModalPi !== null && (
        <HandRangeModal
          onSelectCombo={(combo) => {
            setPlayerCards((prev) => {
              const next = prev.map((pc) => [...pc]);
              next[rangeModalPi] = combo;
              return next;
            });
            setRangeModalPi(null);
          }}
          onClose={() => setRangeModalPi(null)}
        />
      )}
    </div>
  );
}

const btnGhost = {
  background: "transparent",
  border: "1px solid #2f5c46",
  color: "#cfe8db",
  borderRadius: 6,
  padding: "4px 10px",
  fontSize: 12,
  cursor: "pointer",
};