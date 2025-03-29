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
        engine = RegexEngine("world")
        match = engine.search("hello world!")
        self.assertIsNotNone(match)
        self.assertEqual(match.group, "world")
        self.assertEqual(match.start, 6)
        self.assertEqual(match.end, 11)

        self.assertIsNone(engine.search("hello there"))

        engine = RegexEngine(r"(?:[01]\d|2[0-3]):[0-5]\d")
        match = engine.search("The meeting is at 14:45.")
        self.assertIsNotNone(match)
        self.assertEqual(match.group, "14:45")

    def test_sub(self):
        engine = RegexEngine("hello")
        self.assertEqual(engine.sub("hi", "hello there"), "hi there")

        engine = RegexEngine(r"\d+")
        self.assertEqual(
            engine.sub("num", "There are 2 apples and 3 oranges"),
            "There are num apples and num oranges"
        )

        engine = RegexEngine(r"cat")
        self.assertEqual(engine.sub(
            "dog", "cat cat cat", count=2), "dog dog cat")

    def test_split(self):
        engine = RegexEngine(r",\s*")
        self.assertEqual(engine.split("a, b, c"), ["a", "b", "c"])

        engine = RegexEngine(r"\s+")
        self.assertEqual(engine.split("hello   world  program"
                                      ), ["hello", "world", "program"])

        engine = RegexEngine(r",")
        self.assertEqual(engine.split("abc"), ["abc"])


if __name__ == "__main__":
    unittest.main()
