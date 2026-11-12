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

if __name__ == "__main__":
    unittest.main()
