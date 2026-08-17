import unittest

from shusha.models.database import Condition, Field, Query


class TestQuerySyntax(unittest.TestCase):
    def test_query_field(self):
        query = Query()
        field = query.foo
        self.assertIsInstance(field, Field)
        self.assertEqual(field.field_name, "foo")

    def test_condition_properties(self):
        condition = Condition("field", "==", "value")
        self.assertEqual(condition.field, "field")
        self.assertEqual(condition.operator, "==")
        self.assertEqual(condition.value, "value")

    def test_condition_logical_operations(self):
        c1 = Condition("type", "==", "A")
        c2 = Condition("value", ">", 15)
        c_and = c1 & c2
        self.assertEqual(c_and.operator, "AND")
        c_or = c1 | c2
        self.assertEqual(c_or.operator, "OR")


if __name__ == "__main__":
    unittest.main()
