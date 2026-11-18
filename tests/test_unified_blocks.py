import unittest
from efpp import special_block_decode


class TestUnifiedBlocks(unittest.TestCase):
    def test_crossed_legacy_skip_rejected(self):
        source = [
            'do <just_once>\n',
            '  ===<skip counter:8>===\n',
            '    call output()\n',
            'end do\n',
            '  ===</skip counter>===\n',
        ]
        with self.assertRaises(ValueError):
            special_block_decode(source)

    def test_reverse_nesting(self):
        source = [
            'if <skip counter:8>\n',
            '  do <just_once>\n',
            '    call initialize()\n',
            '  end do\n',
            'end if\n',
        ]
        expected = [
            'if(mod(counter,8)==0) then\n',
            '  if (just_once) then\n',
            '    call initialize()\n',
            '  just_once = .false. ; end if\n',
            'end if; counter = counter + 1\n',
        ]
        self.assertEqual(special_block_decode(source), expected)

    def test_legacy_output_unchanged(self):
        source = [
            '  ==<just_once>==\n',
            '  ==</just_once>==\n',
            '  ===<skip ctr:8>===\n',
            '  ===</skip ctr>===\n',
        ]
        expected = [
            '  if (just_once) then \n',
            '  just_once = .false. ; end if \n',
            '  if(mod(ctr,8)==0) then\n',
            '  end if; ctr = ctr + 1 \n',
        ]
        self.assertEqual(special_block_decode(source), expected)

    def test_unclosed_skip_rejected(self):
        with self.assertRaises(ValueError):
            special_block_decode(['if <skip ctr:8>\n', '  call output()\n'])

    def test_ordinary_do_contains_once(self):
        source = [
            'do i = 1, 10\n',
            '  do <just_once>\n',
            '    call initialize()\n',
            '  end do\n',
            'end do\n',
        ]
        expected = [
            'do i = 1, 10\n',
            '  if (just_once) then\n',
            '    call initialize()\n',
            '  just_once = .false. ; end if\n',
            'end do\n',
        ]
        self.assertEqual(special_block_decode(source), expected)

    def test_ordinary_do_inside_once(self):
        source = [
            'do <just_once>\n',
            '  do i = 1, 3\n',
            '    call initialize()\n',
            '  end do\n',
            'end do\n',
        ]
        expected = [
            'if (just_once) then\n',
            '  do i = 1, 3\n',
            '    call initialize()\n',
            '  end do\n',
            'just_once = .false. ; end if\n',
        ]
        self.assertEqual(special_block_decode(source), expected)

    def test_old_if_style_rejected(self):
        with self.assertRaisesRegex(ValueError, 'use do <just_once>'):
            special_block_decode(['if <just_once>\n', 'end if\n'])

    def test_crossed_if_do_rejected(self):
        with self.assertRaises(ValueError):
            special_block_decode(['do <just_once>\n', 'if (x) then\n',
                                  'end do\n', 'end if\n'])

    def test_nested_just_once_rejected(self):
        with self.assertRaises(ValueError):
            special_block_decode(['do <just_once>\n', 'do <just_once>\n',
                                  'end do\n', 'end do\n'])

    def test_inline_comment_preserved(self):
        source = ['do <just_once> ! only once\n', '  call init()\n',
                  'end do ! done\n']
        expected = ['if (just_once) then ! only once\n',
                    '  call init()\n',
                    'just_once = .false. ; end if ! done\n']
        self.assertEqual(special_block_decode(source), expected)

    def test_multiline_if_inside_do(self):
        source = [
            'do k = 1, 3\n',
            '  if (a > 0 .or. &\n',
            '      b > 0) then\n',
            '    call update()\n',
            '  end if\n',
            'end do\n',
        ]
        self.assertEqual(special_block_decode(source), source)

    def test_multiline_if_inside_just_once(self):
        source = [
            'do <just_once>\n',
            '  if (a > 0 .or. & ! continuation\n',
            '      & b > 0) then\n',
            '    call update()\n',
            '  end if\n',
            'end do\n',
        ]
        result = special_block_decode(source)
        self.assertEqual(result[0], 'if (just_once) then\n')
        self.assertEqual(result[-1], 'just_once = .false. ; end if\n')
        self.assertEqual(result[1:-1], source[1:-1])

    def test_unclosed_do_once_rejected(self):
        with self.assertRaises(ValueError):
            special_block_decode(['do <just_once>\n', '  call init()\n'])


if __name__ == '__main__':
    unittest.main()
