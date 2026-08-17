"""
music21 score export engine — builds a score from validated JSON and exports to .mxl

Provides export_to_mxl() as the main entry point, plus parse_duration(),
get_duration_type() and other helper functions.
"""

import os
import re
import zipfile
import tempfile
from music21 import stream, note, chord, tempo, meter, key, instrument, expressions, articulations, dynamics as dynamics21
from music21 import metadata as metadata21
from music21 import spanner as spanner21
from music21 import dynamics as dynamics_mod


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
    "pppp": dynamics21.Dynamic("pppp"),
    "ppp": dynamics21.Dynamic("ppp"),
    "pp": dynamics21.Dynamic("pp"),
    "p": dynamics21.Dynamic("p"),
    "mp": dynamics21.Dynamic("mp"),
    "mf": dynamics21.Dynamic("mf"),
    "f": dynamics21.Dynamic("f"),
    "ff": dynamics21.Dynamic("ff"),
    "fff": dynamics21.Dynamic("fff"),
    "ffff": dynamics21.Dynamic("ffff"),
    "sfz": dynamics21.Dynamic("sfz"),
    "sf": dynamics21.Dynamic("sf"),
    "fz": dynamics21.Dynamic("fz"),
    "rfz": dynamics21.Dynamic("rfz"),
    "sffz": dynamics21.Dynamic("sffz"),
    "fp": dynamics21.Dynamic("fp"),
    "sfp": dynamics21.Dynamic("sfp"),
    "crescendo": dynamics21.Dynamic("crescendo"),
    "diminuendo": dynamics21.Dynamic("diminuendo"),
    "calando": dynamics21.Dynamic("calando"),
    "morendo": dynamics21.Dynamic("morendo"),
    "smorzando": dynamics21.Dynamic("smorzando"),
    "rinforzando": dynamics21.Dynamic("rinforzando"),
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
    from music21 import expressions as expr

    if ornament_str == "trill":
        n_obj.expressions.append(expr.Trill())
    elif ornament_str == "mordent":
        n_obj.expressions.append(expr.Mordent())
    elif ornament_str == "inverted_mordent":
        n_obj.expressions.append(expr.InvertedMordent())
    elif ornament_str == "turn":
        n_obj.expressions.append(expr.Turn())
    elif ornament_str == "inverted_turn":
        n_obj.expressions.append(expr.InvertedTurn())


def export_to_mxl(json_data: dict, output_path: str) -> bool:
    """
    Build a music21.stream.Score from validated JSON score data and export to .mxl.

    Build process:
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
         h. Add the Part to the Score
      3. Export to MusicXML format and remove DOCTYPE declaration
      4. Compress into .mxl format

    Args:
        json_data: Validated score JSON dict with title, composer, metadata, tracks.
        output_path: Output .mxl file path.

    Returns:
        bool: True on success.

    Raises:
        OSError: If the output directory cannot be created or music21 export fails.
    """
    # 1. Auto-create output directory
    output_dir = os.path.dirname(output_path)
    if output_dir:
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            raise OSError(f"Cannot create output directory: {output_dir}") from e

    # 2. Import gm_mapping (lazy import to avoid circular dependency)
    from core import gm_mapping

    # 3. Create Score object
    score = stream.Score()

    # 4. Set metadata (title / composer)
    md = metadata21.Metadata()
    md.title = json_data.get("title", "Untitled")
    md.composer = json_data.get("composer", "Do Muse")
    score.insert(0, md)

    # 5. Read metadata sub-dict
    meta = json_data.get("metadata", {})

    # 6. Iterate over each track
    for track in json_data.get("tracks", []):
        # 6a. Get instrument name and MIDI program number
        instrument_name = track.get("instrument", "Acoustic Grand Piano")
        program_number = gm_mapping.get_program_number(instrument_name)

        # 6b. Create Part
        part = stream.Part()

        # 6c. Set instrument (using MIDI program number)
        inst = instrument.Instrument()
        inst.midiProgram = program_number
        inst.instrumentName = instrument_name
        part.insert(0, inst)

        # 6d. Insert time signature, key signature, tempo at the start
        time_sig = meta.get("time_signature", "4/4")
        part.insert(0, meter.TimeSignature(time_sig))

        key_sig = meta.get("key_signature")
        if key_sig:
            part.insert(0, key.Key(key_sig))

        bpm = meta.get("tempo_bpm", 120)
        part.insert(0, tempo.MetronomeMark(number=bpm))

        # 6e. Set clef
        clef_sign, clef_line = _get_clef_for_program(program_number)
        from music21 import clef
        part.insert(0, clef.TrebleClef() if clef_sign == 'G' else clef.BassClef())

        # 6f. Iterate notes, building by offset accumulation
        offset = 0.0
        part._current_tempo = bpm
        for n in track.get("notes", []):
            pitch = n.get("pitch")
            dur_str = n.get("duration", "quarter")
            vel = n.get("velocity", 80)

            dur_type = get_duration_type(dur_str)
            dot_count = _get_dot_count(dur_str)
            dur_float = parse_duration(dur_str)

            if pitch is None or pitch == -1:
                # Rest
                n_obj = note.Rest(type=dur_type)
                n_obj.duration.dots = dot_count
            else:
                # Note
                n_obj = note.Note(pitch, type=dur_type)
                n_obj.duration.dots = dot_count
                n_obj.volume.velocity = vel

                # Articulation
                articulation = n.get("articulation")
                if articulation is not None:
                    _apply_articulations(n_obj, articulation)

                # Dynamics
                dynamics = n.get("dynamics")
                if dynamics is not None:
                    _apply_dynamics(n_obj, dynamics)

                # Tie
                tie = n.get("tie")
                if tie is not None:
                    _apply_tie(n_obj, tie)

                # Lyric
                lyric = n.get("lyric")
                if lyric is not None:
                    _apply_lyric(n_obj, lyric)

                # Ornament
                ornament = n.get("ornament")
                if ornament is not None:
                    _apply_ornament(n_obj, ornament)

                # Grace note
                grace_note = n.get("grace_note")
                if grace_note is not None:
                    gn_obj = _build_grace_note(grace_note)
                    gn_obj.offset = offset
                    part.insert(gn_obj)

                # Fermata
                fermata = n.get("fermata")
                if fermata is not None and fermata:
                    n_obj.expressions.append(expressions.Fermata())

            # Tempo change
            tempo_change = n.get("tempo_change")
            if tempo_change is not None:
                tm = tempo.MetronomeMark(number=tempo_change)
                tm.offset = offset
                part.insert(tm)

            # Text annotation
            note_text = n.get("text")
            if note_text is not None:
                te = expressions.TextExpression(note_text)
                te.offset = offset
                part.insert(te)

            # Pedal marking
            pedal = n.get("pedal")
            if pedal is not None:
                if pedal == "start":
                    te_ped = expressions.TextExpression("Ped.")
                    te_ped.offset = offset
                    part.insert(te_ped)
                elif pedal == "continue":
                    te_ped = expressions.TextExpression("Ped.")
                    te_ped.offset = offset
                    part.insert(te_ped)
                elif pedal == "stop":
                    te_ped = expressions.TextExpression("Ped. stop")
                    te_ped.offset = offset
                    part.insert(te_ped)

            # ---------- JSON Schema-like field export ----------

            # Chord
            chord_pitches = n.get("chord")
            if chord_pitches is not None and isinstance(chord_pitches, list) and len(chord_pitches) > 0:
                chord_obj = chord.Chord(chord_pitches)
                chord_obj.duration = n_obj.duration
                chord_obj.volume.velocity = vel
                if hasattr(n_obj, 'articulations'):
                    chord_obj.articulations = n_obj.articulations
                if hasattr(n_obj, 'expressions'):
                    chord_obj.expressions = n_obj.expressions
                n_obj = chord_obj

            # Time signature change
            time_sig_change = n.get("time_signature_change")
            if time_sig_change is not None:
                ts = meter.TimeSignature(time_sig_change)
                ts.offset = offset
                part.insert(ts)

            # Key signature change
            key_sig_change = n.get("key_signature_change")
            if key_sig_change is not None:
                ks = key.Key(key_sig_change)
                ks.offset = offset
                part.insert(ks)

            # Arpeggio
            arpeggio = n.get("arpeggio")
            if arpeggio is not None and arpeggio:
                n_obj.expressions.append(expressions.ArpeggioMark())

            # Tremolo
            tremolo = n.get("tremolo")
            if tremolo is not None and isinstance(tremolo, dict):
                trem_dur_str = tremolo.get("duration", "eighth")
                trem_dur_type = get_duration_type(trem_dur_str)
                tremolo_obj = expressions.Tremolo(type=trem_dur_type)
                n_obj.expressions.append(tremolo_obj)

            # Glissando
            glissando = n.get("glissando")
            if glissando is not None and glissando:
                if hasattr(part, '_prev_note') and part._prev_note is not None:
                    gliss = spanner21.Glissando([part._prev_note, n_obj])
                    part.insert(gliss)
                part._prev_note = n_obj

            # Navigation
            navigation = n.get("navigation")
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
                    expr.offset = offset
                    part.insert(expr)

            # ---------- Expressive field export ----------

            # Hairpin
            hairpin = n.get("hairpin")
            if hairpin is not None:
                if hairpin in ("crescendo", "diminuendo"):
                    part._hairpin_start = n_obj
                    part._hairpin_type = hairpin
                elif hairpin == "stop":
                    if hasattr(part, '_hairpin_start') and part._hairpin_start is not None:
                        start_note = part._hairpin_start
                        hp_type = getattr(part, '_hairpin_type', 'crescendo')
                        if hp_type == "crescendo":
                            hp_obj = dynamics_mod.Crescendo()
                        else:
                            hp_obj = dynamics_mod.Diminuendo()
                        hp_obj.addSpannedElements([start_note, n_obj])
                        hp_obj.offset = start_note.offset
                        part.insert(hp_obj)
                        part._hairpin_start = None
                        part._hairpin_type = None

            # Tempo gradual
            tempo_gradual = n.get("tempo_gradual")
            if tempo_gradual is not None and isinstance(tempo_gradual, dict):
                tg_target = tempo_gradual.get("target_bpm", 120)
                tg_duration = tempo_gradual.get("duration_beats", 4.0)
                current_tempo = getattr(part, '_current_tempo', 120)
                if tg_target != current_tempo and tg_duration > 0:
                    num_steps = max(2, min(10, int(tg_duration / 0.5)))
                    for i in range(1, num_steps + 1):
                        t = i / num_steps
                        intermediate_tempo = current_tempo + (tg_target - current_tempo) * t
                        tm = tempo.MetronomeMark(number=int(round(intermediate_tempo)))
                        tm.offset = offset + tg_duration * t
                        part.insert(tm)
                    tm_final = tempo.MetronomeMark(number=tg_target)
                    tm_final.offset = offset + tg_duration
                    part.insert(tm_final)
                    part._current_tempo = tg_target

            # Subito
            subito = n.get("subito")
            if subito is not None:
                dyn = dynamics21.Dynamic(f"subito {subito}")
                dyn.offset = offset
                part.insert(dyn)

            # Expression
            expression = n.get("expression")
            if expression is not None:
                expr = expressions.TextExpression(expression)
                expr.offset = offset
                part.insert(expr)

            # Tuplet
            tuplet_val = n.get("tuplet")
            if tuplet_val:
                from music21 import duration
                tuplet = duration.Tuplet(tuplet_val, _get_tuplet_normal(tuplet_val))
                n_obj.duration.appendTuplet(tuplet)
                dur_float_adjusted = dur_float * (_get_tuplet_normal(tuplet_val) / tuplet_val)
            else:
                dur_float_adjusted = dur_float

            n_obj.offset = offset
            part.insert(n_obj)
            offset += dur_float_adjusted

        # 6g. Track-level repeat markings
        repeat_begin = track.get("repeat_begin")
        if repeat_begin is not None and repeat_begin:
            from music21 import bar
            part.insert(0, bar.Repeat(direction="start"))

        repeat_end = track.get("repeat_end")
        if repeat_end is not None and repeat_end:
            from music21 import bar
            part.insert(offset, bar.Repeat(direction="end"))

        # 6h. Add Part to Score
        score.append(part)

    # 7. Export to temporary XML, then post-process
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