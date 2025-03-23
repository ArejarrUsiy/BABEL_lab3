import logging
from graphviz import Digraph
from collections import deque
from functools import wraps
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RegexEngine")

# 输入验证装饰器
def validate_pattern(func):
    @wraps(func)
    def wrapper(pattern, *args, **kwargs):
        if not isinstance(pattern, str):
            logger.error("Pattern must be a string")
            raise ValueError("Invalid pattern type")
        if re.search(r"(?<!\\)\\[^dwsnrt\\^$.|?*+(){}[\]]", pattern):
            logger.error("Invalid escape sequence")
            raise ValueError("Invalid escape character")
        return func(pattern, *args, **kwargs)
    return wrapper

class State:
    """NFA状态节点"""
    _id = 0
    
    def __init__(self):
        self.id = State._id
        State._id += 1
        self.transitions = {}  # 字符: [目标状态]
        self.epsilon = []      # ε转移

class NFA:
    """NFA状态机"""
    def __init__(self, start: State, end: State):
        self.start = start
        self.end = end

class RegexComponent:
    def build_nfa(self) -> NFA:
        raise NotImplementedError

class Literal(RegexComponent):
    def __init__(self, char: str):
        self.char = char
    
    def build_nfa(self) -> NFA:
        start = State()
        end = State()
        start.transitions[self.char] = [end]
        return NFA(start, end)

class CharClass(RegexComponent):
    def __init__(self, positive: bool, chars: set):
        self.positive = positive
        self.chars = chars
    
    def build_nfa(self) -> NFA:
        start = State()
        end = State()
        start.transitions["class"] = (self.positive, self.chars)
        start.epsilon.append(end)
        return NFA(start, end)

class Quantifier(RegexComponent):
    def __init__(self, expr: RegexComponent, min_: int, max_: int):
        self.expr = expr
        self.min = min_
        self.max = max_
    
    def build_nfa(self) -> NFA:
        # 实现量词NFA构造
        pass

class RegexParser:
    def __init__(self, pattern: str):
        self.pattern = pattern
        self.pos = 0
    
    def parse(self) -> RegexComponent:
        # 解析主逻辑
        pass

class RegexEngine:
    @validate_pattern
    def __init__(self, pattern: str):
        self.pattern = pattern
        self.ast = RegexParser(pattern).parse()
        self.nfa = self.ast.build_nfa()
        logger.info(f"Built NFA with {State._id} states")
    
    def _nfa_simulation(self, text: str) -> bool:
        """NFA模拟引擎"""
        current = set()
        closure(self.nfa.start, current)
        
        for char in text:
            logger.debug(f"Processing '{char}' @ states {[s.id for s in current]}")
            next_states = set()
            
            for state in current:
                # 处理字符转移
                if char in state.transitions:
                    next_states.update(state.transitions[char])
                # 处理字符类
                if "class" in state.transitions:
                    positive, chars = state.transitions["class"]
                    if (char in chars) == positive:
                        next_states.update(state.epsilon)
            
            current = set()
            for s in next_states:
                closure(s, current)
        
        return any(s == self.nfa.end for s in current)
    
    @validate_pattern
    def match(self, text: str) -> bool:
        """从字符串开头匹配"""
        logger.info(f"Matching '{text}' with '{self.pattern}'")
        return self._nfa_simulation(text)
    
    def visualize(self) -> Digraph:
        """生成有限状态机图"""
        dot = Digraph()
        visited = set()
        queue = deque([self.nfa.start])
        
        while queue:
            state = queue.popleft()
            if state.id in visited:
                continue
            visited.add(state.id)
            
            shape = "doublecircle" if state == self.nfa.end else "circle"
            dot.node(str(state.id), shape=shape)
            
            # ε转移
            for eps in state.epsilon:
                dot.edge(str(state.id), str(eps.id), label="ε")
                if eps not in visited:
                    queue.append(eps)
            
            # 字符转移
            for char, targets in state.transitions.items():
                for target in targets:
                    label = {
                        "class": "CharClass",
                        "d": r"\d",
                        "w": r"\w"
                    }.get(char, char)
                    dot.edge(str(state.id), str(target.id), label=label)
                    if target not in visited:
                        queue.append(target)
        
        return dot

def closure(state: State, states: set):
    """计算ε闭包"""
    if state in states:
        return
    states.add(state)
    for eps in state.epsilon:
        closure(eps, states)