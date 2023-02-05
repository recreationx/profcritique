import sqlite3
from prototype.model import ReviewSentiment

init_table = {
    "teachers": """
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY,
            name TEXT,
            school_id INTEGER,
            FOREIGN KEY(school_id) REFERENCES schools(id)
        );
    """,
    "users": """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT
        );
    """,
    "reviews": """
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER,
            user_id INTEGER,
            rating INTEGER,
            comment TEXT,
            flag TEXT,
            FOREIGN KEY(teacher_id) REFERENCES teachers(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        );
    """,
    "schools": """
        CREATE TABLE IF NOT EXISTS schools (
            id INTEGER PRIMARY KEY,
            name TEXT
        );
    """,
}

insert_table = {
    "create_teacher": """
    INSERT INTO teachers VALUES (id, name, school_id);
    """,
    "create_user": """
    INSERT INTO users (username, password) VALUES (?, ?);
    """,
    "add_review": """
    INSERT INTO reviews (teacher_id, user_id, rating, comment, flag) VALUES (?, ?, ?, ?, ?);
    """,
    "create_school": """
    INSERT INTO schools VALUES (id, name);
    """,
}

query_table = {
    "load_user_by_id": """
    SELECT * from users WHERE id=?;
    """,
    "load_user_by_name": """
    SELECT * from users WHERE username=?;
    """,
    "search_teacher": """
    SELECT teachers.id AS teacher_id, teachers.name AS teacher_name, schools.name AS school_name
    FROM teachers
    JOIN schools ON teachers.school_id = schools.id
    WHERE teachers.name LIKE ?;
    """,
    "get_teacher_by_id": """
    SELECT teachers.name AS teacher_name, schools.name AS school_name
    FROM teachers
    JOIN schools ON teachers.school_id = schools.id
    WHERE teachers.id = ?;
    """,
    "get_review": """
    SELECT users.username AS username, reviews.rating AS rating, reviews.comment AS review, reviews.flag AS flag
    FROM reviews
    JOIN users ON users.id = reviews.user_id
    WHERE reviews.teacher_id = ?
    ORDER BY reviews.id DESC;
    """,
    "get_aggregated_score": """
    SELECT avg(reviews.rating) AS rating
    FROM reviews
    WHERE reviews.teacher_id = ?
    """,
}


class Datastore:
    def __init__(self, uri: str):
        """Initialize a database with given URI

        Args:
            uri (string): URI for database
        """
        self.uri = uri
        self.predictor = ReviewSentiment()

    def get_conn(self) -> sqlite3.Connection:
        """Retrieves a connection with the database
        Returns:
            conn: A sqlite3 Connection object connected to stored URI
        """

        def dict_factory(cursor: sqlite3.Cursor, row: sqlite3.Row) -> dict:
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d

        conn = sqlite3.connect(self.uri)
        conn.row_factory = dict_factory
        return conn

    def get_record(self, command, param=None):
        """Retrieve a single record using key from query_table
        Args:
            command (str): A key in query_table
            param (tup/list, optional): parameters to pass in.
            Defaults to None.
        Returns:
            arr: Array of rows
        """
        conn = self.get_conn()
        cur = conn.cursor()
        if param is None:
            cur.execute(query_table[command])
        else:
            cur.execute(query_table[command], param)
        return cur.fetchone()

    def get_records(self, command, param=None):
        """Retrieve records using key from query_table
        Args:
            command (str): A key in query_table
            param (tup/list, optional): parameters to pass in.
            Defaults to None.
        Returns:
            arr: Array of rows
        """
        conn = self.get_conn()
        cur = conn.cursor()
        if param is None:
            cur.execute(query_table[command])
        else:
            cur.execute(query_table[command], param)
        return cur.fetchall()

    def tables_init(self):
        """Initializes required tables for the database"""
        conn = self.get_conn()
        cursor = conn.cursor()
        for table_commands in init_table.keys():
            cursor.execute(init_table[table_commands])

        conn.commit()
        conn.close()

    def get_user_by_id(self, user_id):
        user = self.get_record("load_user_by_id", (user_id,))
        return user

    def get_user_by_name(self, username):
        user = self.get_record("load_user_by_name", (username,))
        return user

    def create_user(self, username, password):
        conn = self.get_conn()
        conn.execute(insert_table["create_user"], (username, password))
        conn.commit()

    def search_teacher(self, teacher_name):
        teachers = self.get_records("search_teacher", (f"%{teacher_name}%",))
        return teachers

    def get_teacher_by_id(self, teacher_id):
        teacher = self.get_record("get_teacher_by_id", (int(teacher_id),))
        score = self.get_record("get_aggregated_score", (int(teacher_id),))
        if score["rating"] is None:
            score["rating"] = 0.0
        return dict(teacher, **score)

    def add_review(self, teacher_id, user_id, rating, review, fallback_rating):
        conn = self.get_conn()
        prediction = self.predictor.predict(review)
        if prediction == []:
            conn.execute(
                insert_table["add_review"],
                (teacher_id, user_id, fallback_rating, review, "Manual"),
            )
            conn.commit()
        else:
            rating = sum((2 * i) + 3 for i in prediction[0]["labels"]) // len(
                prediction[0]["labels"]
            )
            conn.execute(
                insert_table["add_review"],
                (teacher_id, user_id, rating, review, "AI"),
            )
            conn.commit()

    def get_review(self, teacher_id):
        reviews = self.get_records("get_review", (int(teacher_id),))
        return reviews
