#!/usr/bin/env python3
#
#  efpp.py:
#    Preprocessor for eFortran, a dialect of Modern Fortran.
#
#  developed by A. Kageyama (kage@port.kobe-u.ac.jp)
#            on 2017.09.17, for cg-mhd project.
#    revised on 2018.07.13, for general eFortran codes.
#
#  Reference:
#     S. Hosoyamada and A. Kageyama,
#     "A Dialect of Modern Fortran for Simulations" '
#     in Communications in Computer and Information Science,
#     vol 946, pages 439-448, 2018 (Proceedings of AsiaSim2018)
#
#  Home page:
#     https://github.com/akageyama/efpp
#
import re
import sys

#=============================================
def block_comment(lines_in):
#=============================================
    """
      sample input:
      --------------------------
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

      sample output
      --------------------------
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
      --------------------------
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
    left = ''
    right = ''
    with open(filename) as f:
        for line in f:
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
                alias_dict[left] = right
                left, right='', ''
            elif m_left_hand_side:
                left = m_left_hand_side.group(1)
                if right:
                    alias_dict[left] = right
                    left, right='', ''
            elif m_right_hand_side:
                right = m_right_hand_side.group(1)
                if left:
                    alias_dict[left] = right
                    left, right='', ''
            elif m_left_or_right:
                if left != '':
                    right = m_left_or_right.group(1)
                else:
                    left = m_left_or_right.group(1)
                if left != '' and right !='':
                    alias_dict[left] = right
                    left, right='', ''
            else:
                print("error. unknown pattern.")
                sys.exit()

    return alias_dict


#=============================================
def replace_period_in_member_accessor(string_in):
#=============================================

    string_work1 = replace_characters_sandwiched_by_double_quotes(string_in)
    string_work2 = replace_characters_sandwiched_by_single_quotes(string_work1)
    string_work3 = remove_characters_in_comment(string_work2)

    # Regexp for the period letter '.' used as a member access operator.
    # pattern = r'[a-zA-Z][a-zA-Z_0-9]*?\)?\.[a-zA-Z][a-zA-Z_0-9]*?'  # before 2022.08.11
    pattern = r'[a-zA-Z][a-zA-Z_0-9]*?(\([a-zA-Z_0-9]*\))?\.[a-zA-Z][a-zA-Z_0-9]*?'  # revised on 2022.08.11
    #  array(3).a02.mem01 ==> array(3)%a02%mem01
    m = re.search(pattern, string_work3)
    ans = string_in
    if m:
        char_pos = string_in.find('.', m.start(), m.end()) # in the match
        string_work = replace_chars_in_string(string_in, char_pos, char_pos, '%')
        ans = replace_period_in_member_accessor(string_work)
    return ans


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
    ans = string_in
    m = re.search(r'\".*?\"', string_in)
    if m:
        string_tmp = replace_chars_in_string(string_in, m.start(), m.end()-1, 'X')
        ans = replace_characters_sandwiched_by_double_quotes(string_tmp)  # Recursion
    return ans


#=============================================
def replace_characters_sandwiched_by_single_quotes(string_in):
#=============================================
    ans = string_in
    m = re.search(r'\'.*?\'', string_in)
    if m:
        string_tmp = replace_chars_in_string(string_in, m.start(), m.end()-1, 'Y')
        ans = replace_characters_sandwiched_by_single_quotes(string_tmp)  # Recursion
    return ans

#=============================================
def remove_characters_in_comment(string_in):
#=============================================
    return re.sub(r'!.*', '!', string_in)



#=============================================
def alias_decode(lines_in):
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

    # Append user-defined macros
    alias_dict.update(read_alias_list_and_make_dict('efpp_alias.list'))

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
def just_once_region(lines_in):
#=============================================
    """
       program test
         logical :: just_once = .true.
         ==<just_once>==    ! you can put comment here.
           call subsub('asdfasdf')
         ==</just_once>==   ! end of just_once region.
       end program test
    """
    output = list()
    pat_begin = re.compile(r'^([^=]+)=+<just_once>=+(.*)$')
    pat_end = re.compile(r'^([^=]+)=+</just_once>=+(.*)$')

    for line in lines_in:
        match_begin = pat_begin.search(line)
        match_end = pat_end.search(line)
        if match_begin:
            s = match_begin.group(1)
            s += 'if (just_once) then'
            s += ' ' + match_begin.group(2)
            s += '\n'
        elif match_end:
            s = match_end.group(1)
            s += 'just_once = .false. ; end if'
            s += ' ' + match_end.group(2)
            s += '\n'
        else:
            s = line
        output.append(s)

    return output


#=============================================
def skip_counter(lines_in):
#=============================================
    """
        # program test
        #   inte(SI) :: ctr=0
        #   inte(SI) :: i
        #   do i = 1 , 200
        #     ===<skip ctr:8>===  ! you can put comment.
        #       call subsub('asdfasdf',i)
        #     ===</skip ctr>===   ! end of skip block.
        #   end do
        # end program test
    """
    output = list()
    pat_begin = re.compile(r'^([^=]+)=+<skip\s+([a-zA-Z][a-zA-Z_0-9]*):(\s*.+)>=+(.*)$')
    pat_end = re.compile(r'^([^=]+)=+</skip\s+([a-zA-Z][a-zA-Z_0-9]*)>=+(.*)$')

    for line in lines_in:
        match_begin = pat_begin.search(line)
        match_end = pat_end.search(line)
        if match_begin:
            s = match_begin.group(1)
            s += 'if(mod(' + match_begin.group(2)
            s += ',' + match_begin.group(3)
            s += ')==0) then' + match_begin.group(4)
            s += '\n'
        elif match_end:
            s = match_end.group(1)
            s += 'end if; '
            s += match_end.group(2) + ' = '
            s += match_end.group(2) + ' + 1'
            s += ' ' + match_end.group(3)
            s += '\n'
        else:
            s = line
        output.append(s)

    return output

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
def kutimer_docode(lines_in):
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
     #                          -call kutimer__start('  main')
     #   call fluid%create(lat) -call kutimer__('  main','flu cr')
     #   call fluid%set_initial(lat)
     #                          -call kutimer__('  main','flu in')
     #   do loop = 1 , loop_max -call kutimer__count
     #     call pdf%shift(lat)  -call kutimer__('  main','pdfsht')
     #   end do
     #   call fluid%finalize    -call kutimer__end('  main')
     #                          -call kutimer__print
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
            line += '-call kutimer__start(\'' + match_stt.group(2)
            line += '\')' + '\n'
        if match_cal:
            line = match_cal.group(1) + ' '
            line += '-call kutimer__(\'' + match_cal.group(2)
            line += '\',\'' +  match_cal.group(3)
            line += '\')' + '\n'
        if match_cnt:
            line = match_cnt.group(1) + ' '
            line += '-call kutimer__count\n'
        if match_end:
            line = match_end.group(1) + ' '
            line += '-call kutimer__end(\'' + match_end.group(2)
            line += '\')' + '\n'
        if match_pri:
            line = match_pri.group(1) + ' '
            line += '-call kutimer__print' + match_pri.group(2) + '\n'
        output.append(line)

    return output


#=============================================
def operator_decode(lines_in):
#=============================================
    """
      "... val += aa"     is converted into
      "... val = val + aa"

      "... val -= aa"     is converted into
      "... val = val - aa"

      "if (xyz>0) xyz *=  2" is converted into
      "if (xyz>0) xyz = xyz * 2"

      but

       "val /= 2" is not converted since
       it stands for val does not equal to 2.
    """
    output = list()

    pat = re.compile(r'(.*)\s+?(\S+)' \
                      '\s+?([\+\-\*])=\s+?' \
                      '(.+)$')
    for line in lines_in:
        match = pat.search(line)
        if match:
            s = match.group(1)          # if (xyz>0)
            s += ' ' + match.group(2)   # if (xyz>0) xyz
            s += ' = ' + match.group(2) # if (xyz>0) xyz = xyz
            s += ' ' + match.group(3)   # if (xyz>0) xyz = xyz /
            s += ' ' + match.group(4)   # if (xyz>0) xyz = xyz / 2
            s += '\n'
            output.append(s)
        else:
            output.append(line)

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
def efpp(filename_in):
#=============================================

    """    A preprocessor for Fortran 2003.

         input: filename_in (e.g., 'main.e03')
        output: standard out
    """
    with open(filename_in,'r') as f:
        lines = f.readlines()
        # In the followings, we apply multiple docoders
        # to 'lines. Their call-order is basically arbitrary.
        # Only exception is that 'kutimer_decode' shoud be
        # called before 'subsdiary_call_decode', because
        # 'kutimer_decode' generates routine calls such
        # as '...  -call kutimer__...', which is supposed
        # to be processed by 'subsdiary_call_decode'.
        #   One more condition, 'alias_docode' should be
        # called before 'routine_name_macro', __LINE__ etc, 
        # could be included in 'efpp_alias.list'.
        lines = kutimer_docode(lines)
        lines = subsdiary_call_decode(lines)
        lines = block_comment(lines)
        lines = operator_decode(lines)
        lines = just_once_region(lines)
        lines = skip_counter(lines)
        lines = alias_decode(lines)
        lines = debugp_decode(lines)
        lines = routine_name_macro(lines)
        lines = member_access_operator_macro(lines)

        check_implicit_none(filename_in, lines)

        for l in lines:
            print(l,end='')




if __name__ == '__main__':

    if len(sys.argv)==1:
        filename_in = input('enter filename_in name > ')
    else:
        filename_in = sys.argv[1]

    efpp(filename_in)
