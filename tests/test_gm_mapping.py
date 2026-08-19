"""
Do Muse — GM 乐器映射单元测试
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.gm_mapping import get_program_number, get_instrument_name


class TestGmMapping(unittest.TestCase):
    """GM 乐器映射双向一致性的单元测试。"""

    def test_piano_mapping(self):
        """测试钢琴的双向映射。"""
        self.assertEqual(get_instrument_name(0), "Acoustic Grand Piano")
        self.assertEqual(get_program_number("Acoustic Grand Piano"), 0)

    def test_viola_mapping(self):
        """测试中提琴的双向映射。"""
        name = get_instrument_name(41)
        prog = get_program_number(name)
        self.assertEqual(prog, 41)

    def test_cello_mapping(self):
        """测试大提琴的双向映射。"""
        name = get_instrument_name(42)
        prog = get_program_number(name)
        self.assertEqual(prog, 42)

    def test_unknown_instrument(self):
        """测试未知乐器名返回默认值 (0)。"""
        result = get_program_number("Nonexistent Instrument")
        self.assertEqual(result, 0)


if __name__ == "__main__":
    unittest.main()
