"""
Simple integration test that connects two socket.io clients, joins the same room,
and checks that a `field_update` emitted by one client is received by the other.

Run: /home/theious/PROGS/sistema-atas-cri1/.venv/bin/python test/socket_sync_test.py

Note: The Flask app (socketio.run) must be running on http://localhost:5000
"""

import sqlite3
import time
import threading
import socketio

# Pick an existing sacramental ata from the DB to use rooms
DB = 'database/atas.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()
row = c.execute("SELECT id, data FROM atas WHERE tipo='sacramental' ORDER BY data DESC LIMIT 1").fetchone()
if not row:
    raise SystemExit("Nenhuma ata sacramental encontrada na base de dados (esperando pelo menos uma).")
ata_id = row['id']
data = row['data']
conn.close()

room_ata = f"ata-{ata_id}"
room_date = f"date-{data}"
print('Using rooms:', room_ata, room_date)

s1 = socketio.Client()
s2 = socketio.Client()

received = {
    's1_field_updates': [],
    's2_field_updates': [],
    's1_update_users': [],
    's2_update_users': []
}

connected = threading.Event()

@s1.event
def connect():
    print('[s1] connect')

@s1.on('field_update')
def s1_field(data):
    print('[s1] got field_update', data)
    received['s1_field_updates'].append(data)

@s1.on('update_users')
def s1_update(data):
    print('[s1] got update_users', data)
    received['s1_update_users'].append(data)

@s2.event
def connect():
    print('[s2] connect')

@s2.on('field_update')
def s2_field(data):
    print('[s2] got field_update', data)
    received['s2_field_updates'].append(data)

@s2.on('update_users')
def s2_update(data):
    print('[s2] got update_users', data)
    received['s2_update_users'].append(data)

# Connect both (they will join rooms below)
try:
    s1.connect('http://localhost:5000')
    s2.connect('http://localhost:5000')
except Exception as e:
    raise SystemExit(f'Could not connect to server: {e}')

# Join room_ata from s1
s1.emit('join', {'ata_id': room_ata, 'nick': 'Tester1'})
# small delay
time.sleep(0.2)
# s2 joins same room
s2.emit('join', {'ata_id': room_ata, 'nick': 'Tester2'})

# Wait a bit to allow server to send initial state
time.sleep(0.5)

# s2 emits a field_update (simulate saving a field in the full-ata form)
payload = {'ata_id': room_ata, 'name': 'discursante_1', 'value': 'Automated Test Name'}
print('[s2] emitting field_update', payload)
s2.emit('field_update', payload)

# Wait for delivery
time.sleep(1.0)

# Validate
s1_received = any(d.get('name') == 'discursante_1' and d.get('value') == 'Automated Test Name' for d in received['s1_field_updates'])
s2_received = any(d.get('name') == 'discursante_1' and d.get('value') == 'Automated Test Name' for d in received['s2_field_updates'])

print('\nRESULTS:')
print('s1_received_field_update:', s1_received)
print('s2_received_field_update (loopback excluded):', s2_received)

# Clean up
s1.emit('leave', {'ata_id': room_ata, 'nick': 'Tester1'})
s2.emit('leave', {'ata_id': room_ata, 'nick': 'Tester2'})
s1.disconnect()
s2.disconnect()

if not s1_received:
    raise SystemExit('Test failed: s1 did not receive the field_update from s2')

print('Test passed')
