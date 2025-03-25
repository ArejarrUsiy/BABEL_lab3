# BABEL - lab 03 - variant 07

## Project structure

### regex-engine/
- RegularExpression.py # Core NFA implementation
   - State # NFA state with transitions
   - NFA # NFA container (start/end states)
   - RegexComponent # Base class for regex elements
      - Literal # Single character matching
      - CharClass # [a-z]/[^0-9] style matching
      - Quantifier # {min,max} repetition logic
      - AnchorStart # ^ beginning anchor
      - AnchorEnd # $ end anchor
   - RegexParser # Pattern parsing subsystem
   - RegexEngine # Matching engine with visualization
-  RegularExpression_test.py # Comprehensive test suite
   - TestRegexComponents # Basic element tests
   - TestQuantifiers # */+ quantifier validation
   - TestSpecialConstructs # Anchor/edge case checks
   - TestComplexExamples # Real-world pattern tests
   - TestInputValidation # Invalid pattern handling

## Features

| Feature          | Example        | Implementation Class |
|------------------|----------------|----------------------|
| Literal matching | `a`, `5`       | `Literal`            |
| Character classes| `[a-z]`, `[^0]`| `CharClass`          |
| Predefined sets  | `\d`, `\w`     | `CharClass`          |
| Wildcard         | `.`            | `CharClass(negative)`|
| Anchors          | `^...$`        | `AnchorStart/End`    |
| Custom quantifiers| `a{min,max}`  | `Quantifier`         |

## Contribution

- LIN Yanjun (972613709@qq.com)

## Changelog

- 25.03.2022 - 4
   - Update README.
- 25.03.2022 - 3
   - Fix test function support.
- 24.03.2022 - 2
   - Add RegularExpression_test.py.
- 24.03.2022 - 1
   - Add RegularExpression.py.
- 23.03.2025 - 0
   - Initial

## Design notes

- Learned to call from the bottom to the top using a layered architecture: State → NFA → RegexComponent → RegexParser → RegexEngine.

- The NFA working mechanism can be implemented recursively via _add_state() ε-closure computation.

- To match the parallel transfer of the process simulation state machine can be done like this: current_states → char → next_states.

- Regular validity can be verified at initialisation time using standard library precalibration.

