"""
JSON validator — validates the completeness and legality of score JSON data

Provides the validate() function to check the AI Muse score JSON structure,
including required fields, type checks, range checks, and duration validity,
and auto-fills missing default values.
Also supports macro expansion: macros defined in the top-level "macros" field
can be referenced via {"ref": "macro_name"} in notes arrays.
"""

import copy

# Base duration set
_BASE_DURATIONS = {"whole", "half", "quarter", "eighth", "16th", "32nd", "64th"}

# Valid tuplet types (actual note count)
_VALID_TUPLETS = {3, 5, 6, 7, 9}

# Valid articulation types
_VALID_ARTICULATIONS = {
    "staccato", "staccatissimo", "accent", "tenuto", "marcato", "sforzando"
}

# Valid dynamics markings
_VALID_DYNAMICS = {
    "pppp", "ppp", "pp", "p", "mp", "mf", "f", "ff", "fff", "ffff",
    "sfz", "sf", "fz", "rfz", "sffz",
    "fp", "sfp",
    "crescendo", "diminuendo",
    "calando", "morendo", "smorzando", "rinforzando",
}

# Valid ornament types
_VALID_ORNAMENTS = {
    "trill", "mordent", "inverted_mordent", "turn", "inverted_turn"
}

# Default values
_DEFAULT_TITLE = "Untitled"
_DEFAULT_COMPOSER = "Unknown"
_DEFAULT_VELOCITY = 80

# Voice validation constants
_VOICE_NAME_MAX_LENGTH = 50

# Transpose instrument constants
_VALID_TRANSPOSE_INTERVALS = {"-12", "-11", "-10", "-9", "-8", "-7", "-6", "-5", "-4", "-3", "-2", "-1", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12"}

# Barline style constants
_VALID_BARLINE_STYLES = {"single", "double", "final", "dashed", "invisible"}


def _is_valid_duration(duration_str: str) -> bool:
    """
    Check whether a duration string is valid.

    Valid durations are base types (whole/half/quarter/eighth/16th/32nd/64th)
    with an optional "." suffix for dotted notes.

    Args:
        duration_str: The duration string to validate.

    Returns:
        bool: True if the duration is valid, False otherwise.
    """
    if not isinstance(duration_str, str):
        return False
    base = duration_str.rstrip(".")
    dot_count = len(duration_str) - len(base)
    if dot_count > 1:
        return False
    return base in _BASE_DURATIONS


def _expand_macros(json_data: dict) -> list:
    """
    Expand macro references in the score JSON data.

    Macros are defined in the top-level "macros" field as a dict of
    name -> notes_array mappings. References in tracks use {"ref": "name"}
    to insert the macro's notes array inline.

    This function validates macro definitions, expands all references,
    and removes the "macros" field from the data.

    Args:
        json_data: The score JSON dict to expand macros in.

    Returns:
        list: A list of error messages (empty if no errors).
    """
    errors = []

    macros = json_data.get("macros")
    macros_present = macros is not None
    if not macros_present:
        # No macros block defined: treat as an empty dict so that any
        # {"ref": ...} used in notes is still reported as an *undefined* macro
        # reference below (instead of being silently ignored).
        macros = {}

    # Validate macros structure
    if not isinstance(macros, dict):
        errors.append("macros must be an object (dict)")
        return errors

    if macros_present and len(macros) == 0:
        errors.append("macros cannot be empty")
        return errors

    # Validate each macro definition
    for macro_name, macro_notes in macros.items():
        if not isinstance(macro_name, str):
            errors.append(
                f"Macro name must be a string, got {type(macro_name).__name__}"
            )
            continue

        if not isinstance(macro_notes, list):
            errors.append(
                f"Macro '{macro_name}' must be an array of note objects"
            )
            continue

        if len(macro_notes) == 0:
            errors.append(f"Macro '{macro_name}' cannot be empty")
            continue

        # Validate each note in the macro
        for mn_idx, mn in enumerate(macro_notes):
            if not isinstance(mn, dict):
                errors.append(
                    f"Macro '{macro_name}', note {mn_idx + 1} must be an object"
                )
                continue

            # Check for nested ref (forbidden)
            if "ref" in mn:
                errors.append(
                    f"Macro '{macro_name}', note {mn_idx + 1}: nested 'ref' "
                    "is not allowed inside macros"
                )
                continue

            # Basic note validation: must have pitch or chord
            if "pitch" not in mn and "chord" not in mn:
                errors.append(
                    f"Macro '{macro_name}', note {mn_idx + 1}: "
                    "each note must have 'pitch' or 'chord'"
                )

    if errors:
        return errors

    # Expand refs in tracks
    tracks = json_data.get("tracks")
    if tracks is not None and isinstance(tracks, list):
        for t_idx, track in enumerate(tracks):
            if not isinstance(track, dict):
                continue

            # Check for voices field (multivoice support)
            voices = track.get("voices")
            notes = track.get("notes")
            
            # Expand macros in voices
            if voices is not None:
                for v_idx, voice in enumerate(voices):
                    if not isinstance(voice, dict):
                        continue
                    
                    voice_notes = voice.get("notes")
                    if voice_notes is None or not isinstance(voice_notes, list):
                        continue
                    
                    expanded_notes = []
                    for n_idx, note_obj in enumerate(voice_notes):
                        if not isinstance(note_obj, dict):
                            expanded_notes.append(note_obj)
                            continue

                        ref = note_obj.get("ref")
                        if ref is not None:
                            # Validate ref field is a string
                            if not isinstance(ref, str):
                                errors.append(
                                    f"Track {t_idx + 1}, voice {v_idx + 1}, note {n_idx + 1}: "
                                    "'ref' must be a string"
                                )
                                expanded_notes.append(note_obj)
                                continue

                            # Check ref doesn't coexist with other fields
                            other_keys = [k for k in note_obj if k != "ref"]
                            if other_keys:
                                errors.append(
                                    f"Track {t_idx + 1}, voice {v_idx + 1}, note {n_idx + 1}: "
                                    "'ref' cannot coexist with other fields "
                                    f"({', '.join(other_keys)})"
                                )
                                expanded_notes.append(note_obj)
                                continue

                            # Look up the macro
                            if ref not in macros:
                                errors.append(
                                    f"Track {t_idx + 1}, voice {v_idx + 1}, note {n_idx + 1}: "
                                    f"macro '{ref}' is not defined"
                                )
                                expanded_notes.append(note_obj)
                                continue

                            # Expand: deep copy macro notes to avoid mutation issues
                            expanded_notes.extend(copy.deepcopy(macros[ref]))
                        else:
                            expanded_notes.append(note_obj)

                    voice["notes"] = expanded_notes
            
            # Expand macros in notes (backward compatibility)
            elif notes is not None and isinstance(notes, list):
                expanded_notes = []
                for n_idx, note_obj in enumerate(notes):
                    if not isinstance(note_obj, dict):
                        expanded_notes.append(note_obj)
                        continue

                    ref = note_obj.get("ref")
                    if ref is not None:
                        # Validate ref field is a string
                        if not isinstance(ref, str):
                            errors.append(
                                f"Track {t_idx + 1}, note {n_idx + 1}: "
                                "'ref' must be a string"
                            )
                            expanded_notes.append(note_obj)
                            continue

                        # Check ref doesn't coexist with other fields
                        other_keys = [k for k in note_obj if k != "ref"]
                        if other_keys:
                            errors.append(
                                f"Track {t_idx + 1}, note {n_idx + 1}: "
                                "'ref' cannot coexist with other fields "
                                f"({', '.join(other_keys)})"
                            )
                            expanded_notes.append(note_obj)
                            continue

                        # Look up the macro
                        if ref not in macros:
                            errors.append(
                                f"Track {t_idx + 1}, note {n_idx + 1}: "
                                f"macro '{ref}' is not defined"
                            )
                            expanded_notes.append(note_obj)
                            continue

                        # Expand: deep copy macro notes to avoid mutation issues
                        expanded_notes.extend(copy.deepcopy(macros[ref]))
                    else:
                        expanded_notes.append(note_obj)

                track["notes"] = expanded_notes

    # Remove macros field after expansion
    if macros_present:
        del json_data["macros"]

    return errors


def validate(json_data: dict) -> tuple:
    """
    Validate the completeness and legality of a score JSON dictionary, and auto-fill
    missing default values.

    Supports macro expansion: if the JSON contains a top-level "macros" field,
    macro references {"ref": "macro_name"} in notes arrays are expanded before
    validation.

    Validation rules:
      - metadata must exist with tempo_bpm (int) and time_signature (string "x/y")
      - tracks must exist and be a non-empty array
      - each track must have instrument (string) and notes (non-empty array)
      - each note must have pitch (int or None, -1 for rest) and duration (string)
      - pitch must be in 21-108 range if provided as an integer
      - duration must be a valid duration string
      - velocity is optional (default 80), must be 0-127 if provided
      - articulation, dynamics, tie, slur, lyric, etc. are optional with constraints
      - chord, time_signature_change, key_signature_change, arpeggio, tremolo,
        glissando, navigation, hairpin, tempo_gradual, subito, expression are optional
      - Fills in missing defaults: title, composer, velocity

    Args:
        json_data: The score JSON dictionary to validate.

    Returns:
        tuple: (is_valid, errors), where is_valid is a bool and errors is a list of
               error message strings (empty if valid).
    """
    errors = []

    # ---------- Type check ----------
    if not isinstance(json_data, dict):
        errors.append("JSON data must be an object (not an array or scalar)")
        return (False, errors)

    # ---------- Expand macros (if present) ----------
    errors.extend(_expand_macros(json_data))

    # ---------- Fill defaults ----------
    if "title" not in json_data or json_data.get("title") is None:
        json_data["title"] = _DEFAULT_TITLE
    if "composer" not in json_data or json_data.get("composer") is None:
        json_data["composer"] = _DEFAULT_COMPOSER

    # ---------- metadata validation ----------
    metadata = json_data.get("metadata")
    if metadata is None or not isinstance(metadata, dict):
        errors.append("metadata must exist and be an object")
    else:
        tempo = metadata.get("tempo_bpm")
        if tempo is None or not isinstance(tempo, int):
            errors.append("metadata.tempo_bpm must exist and be an integer")

        time_sig = metadata.get("time_signature")
        if time_sig is None or not isinstance(time_sig, str):
            errors.append("metadata.time_signature must exist and be a string")
        else:
            parts = time_sig.split("/")
            if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
                errors.append("metadata.time_signature format must be x/y (e.g. 4/4)")

        # anacrusis validation (optional - for pickup measures)
        anacrusis = metadata.get("anacrusis")
        if anacrusis is not None:
            if not isinstance(anacrusis, bool):
                errors.append("metadata.anacrusis must be a boolean (true/false)")

    # ---------- tracks validation ----------
    tracks = json_data.get("tracks")
    if tracks is None or not isinstance(tracks, list):
        errors.append("tracks must exist and be an array")
    elif len(tracks) == 0:
        errors.append("tracks cannot be an empty array")
    else:
        for t_idx, track in enumerate(tracks):
            track_num = t_idx + 1

            if not isinstance(track, dict):
                errors.append(f"Track {track_num} must be an object")
                continue

            instrument = track.get("instrument")
            if instrument is None or not isinstance(instrument, str):
                errors.append(f"Track {track_num} instrument must exist and be a string")

            # Check for voices field (new multivoice support)
            voices = track.get("voices")
            notes = track.get("notes")
            
            # Validate voices structure
            if voices is not None:
                if not isinstance(voices, list):
                    errors.append(f"Track {track_num} voices must be an array")
                elif len(voices) == 0:
                    errors.append(f"Track {track_num} voices cannot be an empty array")
                else:
                    # Validate each voice
                    for v_idx, voice in enumerate(voices):
                        voice_num = v_idx + 1
                        if not isinstance(voice, dict):
                            errors.append(f"Track {track_num}, voice {voice_num} must be an object")
                            continue
                        
                        # Validate voice name
                        voice_name = voice.get("name")
                        if voice_name is None or not isinstance(voice_name, str):
                            errors.append(f"Track {track_num}, voice {voice_num} name must exist and be a string")
                        elif len(voice_name) > _VOICE_NAME_MAX_LENGTH:
                            errors.append(f"Track {track_num}, voice {voice_num} name exceeds {_VOICE_NAME_MAX_LENGTH} characters")
                        
                        # Validate voice notes
                        voice_notes = voice.get("notes")
                        if voice_notes is None or not isinstance(voice_notes, list):
                            errors.append(f"Track {track_num}, voice {voice_num} notes must exist and be an array")
                        elif len(voice_notes) == 0:
                            errors.append(f"Track {track_num}, voice {voice_num} notes cannot be an empty array")
                        else:
                            # Validate each note in voice (reuse existing note validation logic)
                            for n_idx, note in enumerate(voice_notes):
                                note_num = n_idx + 1
                                if not isinstance(note, dict):
                                    errors.append(f"Track {track_num}, voice {voice_num}, note {note_num} must be an object")
                                    continue
                                
                                # pitch validation (optional if chord is present)
                                pitch = note.get("pitch")
                                has_chord = note.get("chord") is not None
                                if pitch is None and not has_chord:
                                    errors.append(f"Track {track_num}, voice {voice_num}, note {note_num} pitch must exist (or provide chord)")
                                elif pitch is not None and not isinstance(pitch, int):
                                    errors.append(f"Track {track_num}, voice {voice_num}, note {note_num} pitch must be an integer or null (-1 for rest)")
                                elif pitch is not None and pitch != -1 and (pitch < 21 or pitch > 108):
                                    errors.append(
                                        f"Track {track_num}, voice {voice_num}, note {note_num} pitch value {pitch} out of range 21-108"
                                    )
                                
                                # duration validation
                                duration = note.get("duration")
                                if duration is None or not isinstance(duration, str):
                                    errors.append(f"Track {track_num}, voice {voice_num}, note {note_num} duration must exist and be a string")
                                elif not _is_valid_duration(duration):
                                    errors.append(
                                        f"Track {track_num}, voice {voice_num}, note {note_num} duration '{duration}' is not a valid duration"
                                    )
                                
                                # velocity fill and validation
                                velocity = note.get("velocity")
                                if velocity is None:
                                    note["velocity"] = _DEFAULT_VELOCITY
                                elif not isinstance(velocity, int) or velocity < 0 or velocity > 127:
                                    errors.append(
                                        f"Track {track_num}, voice {voice_num}, note {note_num} velocity must be in 0-127 range"
                                    )
            
            # If no voices, validate original notes structure (backward compatibility)
            elif notes is None or not isinstance(notes, list):
                errors.append(f"Track {track_num} notes must exist and be an array (or add voices for multivoice support)")
            elif len(notes) == 0:
                errors.append(f"Track {track_num} notes cannot be an empty array")
            else:
                for n_idx, note in enumerate(notes):
                    note_num = n_idx + 1

                    if not isinstance(note, dict):
                        errors.append(f"Track {track_num}, note {note_num} must be an object")
                        continue

                    # pitch validation (optional if chord is present)
                    pitch = note.get("pitch")
                    has_chord = note.get("chord") is not None
                    if pitch is None and not has_chord:
                        errors.append(f"Track {track_num}, note {note_num} pitch must exist (or provide chord)")
                    elif pitch is not None and not isinstance(pitch, int):
                        errors.append(f"Track {track_num}, note {note_num} pitch must be an integer or null (-1 for rest)")
                    elif pitch is not None and pitch != -1 and (pitch < 21 or pitch > 108):
                        errors.append(
                            f"Track {track_num}, note {note_num} pitch value {pitch} out of range 21-108"
                        )

                    # duration validation
                    duration = note.get("duration")
                    if duration is None or not isinstance(duration, str):
                        errors.append(f"Track {track_num}, note {note_num} duration must exist and be a string")
                    elif not _is_valid_duration(duration):
                        errors.append(
                            f"Track {track_num}, note {note_num} duration '{duration}' is not a valid duration"
                        )

                    # velocity fill and validation
                    velocity = note.get("velocity")
                    if velocity is None:
                        note["velocity"] = _DEFAULT_VELOCITY
                    elif not isinstance(velocity, int) or velocity < 0 or velocity > 127:
                        errors.append(
                            f"Track {track_num}, note {note_num} velocity must be in 0-127 range"
                        )

                    # tuplet validation (optional)
                    tuplet = note.get("tuplet")
                    if tuplet is not None:
                        if not isinstance(tuplet, int):
                            errors.append(
                                f"Track {track_num}, note {note_num} tuplet must be an integer"
                            )
                        elif tuplet < 2:
                            errors.append(
                                f"Track {track_num}, note {note_num} tuplet value {tuplet} is invalid, "
                                f"tuplet actual note count must be >= 2"
                            )
                        elif tuplet not in _VALID_TUPLETS:
                            errors.append(
                                f"Track {track_num}, note {note_num} tuplet value {tuplet} is invalid, "
                                f"only {sorted(_VALID_TUPLETS)} supported (e.g. 3=triplet, 5=quintuplet)"
                            )

                    # articulation validation (optional)
                    articulation = note.get("articulation")
                    if articulation is not None:
                        if not isinstance(articulation, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} articulation must be a string"
                            )
                        elif articulation not in _VALID_ARTICULATIONS:
                            errors.append(
                                f"Track {track_num}, note {note_num} articulation value '{articulation}' is invalid, "
                                f"only {sorted(_VALID_ARTICULATIONS)} supported"
                            )

                    # dynamics validation (optional)
                    dynamics = note.get("dynamics")
                    if dynamics is not None:
                        if not isinstance(dynamics, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} dynamics must be a string"
                            )
                        elif dynamics not in _VALID_DYNAMICS:
                            errors.append(
                                f"Track {track_num}, note {note_num} dynamics value '{dynamics}' is invalid, "
                                f"only {sorted(_VALID_DYNAMICS)} supported"
                            )

                    # tie validation (optional)
                    tie = note.get("tie")
                    if tie is not None:
                        if not isinstance(tie, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} tie must be a string"
                            )
                        elif tie not in ("start", "stop", "continue"):
                            errors.append(
                                f"Track {track_num}, note {note_num} tie value '{tie}' is invalid, "
                                f"only 'start', 'stop', or 'continue' supported"
                            )

                    # slur validation (optional)
                    slur = note.get("slur")
                    if slur is not None:
                        if not isinstance(slur, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} slur must be a string"
                            )
                        elif slur not in ("start", "stop", "continue"):
                            errors.append(
                                f"Track {track_num}, note {note_num} slur value '{slur}' is invalid, "
                                f"only 'start', 'stop', or 'continue' supported"
                            )

                    # lyric validation (optional)
                    lyric = note.get("lyric")
                    if lyric is not None:
                        if not isinstance(lyric, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} lyric must be a string"
                            )
                        elif len(lyric) > 100:
                            errors.append(
                                f"Track {track_num}, note {note_num} lyric length exceeds 100 characters"
                            )

                    # grace_note validation (optional)
                    grace_note = note.get("grace_note")
                    if grace_note is not None:
                        if not isinstance(grace_note, dict):
                            errors.append(
                                f"Track {track_num}, note {note_num} grace_note must be an object"
                            )
                        else:
                            gn_pitch = grace_note.get("pitch")
                            if gn_pitch is None or not isinstance(gn_pitch, int):
                                errors.append(
                                    f"Track {track_num}, note {note_num} grace_note.pitch must exist and be an integer"
                                )
                            elif gn_pitch != -1 and (gn_pitch < 21 or gn_pitch > 108):
                                errors.append(
                                    f"Track {track_num}, note {note_num} grace_note.pitch value {gn_pitch} out of range 21-108"
                                )
                            gn_duration = grace_note.get("duration")
                            if gn_duration is not None:
                                if not isinstance(gn_duration, str) or not _is_valid_duration(gn_duration):
                                    errors.append(
                                        f"Track {track_num}, note {note_num} grace_note.duration '{gn_duration}' is not a valid duration"
                                    )

                    # ornament validation (optional)
                    ornament = note.get("ornament")
                    if ornament is not None:
                        if not isinstance(ornament, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} ornament must be a string"
                            )
                        elif ornament not in _VALID_ORNAMENTS:
                            errors.append(
                                f"Track {track_num}, note {note_num} ornament value '{ornament}' is invalid, "
                                f"only {sorted(_VALID_ORNAMENTS)} supported"
                            )

                    # tempo_change validation (optional)
                    tempo_change = note.get("tempo_change")
                    if tempo_change is not None:
                        if not isinstance(tempo_change, int):
                            errors.append(
                                f"Track {track_num}, note {note_num} tempo_change must be an integer (BPM)"
                            )
                        elif tempo_change < 20 or tempo_change > 300:
                            errors.append(
                                f"Track {track_num}, note {note_num} tempo_change value {tempo_change} out of range 20-300"
                            )

                    # text validation (optional)
                    text = note.get("text")
                    if text is not None:
                        if not isinstance(text, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} text must be a string"
                            )
                        elif len(text) > 200:
                            errors.append(
                                f"Track {track_num}, note {note_num} text length exceeds 200 characters"
                            )

                    # fermata validation (optional)
                    fermata = note.get("fermata")
                    if fermata is not None:
                        if not isinstance(fermata, bool):
                            errors.append(
                                f"Track {track_num}, note {note_num} fermata must be a boolean (true/false)"
                            )

                    # pedal validation (optional)
                    pedal = note.get("pedal")
                    if pedal is not None:
                        if not isinstance(pedal, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} pedal must be a string"
                            )
                        elif pedal not in ("start", "stop", "continue"):
                            errors.append(
                                f"Track {track_num}, note {note_num} pedal value '{pedal}' is invalid, "
                                f"only 'start', 'stop', or 'continue' supported"
                            )

                    # ---------- Expressive field validation ----------

                    # hairpin validation (optional)
                    hairpin = note.get("hairpin")
                    if hairpin is not None:
                        if not isinstance(hairpin, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} hairpin must be a string"
                            )
                        elif hairpin not in ("crescendo", "diminuendo", "stop"):
                            errors.append(
                                f"Track {track_num}, note {note_num} hairpin value '{hairpin}' is invalid, "
                                f"only 'crescendo', 'diminuendo', or 'stop' supported"
                            )

                    # tempo_gradual validation (optional)
                    tempo_gradual = note.get("tempo_gradual")
                    if tempo_gradual is not None:
                        if not isinstance(tempo_gradual, dict):
                            errors.append(
                                f"Track {track_num}, note {note_num} tempo_gradual must be an object"
                            )
                        else:
                            tg_target = tempo_gradual.get("target_bpm")
                            if tg_target is None or not isinstance(tg_target, int):
                                errors.append(
                                    f"Track {track_num}, note {note_num} tempo_gradual.target_bpm must exist and be an integer"
                                )
                            elif tg_target < 20 or tg_target > 300:
                                errors.append(
                                    f"Track {track_num}, note {note_num} tempo_gradual.target_bpm value {tg_target} out of range 20-300"
                                )
                            tg_duration = tempo_gradual.get("duration_beats")
                            if tg_duration is not None:
                                if not isinstance(tg_duration, (int, float)):
                                    errors.append(
                                        f"Track {track_num}, note {note_num} tempo_gradual.duration_beats must be a number"
                                    )
                                elif tg_duration <= 0 or tg_duration > 100:
                                    errors.append(
                                        f"Track {track_num}, note {note_num} tempo_gradual.duration_beats value {tg_duration} out of range 0.1-100"
                                    )

                    # subito validation (optional)
                    subito = note.get("subito")
                    if subito is not None:
                        if not isinstance(subito, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} subito must be a string"
                            )
                        elif subito not in _VALID_DYNAMICS:
                            errors.append(
                                f"Track {track_num}, note {note_num} subito value '{subito}' is invalid, "
                                f"only valid dynamics markings supported: {sorted(_VALID_DYNAMICS)}"
                            )

                    # anacrusis validation (optional - for pickup measures)
                    anacrusis = note.get("anacrusis")
                    if anacrusis is not None:
                        if not isinstance(anacrusis, bool):
                            errors.append(
                                f"Track {track_num}, note {note_num} anacrusis must be a boolean (true/false)"
                            )

                    # ottava validation (optional - for octave transposition)
                    ottava = note.get("ottava")
                    if ottava is not None:
                        if not isinstance(ottava, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} ottava must be a string"
                            )
                        elif ottava not in ("8va", "8vb", "15ma", "15mb"):
                            errors.append(
                                f"Track {track_num}, note {note_num} ottava value '{ottava}' is invalid, "
                                f"only '8va', '8vb', '15ma', '15mb' supported"
                            )

                    # expression validation (optional)
                    expression = note.get("expression")
                    if expression is not None:
                        if not isinstance(expression, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} expression must be a string"
                            )
                        elif len(expression) > 200:
                            errors.append(
                                f"Track {track_num}, note {note_num} expression length exceeds 200 characters"
                            )

                    # ---------- JSON Schema-like field validation ----------

                    # chord validation (optional)
                    chord = note.get("chord")
                    if chord is not None:
                        if not isinstance(chord, list):
                            errors.append(
                                f"Track {track_num}, note {note_num} chord must be an array of integers"
                            )
                        elif len(chord) == 0:
                            errors.append(
                                f"Track {track_num}, note {note_num} chord cannot be empty"
                            )
                        else:
                            for i, p in enumerate(chord):
                                if not isinstance(p, int):
                                    errors.append(
                                        f"Track {track_num}, note {note_num} chord pitch {i+1} must be an integer"
                                    )
                                elif p != -1 and (p < 21 or p > 108):
                                    errors.append(
                                        f"Track {track_num}, note {note_num} chord pitch {p} out of range 21-108"
                                    )

                    # time_signature_change validation (optional)
                    time_sig_change = note.get("time_signature_change")
                    if time_sig_change is not None:
                        if not isinstance(time_sig_change, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} time_signature_change must be a string"
                            )
                        else:
                            parts = time_sig_change.split("/")
                            if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
                                errors.append(
                                    f"Track {track_num}, note {note_num} time_signature_change format must be x/y (e.g. 3/4)"
                                )

                    # key_signature_change validation (optional)
                    key_sig_change = note.get("key_signature_change")
                    if key_sig_change is not None:
                        if not isinstance(key_sig_change, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} key_signature_change must be a string"
                            )

                    # arpeggio validation (optional)
                    arpeggio = note.get("arpeggio")
                    if arpeggio is not None:
                        if not isinstance(arpeggio, bool):
                            errors.append(
                                f"Track {track_num}, note {note_num} arpeggio must be a boolean"
                            )

                    # tremolo validation (optional)
                    tremolo = note.get("tremolo")
                    if tremolo is not None:
                        if not isinstance(tremolo, dict):
                            errors.append(
                                f"Track {track_num}, note {note_num} tremolo must be an object"
                            )
                        else:
                            trem_dur = tremolo.get("duration")
                            if trem_dur is not None:
                                if not isinstance(trem_dur, str) or not _is_valid_duration(trem_dur):
                                    errors.append(
                                        f"Track {track_num}, note {note_num} tremolo.duration '{trem_dur}' is not a valid duration"
                                    )

                    # glissando validation (optional)
                    glissando = note.get("glissando")
                    if glissando is not None:
                        if not isinstance(glissando, bool):
                            errors.append(
                                f"Track {track_num}, note {note_num} glissando must be a boolean"
                            )

                    # navigation validation (optional)
                    navigation = note.get("navigation")
                    if navigation is not None:
                        if not isinstance(navigation, str):
                            errors.append(
                                f"Track {track_num}, note {note_num} navigation must be a string"
                            )
                        elif navigation not in ("D.C.", "D.S.", "Coda", "Fine"):
                            errors.append(
                                f"Track {track_num}, note {note_num} navigation value '{navigation}' is invalid, "
                                f"only 'D.C.', 'D.S.', 'Coda', 'Fine' supported"
                            )

            # Track-level field validation
            repeat_begin = track.get("repeat_begin")
            if repeat_begin is not None:
                if not isinstance(repeat_begin, bool):
                    errors.append(f"Track {track_num} repeat_begin must be a boolean")

            repeat_end = track.get("repeat_end")
            if repeat_end is not None:
                if not isinstance(repeat_end, bool):
                    errors.append(f"Track {track_num} repeat_end must be a boolean")

            volta = track.get("volta")
            if volta is not None:
                if not isinstance(volta, int):
                    errors.append(f"Track {track_num} volta must be an integer")
                elif volta < 1 or volta > 4:
                    errors.append(f"Track {track_num} volta value {volta} out of range 1-4")

            # instrument_transpose validation (optional)
            instrument_transpose = track.get("instrument_transpose")
            if instrument_transpose is not None:
                if not isinstance(instrument_transpose, str):
                    errors.append(f"Track {track_num} instrument_transpose must be a string")
                elif instrument_transpose not in _VALID_TRANSPOSE_INTERVALS:
                    errors.append(f"Track {track_num} instrument_transpose value '{instrument_transpose}' is invalid, "
                                  f"only semitone intervals from -12 to 12 are supported")

            # barline validation (optional)
            barline = track.get("barline")
            if barline is not None:
                if not isinstance(barline, str):
                    errors.append(f"Track {track_num} barline must be a string")
                elif barline not in _VALID_BARLINE_STYLES:
                    errors.append(f"Track {track_num} barline value '{barline}' is invalid, "
                                  f"only {sorted(_VALID_BARLINE_STYLES)} supported")

    return (len(errors) == 0, errors)