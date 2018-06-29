#!/usr/bin/env python3
#
#  efpp.py    A preprocessor for Fortran 2003.
#
#
#     developed by A. Kageyama (kage@port.kobe-u.ac.jp)
#               on 2017.09.17, for cg-mhd.
#     revised by A. Kageyama on 2018.05.28 for yyz-relax.
#     revised by S. Hosoyamada on 2018.06.26,
#             adding new function "type_member_macro".
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
                =======
                abc def ghijklmn opq
                  ======
                  abc def ghijklmn opq
                  abc def ghijklmn opq
                  ======
                abc def ghijklmn opq
                =======
                abc def ghijklmn opq

      sample output
      --------------------------
                abc def ghijklmn opq
                !=======
                !abc def ghijklmn opq
                !!  ======
                !!  abc def ghijklmn opq
                !!  abc def ghijklmn opq
                !!  ======
                !abc def ghijklmn opq
                !=======
                abc def ghijklmn opq
      --------------------------
    """

    output = list()

    comment_span_list = list()
    comment_depth = 0
    comment_block_exit_flag = False

    for line in lines_in:
        match_obj = re.search(r'^ *===+\s+$', line)
        comment_block_exit_flag = False
        if match_obj:
            span = match_obj.span()
            if comment_depth == 0:  # Entered the 1st comment block.
                comment_span_list.append(span)
                comment_depth = 1
            else:
                if span==comment_span_list[-1]:
                    # End of the present comment block.
                    del comment_span_list[-1]
                    comment_block_exit_flag = True
                else: # Entered new (deeper) comment block.
                    comment_span_list.append(span)
                    comment_depth += 1

        if comment_depth>0:
            line = re.sub(r'^', '!'*comment_depth, line)

        if comment_block_exit_flag:
            comment_depth -= 1

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
          ,
            "\[div_v_ijk_term01\]"
          : "(vx(ip1,j,k)-vx(im1,j,k))*dx1"
          ,
            "\[div_v_ijk_term02\]"
          : "(vy(i,jp1,k)-vy(i,jm1,k))*dy1"
          ,
            "\[div_v_ijk_term03\]"
          : "(vz(i,j,kp1)-vz(i,j,km1))*dz1"
          ,
            "\[curl_v_ijk_x\]"
          : "(vz(i,jp1,k)-vz(i,jm1,k))*dy1-(vy(i,j,kp1)-vy(i,j,km1))*dz1"
          ,
            "\[curl_v_ijk_y\]"
          : "(vx(i,j,kp1)-vx(i,j,km1))*dz1-(vz(ip1,j,k)-vz(im1,j,k))*dx1"
          ,
            "\[curl_v_ijk_z\]"
          : "(vy(ip1,j,k)-vy(im1,j,k))*dx1-(vx(i,jp1,k)-vx(i,jm1,k))*dy1"
          ,
            "\[grad_f_ijk_x\]"
          : "(f(ip1,j,k)-f(im1,j,k))*dx1"
          ,
            "\[grad_f_ijk_y\]"
          : "(f(i,jp1,k)-f(i,jm1,k))*dy1"
          ,
            "\[grad_f_ijk_z\]"
          : "(f(i,j,kp1)-f(i,j,km1))*dz1"
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

             "\[div_v_ijk_term01\]"
          => "(vx(ip1,j,k)-vx(im1,j,k))*dx1"

             "\[div_v_ijk_term02\]"
          => "(vy(i,jp1,k)-vy(i,jm1,k))*dy1"

             "\[div_v_ijk_term03\]"
          => "(vz(i,j,kp1)-vz(i,j,km1))*dz1"

             "\[curl_v_ijk_x\]"
          => "(vz(i,jp1,k)-vz(i,jm1,k))*dy1-(vy(i,j,kp1)-vy(i,j,km1))*dz1"

             "\[curl_v_ijk_y\]"
          => "(vx(i,j,kp1)-vx(i,j,km1))*dz1-(vz(ip1,j,k)-vz(im1,j,k))*dx1"

             "\[curl_v_ijk_z\]"
          => "(vy(ip1,j,k)-vy(im1,j,k))*dx1-(vx(i,jp1,k)-vx(i,jm1,k))*dy1"

             "\[grad_f_ijk_x\]"
          => "(f(ip1,j,k)-f(im1,j,k))*dx1"

             "\[grad_f_ijk_y\]"
          => "(f(i,jp1,k)-f(i,jm1,k))*dy1"

             "\[grad_f_ijk_z\]"
          => "(f(i,j,kp1)-f(i,j,km1))*dz1"

    ====</source of the above: efpp_alias.list>====

    """

    # Default macros
    alias_dict = {
            " inte(SI)"
          : " integer(SI)"
          ,
            " inte(DI)"
          : " integer(DI)"
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
    pat_begin = re.compile(r'^([^=]+)[=]+<just_once>[=]+(.*)$')
    pat_end = re.compile(r'^([^=]+)[=]+</just_once>[=]+(.*)$')

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
    pat_begin = re.compile(r'^([^=]+)[=]+<skip[\s]+([a-zA-Z][a-zA-Z_0-9]*):([\s]*[\d]+)>[=]+(.*)$')
    pat_end = re.compile(r'^([^=]+)[=]+</skip[\s]+([a-zA-Z][a-zA-Z_0-9]*)>[=]+(.*)$')

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
               print('__FILE__/__PROGRAM__')   ! print('main0/sub1/fun2')
             end function fun2
           end subroutine sub1
         end program main0
    """
    this_line_is_in_interface = False
    output = list()
    pat_program_in = re.compile(r'^([\s]*)program[\s]+([a-zA-Z][a-zA-Z_0-9]*)\s+')
    pat_module_in = re.compile(r'^([\s]*)module[\s]+([a-zA-Z][a-zA-Z_0-9]*)\s+')
    pat_subroufunc_in = re.compile(r'^([\s]*)(subroutine|function)[\s]+([a-zA-Z][a-zA-Z_0-9]*)[\s\(].*')
    pat_interface_in = re.compile(r'^([\s]*)interface[\s]+[a-zA-Z][a-zA-Z_0-9]*')

    pat_program_out = re.compile(r'^([\s]*)end[\s]+program[\s]+[a-zA-Z][a-zA-Z_0-9]*')
    pat_module_out = re.compile(r'^([\s]*)end[\s]+module[\s]+[a-zA-Z][a-zA-Z_0-9]*')
    pat_subroufunc_out = re.compile(r'^([\s]*)end[\s]+(subroutine|function)[\s]+[a-zA-Z][a-zA-Z_0-9]*')
    pat_interface_out = re.compile(r'^([\s]*)end[\s]+interface')

    name = list()
    for line in lines_in:
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
            name.append(match_subroufunc_in.group(3))
        if match_program_out:
            name.pop()
        if match_module_out:
            name.pop()
        if match_subroufunc_out:
            name.pop()

        if len(name)>0:
            progmodule_name = name[0]
            line = line.replace('__FILE__', progmodule_name)
        if len(name)==3:
            subroufunc_name = name[1] + '/' + name[2]
            line = line.replace('__ROUTINE__', subroufunc_name)
        elif len(name)==2:
            subroufunc_name = name[1]
            line = line.replace('__ROUTINE__', subroufunc_name)

        output.append(line)

    return output


#=============================================
def type_member_macro(lines_in):
#=============================================
    """
      Replaces "." to "%", for example,

        > call mhd.sub.update(mhd.main)

      is converted to

        > call mhd%sub%update(mhd%main)

      Exceptions of the conversion:
        1) The dot in single-quotation makrs.  e.g.) filename = 'main.e03'
        2) The dot in double-quotation makrs.  e.g.) filename = "main.e03"
        3) User-defined and logical operators. e.g.) A .and. B
        4) Logical operator ".not.".           e.g.) .not.must_be_true
        5) The dot in a floating point number. e.g.) 3.141592, -1.e-14
        6) Dots in comment lines.              e.g.) ! main.sub 
    """
    output = list()
    pat_type_member = re.compile(r'.*[a-zA-Z_0-9]\.[a-zA-Z_].*\n')
    pat_single_quotation = r'\'.*?\''
    pat_double_quotation = r'\".*?\"'
    pat_surrounded_dot = r'\s+\.[a-zA-Z_0-9]*?\.\s+'
    pat_not_dot = r'\.not\.'
    pat_number_dot = r'[+-]?[0-9]+\.[eE]?[+-]?[0-9]*'
    pat_exclamation = re.compile(r'\!.*\n')

    for line in lines_in:
        before = pat_type_member.search(line)
        if before:
            before_line = before.group()
            ignore_list = list()
            iterator_sq = re.finditer(pat_single_quotation,before_line)
            for match_sq in iterator_sq:
                ignore_list.append(match_sq.span())
            iterator_dq = re.finditer(pat_double_quotation,before_line)
            for match_dq in iterator_dq:
                ignore_list.append(match_dq.span())
            iterator_sd = re.finditer(pat_surrounded_dot,before_line)
            for match_sd in iterator_sd:
                ignore_list.append(match_sd.span())
            iterator_notd = re.finditer(pat_not_dot,before_line)
            for match_notd in iterator_notd:
                ignore_list.append(match_notd.span())
            iterator_numd = re.finditer(pat_number_dot,before_line)
            for match_numd in iterator_numd:
                ignore_list.append(match_numd.span())
            if pat_exclamation.search(before_line):
                match_ex = pat_exclamation.search(before_line)
                ignore_list.append(match_ex.span())
            end = (len(before_line),0)
            ignore_list.append(end)
            ctr = 0
            if len(ignore_list)>0:
                for ignore in sorted(ignore_list):
                    if ctr>ignore[0]:
                        pass
                    else:
                        before_slice = before_line[ctr:ignore[0]]
                        after_slice = before_slice.replace('.','%')
                        before_line = before_line.replace(before_slice,after_slice)
                        ctr = ignore[1]
            else:
                before_line = before_line.replace('.','%')
            line = before_line
        output.append(line)

    return output


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
    pat_pri = re.compile(r'^(.*)\s+!\{\{print\}\}')

    name = list()
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
            line += '-call kutimer__print\n'
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

    pat = re.compile(r'^(.*)\s+(.*)\s+([\+\-\*])=\s+(.*)$')
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
        lines = kutimer_docode(lines)
        lines = subsdiary_call_decode(lines)
        lines = block_comment(lines)
        lines = operator_decode(lines)
        lines = just_once_region(lines)
        lines = skip_counter(lines)
        lines = routine_name_macro(lines)
        lines = type_member_macro(lines)
        lines = alias_decode(lines)

        for l in lines:
            print(l,end='')




if __name__ == '__main__':

    if len(sys.argv)==1:
        filename_in = input('enter filename_in name > ')
    else:
        filename_in = sys.argv[1]

    efpp(filename_in)
