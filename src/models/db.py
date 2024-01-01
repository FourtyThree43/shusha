import sqlite3
import json
from threading import Lock
from sqlite3 import Error
from contextlib import contextmanager
from logger import LoggerService

DB_FILE = "shusha.db"


class StructsDB:
    TABLE_DOWNLOAD = 'downloads_t'
    TABLE_FILES = 'files_t'
    TABLE_BITTORRENT = 'bittorrent_t'
    TABLE_QUEUE = 'queue_t'

    def __init__(self, db_path=DB_FILE):
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.create_tables()
        self.lock = Lock()
        self.logger = LoggerService(logger_name="ShushaDB")

    @contextmanager
    def database_transaction(self):
        """
        Context manager for managing a transaction.
        """
        with self.lock:
            try:
                # Open transaction
                yield self.connection

                # Commit transaction
                self.logger.log("Database transaction committed.")
                self.connection.commit()
            except Error as e:
                # Rollback transaction on error
                self.connection.rollback()
                self.logger.log(f"Error during transaction: {e}",
                                level="error")
                raise e

    def _execute_query(self, cursor, query, value=None):
        try:
            if value:
                cursor.execute(query, value)
            else:
                cursor.execute(query)
        except Error as e:
            self.logger.log(f"Error executing query: {e}", level="error")

    def _execute_query_and_fetchall(self, cursor, query, params=None):
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchall()
        except Error as e:
            self.logger.log(f"Error executing query: {e}", level="error")
            return []

    def _execute_query_and_fetchone(self, cursor, query, params=None):
        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.fetchone()
        except Error as e:
            self.logger.log(f"Error executing query: {e}", level="error")
            return None

    def create_tables(self):
        with self.connection:
            cursor = self.connection.cursor()

            # Table for storing download information
            download_table_query = f'''
                CREATE TABLE IF NOT EXISTS {StructsDB.TABLE_DOWNLOAD} (
                    gid TEXT PRIMARY KEY,
                    status TEXT,
                    totalLength INTEGER,
                    completedLength INTEGER,
                    uploadLength INTEGER,
                    bitfield TEXT,
                    downloadSpeed INTEGER,
                    uploadSpeed INTEGER,
                    infoHash TEXT,
                    numSeeders INTEGER,
                    seeder INTEGER,
                    pieceLength INTEGER,
                    numPieces INTEGER,
                    connections INTEGER,
                    errorCode INTEGER,
                    errorMessage TEXT,
                    followedBy TEXT,
                    following TEXT,
                    belongsTo TEXT,
                    dir TEXT,
                    verifiedLength INTEGER,
                    verifyIntegrityPending INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            '''
            self._execute_query(cursor, download_table_query)

            # Table for storing files information linked to downloads
            files_table_query = f'''
                CREATE TABLE IF NOT EXISTS {StructsDB.TABLE_FILES} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_index INTEGER,
                    path TEXT,
                    length INTEGER,
                    completed_length INTEGER,
                    selected INTEGER,
                    uris TEXT,
                    download_id TEXT,
                    FOREIGN KEY (download_id) REFERENCES {StructsDB.TABLE_DOWNLOAD} (gid)
                )
            '''
            self._execute_query(cursor, files_table_query)

            # Table for storing BitTorrent information linked to downloads
            bittorrent_table_query = f'''
                CREATE TABLE IF NOT EXISTS {StructsDB.TABLE_BITTORRENT} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    announce_list TEXT,
                    comment TEXT,
                    creation_date INTEGER,
                    mode TEXT,
                    info_name TEXT,
                    download_id TEXT,
                    FOREIGN KEY (download_id) REFERENCES {StructsDB.TABLE_DOWNLOAD} (gid)
                )
            '''
            self._execute_query(cursor, bittorrent_table_query)

    def insert_download_info(self, cursor, gid, info):
        """
        Insert download information into the 'downloads' table.
        """
        columns = [
            "gid", "status", "totalLength", "completedLength", "uploadLength",
            "bitfield", "downloadSpeed", "uploadSpeed", "infoHash",
            "numSeeders", "seeder", "pieceLength", "numPieces", "connections",
            "errorCode", "errorMessage", "followedBy", "following",
            "belongsTo", "dir", "verifiedLength", "verifyIntegrityPending"
        ]
        values = [gid] + [
            info.get(column, 0) if column != "followedBy" else json.dumps(
                info.get("followedBy", [])) for column in columns[1:]
        ]
        placeholders = ', '.join(['?' for _ in columns])

        query = f"INSERT INTO {StructsDB.TABLE_DOWNLOAD} ({', '.join(columns)}) VALUES ({placeholders})"

        self._execute_query(cursor, query, values)

    def insert_file_info(self, cursor, file_info, gid):
        """
        Insert file information linked to downloads into the 'files_t' table.
        """
        columns = [
            "file_index", "path", "length", "completed_length", "selected",
            "uris", "download_id"
        ]
        values = [
            file_info.get(column, 0) if column != "uris" else json.dumps(
                file_info.get("uris", [])) for column in columns[:-1]
        ] + [gid]

        query = f"INSERT INTO files_t ({', '.join(columns)}) VALUES ({', '.join(['?' for _ in columns])})"

        self._execute_query(cursor, query, values)

    def insert_bittorrent_info(self, cursor, bittorrent_info_entry, gid):
        """
        Insert BitTorrent information linked to downloads into the 'bittorrent_t' table.
        """
        columns = [
            "announce_list", "comment", "creation_date", "mode", "info_name",
            "download_id"
        ]
        values = [
            json.dumps(bittorrent_info_entry.get("announce_list", [])),
            bittorrent_info_entry.get("comment", ""),
            bittorrent_info_entry.get("creation_date", 0),
            bittorrent_info_entry.get("mode", ""),
            bittorrent_info_entry.get("info_name", ""), gid
        ]

        query = f"INSERT INTO bittorrent_t ({', '.join(columns)}) VALUES ({', '.join(['?' for _ in columns])})"

        self._execute_query(cursor, query, values)

    def update_table(self, table_name, set_values, where_column, where_value):
        with self.database_transaction() as conn:
            cursor = conn.cursor()

            set_columns = ', '.join(
                [f"{column} = ?" for column, _ in set_values.items()])
            query = f"UPDATE {table_name} SET {set_columns} WHERE {where_column} = ?"

            values = list(set_values.values()) + [where_value]
            self._execute_query(cursor, query, values)

    def store_download_info(self, gid, info):
        """
        Save download status, files, and BitTorrents to the database.
        """
        with self.database_transaction() as conn:
            cursor = conn.cursor()

            self.insert_download_info(cursor, gid, info)

            files_info = info.get("files", [])
            for file_info in files_info:
                self.insert_file_info(cursor, file_info, gid)

            bittorrent_info = info.get("bittorrent", [])
            for bittorrent_info_entry in bittorrent_info:
                self.insert_bittorrent_info(cursor, bittorrent_info_entry, gid)

    def get_all_downloads(self):
        with self.connection:
            cursor = self.connection.cursor()

            query = f'''
                SELECT gid, status, totalLength, completedLength, uploadLength,
                       bitfield, downloadSpeed, uploadSpeed, infoHash, numSeeders,
                       seeder, pieceLength, numPieces, connections, errorCode,
                       errorMessage, followedBy, following, belongsTo, dir,
                       verifiedLength, verifyIntegrityPending, timestamp
                FROM {StructsDB.TABLE_DOWNLOAD}
            '''

            return self._execute_query_and_fetchall(cursor, query)

    def get_download_info(self, gid):
        """
        Get download status from the 'downloads' table based on 'gid'.
        """
        with self.connection:
            cursor = self.connection.cursor()

            query = f'''
                SELECT gid, status, totalLength, completedLength, uploadLength,
                       bitfield, downloadSpeed, uploadSpeed, infoHash, numSeeders,
                       seeder, pieceLength, numPieces, connections, errorCode,
                       errorMessage, followedBy, following, belongsTo, dir,
                       verifiedLength, verifyIntegrityPending, timestamp
                FROM {StructsDB.TABLE_DOWNLOAD}
                WHERE gid = ?
            '''

            return self._execute_query_and_fetchone(cursor, query, (gid, ))

    def get_files_info(self, gid):
        with self.connection:
            cursor = self.connection.cursor()

            query = f'''
                SELECT id, file_index, path, length, completed_length, selected, uris, download_id
                FROM {StructsDB.TABLE_FILES}
                WHERE download_id = ?
            '''

            return self._execute_query_and_fetchall(cursor, query, (gid, ))

    def get_bittorrent_info(self, gid):
        with self.connection:
            cursor = self.connection.cursor()

            query = f'''
                SELECT id, announce_list, comment, creation_date, mode, info_name, download_id
                FROM {StructsDB.TABLE_BITTORRENT}
                WHERE download_id = ?
            '''

            return self._execute_query_and_fetchall(cursor, query, (gid, ))

    def reset_database(self):
        """
        Reset the entire database by deleting all items.
        """
        with self.database_transaction() as conn:
            cursor = conn.cursor()
            self._execute_query(cursor, "DELETE FROM downloads")
            self._execute_query(cursor, "DELETE FROM files_t")
            self._execute_query(cursor, "DELETE FROM bittorrent_t")

    def update_download(self, gid, info_updates: dict):
        """
        Update download status in the 'downloads' table based on 'gid'.
        """
        where_column = "gid"
        self.update_table(StructsDB.TABLE_DOWNLOAD, info_updates, where_column,
                          gid)

    def close_connection(self):
        """Close the database connection if it is open."""
        if self.connection:
            try:
                self.connection.close()
                self.logger.log("Database connection closed.")
            except Error as e:
                self.logger.log(f"Error closing database connection: {e}",
                                level="error")


# Example usage:
if __name__ == "__main__":
    db = StructsDB()

    db.create_tables()

    # Example: Storing download information
    download_info = {
        "gid": "3089b05edsas3d829",
        "status": "complete",
        "totalLength": "34896138",
        "completedLength": "34896138",
        "uploadLength": "0",
        "bitfield": "ffff80",
        "downloadSpeed": "0",
        "uploadSpeed": "0",
        "infoHash": "",
        "numSeeders": "0",
        "seeder": "0",
        "pieceLength": "2097152",
        "numPieces": "17",
        "connections": "0",
        "errorCode": "0",
        "errorMessage": "",
        "followedBy": [],
        "following": "",
        "belongsTo": "",
        "dir": "/downloads",
        "verifiedLength": "0",
        "verifyIntegrityPending": "0"
    }

    db.store_download_info(download_info["gid"], download_info)

    # Example: Retrieving all download information
    all_downloads = db.get_all_downloads()
    for download in all_downloads:
        db.logger.log(download)

    # Example: Retrieving files information linked to a download
    files_for_download = db.get_files_info(download_info["gid"])
    for file_info in files_for_download:
        # Convert 'file_index' to 'index' when presenting the data
        file_info_dict = dict(file_info)
        file_info_dict['index'] = file_info_dict.pop('file_index')
        db.logger.log(f"Files for download: {file_info_dict}")

    # Example: Retrieving BitTorrent information linked to a download
    bittorrent_info_for_download = db.get_bittorrent_info(download_info["gid"])
    for bittorrent_info in bittorrent_info_for_download:
        db.logger.log(f"BitTorrent info for download: {bittorrent_info}")

    # Example usage to update the 'downloads' table
    gid_to_update = "3089b05edsas3d829"
    status_updates = {"status": "paused", "downloadSpeed": 10000}

    db.logger.log(db.get_download_info(gid=gid_to_update))
    db.update_download(gid_to_update, status_updates)
    db.logger.log(db.get_download_info(gid=gid_to_update))

    db.close_connection()
