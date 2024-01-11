import shelve
import threading
import uuid

from models.logger import LoggerService

logger = LoggerService(__name__)


class Condition:
    """ A condition that can be used to filter data in a query.
    """

    def __init__(self, field, operator, value):
        self.field = field
        self.operator = operator
        self.value = value


class Field:
    """ A field that can be used to build a query.
    """

    def __init__(self, field_name):
        """ Constructor for the Field class.
        """
        self.field_name = field_name

    def __eq__(self, value):
        """ Returns a Condition instance for the given field name and value.
        """
        return Condition(self.field_name, '==', value)

    def __getitem__(self, key):
        """ Returns a Condition instance for the given field name and key.
        """
        return Condition(f'{self.field_name}[{key}]', None, None)

    def fragment(self, value):
        """ Returns a Condition instance for the given field name , fragment
            and value.
        """
        return Condition(f'{self.field_name}', 'fragment', value)


class Query:
    """ A Query instance can be used to build a query."""

    def __getattr__(self, field):
        """ Returns a Field instance for the given field name."""
        return Field(field)

    def __getitem__(self, field_name):
        """ Returns a Field instance for the given field name."""
        return Field(field_name)

    def fragment(self, value):
        """ Returns a Condition instance for the given fragment and value."""
        return Condition('', 'fragment', value)


def where(field_name):
    """ A method that can be used to build a query."""
    return Query()[field_name]


class ShushaDB:
    """ A simple, lightweight, persistent, document-oriented database.
    """

    default_table_name = '_default'

    def __init__(self, filename="shusha.db"):
        self.filename = filename
        self._tables = {self.default_table_name: {}}
        self.current_table = self.default_table_name
        self.transaction_in_progress = False
        self.transaction_buffer = []
        self.lock = threading.Lock()  # Use a lock for transaction isolation

    def generate_doc_id(self):
        """ Generates a unique document ID."""
        return str(uuid.uuid4())

    # Transaction Management
    def begin_transaction(self, isolation_level='read_committed'):
        """ Begins a transaction with the given isolation level.
            Supported isolation levels:
            - read_uncommitted
            - read_committed
        """
        if self.transaction_in_progress:
            raise TransactionError("Nested transactions are not supported.")

        self.transaction_in_progress = True
        self.transaction_buffer = []

        if isolation_level == 'read_uncommitted':
            # No additional actions needed for read_uncommitted
            pass
        elif isolation_level == 'read_committed':
            # Acquire a lock for read_committed isolation level
            self.lock.acquire()
        else:
            raise ValueError(f"Unsupported isolation level: {isolation_level}")

    def commit_transaction(self):
        """ Commits the current transaction."""
        if self.transaction_in_progress:
            try:
                for operation, *args in self.transaction_buffer:
                    if operation == 'insert':
                        self._commit_insert(*args)
                    elif operation == 'update':
                        self._commit_update(*args)
                    elif operation == 'remove':
                        self._commit_remove(*args)
                self._commit_save()
            except Exception as e:
                raise TransactionError(f"Error committing transaction: {e}")
            finally:
                self._reset_transaction()

    def _reset_transaction(self):
        """ Resets the current transaction."""
        if self.transaction_in_progress:
            if self.transaction_buffer:
                # Release lock if it was acquired for read_committed isolation
                self.lock.release()
            self.transaction_in_progress = False
            self.transaction_buffer = []

    # Commit Methods
    def _commit_insert(self, document, key='gid'):
        """ Commits an insert operation."""
        doc_id = self.get_doc_gid(document, key)
        try:
            self._tables[self.current_table][doc_id] = document
            if not self.transaction_in_progress:
                self._commit_save()
            return doc_id
        except Exception as e:
            raise InsertionError(f"Error committing insert: {e}")

    def _commit_update(self, new_data, query):
        """ Commits an update operation."""
        try:
            for doc_id, document in self._tables[self.current_table].items():
                if self._evaluate_condition(document, query):
                    document.update(new_data)
            if not self.transaction_in_progress:
                self._commit_save()
        except Exception as e:
            raise UpdateError(f"Error committing update: {e}")

    def _commit_remove(self, query):
        """ Commits a remove operation."""
        try:
            doc_ids_to_remove = [
                doc_id for doc_id, document in self._tables[
                    self.current_table].items()
                if self._evaluate_condition(document, query)
            ]
            for doc_id in doc_ids_to_remove:
                del self._tables[self.current_table][doc_id]
            if not self.transaction_in_progress:
                self._commit_save()
        except Exception as e:
            raise RemovalError(f"Error committing remove: {e}")

    def _commit_save(self):
        """ Commits a save operation."""
        try:
            with shelve.open(self.filename, writeback=True) as db:
                db['tables'] = self._tables
        except Exception as e:
            raise RuntimeError(f"Error committing save: {e}")
        finally:
            if self.transaction_in_progress:
                # Release lock after saving changes for read_committed isolation
                self.lock.release()

    # Query and Condition Building
    def __getattr__(self, field):
        """ Returns a Field instance for the given field name."""
        return Field(field)

    def __getitem__(self, field_name):
        """ Returns a Field instance for the given field name."""
        return Field(field_name)

    @staticmethod
    def where(field_name):
        """ Returns a Query instance for the given field name."""
        return Query()[field_name]

    # Document Manipulation
    def get_doc_gid(self, document, key='gid'):
        """ Returns the document's id value if it exists, otherwise
            generates a new id value.
        """
        gid_value = document.get(key)
        if gid_value and gid_value in self._tables[self.current_table]:
            return self.generate_doc_id()
        else:
            return gid_value or self.generate_doc_id()

    def insert(self, document, key='gid'):
        """ Inserts a document into the database and returns its id."""
        doc_id = self.get_doc_gid(document, key)
        try:
            self._tables[self.current_table][doc_id] = document
            if not self.transaction_in_progress:
                self.save()
            return doc_id
        except Exception as e:
            print(f"Error inserting data: {e}")
            return None

    def insert_multiple(self, documents):
        """ Inserts multiple documents into the database
            and returns their ids.
        """
        doc_ids = []
        try:
            for document in documents:
                doc_id = self.insert(document)
                doc_ids.append(doc_id)
            return doc_ids
        except Exception as e:
            print(f"Error inserting multiple documents: {e}")
            return None

    def retrieve(self, doc_id):
        """ Retrieves a document from the database by its id."""
        try:
            return self._tables[self.current_table].get(doc_id, None)
        except Exception as e:
            print(f"Error retrieving data: {e}")
            return None

    def get(self, doc_id):
        """ Wrapper for the retrieve method."""
        return self.retrieve(doc_id)

    def contains(self, doc_id):
        """ Checks if a document with the given id exists in the database."""
        return doc_id in self._tables[self.current_table]

    def update(self, new_data, query):
        """ Updates documents in the database that match the given query."""
        try:
            for doc_id, document in self._tables[self.current_table].items():
                if self._evaluate_condition(document, query):
                    document.update(new_data)
            if not self.transaction_in_progress:
                self.save()
        except Exception as e:
            print(f"Error updating data: {e}")

    def remove(self, query):
        """ Removes documents from the database that match the given query."""
        try:
            doc_ids_to_remove = [
                doc_id for doc_id, document in self._tables[
                    self.current_table].items()
                if self._evaluate_condition(document, query)
            ]
            for doc_id in doc_ids_to_remove:
                del self._tables[self.current_table][doc_id]
            if not self.transaction_in_progress:
                self.save()
        except Exception as e:
            print(f"Error removing data: {e}")

    def all(self):
        """ Retrieves all documents from the database."""
        try:
            return list(self._tables[self.current_table].values())
        except Exception as e:
            print(f"Error retrieving all data: {e}")
            return []

    def __iter__(self):
        """ Returns an iterator for the current table."""
        return iter(self._tables[self.current_table].values())

    # Search and Query and Field Handling
    def search(self, condition):
        """ Searches the database for documents that match the given condition.
        """
        try:
            results = []
            for doc in self._tables[self.current_table].values():
                if self._evaluate_condition(doc, condition):
                    results.append(doc)
            return results
        except Exception as e:
            print(f"Error during search: {e}")
            return []

    def _evaluate_condition(self, document, condition):
        """ Evaluates a condition for a given document."""
        if not isinstance(condition, Condition):
            return False

        if condition.operator == 'fragment':
            return self._evaluate_fragment_condition(document, condition.value)
        else:
            field_value = self._get_nested_field_value(document,
                                                       condition.field)

            if condition.operator == '==':
                return field_value == condition.value
            elif condition.operator is None:
                return bool(field_value)
            else:
                print(f"Unsupported operator: {condition.operator}")
                return False

    def _evaluate_fragment_condition(self, document, fragment):
        """ Evaluates a fragment condition for a given document."""
        try:
            for key, value in fragment.items():
                if document.get(key) != value:
                    return False
            return True
        except Exception as e:
            print(f"Error evaluating fragment condition: {e}")
            return False

    def _get_nested_field_value(self, document, field_path):
        """ Returns the value of a nested field."""
        try:
            fields = field_path.split('.')
            value = document
            for field in fields:
                if '[' in field:
                    field, key = field.split('[')
                    key = key.rstrip(']')
                    value = value.get(field, {}).get(key)
                else:
                    value = value.get(field)
                if value is None:
                    break
            return value
        except Exception as e:
            print(f"Error getting nested field value: {e}")
            return None

    # Table Management
    def table(self, name):
        """ Returns a table instance for the given table name."""
        self.current_table = name
        if name not in self._tables:
            self._tables[name] = {}
            print(f"Table '{name}' not found.")
        return self

    def drop_table(self, name):
        """ Removes the table with the given name from the database."""
        try:
            del self._tables[name]
            if not self.transaction_in_progress:
                self.save()
        except Exception as e:
            print(f"Error dropping table: {e}")

    def drop_tables(self):
        """ Removes all tables from the database."""
        try:
            self._tables = {}
            if not self.transaction_in_progress:
                self.save()
        except Exception as e:
            print(f"Error dropping all tables: {e}")

    def tables(self):
        """ Returns a set of all table names in the database."""
        return set(self._tables.keys())

    # Persistence (File I/O)
    def save(self):
        """ Saves the database to a file."""
        try:
            with shelve.open(self.filename, writeback=True) as db:
                db['tables'] = self._tables
        except Exception as e:
            print(f"Error saving data: {e}")

    def load(self):
        """ Loads the database from a file."""
        try:
            with shelve.open(self.filename, writeback=True) as db:
                self._tables = db.get('tables', {})
        except Exception as e:
            print(f"Error loading data: {e}")


# Errors
class MySmallDBError(Exception):
    """Base class for exceptions in MySmallDB."""
    pass


class InsertionError(MySmallDBError):
    """Exception raised for errors related to data insertion."""


class UpdateError(MySmallDBError):
    """Exception raised for errors related to data updating."""


class RemovalError(MySmallDBError):
    """Exception raised for errors related to data removal."""


class TransactionError(MySmallDBError):
    """Exception raised for errors related to transactions."""


class TableManagementError(MySmallDBError):
    """Base class for table management errors."""
    pass


class TableNotFoundError(TableManagementError):
    """Exception raised when attempting operations on a non-existent table."""
    pass


class PersistenceError(MySmallDBError):
    """Base class for file I/O errors."""
    pass


class SaveError(PersistenceError):
    """Exception raised for errors during data save."""
    pass


class LoadError(PersistenceError):
    """Exception raised for errors during data load."""
    pass


class DropTableError(TableManagementError):
    """Exception raised for errors during table dropping."""
    pass


class DropAllTablesError(TableManagementError):
    """Exception raised for errors during dropping all tables."""
    pass
