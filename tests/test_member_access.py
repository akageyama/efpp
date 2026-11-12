import unittest
from efpp import replace_period_in_member_accessor


class TestMemberAccess(unittest.TestCase):

    def test_simple_member(self):
        result = replace_period_in_member_accessor("a.b")
        self.assertEqual(result, "a%b")

    def test_nested_member(self):
        result = replace_period_in_member_accessor("a.b.c")
        self.assertEqual(result, "a%b%c")

    def test_real_number(self):
        result = replace_period_in_member_accessor("x = 3.14")
        self.assertEqual(result, "x = 3.14")

    def test_logical_operator(self):
        result = replace_period_in_member_accessor(
            "if (a .and. b) then"
        )
        self.assertEqual(result, "if (a .and. b) then")

    def test_logical_operator_without_spaces(self):
        result = replace_period_in_member_accessor(
            "if (a.and.b) then"
        )
        self.assertEqual(result, "if (a.and.b) then")

    def test_single_quoted_string(self):
        s = "print *, 'This is a.b'"
        self.assertEqual(
            replace_period_in_member_accessor(s), s
        )

    def test_escaped_quote(self):
        s = "print *, 'It''s a.b'"
        self.assertEqual(
            replace_period_in_member_accessor(s), s
        )

    def test_exponent_number(self):
        s = "x = 1.d-3 + 2.5e+10"
        self.assertEqual(
            replace_period_in_member_accessor(s), s
        )

    def test_user_defined_operator(self):
        s = "x = a .cross. b"
        self.assertEqual(
            replace_period_in_member_accessor(s), s
        )

    def test_inline_comment(self):
        s = "x.y = 1.0 ! a.b should not change"
        expected = "x%y = 1.0 ! a.b should not change"
        self.assertEqual(
            replace_period_in_member_accessor(s), expected
        )

    def test_exclamation_in_string(self):
        s = 'print *, "Hello! a.b"; x.y = 1'
        expected = 'print *, "Hello! a.b"; x%y = 1'
        self.assertEqual(
            replace_period_in_member_accessor(s), expected
        )

    def test_double_quoted_string(self):
        s = 'print *, "He said ""a.b"""'
        self.assertEqual(
            replace_period_in_member_accessor(s), s
        )

    def test_operator_declaration(self):
        s = "public :: operator(.grad.)"
        self.assertEqual(
            replace_period_in_member_accessor(s), s
        )

    def test_operator_interface(self):
        s = "interface operator(.curl.)"
        self.assertEqual(
            replace_period_in_member_accessor(s), s
        )

if __name__ == "__main__":
    unittest.main()
