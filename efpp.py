#!/usr/bin/env python3
#
# efpp.py - Preprocessor for eFortran,
#           a readability-oriented dialect of Modern Fortran.
#
# https://github.com/akageyama/efpp
#
import re
import sys

#=============================================
def block_comment(lines_in):
#=============================================
    """
      Sample
              input:
                        abc def ghijklmn opq
                        !!>
                        abc def ghijklmn opq
                          !!>
                          abc def ghijklmn opq
                          abc def ghijklmn opq
                          !!<
                        abc def ghijklmn opq
                        !!<
                        abc def ghijklmn opq
        
              output:
                        abc def ghijklmn opq
                        !!>
                        !abc def ghijklmn opq
                        !   !!>
                        !!  abc def ghijklmn opq
                        !!  abc def ghijklmn opq
                        !   !!<
                        !abc def ghijklmn opq
                        !!<
                        abc def ghijklmn opq
    """

    output = list()

    comment_depth = 0

    for line in lines_in:
        match_obj_in = re.search(r'^\s*!!>', line)
        match_obj_out = re.search(r'^\s*!!<', line)
        if match_obj_out:
            comment_depth -= 1

        if comment_depth>0:
            line = re.sub(r'^', '!'*comment_depth, line)

        if match_obj_in:
            comment_depth += 1

        output.append(line)

    return output


#=============================================
def read_alias_list_and_make_dict(filename):
#=============================================
    """
        input = file 'efpp_alias.list'
        output = dictionary 'alias_dict'

        Example:
        --------<input>-------
        > cat efpp_alias.list
                 "do i bulk"  # you can separate the rule to two lines.
              => "do i = 1 , NXPP"

                 "do i full" => # you can put arrows, here, too.
                 "do i = 0 , NXPP1"
        --------</input>-------

        --------<output>-------
        alias_dict =  {
            'do i bulk': 'do i = 1 , NXPP',
            'do i full': 'do i = 0 , NXPP1'
        }
        --------</output>-------

    """

    patt_blank_line = r'^\s*$'
       #  000  '  '  (blank line)
    patt_comment_line = r'^\s*#.*$'
       #  000  '# comment ...'
    patt_both_left_and_right = r'^\s*\"(.*?)\"\s*=>\s*\"(.*?)\"\s#*.*$'
       #  000  '" left" => " right"               '
       #  000  '" left" => " right"  # comment ...'
    patt_left_hand_side = r'^\s*\"(.*?)\"\s*=>\s*#*.*$'
       #  000  '" left" =>                '
       #  000  '" left" =>   # comment ...'
    patt_right_hand_side = r'^\s*=>\s*\"(.*?)\"\s*#*.*$'
       #  000   '=> " right"               '
       #  000   '=> " right"  # comment ...'
    patt_left_or_right = r'^\s*\"(.*?)\"\s*#*.*$'
       #  000  '" left"                   '
       #  000  '" left"   # comment...    '
       #  000  '" right"                  '
       #  000  '" right"  # comment...    '

    alias_dict = dict()

    def register_alias(left, right, lineno):
        if left in alias_dict:
            print(
                f"efpp: error: duplicate alias '{left}' "
                f"at {filename}:{lineno}",
                file=sys.stderr
            )
            sys.exit(1)

        alias_dict[left] = right

    left = ''
    right = ''

    with open(filename) as f:
        for lineno, line in enumerate(f, start=1):
            m_blank_line = re.match(patt_blank_line, line)
            m_comment_line = re.match(patt_comment_line, line)
            m_both_left_and_right = re.match(patt_both_left_and_right, line)
            m_left_hand_side = re.match(patt_left_hand_side, line)
            m_right_hand_side = re.match(patt_right_hand_side, line)
            m_left_or_right = re.match(patt_left_or_right, line)
            if m_blank_line or m_comment_line:
                continue
            elif m_both_left_and_right:
                left = m_both_left_and_right.group(1)
                right = m_both_left_and_right.group(2)
                register_alias(left, right, lineno)
                left, right='', ''
            elif m_left_hand_side:
                left = m_left_hand_side.group(1)
                if right:
                    register_alias(left, right, lineno)
                    left, right='', ''
            elif m_right_hand_side:
                right = m_right_hand_side.group(1)
                if left:
                    register_alias(left, right, lineno)
                    left, right='', ''
            elif m_left_or_right:
                if left != '':
                    right = m_left_or_right.group(1)
                else:
                    left = m_left_or_right.group(1)
                if left != '' and right !='':
                    register_alias(left, right, lineno)
                    left, right='', ''
            else:
                print(
                    f"efpp: error: invalid alias definition "
                    f"at {filename}:{lineno}",
                    file=sys.stderr
                )
                sys.exit(1)

    # Check for an incomplete alias definition at EOF.
    if left or right:
        print(
            f"efpp: error: incomplete alias definition "
            f"at end of {filename}",
            file=sys.stderr
        )
        sys.exit(1)

    return alias_dict


#=============================================
def replace_period_in_member_accessor(string_in):
#=============================================
    """
    Convert member-access dots to '%', preserving
    Fortran strings, comments, numbers, and dot operators.
    """

    intrinsic_dots = {
        "and", "or", "not", "eqv", "neqv",
        "eq", "ne", "lt", "le", "gt", "ge",
        "true", "false"
    }


    # Mask strings and comments using the common lexer.
    code, comment_pos = mask_strings_and_comments(string_in)

    protected = [
        original == "." and masked != "."
        for original, masked in zip(string_in, code)
    ]

    # Protect decimal points in numeric literals.
    number_pattern = re.compile(
        r"(?<![A-Za-z_0-9.])"
        r"(?:"
        r"\d+\.\d*"
        r"|\.\d+"
        r")"
        r"(?:[eEdDqQ][+-]?\d+)?"
        r"(?:_[A-Za-z_0-9]+)?"
    )

    for m in number_pattern.finditer(code):
        for j in range(m.start(), m.end()):
            if code[j] == ".":
                protected[j] = True

    # Protect user-defined operators in OPERATOR declarations.
    operator_pattern = re.compile(
        r"\boperator\s*\(\s*\.[A-Za-z][A-Za-z_0-9]*\.\s*\)",
        re.IGNORECASE
    )

    for m in operator_pattern.finditer(code):
        for j in range(m.start(), m.end()):
            if code[j] == ".":
                protected[j] = True

    # Protect intrinsic and explicitly spaced dot operators.
    dot_pattern = re.compile(
        r"\.([A-Za-z][A-Za-z_0-9]*)\."
    )

    for m in dot_pattern.finditer(code):
        name = m.group(1).lower()
        left = m.start() - 1
        right = m.end()

        spaced = (
            (left >= 0 and code[left].isspace())
            or (right < len(code) and code[right].isspace())
        )

        if name in intrinsic_dots or spaced:
            protected[m.start()] = True
            protected[m.end() - 1] = True

    # Replace remaining dots.
    return "".join(
        "%" if c == "." and not protected[i] else c
        for i, c in enumerate(string_in)
    )


#=============================================
def replace_chars_in_string(string_in, pos_stt, pos_end, target_char):
#=============================================
    i = pos_stt
    char_list = list(string_in)

    while i <= pos_end:
        char_list[i] = target_char
        i += 1
    string_out = "".join(char_list)
    return string_out


#=============================================
def replace_characters_sandwiched_by_double_quotes(string_in):
#=============================================
    """
     Replace from abcd "efg hijklmn"
               to abcd "YYYYYYYYYYY"
    """
    ans = string_in
    m = re.search(r'\".*?\"', string_in)
    if m:
        string_tmp = replace_chars_in_string(string_in, m.start(), m.end(), 'X')
        ans = replace_characters_sandwiched_by_double_quotes(string_tmp)  # Recursion
    return ans


#=============================================
def replace_characters_sandwiched_by_single_quotes(string_in):
#=============================================
    """
     Replace from abcd 'efg hijklmn'
               to abcd 'YYYYYYYYYYY'
    """
    ans = string_in
    m = re.search(r'\'.*?\'', string_in)
    if m:
        string_tmp = replace_chars_in_string(string_in, m.start(), m.end(), 'Y')
        ans = replace_characters_sandwiched_by_single_quotes(string_tmp)  # Recursion
    return ans


#=============================================
def replace_decimal_point_number_of_dot_and_digits(string_in):
#=============================================
    """
     Replace from 0.14 +10.14 0.123 -3.14 .123 +0.123 -0.123 .123 +.1234 -.1234
               to 0Z14 +10Z14 0Z123 -3Z14 Z123 +0Z123 -0Z123 Z123 +Z1234 -Z1234
    """
    ans = string_in
    m = re.search(r'\.[0-9]', string_in)
    if m:
        string_tmp = replace_chars_in_string(string_in, m.start(), m.start(), 'Z')
        ans = replace_decimal_point_number_of_dot_and_digits(string_tmp)  # Recursion
    return ans


#=============================================
def replace_decimal_point_number_of_dot_and_e_and_digits(string_in):
#=============================================
    """
     Replace from 1.23e14 1.23e+14 1.23e-14 1.e14 1.e+14 1.e-14
               to 1Z23e14 1Z23e+14 1Z23e-14 1Ze14 1Ze+14 1Ze-14
    """
    ans = string_in
    m = re.search(r'[0-9]\.e[\+\-]?[0-9]+', string_in) 
    if m:
        string_tmp = replace_chars_in_string(string_in, m.start(), m.end(), 'Z')
        ans = replace_decimal_point_number_of_dot_and_e_and_digits(string_tmp)  # Recursion
    return ans


#=============================================
def replace_space_dot_string_dot_space(string_in):
#=============================================
    """
     Replace from a = .true. | a .cross. b | a = .not. b | routine(.abc.) 
               to a = ZtrueZ | a ZcrossZ b | a = ZnotZ b | routine(ZabcZ)
    """
    ans = string_in
    m = re.search(r'[ (]\.[a-zA-Z][a-zA-Z_0-9]*?\.[ )\n]', string_in)
    if m:
        string_tmp = replace_chars_in_string(string_in, m.start(), m.end()-1, 'Z')
        ans = replace_space_dot_string_dot_space(string_tmp)  # Recursion
    return ans


#=============================================
def remove_characters_in_comment(string_in):
#=============================================
    return re.sub(r'!.*', '!', string_in)


#=============================================
def alias_decode(alias_list, lines_in):
#=============================================
    """
    Converts strings. The rule is defined in alias_dict, which
    is constructed from a source text named 'efpp_alias.list'.

    ====<sample of alias_dict>====
        alias_dict = {
            "type(sfield_t)"
          : "real(DR), dimension(0:NXPP1,0:NYPP1,0:NZPP1)"
          ,
            "do i bulk"
          : "do i = 1 , NXPP"
          ,
            "do i full"
          : "do i = 0 , NXPP1"
          ,
            "do j bulk"
          : "do j = 1 , NYPP"
          ,
            "do j full"
          : "do j = 0 , NYPP1"
          ,
            "do k bulk"
          : "do k = 1 , NZPP"
          ,
            "do k full"
          : "do k = 0 , NZPP1"
        }
    ====</sample of alias_dict>====

    ====<source of the above: efpp_alias.list>====

        # since there is no typedef in fortran.
             "type(sfield_t)"
          => "real(DR), dimension(0:NXPP1,0:NYPP1,0:NZPP1)"

             "do i bulk"  # special macro in this code.
          => "do i = 1 , NXPP"

             "do i full" =>
             "do i = 0 , NXPP1"

             "do j bulk" =>
             "do j = 1 , NYPP"

             "do j full" =>
             "do j = 0 , NYPP1"

             "do k bulk"
          => "do k = 1 , NZPP"

             "do k full"
          => "do k = 0 , NZPP1"

    ====</source of the above: efpp_alias.list>====

    """

    # Default macros
    alias_dict = {
            "_?_"
          : "_BOOLEAN"
          ,
            " char(len="
          : " character(len="
          ,
            " <in> "
          : ", intent(in) "
          ,
            " <out> "
          : ", intent(out) "
          ,
            " <io> "
          : ", intent(inout) "
          ,
            " <optin> "
          : ", intent(in), optional "
          ,
            " <optout> "
          : ", intent(out), optional "
          ,
            " <optio> "
          : ", intent(inout), optional "
          ,
            " <const> "
          : ", parameter "
        }

    # Append user-defined macros only when an alias file is selected.
    if alias_list is not None:
        alias_dict.update(read_alias_list_and_make_dict(alias_list))

    output = list()
    for line in lines_in:
        l = line
        for i in alias_dict:
            l = l.replace(i,alias_dict[i])
        output.append(l)

    return output

#=============================================
def subsdiary_call_decode(lines_in):
#=============================================
    """
       xyz -call abc()  =>  xyz ;call abc()
           -call abc()  =>       call abc()
    """
    output = list()
    pat = re.compile(r'^(.*) -call +([a-zA-Z].*)')

    for line in lines_in:
        match = pat.search(line)
        if match:
            s = match.group(1)
            if re.search(r'^\s*$', s):
                s += '  call '
            else:
                s += ' ;call '
            s += match.group(2)
            s += '\n'
            output.append(s)
        else:
            output.append(line)

    return output


#=============================================
def special_block_decode(lines_in):
#=============================================
    """Translate DO-style just_once/every, and legacy blocks.

    Old marker spellings and their historical output formatting are preserved.
    Every source line produces exactly one output line. Ordinary Fortran IF
    and DO blocks are tracked to match special block terminators.
    """
    output = []
    # (kind, counter, source_line); counter is used only for skip blocks.
    stack = []
    pending_if = None  # Continued ordinary IF statement, not yet completed.

    legacy_once_begin = re.compile(r'^([^=]+)=+<just_once>=+(.*)$')
    legacy_once_end = re.compile(r'^([^=]+)=+</just_once>=+(.*)$')
    legacy_skip_begin = re.compile(
        r'^([^=]+)=+<skip\s+([a-zA-Z][a-zA-Z_0-9]*):(\s*.+)>=+(.*)$'
    )
    legacy_skip_end = re.compile(
        r'^([^=]+)=+</skip\s+([a-zA-Z][a-zA-Z_0-9]*)>=+(.*)$'
    )
    new_once_begin = re.compile(
        r'^(\s*)do\s*<just_once>\s*$', re.IGNORECASE
    )
    new_every_begin = re.compile(
        r'^(\s*)do\s*<every\s+([A-Za-z][A-Za-z_0-9]*)\s*:\s*([^>\r\n]+?)\s*>\s*$',
        re.IGNORECASE,
    )
    obsolete_skip_begin = re.compile(
        r'^\s*if\s*<skip\b', re.IGNORECASE
    )
    ordinary_if_begin = re.compile(
        r'^\s*(?:[A-Za-z]\w*\s*:\s*)?if\s*\(.*\)\s*then\s*$',
        re.IGNORECASE,
    )
    ordinary_if_end = re.compile(
        r'^\s*(?:end\s*if|endif)(?:\s+[A-Za-z]\w*)?\s*$',
        re.IGNORECASE,
    )
    obsolete_once_begin = re.compile(
        r'^\s*if\s*<just_once>\s*$', re.IGNORECASE
    )
    # Recognize ordinary block DO, including named DO and DO WHILE/CONCURRENT.
    ordinary_do_begin = re.compile(
        r'^\s*(?:[A-Za-z]\w*\s*:\s*)?do(?=\s|$)(?!\s*<)',
        re.IGNORECASE,
    )
    ordinary_do_end = re.compile(
        r'^\s*(?:end\s*do|enddo)(?:\s+[A-Za-z]\w*)?\s*$',
        re.IGNORECASE,
    )

    def reject_nested_just_once():
        if any(kind in ('just_once', 'legacy_just_once')
               for kind, _, _ in stack):
            raise ValueError('Nested just_once blocks are not allowed')

    for lineno, line in enumerate(lines_in, 1):
        # Legacy forms retain their original spelling-to-output mapping.
        m = legacy_once_begin.search(line)
        if m:
            reject_nested_just_once()
            stack.append(('legacy_just_once', None, lineno))
            output.append(m.group(1) + 'if (just_once) then '
                          + m.group(2) + '\n')
            continue

        m = legacy_once_end.search(line)
        if m:
            if not stack or stack[-1][0] != 'legacy_just_once':
                raise ValueError(f'Mismatched legacy just_once end at line {lineno}')
            stack.pop()
            output.append(m.group(1) + 'just_once = .false. ; end if '
                          + m.group(2) + '\n')
            continue

        m = legacy_skip_begin.search(line)
        if m:
            counter = m.group(2)
            stack.append(('legacy_skip', counter, lineno))
            output.append(m.group(1) + 'if(mod(' + counter + ','
                          + m.group(3) + ')==0) then' + m.group(4) + '\n')
            continue

        m = legacy_skip_end.search(line)
        if m:
            counter = m.group(2)
            if not stack or stack[-1][:2] != ('legacy_skip', counter):
                raise ValueError(f'Mismatched legacy skip end at line {lineno}')
            stack.pop()
            output.append(m.group(1) + 'end if; ' + counter + ' = '
                          + counter + ' + 1 ' + m.group(3) + '\n')
            continue

        # Ignore content inside strings and after an unquoted comment mark.
        _, comment_pos = mask_strings_and_comments(line)
        code = line[:comment_pos].rstrip('\r\n')
        comment = line[comment_pos:]
        trailing = code[len(code.rstrip(' \t')):]
        code = code.rstrip(' \t')
        newline = ('\r\n' if line.endswith('\r\n') else
                   '\n' if line.endswith('\n') else '')
        if newline and comment.endswith(newline):
            comment = comment[:-len(newline)]

        # A normal Fortran block IF may span continuation lines, e.g.
        #   if (a > 0 .or. &
        #       b > 0) then
        # Track the complete statement before classifying it as a block IF.
        # Preserve the original lines unchanged.
        if pending_if is not None:
            piece = code.strip()
            if piece and not piece.startswith('!'):
                piece = piece.lstrip('&').strip()
                continued = piece.endswith('&')
                pending_if += ' ' + piece.rstrip('&').rstrip()
                if not continued:
                    if ordinary_if_begin.match(pending_if):
                        stack.append(('if', None, lineno))
                    pending_if = None
            output.append(line)
            continue

        if re.match(r'^\s*(?:[A-Za-z]\w*\s*:\s*)?if\s*\(', code,
                    re.IGNORECASE) and code.endswith('&'):
            pending_if = code[:-1].rstrip()
            output.append(line)
            continue

        if obsolete_once_begin.match(code):
            raise ValueError(
                f'Unsupported if <just_once> at line {lineno}: '
                'use do <just_once> ... end do'
            )

        m = new_once_begin.match(code)
        if m:
            reject_nested_just_once()
            stack.append(('just_once', None, lineno))
            output.append(m.group(1) + 'if (just_once) then'
                          + trailing + comment + newline)
            continue

        if obsolete_skip_begin.match(code):
            raise ValueError(
                f'Unsupported if <skip ...> at line {lineno}: '
                'use do <every counter:interval> ... end do'
            )

        m = new_every_begin.match(code)
        if m:
            indent, counter, interval = m.groups()
            stack.append(('every', counter, lineno))
            output.append(indent + 'if(mod(' + counter + ','
                          + interval.strip() + ')==0) then'
                          + trailing + comment + newline)
            continue

        if ordinary_if_begin.match(code):
            stack.append(('if', None, lineno))
            output.append(line)
            continue

        if ordinary_do_begin.match(code):
            stack.append(('do', None, lineno))
            output.append(line)
            continue

        if ordinary_do_end.match(code):
            if not stack:
                output.append(line)  # Leave ordinary Fortran errors to compiler.
                continue
            kind, _, _ = stack[-1]
            if kind in ('if', 'legacy_just_once', 'legacy_skip'):
                raise ValueError(f'Mismatched end do at line {lineno}')
            stack.pop()
            indent = re.match(r'^\s*', code).group()
            if kind == 'just_once':
                output.append(indent + 'just_once = .false. ; end if'
                              + trailing + comment + newline)
            elif kind == 'every':
                output.append(indent + 'end if; ' + counter + ' = '
                              + counter + ' + 1'
                              + trailing + comment + newline)
            else:
                output.append(line)
            continue

        if ordinary_if_end.match(code):
            if not stack:
                output.append(line)  # Leave ordinary Fortran errors to compiler.
                continue
            kind, _, _ = stack[-1]
            if kind != 'if':
                raise ValueError(f'Mismatched end if at line {lineno}: '
                                 f'cannot close {kind} block')
            stack.pop()
            indent = re.match(r'^\s*', code).group()
            output.append(line)
            continue

        output.append(line)

    special_unclosed = [item for item in stack if item[0] not in ('if', 'do')]
    if special_unclosed:
        kind, _, lineno = special_unclosed[-1]
        raise ValueError(f'Unclosed {kind} block starting at line {lineno}')
    return output


#=============================================
def just_once_region(lines_in):
#=============================================
    """Compatibility wrapper for legacy and DO-style just_once blocks.

    New code should call special_block_decode() to handle just_once and skip
    in one pass. The wrapper remains for existing callers and unit tests.
    """
    return special_block_decode(lines_in)


#=============================================
def skip_counter(lines_in):
#=============================================
    """Compatibility wrapper for legacy skip and DO-style every blocks.

    Prefer special_block_decode() for new code; it handles all special blocks
    with one stack. The old IF-style skip spelling is no longer supported.
    """
    return special_block_decode(lines_in)


#=============================================
def routine_name_macro(lines_in):
#=============================================
    """
         module test_m ! <= Count this 'module'
           interface gen
             module procedure ... ! <= Do not count
                                  !    this as a 'module'
           end interface
           ..
         contains
           subroutine test__sub ! <= Count this as a 'subroutine'
           end subroutine test__sub
         end module test_m

         program main0 ! <= Count this as a 'program'
          ..
         contains
           subroutine sub1(...) ! <= Count this as a 'subroutine'
           contains
             function fun2(...) ! <= Count this as a 'function'
               print('__MODFUNC__')   ! print('main0/sub1/fun2')
             end function fun2
           end subroutine sub1
         end program main0
    """
    this_line_is_in_interface = False
    output = list()
    pat_program_in = re.compile(r'^(\s*)program\s+([a-zA-Z][a-zA-Z_0-9]*)\s+')
    pat_module_in = re.compile(r'^(\s*)module\s+([a-zA-Z][a-zA-Z_0-9]*)\s+')
    pat_subroufunc_in = re.compile(r'^(\s*)(elemental\s+)?(subroutine|function)\s+([a-zA-Z][a-zA-Z_0-9]*)[\s\(].*')
    pat_interface_in = re.compile(r'^(\s*)interface\s+[a-zA-Z][a-zA-Z_0-9]*')

    pat_program_out = re.compile(r'^(\s*)end\s+program\s+[a-zA-Z][a-zA-Z_0-9]*')
    pat_module_out = re.compile(r'^(\s*)end\s+module\s+[a-zA-Z][a-zA-Z_0-9]*')
    pat_subroufunc_out = re.compile(r'^(\s*)end\s+(subroutine|function)\s+[a-zA-Z][a-zA-Z_0-9]*')
    pat_interface_out = re.compile(r'^(\s*)end\s+interface')

    lctr = 0  # line counter
    name = list()
    for line in lines_in:
        lctr += 1
        match_program_in = pat_program_in.search(line)
        match_module_in = pat_module_in.search(line)
        match_subroufunc_in = pat_subroufunc_in.search(line)
        match_interface_in = pat_interface_in.search(line)
        match_program_out = pat_program_out.search(line)
        match_module_out = pat_module_out.search(line)
        match_subroufunc_out = pat_subroufunc_out.search(line)
        match_interface_out = pat_interface_out.search(line)

        if match_program_in:
            name.append(match_program_in.group(2))

        if match_interface_in:
            this_line_is_in_interface = True
        if match_interface_out:
            this_line_is_in_interface = False

        if match_module_in:
            if not this_line_is_in_interface:
                name.append(match_module_in.group(2))
        if match_subroufunc_in:
            name.append(match_subroufunc_in.group(4))
        if match_program_out:
            name.pop()
        if match_module_out:
            name.pop()
        if match_subroufunc_out:
            name.pop()

        if len(name)>0:
            progmodule_name = name[0]
            line = line.replace('__MODULE__', progmodule_name)
            module_plus_linenum =  progmodule_name + '(' + str(lctr) + ')'
            line = line.replace('__MODLINE__', module_plus_linenum )
        if len(name)==3:
            subroufunc_name = name[1] + '/' + name[2]
            line = line.replace('__FUNC__', subroufunc_name)
            module_plus_subroufunc_name = progmodule_name + '/' + subroufunc_name
            line = line.replace('__MODFUNC__', module_plus_subroufunc_name)
        elif len(name)==2:
            subroufunc_name = name[1]
            line = line.replace('__FUNC__', subroufunc_name)
            module_plus_subroufunc_name = progmodule_name + '/' + subroufunc_name
            line = line.replace('__MODFUNC__', module_plus_subroufunc_name)

        line = line.replace('__LINE__', str(lctr))

        output.append(line)

    return output


#=============================================
def member_access_operator_macro(lines_in):
#=============================================
    """
      Replaces "." to "%", for example,

        > call mhd.sub.update(mhd.main)

      is converted to

        > call mhd%sub%update(mhd%main)
    """
    """
        a3.y14 = 3.10_DR
        grid.x = 1.0_DR
    """

    output = list()

    for line in lines_in:
        line_replaced = replace_period_in_member_accessor(line)
        output.append(line_replaced)

    return output


#=============================================
def check_implicit_none(filename_in, lines_in):
#=============================================
    """
      Check if the line "implicit none" appears.
    """
    pat_comment = re.compile(r'^\s*\!.*$')
    pat_blank = re.compile(r'^\s*$')
    pat_use = re.compile(r'^\s*use\s+[a-zA-Z][a-zA-Z_0-9]*')
    pat_implicit_none = re.compile(r'^\s*implicit none\s+')
    pat_program = re.compile(r'^\s*program\s+[a-zA-Z][a-zA-Z_0-9]*')
    pat_module = re.compile(r'^\s*module\s+[a-zA-Z][a-zA-Z_0-9]*')
    search_mode_on_for_implicit_none = False

    for line in lines_in:
        if pat_comment.search(line) or pat_blank.search(line):
            continue  # Skip comment lines.
        if search_mode_on_for_implicit_none:
            if pat_use.search(line):
                continue  # Skip 'use ***' lines.
            elif pat_implicit_none.search(line):
                return  # O.K. this code is fine.
            else:
                break  # Other line appears before "implicit none"
        elif pat_module.search(line) or pat_program.search(line):
            search_mode_on_for_implicit_none = True

    error_message = 'Error in '+filename_in+': You forgot "implicit none"\n'
    sys.stderr.write(error_message)
    sys.exit(1)


#=============================================
def clock_decode(lines_in):
#=============================================
    """
     # Before...
     #   ___________________________________________
     #                          !{  main}{{STT}}
     #   call fluid%create(lat) !{  main}{flu cr}
     #   call fluid%set_initial(lat)
     #                          !{  main}{flu in}
     #   do loop = 1 , loop_max !{{count}}
     #     call pdf%shift(lat)  !{  main}{pdfsht}
     #   end do
     #   call fluid%finalize    !{  main}{{END}}
     #                          !{{print}}
     #
     # After...  (You should apply "subsidiary_caller" later.)
     #   ___________________________________________
     #                          -call Clock%start('  main')
     #   call fluid%create(lat) -call Clock%lap  ('  main','flu cr')
     #   call fluid%set_initial(lat)
     #                          -call Clock%lap  ('  main','flu in')
     #   do loop = 1 , loop_max -call Clock%count
     #     call pdf%shift(lat)  -call Clock%lap  ('  main','pdfsht')
     #   end do
     #   call fluid%finalize    -call Clock%stop ('  main')
     #                          -call Clock%print
     #
    """
    output = list()
    pat_stt = re.compile(r'^(.*)\s+!\{(......)\}\{\{STT\}\}')
    pat_cal = re.compile(r'^(.*)\s+!\{(......)\}\{(......)\}')
    pat_cnt = re.compile(r'^(.*)\s+!\{\{count\}\}')
    pat_end = re.compile(r'^(.*)\s+!\{(......)\}\{\{END\}\}')
    pat_pri = re.compile(r'^(.*)\s+!\{\{print\}\}(.*)')

    for line in lines_in:
        match_stt = pat_stt.search(line)
        match_cal = pat_cal.search(line)
        match_cnt = pat_cnt.search(line)
        match_end = pat_end.search(line)
        match_pri = pat_pri.search(line)
        if match_stt:
            line = match_stt.group(1) + ' '
            line += '-call Clock%start(\'' + match_stt.group(2)
            line += '\')' + '\n'
        if match_cal:
            line = match_cal.group(1) + ' '
            line += '-call Clock%lap  (\'' + match_cal.group(2)
            line += '\',\'' +  match_cal.group(3)
            line += '\')' + '\n'
        if match_cnt:
            line = match_cnt.group(1) + ' '
            line += '-call Clock%count\n'
        if match_end:
            line = match_end.group(1) + ' '
            line += '-call Clock%stop (\'' + match_end.group(2)
            line += '\')' + '\n'
        if match_pri:
            line = match_pri.group(1) + ' '
            line += '-call Clock%print' + match_pri.group(2) + '\n'
        output.append(line)

    return output


#=============================================
def mask_strings_and_comments(line):
#=============================================
    """
    Mask Fortran string literals and comments with spaces.

    Returns:
        masked: same-length string with literals and comments masked
        comment_pos: position of the first unquoted '!'
                     or len(line) if no comment exists
    """
    masked = list(line)
    quote = None
    i = 0

    while i < len(line):
        c = line[i]

        if quote is not None:
            masked[i] = ' '
            if c == quote:
                if i + 1 < len(line) and line[i + 1] == quote:
                    masked[i + 1] = ' '
                    i += 2
                    continue
                quote = None

        elif c in ("'", '"'):
            quote = c
            masked[i] = ' '

        elif c == '!':
            masked[i:] = [' '] * (len(line) - i)
            return ''.join(masked), i

        i += 1

    return ''.join(masked), len(line)


#=============================================
def operator_decode_single(statement):
#=============================================
    """
    Convert a compound assignment in a single Fortran
    statement. The input and output contain no newline,
    comment, or statement-separating semicolon.
    """

    def split_if_prefix(text, masked):
        m = re.match(r'^\s*if\s*\(', masked, re.IGNORECASE)

        if not m:
            return '', text

        depth = 1
        i = m.end()

        while i < len(masked) and depth > 0:
            if masked[i] == '(':
                depth += 1
            elif masked[i] == ')':
                depth -= 1
            i += 1

        if depth != 0:
            return '', text

        if i >= len(masked) or not masked[i].isspace():
            return '', text

        while i < len(masked) and masked[i].isspace():
            i += 1

        return text[:i], text[i:]

    masked, _ = mask_strings_and_comments(statement)

    m = re.search(r'([+\-*])=', masked)
    if m is None:
        return statement

    op = m.group(1)
    left = statement[:m.start()]
    right = statement[m.end():]

    prefix, lhs = split_if_prefix(left, masked[:m.start()])

    if not prefix:
        indent = re.match(r'^\s*', lhs).group()
        prefix = indent
        lhs = lhs[len(indent):]

    lhs = lhs.strip()
    rhs = right.strip()

    # Preserve trailing whitespace.
    trailing_spaces = right[len(right.rstrip(' \t')):]

    if not lhs or not rhs:
        return statement

    if not re.match(r'^[A-Za-z_][A-Za-z_0-9]*', lhs):
        return statement

    # Check balanced parentheses in the LHS.
    depth = 0
    for c in lhs:
        if c == '(':
            depth += 1
        elif c == ')':
            depth -= 1
            if depth < 0:
                return statement

    if depth != 0:
        return statement

    return (
        prefix + lhs + ' = ' + lhs
        + ' ' + op + ' ' + rhs + trailing_spaces
    )


#=============================================
def operator_decode(lines_in):
#=============================================
    """
    Convert compound assignments in semicolon-separated
    Fortran statements, preserving strings and comments.
    """
    output = []

    for line in lines_in:
        masked, comment_pos = mask_strings_and_comments(line)

        code = line[:comment_pos]
        comment = line[comment_pos:]

        # Locate semicolons outside string literals.
        positions = [
            i for i, c in enumerate(masked[:comment_pos])
            if c == ';'
        ]

        # Preserve whitespace immediately before a comment.
        trailing_spaces = ''

        if comment_pos < len(line):
            trailing_spaces = code[len(code.rstrip(' \t')):]
            code = code.rstrip(' \t')

        # Split while retaining semicolons.
        parts = []
        start = 0

        for pos in positions:
            parts.append(code[start:pos + 1])
            start = pos + 1

        parts.append(code[start:])

        converted_parts = []

        for part in parts:
            # Preserve whitespace before a semicolon.
            if part.endswith(';'):
                statement = part[:-1]
                spaces_before_semicolon = statement[len(statement.rstrip(' \t')):]
                statement = statement.rstrip(' \t')
                delimiter = spaces_before_semicolon + ';'
            else:
                statement = part
                delimiter = ''

            # Reuse the existing single-statement converter.
            converted = operator_decode_single(
                statement.rstrip('\r\n')
            )

            converted_parts.append(
                converted + delimiter
            )

        # Preserve the original line ending.
        newline = ''
        if line.endswith('\r\n'):
            newline = '\r\n'
        elif line.endswith('\n'):
            newline = '\n'

        # Remove the newline from the comment, if present.
        if newline and comment.endswith(newline):
            comment = comment[:-len(newline)]

        output.append(
            ''.join(converted_parts)
            + trailing_spaces + comment + newline
        )

    return output


#=============================================
def debugp_decode(lines_in):
#=============================================
    """
      !debugp val
    =>
      print *, "\\modname(linenum): ", "val =", val

      !debugp "str"
    =>
      print *, "\\modname(linenum): ", "str"

      !debugp "str", val1
    =>
      print *, "\\modname(linenum): ", "str", "val1 = ", val1

      !debugp "str", val1, val2, ...
    =>
      print *, "\\modname(linenum): ", "str", "val1 = ", val1, "val2 = ", ...

      !debugp "str1", val1, "str2", val2, ...
    =>
      print *, "\\modname(linenum): ", "str1", "val1 = ", val1, "str2", "val2 = ", ...
    """
    output = list()

    pat = re.compile(r'(.*)!debugp\s+(.*)$')

    for line in lines_in:
        match = pat.search(line)
        if match:
            args = match.group(2).split(',')
            line = match.group(1)
            if line.strip():  # it's not empty.
                line += ';'
            line += 'print *, '
            line += '\"\\\\__MODULE__(__LINE__): \", '
            countParenthesis = 0
            temp = ''
            for arg in args:
                a = arg.strip() # put off blanks
                if a[0]=='\'' or a[0]=='\"':  # string (e.g., 'message')
                    if a[-1]=='\'' or a[-1]=='\"':  # string (e.g., 'say,...)
                        line += a + ', '
                    else:
                        line += a + ', ' + a[0] + ', '
                elif a[-1]=='\'' or a[-1]=='\"':# string (e.g., '..., smthng')
                    line +=  a[-1] + a + ', '
                elif '(' in a or countParenthesis!=0:
                    if '(' in a:
                        countParenthesis += a.count('(') - a.count(')')
                        temp += a + ', '
                        if countParenthesis == 0:
                            temp = temp[:-2]  # put of the last "comma + space"
                            line += "\" " + temp + " = \", " + temp + ', '
                    elif ')' in a:
                        countParenthesis += a.count('(') - a.count(')')
                        temp += a + ', '
                        if countParenthesis == 0:
                            temp = temp[:-2]  # put of the last "comma + space"
                            line += "\" " + temp + " = \", " + temp + ', '
                    else:
                        temp += a + ', '
                else:
                    line += "\" " + a + " = \", " + a + ', '
            line = line[:-2]  # put of the last "comma + space"
            line += '\n'
        output.append(line)

    return output


#=============================================
def efpp(filename_in, alias_list):
#=============================================

    """    A preprocessor for Fortran 2003.

         input: filename_in (e.g., 'main.ef')
        output: standard out
    """
    with open(filename_in,'r') as f:
        lines = f.readlines()
        # We are applying multiple docoders to 'lines. 
        #
        # The call-order is basically arbitrary, with
        # the following two caveat:
        #
        # (1) 'clock_decode' shoud be called before 
        #     'subsdiary_call_decode'.
        # (2) 'alias_docode' should be called before 
        #     'routine_name_macro', __LINE__ etc, 
        # could be included in 'efpp_alias.list'.
        lines = clock_decode(lines)
        lines = subsdiary_call_decode(lines)
        lines = block_comment(lines)
        lines = operator_decode(lines)
        lines = special_block_decode(lines)
        lines = alias_decode(alias_list, lines)
        lines = debugp_decode(lines)
        lines = routine_name_macro(lines)
        lines = member_access_operator_macro(lines)

        check_implicit_none(filename_in, lines)

        for l in lines:
            print(l,end='')


if __name__ == '__main__':

    if len(sys.argv) == 1:
        filename_in = input('enter filename_in name > ')
    else:
        filename_in = sys.argv[1]

    if len(sys.argv) >= 3:
        # An explicitly specified alias file must exist.
        filename_alias_list = sys.argv[2]
    else:
        # The default alias file is optional (relative to the working directory).
        import os
        default_alias = 'efpp_alias.list'
        filename_alias_list = (
            default_alias if os.path.isfile(default_alias) else None
        )

    try:
        efpp(filename_in, filename_alias_list)
    except FileNotFoundError as e:
        print(
            f"efpp: error: file not found: {e.filename}",
            file=sys.stderr
        )
        sys.exit(1)
