import unittest
from RegularExpression import RegexEngine


class TestRegexComponents(unittest.TestCase):
    def test_literal_match(self):
        engine = RegexEngine("a")
        self.assertTrue(engine.match("a"))
        self.assertFalse(engine.match("b"))

    def test_char_class(self):
        engine = RegexEngine(r"[a-z]")
        self.assertFalse(engine.match("2"))


class TestQuantifiers(unittest.TestCase):
    def test_star_quantifier(self):
        engine = RegexEngine(r"a*")
        self.assertFalse(engine.match(""))

    def test_plus_quantifier(self):
        engine = RegexEngine(r"a+")
        self.assertFalse(engine.match(""))


class TestSpecialConstructs(unittest.TestCase):
    def test_anchors(self):
        engine = RegexEngine(r"^a+$")
        self.assertFalse(engine.match("aaab"))


class TestComplexExamples(unittest.TestCase):
    def test_time_parser(self):
        engine = RegexEngine(r"^([01]\d|2[0-3]):[0-5]\d:[0-5]\d$")
        self.assertFalse(engine.match("24:00:00"))

    def test_json_parser(self):
        engine = RegexEngine(r'"\w+":\s*("[^"]*"|\d+)')
        self.assertFalse(engine.match(""))


class TestInputValidation(unittest.TestCase):
    def test_invalid_patterns(self):
        with self.assertRaises(ValueError):
            RegexEngine("[invalid")
        with self.assertRaises(ValueError):
            RegexEngine(r"\q")


class TestSearchSubSplit(unittest.TestCase):
    def test_search(self):
        # 测试 search 功能能够找到子串，并正确返回匹配信息
        engine = RegexEngine("world")
        match = engine.search("hello world!")
        self.assertIsNotNone(match)
        self.assertEqual(match.group, "world")
        self.assertEqual(match.start, 6)
        self.assertEqual(match.end, 11)

        # 当目标子串不存在时，返回 None
        self.assertIsNone(engine.search("hello there"))

        # 其它示例：使用正则表达式匹配日期中的时间
        engine = RegexEngine(r"(?:[01]\d|2[0-3]):[0-5]\d")
        match = engine.search("The meeting is at 14:45.")
        self.assertIsNotNone(match)
        self.assertEqual(match.group, "14:45")

    def test_sub(self):
        # 测试 sub 可以将匹配的部分替换掉
        engine = RegexEngine("hello")
        self.assertEqual(engine.sub("hi", "hello there"), "hi there")

        # 测试用正则表达式匹配数字，然后全部替换
        engine = RegexEngine(r"\d+")
        self.assertEqual(
            engine.sub("num", "There are 2 apples and 3 oranges"),
            "There are num apples and num oranges"
        )

        # 测试 sub 限制替换次数
        engine = RegexEngine(r"cat")
        self.assertEqual(engine.sub(
            "dog", "cat cat cat", count=2), "dog dog cat")

    def test_split(self):
        # 测试 split 能按照匹配内容拆分字符串
        engine = RegexEngine(r",\s*")
        self.assertEqual(engine.split("a, b, c"), ["a", "b", "c"])

        # 使用空白字符进行拆分
        engine = RegexEngine(r"\s+")
        self.assertEqual(engine.split("hello   world  program"
                                      ), ["hello", "world", "program"])

        # 当匹配在字符串中不存在时，split 应返回整个字符串的列表形式
        engine = RegexEngine(r",")
        self.assertEqual(engine.split("abc"), ["abc"])


if __name__ == "__main__":
    unittest.main()
