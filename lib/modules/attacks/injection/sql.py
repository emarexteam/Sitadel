import re
from urllib.parse import parse_qsl, urlencode, urlsplit

from lib.utils.container import Services
from .. import AttackPlugin


class Sql(AttackPlugin):
    def dberror(self, data):
        if re.search(
            r"supplied argument is not a valid MySQL|Column count doesn\'t match value count at row|mysql_fetch_array()|on MySQL result index|You have an error in your SQL syntax;|You have an error in your SQL syntax near|MySQL server version for the right syntax to use|\[MySQL]\[ODBC|Column count doesn\'t match|valid MySQL result|MySqlClient.",
            data,
        ):
            return "MySQL Injection"
        if re.search(
            r"System.Data.OleDb.OleDbException|\[Microsoft]\[ODBC SQL Server Driver]|\[Macromedia]\[SQLServer JDBC Driver]|SqlException|System.Data.SqlClient.SqlException|Unclosed quotation mark after the character string|mssql_query()|Microsoft OLE DB Provider for ODBC Drivers|Microsoft OLE DB Provider for SQL Server|Incorrect syntax near|Sintaxis incorrecta cerca de|Syntax error in string in query expression|Unclosed quotation mark before the character string|Data type mismatch in criteria expression.|ADODB.Field (0x800A0BCD)|the used select statements have different number of columns",
            data,
        ):
            return "MSSQL-Based Injection"
        if re.search(
            r"java.sql.SQLException|java.sql.SQLSyntaxErrorException|org.hibernate.QueryException: unexpected char:|org.hibernate.QueryException: expecting \'",
            data,
        ):
            return "Java.SQL Injection"
        if re.search(
            r"PostgreSQL query failed:|supplied argument is not a valid PostgreSQL result|pg_query() \[:|pg_exec() \[:|valid PostgreSQL result|Npgsql.|PostgreSQL query failed: ERROR: parser:",
            data,
        ):
            return "PostgreSQL Injection"
        if re.search(r"\[IBM]\[CLI Driver]\[DB2/6000]|DB2 SQL error", data):
            return "DB2 Injection"
        if re.search(
            r"<b>Warning</b>: ibase_|Unexpected end of command in statement|Dynamic SQL Error",
            data,
        ):
            return "Interbase Injection"
        if re.search(r"Sybase message:", data):
            return "Sybase Injection"
        if re.search(r"Oracle error", data):
            return "Oracle Injection"
        if re.search(
            r"SQLite/JDBCDriver|System.Data.SQLite.SQLiteException|SQLITE_ERROR|SQLite.Exception",
            data,
        ):
            return "SQLite Injection"
        return None

    def process(self, start_url, crawled_urls):
        output = Services.get("output")
        request = Services.get("request_factory")
        datastore = Services.get("datastore")

        output.info("Checking sql injection...")
        db = datastore.open("sql.txt", "r")
        dbfiles = [x.split("\n") for x in db]
        try:
            for payload in dbfiles:
                for url in crawled_urls:

                    # Current request parameters
                    params = dict(parse_qsl(urlsplit(url).query))
                    # Change the value of the parameters with the payload
                    tainted_params = {x: payload for x in params}

                    if len(tainted_params) > 0:
                        # Prepare the attack URL
                        attack_url = urlsplit(url).geturl() + urlencode(tainted_params)
                        output.debug("Testing: %s" % attack_url)
                        resp = request.send(
                            url=attack_url, method="GET", payload=None, headers=None
                        )
                        erro = self.dberror(resp.text)
                        if erro is not None:
                            output.finding(
                                "That site may be vulnerable to SQL Injection at %s\nInjection: %s"
                                % (url, payload)
                            )
        except Exception as e:
            output.error("Error occured\nAborting this attack...\n")
            output.debug("Traceback: %s" % e)
            return
