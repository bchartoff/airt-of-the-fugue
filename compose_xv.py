#!/usr/bin/env python3
"""Compose Contrapunctus XV — EDM fugue with 12 voices.

Bach's Art of the Fugue subject gets the full electronic treatment:
  Lead:     main melody, subject statements with filter-sweep feel
  Pad:      sustained chords, slow attacks
  Arp:      sixteenth-note arpeggiated patterns
  Sub Bass: 808-style sub bass, octave drops
  Pluck:    staccato plucked subject fragments
  Stab:     chord stabs on off-beats
  Hi-Hat:   rhythmic patterns on high pitches (pitched percussion)
  Kick:     four-on-the-floor low bass drum pattern
  Clap:     snare/clap hits
  FX Rise:  risers and sweeps before drops
  Acid:     303-style acid line, slides and resonance
  Supersaw: thick unison lead for hooks

Structure (128 bars at ~130 BPM):
  m1-8:    Intro — kick + hi-hat + sub bass build
  m9-24:   Build 1 — subject enters in Lead, Arp joins
  m25-32:  DROP 1 — full blast, all voices
  m33-48:  Breakdown — stripped back, subject in Pad + Acid
  m49-56:  Build 2 — rising FX, stretto entries
  m57-72:  DROP 2 — maximum energy, supersaw + subject stretto
  m73-80:  Breakdown 2 — half-time feel
  m81-96:  DROP 3 / FINALE — augmented subject in Sub Bass, everything layered
  m97-104: Outro — gradual strip-down
"""

import mido

# ── Tick constants (130 BPM → tempo=461538) ──
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
TEMPO    = 461538  # ~130 BPM

# Subject intervals
SUBJ = [7, -4, -3, -1, 1, 2, 1]
INV  = [-7, 4, 3, 1, -1, -2, -1]
ANS  = [5, -2, -3, -1, 1, 2, 1]
INV_ANS = [-5, 2, 3, 1, -1, -2, -1]

# Chord tones
CHORDS = {
    'm':   [0, 3, 7],
    'M':   [0, 4, 7],
    '7':   [0, 4, 7, 10],
    'dim': [0, 3, 6],
}

# ── Harmonic plan (per half-bar, 2 beats each) ──
# Dm-centered EDM progression with some borrowed chords
H_INTRO = [(2,'m')] * 8 + [(7,'m')] * 4 + [(9,'7')] * 4  # 8 bars
H_BUILD1 = [
    (2,'m'),(2,'m'), (10,'M'),(10,'M'), (0,'7'),(0,'7'), (9,'7'),(9,'7'),  # m9-12
    (2,'m'),(2,'m'), (7,'m'),(7,'m'), (10,'M'),(10,'M'), (9,'7'),(9,'7'),  # m13-16
    (2,'m'),(2,'m'), (5,'M'),(5,'M'), (10,'M'),(10,'M'), (9,'7'),(9,'7'),  # m17-20
    (2,'m'),(2,'m'), (7,'m'),(7,'m'), (9,'7'),(9,'7'), (2,'m'),(2,'m'),    # m21-24
]
H_DROP1 = [
    (2,'m'),(2,'m'), (10,'M'),(10,'M'), (0,'7'),(0,'7'), (9,'7'),(9,'7'),  # m25-28
    (2,'m'),(2,'m'), (7,'m'),(7,'m'), (10,'M'),(9,'7'), (2,'m'),(2,'m'),   # m29-32
]
H_BREAK = [
    (2,'m'),(2,'m'), (5,'M'),(5,'M'), (7,'m'),(7,'m'), (9,'7'),(9,'7'),    # m33-36
    (2,'m'),(2,'m'), (10,'M'),(10,'M'), (0,'7'),(0,'7'), (9,'7'),(9,'7'),  # m37-40
    (2,'m'),(2,'m'), (7,'m'),(7,'m'), (10,'M'),(10,'M'), (9,'7'),(9,'7'),  # m41-44
    (2,'m'),(2,'m'), (7,'m'),(7,'m'), (9,'7'),(9,'7'), (2,'m'),(2,'m'),    # m45-48
]
H_BUILD2 = [
    (2,'m'),(2,'m'), (10,'M'),(10,'M'), (7,'m'),(7,'m'), (9,'7'),(9,'7'),  # m49-52
    (2,'m'),(2,'m'), (10,'M'),(10,'M'), (9,'7'),(9,'7'), (9,'7'),(9,'7'),  # m53-56
]
H_DROP2 = [
    (2,'m'),(2,'m'), (10,'M'),(10,'M'), (0,'7'),(0,'7'), (9,'7'),(9,'7'),
    (2,'m'),(2,'m'), (7,'m'),(7,'m'), (10,'M'),(9,'7'), (2,'m'),(2,'m'),
    (2,'m'),(2,'m'), (10,'M'),(10,'M'), (0,'7'),(0,'7'), (9,'7'),(9,'7'),
    (2,'m'),(2,'m'), (7,'m'),(7,'m'), (10,'M'),(9,'7'), (2,'m'),(2,'m'),
]
H_BREAK2 = [
    (2,'m'),(2,'m'), (5,'M'),(5,'M'), (7,'m'),(7,'m'), (9,'7'),(9,'7'),
    (2,'m'),(2,'m'), (10,'M'),(10,'M'), (9,'7'),(9,'7'), (2,'m'),(2,'m'),
]
H_DROP3 = [
    (2,'m'),(2,'m'), (10,'M'),(10,'M'), (0,'7'),(0,'7'), (9,'7'),(9,'7'),
    (2,'m'),(2,'m'), (7,'m'),(7,'m'), (10,'M'),(9,'7'), (2,'m'),(2,'m'),
    (2,'m'),(2,'m'), (10,'M'),(10,'M'), (0,'7'),(0,'7'), (9,'7'),(9,'7'),
    (2,'m'),(2,'m'), (7,'m'),(7,'m'), (9,'7'),(9,'7'), (2,'m'),(2,'m'),
]
H_OUTRO = [(2,'m'),(2,'m'), (7,'m'),(7,'m'), (9,'7'),(9,'7'), (2,'m'),(2,'m')] * 2

ALL_H = H_INTRO + H_BUILD1 + H_DROP1 + H_BREAK + H_BUILD2 + H_DROP2 + H_BREAK2 + H_DROP3 + H_OUTRO

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
        p = start
        self.n(p, rhythm[0], vel)
        for i, iv in enumerate(intervals):
            p += iv
            self.n(p, rhythm[min(i+1, len(rhythm)-1)], vel)

    def arp_pattern(self, root_pc, qual, base, bars, dur=SIXTEENTH, vel=70):
        """Arpeggiate chord for N bars."""
        pitches = chord_pitches(root_pc, qual, base)
        pitches_ext = pitches + [p + 12 for p in pitches]  # extend up
        total = bars * MEASURE
        written = 0
        idx = 0
        while written < total:
            p = pitches_ext[idx % len(pitches_ext)]
            d = min(dur, total - written)
            self.n(p, d, vel)
            written += d
            idx += 1


def compose():
    # 12 voices: channels 0-11
    lead     = V(0)   # Lead melody
    pad      = V(1)   # Sustained chords
    arp      = V(2)   # Arpeggios
    sub      = V(3)   # Sub bass
    pluck    = V(4)   # Plucked fragments
    stab     = V(5)   # Chord stabs
    hihat    = V(6)   # Hi-hat (pitched high)
    kick     = V(7)   # Kick drum (pitched low)
    clap     = V(8)   # Clap/snare
    fx       = V(9)   # FX risers
    acid     = V(10)  # Acid line
    ssaw     = V(11)  # Supersaw

    # Standard rhythms
    R_BASIC = [HALF, HALF, HALF, HALF, HALF, QUARTER, QUARTER, HALF]
    R_DRIVE = [QUARTER, QUARTER, QUARTER, QUARTER, QUARTER, EIGHTH, EIGHTH, HALF]
    R_SHORT = [EIGHTH, EIGHTH, EIGHTH, EIGHTH, EIGHTH, SIXTEENTH, SIXTEENTH, QUARTER]
    R_AUG   = [WHOLE, WHOLE, WHOLE, WHOLE, WHOLE, HALF, HALF, WHOLE]

    # ════════════════════════════════════════
    # INTRO (m1-8): Kick + hi-hat + sub bass
    # ════════════════════════════════════════

    # Kick: four-on-the-floor
    for bar in range(8):
        for beat in range(4):
            kick.go(bar * MEASURE + beat * QUARTER)
            kick.n(36, EIGHTH, 100)  # C2 = kick

    # Hi-hat: eighth notes, accented on off-beats
    for bar in range(8):
        for eighth in range(8):
            hihat.go(bar * MEASURE + eighth * EIGHTH)
            vel = 90 if eighth % 2 == 1 else 60  # off-beat accent
            hihat.n(80, EIGHTH, vel)  # G#5 = closed hi-hat range

    # Sub bass: D1 pedal, pulsing quarter notes
    for bar in range(8):
        for beat in range(4):
            sub.go(bar * MEASURE + beat * QUARTER)
            sub.n(38, EIGHTH, 90)  # D2
            sub.r(EIGHTH)  # rest = pumping

    # Clap on beats 2 and 4
    for bar in range(4, 8):  # enters at m5
        for beat in [1, 3]:
            clap.go(bar * MEASURE + beat * QUARTER)
            clap.n(74, EIGHTH, 85)

    # FX: rising sweep m7-8
    fx.go(6 * MEASURE)
    for i in range(32):
        p = 60 + i  # chromatic rise from C4 to G#5
        fx.n(p, SIXTEENTH, 40 + i)

    # All other voices rest during intro
    for v in [lead, pad, arp, pluck, stab, acid, ssaw]:
        v.r(8 * MEASURE)

    # ════════════════════════════════════════
    # BUILD 1 (m9-24): Subject enters, layers build
    # ════════════════════════════════════════
    t9 = 8 * MEASURE

    # Lead: subject on D4(62), basic rhythm
    lead.go(t9)
    lead.subj(62, SUBJ, R_BASIC, vel=90)
    # Lead: subject again on A4(69) — answer
    lead.subj(69, ANS, R_DRIVE, vel=85)

    # Pad: sustained Dm chord m9-16
    pad.go(t9)
    for bar_group in range(4):  # 4 groups of 4 bars
        rpc, qual = harm(t9 + bar_group * 4 * MEASURE)
        pts = chord_pitches(rpc, qual, 55)
        for p in pts:
            pad.notes.append((t9 + bar_group * 4 * MEASURE, p, 4 * MEASURE, 50))
        pad.c = t9 + (bar_group + 1) * 4 * MEASURE

    # Arp: starts m13, sixteenth arpeggios
    arp.go(t9 + 4 * MEASURE)
    for bar in range(12):  # m13-24
        tick = t9 + (4 + bar) * MEASURE
        rpc, qual = harm(tick)
        base = 62
        while (base % 12) != rpc:
            base += 1
        if base > 72:
            base -= 12
        pts = chord_pitches(rpc, qual, base)
        pts_ext = pts + [p + 12 for p in pts] + [p + 24 for p in pts[:2]]
        idx = 0
        arp.go(tick)
        for _ in range(16):  # 16 sixteenths per bar
            arp.n(pts_ext[idx % len(pts_ext)], SIXTEENTH, 70)
            idx += 1

    # Acid: enters m17, 303-style line
    acid.go(t9 + 8 * MEASURE)
    # Subject in acid style: short staccato with slides
    acid.subj(50, SUBJ, R_SHORT, vel=85)
    # Then inverted
    acid.subj(57, INV, R_SHORT, vel=80)

    # Continue kick, hihat, sub, clap through build
    for bar in range(8, 24):
        for beat in range(4):
            kick.go(bar * MEASURE + beat * QUARTER)
            kick.n(36, EIGHTH, 100)
        for eighth in range(8):
            hihat.go(bar * MEASURE + eighth * EIGHTH)
            vel = 95 if eighth % 2 == 1 else 65
            hihat.n(80, EIGHTH, vel)
        for beat in range(4):
            sub.go(bar * MEASURE + beat * QUARTER)
            rpc, _ = harm(bar * MEASURE)
            bass_p = 26 + rpc  # very low
            if bass_p < 28: bass_p += 12
            sub.n(bass_p, EIGHTH, 95)
        if bar >= 8:
            for beat in [1, 3]:
                clap.go(bar * MEASURE + beat * QUARTER)
                clap.n(74, EIGHTH, 85)

    # FX: riser before drop (m23-24)
    fx.go(22 * MEASURE)
    for i in range(64):
        p = 55 + (i * 30) // 64  # sweep up
        fx.n(p, EIGHTH if i < 48 else SIXTEENTH, 30 + i)

    # Pluck: subject fragments m17-24
    pluck.go(t9 + 8 * MEASURE)
    pluck.subj(74, SUBJ, [EIGHTH, EIGHTH, EIGHTH, EIGHTH, EIGHTH, SIXTEENTH, SIXTEENTH, EIGHTH], vel=75)
    pluck.r(MEASURE)
    pluck.subj(69, ANS, [EIGHTH, EIGHTH, EIGHTH, EIGHTH, EIGHTH, SIXTEENTH, SIXTEENTH, EIGHTH], vel=70)

    # ════════════════════════════════════════
    # DROP 1 (m25-32): FULL BLAST
    # ════════════════════════════════════════
    t25 = 24 * MEASURE

    # Supersaw: massive subject statement
    ssaw.go(t25)
    ssaw.subj(74, SUBJ, R_DRIVE, vel=100)
    ssaw.subj(69, INV, R_DRIVE, vel=95)

    # Lead: inverted subject on top
    lead.go(t25)
    lead.subj(81, INV, R_DRIVE, vel=90)
    lead.subj(74, SUBJ, R_SHORT, vel=85)

    # Stab: off-beat chord stabs
    for bar in range(8):
        tick = t25 + bar * MEASURE
        rpc, qual = harm(tick)
        pts = chord_pitches(rpc, qual, 62)
        for beat_off in [EIGHTH, QUARTER + EIGHTH, 2*QUARTER + EIGHTH, 3*QUARTER + EIGHTH]:
            stab.go(tick + beat_off)
            for p in pts:
                stab.notes.append((tick + beat_off, p, EIGHTH, 80))
            stab.c = tick + beat_off + EIGHTH

    # Arp: double-time (32nd notes!)
    for bar in range(8):
        tick = t25 + bar * MEASURE
        rpc, qual = harm(tick)
        base = 62
        while (base % 12) != rpc: base += 1
        if base > 72: base -= 12
        pts = chord_pitches(rpc, qual, base)
        pts_ext = pts + [p + 12 for p in pts] + [p - 12 for p in pts]
        pts_ext.sort()
        arp.go(tick)
        for i in range(32):  # 32 thirty-seconds per bar
            arp.n(pts_ext[i % len(pts_ext)], THIRTYSECOND, 65)

    # Acid: wild acid line
    acid.go(t25)
    acid.subj(50, SUBJ, R_SHORT, vel=90)
    acid.subj(45, ANS, R_SHORT, vel=85)
    acid.subj(50, INV, R_SHORT, vel=88)
    acid.subj(57, INV_ANS, R_SHORT, vel=82)

    # Pad: huge sustained chords
    for bar_g in range(2):
        tick = t25 + bar_g * 4 * MEASURE
        rpc, qual = harm(tick)
        for p in chord_pitches(rpc, qual, 50):
            pad.notes.append((tick, p, 4 * MEASURE, 60))
        # Add upper voicing too
        for p in chord_pitches(rpc, qual, 67):
            pad.notes.append((tick, p, 4 * MEASURE, 45))

    # Pluck: rapid-fire subject fragments
    pluck.go(t25)
    for rep in range(4):
        pluck.subj(74 - rep * 5, SUBJ, [SIXTEENTH]*8, vel=70)

    # Kick, hihat, sub, clap continue with more energy
    for bar in range(24, 32):
        for beat in range(4):
            kick.go(bar * MEASURE + beat * QUARTER)
            kick.n(36, EIGHTH, 110)
        for sixteenth in range(16):
            hihat.go(bar * MEASURE + sixteenth * SIXTEENTH)
            vel = 100 if sixteenth % 4 == 2 else (80 if sixteenth % 2 == 1 else 55)
            hihat.n(82 if sixteenth % 4 == 2 else 80, SIXTEENTH, vel)  # open hat on "and"
        for beat in range(4):
            sub.go(bar * MEASURE + beat * QUARTER)
            rpc, _ = harm(bar * MEASURE)
            sub.n(26 + rpc if 26 + rpc >= 28 else 26 + rpc + 12, EIGHTH, 100)
        for beat in [1, 3]:
            clap.go(bar * MEASURE + beat * QUARTER)
            clap.n(74, EIGHTH, 95)

    # ════════════════════════════════════════
    # BREAKDOWN (m33-48): stripped back
    # ════════════════════════════════════════
    t33 = 32 * MEASURE

    # Pad: exposed subject in long notes
    pad.go(t33)
    pad.subj(62, SUBJ, R_AUG, vel=55)

    # Acid: solo acid subject, slinky
    acid.go(t33)
    acid.subj(50, SUBJ, [DOTTED_Q, EIGHTH, DOTTED_Q, EIGHTH, HALF, EIGHTH, EIGHTH, DOTTED_Q], vel=80)
    acid.r(MEASURE)
    acid.subj(57, INV, [DOTTED_Q, EIGHTH, DOTTED_Q, EIGHTH, HALF, EIGHTH, EIGHTH, DOTTED_Q], vel=75)

    # Hi-hat: just closed hats, sparse
    for bar in range(32, 48):
        for beat in range(4):
            hihat.go(bar * MEASURE + beat * QUARTER)
            hihat.n(80, QUARTER, 50)

    # Kick: half-time feel
    for bar in range(32, 48):
        kick.go(bar * MEASURE)
        kick.n(36, EIGHTH, 90)
        kick.go(bar * MEASURE + 2 * QUARTER + EIGHTH)
        kick.n(36, EIGHTH, 70)

    # Clap: just on 3
    for bar in range(32, 48):
        clap.go(bar * MEASURE + 2 * QUARTER)
        clap.n(74, EIGHTH, 75)

    # Sub: minimal pulse
    for bar in range(32, 48):
        sub.go(bar * MEASURE)
        rpc, _ = harm(bar * MEASURE)
        sub.n(26 + rpc if 26 + rpc >= 28 else 26 + rpc + 12, HALF, 80)

    # Pluck: call and response with acid
    pluck.go(t33 + 4 * MEASURE)
    pluck.subj(69, ANS, [QUARTER, QUARTER, QUARTER, QUARTER, QUARTER, EIGHTH, EIGHTH, QUARTER], vel=65)
    pluck.r(2 * MEASURE)
    pluck.subj(74, SUBJ, [QUARTER, QUARTER, QUARTER, QUARTER, QUARTER, EIGHTH, EIGHTH, QUARTER], vel=60)

    # Arp: sparse, filtered feel — just roots and 5ths
    for bar in range(32, 48):
        tick = bar * MEASURE
        rpc, qual = harm(tick)
        base = 60
        while (base % 12) != rpc: base += 1
        if base > 72: base -= 12
        arp.go(tick)
        arp.n(base, QUARTER, 40)
        arp.n(base + 7, QUARTER, 40)
        arp.n(base + 12, QUARTER, 40)
        arp.n(base + 7, QUARTER, 40)

    # ════════════════════════════════════════
    # BUILD 2 (m49-56): Rising FX, stretto entries
    # ════════════════════════════════════════
    t49 = 48 * MEASURE

    # Lead: stretto — subject, then answer 1 beat later in stab
    lead.go(t49)
    lead.subj(62, SUBJ, R_DRIVE, vel=85)
    # Second entry 2 bars later
    lead.subj(69, ANS, R_DRIVE, vel=80)

    # Stab: inversion entering 1 beat after lead
    stab.go(t49 + QUARTER)
    stab.subj(69, INV, R_DRIVE, vel=80)

    # Pluck: answer entering 2 beats after
    pluck.go(t49 + HALF)
    pluck.subj(57, ANS, R_DRIVE, vel=75)

    # FX: massive riser across all 8 bars
    fx.go(t49)
    for i in range(128):
        p = 48 + (i * 36) // 128  # sweep from C3 to Bb5
        vel = 20 + (i * 80) // 128
        fx.n(p, SIXTEENTH, vel)

    # Acid: building intensity
    acid.go(t49)
    acid.subj(50, SUBJ, R_SHORT, vel=80)
    acid.subj(45, INV, R_SHORT, vel=85)
    acid.subj(50, ANS, R_SHORT, vel=90)
    acid.subj(57, SUBJ, R_SHORT, vel=95)

    # Continue drums, building fills
    for bar in range(48, 56):
        intensity = (bar - 48) / 8  # 0 to 1
        for beat in range(4):
            kick.go(bar * MEASURE + beat * QUARTER)
            kick.n(36, EIGHTH, int(80 + 30 * intensity))
        for sixteenth in range(16):
            hihat.go(bar * MEASURE + sixteenth * SIXTEENTH)
            hihat.n(80, SIXTEENTH, int(50 + 50 * intensity))
        for beat in [1, 3]:
            clap.go(bar * MEASURE + beat * QUARTER)
            clap.n(74, EIGHTH, int(70 + 25 * intensity))
        sub.go(bar * MEASURE)
        rpc, _ = harm(bar * MEASURE)
        sub.n(26 + rpc if 26 + rpc >= 28 else 26 + rpc + 12, QUARTER, int(80 + 20 * intensity))

    # Snare roll m55-56
    for i in range(32):
        clap.go(54 * MEASURE + i * EIGHTH)
        clap.n(74, EIGHTH, 60 + i * 2)

    # ════════════════════════════════════════
    # DROP 2 (m57-72): MAXIMUM ENERGY
    # ════════════════════════════════════════
    t57 = 56 * MEASURE

    # Supersaw: HUGE subject + inversion stretto
    ssaw.go(t57)
    ssaw.subj(74, SUBJ, R_DRIVE, vel=110)
    ssaw.subj(69, INV, R_DRIVE, vel=105)
    ssaw.subj(74, ANS, R_SHORT, vel=100)
    ssaw.subj(81, SUBJ, R_SHORT, vel=105)

    # Lead: counter-melody, inverted subject high
    lead.go(t57)
    lead.subj(81, INV, R_DRIVE, vel=95)
    lead.subj(76, SUBJ, R_DRIVE, vel=90)
    lead.subj(81, ANS, R_SHORT, vel=88)
    lead.subj(74, INV_ANS, R_SHORT, vel=85)

    # Stab: massive chord stabs every beat
    for bar in range(16):
        tick = t57 + bar * MEASURE
        rpc, qual = harm(tick)
        pts = chord_pitches(rpc, qual, 55)
        pts2 = chord_pitches(rpc, qual, 67)
        for beat in range(4):
            t_beat = tick + beat * QUARTER
            stab.go(t_beat)
            for p in pts + pts2:
                stab.notes.append((t_beat, p, EIGHTH, 85))
            stab.c = t_beat + EIGHTH

    # Arp: insane 32nd note arpeggios
    for bar in range(16):
        tick = t57 + bar * MEASURE
        rpc, qual = harm(tick)
        base = 60
        while (base % 12) != rpc: base += 1
        if base > 72: base -= 12
        pts = chord_pitches(rpc, qual, base)
        pts_up = pts + [p + 12 for p in pts] + [p + 24 for p in pts[:2]]
        pts_down = list(reversed(pts_up))
        combined = pts_up + pts_down
        arp.go(tick)
        for i in range(32):
            arp.n(combined[i % len(combined)], THIRTYSECOND, 60 + (i % 8) * 3)

    # Acid: aggressive pattern
    acid.go(t57)
    for rep in range(4):
        acid.subj(50 + rep * 2, SUBJ, R_SHORT, vel=90)
        acid.subj(57 - rep, INV, R_SHORT, vel=88)

    # Pluck: rapid repeated subject
    pluck.go(t57)
    for rep in range(8):
        pluck.subj(74 - (rep % 4) * 5, SUBJ, [SIXTEENTH]*8, vel=75)

    # Pad: walls of sound
    for bar_g in range(4):
        tick = t57 + bar_g * 4 * MEASURE
        rpc, qual = harm(tick)
        for p in chord_pitches(rpc, qual, 48):
            pad.notes.append((tick, p, 4 * MEASURE, 55))
        for p in chord_pitches(rpc, qual, 60):
            pad.notes.append((tick, p, 4 * MEASURE, 50))
        for p in chord_pitches(rpc, qual, 72):
            pad.notes.append((tick, p, 4 * MEASURE, 40))

    # Full drums
    for bar in range(56, 72):
        for beat in range(4):
            kick.go(bar * MEASURE + beat * QUARTER)
            kick.n(36, EIGHTH, 115)
        for sixteenth in range(16):
            hihat.go(bar * MEASURE + sixteenth * SIXTEENTH)
            vel = 105 if sixteenth % 4 == 2 else (85 if sixteenth % 2 == 1 else 60)
            pitch = 82 if sixteenth % 4 == 2 else 80
            hihat.n(pitch, SIXTEENTH, vel)
        for beat in [1, 3]:
            clap.go(bar * MEASURE + beat * QUARTER)
            clap.n(74, EIGHTH, 100)
        for beat in range(4):
            sub.go(bar * MEASURE + beat * QUARTER)
            rpc, _ = harm(bar * MEASURE)
            sub.n(26 + rpc if 26 + rpc >= 28 else 26 + rpc + 12, EIGHTH, 105)

    # ════════════════════════════════════════
    # BREAKDOWN 2 (m73-80): Half-time
    # ════════════════════════════════════════
    t73 = 72 * MEASURE

    # Lead: exposed subject, emotional
    lead.go(t73)
    lead.subj(74, SUBJ, [DOTTED_H, HALF, DOTTED_H, HALF, WHOLE, QUARTER, QUARTER, DOTTED_H], vel=75)

    # Pad: gentle chords
    for bar_g in range(2):
        tick = t73 + bar_g * 4 * MEASURE
        rpc, qual = harm(tick)
        for p in chord_pitches(rpc, qual, 55):
            pad.notes.append((tick, p, 4 * MEASURE, 40))

    # Sparse drums
    for bar in range(72, 80):
        kick.go(bar * MEASURE)
        kick.n(36, EIGHTH, 80)
        kick.go(bar * MEASURE + 2 * QUARTER + EIGHTH)
        kick.n(36, EIGHTH, 60)
        clap.go(bar * MEASURE + 2 * QUARTER)
        clap.n(74, EIGHTH, 65)
        for beat in range(4):
            hihat.go(bar * MEASURE + beat * QUARTER)
            hihat.n(80, QUARTER, 45)
        sub.go(bar * MEASURE)
        rpc, _ = harm(bar * MEASURE)
        sub.n(26 + rpc if 26 + rpc >= 28 else 26 + rpc + 12, WHOLE, 70)

    # FX: riser again
    fx.go(t73 + 4 * MEASURE)
    for i in range(64):
        p = 50 + (i * 38) // 64
        fx.n(p, SIXTEENTH, 25 + i)

    # Acid: minimal
    acid.go(t73)
    acid.subj(50, SUBJ, [HALF, HALF, HALF, HALF, HALF, QUARTER, QUARTER, HALF], vel=60)

    # ════════════════════════════════════════
    # DROP 3 / FINALE (m81-96): AUGMENTED SUBJECT + EVERYTHING
    # ════════════════════════════════════════
    t81 = 80 * MEASURE

    # Sub bass: AUGMENTED subject — each note = whole note
    sub.go(t81)
    sub.subj(26, SUBJ, R_AUG, vel=110)
    # Second augmented statement
    sub.subj(33, ANS, R_AUG, vel=105)

    # Supersaw: triple subject stretto
    ssaw.go(t81)
    ssaw.subj(74, SUBJ, R_DRIVE, vel=110)
    ssaw.subj(69, INV, R_SHORT, vel=105)
    ssaw.subj(81, SUBJ, R_DRIVE, vel=100)
    ssaw.subj(74, ANS, R_SHORT, vel=100)
    ssaw.subj(69, SUBJ, R_DRIVE, vel=95)
    ssaw.subj(76, INV_ANS, R_SHORT, vel=90)

    # Lead: soaring melody over everything
    lead.go(t81)
    lead.subj(81, SUBJ, R_DRIVE, vel=95)
    lead.subj(76, INV, R_DRIVE, vel=90)
    lead.subj(81, ANS, R_DRIVE, vel=88)
    lead.subj(74, SUBJ, R_SHORT, vel=90)
    lead.subj(81, INV_ANS, R_SHORT, vel=85)
    lead.subj(69, SUBJ, R_DRIVE, vel=92)

    # Acid: relentless
    acid.go(t81)
    for rep in range(8):
        acid.subj(50 + (rep % 3) * 3, SUBJ, R_SHORT, vel=85)

    # Stab: power chords on every beat
    for bar in range(16):
        tick = t81 + bar * MEASURE
        rpc, qual = harm(tick)
        pts = chord_pitches(rpc, qual, 55) + chord_pitches(rpc, qual, 67)
        for beat in range(4):
            t_beat = tick + beat * QUARTER
            for p in pts:
                stab.notes.append((t_beat, p, EIGHTH, 90))

    # Arp: maximum speed
    for bar in range(16):
        tick = t81 + bar * MEASURE
        rpc, qual = harm(tick)
        base = 62
        while (base % 12) != rpc: base += 1
        if base > 72: base -= 12
        pts = chord_pitches(rpc, qual, base)
        pts_ext = pts + [p+12 for p in pts] + [p+24 for p in pts[:2]]
        arp.go(tick)
        for i in range(32):
            arp.n(pts_ext[i % len(pts_ext)], THIRTYSECOND, 70)

    # Pluck: subject fragments everywhere
    pluck.go(t81)
    for rep in range(12):
        pluck.subj(74 - (rep % 5) * 3, SUBJ if rep % 2 == 0 else INV, [SIXTEENTH]*8, vel=70)

    # Pad: massive
    for bar_g in range(4):
        tick = t81 + bar_g * 4 * MEASURE
        rpc, qual = harm(tick)
        for octave_base in [43, 55, 67, 79]:
            for p in chord_pitches(rpc, qual, octave_base):
                pad.notes.append((tick, p, 4 * MEASURE, 45))

    # Full drums
    for bar in range(80, 96):
        for beat in range(4):
            kick.go(bar * MEASURE + beat * QUARTER)
            kick.n(36, EIGHTH, 120)
        for sixteenth in range(16):
            hihat.go(bar * MEASURE + sixteenth * SIXTEENTH)
            vel = 110 if sixteenth % 4 == 2 else (90 if sixteenth % 2 == 1 else 65)
            hihat.n(82 if sixteenth % 4 == 2 else 80, SIXTEENTH, vel)
        for beat in [1, 3]:
            clap.go(bar * MEASURE + beat * QUARTER)
            clap.n(74, EIGHTH, 105)

    # ════════════════════════════════════════
    # OUTRO (m97-104): Strip down
    # ════════════════════════════════════════
    t97 = 96 * MEASURE

    # Lead: final subject statement, fading
    lead.go(t97)
    lead.subj(62, SUBJ, R_BASIC, vel=70)
    lead.subj(62, SUBJ, R_AUG, vel=50)  # echo, dying away

    # Pad: final Dm
    for p in chord_pitches(2, 'm', 55):
        pad.notes.append((t97, p, 8 * MEASURE, 35))
    for p in chord_pitches(2, 'm', 67):
        pad.notes.append((t97, p, 8 * MEASURE, 25))

    # Kick fading out
    for bar in range(96, 104):
        fade = 1.0 - (bar - 96) / 8
        kick.go(bar * MEASURE)
        kick.n(36, EIGHTH, int(80 * fade))
        kick.go(bar * MEASURE + 2 * QUARTER)
        kick.n(36, EIGHTH, int(60 * fade))

    # Hi-hat fading
    for bar in range(96, 100):
        for beat in range(4):
            hihat.go(bar * MEASURE + beat * QUARTER)
            hihat.n(80, QUARTER, int(40 * (1 - (bar - 96) / 4)))

    # Sub: final D
    sub.go(t97)
    sub.n(38, 4 * MEASURE, 60)
    sub.n(26, 4 * MEASURE, 40)  # sub octave

    # Acid: last whisper of the subject
    acid.go(t97 + 2 * MEASURE)
    acid.subj(50, SUBJ, R_BASIC, vel=45)

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
