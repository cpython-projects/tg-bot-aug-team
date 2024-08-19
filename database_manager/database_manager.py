import sqlite3


class DatabaseManager:
    """
    Manages the connection to the SQLite database and provides methods
    for initializing the database schema and saving user registration data.
    """

    def __init__(self, db_name='tb_bot_db.db'):
        """
        Initializes the DatabaseManager by setting the database name.
        The actual connection is established when needed.
        """
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        """
        Creates the user_registration table in the database if it doesn't already exist.
        This method establishes a temporary connection for initialization.
        """
        with sqlite3.connect(self.db_name) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_registration (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    username TEXT,
                    course_name TEXT
                )
            ''')
            connection.commit()

    def save_user_registration(self, user_id: int, username: str, course_name: str):
        """
        Saves user registration data to the database.
        A new connection is established for this operation.

        Parameters:
        - user_id (int): The ID of the user.
        - username (str): The username of the user.
        - course_name (str): The name of the course the user is registering for.
        """
        with sqlite3.connect(self.db_name) as connection:
            cursor = connection.cursor()
            cursor.execute('''
                INSERT INTO user_registration (user_id, username, course_name)
                VALUES (?, ?, ?)
            ''', (user_id, username, course_name))
            connection.commit()
