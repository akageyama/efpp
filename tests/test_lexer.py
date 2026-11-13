import unittest
from efpp import mask_strings_and_comments


class TestLexer(unittest.TestCase):

    def test_plain_code(self):
        s = "a.b += c\n"
        masked, pos = mask_strings_and_comments(s)
        self.assertEqual(masked, s)
        self.assertEqual(pos, len(s))

    def test_single_quoted_string(self):
        s = "print *, 'a.b'\n"
        masked, pos = mask_strings_and_comments(s)
        self.assertEqual(masked, "print *,      \n")
        self.assertEqual(pos, len(s))

    def test_inline_comment(self):
        s = "a.b = 1 ! comment.a\n"
        masked, pos = mask_strings_and_comments(s)
        self.assertEqual(masked[:pos], "a.b = 1 ")
        self.assertEqual(masked[pos:], " " * (len(s) - pos))
        self.assertEqual(pos, s.index("!"))

    def test_exclamation_in_string(self):
        s = 'print *, "Hello!"; a.b = 1\n'
        masked, pos = mask_strings_and_comments(s)
        self.assertEqual(pos, len(s))
        self.assertIn("a.b = 1", masked)

    def test_length_preserved(self):
        samples = [
            "a.b\n",
            "print *, 'a.b'\n",
            'print *, "Hello!" ! comment\n',
            "x += y ! update\n",
        ]
        for s in samples:
            masked, _ = mask_strings_and_comments(s)
            self.assertEqual(len(masked), len(s))


if __name__ == "__main__":
    unittest.main()
