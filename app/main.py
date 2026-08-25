import sys
import os


def match_char_at(pattern, input_line, pi, ii):
    """Try to match one pattern element at input position ii.
    Returns new input index on match, or None on failure."""
    if pi < len(pattern) and pattern[pi] == '\\' and pi + 1 < len(pattern):
        esc = pattern[pi + 1]
        if esc == 'd':
            if ii < len(input_line) and '0' <= input_line[ii] <= '9':
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
        if pattern[pi] == '.':
            if ii < len(input_line) and input_line[ii] != '\n':
                return ii + 1
        elif ii < len(input_line) and input_line[ii] == pattern[pi]:
            return ii + 1
    return None


def parse_brace(pattern, pi):
    """Check if pattern[pi:] starts with {n}. Returns (count, brace_len) or None."""
    if pi < len(pattern) and pattern[pi] == '{':
        end = pattern.index('}', pi + 1)
        num = pattern[pi + 1:end]
        if num.isdigit():
            return (int(num), end - pi + 1)
    return None


def elem_len(pattern, pi):
    """Return how many pattern chars one element starting at pi consumes."""
    if pattern[pi] == '\\' and pi + 1 < len(pattern):
        base = 2
    elif pattern[pi] == '[':
        base = pattern.index(']', pi + 1) - pi + 1
    elif pattern[pi] == '(':
        base = find_group_end(pattern, pi) - pi + 1
    else:
        base = 1
    brace = parse_brace(pattern, pi + base)
    if brace:
        base += brace[1]
    return base


def find_group_end(pattern, start):
    """Find the closing ) matching the ( at start. Returns index of ')' or -1."""
    depth = 1
    i = start + 1
    while i < len(pattern) and depth > 0:
        if pattern[i] == '(':
            depth += 1
        elif pattern[i] == ')':
            depth -= 1
        i += 1
    return i - 1 if depth == 0 else -1


def split_alternatives(group_content):
    """Split group content by | at the top level (not inside nested parens)."""
    alternatives = []
    depth = 0
    current = []
    for ch in group_content:
        if ch == '(':
            depth += 1
            current.append(ch)
        elif ch == ')':
            depth -= 1
            current.append(ch)
        elif ch == '|' and depth == 0:
            alternatives.append(''.join(current))
            current = []
        else:
            current.append(ch)
    alternatives.append(''.join(current))
    return alternatives


def match_from(pattern, input_line, pi, ii):
    """Match pattern[pi:] against input starting at ii. Returns end index or None."""
    while pi < len(pattern):
        # Compute base element length (without quantifiers)
        if pattern[pi] == '\\' and pi + 1 < len(pattern):
            base = 2
        elif pattern[pi] == '[':
            base = pattern.index(']', pi + 1) - pi + 1
        elif pattern[pi] == '(':
            base = find_group_end(pattern, pi) - pi + 1
        else:
            base = 1
        q_pos = pi + base  # position where quantifier might be
        # Check for quantifiers
        if q_pos < len(pattern) and pattern[q_pos] == '+':
            positions = []
            nxt = match_char_at(pattern, input_line, pi, ii)
            if nxt is None:
                return None
            positions.append(nxt)
            while True:
                nxt = match_char_at(pattern, input_line, pi, positions[-1])
                if nxt is None:
                    break
                positions.append(nxt)
            for pos in reversed(positions):
                result = match_from(pattern, input_line, q_pos + 1, pos)
                if result is not None:
                    return result
            return None
        if q_pos < len(pattern) and pattern[q_pos] == '*':
            positions = [ii]
            while True:
                nxt = match_char_at(pattern, input_line, pi, positions[-1])
                if nxt is None:
                    break
                positions.append(nxt)
            for pos in reversed(positions):
                result = match_from(pattern, input_line, q_pos + 1, pos)
                if result is not None:
                    return result
            return None
        if q_pos < len(pattern) and pattern[q_pos] == '?':
            nxt = match_char_at(pattern, input_line, pi, ii)
            if nxt is not None:
                result = match_from(pattern, input_line, q_pos + 1, nxt)
                if result is not None:
                    return result
            return match_from(pattern, input_line, q_pos + 1, ii)
        brace = parse_brace(pattern, q_pos)
        if brace and pattern[pi] != '(':
            count, brace_len = brace
            rest_pi = q_pos + brace_len
            cur = ii
            for _ in range(count):
                nxt = match_char_at(pattern, input_line, pi, cur)
                if nxt is None:
                    return None
                cur = nxt
            pi = rest_pi
            ii = cur
            continue
        if pattern[pi] == '(':
            end = find_group_end(pattern, pi)
            if end == -1:
                return None
            group_content = pattern[pi + 1:end]
            rest_pi = end + 1
            brace = parse_brace(pattern, rest_pi)
            if brace:
                count, brace_len = brace
                after_group = rest_pi + brace_len

                def match_repeated_group(repetitions, current):
                    if repetitions == 0:
                        return match_from(pattern, input_line, after_group, current)
                    for alt in split_alternatives(group_content):
                        next_position = match_from(alt, input_line, 0, current)
                        if next_position is not None:
                            result = match_repeated_group(repetitions - 1, next_position)
                            if result is not None:
                                return result
                    return None

                return match_repeated_group(count, ii)
            # Check for quantifier after group
            if rest_pi < len(pattern) and pattern[rest_pi] in ('+', '?'):
                q = pattern[rest_pi]
                rest_pi += 1
                if q == '+':
                    positions = []
                    cur = ii
                    # Must match at least once
                    found_any = False
                    for alt in split_alternatives(group_content):
                        r = match_from(alt, input_line, 0, cur)
                        if r is not None:
                            positions.append(r)
                            found_any = True
                    if not found_any:
                        return None
                    # Greedily try more
                    while True:
                        found_more = False
                        for alt in split_alternatives(group_content):
                            r = match_from(alt, input_line, 0, positions[-1])
                            if r is not None:
                                positions.append(r)
                                found_more = True
                        if not found_more:
                            break
                    for pos in reversed(positions):
                        result = match_from(pattern, input_line, rest_pi, pos)
                        if result is not None:
                            return result
                    return None
                else:  # ?
                    for alt in split_alternatives(group_content):
                        r = match_from(alt, input_line, 0, ii)
                        if r is not None:
                            result = match_from(pattern, input_line, rest_pi, r)
                            if result is not None:
                                return result
                    return match_from(pattern, input_line, rest_pi, ii)
            # No quantifier: try each alternative
            for alt in split_alternatives(group_content):
                r = match_from(alt, input_line, 0, ii)
                if r is not None:
                    result = match_from(pattern, input_line, rest_pi, r)
                    if result is not None:
                        return result
            return None
        nxt = match_char_at(pattern, input_line, pi, ii)
        if nxt is None:
            return None
        ii = nxt
        pi = pi + base
    return ii


def match_pattern(inp, pat):
    anchored_start = pat.startswith('^')
    if anchored_start:
        pat = pat[1:]
    has_end_anchor = pat.endswith('$')
    if has_end_anchor:
        pat = pat[:-1]
    starts = [0] if anchored_start else range(len(inp) + 1)
    for start in starts:
        end = match_from(pat, inp, 0, start)
        if end is not None:
            if has_end_anchor:
                if end == len(inp):
                    return True
            else:
                return True
    return False


def find_match(inp, pat):
    """Return (start, end) of the first match, or None."""
    anchored_start = pat.startswith('^')
    if anchored_start:
        pat = pat[1:]
    has_end_anchor = pat.endswith('$')
    if has_end_anchor:
        pat = pat[:-1]
    starts = [0] if anchored_start else range(len(inp) + 1)
    for start in starts:
        end = match_from(pat, inp, 0, start)
        if end is not None:
            if has_end_anchor:
                if end == len(inp):
                    return (start, end)
            else:
                return (start, end)
    return None


def find_all_matches(inp, pat):
    """Return list of (start, end) for all non-overlapping matches."""
    anchored_start = pat.startswith('^')
    if anchored_start:
        pat = pat[1:]
    has_end_anchor = pat.endswith('$')
    if has_end_anchor:
        pat = pat[:-1]
    if anchored_start:
        end = match_from(pat, inp, 0, 0)
        if end is not None:
            if has_end_anchor:
                if end == len(inp):
                    return [(0, end)]
            else:
                return [(0, end)]
        return []
    matches = []
    pos = 0
    while pos <= len(inp):
        found = False
        for start in range(pos, len(inp) + 1):
            end = match_from(pat, inp, 0, start)
            if end is not None:
                if has_end_anchor:
                    if end == len(inp):
                        matches.append((start, end))
                        found = True
                        break
                else:
                    matches.append((start, end))
                    pos = end  # continue after this match
                    found = True
                    break
        if not found:
            break
    return matches


def main():
    import os
    args = sys.argv[1:]
    only_matching = '-o' in args
    if only_matching:
        args.remove('-o')
    recursive = '-r' in args
    if recursive:
        args.remove('-r')
    color = None
    for arg in args:
        if arg.startswith('--color='):
            color = arg.split('=', 1)[1]
            args.remove(arg)
            break
    if color == 'auto':
        color = 'always' if os.isatty(sys.stdout.fileno()) else 'never'
    pattern = args[1]

    if args[0] != "-E":
        print("Expected first argument to be '-E'")
        exit(1)

    print("Logs from your program will appear here!", file=sys.stderr)

    file_paths = args[2:] if len(args) > 2 else []

    if recursive and file_paths:
        input_files = []
        for fp in file_paths:
            if os.path.isfile(fp):
                input_files.append((fp, fp))
            elif os.path.isdir(fp):
                for root, dirs, files in os.walk(fp):
                    dirs.sort()
                    for fname in sorted(files):
                        full = os.path.join(root, fname)
                        input_files.append((full, full))
        multiple_files = True
    else:
        input_files = [(fp, fp) for fp in file_paths] if file_paths else []
        multiple_files = len(input_files) > 1

    def process_line(line, prefix):
        nonlocal found
        if only_matching:
            for start, end in find_all_matches(line, pattern):
                print(prefix + line[start:end])
                found = True
        else:
            if match_pattern(line, pattern):
                if color == 'always':
                    matches = find_all_matches(line, pattern)
                    result = []
                    prev = 0
                    for s, e in matches:
                        result.append(line[prev:s])
                        result.append('\033[01;31m' + line[s:e] + '\033[m')
                        prev = e
                    result.append(line[prev:])
                    print(prefix + ''.join(result))
                else:
                    print(prefix + line)
                found = True

    found = False
    if input_files:
        for fp, display_path in input_files:
            with open(fp) as f:
                input_data = f.read()
            prefix = display_path + ':' if multiple_files else ''
            for line in input_data.split('\n'):
                if line == '' and input_data.endswith('\n'):
                    continue
                process_line(line, prefix)
    else:
        input_data = sys.stdin.read()
        lines = input_data.split('\n')
        if lines and lines[-1] == '':
            lines = lines[:-1]
        for line in lines:
            process_line(line, '')

    if found:
        exit(0)
    else:
        exit(1)


if __name__ == "__main__":
    main()
