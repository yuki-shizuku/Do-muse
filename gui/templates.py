"""
Do Muse — JSON score templates

Pre-built JSON templates for common score configurations.
Used by the main window to provide quick-start options.
"""

TEMPLATES: dict[str, dict] = {
    "macro_demo": {
        "title": "Macro Demo",
        "composer": "Do Muse",
        "metadata": {
            "tempo_bpm": 120,
            "time_signature": "4/4",
            "key_signature": "C"
        },
        "macros": {
            "bass_line": [
                {"pitch": 36, "duration": "quarter", "velocity": 75},
                {"pitch": 43, "duration": "quarter", "velocity": 75},
                {"pitch": 40, "duration": "quarter", "velocity": 75},
                {"pitch": 48, "duration": "quarter", "velocity": 75}
            ],
            "chord_hit": [
                {"chord": [60, 64, 67], "duration": "half", "velocity": 85, "arpeggio": True}
            ]
        },
        "tracks": [
            {
                "instrument": "Acoustic Grand Piano",
                "notes": [
                    {"ref": "bass_line"},
                    {"ref": "chord_hit"},
                    {"ref": "bass_line"},
                    {"ref": "chord_hit"},
                    {"pitch": 72, "duration": "whole", "velocity": 90}
                ]
            }
        ]
    },
    "blank": {
        "title": "Untitled",
        "composer": "Unknown",
        "metadata": {
            "tempo_bpm": 120,
            "time_signature": "4/4",
            "key_signature": "C"
        },
        "tracks": [
            {
                "instrument": "Acoustic Grand Piano",
                "notes": [
                    {"pitch": 60, "duration": "quarter", "velocity": 80},
                    {"pitch": -1, "duration": "quarter", "velocity": 0}
                ]
            }
        ]
    },
    "piano": {
        "title": "Piano Solo",
        "composer": "Do Muse",
        "metadata": {
            "tempo_bpm": 120,
            "time_signature": "4/4",
            "key_signature": "C"
        },
        "tracks": [
            {
                "instrument": "Acoustic Grand Piano",
                "notes": [
                    {"pitch": 60, "duration": "quarter", "velocity": 80},
                    {"pitch": 64, "duration": "quarter", "velocity": 80},
                    {"pitch": 67, "duration": "quarter", "velocity": 80},
                    {"pitch": 72, "duration": "half", "velocity": 85}
                ]
            }
        ]
    },
    "duo": {
        "title": "Duo",
        "composer": "Do Muse",
        "metadata": {
            "tempo_bpm": 110,
            "time_signature": "4/4",
            "key_signature": "G"
        },
        "tracks": [
            {
                "instrument": "Violin",
                "notes": [
                    {"pitch": 67, "duration": "half", "velocity": 75},
                    {"pitch": 69, "duration": "half", "velocity": 75}
                ]
            },
            {
                "instrument": "Cello",
                "notes": [
                    {"pitch": 48, "duration": "whole", "velocity": 70}
                ]
            }
        ]
    },
    "scale": {
        "title": "C Major Scale",
        "composer": "Do Muse",
        "metadata": {
            "tempo_bpm": 100,
            "time_signature": "4/4",
            "key_signature": "C"
        },
        "tracks": [
            {
                "instrument": "Acoustic Grand Piano",
                "notes": [
                    {"pitch": 60, "duration": "quarter", "velocity": 80},
                    {"pitch": 62, "duration": "quarter", "velocity": 80},
                    {"pitch": 64, "duration": "quarter", "velocity": 80},
                    {"pitch": 65, "duration": "quarter", "velocity": 80},
                    {"pitch": 67, "duration": "quarter", "velocity": 85},
                    {"pitch": 69, "duration": "quarter", "velocity": 85},
                    {"pitch": 71, "duration": "quarter", "velocity": 85},
                    {"pitch": 72, "duration": "half", "velocity": 90}
                ]
            }
        ]
    },
    "piano_duet": {
        "title": "Piano Duet (Four Hands)",
        "composer": "Do Muse",
        "metadata": {
            "tempo_bpm": 100,
            "time_signature": "4/4",
            "key_signature": "C"
        },
        "tracks": [
            {
                "instrument": "Acoustic Grand Piano",
                "voices": [
                    {
                        "name": "Primo",
                        "notes": [
                            {"pitch": 72, "duration": "quarter", "velocity": 80},
                            {"pitch": 76, "duration": "quarter", "velocity": 80},
                            {"pitch": 79, "duration": "quarter", "velocity": 85},
                            {"pitch": 84, "duration": "half", "velocity": 90, "fermata": True}
                        ]
                    },
                    {
                        "name": "Secondo",
                        "notes": [
                            {"chord": [48, 52, 55], "duration": "half", "velocity": 75},
                            {"chord": [50, 53, 57], "duration": "half", "velocity": 75},
                            {"chord": [45, 49, 52], "duration": "half", "velocity": 75},
                            {"pitch": 48, "duration": "half", "velocity": 80, "fermata": True}
                        ]
                    }
                ]
            }
        ]
    },
    "satb_choir": {
        "title": "SATB Choir",
        "composer": "Do Muse",
        "metadata": {
            "tempo_bpm": 90,
            "time_signature": "4/4",
            "key_signature": "G"
        },
        "tracks": [
            {
                "instrument": "Choir Aahs",
                "voices": [
                    {
                        "name": "Soprano",
                        "notes": [
                            {"pitch": 67, "duration": "whole", "velocity": 75, "lyric": "A"},
                            {"pitch": 72, "duration": "whole", "velocity": 75, "lyric": "men"},
                            {"pitch": 74, "duration": "whole", "velocity": 78, "lyric": "a"},
                            {"pitch": 67, "duration": "whole", "velocity": 75, "lyric": "men"}
                        ]
                    },
                    {
                        "name": "Alto",
                        "notes": [
                            {"pitch": 62, "duration": "whole", "velocity": 70, "lyric": "A"},
                            {"pitch": 64, "duration": "whole", "velocity": 70, "lyric": "men"},
                            {"pitch": 66, "duration": "whole", "velocity": 72, "lyric": "a"},
                            {"pitch": 62, "duration": "whole", "velocity": 70, "lyric": "men"}
                        ]
                    },
                    {
                        "name": "Tenor",
                        "notes": [
                            {"pitch": 59, "duration": "whole", "velocity": 70, "lyric": "A"},
                            {"pitch": 60, "duration": "whole", "velocity": 70, "lyric": "men"},
                            {"pitch": 62, "duration": "whole", "velocity": 72, "lyric": "a"},
                            {"pitch": 59, "duration": "whole", "velocity": 70, "lyric": "men"}
                        ]
                    },
                    {
                        "name": "Bass",
                        "notes": [
                            {"pitch": 43, "duration": "whole", "velocity": 70, "lyric": "A"},
                            {"pitch": 48, "duration": "whole", "velocity": 70, "lyric": "men"},
                            {"pitch": 43, "duration": "whole", "velocity": 72, "lyric": "a"},
                            {"pitch": 43, "duration": "whole", "velocity": 70, "lyric": "men"}
                        ]
                    }
                ]
            }
        ]
    },
}
