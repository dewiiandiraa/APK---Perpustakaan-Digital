import mysql.connector
from mysql.connector import Error

class Database:
    def __init__(self):
        self.config = {
            "host": "localhost",
            "user": "root",
            "password": "",
            "database": "perpustakaan",
            "port": 3306,
            "autocommit": False
        }

    def hubungkan(self):
        try:
            conn = mysql.connector.connect(**self.config)
            if conn.is_connected():
                return conn
            raise Error("Koneksi database gagal.")
        except Error as e:
            raise ConnectionError(
                f"Tidak dapat terhubung ke database perpustakaan: {e}"
            ) from e
