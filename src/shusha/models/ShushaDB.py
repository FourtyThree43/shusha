from __future__ import annotations

import shelve
import threading
import uuid
from typing import Any, Dict, List, Optional, Union

from models.logger import LoggerService
from models.utilities import data_dir

logger = LoggerService(__name__)
DEFAULT_DB_DIR = data_dir(appname="shusha")
DEFAULT_DB_FILENAME = "shusha.db"
DEFAULT_DB_PATH = DEFAULT_DB_DIR / DEFAULT_DB_FILENAME


class Condition:
    """ A class for building query conditions to filter data in a query. """

    def __init__(self, field_name: str, operator: Optional[str], value: Any):
        """
        Initialize a Condition instance.

        Args:
            field_name: The name of the field to query.
            operator: The operator to use for the query.
            value: The value to compare against.
        """
        self.field = field_name
        self.operator = operator
        self.value = value

    def __or__(self, other):
        """
        Combine two conditions using logical OR.

        Args:
            other: The other condition to combine with.

        Returns:
            A new Condition instance.
        """
        if isinstance(other, Condition):
            return Condition('', 'OR', (self, other))
        else:
            raise TypeError(
                f"Unsupported operand type(s) for |: {type(self)} and {type(other)}"
            )

    def __and__(self, other):
        """
        Combine two conditions using logical AND.

        Args:
            other: The other condition to combine with.

        Returns:
            A new Condition instance.
        """
        if isinstance(other, Condition):
            return Condition('', 'AND', (self, other))
        else:
            raise TypeError(
                f"Unsupported operand type(s) for &: {type(self)} and {type(other)}"
            )

    def __invert__(self):
        """
        Negate the current condition.

        Returns:
            A new Condition instance.
        """
        return Condition('', 'NOT', self)


class Field:
    """ A class for building query fields. """

    def __init__(self, field_name: str):
        """
        Initialize a Field instance.

        Args:
            field_name (str): The name of the field to query.
        """
        self.field_name = field_name

    def __eq__(self, value: Any):
        """
        Build an equality condition.

        Args:
            value (Any): The value to compare against.

        Returns:
            A new Condition instance.
        """
        return Condition(self.field_name, '==', value)

    def __ne__(self, value: Any):
        """
        Build a non-equality condition.

        Args:
            value (Any): The value to compare against.

        Returns:
            A new Condition instance.
        """
        return Condition(self.field_name, '!=', value)

    def __gt__(self, value: Any):
        """
        Build a greater-than condition.

        Args:
            value (Any): The value to compare against.

        Returns:
            A new Condition instance.
        """
        return Condition(self.field_name, '>', value)

    def __ge__(self, value: Any):
        """
        Build a greater-than-or-equal condition.

        Args:
            value (Any): The value to compare against.

        Returns:
            A new Condition instance.
        """
        return Condition(self.field_name, '>=', value)

    def __lt__(self, value: Any):
        """
        Build a less-than condition.

        Args:
            value (Any): The value to compare against.

        Returns:
            A new Condition instance.
        """
        return Condition(self.field_name, '<', value)

    def __le__(self, value: Any):
        """
        Build a less-than-or-equal condition.

        Args:
            value (Any): The value to compare against.

        Returns:
            A new Condition instance.
        """
        return Condition(self.field_name, '<=', value)

    def __and__(self, other: Condition):
        """
        Build a condition using logical AND.

        Args:
            other: The other condition to combine with.

        Returns:
            A new Condition instance.
        """
        if isinstance(other, Field):
            # Combine two fields using logical AND (intersection)
            return Field(f'{self.field_name} AND {other.field_name}')
        elif isinstance(other, Condition):
            # Combine field and condition using logical AND
            return Condition('', 'AND', (self, other))
        else:
            raise TypeError(
                f"Unsupported operand type(s) for &: {type(self)} and {type(other)}"
            )

    def __or__(self, other: Condition):
        """
        Build a condition using logical OR.

        Args:
            other: The other condition to combine with.

        Returns:
            A new Condition instance.
        """
        if isinstance(other, Field):
            # Combine two fields using logical OR (union)
            return Field(f'{self.field_name} OR {other.field_name}')
        elif isinstance(other, Condition):
            # Combine field and condition using logical OR
            return Condition('', 'OR', (self, other))
        else:
            raise TypeError(
                f"Unsupported operand type(s) for |: {type(self)} and {type(other)}"
            )

    def __getitem__(self, key: str) -> Condition:
        """
        Build a condition for a nested field.

        Args:
            key (str): The name of the nested field.

        Returns:
            A new Condition instance.
        """
        return Condition(f'{self.field_name}[{key}]', None, None)

    def fragment(self, value: Dict[str, Any]) -> Condition:
        """
        Build a fragment condition.

        Args:
            value (Dict[str, Any]): The value to compare against.

        Returns:
            A new Condition instance.
        """
        return Condition(f'{self.field_name}', 'fragment', value)


class Query:
    """ A class for building queries. """

    def __getattr__(self, field_name: str) -> Field:
        """
        Get attribute for building a query field.

        Args:
            field_name (str): The name of the field to query.

        Returns:
            A new Field instance.
        """
        return Field(field_name)

    def __getitem__(self, field_name: str) -> Field:
        """
        Get item for building a query field.

        Args:
            field_name (str): The name of the field to query.

        Returns:
            A new Field instance.
        """
        return Field(field_name)

    def fragment(self, value: Dict[str, Any]) -> Condition:
        """
        Build a fragment condition.

        Args:
            value (Dict[str, Any]): The value to compare against.

        Returns:
            A new Condition instance.
        """
        return Condition('', 'fragment', value)

    def __or__(self, other: Condition):
        """
        Build a condition using logical OR.

        Args:
            other: The other condition to combine with.

        Returns:
            A new Condition instance.
        """
        if isinstance(other, Condition):
            return Condition('', 'OR', (self, other))
        else:
            raise TypeError(
                f"Unsupported operand type(s) for |: {type(self)} and {type(other)}"
            )

    def __and__(self, other: Condition):
        """
        Build a condition using logical AND.

        Args:
            other: The other condition to combine with.

        Returns:
            A new Condition instance.
        """
        if isinstance(other, Condition):
            return Condition('', 'AND', (self, other))
        else:
            raise TypeError(
                f"Unsupported operand type(s) for &: {type(self)} and {type(other)}"
            )


def where(field_name: str) -> Field:
    """
    Build a query field.
    """
    return Query()[field_name]


class ShushaDB:
    """ A simple, lightweight, persistent, document-oriented database.
    """

    default_table_name = '_default'

    def __init__(self, filename: str):
        """
        Initialize a MySmallDB instance.

        Args:
            filename (str): The name of the database file.
            _tables (Dict): The database tables.
            current_table (str): The current table.
            transaction_in_progress (bool): Whether a transaction is in progress.
            transaction_buffer (List): A buffer for transaction operations.
            lock (threading.Lock): A lock for transaction isolation.
            tables_lock (threading.Lock): A lock for table operations.
        """
        self.filename = filename
        self._tables = {
            self.default_table_name: {}
        }  # type: ignore[var-annotated]
        self.current_table = self.default_table_name
        self.transaction_in_progress = False
        self.transaction_buffer = []  # type: ignore[var-annotated]
        self.lock = threading.Lock()
        self.tables_lock = threading.Lock()

    # Context Manager
    def __enter__(self):
        """
        Enter the context manager, starting a transaction.
        """
        self.begin_transaction()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Exit the context manager, committing or rolling back the transaction.
        """
        if exc_type is not None:
            self.rollback_transaction()
        else:
            self.commit_transaction()

    # Magic Methods
    # Container Methods
    def __contains__(self, doc_id: str):
        """ Return True if the database contains a document with the given ID.
        """
        return self.contains(doc_id)

    def __iter__(self):
        """ Return an iterator over the documents in the database. """
        return iter(self._tables[self.current_table].values())

    def __len__(self):
        """ Return the number of documents in the database. """
        try:
            return len(self._tables[self.current_table])
        except Exception as e:
            print(f"Error counting data: {e}")
            return 0

    def __repr__(self):
        """ Return a string representation of the database. """
        return f"MySmallDB({self.filename!r})"

    def __str__(self):
        """ Return a string representation of the database. """
        return f"MySmallDB({self.filename!r})"

    def __del__(self):
        """ Close the database when the instance is deleted. """
        try:
            if not self.transaction_in_progress:
                self.save()
        except Exception as e:
            print(f"Error saving data: {e}")

    # Transaction Management
    def begin_transaction(self, isolation_level='read_committed'):
        """
        Begins a transaction with the given isolation level.
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
        """
        Commit the transaction and perform necessary actions.
        """
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
                self.rollback_transaction()
                raise TransactionError(f"Error committing transaction: {e}")
            finally:
                self._reset_transaction()

    def rollback_transaction(self):
        """
        Roll back the transaction and perform necessary actions.
        """
        if self.transaction_in_progress:
            self.transaction_buffer = []
            if self.lock.locked():
                self.lock.release()
            print("Transaction rolled back.")

    def _reset_transaction(self):
        """
        Reset the transaction state.
        """
        if self.transaction_in_progress:
            if self.transaction_buffer:
                # Release lock if it was acquired for read_committed isolation
                self.lock.release()
            self.transaction_in_progress = False
            self.transaction_buffer = []

    # Commit Methods
    def _commit_insert(self, document: Dict, key='gid') -> str:
        """
        Commit the insert operation within a transaction.

        Args:
            document: The document to insert.
            key: The key to use for the document ID.
        """
        doc_id = self.get_doc_gid(document, key)
        try:
            self._tables[self.current_table][doc_id] = document
            if not self.transaction_in_progress:
                self._commit_save()
            return doc_id
        except Exception as e:
            raise InsertionError(f"Error committing insert: {e}")

    def _commit_update(self, new_data: Dict, query: Condition) -> None:
        """
        Commit the update operation within a transaction.

        Args:
            new_data: The new data to update with.
            query: The query to match documents to update.
        """
        try:
            for doc_id, document in self._tables[self.current_table].items():
                if self._evaluate_condition(document, query):
                    updated_document = document.copy()
                    updated_document.update(new_data)
                    self._tables[self.current_table][doc_id] = updated_document

            if not self.transaction_in_progress:
                self._commit_save()
        except Exception as e:
            raise UpdateError(f"Error committing update: {e}")

    def _commit_remove(self, query: Condition) -> None:
        """
        Commit the remove operation within a transaction.

        Args:
            query: The query to match documents to remove.
        """
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
        """
        Commit the save operation within a transaction.
        """
        try:
            with shelve.open(self.filename, writeback=True) as db:
                db['tables'] = self._tables
        except Exception as e:
            raise RuntimeError(f"Error committing save: {e}")
        finally:
            if self.transaction_in_progress:
                # Release lock after saving changes for read_committed isolation
                self.lock.release()

    def _load_tables_from_disk(self):
        """
        Load tables from the shelve file on disk.
        """
        try:
            with shelve.open(self.filename, writeback=True) as db:
                return db.get('tables', {})
        except Exception as e:
            raise RuntimeError(f"Error loading tables from disk: {e}")

    # Transactional Operations
    # Document Manipulation
    def generate_doc_id(self):
        """
        Generate a new document ID.
        """
        return str(uuid.uuid4())

    def get_doc_gid(self, document: Dict[str, Any], key='gid') -> str:
        """
        Get the document ID from the document or generate a new one.

        Args:
            document: The document to get the ID from.
            key: The key to use for the document ID.

        Returns:
            The document ID.
        """
        gid_value = document.get(key)
        if gid_value and gid_value in self._tables[self.current_table]:
            return self.generate_doc_id()
        else:
            return gid_value or self.generate_doc_id()

    def insert(self, document: Dict[str, Any], key='gid') -> Optional[str]:
        """
        Insert a document into the current table.

        Args:
            document: The document to insert.
            key: The key to use for the document ID.

        Returns:
            The document ID.
        """
        doc_id = self.get_doc_gid(document, key)
        try:
            self._tables[self.current_table][doc_id] = document
            if not self.transaction_in_progress:
                self.save()
            return doc_id
        except Exception as e:
            print(f"Error inserting data: {e}")
            return None

    def insert_multiple(self, documents: List[Dict[str,
                                                   Any]]) -> Optional[List]:
        """
        Insert multiple documents into the current table.

        Args:
            documents (List[Dict]): The documents to insert.

        Returns:
            list: The document IDs.
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

    def retrieve(self, doc_id: Union[str, None]) -> Optional[Dict[str, Any]]:
        try:
            return self._tables[self.current_table].get(doc_id, None)
        except Exception as e:
            print(f"Error retrieving data: {e}")
            return None

    def get(self, doc_id: str):
        return self.retrieve(doc_id)

    def contains(self, doc_id: str):
        return doc_id in self._tables[self.current_table]

    def update(self, new_data: dict, query: Condition) -> None:
        try:
            with self.tables_lock:
                self._commit_update(new_data, query)
        except Exception as e:
            print(f"Error updating data: {e}")

    def remove(self, query: Condition) -> None:
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

    def all(self) -> List[Dict[str, Any]]:
        try:
            return list(self._tables[self.current_table].values())
        except Exception as e:
            print(f"Error retrieving all data: {e}")
            return []

    # Search and Query and Field Handling
    # Query and Condition Building
    @staticmethod
    def where(field_name: str) -> Field:
        """
        Build a query field.

        Args:
            field_name (str): The name of the field to query.

        Returns:
            A new Field instance.
        """
        return Query()[field_name]

    def _commit_search(self, condition: Condition):
        """
        Commit the search operation within a transaction.

        Args:
            condition: The condition to match.

        Returns:
            A list of matching documents.
        """
        try:
            results = [
                doc for doc in self._tables[self.current_table].values()
                if self._evaluate_condition(doc, condition)
            ]
            return results
        except Exception as e:
            print(f"Error during search: {e}")
            return []

    def search(self, condition):
        """
        Search the database for documents matching the given condition.

        Args:
            condition: The condition to match.

        Returns:
            A list of matching documents.
        """
        try:
            with self.tables_lock:
                results = self._commit_search(condition)
            return results
        except Exception as e:
            print(f"Error during search: {e}")
            return []

    def _evaluate_condition(self, document: Dict[str, Any],
                            condition: Condition) -> bool:
        """
        Evaluates a condition for a given document.

        Args:
            document (dict): The document to evaluate the condition for.
            condition: The condition to evaluate.
        """
        if not isinstance(condition, Condition):
            return False

        if condition.operator == 'fragment':
            return self._evaluate_fragment_condition(document, condition.value)
        elif condition.operator == 'AND':
            # Logical AND operation
            return all(
                self._evaluate_condition(document, sub_condition)
                for sub_condition in condition.value)
        elif condition.operator == 'OR':
            # Logical OR operation
            return any(
                self._evaluate_condition(document, sub_condition)
                for sub_condition in condition.value)
        else:
            field_value = self._get_nested_field_value(document,
                                                       condition.field)

            if condition.operator == '==':
                return field_value == condition.value
            elif condition.operator == '!=':
                return field_value != condition.value
            elif condition.operator == '>':
                return field_value > condition.value
            elif condition.operator == '>=':
                return field_value >= condition.value
            elif condition.operator == '<':
                return field_value < condition.value
            elif condition.operator == '<=':
                return field_value <= condition.value
            elif condition.operator is None:
                return bool(field_value)
            else:
                print(f"Unsupported operator: {condition.operator}")
                return False

    def _evaluate_fragment_condition(self, document: Dict[str, Any],
                                     fragment: Dict[str, Any]) -> bool:
        """
        Evaluates a fragment condition for a given document.

        Args:
            document (dict): The document to evaluate the condition for.
            fragment (dict): The fragment to evaluate.

        Returns:
            bool: Whether the fragment matches the document.
        """
        try:
            # print("Evaluating fragment condition...")
            for key, value in fragment.items():
                field_value = self._get_nested_field_value(document, key)
                if field_value == value:
                    print("No fragment match found")
                    return False

            # print("Fragment match found")
            return True
        except Exception as e:
            print(f"Error evaluating fragment condition: {e}")
            return False

    def _get_nested_field_value(self, document: Dict[str, Any],
                                field_path: str) -> Any:
        """
        Returns the value of a nested field.

        Args:
            document (dict): The document to get the field value from.
            field_path (str): The path to the field.

        Returns:
            The value of the field.
        """

        def get_nested_value(doc: Dict[str, Any], fields: List[str]) -> Any:
            """
            Recursively get the value of a nested field.
            """
            if not fields:
                return doc
            field = fields[0]
            if '[' in field:
                field, key = field.split('[')
                key = key.rstrip(']')
                nested_value = doc.get(field, {}).get(key)
            else:
                nested_value = doc.get(field)
            return get_nested_value(nested_value,
                                    fields[1:]) if nested_value else None

        try:
            fields = field_path.split('.')
            return get_nested_value(document, fields)
        except Exception as e:
            print(f"Error getting nested field value: {e}")
            return None

    # Table Management
    def table(self, name: str):
        """
        Returns a table instance for the given table name.

        Args:
            name (str): The name of the table.

        Returns:
            A table instance.
        """
        self.current_table = name
        if name not in self._tables:
            self._tables[name] = {}
            print(f"Table '{name}' not found.")
        return self

    def drop_table(self, name: str):
        """
        Removes the table with the given name from the database.

        Args:
            name (str): The name of the table.
        """
        try:
            del self._tables[name]
            if not self.transaction_in_progress:
                self.save()
        except Exception as e:
            print(f"Error dropping table: {e}")

    def drop_tables(self):
        """
        Removes all tables from the database.

        Args:
            name (str): The name of the table.
        """
        try:
            self._tables = {}
            if not self.transaction_in_progress:
                self.save()
        except Exception as e:
            print(f"Error dropping all tables: {e}")

    def tables(self):
        """
        Returns a set of all table names in the database.
        """
        return set(self._tables.keys())

    # Persistence (File I/O)
    def save(self):
        """
        Saves the database to a file.
        """
        try:
            with self.tables_lock:
                if self.transaction_in_progress:
                    # If a transaction is in progress, do not save directly
                    print("Transaction in progress, skipping save.")
                elif self._tables != self._load_tables_from_disk():
                    # Save only if there are changes
                    self._commit_save()
        except Exception as e:
            print(f"Error saving data: {e}")
            self.rollback_transaction()

    def load(self):
        """
        Loads the database from a file.
        """
        try:
            self.begin_transaction()
            with shelve.open(self.filename, writeback=True) as db:
                self._tables = db.get('tables', {})
            self.commit_transaction()
        except Exception as e:
            print(f"Error loading data: {e}")
            self.rollback_transaction()


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
