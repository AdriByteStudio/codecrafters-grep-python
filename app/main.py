import sys

# import pyparsing - available if you need it!
# import lark - available if you need it!


def match_char_at(input_line, pi, ii):
    """Try to match one pattern element at input position ii.
    Returns new input index on match, or None on failure."""
    if pi < len(pattern) and pattern[pi] == '\\' and pi + 1 < len(pattern):
        esc = pattern[pi + 1]
        if esc == 'd':
            if ii < len(input_line) and input_line[ii].isdigit():
                return ii + 1
        elif esc == 'w':
            if ii < len(input_line) and (input_line[ii].isalnum() or input_line[ii] == '_'):
                return ii + 1
    elif pi < len(pattern) and pattern[pi] == '[':
        end = pattern.index(']', pi + 1)
        if pattern[pi + 1] == '^':
            chars = pattern[pi + 2:end]
            if ii < len(input_line) and input_line[ii] not in chars:
                return ii + 1
        else:
            chars = pattern[pi + 1:end]
            if ii < len(input_line) and input_line[ii] in chars:
                return ii + 1
    elif pi < len(pattern):
        if ii < len(input_line) and input_line[ii] == pattern[pi]:
            return ii + 1
    return None


def elem_len(pi):
    """Return how many pattern chars one element starting at pi consumes."""
    if pattern[pi] == '\\' and pi + 1 < len(pattern):
        return 2
    if pattern[pi] == '[':
        return pattern.index(']', pi + 1) - pi + 1
    return 1


def match_from(input_line, pi, ii):
    """Match pattern[pi:] against input starting at ii. Returns end index or None."""
    while pi < len(pattern):
        next_pi = pi + elem_len(pi)
        if next_pi < len(pattern) and pattern[next_pi] == '+':
            elen = elem_len(pi)
            # Greedily match as many as possible (at least 1)
            positions = []
            nxt = match_char_at(input_line, pi, ii)
            if nxt is None:
                return None  # + requires at least one match
            positions.append(nxt)
            while True:
                nxt = match_char_at(input_line, pi, positions[-1])
                if nxt is None:
                    break
                positions.append(nxt)
            # Try from most greedy to least
            for pos in reversed(positions):
                result = match_from(input_line, next_pi + 1, pos)
                if result is not None:
                    return result
            return None
        if next_pi < len(pattern) and pattern[next_pi] == '?':
            # Try one match first (greedy), then zero
            nxt = match_char_at(input_line, pi, ii)
            if nxt is not None:
                result = match_from(input_line, next_pi + 1, nxt)
                if result is not None:
                    return result
            return match_from(input_line, next_pi + 1, ii)
        nxt = match_char_at(input_line, pi, ii)
        if nxt is None:
            return None
        ii = nxt
        pi = next_pi
    return ii


def match_pattern(inp, pat):
    global pattern
    pattern = pat
    anchored_start = pattern.startswith('^')
    if anchored_start:
        pattern = pattern[1:]
    has_end_anchor = pattern.endswith('$')
    if has_end_anchor:
        pattern = pattern[:-1]
    starts = [0] if anchored_start else range(len(inp) + 1)
    for start in starts:
        end = match_from(inp, 0, start)
        if end is not None:
            if has_end_anchor:
                if end == len(inp):
                    return True
            else:
                return True
    return False


def main():
    pattern = sys.argv[2]
    input_line = sys.stdin.read().rstrip('\n')

    if sys.argv[1] != "-E":
        print("Expected first argument to be '-E'")
        exit(1)

    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

    # TODO: Uncomment the code below to pass the first stage
    if match_pattern(input_line, pattern):
      exit(0)
    else:
        exit(1)


if __name__ == "__main__":
    main()
