import json
import crypt
import sys 
import sqlite3

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except (ValueError):
        sys.exit(ValueError)

def create_user (conn, user):
    """
    Create a new project into the projects table
    :param conn:
    :param project:
    :return: project id
    """
    sql = ''' INSERT INTO users(name, role, password, uid, groups, state, timestamp_update_state, vmID_assigned,current_alloc_id) VALUES(?,?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, user)
    return cur.lastrowid

def get_users(filename):
    users = []
    try: 
        f = open(filename, "r")
        for line in f:
            if line != "":                 
                user = json.loads (line)
                password_encrypted = user['password']
                users.append ( (user['name'], user['role'], password_encrypted, user['uid'], user['groups'], 1, 0, "-1", "-1") )
        f.close()
    except:
        sys.exit('Error adding users')
    return users

def main():
    database = "./cem.db"
    users_file = "./users.json"
    users_list = get_users(users_file)

    # create a database connection
    conn = create_connection(database)
    with conn:
        for user in users_list:
            create_user(conn, user)

if __name__ == '__main__':
    main()
