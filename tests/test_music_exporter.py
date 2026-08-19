"""
Do Muse — 乐谱导出器单元测试
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.music_exporter import (
    parse_duration,
    _get_clef_for_program,
    _create_dynamics,
    _create_articulation,
)


class TestParseDuration(unittest.TestCase):
    """parse_duration() 的单元测试。"""

    def test_quarter(self):
        """测试四分音符时值为 1.0。"""
        self.assertEqual(parse_duration("quarter"), 1.0)

    def test_half(self):
        """测试二分音符时值为 2.0。"""
        self.assertEqual(parse_duration("half"), 2.0)

    def test_whole(self):
        """测试全音符时值为 4.0。"""
        self.assertEqual(parse_duration("whole"), 4.0)

    def test_eighth(self):
        """测试八分音符时值为 0.5。"""
        self.assertEqual(parse_duration("eighth"), 0.5)

    def test_sixteenth(self):
        """测试十六分音符时值为 0.25。"""
        self.assertEqual(parse_duration("16th"), 0.25)

    def test_dotted_quarter(self):
        """测试附点四分音符时值为 1.5。"""
        self.assertEqual(parse_duration("quarter."), 1.5)


class TestGetClefForProgram(unittest.TestCase):
    """_get_clef_for_program() 的单元测试。"""

    def test_piano_treble(self):
        """测试钢琴（program=0）使用高音谱号。"""
        self.assertEqual(_get_clef_for_program(0), "treble")

    def test_cello_bass(self):
        """测试大提琴（program=42）使用低音谱号。"""
        self.assertEqual(_get_clef_for_program(42), "bass")

    def test_viola_alto(self):
        """测试中提琴（program=41）使用中音谱号。"""
        self.assertEqual(_get_clef_for_program(41), "alto")

    def test_timpani_bass(self):
        """测试定音鼓（program=47）使用低音谱号。"""
        self.assertEqual(_get_clef_for_program(47), "bass")

    def test_bassoon_bass(self):
        """测试大管（program=70）使用低音谱号。"""
        self.assertEqual(_get_clef_for_program(70), "bass")

    def test_flute_treble(self):
        """测试长笛（program=73）使用高音谱号。"""
        self.assertEqual(_get_clef_for_program(73), "treble")


class TestCreateDynamics(unittest.TestCase):
    """_create_dynamics() 的单元测试。"""

    def test_valid_dynamics(self):
        """测试有效力度标记返回新实例。"""
        from music21 import dynamics
        d1 = _create_dynamics("f")
        d2 = _create_dynamics("f")
        self.assertIsInstance(d1, dynamics.Dynamic)
        self.assertIsNot(d1, d2)  # 不是同一对象

    def test_invalid_dynamics(self):
        """测试无效力度标记返回 None。"""
        self.assertIsNone(_create_dynamics("invalid"))


class TestCreateArticulation(unittest.TestCase):
    """_create_articulation() 的单元测试。"""

    def test_valid_articulation(self):
        """测试有效演奏法标记返回新实例。"""
        from music21 import articulations
        a1 = _create_articulation("staccato")
        a2 = _create_articulation("staccato")
        self.assertIsInstance(a1, articulations.Staccato)
        self.assertIsNot(a1, a2)  # 不是同一对象

    def test_invalid_articulation(self):
        """测试无效演奏法标记返回 None。"""
        self.assertIsNone(_create_articulation("invalid"))


if __name__ == "__main__":
    unittest.main()
