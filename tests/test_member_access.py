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

    @unittest.expectedFailure
    def test_logical_operator_without_spaces(self):
        result = replace_period_in_member_accessor(
            "if (a.and.b) then"
        )
        self.assertEqual(result, "if (a.and.b) then")

if __name__ == "__main__":
    unittest.main()
