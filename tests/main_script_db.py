# main_script.py
from shusha.models.ShushaDB import Condition, Field, Query, ShushaDB, where

# Sample data
# sp = {}
sample_data = {'gid': '551de12efd12', 'foo': 'bar'}

sample_data_list = [
    {
        'gid': '451de12efd12',
        'foo': 'bar'
    },
    {
        'gid': '651de12efd12',
        'foo': 'bar'
    },
    {
        'gid': '751de12efd13',
        'foo': 'baz'
    },
    # Add more documents as needed
]

# Create an instance of MySmallDB with a specified filename
db = ShushaDB("0-test_file_storage_db")

# Insert sample data
# doc_id = db.insert(sample_data)

# # Print the original data
# odata = db.retrieve(doc_id)
# print(f"Original data for document ID {doc_id}:\n{odata}")

# Define a query to select documents with a specific 'gid'
# query = db.where('gid') == '551de12efd12'

# Define new data to update
# update_data = {'foo': 'baz'}

# # Update documents matching the query with the new data
# db.update(update_data, query)

# Print the updated data
# print(f"Updated data for document ID {doc_id}:\n{db.retrieve(doc_id)}")

# Mutiple inserts
# Insert multiple documents
# doc_ids = db.insert_multiple(sample_data_list)

# Print the inserted document IDs
# print(f"Inserted document IDs: {doc_ids}")

# # Retrieve and print the inserted documents
# for doc_id in doc_ids:
#     print(f"Retrieved data for document ID {doc_id}:\n{db.retrieve(doc_id)}")

# db.load()

# print("All:\n", db.all())

# query1 = db.where("gid") == '551de12efd12'
# updates1: dict = {"user": {"name": "Alice", "birthday": {"year": 1985}}}

# db.update(new_data=updates1, query=query1)

# print("After update:\n", db.all())

# db.remove(where("gid") == '551de12efd12')

# print("After remove:\n", db.all())


# ################################ tests ######################################
def test_query():
    query = Query()
    field = query.foo
    assert isinstance(field, Field)
    assert field == Condition('foo', '==', None)
    assert field == 'bar'


def test_condition():
    condition = Condition('field', '==', 'value')
    assert condition.field == 'field'
    assert condition.operator == '=='
    assert condition.value == 'value'


def test_complex_query():
    # Test a complex query with multiple conditions
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
    db.insert_multiple(documents)

    # Query for documents where 'type' is 'A' and 'value' is greater than 15
    condition = (db.where('type') == 'A') & (db.where('value') > 15) | (
        db.where('foo') == "qux")
    search_results = db.search(condition)
    # print(search_results)
    expected_results = [documents[2]]
    # print(expected_results)
    assert search_results == expected_results


def test_field_fragment_condition():
    # Print the document before insertion
    document = {'gid': 'test_id', 'nested': {'field': 'value'}}

    # Insert the document into the database
    db.insert(document)

    # Query for documents where 'nested' field is equal to {'field': 'value'}
    complex_condition = Query().fragment({'field': 'value'})
    complex_condition_v2 = db.where('nested').fragment({'field': 'value'})

    complex_results = db.search(complex_condition)
    complex_results_v2 = db.search(complex_condition_v2)

    expected_results_cx = [document]

    assert complex_results == expected_results_cx
    assert complex_results_v2 == expected_results_cx


# Run the tests
test_query()
test_condition()
# test_complex_query()
test_field_fragment_condition()
