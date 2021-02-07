import sqlite3


class DBHandler:
    def __init__(self) -> None:
        self.conn = sqlite3.connect('mutation_database.db')
        self.c = self.conn.cursor()

    def create_table(self):
        create_query = 'CREATE TABLE IF NOT EXISTS mutationTable(lineNumber String, potentialLine Text, methodBody Text, mutationKind Text)'
        self.c.execute(create_query)

    def insert_data(self, lineNumber, potentialLine, methodBody, mutationKind):
        insert_query = "INSERT INTO mutationTable VALUES (" + "'" + str(
            lineNumber) + "'" + "," + "'" + potentialLine + "'" + "," + "'" + methodBody + "'" + "," + "'" + mutationKind + "'" + ")"
        # print(insert_query)
        self.c.execute(insert_query)
        self.conn.commit()

    def read_data(self):
        read_query = 'SELECT * FROM mutationTable'
        return self.c.execute(read_query)

    def delete_table(self):
        drop_query = 'DROP TABLE mutationTable'
        self.c.execute(drop_query)

    def filter_table(self):
        mutation_list = []
        cursor_obj = self.read_data()
        for row in cursor_obj:
            mutation_list.append(row)
        return mutation_list


def main():
    db_handler = DBHandler()
    # db_handler.create_table()
    # db_handler.insert_data(12, "x = malloc (sizeof(char*))",
    #                      "x = malloc (sizeof(char*))")
    # db_handler.delete_table()
    ds_list = db_handler.filter_table()
    print(ds_list)


if __name__ == "__main__":
    main()
