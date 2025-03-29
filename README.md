# BABEL - lab 03 - variant 07

## Project structure

- This project implements a simple regular
expression engine using a Non-deterministic
Finite Automaton (NFA) approach. It supports
literal matching, character classes, anchors,
custom quantifiers, and more. The engine even
comes with visualization support via Graphviz.

### regex-engine/

- RegularExpression.py # Core NFA implementation 
   - State # NFA state with transitions
   (including ε-transfer) 
   - NFA # Container for start/end states 
   - RegexComponent # Base class for regex
   elements 
      - Literal # Matches a single character 
      - CharClass # Character class matching
      (e.g., [a-z], [^0-9]) 
      - Quantifier # Custom quantifiers
      (e.g., *, +, ?, {min,max}) 
      - AnchorStart # Start anchor (^) 
      - AnchorEnd # End anchor ($) 
      - Alternation # Alternation (| operator) 
      - Group # Capturing groups 
      - EscapeSequence # Escape sequences
      (e.g., \.) 
      - Sequence # Sequence of regex components 
   - RegexParser # Parses the pattern into
   a component tree 
   - RegexEngine # The matching engine
   (with visualization support) 
- RegularExpression_test.py # Comprehensive
test suite covering: 
   - TestRegexComponents 
   - TestQuantifiers 
   - TestSpecialConstructs 
   - TestComplexExamples 
   - TestInputValidation 
   - TestSearchSubSplit

## Features

| Feature             | Example           | Implementation Class           |
|---------------------|-------------------|--------------------------------|
| Literal matching    | `a`, `5`          | `Literal`                      |
| Character classes   | `[a-z]`, `[^0]`   | `CharClass`                    |
| Predefined sets     | `\d`, `\w`        | `CharClass`                    |
| Wildcard            | `.`               | `CharClass` (in negative mode) |
| Anchors             | `^...$`           | `AnchorStart` / `AnchorEnd`    |
| Custom quantifiers  | `a{min,max}`      | `Quantifier`                   |

## State Machine Diagrams for Feature Examples

### 1. Literal Matching (`a`)
+---------+-------+---------+ | State | Input | Next | 
+---------+-------+---------+ | 0 | a | 1 | 
+---------+-------+---------+ | 1 | Accept| - | 
+---------+-------+---------+

### 2. Character Classes (`[a-z]`)

+---------+---------+---------+ | State | Input | Next | 
+---------+---------+---------+ | 0 | [a-z] | 1 | 
+---------+---------+---------+ | 1 | Accept | - | 
+---------+---------+---------+

### 3. Predefined Sets (`\d`)

+---------+-----------+---------+ | State | Input | Next | 
+---------+-----------+---------+ | 0 | [0-9] | 1 | 
+---------+-----------+---------+ | 1 | Accept | - | 
+---------+-----------+---------+

### 4. Wildcard (`.`)

+---------+-------------+---------+ | State | Input | Next | 
+---------+-------------+---------+ | 0 | any char | 1 | 
+---------+-------------+---------+ | 1 | Accept | - | 
+---------+-------------+---------+

### 5. Anchors (`^a+$`)

+------------------+----------------------+---------------------+ 
| State | Transition | Next State | 
+------------------+----------------------+---------------------+ 
| 0 | ε | 1 | | 1 (AnchorStart) | (match start) 
| 2 | | 2 | 'a' | 3 | | 3 | ε (loop for '+') | 2 | | 3 | ε | 4 | | 4 
(AnchorEnd) | (match end) | 5 | | 5 | ε | Accept (6) | 
+------------------+----------------------+---------------------+

### 6. Custom Quantifiers (`a{2,3}` Example)

+---------+---------+-----------------------------------+ 
| State | Input | Next | 
+---------+---------+-----------------------------------+ 
| 0 | 'a' | 1 | | 1 | 'a' | 2 | | 2 | 'a' | 3 (optional third 'a')
 | | 2 | ε | Accept (if only two matches) | | 3 | ε | Accept | 
 +---------+---------+-----------------------------------+


## Contribution

- LIN Yanjun (972613709@qq.com)

## Changelog

- 29.03.2022 - 8
   - Completely fixed bugs in the code.
- 28.03.2022 - 7
   - Testing and adjustment.
- 27.03.2022 - 6
   - Debugging code functions .
- 26.03.2022 - 5
   - Add sub、split.
- 26.03.2022 - 4
   - Add search.
- 25.03.2022 - 3
   - Fix test function support.
- 24.03.2022 - 2
   - Add RegularExpression_test.py.
- 24.03.2022 - 1
   - Add RegularExpression.py.
- 23.03.2025 - 0
   - Initial

## Design notes

- Learned to call from the bottom to the top using a layered architecture
   State → NFA → RegexComponent → RegexParser → RegexEngine.

- The NFA working mechanism can be implemented recursively via
   _add_state() ε-closure computation.

- Regular validity can be verified at initialisation time
   using standard library precalibration.
