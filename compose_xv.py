#!/usr/bin/env python3
"""Compose Contrapunctus XV — progressive layered electronic fugue.

Bach's Art of the Fugue subject, gradually layered across 12 voices.
Think Nils Frahm meets Bach: slow build, melodic variations accumulate,
voices enter one at a time, then thin back out.

Fugal techniques (inspired by Kerman's analysis):
  - Countersubject: complementary melody always accompanying the subject
  - Stretto: overlapping subject entries at progressively shorter gaps
  - Diminution: subject in halved note values (double speed)
  - Augmentation: subject in doubled note values (half speed)
  - Circle of fifths: Dm→Gm→C→F→Bb→Em7b5→A7→Dm harmonic skeleton
  - BACH motif: Bb-A-C-B♮ woven into climax sections

Voices:
  Lead:     main melody, subject statements
  Pad:      sustained chords, slow evolving
  Arp:      arpeggiated chord tones, sixteenths/thirty-seconds
  Sub Bass: root pedals, low sine wave
  Pluck:    staccato rapid-fire subject fragments (the star)
  Stab:     sparse off-beat chord accents
  Hi-Hat:   minimal rhythmic texture
  Kick:     gentle pulse, enters late
  Clap:     sparse accents
  FX Rise:  textural sweeps
  Acid:     subject in all four forms, staccato cycling
  Supersaw: thick sustained subject for climax

Structure (88 bars at ~110 BPM):
  m1-8:    A — Solo: Pad + Lead alone (subject + countersubject)
  m9-16:   B — Echo: Pluck enters, answer in new key
  m17-28:  C — Conversation: Acid joins, stretto begins (2-bar gap)
  m29-44:  D — Accumulation: diminution, rapid pluck fragments
  m45-64:  E — Density: stretto (1-bar gap), augmentation, BACH motif
  m65-76:  F — Thinning: voices drop out, circle of fifths unwinds
  m77-88:  G — Coda: Pad + Lead, final augmented subject, dissolves
"""

import mido

# ── Tick constants (110 BPM → tempo=545454) ──
T = 384
WHOLE    = T * 4
DOTTED_H = T * 3
HALF     = T * 2
DOTTED_Q = T + T // 2
QUARTER  = T
EIGHTH   = T // 2
SIXTEENTH = T // 4
THIRTYSECOND = T // 8
MEASURE  = T * 4
TEMPO    = 545454  # ~110 BPM

# ── Subject intervals ──
SUBJ = [7, -4, -3, -1, 1, 2, 1]
INV  = [-7, 4, 3, 1, -1, -2, -1]
ANS  = [5, -2, -3, -1, 1, 2, 1]
INV_ANS = [-5, 2, 3, 1, -1, -2, -1]

# ── Countersubject intervals ──
# Complementary to the subject: when subject leaps up, CS moves stepwise down.
# D E F A G F E D C# D (10 notes, free counterpoint style)
# Intervals: [+2, +1, +4, -2, -2, -1, -2, -1, +1]
CS_INTERVALS = [2, 1, 4, -2, -2, -1, -2, -1, 1]
CS_INV_INTERVALS = [-2, -1, -4, 2, 2, 1, 2, 1, -1]

# BACH motif: Bb-A-C-B♮
BACH_INT = [-1, 3, -1]

# Chord tones
CHORDS = {
    'm':   [0, 3, 7],
    'M':   [0, 4, 7],
    '7':   [0, 4, 7, 10],
    'm7':  [0, 3, 7, 10],
    'dim': [0, 3, 6],
    'dim7': [0, 3, 6, 9],
}

# ── Circle-of-fifths harmonic plan ──
# Each entry = (root_pitch_class, quality)
# Progression: Dm → Gm → C7 → FM → BbM → Em7b5(dim) → A7 → Dm
CIRCLE_OF_5THS = [
    (2, 'm'),    # Dm
    (7, 'm'),    # Gm
    (0, '7'),    # C7
    (5, 'M'),    # FM
    (10, 'M'),   # BbM
    (4, 'dim'),  # Edim (vii°)
    (9, '7'),    # A7
    (2, 'm'),    # Dm (home)
]

def _h(bars, chords):
    """Expand a chord list to half-bar granularity for N bars."""
    out = []
    per_bar = len(chords)
    if per_bar == 1:
        return chords * (bars * 2)
    total_halves = bars * 2
    per_chord = total_halves // per_bar
    for c in chords:
        out.extend([c] * per_chord)
    while len(out) < total_halves:
        out.append(chords[-1])
    return out[:total_halves]

# Section A: m1-8 — Dm pedal
H_A = _h(8, [(2,'m')])

# Section B: m9-16 — Dm with motion to answer key (Am)
H_B = _h(4, [(2,'m')]) + _h(2, [(9,'7')]) + _h(2, [(2,'m')])

# Section C: m17-28 — Circle of fifths begins
H_C = (
    _h(3, [(2,'m')]) +         # m17-19
    _h(3, [(7,'m')]) +         # m20-22
    _h(3, [(0,'7')]) +         # m23-25
    _h(3, [(5,'M')])           # m26-28
)

# Section D: m29-44 — Full circle of fifths
H_D = (
    _h(4, [(2,'m'), (7,'m')]) +       # m29-32
    _h(4, [(0,'7'), (5,'M')]) +       # m33-36
    _h(4, [(10,'M'), (4,'dim')]) +    # m37-40
    _h(4, [(9,'7'), (2,'m')])         # m41-44
)

# Section E: m45-64 — Circle repeats with more tension
H_E = (
    _h(4, [(2,'m'), (7,'m')]) +       # m45-48
    _h(4, [(0,'7'), (5,'M')]) +       # m49-52
    _h(4, [(10,'M'), (4,'dim')]) +    # m53-56
    _h(4, [(9,'7'), (2,'m')]) +       # m57-60
    _h(4, [(2,'m'), (9,'7')])         # m61-64
)

# Section F: m65-76 — Unwinding back home
H_F = (
    _h(4, [(9,'7'), (7,'m')]) +       # m65-68
    _h(4, [(5,'M'), (0,'7')]) +       # m69-72
    _h(4, [(9,'7'), (2,'m')])         # m73-76
)

# Section G: m77-88 — Dm pedal to end
H_G = _h(12, [(2,'m')])

ALL_H = H_A + H_B + H_C + H_D + H_E + H_F + H_G

def harm(tick):
    idx = tick // HALF
    idx = max(0, min(idx, len(ALL_H) - 1))
    return ALL_H[idx]

def chord_pitches(root_pc, qual, base_oct_pitch):
    """Get chord tones near a base pitch."""
    offsets = CHORDS[qual]
    base = base_oct_pitch
    while (base % 12) != root_pc:
        base += 1
    return [base + o for o in offsets]


class V:
    """Voice builder."""
    def __init__(self, ch):
        self.ch = ch
        self.notes = []
        self.c = 0  # cursor

    def n(self, pitch, dur, vel=80):
        self.notes.append((self.c, pitch, dur, vel))
        self.c += dur

    def r(self, dur):
        self.c += dur

    def go(self, tick):
        self.c = tick

    def mel(self, pairs, vel=80):
        for p, d in pairs:
            self.n(p, d, vel)

    def subj(self, start, intervals, rhythm, vel=80):
        """Play subject from starting pitch with given intervals and rhythm."""
        p = start
        self.n(p, rhythm[0], vel)
        for i, iv in enumerate(intervals):
            p += iv
            self.n(p, rhythm[min(i+1, len(rhythm)-1)], vel)

    def countersubj(self, start, rhythm, vel=70):
        """Play countersubject from starting pitch."""
        self.subj(start, CS_INTERVALS, rhythm, vel)

    def bach_motif(self, start_pitch, dur, vel=75):
        """Play the BACH motif (Bb-A-C-B♮ shape) from any starting pitch."""
        p = start_pitch
        self.n(p, dur, vel)
        for iv in BACH_INT:
            p += iv
            self.n(p, dur, vel)

    def subj_diminution(self, start, intervals, rhythm, vel=80):
        """Subject in diminution (halved durations → double speed)."""
        dim_rhythm = [max(THIRTYSECOND, d // 2) for d in rhythm]
        self.subj(start, intervals, dim_rhythm, vel)

    def subj_augmentation(self, start, intervals, rhythm, vel=80):
        """Subject in augmentation (doubled durations → half speed)."""
        aug_rhythm = [d * 2 for d in rhythm]
        self.subj(start, intervals, aug_rhythm, vel)


def compose():
    # 12 voices: channels 0-11
    lead     = V(0)
    pad      = V(1)
    arp      = V(2)
    sub      = V(3)
    pluck    = V(4)
    stab     = V(5)
    hihat    = V(6)
    kick     = V(7)
    clap     = V(8)
    fx       = V(9)
    acid     = V(10)
    ssaw     = V(11)

    # Rhythm templates
    R_BASIC  = [HALF, HALF, HALF, HALF, HALF, QUARTER, QUARTER, HALF]
    R_DRIVE  = [QUARTER, QUARTER, QUARTER, QUARTER, QUARTER, EIGHTH, EIGHTH, HALF]
    R_SHORT  = [EIGHTH, EIGHTH, EIGHTH, EIGHTH, EIGHTH, SIXTEENTH, SIXTEENTH, QUARTER]
    R_AUG    = [WHOLE, WHOLE, WHOLE, WHOLE, WHOLE, HALF, HALF, WHOLE]
    R_DOTTED = [DOTTED_Q, EIGHTH, DOTTED_Q, EIGHTH, HALF, EIGHTH, EIGHTH, DOTTED_Q]
    R_PLUCK  = [SIXTEENTH] * 8
    R_CS     = [QUARTER, EIGHTH, EIGHTH, QUARTER, QUARTER, QUARTER, EIGHTH, EIGHTH, QUARTER, QUARTER]

    # ── Helpers ──
    def pad_chord(tick, bars, vel=45):
        rpc, qual = harm(tick)
        for p in chord_pitches(rpc, qual, 55):
            pad.notes.append((tick, p, bars * MEASURE, vel))
        for p in chord_pitches(rpc, qual, 67):
            pad.notes.append((tick, p, bars * MEASURE, int(vel * 0.7)))

    def arp_bar(tick, dur=SIXTEENTH, vel=55):
        rpc, qual = harm(tick)
        base = 62
        while (base % 12) != rpc:
            base += 1
        if base > 72:
            base -= 12
        pts = chord_pitches(rpc, qual, base)
        pts_ext = pts + [p + 12 for p in pts] + [p + 24 for p in pts[:2]]
        notes_per_bar = MEASURE // dur
        arp.go(tick)
        for i in range(notes_per_bar):
            arp.n(pts_ext[i % len(pts_ext)], dur, vel)

    def sub_bar(tick, dur=HALF, vel=80):
        rpc, _ = harm(tick)
        bass_p = 26 + rpc
        if bass_p < 28:
            bass_p += 12
        notes_per_bar = MEASURE // dur
        sub.go(tick)
        for _ in range(notes_per_bar):
            sub.n(bass_p, dur, vel)

    def kick_bar(tick, vel=75, pattern='half'):
        kick.go(tick)
        if pattern == 'half':
            kick.n(36, EIGHTH, vel)
            kick.r(HALF - EIGHTH)
            kick.n(36, EIGHTH, int(vel * 0.7))
            kick.r(HALF - EIGHTH)
        elif pattern == 'quarter':
            for _ in range(4):
                kick.n(36, EIGHTH, vel)
                kick.r(QUARTER - EIGHTH)

    def hihat_bar(tick, vel=50, density='quarter'):
        if density == 'quarter':
            for beat in range(4):
                hihat.go(tick + beat * QUARTER)
                hihat.n(80, QUARTER, vel)
        elif density == 'eighth':
            for e in range(8):
                hihat.go(tick + e * EIGHTH)
                v = vel if e % 2 == 0 else int(vel * 1.2)
                hihat.n(80, EIGHTH, v)

    def clap_bar(tick, vel=65):
        clap.go(tick + 2 * QUARTER)
        clap.n(74, EIGHTH, vel)

    def stab_bar(tick, vel=60):
        rpc, qual = harm(tick)
        pts = chord_pitches(rpc, qual, 62)
        for beat_off in [EIGHTH, QUARTER + EIGHTH, 2*QUARTER + EIGHTH, 3*QUARTER + EIGHTH]:
            for p in pts:
                stab.notes.append((tick + beat_off, p, EIGHTH, vel))

    # ════════════════════════════════════════════════
    # A: SOLO (m1-8) — Pad holds Dm, Lead plays subject + countersubject
    # ════════════════════════════════════════════════

    # Pad: sustained Dm chord across 8 bars
    pad_chord(0, 8, vel=40)

    # Lead: subject in unhurried rhythm
    lead.go(MEASURE)  # start at m2 for breathing room
    lead.subj(62, SUBJ, R_BASIC, vel=75)
    # Countersubject follows immediately — the "companion melody"
    lead.r(QUARTER)
    lead.countersubj(64, R_CS, vel=65)
    # Rest, then answer
    lead.r(MEASURE)
    lead.subj(69, ANS, R_BASIC, vel=70)

    # FX: gentle texture sweep m5-8
    fx.go(4 * MEASURE)
    for i in range(16):
        p = 55 + i
        fx.n(p, QUARTER, 25 + i)

    # ════════════════════════════════════════════════
    # B: ECHO (m9-16) — Lead repeats, Pluck enters with staccato subject
    # ════════════════════════════════════════════════
    t9 = 8 * MEASURE

    # Pad: evolving chords
    pad_chord(t9, 4, vel=45)
    pad_chord(t9 + 4 * MEASURE, 4, vel=50)

    # Lead: subject in driving rhythm + countersubject
    lead.go(t9)
    lead.subj(62, SUBJ, R_DRIVE, vel=80)
    lead.countersubj(64, R_CS, vel=68)
    lead.subj(69, ANS, R_DRIVE, vel=75)

    # Pluck: enters! Staccato subject echo — the star
    pluck.go(t9 + 2 * MEASURE)  # m11
    pluck.subj(74, SUBJ, R_PLUCK, vel=60)
    pluck.r(MEASURE)
    pluck.subj(69, ANS, R_PLUCK, vel=55)
    pluck.r(MEASURE)
    # Descending repetitions
    pluck.subj(71, SUBJ, R_PLUCK, vel=62)
    pluck.r(HALF)
    pluck.subj(66, INV, R_PLUCK, vel=58)

    # Sub bass: enters with gentle root pedal
    for bar in range(8, 16):
        sub_bar(bar * MEASURE, dur=WHOLE, vel=65)

    # ════════════════════════════════════════════════
    # C: CONVERSATION (m17-28) — Acid joins, STRETTO begins (2-bar gap)
    # Circle of fifths starts: Dm → Gm → C7 → FM
    # ════════════════════════════════════════════════
    t17 = 16 * MEASURE

    # Pad: continuous, following circle of fifths
    for group_start in range(16, 28, 3):
        bars = min(3, 28 - group_start)
        pad_chord(group_start * MEASURE, bars, vel=48)

    # Lead: subject + countersubject, with stretto entries
    # STRETTO: Lead starts subject, then Acid enters 2 bars later
    lead.go(t17)
    lead.subj(74, SUBJ, R_DRIVE, vel=80)
    # Countersubject accompanies
    lead.countersubj(76, R_CS, vel=68)
    lead.r(MEASURE)
    lead.subj(69, ANS, R_DOTTED, vel=78)
    # Second stretto pair
    lead.r(HALF)
    lead.subj(62, INV, R_DRIVE, vel=75)
    lead.countersubj(60, [EIGHTH]*10, vel=65)

    # Acid: enters! STRETTO partner — enters 2 bars after lead
    acid.go(t17 + 2 * MEASURE)  # stretto gap = 2 bars
    acid.subj(50, SUBJ, R_SHORT, vel=70)
    acid.subj(57, INV, R_SHORT, vel=65)
    acid.r(HALF)
    acid.subj(45, ANS, R_SHORT, vel=72)
    # Countersubject in acid's low register
    acid.countersubj(52, [SIXTEENTH]*10, vel=60)
    acid.subj(50, INV_ANS, R_SHORT, vel=68)
    acid.r(MEASURE)
    acid.subj(52, SUBJ, R_DOTTED, vel=70)

    # Pluck: call and response with acid — DIMINUTION introduced
    pluck.go(t17 + 2 * MEASURE)  # m19
    pluck.subj(74, SUBJ, R_PLUCK, vel=65)
    pluck.r(MEASURE)
    # DIMINUTION: subject at double speed!
    pluck.subj_diminution(69, INV, R_PLUCK, vel=60)
    pluck.r(HALF)
    pluck.subj(71, ANS, R_PLUCK, vel=63)
    pluck.r(HALF)
    pluck.subj(76, SUBJ, R_PLUCK, vel=67)
    # Rapid descending cascade
    for i in range(3):
        pluck.subj(74 - i * 3, SUBJ, R_PLUCK, vel=60 + i * 3)

    # Arp: gentle sixteenths, enters at m21
    for bar in range(20, 28):
        arp_bar(bar * MEASURE, dur=SIXTEENTH, vel=45 + (bar - 20) * 2)

    # Kick: enters softly at m21
    for bar in range(20, 28):
        kick_bar(bar * MEASURE, vel=55 + (bar - 20), pattern='half')

    # Sub bass: continuous
    for bar in range(16, 28):
        sub_bar(bar * MEASURE, dur=HALF, vel=70)

    # FX: subtle texture m25-28
    fx.go(24 * MEASURE)
    for i in range(24):
        fx.n(58 + (i * 20) // 24, QUARTER, 20 + i)

    # ════════════════════════════════════════════════
    # D: ACCUMULATION (m29-44) — DIMINUTION, rapid pluck, full circle of 5ths
    # All melodic voices active. Stretto tightens to 1.5-bar gap.
    # ════════════════════════════════════════════════
    t29 = 28 * MEASURE

    # Pad: richer voicings following circle of fifths
    for group_start in range(28, 44, 4):
        tick = group_start * MEASURE
        rpc, qual = harm(tick)
        for octave_base in [48, 55, 67]:
            for p in chord_pitches(rpc, qual, octave_base):
                pad.notes.append((tick, p, 4 * MEASURE, 42))

    # Lead: subject in multiple registers with countersubjects
    lead.go(t29)
    lead.subj(74, SUBJ, R_DRIVE, vel=82)
    lead.countersubj(76, R_CS, vel=70)
    # STRETTO: 1.5-bar gap — lead starts new subject before countersubject finishes
    lead.go(t29 + int(1.5 * MEASURE))
    lead.subj(69, INV, R_DRIVE, vel=78)
    lead.r(MEASURE)
    lead.subj(81, SUBJ, R_SHORT, vel=80)
    lead.countersubj(83, [SIXTEENTH]*10, vel=68)
    lead.subj(74, ANS, R_DRIVE, vel=76)
    # Higher register
    lead.r(2 * MEASURE)
    lead.subj(86, SUBJ, R_DRIVE, vel=75)
    lead.countersubj(88, R_CS, vel=65)

    # Pluck: THE STAR — rapid DIMINUTION cascades
    pluck.go(t29)
    # Cascade 1: diminution descending
    for i in range(6):
        pluck.subj_diminution(76 - i * 3, SUBJ, R_PLUCK, vel=65 + i * 2)
    # Cascade 2: ascending inversions in diminution
    pluck.r(MEASURE)
    for i in range(4):
        pluck.subj_diminution(62 + i * 4, INV, R_PLUCK, vel=68 + i * 2)
    # Cascade 3: mixed forms with countersubject fragments
    pluck.r(HALF)
    for i in range(5):
        form = [SUBJ, ANS, INV, INV_ANS, SUBJ][i]
        pluck.subj(74 - i * 2, form, R_PLUCK, vel=70)

    # Acid: cycling through all forms + countersubject interleaved
    acid.go(t29)
    acid.subj(50, SUBJ, R_SHORT, vel=75)
    acid.countersubj(52, [SIXTEENTH]*10, vel=62)
    acid.subj(57, INV, R_SHORT, vel=72)
    acid.subj(45, ANS, R_SHORT, vel=74)
    acid.subj(52, INV_ANS, R_SHORT, vel=70)
    # Second round at different pitch levels (circle of fifths!)
    acid.subj(55, SUBJ, R_DOTTED, vel=73)  # on Gm
    acid.countersubj(57, [SIXTEENTH]*10, vel=60)
    acid.subj(48, INV, R_SHORT, vel=70)
    acid.subj(50, ANS, R_DOTTED, vel=72)

    # Supersaw: enters with AUGMENTED subject (double-length notes)
    ssaw.go(t29 + 4 * MEASURE)  # m33
    ssaw.subj_augmentation(62, SUBJ, R_BASIC, vel=55)

    # Stab: sparse off-beat color
    for bar in range(32, 44):
        if bar % 2 == 0:
            stab_bar(bar * MEASURE, vel=50 + (bar - 32))

    # Arp: sixteenths throughout
    for bar in range(28, 44):
        arp_bar(bar * MEASURE, dur=SIXTEENTH, vel=50 + (bar - 28))

    # Drums: kick + hihat enter, build slowly
    for bar in range(28, 44):
        intensity = (bar - 28) / 16
        kick_bar(bar * MEASURE, vel=int(60 + 20 * intensity), pattern='half')
        if bar >= 32:
            hihat_bar(bar * MEASURE, vel=int(35 + 20 * intensity), density='quarter')
        if bar >= 36:
            clap_bar(bar * MEASURE, vel=int(45 + 15 * intensity))

    # Sub: continuous
    for bar in range(28, 44):
        sub_bar(bar * MEASURE, dur=HALF, vel=75)

    # ════════════════════════════════════════════════
    # E: DENSITY (m45-64) — STRETTO, AUGMENTATION, BACH motif, TUTTI
    # Melodic layering with controlled density. Circle of fifths repeats.
    # m57-60: TUTTI — all 12 voices play subject in octaves (solid color moment!)
    # ════════════════════════════════════════════════
    t45 = 44 * MEASURE
    t_tutti = t45 + 12 * MEASURE  # m57 — the big tutti moment

    # Pad: sustained chords (fewer octaves = less mud)
    for group_start in range(44, 56, 4):
        tick = group_start * MEASURE
        rpc, qual = harm(tick)
        for octave_base in [55, 67]:
            for p in chord_pitches(rpc, qual, octave_base):
                pad.notes.append((tick, p, 4 * MEASURE, 35))

    # Lead: TIGHT STRETTO — 1-bar gap between entries!
    lead.go(t45)
    lead.subj(74, SUBJ, R_DRIVE, vel=82)
    # Stretto: next entry just 1 bar later
    lead.go(t45 + MEASURE)
    lead.subj(81, INV, R_DRIVE, vel=78)
    # Counter-stretto
    lead.go(t45 + 2 * MEASURE)
    lead.subj(69, ANS, R_DRIVE, vel=80)
    lead.countersubj(71, R_CS, vel=65)
    # BACH motif woven in at climax (m49-50)
    lead.go(t45 + 4 * MEASURE)
    lead.bach_motif(70, QUARTER, vel=82)  # Bb-A-C-B♮
    lead.r(HALF)
    lead.bach_motif(82, QUARTER, vel=78)  # higher octave
    # More stretto
    lead.r(MEASURE)
    lead.subj(74, SUBJ, R_SHORT, vel=76)
    # 1-bar gap stretto again
    lead.go(t45 + 8 * MEASURE)
    lead.subj(81, SUBJ, R_DRIVE, vel=75)
    lead.go(t45 + 9 * MEASURE)
    lead.subj(69, INV_ANS, R_DRIVE, vel=72)

    # Pluck: cascading but fewer rounds (less clutter)
    pluck.go(t45)
    # Cascade 1: diminution descending (6 rounds, not 8)
    for i in range(6):
        pluck.subj_diminution(79 - i * 3, SUBJ, R_PLUCK, vel=65)
    # Ascending cascade with inversions
    pluck.r(MEASURE)
    for i in range(4):
        pluck.subj_diminution(62 + i * 4, INV, R_PLUCK, vel=62)
    # BACH motif as rapid pluck ornament
    pluck.r(HALF)
    for octave in range(3):
        pluck.bach_motif(62 + octave * 12, SIXTEENTH, vel=60)
        pluck.r(EIGHTH)

    # Acid: cycling but with fewer countersubjects (less density)
    acid.go(t45)
    for rep in range(6):
        form = [SUBJ, INV, ANS, INV_ANS][rep % 4]
        start_p = 50 + (rep % 3) * 3
        acid.subj(start_p, form, R_SHORT, vel=68 + rep)
    # BACH motif in acid register
    acid.bach_motif(46, EIGHTH, vel=65)
    acid.r(QUARTER)
    acid.bach_motif(58, EIGHTH, vel=68)

    # Supersaw: AUGMENTED subject — majestic, slow
    ssaw.go(t45)
    ssaw.subj_augmentation(74, SUBJ, R_DRIVE, vel=60)
    # Second entry in inversion
    ssaw.go(t45 + 8 * MEASURE)
    ssaw.subj_augmentation(69, INV, R_DRIVE, vel=58)

    # Stab: every other bar (not every bar)
    for bar in range(44, 56):
        if bar % 2 == 0:
            stab_bar(bar * MEASURE, vel=45)

    # Arp: SIXTEENTHS not thirty-seconds (less ear fatigue)
    for bar in range(44, 56):
        arp_bar(bar * MEASURE, dur=SIXTEENTH, vel=42)

    # Drums: half-note kick (not quarter), lighter
    for bar in range(44, 56):
        kick_bar(bar * MEASURE, vel=65, pattern='half')
        hihat_bar(bar * MEASURE, vel=38, density='quarter')
        if bar % 2 == 0:
            clap_bar(bar * MEASURE, vel=48)

    # Sub: HALF notes (not quarter — less sub pulsing)
    for bar in range(44, 56):
        sub_bar(bar * MEASURE, dur=HALF, vel=72)

    # FX: textural sweep m53-56
    fx.go(t45 + 8 * MEASURE)
    for i in range(16):
        p = 50 + (i * 25) // 16
        fx.n(p, EIGHTH, 22 + i * 2)

    # ── TUTTI (m57-60) — ALL 12 VOICES PLAY SUBJECT IN OCTAVES ──
    # This creates the "all solid color" moment across every lane.
    # Each voice plays the subject at its natural register.
    tutti_vel = 75
    R_TUTTI = [HALF, HALF, HALF, HALF, HALF, QUARTER, QUARTER, HALF]

    # Melodic voices: subject in different octaves
    lead.go(t_tutti)
    lead.subj(74, SUBJ, R_TUTTI, vel=tutti_vel)     # D5 range

    pad.go(t_tutti)
    # Pad plays subject as sustained notes instead of chords
    p = 62  # D4
    pad.n(p, R_TUTTI[0], tutti_vel - 10)
    for idx, iv in enumerate(SUBJ):
        p += iv
        pad.n(p, R_TUTTI[min(idx+1, len(R_TUTTI)-1)], tutti_vel - 10)

    arp.go(t_tutti)
    arp.subj(86, SUBJ, R_TUTTI, vel=tutti_vel - 8)  # D6 range

    sub.go(t_tutti)
    sub.subj(38, SUBJ, R_TUTTI, vel=tutti_vel - 5)  # D2 range

    pluck.go(t_tutti)
    pluck.subj(74, SUBJ, R_PLUCK, vel=tutti_vel)    # rapid version
    pluck.subj(69, ANS, R_PLUCK, vel=tutti_vel - 5)
    pluck.subj(74, SUBJ, R_PLUCK, vel=tutti_vel)
    pluck.subj(81, SUBJ, R_PLUCK, vel=tutti_vel - 5)

    stab.go(t_tutti)
    # Stab plays short chord stabs on subject pitches
    p = 62
    stab.n(p, QUARTER, tutti_vel - 15)
    for idx, iv in enumerate(SUBJ):
        p += iv
        stab.n(p, QUARTER, tutti_vel - 15)

    hihat.go(t_tutti)
    # Hi-hat: steady eighths for 4 bars
    for _ in range(32):
        hihat.n(80, EIGHTH, tutti_vel - 30)

    kick.go(t_tutti)
    # Kick: on each subject note arrival
    kick.n(36, QUARTER, tutti_vel - 10)
    for _ in range(7):
        kick.r(HALF - QUARTER)
        kick.n(36, QUARTER, tutti_vel - 15)

    clap.go(t_tutti + 2 * QUARTER)
    # Clap: beat 3 of each bar
    for bar in range(4):
        clap.n(74, EIGHTH, tutti_vel - 20)
        clap.r(MEASURE - EIGHTH)

    fx.go(t_tutti)
    fx.subj(62, SUBJ, R_TUTTI, vel=tutti_vel - 25)  # ghost of subject

    acid.go(t_tutti)
    acid.subj(50, SUBJ, R_TUTTI, vel=tutti_vel - 5)  # low subject

    ssaw.go(t_tutti)
    ssaw.subj(62, SUBJ, R_TUTTI, vel=tutti_vel - 8)  # thick subject

    # ── Post-tutti (m61-64): brief afterglow, winding down ──
    t61 = t_tutti + 4 * MEASURE

    # Pad returns to chords
    pad_chord(t61, 4, vel=35)

    # Lead: BACH at climax peak, then one more subject
    lead.go(t61)
    lead.bach_motif(70, HALF, vel=75)
    lead.r(QUARTER)
    lead.subj(62, SUBJ, R_BASIC, vel=70)

    # Supersaw: BACH motif — powerful
    ssaw.go(t61)
    ssaw.bach_motif(70, WHOLE, vel=60)

    # Lighter texture
    for bar in range(60, 64):
        arp_bar(bar * MEASURE, dur=SIXTEENTH, vel=35)
        kick_bar(bar * MEASURE, vel=55, pattern='half')
        sub_bar(bar * MEASURE, dur=HALF, vel=65)

    # ════════════════════════════════════════════════
    # F: THINNING (m65-76) — Voices drop out gradually
    # Circle of fifths unwinds (A7 → Gm → F → C → A7 → Dm)
    # ════════════════════════════════════════════════
    t65 = 64 * MEASURE

    # Pad: gentle, thinning
    pad_chord(t65, 4, vel=40)
    pad_chord(t65 + 4 * MEASURE, 4, vel=32)
    pad_chord(t65 + 8 * MEASURE, 4, vel=25)

    # Lead: final AUGMENTED subject, then fading statements
    lead.go(t65)
    lead.subj_augmentation(74, SUBJ, R_BASIC, vel=70)
    # Countersubject as farewell
    lead.countersubj(76, [HALF]*10, vel=55)
    # Small echo at end
    lead.go(t65 + 8 * MEASURE)
    lead.subj(62, SUBJ, R_BASIC, vel=50)
    # Final BACH motif, slow and quiet
    lead.r(QUARTER)
    lead.bach_motif(70, HALF, vel=45)

    # Pluck: continues but fading
    pluck.go(t65)
    for i in range(4):
        pluck.subj(74 - i * 3, SUBJ, R_PLUCK, vel=60 - i * 8)
    pluck.r(2 * MEASURE)
    for i in range(3):
        pluck.subj(69 - i * 4, INV, R_PLUCK, vel=40 - i * 5)

    # Acid: fading subject statements with countersubject
    acid.go(t65)
    acid.subj(50, SUBJ, R_SHORT, vel=60)
    acid.countersubj(52, [EIGHTH]*10, vel=45)
    acid.subj(57, INV, R_DOTTED, vel=50)
    acid.r(2 * MEASURE)
    acid.subj(50, SUBJ, R_BASIC, vel=40)

    # Arp: slowing down
    for bar in range(64, 72):
        fade = 1.0 - (bar - 64) / 8
        arp_bar(bar * MEASURE, dur=SIXTEENTH, vel=int(45 * fade))

    # Supersaw: drops out after one last statement
    ssaw.go(t65)
    ssaw.subj(62, SUBJ, R_BASIC, vel=50)

    # Drums: thinning
    for bar in range(64, 72):
        fade = 1.0 - (bar - 64) / 8
        kick_bar(bar * MEASURE, vel=int(60 * fade), pattern='half')
        if bar < 68:
            hihat_bar(bar * MEASURE, vel=int(35 * fade), density='quarter')
        if bar < 66:
            clap_bar(bar * MEASURE, vel=int(40 * fade))

    # Sub: fading
    for bar in range(64, 72):
        fade = 1.0 - (bar - 64) / 8
        sub_bar(bar * MEASURE, dur=WHOLE, vel=int(65 * fade))

    # ════════════════════════════════════════════════
    # G: CODA (m77-88) — Pad + Lead, dissolving
    # Final augmented subject, BACH motif as last word
    # ════════════════════════════════════════════════
    t77 = 76 * MEASURE

    # Pad: final Dm, slowly fading
    for p in chord_pitches(2, 'm', 55):
        pad.notes.append((t77, p, 12 * MEASURE, 30))
    for p in chord_pitches(2, 'm', 67):
        pad.notes.append((t77, p, 12 * MEASURE, 20))

    # Lead: subject one last time, augmented (very slow)
    lead.go(t77 + MEASURE)
    lead.subj_augmentation(62, SUBJ, R_BASIC, vel=45)
    # Final BACH motif — the last word
    lead.go(t77 + 9 * MEASURE)
    lead.bach_motif(70, WHOLE, vel=35)  # Bb-A-C-B♮ in whole notes

    # Sub: final D pedal
    sub.go(t77)
    sub.n(38, 6 * MEASURE, 45)
    sub.n(26, 6 * MEASURE, 30)  # sub octave, dying away

    # Acid: ghost of the subject + BACH
    acid.go(t77 + 2 * MEASURE)
    acid.subj(50, SUBJ, R_BASIC, vel=30)
    acid.r(MEASURE)
    acid.bach_motif(46, HALF, vel=25)  # final whispered BACH

    # Pluck: one last tiny echo
    pluck.go(t77 + 4 * MEASURE)
    pluck.subj(74, SUBJ, R_PLUCK, vel=25)

    return [lead, pad, arp, sub, pluck, stab, hihat, kick, clap, fx, acid, ssaw]


def voices_to_midi(voices, path):
    mid = mido.MidiFile(type=1, ticks_per_beat=T)

    meta = mido.MidiTrack()
    meta.append(mido.MetaMessage('time_signature', numerator=4, denominator=4,
                                  clocks_per_click=96, notated_32nd_notes_per_beat=8, time=0))
    meta.append(mido.MetaMessage('set_tempo', tempo=TEMPO, time=0))
    meta.append(mido.MetaMessage('key_signature', key='Dm', time=0))
    meta.append(mido.MetaMessage('end_of_track', time=0))
    mid.tracks.append(meta)

    names = ['Lead', 'Pad', 'Arp', 'Sub Bass', 'Pluck', 'Stab',
             'Hi-Hat', 'Kick', 'Clap', 'FX Rise', 'Acid', 'Supersaw']

    for voice, name in zip(voices, names):
        track = mido.MidiTrack()
        track.append(mido.MetaMessage('track_name', name=name, time=0))
        track.append(mido.MetaMessage('key_signature', key='Dm', time=0))

        events = []
        for (t, p, d, v) in voice.notes:
            events.append((t, 'on', p, v))
            events.append((t + d, 'off', p, 0))
        events.sort(key=lambda e: (e[0], 0 if e[1] == 'off' else 1))

        prev = 0
        for (t, typ, p, v) in events:
            delta = t - prev
            if typ == 'on':
                track.append(mido.Message('note_on', channel=voice.ch, note=p, velocity=v, time=delta))
            else:
                track.append(mido.Message('note_off', channel=voice.ch, note=p, velocity=0, time=delta))
            prev = t

        track.append(mido.MetaMessage('end_of_track', time=0))
        mid.tracks.append(track)

    mid.save(path)
    total = sum(len(v.notes) for v in voices)
    max_t = max(max(t+d for t,_,d,_ in v.notes) for v in voices if v.notes)
    print(f'Wrote {path}')
    print(f'  {total} notes, {max_t // MEASURE} measures, {max_t / T * (TEMPO / 1e6):.1f}s')


if __name__ == '__main__':
    voices = compose()
    voices_to_midi(voices, '/Users/benjaminchartoff/Projects/airt-of-the-fugue/contrapunctus_xv.mid')
