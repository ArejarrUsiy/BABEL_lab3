import logging
# from graphviz import Digraph  # type: ignore
from collections import deque
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RegexEngine")


class State:
    _id = 0

    def __init__(self):
        self.id = State._id
        State._id += 1
        self.transitions = {}  # 字符到状态的映射
        self.epsilon = []      # ε-转移
        self.char_class = None  # 新增：存储字符类信息


class NFA:
    def __init__(self, start: State, end: State):
        self.start = start
        self.end = end


class RegexComponent:
    def build_nfa(self) -> NFA: raise NotImplementedError


class Literal(RegexComponent):

    def __init__(self, char: str): self.char = char

    def build_nfa(self) -> NFA:
        start = State()
        end = State()
        start.transitions[self.char] = [end]
        return NFA(start, end)


class CharClass(RegexComponent):

    def __init__(self, chars: set, positive=True):
        self.chars = chars
        self.positive = positive

    def build_nfa(self) -> NFA:
        start = State()
        end = State()
        start.char_class = (self.positive, self.chars)
        start.epsilon.append(end)
        return NFA(start, end)


class Quantifier(RegexComponent):

    def __init__(self, expr: RegexComponent, min_: int, max_: int):
        self.expr = expr
        self.min = min_
        self.max = max_

    def build_nfa(self) -> NFA:
        base_nfa = self.expr.build_nfa()
        start = State()
        end = State()

        # Minimum repetitions
        start.epsilon.append(base_nfa.start)
        for _ in range(self.min-1):
            base_nfa.end.epsilon.append(base_nfa.start)
            base_nfa.end = base_nfa.end.epsilon[0]

        # Optional repetitions
        if self.max == -1 or self.max > self.min:
            base_nfa.end.epsilon.append(base_nfa.start)
            base_nfa.end.epsilon.append(end)
        else:
            base_nfa.end.epsilon.append(end)

        return NFA(start, end)


class AnchorStart(RegexComponent):

    def build_nfa(self) -> NFA:
        start = State()
        return NFA(start, start)


class AnchorEnd(RegexComponent):
    def build_nfa(self) -> NFA:
        end = State()
        return NFA(end, end)


class RegexParser:
    def __init__(self, pattern: str):
        self.pattern = pattern
        self.pos = 0

    def parse(self) -> list:
        components = []
        while self.pos < len(self.pattern):
            char = self.pattern[self.pos]
            if char == '[':
                components.append(self._parse_char_class())
            elif char == '^':
                components.append(AnchorStart())
                self.pos += 1
            elif char == '$':
                components.append(AnchorEnd())
                self.pos += 1
            elif char == '.':
                components.append(CharClass(set(), False))  # Match any
                self.pos += 1
            elif char == '\\':
                self.pos += 1
                if self.pattern[self.pos] == 'd':
                    components.append(CharClass
                                      (set(str(i) for i in range(10))))
                elif self.pattern[self.pos] == 'w':
                    chars = set(chr(i) for i in range(97, 123))  # a-z
                    chars.update(chr(i) for i in range(65, 91))  # A-Z
                    chars.add('_')
                    components.append(CharClass(chars))
                self.pos += 1
            else:
                components.append(Literal(char))
                self.pos += 1
        return components

    def _parse_char_class(self):
        self.pos += 1  # Skip [
        positive = True
        if self.pattern[self.pos] == '^':
            positive = False
            self.pos += 1

        chars = set()
        while self.pos < len(self.pattern) and self.pattern[self.pos] != ']':
            if self.pattern[self.pos] == '-':
                # Handle ranges
                prev = self.pattern[self.pos-1]
                next_char = self.pattern[self.pos+1]
                chars.update(chr(c) for c in range
                             (ord(prev)+1, ord(next_char)+1))
                self.pos += 2
            else:
                chars.add(self.pattern[self.pos])
                self.pos += 1
        self.pos += 1  # Skip ]
        return CharClass(chars, positive)


class RegexEngine:
    def __init__(self, pattern: str):
        try:
            re.compile(pattern)  # Validate pattern
        except re.error as e:
            raise ValueError(f"Invalid regex: {e}")

        self.pattern = pattern
        self.start_anchor = pattern.startswith('^')
        self.end_anchor = pattern.endswith('$')
        clean_pattern = pattern.strip('^$')

        parser = RegexParser(clean_pattern)
        self.components = parser.parse()
        self.nfa = self._build_nfa()

    def _build_nfa(self) -> NFA:
        start = State()
        end = State()
        current = start

        # Handle start anchor
        if self.start_anchor:
            anchor = AnchorStart().build_nfa()
            current.epsilon.append(anchor.start)
            current = anchor.end

        # Main components
        for comp in self.components:
            nfa = comp.build_nfa()
            current.epsilon.append(nfa.start)
            current = nfa.end

        # Handle end anchor
        if self.end_anchor:
            anchor = AnchorEnd().build_nfa()
            current.epsilon.append(anchor.start)
            current = anchor.end

        current.epsilon.append(end)
        return NFA(start, end)

    def match(self, text: str) -> bool:
        current_states: set[State] = set()
        self._add_state(self.nfa.start, current_states)

        # Check start anchor
        if self.start_anchor and (not text or text[0] != self.pattern[1]):
            return False

        for char in text:
            next_states = set()
            for state in current_states:
                # Character transitions
                if char in state.transitions:
                    next_states.update(state.transitions[char])
                # Class transitions
                if "class" in state.transitions:
                    positive, chars = state.transitions["class"]
                    if (char in chars) == positive:
                        next_states.update(state.epsilon)
            current_states = set()
            for state in next_states:
                self._add_state(state, current_states)
            if not current_states:
                break

        # Check end anchor
        if self.end_anchor and (not text or text[-1] != self.pattern[-2]):
            return False

        return any(state == self.nfa.end for state in current_states)

    def _add_state(self, state: State, states: set):
        if state in states:
            return
        states.add(state)
        for eps in state.epsilon:
            self._add_state(eps, states)


# def visualize(self) -> Digraph:
#     dot = Digraph()
#     visited = set()
#     queue = deque([self.nfa.start])

#     while queue:
#         state = queue.popleft()
#         if state.id in visited:
#             continue
#         visited.add(state.id)

#         shape = "doublecircle" if state == self.nfa.end else "circle"
#         dot.node(str(state.id), shape=shape)

#         # 处理 ε-转移
#         for eps in state.epsilon:
#             dot.edge(str(state.id), str(eps.id), label="ε")
#             queue.append(eps)

#         # 处理字符转移
#         for char, targets in state.transitions.items():
#             # 处理字符类标签
#             if char == "class" and state.char_class:
#                 positive, chars = state.char_class
#                 sorted_chars = "".join(sorted(chars))
#                 label = f"[{'^' if not positive else ''}{sorted_chars}]"
#             else:
#                 label = char
#             # 添加边
#             for target in targets:
#                 dot.edge(str(state.id), str(target.id), label=label)
#                 queue.append(target)
#     return dot
