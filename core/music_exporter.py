"""
music21 score export engine — builds a score from validated JSON and exports
to multiple formats (.mxl, .mid, .xml, .ly).

Provides:
  - export_to_mxl()   — compressed MusicXML
  - export_to_midi()  — Standard MIDI File
  - export_to_xml()   — uncompressed MusicXML
  - export_to_ly()    — LilyPond
  - export_score()    — dispatch by format string
  - _build_score()    — shared score builder (used by all exporters)
  - parse_duration()  — duration string -> float
  - get_duration_type() — duration string -> music21 type string
"""

import os
import re
import zipfile
import tempfile
from dataclasses import dataclass, field
from typing import Optional

from music21 import stream, note, chord, tempo, meter, key, instrument, \
    expressions, articulations, dynamics
from music21 import metadata as metadata21
from music21 import spanner as spanner21


# Base duration -> float (quarter note units) mapping
_DURATION_TO_FLOAT: dict[str, float] = {
    "whole": 4.0,
    "half": 2.0,
    "quarter": 1.0,
    "eighth": 0.5,
    "16th": 0.25,
    "32nd": 0.125,
    "64th": 0.0625,
}

# Dynamics marking -> music21 Dynamic object mapping
_DYNAMICS_MAP = {
    "pppp": dynamics.Dynamic("pppp"),
    "ppp": dynamics.Dynamic("ppp"),
    "pp": dynamics.Dynamic("pp"),
    "p": dynamics.Dynamic("p"),
    "mp": dynamics.Dynamic("mp"),
    "mf": dynamics.Dynamic("mf"),
    "f": dynamics.Dynamic("f"),
    "ff": dynamics.Dynamic("ff"),
    "fff": dynamics.Dynamic("fff"),
    "ffff": dynamics.Dynamic("ffff"),
    "sfz": dynamics.Dynamic("sfz"),
    "sf": dynamics.Dynamic("sf"),
    "fz": dynamics.Dynamic("fz"),
    "rfz": dynamics.Dynamic("rfz"),
    "sffz": dynamics.Dynamic("sffz"),
    "fp": dynamics.Dynamic("fp"),
    "sfp": dynamics.Dynamic("sfp"),
    "crescendo": dynamics.Dynamic("crescendo"),
    "diminuendo": dynamics.Dynamic("diminuendo"),
    "calando": dynamics.Dynamic("calando"),
    "morendo": dynamics.Dynamic("morendo"),
    "smorzando": dynamics.Dynamic("smorzando"),
    "rinforzando": dynamics.Dynamic("rinforzando"),
}

# Articulation -> music21 Articulation object mapping
_ARTICULATION_MAP = {
    "staccato": articulations.Staccato(),
    "staccatissimo": articulations.Staccatissimo(),
    "accent": articulations.Accent(),
    "tenuto": articulations.Tenuto(),
    "marcato": articulations.StrongAccent(),
    "sforzando": articulations.StrongAccent(),
}


@dataclass
class _BuildContext:
    """
    Mutable state used while building a single Part from a track.

    Replaces the old approach of dynamically injecting attributes
    (_current_tempo, _hairpin_start, _prev_note, etc.) onto the music21
    Part object, which caused TypeError at runtime.

    Attributes:
        offset: Current cumulative offset (quarter note units).
        current_tempo: Current tempo in BPM (for tempo_gradual).
        prev_note: Previous note object (for glissando/slur linking).
        hairpin_start: The note where a hairpin wedge started.
        hairpin_type: "crescendo" or "diminuendo".
        slur_start: The note where a slur started.
        pending_slur: Whether a slur is currently open.
    """
    offset: float = 0.0
    current_tempo: float = 120.0
    prev_note: Optional[note.GeneralNote] = None
    hairpin_start: Optional[note.GeneralNote] = None
    hairpin_type: Optional[str] = None
    slur_start: Optional[note.GeneralNote] = None
    pending_slur: bool = False


def parse_duration(duration_str: str) -> float:
    """
    Parse a duration string into a float (in quarter note units).

    Supports base durations: whole(4.0), half(2.0), quarter(1.0), eighth(0.5),
    16th(0.25), 32nd(0.125), 64th(0.0625).
    Dotted notes: if the string ends with ".", the value is multiplied by 1.5.

    Args:
        duration_str: Duration string, e.g. "quarter", "half.", "16th".

    Returns:
        float: Duration in quarter note units.
    """
    base = duration_str.rstrip(".")
    dots = len(duration_str) - len(base)
    value = _DURATION_TO_FLOAT.get(base, 1.0)
    if dots > 0:
        value *= 1.5
    return value


def get_duration_type(duration_str: str) -> str:
    """
    Return the music21 duration type string.

    Strips the trailing dot suffix, e.g. "half." -> "half", "quarter" -> "quarter".

    Args:
        duration_str: Duration string, e.g. "quarter", "half.", "16th".

    Returns:
        str: music21 duration type string.
    """
    return duration_str.rstrip(".")


def _get_dot_count(duration_str: str) -> int:
    """
    Get the number of dots in a duration string.

    Args:
        duration_str: Duration string.

    Returns:
        int: Number of dots (0 or 1).
    """
    base = duration_str.rstrip(".")
    return len(duration_str) - len(base)


def _remove_doctype(xml_content: str) -> str:
    """
    Remove the DOCTYPE declaration from MusicXML to prevent MuseScore from
    attempting to fetch the DTD over the network.

    Args:
        xml_content: Raw XML string.

    Returns:
        str: XML string with DOCTYPE removed.
    """
    return re.sub(
        r'<!DOCTYPE\s+score-partwise\s+PUBLIC\s+"[^"]*"\s+"[^"]*"\s*>',
        "",
        xml_content,
    )


def _get_clef_for_program(program_number: int) -> tuple:
    """
    Return the appropriate clef (sign, line) based on MIDI program number.

    Args:
        program_number: MIDI program number (0-127).

    Returns:
        tuple: (sign, line), e.g. ('G', 2) for treble clef.
    """
    # Bass instruments use bass clef
    if program_number in (32, 33, 34, 35, 36, 37, 38, 39, 43):
        return ('F', 4)
    if program_number in (42, 70):
        return ('F', 4)
    if program_number in (58,):
        return ('F', 4)
    # Default to treble clef
    return ('G', 2)


def _get_tuplet_normal(actual: int) -> int:
    """
    Return the normal (standard notation) note count for a given tuplet type.

    Standard music theory rules:
      - 3 notes: 3 replaces 2
      - 5/6/7 notes: N replaces 4
      - 9 notes: 9 replaces 8

    Args:
        actual: Actual note count in the tuplet (e.g. 3, 5, 6, 7, 9).

    Returns:
        int: Standard notation note count (normal).
    """
    if actual <= 3:
        return 2
    if actual <= 7:
        return 4
    return 8


# ---------------------------------------------------------------------------
# Individual note-marking processors
# ---------------------------------------------------------------------------

def _apply_articulations(n_obj, articulation_str: str) -> None:
    """
    Apply articulation markings to a note object.

    Args:
        n_obj: music21 Note object.
        articulation_str: Articulation type string.
    """
    art = _ARTICULATION_MAP.get(articulation_str)
    if art is not None:
        n_obj.articulations.append(art)


def _apply_dynamics(n_obj, dynamics_str: str) -> None:
    """
    Apply dynamics markings to a note object.

    Args:
        n_obj: music21 Note object.
        dynamics_str: Dynamics marking string.
    """
    dyn = _DYNAMICS_MAP.get(dynamics_str)
    if dyn is not None:
        n_obj.expressions.append(dyn)


def _apply_tie(n_obj, tie_str: str) -> None:
    """
    Apply a tie to a note object.

    Args:
        n_obj: music21 Note object.
        tie_str: "start", "stop", or "continue".
    """
    from music21 import tie
    n_obj.tie = tie.Tie(tie_str)


def _apply_lyric(n_obj, lyric_str: str) -> None:
    """
    Apply lyrics to a note object.

    Args:
        n_obj: music21 Note object.
        lyric_str: Lyric text.
    """
    n_obj.lyrics.append(note.Lyric(lyric_str, number=1))


def _build_grace_note(gn_data: dict) -> note.Note:
    """
    Build a music21 grace note from JSON grace_note data.

    Args:
        gn_data: Grace note dict with pitch and optional duration.

    Returns:
        Note: The constructed grace note object.
    """
    from music21 import duration

    gn_pitch = gn_data.get("pitch", -1)
    gn_dur_str = gn_data.get("duration", "16th")
    gn_dur_type = get_duration_type(gn_dur_str)

    if gn_pitch == -1:
        gn_obj = note.Rest(type=gn_dur_type)
    else:
        gn_obj = note.Note(gn_pitch, type=gn_dur_type)

    gn_obj.duration = duration.GraceDuration(gn_dur_type)
    return gn_obj


def _apply_ornament(n_obj, ornament_str: str) -> None:
    """
    Apply ornament markings to a note object.

    Args:
        n_obj: music21 Note object.
        ornament_str: Ornament type string.
    """
    if ornament_str == "trill":
        n_obj.expressions.append(expressions.Trill())
    elif ornament_str == "mordent":
        n_obj.expressions.append(expressions.Mordent())
    elif ornament_str == "inverted_mordent":
        n_obj.expressions.append(expressions.InvertedMordent())
    elif ornament_str == "turn":
        n_obj.expressions.append(expressions.Turn())
    elif ornament_str == "inverted_turn":
        n_obj.expressions.append(expressions.InvertedTurn())


# ---------------------------------------------------------------------------
# Per-note feature processors (context-driven)
# ---------------------------------------------------------------------------

def _process_grace_note(part: stream.Part, ctx: _BuildContext, n_data: dict) -> None:
    """
    Insert a grace note before the main note.

    Args:
        part: music21 Part being built.
        ctx: Build context.
        n_data: Note JSON dict.
    """
    grace_note = n_data.get("grace_note")
    if grace_note is not None:
        gn_obj = _build_grace_note(grace_note)
        gn_obj.offset = ctx.offset
        part.insert(gn_obj)


def _process_fermata(n_obj, n_data: dict) -> None:
    """
    Attach a fermata expression if requested.

    Args:
        n_obj: music21 note object.
        n_data: Note JSON dict.
    """
    fermata = n_data.get("fermata")
    if fermata is not None and fermata:
        n_obj.expressions.append(expressions.Fermata())


def _process_tempo_change(part: stream.Part, ctx: _BuildContext, n_data: dict) -> None:
    """
    Insert a tempo change metronome mark at the current offset.

    Args:
        part: music21 Part being built.
        ctx: Build context.
        n_data: Note JSON dict.
    """
    tempo_change = n_data.get("tempo_change")
    if tempo_change is not None:
        tm = tempo.MetronomeMark(number=tempo_change)
        tm.offset = ctx.offset
        part.insert(tm)


def _process_text(part: stream.Part, ctx: _BuildContext, n_data: dict) -> None:
    """
    Insert a text annotation at the current offset.

    Args:
        part: music21 Part being built.
        ctx: Build context.
        n_data: Note JSON dict.
    """
    note_text = n_data.get("text")
    if note_text is not None:
        te = expressions.TextExpression(note_text)
        te.offset = ctx.offset
        part.insert(te)


def _process_pedal(part: stream.Part, ctx: _BuildContext, n_data: dict) -> None:
    """
    Insert pedal markings at the current offset.

    Args:
        part: music21 Part being built.
        ctx: Build context.
        n_data: Note JSON dict.
    """
    pedal = n_data.get("pedal")
    if pedal is not None:
        if pedal == "start":
            te_ped = expressions.TextExpression("Ped.")
            te_ped.offset = ctx.offset
            part.insert(te_ped)
        elif pedal == "continue":
            te_ped = expressions.TextExpression("Ped.")
            te_ped.offset = ctx.offset
            part.insert(te_ped)
        elif pedal == "stop":
            te_ped = expressions.TextExpression("Ped. stop")
            te_ped.offset = ctx.offset
            part.insert(te_ped)


def _process_chord(n_obj, n_data: dict, vel: int) -> object:
    """
    Convert the note object into a chord if a chord array is provided.

    Args:
        n_obj: The original note object (used for duration/articulations).
        n_data: Note JSON dict.
        vel: Velocity to apply to the chord.

    Returns:
        The chord object if a chord was built, otherwise the original n_obj.
    """
    chord_pitches = n_data.get("chord")
    if chord_pitches is not None and isinstance(chord_pitches, list) and len(chord_pitches) > 0:
        chord_obj = chord.Chord(chord_pitches)
        chord_obj.duration = n_obj.duration
        chord_obj.volume.velocity = vel
        if hasattr(n_obj, 'articulations'):
            chord_obj.articulations = n_obj.articulations
        if hasattr(n_obj, 'expressions'):
            chord_obj.expressions = n_obj.expressions
        return chord_obj
    return n_obj


def _process_time_sig_change(part: stream.Part, ctx: _BuildContext, n_data: dict) -> None:
    """
    Insert a time signature change at the current offset.

    Args:
        part: music21 Part being built.
        ctx: Build context.
        n_data: Note JSON dict.
    """
    time_sig_change = n_data.get("time_signature_change")
    if time_sig_change is not None:
        ts = meter.TimeSignature(time_sig_change)
        ts.offset = ctx.offset
        part.insert(ts)


def _process_key_sig_change(part: stream.Part, ctx: _BuildContext, n_data: dict) -> None:
    """
    Insert a key signature change at the current offset.

    Args:
        part: music21 Part being built.
        ctx: Build context.
        n_data: Note JSON dict.
    """
    key_sig_change = n_data.get("key_signature_change")
    if key_sig_change is not None:
        ks = key.Key(key_sig_change)
        ks.offset = ctx.offset
        part.insert(ks)


def _process_arpeggio(n_obj, n_data: dict) -> None:
    """
    Attach an arpeggio mark if requested.

    Args:
        n_obj: music21 note object.
        n_data: Note JSON dict.
    """
    arpeggio = n_data.get("arpeggio")
    if arpeggio is not None and arpeggio:
        n_obj.expressions.append(expressions.ArpeggioMark())


def _process_tremolo(n_obj, n_data: dict) -> None:
    """
    Attach a tremolo marking if requested.

    Args:
        n_obj: music21 note object.
        n_data: Note JSON dict.
    """
    tremolo = n_data.get("tremolo")
    if tremolo is not None and isinstance(tremolo, dict):
        trem_dur_str = tremolo.get("duration", "eighth")
        trem_dur_type = get_duration_type(trem_dur_str)
        tremolo_obj = expressions.Tremolo(type=trem_dur_type)
        n_obj.expressions.append(tremolo_obj)


def _process_glissando(part: stream.Part, ctx: _BuildContext, n_obj, n_data: dict) -> None:
    """
    Create a glissando from the previous note to the current note.

    Args:
        part: music21 Part being built.
        ctx: Build context.
        n_obj: Current note object.
        n_data: Note JSON dict.
    """
    glissando = n_data.get("glissando")
    if glissando is not None and glissando:
        if ctx.prev_note is not None:
            gliss = spanner21.Glissando([ctx.prev_note, n_obj])
            part.insert(gliss)
    ctx.prev_note = n_obj


def _process_slur(part: stream.Part, ctx: _BuildContext, n_obj, n_data: dict) -> None:
    """
    Handle slur start/stop by creating a music21 Slur spanner.

    Args:
        part: music21 Part being built.
        ctx: Build context.
        n_obj: Current note object.
        n_data: Note JSON dict.
    """
    slur = n_data.get("slur")
    if slur is None:
        return

    if slur == "start":
        ctx.slur_start = n_obj
        ctx.pending_slur = True
    elif slur == "stop" and ctx.pending_slur and ctx.slur_start is not None:
        slur_obj = spanner21.Slur([ctx.slur_start, n_obj])
        part.insert(slur_obj)
        ctx.slur_start = None
        ctx.pending_slur = False


def _process_navigation(part: stream.Part, ctx: _BuildContext, n_data: dict) -> None:
    """
    Insert a navigation text expression (D.C., D.S., Coda, Fine).

    Args:
        part: music21 Part being built.
        ctx: Build context.
        n_data: Note JSON dict.
    """
    navigation = n_data.get("navigation")
    if navigation is not None:
        nav_texts = {
            "D.C.": "D.C.",
            "D.S.": "D.S.",
            "Coda": "Coda",
            "Fine": "Fine",
        }
        text = nav_texts.get(navigation)
        if text:
            expr = expressions.TextExpression(text)
            expr.offset = ctx.offset
            part.insert(expr)


def _process_hairpin(part: stream.Part, ctx: _BuildContext, n_obj, n_data: dict) -> None:
    """
    Handle hairpin (crescendo/diminuendo) start and stop.

    Args:
        part: music21 Part being built.
        ctx: Build context.
        n_obj: Current note object.
        n_data: Note JSON dict.
    """
    hairpin = n_data.get("hairpin")
    if hairpin is None:
        return

    if hairpin in ("crescendo", "diminuendo"):
        ctx.hairpin_start = n_obj
        ctx.hairpin_type = hairpin
    elif hairpin == "stop":
        if ctx.hairpin_start is not None:
            start_note = ctx.hairpin_start
            hp_type = ctx.hairpin_type or "crescendo"
            if hp_type == "crescendo":
                hp_obj = dynamics.Crescendo()
            else:
                hp_obj = dynamics.Diminuendo()
            hp_obj.addSpannedElements([start_note, n_obj])
            hp_obj.offset = start_note.offset
            part.insert(hp_obj)
            ctx.hairpin_start = None
            ctx.hairpin_type = None


def _process_tempo_gradual(part: stream.Part, ctx: _BuildContext, n_data: dict) -> None:
    """
    Insert intermediate metronome marks for a gradual tempo change.

    Args:
        part: music21 Part being built.
        ctx: Build context.
        n_data: Note JSON dict.
    """
    tempo_gradual = n_data.get("tempo_gradual")
    if tempo_gradual is not None and isinstance(tempo_gradual, dict):
        tg_target = tempo_gradual.get("target_bpm", 120)
        tg_duration = tempo_gradual.get("duration_beats", 4.0)
        current_tempo = ctx.current_tempo
        if tg_target != current_tempo and tg_duration > 0:
            num_steps = max(2, min(10, int(tg_duration / 0.5)))
            for i in range(1, num_steps + 1):
                t = i / num_steps
                intermediate_tempo = current_tempo + (tg_target - current_tempo) * t
                tm = tempo.MetronomeMark(number=int(round(intermediate_tempo)))
                tm.offset = ctx.offset + tg_duration * t
                part.insert(tm)
            tm_final = tempo.MetronomeMark(number=tg_target)
            tm_final.offset = ctx.offset + tg_duration
            part.insert(tm_final)
            ctx.current_tempo = tg_target


def _process_subito(part: stream.Part, ctx: _BuildContext, n_data: dict) -> None:
    """
    Insert a subito dynamics marking at the current offset.

    Args:
        part: music21 Part being built.
        ctx: Build context.
        n_data: Note JSON dict.
    """
    subito = n_data.get("subito")
    if subito is not None:
        dyn = dynamics.Dynamic(f"subito {subito}")
        dyn.offset = ctx.offset
        part.insert(dyn)


def _process_expression(part: stream.Part, ctx: _BuildContext, n_data: dict) -> None:
    """
    Insert an expression text at the current offset.

    Args:
        part: music21 Part being built.
        ctx: Build context.
        n_data: Note JSON dict.
    """
    expression = n_data.get("expression")
    if expression is not None:
        expr = expressions.TextExpression(expression)
        expr.offset = ctx.offset
        part.insert(expr)


# ---------------------------------------------------------------------------
# Score builder
# ---------------------------------------------------------------------------

def _build_note_object(n: dict, dur_type: str, dot_count: int, vel: int) -> object:
    """
    Build the core music21 note/rest object from a note JSON dict.

    Args:
        n: Note JSON dict.
        dur_type: Duration type string (dots stripped).
        dot_count: Number of dots.
        vel: Velocity value.

    Returns:
        A music21 Note or Rest object.
    """
    pitch = n.get("pitch")
    if pitch is None or pitch == -1:
        n_obj = note.Rest(type=dur_type)
        n_obj.duration.dots = dot_count
    else:
        n_obj = note.Note(pitch, type=dur_type)
        n_obj.duration.dots = dot_count
        n_obj.volume.velocity = vel
    return n_obj


def _apply_note_markings(n_obj, n: dict) -> None:
    """
    Apply simple markings (articulation, dynamics, tie, lyric, ornament)
    that only depend on the note object itself.

    Args:
        n_obj: music21 note object.
        n: Note JSON dict.
    """
    pitch = n.get("pitch")
    if pitch is None or pitch == -1:
        return

    articulation = n.get("articulation")
    if articulation is not None:
        _apply_articulations(n_obj, articulation)

    dyn = n.get("dynamics")
    if dyn is not None:
        _apply_dynamics(n_obj, dyn)

    tie = n.get("tie")
    if tie is not None:
        _apply_tie(n_obj, tie)

    lyric = n.get("lyric")
    if lyric is not None:
        _apply_lyric(n_obj, lyric)

    ornament = n.get("ornament")
    if ornament is not None:
        _apply_ornament(n_obj, ornament)


def _build_score(json_data: dict) -> stream.Score:
    """
    Build a music21 Score object from validated JSON score data.

    Shared by all export format functions. Build process:
      1. Create a Score object with metadata (title, composer)
      2. For each track:
         a. Get MIDI program number via gm_mapping.get_program_number()
         b. Create a Part with the instrument
         c. Insert time signature, key signature, tempo, clef at the start
         d. Iterate notes, building notes/rests by offset accumulation
         e. Support articulation, dynamics, tie, slur, lyric, ornament, grace note
         f. Support chord, time signature change, key signature change, arpeggio,
            tremolo, glissando, navigation
         g. Support hairpin, tempo_gradual, subito, expression
         h. Support volta (1st/2nd ending) brackets
         i. Add the Part to the Score

    Args:
        json_data: Validated score JSON dict with title, composer, metadata, tracks.

    Returns:
        stream.Score: The constructed music21 Score object.
    """
    from core import gm_mapping
    from music21 import clef
    from music21 import spanner as spanner_mod

    score = stream.Score()

    # Set metadata (title / composer)
    md = metadata21.Metadata()
    md.title = json_data.get("title", "Untitled")
    md.composer = json_data.get("composer", "Do Muse")
    score.insert(0, md)

    meta = json_data.get("metadata", {})

    for track in json_data.get("tracks", []):
        instrument_name = track.get("instrument", "Acoustic Grand Piano")
        program_number = gm_mapping.get_program_number(instrument_name)

        part = stream.Part()

        # Set instrument
        inst = instrument.Instrument()
        inst.midiProgram = program_number
        inst.instrumentName = instrument_name
        part.insert(0, inst)

        # Insert time signature, key signature, tempo at the start
        time_sig = meta.get("time_signature", "4/4")
        part.insert(0, meter.TimeSignature(time_sig))

        key_sig = meta.get("key_signature")
        if key_sig:
            part.insert(0, key.Key(key_sig))

        bpm = meta.get("tempo_bpm", 120)
        part.insert(0, tempo.MetronomeMark(number=bpm))

        # Set clef
        clef_sign, clef_line = _get_clef_for_program(program_number)
        part.insert(0, clef.TrebleClef() if clef_sign == 'G' else clef.BassClef())

        # Volta (1st/2nd ending) bracket
        volta = track.get("volta")
        if volta is not None and volta:
            from music21 import spanner as spanner_mod
            volta_spanner = spanner21.Volta("volta", number=volta)

        # Build context for this track
        ctx = _BuildContext(offset=0.0, current_tempo=float(bpm))

        for n in track.get("notes", []):
            pitch = n.get("pitch")
            dur_str = n.get("duration", "quarter")
            vel = n.get("velocity", 80)

            dur_type = get_duration_type(dur_str)
            dot_count = _get_dot_count(dur_str)
            dur_float = parse_duration(dur_str)

            # Build the core note/rest object
            n_obj = _build_note_object(n, dur_type, dot_count, vel)

            # Apply simple markings
            _apply_note_markings(n_obj, n)

            # Grace note (inserted before the main note)
            _process_grace_note(part, ctx, n)

            # Fermata
            _process_fermata(n_obj, n)

            # Tempo change
            _process_tempo_change(part, ctx, n)

            # Text annotation
            _process_text(part, ctx, n)

            # Pedal marking
            _process_pedal(part, ctx, n)

            # Chord (may replace n_obj)
            n_obj = _process_chord(n_obj, n, vel)

            # Time signature change
            _process_time_sig_change(part, ctx, n)

            # Key signature change
            _process_key_sig_change(part, ctx, n)

            # Arpeggio
            _process_arpeggio(n_obj, n)

            # Tremolo
            _process_tremolo(n_obj, n)

            # Glissando (also updates ctx.prev_note)
            _process_glissando(part, ctx, n_obj, n)

            # Slur
            _process_slur(part, ctx, n_obj, n)

            # Navigation
            _process_navigation(part, ctx, n)

            # Hairpin
            _process_hairpin(part, ctx, n_obj, n)

            # Tempo gradual
            _process_tempo_gradual(part, ctx, n)

            # Subito
            _process_subito(part, ctx, n)

            # Expression
            _process_expression(part, ctx, n)

            # Tuplet
            tuplet_val = n.get("tuplet")
            if tuplet_val:
                from music21 import duration
                tuplet = duration.Tuplet(tuplet_val, _get_tuplet_normal(tuplet_val))
                n_obj.duration.appendTuplet(tuplet)
                dur_float_adjusted = dur_float * (_get_tuplet_normal(tuplet_val) / tuplet_val)
            else:
                dur_float_adjusted = dur_float

            n_obj.offset = ctx.offset
            part.insert(n_obj)
            ctx.offset += dur_float_adjusted

        # Track-level repeat markings
        repeat_begin = track.get("repeat_begin")
        if repeat_begin is not None and repeat_begin:
            from music21 import bar
            part.insert(0, bar.Repeat(direction="start"))

        repeat_end = track.get("repeat_end")
        if repeat_end is not None and repeat_end:
            from music21 import bar
            part.insert(ctx.offset, bar.Repeat(direction="end"))

        score.append(part)

    return score


def _ensure_output_dir(output_path: str) -> None:
    """
    Auto-create the output directory if it does not exist.

    Args:
        output_path: Full output file path.

    Raises:
        OSError: If the directory cannot be created.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            raise OSError(f"Cannot create output directory: {output_dir}") from e


def export_to_mxl(json_data: dict, output_path: str) -> bool:
    """
    Build a music21 Score from validated JSON and export to compressed .mxl.

    Args:
        json_data: Validated score JSON dict.
        output_path: Output .mxl file path.

    Returns:
        bool: True on success.

    Raises:
        OSError: If music21 export fails.
    """
    _ensure_output_dir(output_path)

    score = _build_score(json_data)

    # Export to temporary XML, then post-process
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as tmp:
            temp_path = tmp.name

        score.write('musicxml', fp=temp_path)

        with open(temp_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        xml_content = _remove_doctype(xml_content)

        mxl_filename = os.path.splitext(os.path.basename(output_path))[0] + '.musicxml'
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            container_xml = (
                '<?xml version="1.0" encoding="UTF-8"?>\n'
                '<container>\n'
                '  <rootfiles>\n'
                f'    <rootfile full-path="{mxl_filename}"/>\n'
                '  </rootfiles>\n'
                '</container>\n'
            )
            zf.writestr('META-INF/container.xml', container_xml)
            zf.writestr(mxl_filename, xml_content)

        os.unlink(temp_path)

    except Exception as e:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise OSError(f"music21 export failed: {e}") from e

    return True


def export_to_midi(json_data: dict, output_path: str) -> bool:
    """
    Build a music21 Score from validated JSON and export to Standard MIDI File (.mid).

    Args:
        json_data: Validated score JSON dict.
        output_path: Output .mid file path.

    Returns:
        bool: True on success.

    Raises:
        OSError: If music21 export fails.
    """
    _ensure_output_dir(output_path)
    score = _build_score(json_data)
    try:
        score.write('midi', fp=output_path)
    except Exception as e:
        raise OSError(f"MIDI export failed: {e}") from e
    return True


def export_to_xml(json_data: dict, output_path: str) -> bool:
    """
    Build a music21 Score from validated JSON and export to uncompressed MusicXML (.xml).

    Args:
        json_data: Validated score JSON dict.
        output_path: Output .xml file path.

    Returns:
        bool: True on success.

    Raises:
        OSError: If music21 export fails.
    """
    _ensure_output_dir(output_path)
    score = _build_score(json_data)
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False, encoding='utf-8') as tmp:
            temp_path = tmp.name

        score.write('musicxml', fp=temp_path)

        with open(temp_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        xml_content = _remove_doctype(xml_content)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)

        os.unlink(temp_path)
    except Exception as e:
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.unlink(temp_path)
        raise OSError(f"MusicXML export failed: {e}") from e
    return True


def export_to_ly(json_data: dict, output_path: str) -> bool:
    """
    Build a music21 Score from validated JSON and export to LilyPond (.ly).

    Args:
        json_data: Validated score JSON dict.
        output_path: Output .ly file path.

    Returns:
        bool: True on success.

    Raises:
        OSError: If music21 export fails.
    """
    _ensure_output_dir(output_path)
    score = _build_score(json_data)
    try:
        score.write('lilypond', fp=output_path)
    except Exception as e:
        raise OSError(f"LilyPond export failed: {e}") from e
    return True


def export_score(json_data: dict, output_path: str, fmt: str = "mxl") -> bool:
    """
    Dispatch to the appropriate export function based on format string.

    Supported formats:
      - "mxl"  -> compressed MusicXML
      - "midi" -> Standard MIDI File
      - "xml"  -> uncompressed MusicXML
      - "ly"   -> LilyPond

    Args:
        json_data: Validated score JSON dict.
        output_path: Output file path.
        fmt: Target format identifier. Defaults to "mxl".

    Returns:
        bool: True on success.

    Raises:
        ValueError: If the format string is not supported.
    """
    exporters = {
        "mxl": export_to_mxl,
        "midi": export_to_midi,
        "xml": export_to_xml,
        "ly": export_to_ly,
    }
    exporter = exporters.get(fmt.lower())
    if exporter is None:
        raise ValueError(
            f"Unsupported export format: '{fmt}'. "
            f"Supported formats: {', '.join(sorted(exporters.keys()))}"
        )
    return exporter(json_data, output_path)
