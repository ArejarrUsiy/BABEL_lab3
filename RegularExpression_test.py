import unittest
from regex_engine import RegexEngine, validate_pattern

class TestRegexComponents(unittest.TestCase):
    def test_literal_match(self):
        engine = RegexEngine("a")
        self.assertTrue(engine.match("a"))
        self.assertFalse(engine.match("b"))
    
    def test_char_class(self):
        engine = RegexEngine(r"[a-z]")
        self.assertTrue(engine.match("c"))
        self.assertFalse(engine.match("2"))
        
        engine = RegexEngine(r"[^0-9]")
        self.assertTrue(engine.match("a"))
        self.assertFalse(engine.match("5"))

class TestQuantifiers(unittest.TestCase):
    def test_star_quantifier(self):
        engine = RegexEngine(r"a*")
        self.assertTrue(engine.match(""))
        self.assertTrue(engine.match("aaaaa"))
    
    def test_plus_quantifier(self):
        engine = RegexEngine(r"a+")
        self.assertFalse(engine.match(""))
        self.assertTrue(engine.match("aaa"))

class TestSpecialConstructs(unittest.TestCase):
    def test_anchors(self):
        engine = RegexEngine(r"^start.*end$")
        self.assertTrue(engine.match("start middle end"))
        self.assertFalse(engine.match(" startend "))

class TestComplexExamples(unittest.TestCase):
    def test_time_parser(self):
        class TimeParser(RegexEngine):
            @validate_pattern
            def __init__(self):
                pattern = r"^(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\d$"
                super().__init__(pattern)
        
        tp = TimeParser()
        self.assertTrue(tp.match("23:59:59"))
        self.assertFalse(tp.match("24:00:00"))

    def test_json_parser(self):
        class JsonParser(RegexEngine):
            @validate_pattern
            def __init__(self):
                pattern = r'"(\w+)":\s*("[^"]*"|\d+)'
                super().__init__(pattern)
            
            def parse(self, json_str):
                # 实现解析逻辑
                pass
        
        jp = JsonParser()
        self.assertTrue(jp.match('"key": "value"'))
        self.assertTrue(jp.match('"age": 25'))

class TestInputValidation(unittest.TestCase):
    def test_invalid_patterns(self):
        with self.assertRaises(ValueError):
            RegexEngine("[invalid")
        
        with self.assertRaises(ValueError):
            RegexEngine(r"\q")

if __name__ == "__main__":
    unittest.main()