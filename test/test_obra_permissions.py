import os
import sys
import sqlite3
import pytest
# Make project root importable when running pytest directly
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

DB = 'database/atas.db'

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def login_as_obra(client):
    resp = client.post('/', data={'username': 'Obra', 'password': 'Obra1.33@2026'}, follow_redirects=True)
    assert resp.status_code in (200, 302)
    data = resp.get_data(as_text=True)
    assert ('Bem-vindo' in data) or ('Login realizado com sucesso' in data)


def insert_ata(conn, tipo, ala_id, data_str):
    cur = conn.execute("INSERT INTO atas (tipo, data, ala_id) VALUES (?, ?, ?)", (tipo, data_str, ala_id))
    ata_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.commit()
    return ata_id


def test_obra_permissions_and_pdf_export(client):
    # Ensure user exists
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    u = conn.execute('SELECT * FROM users WHERE username = ?', ('Obra',)).fetchone()
    assert u is not None, "Usuário Obra deve existir para o teste"
    ala_id = u['id']

    # Create a sacramental and a batismo for this ala
    sac_id = insert_ata(conn, 'sacramental', ala_id, '2026-03-01')
    conn.execute('INSERT INTO sacramental (ata_id, presidido) VALUES (?, ?)', (sac_id, 'Pres'))

    bat_id = insert_ata(conn, 'batismo', ala_id, '2026-03-02')
    conn.execute('INSERT INTO batismo (ata_id, dedicado, presidido, dirigido, batizados) VALUES (?, ?, ?, ?, ?)',
                 (bat_id, 'Dedicado', 'PresB', 'DirB', '[]'))
    conn.commit()

    try:
        # Login as Obra
        login_as_obra(client)

        # List all atas - should only show batismo
        resp = client.get('/atas')
        assert resp.status_code == 200
        text = resp.get_data(as_text=True)
        assert '2026-03-02' in text, 'Batismo deve aparecer na lista'
        assert '2026-03-01' not in text, 'Sacramental não deve aparecer para Obra'

        # Trying to visualize sacramental should be blocked
        resp = client.get(f'/ata/{sac_id}', follow_redirects=True)
        text = resp.get_data(as_text=True)
        assert ('Você não tem permissão' in text) or ('Você não tem acesso' in text)

        # Visualizar batismo should succeed
        resp = client.get(f'/ata/{bat_id}')
        assert resp.status_code == 200
        assert 'Batismo' in resp.get_data(as_text=True) or 'dedicado' in resp.get_data(as_text=True).lower()

        # Edit batismo (via editar_ata) should redirect to form
        resp = client.get(f'/ata/editar/{bat_id}', follow_redirects=True)
        assert resp.status_code == 200
        assert 'Criar Nova Ata' in resp.get_data(as_text=True) or 'Serviço Batismal' in resp.get_data(as_text=True)

        # Update batismo using form submission (set presidido)
        resp = client.post('/ata/form', data={'tipo':'batismo','data':'2026-03-02','editar':str(bat_id),'presidido':'NovoPres'}, follow_redirects=True)
        assert resp.status_code == 200
        # verify DB updated
        r = conn.execute('SELECT presidido FROM batismo WHERE ata_id=?',(bat_id,)).fetchone()
        assert r and r['presidido'] == 'NovoPres'

        # Export batismo PDF should be allowed
        resp = client.get(f'/ata/exportar_batismo/{bat_id}')
        assert resp.status_code == 200
        assert resp.headers.get('Content-Type', '').startswith('application/pdf')

        # Delete batismo via deletar_ata POST should be allowed
        resp = client.post('/deletar_ata', data={'ata_id': str(bat_id)}, follow_redirects=True)
        assert resp.status_code == 200
        text = resp.get_data(as_text=True)
        assert 'deletada com sucesso' in text or 'deletado' in text or 'deletada' in text

        # Export sacramental PDF should be blocked
        resp = client.get(f'/ata/exportar_sacramental/{sac_id}', follow_redirects=True)
        text = resp.get_data(as_text=True)
        assert ('Você não tem permissão' in text) or ('Você não tem acesso' in text)

    finally:
        # Cleanup test rows
        conn.execute('DELETE FROM sacramental WHERE ata_id = ?', (sac_id,))
        conn.execute('DELETE FROM batismo WHERE ata_id = ?', (bat_id,))
        conn.execute('DELETE FROM atas WHERE id IN (?, ?)', (sac_id, bat_id))
        conn.commit()
        conn.close()
