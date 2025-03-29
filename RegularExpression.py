import logging
from typing import Optional, List, Dict, Set, NamedTuple, Tuple
from graphviz import Digraph  # type:ignore
from collections import deque

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RegexEngine")


class Match(NamedTuple):
    group: str
    start: int
    end: int
    groups: List[str]


class State:
    _id = 0

    def __init__(self):
        self.id = State._id
        State._id += 1
        self.transitions = {}
        self.epsilon = []
        self.char_class: Optional[Tuple[bool, Set[str]]] = None
        self.quantifier = None
        self.group_id = None
        self.backref = None
        self.group_start = False
        self.group_end = False
        self.is_start_anchor = False
        self.is_end_anchor = False
        self.is_fallback = False

    def get_label(self):
        parts = []
        if self.backref is not None:
            parts.append(f"Backref to group {self.backref}")
        if self.char_class:
            pos, chars = self.char_class
            parts.append(f"[{'^' if not pos else ''}{
                self._format_chars(chars)}]")
        if self.quantifier:
            parts.append(f"Quant: {self.quantifier}")
        if self.group_id is not None:
            parts.append(f"Group {self.group_id}")
        if self.backref is not None:
            parts.append(f"Backref \\{self.backref}")
        return "\n".join(parts) if parts else str(self.id)

    def _format_chars(self, chars):
        safe_chars = []
        for c in sorted(chars):
            if c == '\\':
                safe_chars.append('\\\\')
            elif c == '"':
                safe_chars.append('\\"')
            elif c == '-':
                safe_chars.append('\\-')
            elif ord(c) < 32 or ord(c) > 126:
                safe_chars.append(f'\\u{ord(c):04x}')
            else:
                safe_chars.append(c)
        return ''.join(safe_chars)

    def _detect_ranges(self, chars):
        return "".join(sorted(chars))


class NFA:
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
    def __init__(self, chars: set, positive=True, charset=None):
        self.chars = chars
        self.positive = positive
        self.charset = charset or set(chr(i) for i in range(32, 127))

    def build_nfa(self) -> NFA:
        start = State()
        end = State()
        start.char_class = (self.positive, self.chars)
        if self.positive:
            for c in self.chars:
                start.transitions.setdefault(c, []).append(end)
        else:
            start.transitions["any"] = [end]
            start.char_class = (False, self.chars)
        return NFA(start, end)


class Quantifier(RegexComponent):
    def __init__(self, expr: RegexComponent, min_: int, max_: int):
        self.expr = expr
        self.min = min_
        self.max = max_

    def build_nfa(self) -> NFA:
        if self.min == 0 and self.max == -1:
            start = State()
            end = State()
            end.is_fallback = True
            subnfa = self.expr.build_nfa()
            start.epsilon.append(subnfa.start)
            start.epsilon.append(end)
            subnfa.end.epsilon.append(subnfa.start)
            subnfa.end.epsilon.append(end)
            return NFA(start, end)
        elif self.min == 1 and self.max == -1:
            mandatory = self.expr.build_nfa()
            star_part = Quantifier(self.expr, 0, -1).build_nfa()
            mandatory.end.epsilon.append(star_part.start)
            return NFA(mandatory.start, star_part.end)
        else:
            start = State()
            end = State()
            current = start
            for _ in range(self.min):
                nfa = self.expr.build_nfa()
                current.epsilon.append(nfa.start)
                current = nfa.end
            if self.max == -1 or self.max > self.min:
                loop_entry = State()
                loop_exit = State()
                current.epsilon.append(loop_entry)
                expr_nfa = self.expr.build_nfa()
                loop_entry.epsilon.append(expr_nfa.start)
                expr_nfa.end.epsilon.extend([loop_entry, loop_exit])
                current = loop_exit
            current.epsilon.append(end)
            return NFA(start, end)


class AnchorStart(RegexComponent):
    def build_nfa(self) -> NFA:
        start = State()
        return NFA(start, start)


class AnchorEnd(RegexComponent):
    def build_nfa(self) -> NFA:
        end = State()
        return NFA(end, end)


class Alternation(RegexComponent):
    def __init__(self, left: RegexComponent, right: RegexComponent):
        self.left = left
        self.right = right

    def build_nfa(self) -> NFA:
        start = State()
        end = State()
        left_nfa = self.left.build_nfa()
        right_nfa = self.right.build_nfa()
        start.epsilon.extend([left_nfa.start, right_nfa.start])
        left_nfa.end.epsilon.append(end)
        right_nfa.end.epsilon.append(end)
        return NFA(start, end)


class Backreference(RegexComponent):
    def __init__(self, group_num: int):
        self.group_num = group_num

    def build_nfa(self) -> NFA:
        start = State()
        end = State()
        start.backref = self.group_num
        start.epsilon.append(end)
        return NFA(start, end)


class Group(RegexComponent):
    def __init__(self, sub_components: list, group_id: Optional[int]):
        self.sub_components = sub_components
        self.group_id = group_id

    def build_nfa(self) -> NFA:
        start = State()
        end = State()
        start.group_id = self.group_id
        end.group_id = self.group_id
        start.group_start = True
        end.group_end = True
        current = start
        for comp in self.sub_components:
            nfa = comp.build_nfa()
            current.epsilon.append(nfa.start)
            current = nfa.end
        current.epsilon.append(end)
        return NFA(start, end)


class MatchContext:
    def __init__(self):
        self.group_stack: List[int] = []
        self.groups: Dict[int, Tuple[int, Optional[int]]] = {}

    def enter_group(self, group_id: int, start_pos: int):
        self.group_stack.append(group_id)
        self.groups[group_id] = (start_pos, None)

    def exit_group(self, group_id: int, end_pos: int):
        if group_id in self.groups:
            self.groups[group_id] = (self.groups[group_id][0], end_pos)
            self.group_stack.pop()


class EscapeSequence(RegexComponent):
    def __init__(self, char: str):
        self.char = char

    def build_nfa(self) -> NFA:
        if self.char == ".":
            seq = Sequence([Literal('\\'), CharClass(set(), positive=False)])
        else:
            seq = Sequence([Literal('\\'), Literal(self.char)])
        return seq.build_nfa()


class Sequence(RegexComponent):
    def __init__(self, sub_components: list):
        self.sub_components = sub_components

    def build_nfa(self) -> NFA:
        start = State()
        current = start
        for comp in self.sub_components:
            nfa = comp.build_nfa()
            current.epsilon.append(nfa.start)
            current = nfa.end
        end = State()
        current.epsilon.append(end)
        return NFA(start, end)


class RegexParser:
    def __init__(self, pattern: str) -> None:
        self.pattern = pattern
        self.pos = 0
        self.groups: List[RegexComponent] = []
        self.group_counter: int = 0
        self.group_stack: List[Optional[int]] = []

    def parse_alternation(
            self, stop_char: Optional[str] = None) -> list[RegexComponent]:
        alternatives = []
        seq = self.parse_sequence(stop_char)
        alternatives.append(seq)
        while self.pos < len(self.pattern) and self.pattern[self.pos] == '|':
            self.pos += 1  # skip '|'
            seq = self.parse_sequence(stop_char)
            alternatives.append(seq)
        if len(alternatives) == 1:
            return alternatives[0]
        else:
            processed = []
            for alt in alternatives:
                if len(alt) == 1:
                    processed.append(alt[0])
                else:
                    processed.append(Sequence(alt))
            alt_node = processed[0]
            for comp in processed[1:]:
                alt_node = Alternation(alt_node, comp)
            return [alt_node]

    def parse_sequence(
            self, stop_char: Optional[str] = None) -> List[RegexComponent]:
        seq = []
        while self.pos < len(self.pattern) and (
                stop_char is None or self.pattern[self.pos] != stop_char
                    ) and self.pattern[self.pos] != '|':
            atom = self._parse_atom()
            while self.pos < len(self.pattern
                                 ) and self.pattern[self.pos] in (
                                     '*', '+', '?', '{'):
                quant = self.pattern[self.pos]
                if quant in ('*', '+', '?'):
                    self.pos += 1
                    if quant == '*':
                        atom = Quantifier(atom, 0, -1)
                    elif quant == '+':
                        atom = Quantifier(atom, 1, -1)
                    elif quant == '?':
                        atom = Quantifier(atom, 0, 1)
                elif quant == '{':
                    self.pos += 1  # skip '{'
                    atom = self._parse_curly_quantifier(atom)
            seq.append(atom)
        return seq

    def _parse_atom(self) -> "RegexComponent":
        if self.pos >= len(self.pattern):
            raise ValueError(
                "Unexpected arrival at the end of the pattern")
        char = self.pattern[self.pos]
        if char == '(':
            return self._parse_group()
        elif char == '[':
            return self._parse_char_class()
        elif char == '^':
            self.pos += 1
            return AnchorStart()
        elif char == '$':
            self.pos += 1
            return AnchorEnd()
        elif char == '.':
            self.pos += 1
            return CharClass(set(), positive=False)
        elif char == '\\':
            self.pos += 1
            if self.pos >= len(self.pattern):
                raise ValueError("Ends unexpectedly after '\\\'")
            next_char = self.pattern[self.pos]
            self.pos += 1
            if next_char in ('d', 'w', 's', 'D', 'W', 'S'):
                if next_char == 'd':
                    return CharClass(set(str(i) for i in range(10)))
                elif next_char == 'w':
                    chars = set(chr(i) for i in range(97, 123))
                    chars.update(chr(i) for i in range(65, 91))
                    chars.update(str(i) for i in range(10))
                    chars.add('_')
                    return CharClass(chars)
                elif next_char == 's':
                    return CharClass({' ', '\t', '\n', '\r', '\f', '\v'})
                elif next_char == 'S':
                    return CharClass({' ', '\t', '\n', '\r', '\f', '\v'
                                      }, positive=False)
                elif next_char == 'D':
                    return CharClass(set(str(i) for i in range(10)),
                                     positive=False)
                elif next_char == 'W':
                    word_chars = set(chr(i) for i in range(97, 123))
                    word_chars.update(chr(i) for i in range(65, 91))
                    word_chars.update(str(i) for i in range(10))
                    word_chars.add('_')
                    return CharClass(word_chars, positive=False)
                else:
                    fal1 = "next_char in ('d', 'w', 's', 'D', 'W', 'S')"
                    fal2 = "should be exhaustive"
                    assert False, fal1 and fal2
            elif next_char in (
                '\\', '.', '^', '$', '*', '+',
                    '?', '{', '}', '[', ']', '(', ')', '|'):
                return EscapeSequence(next_char)
            else:
                raise ValueError("Invalid escape sequence: \\" + next_char)
        else:
            self.pos += 1
            return Literal(char)

    def _parse_group(self) -> "RegexComponent":
        self.pos += 1  # skip '('
        capturing = True
        if self.pos < len(self.pattern) and self.pattern[self.pos] == '?':
            self.pos += 1
            if self.pos < len(self.pattern) and self.pattern[self.pos] == ':':
                capturing = False
                self.pos += 1  # skip ':'
            else:
                raise ValueError("Unsupported group extensions")
        if capturing:
            group_id: Optional[int] = self.group_counter
            self.group_counter += 1
            self.group_stack.append(group_id)
        else:
            group_id = None
        sub_components = self.parse_alternation(stop_char=')')
        if self.pos >= len(self.pattern) or self.pattern[self.pos] != ')':
            raise ValueError("Unclosed grouping")
        self.pos += 1
        if capturing:
            self.group_stack.pop()
            return Group(sub_components, group_id)
        else:
            if len(sub_components) == 1:
                return sub_components[0]
            else:
                return Sequence(sub_components)

    def _parse_backref(self) -> "RegexComponent":
        start_pos = self.pos
        while self.pos < len(self.pattern
                             ) and self.pattern[self.pos].isdigit():
            self.pos += 1
        num_str = self.pattern[start_pos:self.pos]
        if not num_str:
            raise ValueError("Reverse references must contain numbers")
        return Backreference(int(num_str))

    def _parse_char_class(self) -> "RegexComponent":
        self.pos += 1  # skip '['
        positive = True
        if self.pos < len(self.pattern) and self.pattern[self.pos] == '^':
            positive = False
            self.pos += 1
        chars: Set[str] = set()
        while self.pos < len(self.pattern) and self.pattern[self.pos] != ']':
            if (self.pattern[self.pos] == '-' and chars and
                    self.pos + 1 < len(self.pattern) and
                    self.pattern[self.pos + 1] != ']'):
                prev_char = sorted(chars)[-1]
                self.pos += 1  # skip '-'
                range_end = self.pattern[self.pos]
                for c in range(ord(prev_char) + 1, ord(range_end) + 1):
                    chars.add(chr(c))
                self.pos += 1
            else:
                chars.add(self.pattern[self.pos])
                self.pos += 1
        if self.pos >= len(self.pattern) or self.pattern[self.pos] != ']':
            raise ValueError("unclosed character class")
        self.pos += 1  # skip ']'
        return CharClass(chars, positive)

    def _parse_curly_quantifier(self, comp: "RegexComponent"
                                ) -> "RegexComponent":
        min_str = ""
        max_str = ""
        has_comma = False
        while self.pos < len(self.pattern
                             ) and self.pattern[self.pos].isdigit():
            min_str += self.pattern[self.pos]
            self.pos += 1
        if self.pos < len(self.pattern
                          ) and self.pattern[self.pos] == ',':
            has_comma = True
            self.pos += 1
            while self.pos < len(self.pattern
                                 ) and self.pattern[self.pos].isdigit():
                max_str += self.pattern[self.pos]
                self.pos += 1
        if self.pos >= len(self.pattern) or self.pattern[self.pos] != '}':
            raise ValueError("unclosed quantifier")
        self.pos += 1  # skip '}'
        min_val = int(min_str) if min_str else 0
        if has_comma:
            max_val = int(max_str) if max_str else -1
        else:
            max_val = min_val
        return Quantifier(comp, min_val, max_val)

    def parse(self) -> list[RegexComponent]:
        result = self.parse_alternation(stop_char=None)
        if self.pos != len(self.pattern):
            raise ValueError("Extra characters in pattern")
        return result


class RegexEngine:
    def __init__(self, pattern: str):
        self.pattern = pattern
        self.start_anchor = pattern.startswith('^')
        self.end_anchor = pattern.endswith('$')
        trimmed_pattern = pattern
        if self.start_anchor:
            trimmed_pattern = trimmed_pattern[1:]
        if self.end_anchor:
            trimmed_pattern = trimmed_pattern[:-1]
        parser = RegexParser(trimmed_pattern)
        parsed_components: List[RegexComponent] = parser.parse()
        if isinstance(parsed_components, list) and len(parsed_components) > 1:
            self.components: List[RegexComponent
                                  ] = [Sequence(parsed_components)]
        else:
            self.components = parsed_components if isinstance(
                parsed_components, list) else [parsed_components]
        self.nfa = self.build_nfa()
        self.group_count = parser.group_counter

    def build_nfa(self) -> NFA:
        start = State()
        curr = start
        if self.start_anchor:
            anchor_start = State()
            anchor_start.is_start_anchor = True
            curr.epsilon.append(anchor_start)
            curr = anchor_start
        for comp in self.components:
            comp_nfa = comp.build_nfa()
            curr.epsilon.append(comp_nfa.start)
            curr = comp_nfa.end
        if self.end_anchor:
            anchor_end = State()
            anchor_end.is_end_anchor = True
            curr.epsilon.append(anchor_end)
            curr = anchor_end
        end = State()
        curr.epsilon.append(end)
        return NFA(start, end)

    def _get_epsilon_closure(self, states: set) -> set:
        closure = set(states)
        stack = list(states)
        while stack:
            state = stack.pop()
            for eps in state.epsilon:
                if eps not in closure:
                    closure.add(eps)
                    stack.append(eps)
        return closure

    def _find_matches(self, text: str) -> list[Tuple[int, int, List[str]]]:
        matches: list[Tuple[int, int, List[str]]] = []
        n: int = len(text)
        for i in range(n):
            current_states = self._get_epsilon_closure({self.nfa.start})
            match_end = -1
            for j in range(i, n):
                char = text[j]
                next_states = set()
                for state in current_states:
                    if state.is_start_anchor and j != i:
                        continue
                    if state.is_end_anchor and j != n - 1:
                        continue
                    if char in state.transitions:
                        next_states.update(state.transitions[char])
                    if state.char_class:
                        positive, chars = state.char_class
                        if (char in chars) == positive:
                            ns = state.transitions.get("any", [])
                            next_states.update(ns)
                            next_states.update(state.epsilon)
                current_states = self._get_epsilon_closure(next_states)
                if any(s == self.nfa.end for s in current_states):
                    match_end = j + 1
            if match_end != -1:
                matches.append((i, match_end, []))
        return matches

    def _simulate_nfa(self, text: str) -> list:
        matches: list[Tuple[int, int]] = []
        n = len(text)
        for i in range(n + 1):
            current_states = self._get_epsilon_closure({self.nfa.start})
            match_end = -1
            for j in range(i, n):
                char = text[j]
                next_states = set()
                for state in current_states:
                    if state.is_start_anchor and j != i:
                        continue
                    if state.is_end_anchor and j != n - 1:
                        continue
                    if char in state.transitions:
                        next_states.update(state.transitions[char])
                    if state.char_class:
                        positive, chars = state.char_class
                        if (char in chars) == positive:
                            next_states.update(state.transitions.get(char, []))
                            next_states.update(state.epsilon)
                current_states = self._get_epsilon_closure(next_states)
                if any(s == self.nfa.end for s in current_states):
                    match_end = j + 1
            if match_end != -1:
                matches.append((i, match_end))
        return matches

    def match(self, text: str) -> bool:
        matches = self._find_matches(text)
        return any(start == 0 and
                   end == len(text) for start, end, _ in matches)

    def search(self, text: str):
        matches = self._find_matches(text)
        if matches:
            start, end, _ = matches[0]
            return Match(text[start:end], start, end, [])
        return None

    def _find_first_match(self, text: str, pos: int
                          ) -> Optional[Tuple[int, int]]:
        n = len(text)
        for i in range(pos, n):
            current_states = self._get_epsilon_closure({self.nfa.start})
            match_end = -1
            for j in range(i, n):
                char = text[j]
                next_states = set()
                for state in current_states:
                    if state.is_start_anchor and j != i:
                        continue
                    if state.is_end_anchor and j != n - 1:
                        continue
                    if char in state.transitions:
                        next_states.update(state.transitions[char])
                    if state.char_class:
                        positive, chars = state.char_class
                        if (char in chars) == positive:
                            ns = state.transitions.get("any", [])
                            next_states.update(ns)
                            next_states.update(state.epsilon)
                current_states = self._get_epsilon_closure(next_states)
                if any(s == self.nfa.end for s in current_states):
                    match_end = j + 1
            if match_end != -1:
                return (i, match_end)
        return None

    def findall(self, text: str) -> list:
        found = []
        pos = 0
        while pos < len(text):
            m = self._find_first_match(text, pos)
            if m is None:
                break
            s, e = m
            if s == e:
                found.append(text[pos])
                pos += 1
                continue
            found.append(text[s:e])
            pos = e
        return found

    def sub(self, repl: str, text: str, count: int = 0) -> str:
        pos = 0
        result = []
        num_subs = 0
        n = len(text)
        while pos < n:
            m = self._find_first_match(text, pos)
            if m is None:
                break
            start, end = m
            if start == end:
                result.append(text[pos])
                pos += 1
                continue
            result.append(text[pos:start])
            result.append(repl)
            pos = end
            num_subs += 1
            if count > 0 and num_subs >= count:
                break
        result.append(text[pos:])
        return ''.join(result)

    def split(self, text: str, maxsplit: int = 0) -> list:
        pos = 0
        parts = []
        splits = 0
        n = len(text)
        while pos < n:
            m = self._find_first_match(text, pos)
            if m is None or (maxsplit > 0 and splits >= maxsplit):
                break
            start, end = m
            if start == end:
                pos = end + 1
                continue
            parts.append(text[pos:start])
            pos = end
            splits += 1
        parts.append(text[pos:])
        return parts

    def visualize(self) -> Digraph:
        dot = Digraph(encoding='utf-8')
        dot.attr(rankdir='LR', labelloc='t', fontsize='12')
        styles = {
            'start_end': {'shape': 'rarrow', 'fillcolor': '#FFD700'},
            'quantifier': {'fillcolor': '#FFB6C1'},
            'group': {'shape': 'rectangle', 'fillcolor': '#E0FFFF'},
            'char_class': {'fillcolor': '#98FB98'},
            'backref': {'shape': 'diamond', 'fillcolor': '#FFA07A'}
        }
        visited = set()
        queue = deque([self.nfa.start])
        while queue:
            state = queue.popleft()
            if state.id in visited:
                continue
            visited.add(state.id)
            node_style = {}
            if state == self.nfa.start or state == self.nfa.end:
                node_style = styles['start_end']
            elif state.quantifier:
                node_style = styles['quantifier']
            elif state.group_id is not None:
                node_style = styles['group']
            elif state.char_class:
                node_style = styles['char_class']
            elif state.backref is not None:
                node_style = styles['backref']
            dot.node(str(state.id),
                     label=state.get_label(),
                     **node_style)
            self._add_transitions(dot, state, queue)
        return dot

    def _add_transitions(self, dot, state, queue):
        for eps in state.epsilon:
            dot.edge(str(state.id), str(eps.id),
                     label="ε-transfer",
                     style="dashed",
                     color="#FF8C00")
            queue.append(eps)
        for char, targets in state.transitions.items():
            edge_attrs = {}
            if char == 'class':
                edge_attrs['color'] = '#228B22'
            elif char == 'any':
                edge_attrs['color'] = '#A0522D'
            for target in targets:
                dot.edge(str(state.id), str(target.id),
                         label=self._format_edge_label(char),
                         **edge_attrs)
                queue.append(target)

    def _format_edge_label(self, char):
        char = char.replace('\\', '\\\\').replace('"', '\\"'
                                                  ).replace('-', '\\-')
        labels = {
            '^': 'Line Start',
            '$': 'Line End',
            '.': 'Any Char',
            '\\w': 'Word Char',
            '\\d': 'Digit',
            '\\s': 'Whitespace',
            '\\\\w': '\\\\w',
            '\\\\d': '\\\\d',
            '\\\\s': '\\\\s'
        }
        return labels.get(char, char)
