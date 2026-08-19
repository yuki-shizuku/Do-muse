"""
Do Muse — JSON 验证器单元测试
"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.json_validator import validate


class TestJsonValidator(unittest.TestCase):
    """json_validator.validate() 的单元测试。"""

    def _make_valid_score(self) -> dict:
        """创建一个有效的乐谱 JSON 字典。"""
        return {
            "title": "Test Score",
            "composer": "Test Composer",
            "metadata": {
                "tempo_bpm": 120,
                "time_signature": "4/4",
                "key_signature": "C",
            },
            "tracks": [
                {
                    "instrument": "Acoustic Grand Piano",
                    "notes": [
                        {"pitch": 60, "duration": "quarter", "velocity": 80},
                        {"pitch": 64, "duration": "quarter", "velocity": 80},
                    ],
                }
            ],
        }

    def test_valid_score(self):
        """测试有效乐谱通过验证。"""
        is_valid, errors = validate(self._make_valid_score())
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])

    def test_missing_title_uses_default(self):
        """测试缺少 title 字段时使用默认值，验证仍然通过。"""
        score = self._make_valid_score()
        del score["title"]
        is_valid, errors = validate(score)
        self.assertTrue(is_valid)  # title 缺失时自动填充默认值

    def test_missing_tracks(self):
        """测试缺少 tracks 字段。"""
        score = self._make_valid_score()
        del score["tracks"]
        is_valid, errors = validate(score)
        self.assertFalse(is_valid)

    def test_empty_tracks(self):
        """测试空 tracks 数组。"""
        score = self._make_valid_score()
        score["tracks"] = []
        is_valid, errors = validate(score)
        self.assertFalse(is_valid)

    def test_pitch_out_of_range(self):
        """测试音高超出范围 (21-108)。"""
        score = self._make_valid_score()
        score["tracks"][0]["notes"][0]["pitch"] = 10
        is_valid, errors = validate(score)
        self.assertFalse(is_valid)

    def test_pitch_too_high(self):
        """测试音高过高 (>108)。"""
        score = self._make_valid_score()
        score["tracks"][0]["notes"][0]["pitch"] = 200
        is_valid, errors = validate(score)
        self.assertFalse(is_valid)

    def test_rest_pitch(self):
        """测试休止符 pitch=-1。"""
        score = self._make_valid_score()
        score["tracks"][0]["notes"][0]["pitch"] = -1
        is_valid, errors = validate(score)
        self.assertTrue(is_valid)

    def test_invalid_duration(self):
        """测试无效时值字符串。"""
        score = self._make_valid_score()
        score["tracks"][0]["notes"][0]["duration"] = "invalid"
        is_valid, errors = validate(score)
        self.assertFalse(is_valid)

    def test_repeat_begin_validation(self):
        """测试 repeat_begin 字段类型校验。"""
        score = self._make_valid_score()
        score["tracks"][0]["repeat_begin"] = True
        is_valid, _ = validate(score)
        self.assertTrue(is_valid)

        score["tracks"][0]["repeat_begin"] = "yes"
        is_valid, errors = validate(score)
        self.assertFalse(is_valid)

    def test_volta_range(self):
        """测试 volta 范围 (1-4)。"""
        score = self._make_valid_score()
        score["tracks"][0]["volta"] = 1
        is_valid, _ = validate(score)
        self.assertTrue(is_valid)

        score["tracks"][0]["volta"] = 5
        is_valid, errors = validate(score)
        self.assertFalse(is_valid)

    def test_volta_in_second_track(self):
        """测试第二个轨道的 volta 字段也被校验（回归测试：缩进 bug）。"""
        score = self._make_valid_score()
        score["tracks"].append({
            "instrument": "Violin",
            "notes": [{"pitch": 67, "duration": "quarter", "velocity": 70}],
            "volta": "invalid",  # 应为 int
        })
        is_valid, errors = validate(score)
        self.assertFalse(is_valid)
        # 确保错误信息提到 Track 2
        self.assertTrue(any("Track 2" in e for e in errors))


if __name__ == "__main__":
    unittest.main()
