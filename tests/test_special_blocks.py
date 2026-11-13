import unittest
from efpp import just_once_region


class TestJustOnce(unittest.TestCase):

    def test_legacy_syntax(self):
        source = [
            "  ==<just_once>==\n",
            "    call initialize()\n",
            "  ==</just_once>==\n",
        ]
        expected = [
            "  if (just_once) then \n",
            "    call initialize()\n",
            "  just_once = .false. ; end if \n",
        ]
        self.assertEqual(just_once_region(source), expected)

    def test_new_syntax(self):
        source = [
            "  if <just_once>\n",
            "    call initialize()\n",
            "  end if\n",
        ]
        expected = [
            "  if (just_once) then\n",
            "    call initialize()\n",
            "  just_once = .false. ; end if\n",
        ]
        self.assertEqual(just_once_region(source), expected)

    def test_nested_ordinary_if(self):
        source = [
            "if <just_once>\n",
            "  if (energy > 0.0) then\n",
            "    call initialize()\n",
            "  end if\n",
            "end if\n",
        ]
        expected = [
            "if (just_once) then\n",
            "  if (energy > 0.0) then\n",
            "    call initialize()\n",
            "  end if\n",
            "just_once = .false. ; end if\n",
        ]
        self.assertEqual(just_once_region(source), expected)

    def test_just_once_inside_ordinary_if(self):
        source = [
            "if (DEBUG_MODE) then\n",
            "  if <just_once>\n",
            "    call initialize()\n",
            "  end if\n",
            "end if\n",
        ]
        expected = [
            "if (DEBUG_MODE) then\n",
            "  if (just_once) then\n",
            "    call initialize()\n",
            "  just_once = .false. ; end if\n",
            "end if\n",
        ]
        self.assertEqual(just_once_region(source), expected)

    def test_new_syntax_with_comments(self):
        source = [
            "if <just_once>  ! initialize only once\n",
            "  call initialize()\n",
            "end if         ! end initialization\n",
        ]
        expected = [
            "if (just_once) then  ! initialize only once\n",
            "  call initialize()\n",
            "just_once = .false. ; end if         ! end initialization\n",
        ]
        self.assertEqual(just_once_region(source), expected)

    def test_nested_just_once_rejected(self):
        source = [
            "if <just_once>\n",
            "  call initialize_a()\n",
            "  if <just_once>\n",
            "    call initialize_b()\n",
            "  end if\n",
            "end if\n",
        ]

        with self.assertRaises(ValueError):
            just_once_region(source)

    def test_unclosed_just_once_rejected(self):
        source = [
            "if <just_once>\n",
            "  call initialize()\n",
        ]

        with self.assertRaises(ValueError):
            just_once_region(source)

    def test_unclosed_just_once_with_nested_if(self):
        source = [
            "if <just_once>\n",
            "  if (DEBUG_MODE) then\n",
            "    call initialize()\n",
            "end if\n",
        ]

        with self.assertRaises(ValueError):
            just_once_region(source)

    def test_legacy_and_new_syntax_together(self):
        source = [
            "  ==<just_once>==\n",
            "    call initialize_a()\n",
            "  ==</just_once>==\n",
            "  if <just_once>\n",
            "    call initialize_b()\n",
            "  end if\n",
        ]

        expected = [
            "  if (just_once) then \n",
            "    call initialize_a()\n",
            "  just_once = .false. ; end if \n",
            "  if (just_once) then\n",
            "    call initialize_b()\n",
            "  just_once = .false. ; end if\n",
        ]

        self.assertEqual(just_once_region(source), expected)

    def test_legacy_inside_new_rejected(self):
        source = [
            "if <just_once>\n",
            "  ==<just_once>==\n",
            "    call initialize()\n",
            "  ==</just_once>==\n",
            "end if\n",
        ]

        with self.assertRaises(ValueError):
            just_once_region(source)

if __name__ == "__main__":
    unittest.main()
