import sys

# import pyparsing - available if you need it!
# import lark - available if you need it!


def match_at(input_line, pattern, pos):
    """Try to match the full pattern starting at position pos in input_line."""
    pi = 0  # pattern index
    ii = pos  # input index
    while pi < len(pattern):
        if pattern[pi] == '\\' and pi + 1 < len(pattern):
            esc = pattern[pi + 1]
            if esc == 'd':
                is_match = ii < len(input_line) and input_line[ii].isdigit()
            elif esc == 'w':
                is_match = ii < len(input_line) and (input_line[ii].isalnum() or input_line[ii] == '_')
            else:
                is_match = False
            if not is_match:
                return False
            pi += 2
            ii += 1
        elif pattern[pi] == '[':
            end = pattern.index(']', pi + 1)
            if pattern[pi + 1] == '^':
                chars = pattern[pi + 2:end]
                if ii >= len(input_line) or input_line[ii] in chars:
                    return False
            else:
                chars = pattern[pi + 1:end]
                if ii >= len(input_line) or input_line[ii] not in chars:
                    return False
            pi = end + 1
            ii += 1
        else:
            if ii >= len(input_line) or input_line[ii] != pattern[pi]:
                return False
            pi += 1
            ii += 1
    return True


def match_pattern(input_line, pattern):
    for start in range(len(input_line)):
        if match_at(input_line, pattern, start):
            return True
    return False


def main():
    pattern = sys.argv[2]
    input_line = sys.stdin.read()

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
