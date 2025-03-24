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


if __name__ == "__main__":
    unittest.main()
