import unittest
from efpp import operator_decode


class TestOperator(unittest.TestCase):

    def test_add_assignment(self):
        result = operator_decode(["  x += y\n"])
        self.assertEqual(result, ["  x = x + y\n"])

    def test_sub_assignment(self):
        result = operator_decode(["  x -= y\n"])
        self.assertEqual(result, ["  x = x - y\n"])

    def test_mul_assignment(self):
        result = operator_decode(["  x *= y\n"])
        self.assertEqual(result, ["  x = x * y\n"])

    def test_assignment_without_indent(self):
        result = operator_decode(["x += y\n"])
        self.assertEqual(result, ["x = x + y\n"])

    def test_comment_unchanged(self):
        s = "! a += b ==> a += b\n"
        self.assertEqual(operator_decode([s]), [s])

    def test_array_assignment(self):
        result = operator_decode(["  a(i) += b\n"])
        self.assertEqual(result, ["  a(i) = a(i) + b\n"])

    def test_string_unchanged(self):
        s = '  print *, "x += y"\n'
        self.assertEqual(operator_decode([s]), [s])

    def test_conditional_assignment(self):
        result = operator_decode(["  if (x > 0) x += 1\n"])
        self.assertEqual(
            result,
            ["  if (x > 0) x = x + 1\n"]
        )

    def test_nested_conditional_assignment(self):
        result = operator_decode([
            "  if (abs(x) > 1.0) a(i) += b\n"
        ])
        self.assertEqual(
            result,
            ["  if (abs(x) > 1.0) a(i) = a(i) + b\n"]
        )

    def test_array_assignment_with_spaces(self):
        result = operator_decode([
            "  grid.field( i, j ) += dt * rhs(i,j)\n"
        ])
        self.assertEqual(
            result,
            [
                "  grid.field( i, j ) = "
                "grid.field( i, j ) + dt * rhs(i,j)\n"
            ]
        )

    def test_assignment_with_comment(self):
        result = operator_decode([
            "  x += y  ! update x\n"
        ])
        self.assertEqual(
            result,
            ["  x = x + y  ! update x\n"]
        )

    def test_assignment_with_string_rhs(self):
        result = operator_decode([
            '  x += len("a+b")\n'
        ])
        self.assertEqual(
            result,
            ['  x = x + len("a+b")\n']
        )

    def test_semicolon_separated_statements(self):
        result = operator_decode([
            "  x = 1; y += 2\n"
        ])
        self.assertEqual(
            result,
            ["  x = 1; y = y + 2\n"]
        )

    def test_multiple_compound_assignments(self):
        result = operator_decode([
            "  x += 1; y += 2\n"
        ])
        self.assertEqual(
            result,
            ["  x = x + 1; y = y + 2\n"]
        )

    def test_spaces_before_semicolon(self):
        result = operator_decode([
            "  x += y       ; call update()\n"
        ])
        self.assertEqual(
            result,
            ["  x = x + y       ; call update()\n"]
        )

    def test_semicolon_in_string(self):
        result = operator_decode([
            '  x += len("a;b")\n'
        ])
        self.assertEqual(
            result,
            ['  x = x + len("a;b")\n']
        )

    def test_no_final_newline(self):
        result = operator_decode([
            "  x += y"
        ])
        self.assertEqual(
            result,
            ["  x = x + y"]
        )

    def test_windows_line_ending(self):
        result = operator_decode([
            "  x += y\r\n"
        ])
        self.assertEqual(
            result,
            ["  x = x + y\r\n"]
        )

if __name__ == "__main__":
    unittest.main()
