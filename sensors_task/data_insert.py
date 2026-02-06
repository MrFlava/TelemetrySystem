from datetime import datetime, timedelta

import psycopg2
from psycopg2.extras import execute_values


conn = psycopg2.connect("dbname=sensorsdb user=myuser password=mypassword host=127.0.0.1")
cur = conn.cursor()


cur.execute("INSERT INTO sensor_types (name) VALUES ('V') ON CONFLICT (name) DO NOTHING;")
cur.execute("INSERT INTO sensor_types (name) VALUES ('R') ON CONFLICT (name) DO NOTHING;")


cur.execute("INSERT INTO rooms (name) VALUES ('room_A') ON CONFLICT (name) DO NOTHING;")
cur.execute("INSERT INTO rooms (name) VALUES ('room_B') ON CONFLICT (name) DO NOTHING;")


cur.execute("SELECT id, name FROM rooms;")
rooms = {r[1]: r[0] for r in cur.fetchall()}

cur.execute("SELECT id, name FROM sensor_types;")
types = {t[1]: t[0] for t in cur.fetchall()}

def ensure_sensor(name, room_name, type_name):
    cur.execute("""
        INSERT INTO sensors (room_id, type_id, name)
        VALUES (%s, %s, %s)
        ON CONFLICT DO NOTHING
        RETURNING id;
    """, (rooms[room_name], types[type_name], name))
    res = cur.fetchone()
    if res:
        return res[0]

    cur.execute("""
        SELECT id FROM sensors
        WHERE room_id = %s AND type_id = %s AND name = %s
        """, (rooms[room_name], types[type_name], name))
    return cur.fetchone()[0]

sensor_A1_V = ensure_sensor("A1_V", "room_A", "V")
sensor_A1_R1 = ensure_sensor("A1_R1", "room_A", "R")
sensor_A1_R2 = ensure_sensor("A1_R2", "room_A", "R")

sensor_B1_V = ensure_sensor("B1_V", "room_B", "V")
sensor_B2_V = ensure_sensor("B2_V", "room_B", "V")
sensor_B1_R = ensure_sensor("B1_R", "room_B", "R")
sensor_B2_R = ensure_sensor("B2_R", "room_B", "R")
sensor_B3_R = ensure_sensor("B3_R", "room_B", "R")

conn.commit()
cur.close()
conn.close()



def insert_measurements(conn, sensor_id, ts_values, values):
    rows = [(sensor_id, float(v), ts) for ts, v in zip(ts_values, values)]
    with conn.cursor() as cur:
        insert_sql = "INSERT INTO measurements (sensor_id, value, ts) VALUES %s"
        execute_values(cur, insert_sql, rows)
    conn.commit()

base = datetime(2025, 6, 30, 10, 0, 0, 0, tzinfo=None)

def to_timestamp(dt):
    return dt


def mk_times(start, seconds, per_sensor=2):
    times = []
    for i in range(seconds):
        t = start + timedelta(seconds=i)

        for _ in range(per_sensor):
            times.append(t)
    return times

conn = psycopg2.connect("dbname=sensorsdb user=myuser password=mypassword host=127.0.0.1")
cur = conn.cursor()

start = datetime(2025, 6, 30, 10, 0, 0)

times_V = [start.replace(microsecond=0) + timedelta(seconds=i) for i in range(2)]
vals_V = [50.0, 50.2]

insert_measurements(conn, sensor_A1_V, times_V, vals_V)

times_R1 = [start.replace(microsecond=0) + timedelta(seconds=i) for i in range(2)]
vals_R1 = [10.0, 10.5]
times_R2 = [start.replace(microsecond=0) + timedelta(seconds=0)]
vals_R2 = [9.8]

insert_measurements(conn, sensor_A1_R1, times_R1, vals_R1)
insert_measurements(conn, sensor_A1_R2, times_R2, vals_R2)

startB = datetime(2025, 6, 30, 11, 0, 0)

insert_measurements(conn, sensor_B1_V, [startB, startB], [48.0, 48.5])
insert_measurements(conn, sensor_B2_V, [startB + timedelta(seconds=1), startB + timedelta(seconds=1, microseconds=1000)], [48.2, 48.3])

insert_measurements(conn, sensor_B1_R, [startB, startB], [9.5, 9.7])
insert_measurements(conn, sensor_B2_R, [startB], [9.6])
insert_measurements(conn, sensor_B3_R, [startB + timedelta(seconds=1)], [9.4])

cur.close()
conn.close()
