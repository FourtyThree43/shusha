import unittest

from shusha.models.ShushaDB import Query, ShushaDB


class TestShushaDB(unittest.TestCase):

    def setUp(self):
        # Initialize ShushaDB instance with a test filename
        self.db = ShushaDB(filename="test_database")

    def tearDown(self):
        # Remove the test database file after each test
        import os

        file_extensions = ['.bak', '.dat', '.dir']
        for file_extension in file_extensions:
            filename = f"test_database{file_extension}"
            if os.path.exists(filename):
                os.remove(filename)

        # if os.path.exists("test_database"):
        #     os.remove("test_database")

    def test_insert_and_retrieve(self):
        # Test insert and retrieve operations
        with self.db:
            document = {'gid': 'test_id', 'foo': 'bar'}
            doc_id = self.db.insert(document)
            retrieved_document = self.db.retrieve(doc_id)
            self.assertEqual(retrieved_document, document)

    def test_insert_multiple_and_all(self):
        # Test insert_multiple and all operations
        documents = [{
            'gid': 'id1',
            'foo': 'bar'
        }, {
            'gid': 'id2',
            'foo': 'baz'
        }, {
            'gid': 'id3',
            'foo': 'qux'
        }]
        with self.db:
            doc_ids = self.db.insert_multiple(documents)
            retrieved_documents = self.db.all()
            self.assertEqual(len(retrieved_documents), len(documents))
            for doc_id, document in zip(doc_ids, documents):
                self.assertIn(document, retrieved_documents)

    def test_update(self):
        # Test update operation
        original_document = {'gid': 'test_id', 'foo': 'bar'}
        updated_data = {'foo': 'baz'}
        updated_document = {'gid': 'test_id', 'foo': 'baz'}
        with self.db:
            self.db.insert(original_document)
            self.db.update(updated_data, self.db.where('gid') == 'test_id')
            retrieved_document = self.db.retrieve('test_id')
            self.assertEqual(retrieved_document, updated_document)

    def test_remove(self):
        # Test remove operation
        document = {'gid': 'test_id', 'foo': 'bar'}
        with self.db:
            self.db.insert(document)
            self.assertTrue(self.db.contains('test_id'))
            self.db.remove(self.db.where('gid') == 'test_id')
            self.assertFalse(self.db.contains('test_id'))

    def test_search(self):
        # Test search operation
        documents = [{
            'gid': 'id1',
            'foo': 'bar',
            'type': 'A'
        }, {
            'gid': 'id2',
            'foo': 'baz',
            'type': 'B'
        }, {
            'gid': 'id3',
            'foo': 'qux',
            'type': 'A'
        }]
        with self.db:
            self.db.insert_multiple(documents)
            condition = self.db.where('type') == 'A'
            search_results = self.db.search(condition)
            expected_results = [documents[0], documents[2]]
            self.assertEqual(search_results, expected_results)

    def test_table_management(self):
        # Test table creation, switching, and dropping
        with self.db:
            self.assertEqual(self.db.tables(), {ShushaDB.default_table_name})
            new_table_name = 'test_table'
            self.db.table(new_table_name)
            self.assertEqual(self.db.tables(),
                             {ShushaDB.default_table_name, new_table_name})
            self.db.drop_table(new_table_name)
            self.assertEqual(self.db.tables(), {ShushaDB.default_table_name})

    def test_save_and_load(self):
        # Test save and load operations
        document = {'gid': 'test_id', 'foo': 'bar'}
        self.db.insert(document)
        self.db.save()
        new_db_instance = ShushaDB("test_database")
        new_db_instance.load()
        retrieved_document = new_db_instance.retrieve('test_id')
        self.assertEqual(retrieved_document, document)

    def test_complex_query(self):
        # Test a complex query with multiple conditions
        with self.db:
            documents = [{
                'gid': 'id1',
                'foo': 'bar',
                'type': 'A',
                'value': 10
            }, {
                'gid': 'id2',
                'foo': 'baz',
                'type': 'B',
                'value': 20
            }, {
                'gid': 'id3',
                'foo': 'qux',
                'type': 'A',
                'value': 30
            }]
            self.db.insert_multiple(documents)

            # Query for documents where 'type' is 'A' and 'value' is greater than 15
            condition = (self.db.where('type')
                         == 'A') & (self.db.where('value') > 15)
            search_results = self.db.search(condition)
            expected_results = [documents[2]]
            self.assertEqual(search_results, expected_results)

    def test_field_eq_condition(self):
        # Test the equality condition generated by the Field class
        with self.db:
            document = {'gid': 'test_id', 'foo': 'bar'}
            self.db.insert(document)

            # Query for documents where 'gid' is equal to 'test_id'
            condition = self.db.where('gid') == 'test_id'
            search_results = self.db.search(condition)
            expected_results = [document]
            self.assertEqual(search_results, expected_results)

    def test_field_fragment_condition(self):
        # Test the fragment condition generated by the Field class
        with self.db:
            document = {'gid': 'test_id', 'nested': {'field': 'value'}}
            self.db.insert(document)

            # Query for documents where 'nested' field is equal to {'field': 'value'}
            condition1 = self.db.where('nested').fragment({'field': 'value'})
            condition2 = Query().fragment({'field': 'value'})

            search_results = self.db.search(condition1)
            search_results_2 = self.db.search(condition2)
            expected_results = [document]

            self.assertEqual(search_results, search_results_2)
            self.assertEqual(search_results, expected_results)
            self.assertEqual(search_results_2, expected_results)


if __name__ == '__main__':
    unittest.main()
