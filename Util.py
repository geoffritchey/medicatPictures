import requests
import pyodbc
import build


def initialized():
    global initial
    return initial


def get_properties():
    global conn
    cur = conn.cursor()
    cur.execute("select code, format(value, 'yyyy-MM-ddTHH:mm:ss.fffZ') from last_modified")
    rows = cur.fetchall()
    return dict(rows)


if __name__ == 'only to declare variabes':
    conn = None
    cursor = None
    str_format = None

    username = None
    password = None

    # Create a persistent session in order to maintain authentication
    authenticated_session = None
    authenticated_session.auth = None

    root_uri = "https://sisclientweb-100542.campusnexus.cloud/"

    properties = None
    initial = False


try:
    initialized()
except NameError:
    conn = pyodbc.connect(
        r'DRIVER={SQL Server};'
        r'SERVER=gefjun.lcunet.lcu.edu;'
        r'DATABASE=DynamicsNexusStagingArea;'
        r'UID=Avatar;'
        r'PWD=' + build.avatar_password
    )
    cursor = conn.cursor()

    str_format = '%Y-%m-%dT%H:%M:%S'

    username = build.nexus_username
    password = build.nexus_password

    sftp_username = build.sftp_username
    sftp_password = build.sftp_password

    # Create a persistent session in order to maintain authentication
    authenticated_session = requests.Session()
    authenticated_session.auth = (username, password)

    root_uri = "https://sisclientweb-100542.campusnexus.cloud/"

    properties = get_properties()
    initial = True

