import os

from burdock.sql.ast.ast import Relation
from burdock.sql.ast.tokens import Literal
from burdock.sql.ast.expression import Expression
from burdock.sql.ast.expressions.numeric import BareFunction
from burdock.sql.ast.expressions.sql import BooleanJoinCriteria, UsingJoinCriteria
from .base import Base, NameCompare

"""
    A dumb pipe that gets a rowset back from a database using 
    a SQL string, and converts types to some useful subset
"""
class PrestoReader(Base):
    def __init__(self, host, database, user, password=None, port=None):
        import prestodb
        self.api = prestodb.dbapi
        self.engine = "Presto"

        self.host = host
        self.database = database
        self.user = user
        self.port = int(port)

        if password is None:
            if 'PRESTO_PASSWORD' in os.environ:
                password = os.environ['PRESTO_PASSWORD']
        self.password = password

        self.update_connection_string()
        self.serializer = None
        self.compare = PrestoNameCompare()
    """
        Executes a raw SQL string against the database and returns
        tuples for rows.  This will NOT fix the query to target the
        specific SQL dialect.  Call execute_typed to fix dialect.
    """
    def execute(self, query):
        if not isinstance(query, str):
            raise ValueError("Please pass strings to execute.  To execute ASTs, use execute_typed.")
        cnxn = self.api.connect(
            host=self.host,
            http_scheme='https' if self.port == 443 else 'http',
            user=self.user,
            port=self.port,
            catalog=self.database
        )
        cursor = cnxn.cursor()
        cursor.execute(str(query).replace(';',''))
        rows = cursor.fetchall()
        if cursor.description is None:
            return []
        else:
            col_names = [tuple(desc[0] for desc in cursor.description)]
            rows = [row for row in rows]
            return col_names + rows

    def update_connection_string(self):
        self.connection_string = None
        pass

    def switch_database(self, dbname):
        sql = "USE " + dbname + ";"
        self.execute(sql)

    def db_name(self):
        return self.database

class PrestoNameCompare(NameCompare):
    def __init__(self, search_path=None):
        self.search_path = search_path if search_path is not None else ["dbo"]
    def identifier_match(self, query, meta):
        return self.strip_escapes(query).lower() == self.strip_escapes(meta).lower()