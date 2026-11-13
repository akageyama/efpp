import unittest
import importlib.util
from pathlib import Path

# When copied into efpp/tests/, import the local efpp.py.
from efpp import special_block_decode


class TestUnifiedBlocks(unittest.TestCase):
    def test_crossed_legacy_skip_rejected(self):
        source = [
            'if <just_once>\n',
            '  ===<skip counter:8>===\n',
            '    call output()\n',
            'end if\n',
            '  ===</skip counter>===\n',
        ]
        with self.assertRaises(ValueError):
            special_block_decode(source)

    def test_reverse_nesting(self):
        source = [
            'if <skip counter:8>\n',
            '  if <just_once>\n',
            '    call initialize()\n',
            '  end if\n',
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

if __name__ == '__main__':
    unittest.main()
