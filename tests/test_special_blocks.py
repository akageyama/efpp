import unittest
from efpp import special_block_decode, just_once_region, skip_counter


class TestJustOnce(unittest.TestCase):
    def test_legacy_syntax(self):
        self.assertEqual(just_once_region(['  ==<just_once>==\n', '  ==</just_once>==\n']),
                         ['  if (just_once) then \n', '  just_once = .false. ; end if \n'])

    def test_new_syntax(self):
        self.assertEqual(just_once_region(['  do <just_once>\n', '    call initialize()\n', '  end do\n']),
                         ['  if (just_once) then\n', '    call initialize()\n',
                          '  just_once = .false. ; end if\n'])

    def test_nested_ordinary_if(self):
        src = ['do <just_once>\n', '  if (energy > 0.0) then\n', '    call initialize()\n',
               '  end if\n', 'end do\n']
        expected = ['if (just_once) then\n', '  if (energy > 0.0) then\n',
                    '    call initialize()\n', '  end if\n',
                    'just_once = .false. ; end if\n']
        self.assertEqual(just_once_region(src), expected)

    def test_just_once_inside_ordinary_if(self):
        src = ['if (DEBUG_MODE) then\n', '  do <just_once>\n',
               '    call initialize()\n', '  end do\n', 'end if\n']
        expected = ['if (DEBUG_MODE) then\n', '  if (just_once) then\n',
                    '    call initialize()\n', '  just_once = .false. ; end if\n', 'end if\n']
        self.assertEqual(just_once_region(src), expected)

    def test_new_syntax_with_comments(self):
        src = ['do <just_once>  ! initialize only once\n', '  call initialize()\n',
               'end do         ! end initialization\n']
        expected = ['if (just_once) then  ! initialize only once\n', '  call initialize()\n',
                    'just_once = .false. ; end if         ! end initialization\n']
        self.assertEqual(just_once_region(src), expected)

    def test_nested_just_once_rejected(self):
        with self.assertRaises(ValueError):
            just_once_region(['do <just_once>\n', '  do <just_once>\n',
                              '  end do\n', 'end do\n'])

    def test_unclosed_just_once_rejected(self):
        with self.assertRaises(ValueError):
            just_once_region(['do <just_once>\n', '  call initialize()\n'])

    def test_unclosed_just_once_with_nested_if(self):
        with self.assertRaises(ValueError):
            just_once_region(['do <just_once>\n', '  if (DEBUG_MODE) then\n',
                              '    call initialize()\n', 'end if\n'])

    def test_legacy_and_new_syntax_together(self):
        src = ['  ==<just_once>==\n', '    call initialize_a()\n',
               '  ==</just_once>==\n', '  do <just_once>\n',
               '    call initialize_b()\n', '  end do\n']
        expected = ['  if (just_once) then \n', '    call initialize_a()\n',
                    '  just_once = .false. ; end if \n', '  if (just_once) then\n',
                    '    call initialize_b()\n', '  just_once = .false. ; end if\n']
        self.assertEqual(just_once_region(src), expected)

    def test_legacy_inside_new_rejected(self):
        with self.assertRaises(ValueError):
            just_once_region(['do <just_once>\n', '  ==<just_once>==\n',
                              '  ==</just_once>==\n', 'end do\n'])

    def test_old_if_syntax_rejected(self):
        with self.assertRaisesRegex(ValueError, 'use do <just_once>'):
            special_block_decode(['if <just_once>\n', 'end if\n'])


class TestSkip(unittest.TestCase):
    def test_legacy_skip(self):
        src = ['  ===<skip counter:8>===\n', '    call output()\n',
               '  ===</skip counter>===\n']
        expected = ['  if(mod(counter,8)==0) then\n', '    call output()\n',
                    '  end if; counter = counter + 1 \n']
        self.assertEqual(skip_counter(src), expected)

    def test_old_if_skip_rejected(self):
        with self.assertRaisesRegex(ValueError, 'use do <every'):
            skip_counter(['if <skip counter:8>\n', 'end if\n'])

    def test_new_every(self):
        src = ['  do <every counter:8>\n', '    call output()\n', '  end do\n']
        expected = ['  if(mod(counter,8)==0) then\n', '    call output()\n',
                    '  end if; counter = counter + 1\n']
        self.assertEqual(skip_counter(src), expected)


class TestCombinedBlocks(unittest.TestCase):
    def test_just_once_containing_every(self):
        src = ['do <just_once>\n', '  do <every counter:8>\n',
               '    call output()\n', '  end do\n', 'end do\n']
        expected = ['if (just_once) then\n', '  if(mod(counter,8)==0) then\n',
                    '    call output()\n', '  end if; counter = counter + 1\n',
                    'just_once = .false. ; end if\n']
        self.assertEqual(special_block_decode(src), expected)

    def test_every_containing_just_once(self):
        src = ['do <every counter:8>\n', '  do <just_once>\n',
               '    call initialize()\n', '  end do\n', 'end do\n']
        expected = ['if(mod(counter,8)==0) then\n', '  if (just_once) then\n',
                    '    call initialize()\n', '  just_once = .false. ; end if\n',
                    'end if; counter = counter + 1\n']
        self.assertEqual(special_block_decode(src), expected)

    def test_complex_nested_blocks(self):
        src = ['do <just_once>\n', '  if (DEBUG_MODE) then\n',
               '    do <every counter:8>\n', '      call output()\n',
               '    end do\n', '  end if\n', 'end do\n']
        expected = ['if (just_once) then\n', '  if (DEBUG_MODE) then\n',
                    '    if(mod(counter,8)==0) then\n', '      call output()\n',
                    '    end if; counter = counter + 1\n', '  end if\n',
                    'just_once = .false. ; end if\n']
        self.assertEqual(special_block_decode(src), expected)

    def test_crossed_blocks_rejected(self):
        src = ['do <just_once>\n', '  ===<skip counter:8>===\n',
               '    call output()\n', 'end do\n', '  ===</skip counter>===\n']
        with self.assertRaises(ValueError):
            special_block_decode(src)


if __name__ == '__main__':
    unittest.main()
