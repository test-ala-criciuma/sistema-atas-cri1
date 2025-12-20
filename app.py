import os
import io
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session, jsonify
from flask_socketio import SocketIO, join_room, leave_room, emit
from functools import wraps
import json
from datetime import datetime, timedelta
import calendar
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib import colors
import models as dbHandler
from functions.pdf_exporters import exportar_pdf_bytes, exportar_sacramental_bytes
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import traceback

app = Flask(__name__)

# Configuração do SocketIO para produção 
try:
    import eventlet
    socketio = SocketIO(app, 
                       cors_allowed_origins="*",
                       async_mode='eventlet')
except ImportError:
    socketio = SocketIO(app, 
                       cors_allowed_origins="*",
                       async_mode='threading')

#Secret key para RENDER
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-123')

# #Database do RENDER para produção
# if 'RENDER' in os.environ:
#     DB_PATH = "/opt/render/project/src/database/atas.db"
# else:
#     DB_PATH = "database/atas.db"



# Configuração do Secret Key e Database para desenvolvimento local :)
def get_db():
    conn = sqlite3.connect("database/atas.db")
    conn.row_factory = sqlite3.Row
    return conn

# Inicialização do banco de dados
def init_db():
    with app.app_context():
        conn = get_db()
        try:
            with open('database/schema_inicial.sql', 'r', encoding='utf-8') as f:
                sql_script = f.read()
            conn.executescript(sql_script)
            conn.commit()
            conn.close()
            print("Banco de dados inicializado com sucesso.")
        except Exception as e:
            print(f"Erro ao inicializar banco: {e}")

# Mensagem Autenticação no Login
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Por favor, faça login para acessar esta página.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# app.py

# Autenticação Login
def authenticate_user(username, password):
    conn = get_db()
    # 1. Busca o usuário APENAS pelo username (NUNCA pela senha)
    user = conn.execute(
        "SELECT * FROM users WHERE username = ?", 
        (username,)
    ).fetchone()
    conn.close()
    
    # 2. Se o usuário existir, verifica a senha contra o hash armazenado
    if user and check_password_hash(user['password'], password):
        return user
    return None # Retorna None se o usuário não for encontrado ou a senha não bater

# ==================================================================
# Rotas principais do sistema de atas
# ==================================================================

# Aba de discursantes recentes na criação de atas sacramentais
def get_discursantes_recentes():
    """Busca discursantes dos últimos 3 meses"""
    conn = get_db()
    
    # Data de 3 meses atrás
# -    tres_meses_atras = (datetime.now().replace(day=1) - timedelta(days=90)).strftime("%Y-%m-%d")
# +    # usar os últimos 90 dias (mais confiável que manipular day=1)
    tres_meses_atras = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    
    discursantes_recentes = conn.execute("""
        SELECT s.discursantes, a.data, s.tema
        FROM sacramental s 
        JOIN atas a ON s.ata_id = a.id 
        WHERE a.data >= ? AND a.tipo = 'sacramental' AND a.ala_id = ?
        ORDER BY a.data DESC
    """, (tres_meses_atras, session['user_id'])).fetchall()
    
    # Processar discursantes
    todos_discursantes = []
    nomes_ja_adicionados = set()
    
    for row in discursantes_recentes:
        if row['discursantes']:
            try:
                discursantes_lista = json.loads(row['discursantes'])
                for discursante in discursantes_lista:
                    if discursante and discursante.strip():
                        nome_limpo = discursante.strip()
                        # Evitar duplicatas
                        if nome_limpo not in nomes_ja_adicionados:
                            # Formatar data para exibição
                            data_obj = datetime.strptime(row['data'], "%Y-%m-%d")
                            data_formatada = data_obj.strftime("%d/%m/%Y")
                            
                            todos_discursantes.append({
                                'nome': nome_limpo,
                                'data': data_formatada
                            })
                            nomes_ja_adicionados.add(nome_limpo)
            except json.JSONDecodeError:
                continue
    
    # Limitar a 20 discursantes mais recentes
    return todos_discursantes[:20]


# Próxima reunião sacramental automática na página inicial
def get_proxima_reuniao_sacramental():
    """Encontra a data da próxima reunião sacramental"""
    hoje = datetime.now().date()
    
    # Encontrar próximo domingo
    dias_para_domingo = (6 - hoje.weekday()) % 7
    if dias_para_domingo == 0:  # Se hoje é domingo
        proximo_domingo = hoje
    else:
        proximo_domingo = hoje + timedelta(days=dias_para_domingo)
    
    # Verificar se já existe ata para esta data
    conn = get_db()
    ata_existente = conn.execute(
        "SELECT * FROM atas WHERE data = ? AND tipo = 'sacramental'", 
        (proximo_domingo.strftime("%Y-%m-%d"),)
    ).fetchone()
    
    # Formatar data em português
    data_formatada = proximo_domingo.strftime("%d/%m/%Y")
    
    if ata_existente:
        return {
            'data': proximo_domingo.strftime("%Y-%m-%d"),
            'data_formatada': data_formatada,
            'ata_existente': True,
            'id': ata_existente['id']
        }
    else:
        return None

# NOVA FUNÇÃO
def get_temas_recentes():
    """Busca temas dos últimos 3 meses"""
    conn = get_db()
    
    # Data de 90 dias atrás
    tres_meses_atras = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
    
    temas_recentes = conn.execute("""
        SELECT DISTINCT s.tema, a.data 
        FROM sacramental s 
        JOIN atas a ON s.ata_id = a.id 
        WHERE date(a.data) >= date(?) 
          AND a.tipo = 'sacramental' 
          AND a.ala_id = ? 
          AND s.tema IS NOT NULL 
          AND TRIM(s.tema) <> ''
        ORDER BY a.data DESC
        LIMIT 10
    """, (tres_meses_atras, session['user_id'])).fetchall()
    
    temas_formatados = []
    for tema in temas_recentes:
        if tema['tema']:
            data_obj = datetime.strptime(tema['data'], "%Y-%m-%d")
            data_formatada = data_obj.strftime("%d/%m/%Y")
            temas_formatados.append({
                'tema': tema['tema'],
                'data': data_formatada
            })
    
    conn.close()
    return temas_formatados[:10]

def get_hinos_recentes():
    """Busca hinos tocados nos últimos 2 meses, agrupados por data."""
    conn = get_db()
    
    # Data de 60 dias atrás (aproximadamente 2 meses)
    dois_meses_atras = (datetime.now() - timedelta(days=60)).strftime("%Y-%m-%d")
    
    # Selecionar data e todos os campos de hino
    hinos_recentes_raw = conn.execute("""
        SELECT a.data, s.hinos, s.hino_sacramental, s.hino_intermediario
        FROM sacramental s
        JOIN atas a ON s.ata_id = a.id
        WHERE date(a.data) >= date(?)
          AND a.tipo = 'sacramental'
          AND a.ala_id = ?
        ORDER BY a.data DESC
        LIMIT 10
    """, (dois_meses_atras, session['user_id'])).fetchall()

    hinos_por_data = {}

    for row in hinos_recentes_raw:
        data_obj = datetime.strptime(row['data'], "%Y-%m-%d")
        data_formatada = data_obj.strftime("%d/%m/%Y")

        hinos_lista = []

        # Adiciona Hinos de Abertura e Encerramento (coluna 'hinos' é um JSON array [abertura, encerramento])
        try:
            hinos_json = json.loads(row['hinos'] or '[]')
            if len(hinos_json) > 0 and hinos_json[0] and hinos_json[0].strip(): hinos_lista.append({'tipo': 'Abertura', 'nome': hinos_json[0].strip()})
            if len(hinos_json) > 1 and hinos_json[1] and hinos_json[1].strip(): hinos_lista.append({'tipo': 'Encerramento', 'nome': hinos_json[1].strip()})
        except json.JSONDecodeError: pass

        # Adiciona Hino Sacramental e Intermediário
        if row['hino_sacramental'] and row['hino_sacramental'].strip(): hinos_lista.append({'tipo': 'Sacramental', 'nome': row['hino_sacramental'].strip()})
        if row['hino_intermediario'] and row['hino_intermediario'].strip(): hinos_lista.append({'tipo': 'Intermediário', 'nome': row['hino_intermediario'].strip()})

        if hinos_lista and data_formatada not in hinos_por_data:
            hinos_por_data[data_formatada] = {'data': data_formatada, 'hinos': hinos_lista}
            
    conn.close()
    return list(hinos_por_data.values())[:10]

# Configuração do Rate Limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri="memory://",  # Use memória para desenvolvimento. Em produção, use Redis ou Memcached.
    default_limits=["200 per day", "50 per hour"]
)

# Rota de Login de Usuário
@app.route('/', methods=['GET', 'POST'])
@limiter.limit("5 per minute", methods=["POST"]) # error="Muitas tentativas de login. Tente novamente em um minuto.")
def login():
    # If user is already logged in, redirect to index
    if session.get('logged_in'):
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        if not username or not password:
            flash('Por favor, preencha todos os campos.', 'error')
            return render_template('login.html')
        
        user = authenticate_user(username, password)
        
        if user:
            session['logged_in'] = True
            session['username'] = user['username']
            session['user_id'] = user['id']
            flash(f'Login realizado com sucesso! Bem-vindo, {user["username"]}.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Credenciais inválidas. Por favor, tente novamente.', 'error')
    
    return render_template('login.html')

# Rota de Logout de Usuário
@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'success')
    return redirect(url_for('login'))

# ==================================================================
# Rotas de Configurações
# ==================================================================

# Rota para configurações com clonagem automática de templates padrão
@app.route("/configuracoes")
@login_required
def configuracoes():
    conn = get_db()
    ala_id = session['user_id']

    # 1. Buscar templates da ala logada
    templates_row = conn.execute("SELECT * FROM templates WHERE ala_id = ?", (ala_id,)).fetchall()
    
    # 2. LÓGICA DE CLONAGEM: Se não houver templates para esta ala, copia os padrões (ala_id = 0)
    if not templates_row:
        modelos_mestres = conn.execute("SELECT * FROM templates WHERE ala_id = 0").fetchall()
        for modelo in modelos_mestres:
            conn.execute("""
                INSERT INTO templates (
                    ala_id, tipo_template, nome, boas_vindas, desobrigacoes, apoios, 
                    confirmacoes_batismo, apoio_membro_novo, bencao_crianca, 
                    sacramento, mensagens, live, encerramento
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ala_id, modelo['tipo_template'], modelo['nome'], modelo['boas_vindas'], 
                modelo['desobrigacoes'], modelo['apoios'], modelo['confirmacoes_batismo'], 
                modelo['apoio_membro_novo'], modelo['bencao_crianca'], modelo['sacramento'], 
                modelo['mensagens'], modelo['live'], modelo['encerramento']
            ))
        conn.commit()
        # Refaz a busca agora com os templates clonados
        templates_row = conn.execute("SELECT * FROM templates WHERE ala_id = ?", (ala_id,)).fetchall()

    templates = [dict(t) for t in templates_row]

    # 3. Buscar informações da unidade (Sua lógica original preservada)
    unidade_row = conn.execute(
        "SELECT * FROM unidades WHERE ala_id = ?",
        (ala_id,)
    ).fetchone()

    if unidade_row:
        unidade = dict(unidade_row)
        primeiro = unidade.get('primeiro_conselheiro') or ''
        segundo = unidade.get('segundo_conselheiro') or ''

        if not primeiro and not segundo:
            cons_raw = unidade.get('conselheiros') or ''
            if cons_raw:
                try:
                    parsed = json.loads(cons_raw)
                    if isinstance(parsed, list):
                        primeiro = parsed[0] if len(parsed) > 0 else ''
                        segundo = parsed[1] if len(parsed) > 1 else ''
                except Exception:
                    if '|' in cons_raw:
                        parts = [p.strip() for p in cons_raw.split('|', 1)]
                        primeiro = parts[0]
                        segundo = parts[1] if len(parts) > 1 else ''
                    elif '\n' in cons_raw:
                        parts = [p.strip() for p in cons_raw.split('\n', 1)]
                        primeiro = parts[0]
                        segundo = parts[1] if len(parts) > 1 else ''
                    else:
                        primeiro = cons_raw.strip()

        unidade['primeiro_conselheiro'] = primeiro
        unidade['segundo_conselheiro'] = segundo
    else:
        unidade = {}

    # 4. Buscar estatísticas (Sua lógica original preservada)
    total_atas = conn.execute(
        "SELECT COUNT(*) FROM atas WHERE ala_id = ?",
        (ala_id,)
    ).fetchone()[0]

    atas_sacramentais = conn.execute(
        "SELECT COUNT(*) FROM atas WHERE ala_id = ? AND tipo = 'sacramental'",
        (ala_id,)
    ).fetchone()[0]

    atas_batismo = conn.execute(
        "SELECT COUNT(*) FROM atas WHERE ala_id = ? AND tipo = 'batismo'",
        (ala_id,)
    ).fetchone()[0]

    mes_atual = datetime.now().strftime("%Y-%m")
    atas_mes = conn.execute(
        "SELECT COUNT(*) FROM atas WHERE ala_id = ? AND strftime('%Y-%m', data) = ?",
        (ala_id, mes_atual)
    ).fetchone()[0]

    conn.close()

    return render_template(
        "configuracoes.html",
        templates=templates,
        unidade=unidade,
        total_atas=total_atas,
        atas_sacramentais=atas_sacramentais,
        atas_batismo=atas_batismo,
        atas_mes=atas_mes
    )

# Rota para salvar configurações da ala
@app.route("/configuracoes/ala/salvar", methods=["POST"])
@login_required
def salvar_configuracoes_ala():
    conn = get_db()

    nome_ala = request.form.get("nome_ala")
    bispo = request.form.get("bispo")
    primeiro_conselheiro = request.form.get("primeiro_conselheiro")
    segundo_conselheiro = request.form.get("segundo_conselheiro")
    horario = request.form.get("horario")
    # O template atualmente envia um campo 'estaca' (string), mas a tabela usa estaca_id.
    # Para evitar alterações de schema/ID incorretos, não alteraremos estaca_id aqui.
    # Se quiser atualizar estaca_id a partir do front, eu posso ajustar depois.
    
    # Verificar se já existe registro para esta ala
    unidade_existente = conn.execute(
        "SELECT * FROM unidades WHERE ala_id = ?",
        (session['user_id'],)
    ).fetchone()

    if unidade_existente:
        # Atualizar - não tocar em estaca_id para evitar inconsistências
        conn.execute("""
            UPDATE unidades
            SET nome = ?, bispo = ?, primeiro_conselheiro = ?, segundo_conselheiro = ?, horario = ?
            WHERE ala_id = ?
        """, (nome_ala, bispo, primeiro_conselheiro, segundo_conselheiro, horario, session['user_id']))
    else:
        # Inserir - estaca_id usará valor default definido no schema (DEFAULT 1)
        conn.execute("""
            INSERT INTO unidades (ala_id, nome, bispo, primeiro_conselheiro, segundo_conselheiro, horario)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session['user_id'], nome_ala, bispo, primeiro_conselheiro, segundo_conselheiro, horario))

    conn.commit()
    conn.close()

    flash("Configurações da ala salvas com sucesso!", "success")
    return redirect(url_for("configuracoes"))

# Rota para editar template
@app.route("/configuracoes/template/<int:template_id>")
@login_required
def editar_template(template_id):
    conn = get_db()
    template = conn.execute(
        "SELECT * FROM templates WHERE id = ?", 
        (template_id,)
    ).fetchone()
    
    if template:
        template = dict(template)
        conn.close()
        return render_template("_editar_template.html", template=template)
    else:
        conn.close()
        return "Template não encontrado", 404

# Rota para salvar template
@app.route("/configuracoes/template/<int:template_id>/salvar", methods=["POST"])
@login_required
def salvar_template(template_id):
    conn = get_db()
    try:
        # Mapeamento exato com o seu novo SCHEMA do SQL
        conn.execute("""
            UPDATE templates SET
                nome = ?, boas_vindas = ?, desobrigacoes = ?, apoios = ?, 
                confirmacoes_batismo = ?, apoio_membro_novo = ?, bencao_crianca = ?,
                sacramento = ?, mensagens = ?, live = ?, encerramento = ?
            WHERE id = ? AND ala_id = ?
        """, (
            request.form.get('nome'), request.form.get('boas_vindas'),
            request.form.get('desobrigacoes'), request.form.get('apoios'),
            request.form.get('confirmacoes_batismo'), request.form.get('apoio_membro_novo'),
            request.form.get('bencao_crianca'), request.form.get('sacramento'),
            request.form.get('mensagens'), request.form.get('live'),
            request.form.get('encerramento'), template_id, session['user_id']
        ))
        
        conn.commit()
        flash("Template atualizado com sucesso!", "success")
    except Exception as e:
        flash(f"Erro ao salvar: {e}", "error")
    finally:
        conn.close()
    return redirect(url_for("configuracoes"))

# Rota para criar novo template
@app.route("/configuracoes/template/criar", methods=["POST"])
@login_required
def criar_template():
    conn = get_db()
    ala_id = session.get('user_id')
    
    try:
        nome = request.form.get('nome')
        tipo_template = request.form.get('tipo_template') # 1=Sacramental, 2=Batismo
        
        # 1. VERIFICAÇÃO DE DUPLICIDADE: 
        # Busca se já existe um template desse TIPO para essa ALA
        existente = conn.execute(
            "SELECT id FROM templates WHERE tipo_template = ? AND ala_id = ?", 
            (tipo_template, ala_id)
        ).fetchone()

        if existente:
            # Se já existe, apenas redirecionamos ou avisamos. 
            # O ideal é que o usuário use a rota de SALVAR para editar.
            flash("Já existe um template para este tipo. Por favor, edite o existente.", "warning")
            return redirect(url_for("configuracoes"))

        # 2. INSERÇÃO (Caso seja realmente novo)
        conn.execute("""
            INSERT INTO templates (
                tipo_template, ala_id, nome, boas_vindas, desobrigacoes, apoios, 
                confirmacoes_batismo, apoio_membro_novo, bencao_crianca, 
                sacramento, mensagens, live, encerramento
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tipo_template, ala_id, nome,
            "Bom dia irmãos...", "É proposto...", "O(a) irmão(o)...",
            "O(a) irmão(o)...", "O(a) irmão(o)...", "Gostaríamos...",
            "Passaremos...", "Agradecemos...", "Gostaria...", "Agradecemos..."
        ))
        
        conn.commit()
        flash("Novo template criado com sucesso!", "success")
    except Exception as e:
        print(f"Erro: {e}")
        flash("Erro ao criar template", "error")
    finally:
        conn.close()
    return redirect(url_for("configuracoes"))
   
# Rota para apagar template
@app.route("/configuracoes/template/<int:template_id>/apagar", methods=["POST"])
@login_required
def apagar_template(template_id):
    conn = get_db()
    
    try:
        # Verificar se o template existe
        template = conn.execute(
            "SELECT * FROM templates WHERE id = ?", 
            (template_id,)
        ).fetchone()
        
        if not template:
            return jsonify({
                'success': False,
                'message': 'Template não encontrado'
            }), 404
        
        # Não permitir apagar todos os templates - manter pelo menos um de cada tipo
        templates_restantes = conn.execute(
            "SELECT COUNT(*) FROM templates WHERE tipo_template = ?", 
            (template['tipo_template'],)
        ).fetchone()[0]
        
        if templates_restantes <= 1:
            return jsonify({
                'success': False,
                'message': 'Não é possível apagar o último template deste tipo'
            }, 400)
        
        # Apagar o template
        conn.execute("DELETE FROM templates WHERE id = ?", (template_id,))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Template apagado com sucesso!'
        })
        
    except Exception as e:
        conn.close()
        print(f"Erro ao apagar template: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno ao apagar template'
        }), 500


# Página Inicial com lista de atas
@app.route('/index')
@login_required
def index():
    conn = get_db()
    
    # Gerar lista de meses para o seletor EM PORTUGUÊS
    meses = []
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # Nomes dos meses em português
    meses_ptbr = [
        '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    
    for month in range(1, 13):
        month_name = meses_ptbr[month]
        month_value = f"{current_year}-{month:02d}"
        meses.append({
            'value': month_value,
            'nome': f"{month_name} {current_year}"
        })
    
    # Formato do mês atual para seleção automática
    mes_atual = datetime.now().strftime("%Y-%m")
    mes_nome = meses_ptbr[datetime.now().month] + " " + str(datetime.now().year)  # CORREÇÃO: Definir mes_nome
    
    # Carregar atas do mês atual da ala do usuário
    atas = conn.execute(
        "SELECT * FROM atas WHERE strftime('%Y-%m', data) = ? AND ala_id = ? ORDER BY data DESC", 
        (mes_atual, session['user_id'])
    ).fetchall()
    
    # Buscar próxima reunião sacramental
    proxima_reuniao = get_proxima_reuniao_sacramental()
    
    return render_template(
        "index.html",
        meses=meses,
        mes_atual=mes_atual,
        mes_nome=mes_nome,  # AGORA ESTÁ DEFINIDA
        atas=atas,
        proxima_reuniao=proxima_reuniao
    )

# Rota para visualizar todas as atas
@app.route("/atas")
@login_required
def listar_todas_atas():
    conn = get_db()
    
    # Buscar todas as atas da ala, ordenadas da mais recente para a mais antiga
    atas = conn.execute("""
        SELECT a.*, s.tema 
        FROM atas a 
        LEFT JOIN sacramental s ON a.id = s.ata_id 
        WHERE a.ala_id = ? 
        ORDER BY a.data DESC
    """, (session['user_id'],)).fetchall()
    
    # Buscar discursantes dos últimos 3 meses
    tres_meses_atras = (datetime.now().replace(day=1) - timedelta(days=90)).strftime("%Y-%m-%d")
    
    discursantes_recentes = conn.execute("""
        SELECT s.discursantes, a.data, s.tema
        FROM sacramental s 
        JOIN atas a ON s.ata_id = a.id 
        WHERE a.data >= ? AND a.tipo = 'sacramental' AND a.ala_id = ?
        ORDER BY a.data DESC
    """, (tres_meses_atras, session['user_id'])).fetchall()
    
    # Processar discursantes
    todos_discursantes = []
    nomes_ja_adicionados = set()
    
    for row in discursantes_recentes:
        if row['discursantes']:
            try:
                discursantes_lista = json.loads(row['discursantes'])
                for discursante in discursantes_lista:
                    if discursante and discursante.strip():
                        nome_limpo = discursante.strip()
                        if nome_limpo not in nomes_ja_adicionados:
                            data_obj = datetime.strptime(row['data'], "%Y-%m-%d")
                            data_formatada = data_obj.strftime("%d/%m/%Y")
                            
                            todos_discursantes.append({
                                'nome': nome_limpo,
                                'data': data_formatada,
                                'tema': row['tema'] or 'Sem tema definido'
                            })
                            nomes_ja_adicionados.add(nome_limpo)
            except json.JSONDecodeError:
                continue
    
    # Buscar temas dos últimos 90 dias, ignorando temas nulos/vazios
    temas_recentes = conn.execute("""
        SELECT s.tema, a.data 
        FROM sacramental s 
        JOIN atas a ON s.ata_id = a.id 
        WHERE date(a.data) >= date(?) 
          AND a.tipo = 'sacramental' 
          AND a.ala_id = ? 
          AND s.tema IS NOT NULL 
          AND TRIM(s.tema) <> ''
        ORDER BY a.data DESC
    """, (tres_meses_atras, session['user_id'])).fetchall()

    # DEBUG: mostrar o que foi retornado
    print("DEBUG temas_recentes (count):", len(temas_recentes))
    for t in temas_recentes[:20]:
        print("DEBUG tema row:", dict(t))

    temas_formatados = []
    for tema in temas_recentes:
        if tema['tema']:
            data_obj = datetime.strptime(tema['data'], "%Y-%m-%d")
            data_formatada = data_obj.strftime("%d/%m/%Y")
            temas_formatados.append({
                'tema': tema['tema'],
                'data': data_formatada
            })
    
    conn.close()
    
    return render_template(
        "todas_atas.html",
        atas=atas,
        discursantes_recentes=todos_discursantes[:20],
        temas_recentes=temas_recentes,
        hinos_recentes=get_hinos_recentes()
    )

# Rota para editar uma ata existente
@app.route("/ata/editar/<int:ata_id>")
@login_required
def editar_ata(ata_id):
    """Rota para editar uma ata existente"""
    conn = get_db()
    ata = conn.execute(
        "SELECT * FROM atas WHERE id=? AND ala_id=?", 
        (ata_id, session['user_id'])
    ).fetchone()
    
    if not ata:
        flash("Ata não encontrada ou você não tem permissão para editá-la.", "error")
        return redirect(url_for('index'))
    
    # Redireciona para o formulário apropriado com os dados existentes
    if ata["tipo"] == "sacramental":
        return redirect(url_for("form_ata", tipo="sacramental", data=ata["data"], editar=ata_id))
    else:
        return redirect(url_for("form_ata", tipo="batismo", data=ata["data"], editar=ata_id))

# Rota para excluir uma ata
@app.route("/ata/excluir/<int:ata_id>")
@login_required
def excluir_ata(ata_id: int):
    """Rota para excluir uma ata"""
    conn = get_db()
    
    # Primeiro, exclui os detalhes específicos
    ata = conn.execute("SELECT * FROM atas WHERE id=?", (ata_id,)).fetchone()
    if ata:
        if ata["tipo"] == "sacramental":
            conn.execute("DELETE FROM sacramental WHERE ata_id=?", (ata_id,))
        else:
            conn.execute("DELETE FROM batismo WHERE ata_id=?", (ata_id,))
        
        # Depois exclui a ata principal
        conn.execute("DELETE FROM atas WHERE id=?", (ata_id,))
        conn.commit()
        flash("Ata excluída com sucesso!", "success")
    else:
        flash("Ata não encontrada", "error")
    
    # Always return a redirect response
    return redirect(url_for("index"))

# Rota para listar atas por mês
@app.route("/atas/mes/<string:mes>")
@login_required
def listar_atas_mes(mes):
    conn = get_db()
    
    try:
        # Validar formato do mês (YYYY-MM)
        datetime.strptime(mes, "%Y-%m")
        
        atas = conn.execute(
            "SELECT * FROM atas WHERE strftime('%Y-%m', data) = ? AND ala_id = ? ORDER BY data DESC", 
            (mes, session['user_id'])
        ).fetchall()
        
        # Formatar nome do mês para exibição EM PORTUGUÊS
        meses_ptbr = [
            '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        data_mes = datetime.strptime(mes, "%Y-%m")
        mes_nome = meses_ptbr[data_mes.month] + " " + str(data_mes.year)
        
        return render_template("_atas_list.html", 
                             atas=atas, 
                             mes_selecionado_nome=mes_nome)
    
    except ValueError:
        return "<div class='info-card'>Mês inválido.</div>"

# Filtro de template para carregar listas JSON
@app.template_filter('loads')
def json_loads_filter(s: str) -> list:
    """Template filter to parse JSON strings - always returns a list"""
    if not s:
        return []
    try:
        result = json.loads(s)
        # Ensure we always return a list, even if JSON contains other types
        if isinstance(result, list):
            return result
        else:
            return [result] if result is not None else []
    except (json.JSONDecodeError, TypeError, ValueError):
        return []

# Rota para criar nova ata
@app.route("/ata/nova", methods=["GET", "POST"])
@login_required
def nova_ata():
    if request.method == "POST":
        tipo = request.form.get("tipo")
        data = request.form.get("data")
        
        # Validação básica
        if not tipo or not data:
            flash("Erro: Tipo e data são obrigatórios", "error")
            return render_template("nova_ata.html")
            
        # Validação de data - APENAS VERIFICA SE É UMA DATA VÁLIDA
        try:
            datetime.strptime(data, "%Y-%m-%d")
        except ValueError:
            flash("Erro: Data inválida", "error")
            return render_template("nova_ata.html")
            
        return redirect(url_for("form_ata", tipo=tipo, data=data))
    
    # Data padrão: próximo domingo ou hoje se for domingo
    hoje = datetime.now().date()
    dias_para_domingo = (6 - hoje.weekday()) % 7
    if dias_para_domingo == 0:  # Se hoje é domingo
        data_padrao = hoje.strftime("%Y-%m-%d")
    else:
        data_padrao = (hoje + timedelta(days=dias_para_domingo)).strftime("%Y-%m-%d")
    
    return render_template("nova_ata.html", data_padrao=data_padrao)

# Rota para formulário de ata (criação/edição)
@app.route("/ata/form", methods=["GET", "POST"])
@login_required
def form_ata():
    if request.method == "POST":
        tipo = request.form.get("tipo")
        data = request.form.get("data")
        ata_id_editar = request.form.get("editar")
        
        # Validação básica
        if not tipo or not data:
            flash("Erro: Tipo e data são obrigatórios", "error")
            return redirect(url_for('nova_ata'))
        
        # Validação de data
        try:
            datetime.strptime(data, "%Y-%m-%d")
        except ValueError:
            flash("Erro: Data inválida", "error")
            return redirect(url_for('nova_ata'))
        
        conn = get_db()
        
        if ata_id_editar:
            # Modo edição - verificar se a ata pertence à ala do usuário
            ata_existente = conn.execute(
                "SELECT * FROM atas WHERE id = ? AND ala_id = ?", 
                (ata_id_editar, session['user_id'])
            ).fetchone()
            
            if not ata_existente:
                flash("Você não tem permissão para editar esta ata.", "error")
                return redirect(url_for('index'))
            
            # Atualiza a ata existente
            conn.execute("UPDATE atas SET tipo=?, data=? WHERE id=?", (tipo, data, ata_id_editar))
            ata_id = ata_id_editar
        else:
            # Modo criação - insere nova ata com ala_id
            conn.execute(
                "INSERT INTO atas (tipo, data, ala_id) VALUES (?, ?, ?)", 
                (tipo, data, session['user_id'])
            )
            ata_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

        if tipo == "sacramental":
            discursantes = request.form.getlist("discursantes[]")
            # Filtrar discursantes vazios
            discursantes = [d for d in discursantes if d and d.strip()]
            
            anuncios = request.form.getlist("anuncios[]")
            # Filtrar anúncios vazios
            anuncios = [a for a in anuncios if a and a.strip()]
            
            detalhes = {
                "presidido": request.form.get("presidido", ""),
                "dirigido": request.form.get("dirigido", ""),
                "recepcionistas": request.form.get("recepcionistas", ""),
                "tema": request.form.get("tema", ""), 
                "pianista": request.form.get("pianista", ""),
                "regente_musica": request.form.get("regente_musica", ""),
                "reconhecemos_presenca": request.form.get("reconhecemos_presenca", ""),  # NOVO
                "anuncios": anuncios,
                "hino_abertura": request.form.get("hino_abertura", ""),
                "oracao_abertura": request.form.get("oracao_abertura", ""),
                "desobrigacoes": request.form.get("desobrigacoes", ""),  # NOVO
                "apoios": request.form.get("apoios", ""),  # NOVO
                "confirmacoes_batismo": request.form.get("confirmacoes_batismo", ""),  # NOVO
                "apoio_membros": request.form.get("apoio_membros", ""),  # NOVO
                "bencao_criancas": request.form.get("bencao_criancas", ""),  # NOVO
                "hino_sacramental": request.form.get("hino_sacramental", ""),
                "hino_intermediario": request.form.get("hino_intermediario", ""),
                "ultimo_discursante": request.form.get("ultimo_discursante", ""),  # NOVO
                "hino_encerramento": request.form.get("hino_encerramento", ""),
                "oracao_encerramento": request.form.get("oracao_encerramento", ""),
                "discursantes": discursantes
            }
            
            if ata_id_editar:
                # Atualiza registro existente COM TEMA
                conn.execute("""
                    UPDATE sacramental 
                    SET presidido=?, dirigido=?, recepcionistas=?, pianista=?, regente_musica=?, 
                        reconhecemos_presenca=?, anuncios=?, hinos=?, oracoes=?, discursantes=?, 
                        hino_sacramental=?, hino_intermediario=?, desobrigacoes=?, apoios=?, 
                        confirmacoes_batismo=?, apoio_membros=?, bencao_criancas=?, ultimo_discursante=?, tema=?
                    WHERE ata_id=?
                """, (
                    detalhes["presidido"], 
                    detalhes["dirigido"],
                    detalhes["recepcionistas"],
                    detalhes["pianista"],
                    detalhes["regente_musica"],
                    detalhes["reconhecemos_presenca"],
                    json.dumps(detalhes["anuncios"]),
                    json.dumps([detalhes["hino_abertura"], detalhes["hino_encerramento"]]), 
                    json.dumps([detalhes["oracao_abertura"], detalhes["oracao_encerramento"]]), 
                    json.dumps(detalhes["discursantes"]),
                    detalhes["hino_sacramental"],
                    detalhes["hino_intermediario"],
                    detalhes["desobrigacoes"],
                    detalhes["apoios"],
                    detalhes["confirmacoes_batismo"],
                    detalhes["apoio_membros"],
                    detalhes["bencao_criancas"],
                    detalhes["ultimo_discursante"],
                    detalhes["tema"],  # ← ADICIONAR AQUI
                    ata_id
                ))
            else:
                # Insere novo registro COM TEMA
                conn.execute("""
                    INSERT INTO sacramental (ata_id, presidido, dirigido, recepcionistas, pianista, regente_musica, 
                        reconhecemos_presenca, anuncios, hinos, oracoes, discursantes, hino_sacramental, hino_intermediario,
                        desobrigacoes, apoios, confirmacoes_batismo, apoio_membros, bencao_criancas, ultimo_discursante, tema) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ata_id, 
                    detalhes["presidido"], 
                    detalhes["dirigido"],
                    detalhes["recepcionistas"],
                    detalhes["pianista"],
                    detalhes["regente_musica"],
                    detalhes["reconhecemos_presenca"],
                    json.dumps(detalhes["anuncios"]),
                    json.dumps([detalhes["hino_abertura"], detalhes["hino_encerramento"]]), 
                    json.dumps([detalhes["oracao_abertura"], detalhes["oracao_encerramento"]]), 
                    json.dumps(detalhes["discursantes"]),
                    detalhes["hino_sacramental"],
                    detalhes["hino_intermediario"],
                    detalhes["desobrigacoes"],
                    detalhes["apoios"],
                    detalhes["confirmacoes_batismo"],
                    detalhes["apoio_membros"],
                    detalhes["bencao_criancas"],
                    detalhes["ultimo_discursante"],
                    detalhes["tema"]  # ← ADICIONAR AQUI
                ))
        
        elif tipo == "batismo":
            batizados = request.form.getlist("batizados[]")
            # Filtrar batizados vazios
            batizados = [b for b in batizados if b and b.strip()]
            
            detalhes = {
                "presidido": request.form.get("presidido", ""),
                "dirigido": request.form.get("dirigido", ""),
                "dedicado": request.form.get("dedicado", ""),
                "testemunha1": request.form.get("testemunha1", ""),
                "testemunha2": request.form.get("testemunha2", ""),
                "batizados": batizados
            }
            
            if ata_id_editar:
                # Atualiza registro existente
                conn.execute("""
                    UPDATE batismo 
                    SET dedicado=?, presidido=?, dirigido=?, batizados=?, testemunha1=?, testemunha2=? 
                    WHERE ata_id=?
                """, (
                    detalhes["dedicado"], 
                    detalhes["presidido"], 
                    detalhes["dirigido"], 
                    json.dumps(detalhes["batizados"]), 
                    detalhes["testemunha1"], 
                    detalhes["testemunha2"], 
                    ata_id
                ))
            else:
                # Insere novo registro
                conn.execute("""
                    INSERT INTO batismo (ata_id, dedicado, presidido, dirigido, batizados, testemunha1, testemunha2) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    ata_id, 
                    detalhes["dedicado"], 
                    detalhes["presidido"], 
                    detalhes["dirigido"], 
                    json.dumps(detalhes["batizados"]), 
                    detalhes["testemunha1"], 
                    detalhes["testemunha2"]
                ))
        
        conn.commit()
        flash("Ata salva com sucesso!", "success")
        return redirect(url_for("visualizar_ata", ata_id=ata_id))

    # GET request
    tipo = request.args.get("tipo")
    data = request.args.get("data")
    editar = request.args.get("editar")
    
    # Lógica para carregar dados existentes se estiver editando
    dados_existentes = {}
    if editar:
        conn = get_db()
        if tipo == "sacramental":
            dados = conn.execute("SELECT * FROM sacramental WHERE ata_id=?", (editar,)).fetchone()
            if dados:
                dados_existentes = dict(dados)
                # Converter JSON strings de volta para objetos
                if dados_existentes.get('hinos'):
                    hinos = json.loads(dados_existentes['hinos'])
                    dados_existentes['hino_abertura'] = hinos[0] if len(hinos) > 0 else ''
                    dados_existentes['hino_encerramento'] = hinos[1] if len(hinos) > 1 else ''
                if dados_existentes.get('oracoes'):
                    oracoes = json.loads(dados_existentes['oracoes'])
                    dados_existentes['oracao_abertura'] = oracoes[0] if len(oracoes) > 0 else ''
                    dados_existentes['oracao_encerramento'] = oracoes[1] if len(oracoes) > 1 else ''
                if dados_existentes.get('discursantes'):
                    dados_existentes['discursantes'] = json.loads(dados_existentes['discursantes'])
                if dados_existentes.get('anuncios'):
                    dados_existentes['anuncios'] = json.loads(dados_existentes['anuncios'])
        else:
            dados = conn.execute("SELECT * FROM batismo WHERE ata_id=?", (editar,)).fetchone()
            if dados:
                dados_existentes = dict(dados)
                if dados_existentes.get('batizados'):
                    dados_existentes['batizados'] = json.loads(dados_existentes['batizados'])
    
    if not tipo or not data:
        flash("Erro: Tipo e data são obrigatórios", "error")
        return redirect(url_for("nova_ata"))
    
    if tipo == "sacramental":
        dt = datetime.strptime(data, "%Y-%m-%d")
        primeiro_domingo = min([d for d in range(1, 8) if calendar.weekday(dt.year, dt.month, d) == 6])
        is_primeiro_domingo = dt.day == primeiro_domingo
        

        discursantes_recentes = get_discursantes_recentes() if not editar else []
        temas_recentes = get_temas_recentes() if not editar else []
        hinos_recentes = get_hinos_recentes() if not editar else []
        
        conn = get_db()
        unidade_row = conn.execute("SELECT * FROM unidades WHERE ala_id = ?", (session['user_id'],)).fetchone()
        estaca_row = None

        if unidade_row and unidade_row['estaca_id']:
            estaca_row = conn.execute("SELECT * FROM estacas WHERE id = ?", (unidade_row['estaca_id'],)).fetchone()

        unidade = dict(unidade_row) if unidade_row else {}
        estaca = dict(estaca_row) if estaca_row else {}

        return render_template("sacramental.html", 
                             primeiro=is_primeiro_domingo, 
                             data=data, 
                             editar=editar, 
                             dados=dados_existentes,
                             discursantes_recentes=discursantes_recentes,
                             temas_recentes=temas_recentes,
                             hinos_recentes=hinos_recentes,
                             unidade=unidade,
                             estaca=estaca)
    elif tipo == "batismo":
        return render_template("batismo.html", 
                             data=data, 
                             editar=editar, 
                             dados=dados_existentes)
    else:
        flash("Tipo de ata não reconhecido", "error")
        return redirect(url_for("nova_ata"))

# Rota para visualizar uma ata selecionada
@app.route("/ata/<int:ata_id>")
@login_required
def visualizar_ata(ata_id):
    conn = get_db()
    ata = conn.execute(
        "SELECT * FROM atas WHERE id=? AND ala_id=?", 
        (ata_id, session['user_id'])
    ).fetchone()
    
    if not ata:
        flash("Ata não encontrada ou você não tem permissão para visualizá-la.", "error")
        return redirect(url_for("index"))
        
    # Buscar template padrão para sacramental
    template = None
    if ata["tipo"] == "sacramental":
        # Tente diferentes formas de buscar o template
        template = conn.execute(
            "SELECT * FROM templates WHERE nome = 'Sacramental Padrão'"
        ).fetchone()
        
        if not template:
            template = conn.execute(
                "SELECT * FROM templates WHERE tipo_template = 1"
            ).fetchone()
        
        if template:
            template = dict(template)
            print(f"DEBUG: Template carregado - {template.get('nome', 'Sem nome')}")
    
    if ata["tipo"] == "sacramental":
        detalhes = conn.execute("SELECT * FROM sacramental WHERE ata_id=?", (ata_id,)).fetchone()
        if detalhes:
            # Converter para dicionário para facilitar o acesso
            detalhes_dict = dict(detalhes)
            if detalhes_dict.get('hinos'):
                try:
                    hinos = json.loads(detalhes_dict['hinos'])
                    detalhes_dict['hino_abertura'] = hinos[0] if len(hinos) > 0 else ''
                    detalhes_dict['hino_encerramento'] = hinos[1] if len(hinos) > 1 else ''
                except:
                    detalhes_dict['hino_abertura'] = ''
                    detalhes_dict['hino_encerramento'] = ''
                    
            if detalhes_dict.get('oracoes'):
                try:
                    oracoes = json.loads(detalhes_dict['oracoes'])
                    detalhes_dict['oracao_abertura'] = oracoes[0] if len(oracoes) > 0 else ''
                    detalhes_dict['oracao_encerramento'] = oracoes[1] if len(oracoes) > 1 else ''
                except:
                    detalhes_dict['oracao_abertura'] = ''
                    detalhes_dict['oracao_encerramento'] = ''
                    
            if detalhes_dict.get('discursantes'):
                try:
                    detalhes_dict['discursantes'] = json.loads(detalhes_dict['discursantes'])
                except:
                    detalhes_dict['discursantes'] = []
                    
            if detalhes_dict.get('anuncios'):
                try:
                    detalhes_dict['anuncios'] = json.loads(detalhes_dict['anuncios'])
                except:
                    detalhes_dict['anuncios'] = []
                    
            detalhes = detalhes_dict
        else:
            detalhes = {}
    else:
        detalhes = conn.execute("SELECT * FROM batismo WHERE ata_id=?", (ata_id,)).fetchone()
        if detalhes:
            detalhes_dict = dict(detalhes)
            if detalhes_dict.get('batizados'):
                try:
                    detalhes_dict['batizados'] = json.loads(detalhes_dict['batizados'])
                except:
                    detalhes_dict['batizados'] = []
            detalhes = detalhes_dict
        else:
            detalhes = {}
    
    # Ler os textos padrão dos convites (1º, 2º e 3º discursante)
    def _read_discursante_text(n):
        try:
            path_txt = os.path.join(app.root_path, "templates", "texts", f"discursante_{n}.txt")
            with open(path_txt, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            print(f"Aviso: não foi possível ler discursante_{n}.txt ->", e)
            return ""

    discursante_1_text = _read_discursante_text(1)
    discursante_2_text = _read_discursante_text(2)
    discursante_3_text = _read_discursante_text(3)

    conn.close()

    return render_template(
        "visualizar_ata.html",
        ata=ata,
        detalhes=detalhes,
        template=template,
        discursante_1_text=discursante_1_text,
        discursante_2_text=discursante_2_text,
        discursante_3_text=discursante_3_text
    )

# Rota para exportar ata como PDF simples
@app.route("/ata/exportar/<int:ata_id>")
@login_required
def exportar_pdf(ata_id):
    from functions.pdf_exporters import exportar_pdf_bytes
    
    conn = get_db() 
    try:
        # Usamos um cursor explícito para maior robustez
        cursor = conn.cursor() 
        
        # 1. Buscar a Ata
        cursor.execute(
            "SELECT * FROM atas WHERE id=? AND ala_id=?", 
            (ata_id, session['user_id'])
        )
        ata = cursor.fetchone()
        
        if not ata:
            raise ValueError("Ata não encontrada")
        
        ata = dict(ata)
        
        # =========================================================================
        # CORREÇÃO: Buscar o Template Padrão (ID 1), pois a tabela templates 
        # não possui a coluna ala_id.
        # =========================================================================
        cursor.execute(
            # Anteriormente: "SELECT * FROM templates WHERE ala_id=? LIMIT 1"
            "SELECT * FROM templates WHERE id=1 LIMIT 1" # Agora busca o template padrão (ID 1)
        )
        template = cursor.fetchone()
        
        if template:
            template = dict(template)
        else:
            template = {}
        
        
        # 4. Buscar detalhes conforme tipo (Lógica de deserialização mantida)
        if ata["tipo"] == "sacramental":
            cursor.execute("SELECT * FROM sacramental WHERE ata_id=?", (ata_id,))
            detalhes = cursor.fetchone()
            
            if detalhes:
                detalhes_dict = dict(detalhes)
                
                # Deserialização de JSON
                keys_to_load = ['hinos', 'oracoes', 'discursantes', 'anuncios', 
                                'desobrigacoes', 'apoios', 'confirmacoes_batismo', 
                                'apoio_membro_novo', 'bencao_crianca']

                for key in keys_to_load:
                    if detalhes_dict.get(key) and isinstance(detalhes_dict[key], str):
                        try:
                            detalhes_dict[key] = json.loads(detalhes_dict[key])
                        except:
                            if key in ['discursantes', 'anuncios', 'desobrigacoes', 'apoios', 'confirmacoes_batismo', 'apoio_membro_novo', 'bencao_crianca']:
                                detalhes_dict[key] = []
                            pass

                # Tratamento específico de hinos e orações
                if isinstance(detalhes_dict.get('hinos'), list):
                    hinos = detalhes_dict['hinos']
                    detalhes_dict['hino_abertura'] = hinos[0] if len(hinos) > 0 else ''
                    detalhes_dict['hino_encerramento'] = hinos[1] if len(hinos) > 1 else ''
                    
                if isinstance(detalhes_dict.get('oracoes'), list):
                    oracoes = detalhes_dict['oracoes']
                    detalhes_dict['oracao_abertura'] = oracoes[0] if len(oracoes) > 0 else ''
                    detalhes_dict['oracao_encerramento'] = oracoes[1] if len(oracoes) > 1 else ''
                    
                detalhes = detalhes_dict
            else:
                detalhes = {}
        else: # Tipo batismo
            cursor.execute("SELECT * FROM batismo WHERE ata_id=?", (ata_id,))
            detalhes = cursor.fetchone()
            if detalhes:
                detalhes_dict = dict(detalhes)
                if detalhes_dict.get('batizados'):
                    try:
                        detalhes_dict['batizados'] = json.loads(detalhes_dict['batizados'])
                    except:
                        detalhes_dict['batizados'] = []
                detalhes = detalhes_dict
            else:
                detalhes = {}
        
        # 5. Converter para PDF
        buffer, filename, mimetype = exportar_pdf_bytes(ata, detalhes, template, filename=f"ata_{ata_id}.pdf")
        return send_file(buffer, as_attachment=True, download_name=filename, mimetype=mimetype)
        
    except Exception as e:
        print(f"======== ERRO CRÍTICO NA EXPORTAÇÃO DE PDF: {e} ========")
        flash(f"Erro ao exportar PDF: {str(e)}", "error")
        return redirect(url_for("visualizar_ata", ata_id=ata_id))
    finally:
        conn.close()

# Rota para exportar ata como PDF SIMPLES (SOMENTE CAMPOS/SEM TEXTOS)
@app.route("/ata/exportar_simples/<int:ata_id>")
@login_required
def exportar_pdf_simples(ata_id):
    from functions.pdf_exporters import exportar_pdf_bytes
    
    conn = get_db() 
    try:
        cursor = conn.cursor() 
        
        # 1. Buscar a Ata
        cursor.execute(
            "SELECT * FROM atas WHERE id=? AND ala_id=?", 
            (ata_id, session['user_id'])
        )
        ata = cursor.fetchone()
        
        if not ata:
            raise ValueError("Ata não encontrada")
        
        ata = dict(ata)
        
        # 2. NÃO BUSCAR O TEMPLATE: template = {} ou template = None
        template = {} 
        
        # 3. Buscar detalhes conforme tipo (Lógica de deserialização mantida)
        if ata["tipo"] == "sacramental":
            cursor.execute("SELECT * FROM sacramental WHERE ata_id=?", (ata_id,))
            detalhes = cursor.fetchone()
            
            if detalhes:
                detalhes_dict = dict(detalhes)
                
                # Deserialização de JSON (simplificada)
                keys_to_load = ['hinos', 'oracoes', 'discursantes', 'anuncios', 
                                'desobrigacoes', 'apoios', 'confirmacoes_batismo', 
                                'apoio_membro_novo', 'bencao_crianca']

                for key in keys_to_load:
                    if detalhes_dict.get(key) and isinstance(detalhes_dict[key], str):
                        try:
                            detalhes_dict[key] = json.loads(detalhes_dict[key])
                        except:
                            if key in ['discursantes', 'anuncios', 'desobrigacoes', 'apoios', 'confirmacoes_batismo', 'apoio_membro_novo', 'bencao_crianca']:
                                detalhes_dict[key] = []
                            pass

                # Tratamento específico de hinos e orações
                if isinstance(detalhes_dict.get('hinos'), list):
                    hinos = detalhes_dict['hinos']
                    detalhes_dict['hino_abertura'] = hinos[0] if len(hinos) > 0 else ''
                    detalhes_dict['hino_encerramento'] = hinos[1] if len(hinos) > 1 else ''
                    
                if isinstance(detalhes_dict.get('oracoes'), list):
                    oracoes = detalhes_dict['oracoes']
                    detalhes_dict['oracao_abertura'] = oracoes[0] if len(oracoes) > 0 else ''
                    detalhes_dict['oracao_encerramento'] = oracoes[1] if len(oracoes) > 1 else ''
                    
                detalhes = detalhes_dict
            else:
                detalhes = {}
        else: # Tipo batismo
            cursor.execute("SELECT * FROM batismo WHERE ata_id=?", (ata_id,))
            detalhes = cursor.fetchone()
            if detalhes:
                detalhes_dict = dict(detalhes)
                if detalhes_dict.get('batizados'):
                    try:
                        detalhes_dict['batizados'] = json.loads(detalhes_dict['batizados'])
                    except:
                        detalhes_dict['batizados'] = []
                detalhes = detalhes_dict
            else:
                detalhes = {}
        
        # 4. Converter para PDF (template é vazio/None, resultando em "Sem Textos")
        buffer, filename, mimetype = exportar_pdf_bytes(ata, detalhes, template, filename=f"ata_simples_{ata_id}.pdf")
        return send_file(buffer, as_attachment=True, download_name=filename, mimetype=mimetype)
        
    except Exception as e:
        print(f"======== ERRO CRÍTICO NA EXPORTAÇÃO DE PDF SIMPLES: {e} ========")
        flash(f"Erro ao exportar PDF Simples: {str(e)}", "error")
        return redirect(url_for("visualizar_ata", ata_id=ata_id))
    finally:
        conn.close()

# Rota para exportar ata sacramental como PDF formatado
@app.route("/ata/exportar_sacramental/<int:ata_id>")
@login_required
def exportar_sacramental_pdf(ata_id):
    from functions.pdf_exporters import exportar_sacramental_bytes
    conn = get_db()
    try:
        # Renderizar HTML
        ata = conn.execute(
            "SELECT * FROM atas WHERE id=? AND ala_id=?", 
            (ata_id, session['user_id'])
        ).fetchone()
        
        if not ata:
            raise ValueError("Ata não encontrada")
        
        ata = dict(ata)
        
        if ata["tipo"] != "sacramental":
            raise ValueError("Esta ata não é sacramental")
        
        detalhes = conn.execute("SELECT * FROM sacramental WHERE ata_id=?", (ata_id,)).fetchone()
        if detalhes:
            detalhes = dict(detalhes)
            if detalhes.get('hinos'):
                try:
                    hinos = json.loads(detalhes['hinos'])
                    detalhes['hino_abertura'] = hinos[0] if len(hinos) > 0 else ''
                    detalhes['hino_encerramento'] = hinos[1] if len(hinos) > 1 else ''
                except:
                    pass
            if detalhes.get('oracoes'):
                try:
                    oracoes = json.loads(detalhes['oracoes'])
                    detalhes['oracao_abertura'] = oracoes[0] if len(oracoes) > 0 else ''
                    detalhes['oracao_encerramento'] = oracoes[1] if len(oracoes) > 1 else ''
                except:
                    pass
            if detalhes.get('discursantes'):
                try:
                    detalhes['discursantes'] = json.loads(detalhes['discursantes'])
                except:
                    detalhes['discursantes'] = []
            if detalhes.get('anuncios'):
                try:
                    detalhes['anuncios'] = json.loads(detalhes['anuncios'])
                except:
                    detalhes['anuncios'] = []
        else:
            detalhes = {}
        
        # Buscar template
        template = conn.execute("SELECT * FROM templates WHERE nome = 'Sacramental Padrão'").fetchone()
        
        if not template:
            template = conn.execute(
                "SELECT * FROM templates WHERE tipo_template = 1"
            ).fetchone()
        
        # =================================================================
        # 🚨 CORREÇÃO APLICADA AQUI
        # =================================================================
        if template:
            template = dict(template)
        else:
            # Se nenhuma busca funcionou, defina como um dicionário vazio
            template = {} 
        # =================================================================

        # Converter para PDF
        # Gerar PDF diretamente com dados (ReportLab)
        buffer, filename, mimetype = exportar_sacramental_bytes(ata, detalhes, template=template, filename=f"ata_sacramental_{ata_id}.pdf")
        return send_file(buffer, as_attachment=True, download_name=filename, mimetype=mimetype)
    
    except Exception as e:
        print("======== ERRO CRÍTICO NA EXPORTAÇÃO DE PDF ========")
        traceback.print_exc() # Isso irá imprimir o erro detalhado no console

        flash(f"Erro ao exportar PDF: {str(e)}", "error")
        return redirect(url_for("visualizar_ata", ata_id=ata_id))
    finally:
        conn.close()

@app.template_filter('reverse_date_format')
def reverse_date_format(value):
    """Converte 'AAAA/MM/DD' para 'DD/MM/AAAA' (o template usa replace('-', '/') antes)"""
    # Se o formato original for AAAA-MM-DD, o input é AAAA/MM/DD após o replace no HTML.
    parts = value.split('/')
    if len(parts) == 3:
        # Reverte ordem: [2]DD, [1]MM, [0]AAAA
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return value

@app.route('/deletar_ata', methods=['POST'])
def deletar_ata():
    """Rota para deletar uma ata e seus detalhes relacionados."""
    # Garante que o usuário está logado
    if 'user_id' not in session:
        flash('Você precisa estar logado para realizar esta ação.', 'error')
        return redirect(url_for('login'))

    ata_id = request.form.get('ata_id', type=int)
    ala_id = session['user_id']

    if not ata_id:
        flash('ID da ata não fornecido.', 'error')
        # CORREÇÃO: O endpoint correto é 'listar_todas_atas'
        return redirect(url_for('listar_todas_atas'))

    conn = get_db()
    
    # 1. Obter o tipo da ata para saber qual tabela de detalhes deletar
    ata_info = conn.execute("SELECT tipo FROM atas WHERE id = ? AND ala_id = ?", (ata_id, ala_id)).fetchone()

    if not ata_info:
        flash('Ata não encontrada ou você não tem permissão para deletá-la.', 'error')
        conn.close()
        # CORREÇÃO: O endpoint correto é 'listar_todas_atas'
        return redirect(url_for('listar_todas_atas'))

    ata_tipo = ata_info['tipo']

    try:
        # Inicia transação
        conn.execute("BEGIN TRANSACTION")

        # 2. Deleta os detalhes relacionados (sacramental ou batismo)
        if ata_tipo == 'sacramental':
            conn.execute("DELETE FROM sacramental WHERE ata_id = ?", (ata_id,))
        elif ata_tipo == 'batismo':
            conn.execute("DELETE FROM batismo WHERE ata_id = ?", (ata_id,))
        
        # 3. Deleta a ata principal (precisa ter ala_id para segurança)
        conn.execute("DELETE FROM atas WHERE id = ? AND ala_id = ?", (ata_id, ala_id))

        # Confirma a transação
        conn.commit()
        flash(f'Ata de {ata_tipo.capitalize()} (ID: {ata_id}) deletada com sucesso!', 'success')

    except Exception as e:
        conn.rollback()
        flash(f'Erro ao deletar ata: {e}', 'error')
        
    finally:
        conn.close()

    # CORREÇÃO: O endpoint correto é 'listar_todas_atas'
    return redirect(url_for('listar_todas_atas'))

# Sistema de mensagens flash
@app.context_processor
def inject_flash_messages():
    messages = []
    return dict(flash_messages=messages)

# WebSocket para edição colaborativa em tempo real
users_editing = {}
@socketio.on('join')
def handle_join(data):
    ata_id = data['ata_id']
    users_editing[ata_id] = users_editing.get(ata_id, 0) + 1

    join_room(ata_id)
    emit('update_users', {'count': users_editing[ata_id]}, to=ata_id)

@socketio.on('leave')
def handle_leave(data):
    ata_id = data['ata_id']
    if ata_id in users_editing:
        users_editing[ata_id] = max(users_editing[ata_id] - 1, 0)
        if users_editing[ata_id] == 0:
            del users_editing[ata_id]
        leave_room(ata_id)
        emit('update_users', {'count': users_editing.get(ata_id, 0)}, to=ata_id)

@socketio.on('field_update')
def handle_field_update(data):
    ata_id = data['ata_id']
    emit('field_update', {'name': data['name'], 'value': data['value']}, to=ata_id, include_self=False)

# Rota para renderizar HTML puro da ata (para conversão a PDF)
@app.route("/ata/render_html/<int:ata_id>")
@login_required
def render_ata_html(ata_id):
    """Renderiza o HTML puro (sem base.html) para conversão a PDF"""
    conn = get_db()
    ata = conn.execute(
        "SELECT * FROM atas WHERE id=? AND ala_id=?", 
        (ata_id, session['user_id'])
    ).fetchone()
    
    if not ata:
        flash("Ata não encontrada ou você não tem permissão para acessá-la.", "error")
        return redirect(url_for("index"))
        
    # Buscar template padrão
    template = None
    if ata["tipo"] == "sacramental":
        template = conn.execute(
            "SELECT * FROM templates WHERE nome = 'Sacramental Padrão'"
        ).fetchone()
        
        if not template:
            template = conn.execute(
                "SELECT * FROM templates WHERE tipo_template = 1"
            ).fetchone()
        
        if template:
            template = dict(template)
    
    # Buscar detalhes
    if ata["tipo"] == "sacramental":
        detalhes = conn.execute("SELECT * FROM sacramental WHERE ata_id=?", (ata_id,)).fetchone()
        if detalhes:
            detalhes_dict = dict(detalhes)
            if detalhes_dict.get('hinos'):
                try:
                    hinos = json.loads(detalhes_dict['hinos'])
                    detalhes_dict['hino_abertura'] = hinos[0] if len(hinos) > 0 else ''
                    detalhes_dict['hino_encerramento'] = hinos[1] if len(hinos) > 1 else ''
                except:
                    detalhes_dict['hino_abertura'] = ''
                    detalhes_dict['hino_encerramento'] = ''
                    
            if detalhes_dict.get('oracoes'):
                try:
                    oracoes = json.loads(detalhes_dict['oracoes'])
                    detalhes_dict['oracao_abertura'] = oracoes[0] if len(oracoes) > 0 else ''
                    detalhes_dict['oracao_encerramento'] = oracoes[1] if len(oracoes) > 1 else ''
                except:
                    detalhes_dict['oracao_abertura'] = ''
                    detalhes_dict['oracao_encerramento'] = ''
                    
            if detalhes_dict.get('discursantes'):
                try:
                    detalhes_dict['discursantes'] = json.loads(detalhes_dict['discursantes'])
                except:
                    detalhes_dict['discursantes'] = []
                    
            if detalhes_dict.get('anuncios'):
                try:
                    detalhes_dict['anuncios'] = json.loads(detalhes_dict['anuncios'])
                except:
                    detalhes_dict['anuncios'] = []
                    
            detalhes = detalhes_dict
        else:
            detalhes = {}
    else:
        detalhes = conn.execute("SELECT * FROM batismo WHERE ata_id=?", (ata_id,)).fetchone()
        if detalhes:
            detalhes_dict = dict(detalhes)
            if detalhes_dict.get('batizados'):
                try:
                    detalhes_dict['batizados'] = json.loads(detalhes_dict['batizados'])
                except:
                    detalhes_dict['batizados'] = []
            detalhes = detalhes_dict
        else:
            detalhes = {}
    
    conn.close()
    
    # Renderizar template SEM base.html (use um template dedicado ou renderize inline)
    return render_template("visualizar_ata_pdf.html", ata=ata, detalhes=detalhes, template=template)

# Rodar o app
if __name__ == "__main__":
    # Configurações para produção
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    # Inicializar banco
    init_db()
    
    # Rodar servidor - permitir produção
    socketio.run(app, 
                 host='0.0.0.0', 
                 port=port, 
                 debug=debug,
                 allow_unsafe_werkzeug=True)