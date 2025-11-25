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
            with open("database/schema.sql") as f:
                conn.executescript(f.read())
            conn.commit()
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

# Autenticação Login
def authenticate_user(username, password):
    conn = get_db()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?", 
        (username, password)
    ).fetchone()
    conn.close()
    return user

# ==================================================================
# Rotas de Configurações
# ==================================================================

# Rota para configurações
@app.route("/configuracoes")
@login_required
def configuracoes():
    conn = get_db()
    
    # Buscar templates
    templates = conn.execute("SELECT * FROM templates").fetchall()
    templates = [dict(template) for template in templates]
    
    # Buscar informações da unidade
    unidade = conn.execute(
        "SELECT * FROM unidades WHERE ala_id = ?", 
        (session['user_id'],)
    ).fetchone()
    if unidade:
        unidade = dict(unidade)
    else:
        unidade = {}
    
    # Buscar estatísticas
    total_atas = conn.execute(
        "SELECT COUNT(*) FROM atas WHERE ala_id = ?", 
        (session['user_id'],)
    ).fetchone()[0]
    
    atas_sacramentais = conn.execute(
        "SELECT COUNT(*) FROM atas WHERE ala_id = ? AND tipo = 'sacramental'", 
        (session['user_id'],)
    ).fetchone()[0]
    
    atas_batismo = conn.execute(
        "SELECT COUNT(*) FROM atas WHERE ala_id = ? AND tipo = 'batismo'", 
        (session['user_id'],)
    ).fetchone()[0]
    
    # Atas deste mês
    mes_atual = datetime.now().strftime("%Y-%m")
    atas_mes = conn.execute(
        "SELECT COUNT(*) FROM atas WHERE ala_id = ? AND strftime('%Y-%m', data) = ?", 
        (session['user_id'], mes_atual)
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
    conselheiros = request.form.get("conselheiros")
    horario = request.form.get("horario")
    estaca = request.form.get("estaca")
    
    # Verificar se já existe registro para esta ala
    unidade_existente = conn.execute(
        "SELECT * FROM unidades WHERE ala_id = ?", 
        (session['user_id'],)
    ).fetchone()
    
    if unidade_existente:
        # Atualizar
        conn.execute("""
            UPDATE unidades 
            SET nome = ?, bispo = ?, conselheiros = ?, horario = ?, estaca = ?
            WHERE ala_id = ?
        """, (nome_ala, bispo, conselheiros, horario, estaca, session['user_id']))
    else:
        # Inserir
        conn.execute("""
            INSERT INTO unidades (ala_id, nome, bispo, conselheiros, horario, estaca)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session['user_id'], nome_ala, bispo, conselheiros, horario, estaca))
    
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
        # Buscar todos os campos do formulário
        campos = {
            'nome': request.form.get('nome'),
            'boas_vindas': request.form.get('boas_vindas'),
            'desobrigacoes': request.form.get('desobrigacoes'),
            'apoios': request.form.get('apoios'),
            'confirmacoes_batismo': request.form.get('confirmacoes_batismo'),
            'apoio_membro_novo': request.form.get('apoio_membro_novo'),
            'bencao_crianca': request.form.get('bencao_crianca'),
            'sacramento': request.form.get('sacramento'),
            'mensagens': request.form.get('mensagens'),
            'live': request.form.get('live'),
            'encerramento': request.form.get('encerramento')
        }
        
        # Atualizar template
        conn.execute("""
            UPDATE templates SET
            nome = ?, boas_vindas = ?, desobrigacoes = ?, apoios = ?, 
            confirmacoes_batismo = ?, apoio_membro_novo = ?, bencao_crianca = ?,
            sacramento = ?, mensagens = ?, live = ?, encerramento = ?
            WHERE id = ?
        """, (
            campos['nome'], campos['boas_vindas'], campos['desobrigacoes'],
            campos['apoios'], campos['confirmacoes_batismo'], campos['apoio_membro_novo'],
            campos['bencao_crianca'], campos['sacramento'], campos['mensagens'],
            campos['live'], campos['encerramento'], template_id
        ))
        
        conn.commit()
        conn.close()
        
        flash("Template atualizado com sucesso!", "success")
        return redirect(url_for("configuracoes"))
        
    except Exception as e:
        conn.close()
        print(f"Erro ao salvar template: {e}")
        flash("Erro ao salvar template", "error")
        return redirect(url_for("configuracoes"))

# Rota para criar novo template
@app.route("/configuracoes/template/criar", methods=["POST"])
@login_required
def criar_template():
    conn = get_db()
    
    try:
        # Buscar dados do formulário
        nome = request.form.get('nome')
        tipo_template = request.form.get('tipo_template')
        
        # Inserir novo template com valores padrão
        conn.execute("""
            INSERT INTO templates (tipo_template, nome, boas_vindas, desobrigacoes, apoios, 
            confirmacoes_batismo, apoio_membro_novo, bencao_crianca, sacramento, mensagens, live, encerramento)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            tipo_template,
            nome,
            "Bom dia irmãos e irmãs! Gostaríamos de fazer todos muito bem vindos...",
            "É proposto dar um voto de agradecimento aos serviços prestados...",
            "O(a) irmã(o) [NOME] está sendo chamado(a) como [CHAMADO]...",
            "O(a) irmã(o) [NOME] foram batizados, gostaríamos de convida-los(a)...",
            "O(a) irmã(o) [NOME] foi batizado e confirmado membro da igreja...",
            "Gostaríamos de chamar ao púlpito o irmão [NOME] que irá dar a benção...",
            "Passaremos ao Sacramento, que é a parte mais importante de nossa reunião...",
            "Agradecemos a todos pela reverência durante o Sacramento...",
            "Gostaria de lembrar todos que estejam assistindo a transmissão...",
            "Agradecemos a presença e participação de todos..."
        ))
        
        conn.commit()
        conn.close()
        
        flash("Novo template criado com sucesso!", "success")
        return redirect(url_for("configuracoes"))
        
    except Exception as e:
        conn.close()
        print(f"Erro ao criar template: {e}")
        flash("Erro ao criar template", "error")
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
            }), 400
        
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

# ==================================================================
# Rotas principais do sistema de atas
# ==================================================================

# Aba de discursantes recentes na criação de atas sacramentais
def get_discursantes_recentes():
    """Busca discursantes dos últimos 3 meses"""
    conn = get_db()
    
    # Data de 3 meses atrás
    tres_meses_atras = (datetime.now().replace(day=1) - timedelta(days=90)).strftime("%Y-%m-%d")
    
    discursantes = conn.execute("""
        SELECT s.discursantes, a.data 
        FROM sacramental s 
        JOIN atas a ON s.ata_id = a.id 
        WHERE a.data >= ? AND a.tipo = 'sacramental' AND a.ala_id = ?
        ORDER BY a.data DESC
    """, (tres_meses_atras, session['user_id'])).fetchall()
    
    # Processar e consolidar discursantes
    todos_discursantes = []
    nomes_ja_adicionados = set()  # Para evitar duplicatas
    
    for row in discursantes:
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

# Rota de Login de Usuário
@app.route('/', methods=['GET', 'POST'])
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
    
    # Buscar temas dos últimos 3 meses
    temas_recentes = conn.execute("""
        SELECT s.tema, a.data 
        FROM sacramental s 
        JOIN atas a ON s.ata_id = a.id 
        WHERE a.data >= ? AND a.tipo = 'sacramental' AND a.ala_id = ? AND s.tema IS NOT NULL AND s.tema != ''
        ORDER BY a.data DESC
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
    
    return render_template(
        "todas_atas.html",
        atas=atas,
        discursantes_recentes=todos_discursantes[:20],  # Limitar a 20
        temas_recentes=temas_formatados
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
            
            # NOVOS CAMPOS ADICIONADOS AQUI
            detalhes = {
                "presidido": request.form.get("presidido", ""),
                "dirigido": request.form.get("dirigido", ""),
                "recepcionistas": request.form.get("recepcionistas", ""),  # NOVO
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
                # Atualiza registro existente COM NOVOS CAMPOS
                conn.execute("""
                    UPDATE sacramental 
                    SET presidido=?, dirigido=?, recepcionistas=?, pianista=?, regente_musica=?, 
                        reconhecemos_presenca=?, anuncios=?, hinos=?, oracoes=?, discursantes=?, 
                        hino_sacramental=?, hino_intermediario=?, desobrigacoes=?, apoios=?, 
                        confirmacoes_batismo=?, apoio_membros=?, bencao_criancas=?, ultimo_discursante=?
                    WHERE ata_id=?
                """, (
                    detalhes["presidido"], 
                    detalhes["dirigido"],
                    detalhes["recepcionistas"],  # NOVO
                    detalhes["pianista"],
                    detalhes["regente_musica"],
                    detalhes["reconhecemos_presenca"],  # NOVO
                    json.dumps(detalhes["anuncios"]),
                    json.dumps([detalhes["hino_abertura"], detalhes["hino_encerramento"]]), 
                    json.dumps([detalhes["oracao_abertura"], detalhes["oracao_encerramento"]]), 
                    json.dumps(detalhes["discursantes"]),
                    detalhes["hino_sacramental"],
                    detalhes["hino_intermediario"],
                    detalhes["desobrigacoes"],  # NOVO
                    detalhes["apoios"],  # NOVO
                    detalhes["confirmacoes_batismo"],  # NOVO
                    detalhes["apoio_membros"],  # NOVO
                    detalhes["bencao_criancas"],  # NOVO
                    detalhes["ultimo_discursante"],  # NOVO
                    ata_id
                ))
            else:
                # Insere novo registro COM NOVOS CAMPOS
                conn.execute("""
                    INSERT INTO sacramental (ata_id, presidido, dirigido, recepcionistas, pianista, regente_musica, 
                        reconhecemos_presenca, anuncios, hinos, oracoes, discursantes, hino_sacramental, hino_intermediario,
                        desobrigacoes, apoios, confirmacoes_batismo, apoio_membros, bencao_criancas, ultimo_discursante) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ata_id, 
                    detalhes["presidido"], 
                    detalhes["dirigido"],
                    detalhes["recepcionistas"],  # NOVO
                    detalhes["pianista"],
                    detalhes["regente_musica"],
                    detalhes["reconhecemos_presenca"],  # NOVO
                    json.dumps(detalhes["anuncios"]),
                    json.dumps([detalhes["hino_abertura"], detalhes["hino_encerramento"]]), 
                    json.dumps([detalhes["oracao_abertura"], detalhes["oracao_encerramento"]]), 
                    json.dumps(detalhes["discursantes"]),
                    detalhes["hino_sacramental"],
                    detalhes["hino_intermediario"],
                    detalhes["desobrigacoes"],  # NOVO
                    detalhes["apoios"],  # NOVO
                    detalhes["confirmacoes_batismo"],  # NOVO
                    detalhes["apoio_membros"],  # NOVO
                    detalhes["bencao_criancas"],  # NOVO
                    detalhes["ultimo_discursante"]  # NOVO
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
        
        # Buscar discursantes recentes apenas para sacramental (apenas em modo criação)
        discursantes_recentes = get_discursantes_recentes() if not editar else []
        
        return render_template("sacramental.html", 
                             primeiro=is_primeiro_domingo, 
                             data=data, 
                             editar=editar, 
                             dados=dados_existentes,
                             discursantes_recentes=discursantes_recentes)
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
    
    conn.close()
    
    return render_template("visualizar_ata.html", ata=ata, detalhes=detalhes, template=template)


# Rota para exportar ata como PDF simples (em desenvolvimento, ajustando para ser dinamica com cada ala)
@app.route("/ata/exportar/<int:ata_id>")
@login_required
def exportar_pdf(ata_id):
    conn = get_db()
    ata = conn.execute("SELECT * FROM atas WHERE id=?", (ata_id,)).fetchone()
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFont("Helvetica", 14)
    c.drawString(50, 800, f"Ata de {ata['tipo'].capitalize()} - {ata['data']}")
    c.setFont("Helvetica", 12)

    if ata["tipo"] == "sacramental":
        detalhes = conn.execute("SELECT * FROM sacramental WHERE ata_id=?", (ata_id,)).fetchone()
        if detalhes:
            # Converter para dicionário para evitar o erro do .get()
            detalhes_dict = dict(detalhes)
            hinos = json.loads(detalhes_dict["hinos"])
            oracoes = json.loads(detalhes_dict["oracoes"])
            discursantes = json.loads(detalhes_dict["discursantes"])
            anuncios = json.loads(detalhes_dict["anuncios"]) if detalhes_dict.get("anuncios") else []
            
            c.drawString(50, 770, f"Presidido por: {detalhes_dict['presidido']}")
            c.drawString(50, 750, f"Dirigido por: {detalhes_dict['dirigido']}")
            c.drawString(50, 730, f"Pianista: {detalhes_dict.get('pianista', '')}")  # NOVO
            c.drawString(50, 710, f"Regente de Música: {detalhes_dict.get('regente_musica', '')}")
            
            # Anúncios
            y = 690
            if anuncios and len(anuncios) > 0:
                c.drawString(50, 690, "Anúncios:")
                y = 670
                for a in anuncios:
                    c.drawString(70, y, f"- {a}")
                    y -= 20
            
            c.drawString(50, y-20, f"Hino de Abertura: {hinos[0] if len(hinos) > 0 else ''}")
            c.drawString(50, y-40, f"Oração de Abertura: {oracoes[0] if len(oracoes) > 0 else ''}")
            c.drawString(50, y-60, f"Hino Sacramental: {detalhes_dict.get('hino_sacramental', '')}")
            
            # Discursantes
            y_disc = y-80
            if discursantes and len(discursantes) > 0:
                c.drawString(50, y_disc, "Discursantes:")
                y_disc -= 20
                for d in discursantes:
                    c.drawString(70, y_disc, f"- {d}")
                    y_disc -= 20
            
            c.drawString(50, y_disc-20, f"Hino Intermediário: {detalhes_dict.get('hino_intermediario', '')}")
            c.drawString(50, y_disc-40, f"Hino de Encerramento: {hinos[1] if len(hinos) > 1 else ''}")
            c.drawString(50, y_disc-60, f"Oração de Encerramento: {oracoes[1] if len(oracoes) > 1 else ''}")
    else:
        detalhes = conn.execute("SELECT * FROM batismo WHERE ata_id=?", (ata_id,)).fetchone()
        if detalhes:
            # Converter para dicionário para evitar o erro do .get()
            detalhes_dict = dict(detalhes)
            batizados = json.loads(detalhes_dict["batizados"])
            c.drawString(50, 770, f"Presidido por: {detalhes_dict['presidido']}")
            c.drawString(50, 750, f"Dirigido por: {detalhes_dict['dirigido']}")
            c.drawString(50, 730, f"Dedicado a: {detalhes_dict['dedicado']}")
            c.drawString(50, 710, f"Testemunha 1: {detalhes_dict.get('testemunha1', '')}")
            c.drawString(50, 690, f"Testemunha 2: {detalhes_dict.get('testemunha2', '')}")
            y = 670
            if batizados and len(batizados) > 0:
                c.drawString(50, 670, "Batizados:")
                y = 650
                for b in batizados:
                    c.drawString(70, y, f"- {b}")
                    y -= 20

    c.showPage()
    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"ata_{ata_id}.pdf", mimetype="application/pdf")

# Rota para exportar ata sacramental como PDF formatado e bunitinho (*SAMUEL ESTÁ EM DESENVOLVIMENTO :), AJUSTANDO PARA SER DINAMICA A CADA ALA COM O BD*)
@app.route("/ata/exportar_sacramental/<int:ata_id>")
@login_required
def exportar_sacramental_pdf(ata_id):
    conn = get_db()
    ata = conn.execute("SELECT * FROM atas WHERE id=?", (ata_id,)).fetchone()
    
    if not ata or ata["tipo"] != "sacramental":
        flash("Ata sacramental não encontrada", "error")
        return redirect(url_for("index"))
    
    detalhes = conn.execute("SELECT * FROM sacramental WHERE ata_id=?", (ata_id,)).fetchone()
    if not detalhes:
        flash("Detalhes da ata não encontrados", "error")
        return redirect(url_for("visualizar_ata", ata_id=ata_id))
    
    # Converter para dicionário
    detalhes_dict = dict(detalhes)
    
    # Processar dados
    if detalhes_dict.get('hinos'):
        hinos = json.loads(detalhes_dict['hinos'])
        detalhes_dict['hino_abertura'] = hinos[0] if len(hinos) > 0 else ''
        detalhes_dict['hino_encerramento'] = hinos[1] if len(hinos) > 1 else ''
    
    if detalhes_dict.get('oracoes'):
        oracoes = json.loads(detalhes_dict['oracoes'])
        detalhes_dict['oracao_abertura'] = oracoes[0] if len(oracoes) > 0 else ''
        detalhes_dict['oracao_encerramento'] = oracoes[1] if len(oracoes) > 1 else ''
    
    if detalhes_dict.get('discursantes'):
        detalhes_dict['discursantes'] = json.loads(detalhes_dict['discursantes'])
    
    if detalhes_dict.get('anuncios'):
        detalhes_dict['anuncios'] = json.loads(detalhes_dict['anuncios'])
    
    buffer = io.BytesIO()
    
    # Criar PDF com duas páginas
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # CORES - Baseadas no site da Igreja
    AZUL_IGREJA = colors.HexColor("#004272")  # Azul escuro
    AZUL_CLARO = colors.HexColor("#E6F2FF")   # Azul claro para fundos
    CINZA_CLARO = colors.HexColor("#F8F9FA")  # Cinza muito claro
    
    # ========== PÁGINA 1 (FRENTE) ==========
    c.setFillColor(AZUL_IGREJA)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(180, height - 50, "ATA REUNIÃO SACRAMENTAL")
    
    
    # Tabela de informações
    data_ata = datetime.strptime(ata['data'], "%Y-%m-%d")
    data_formatada = data_ata.strftime("%d/%m/%Y")
    
    table_data = [
        ["ALA [NOME]", "ESTACA CRICIÚMA", f"HORÁRIO [ARRUMAR]", f"DATA {data_formatada}"]
    ]
    
    jooj = 125

    table = Table(table_data, colWidths=[jooj, jooj, jooj, jooj])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), AZUL_IGREJA),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.white),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
    ]))
    table.wrapOn(c, width, height)
    table.drawOn(c, 50, height - 100)
    
    font_a = 12

    # Boas-vindas
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 13)
    texto_boas_vindas = f"Bom dia irmãos e irmãs! Gostaríamos de fazer todos muito bem vindos a mais uma Reunião Sacramental da ALA [NOME], Estaca Criciúma, neste dia {data_formatada}. Desejamos que todos se sintam bem entre nós, especialmente aqueles que nos visitam."
    
    estilo_paragrafo = ParagraphStyle(
        'Normal',
        fontName='Helvetica',
        fontSize=13,
        leading=12,
        alignment=4,  # Justificado
        textColor=colors.black,
        spaceBefore=15,
        spaceAfter=12
    )
    
    p = Paragraph(texto_boas_vindas, estilo_paragrafo)
    p.wrapOn(c, width - 100, height)
    p.drawOn(c, 50, height - 160)
    
    # Informações de presidência
    y_pos = height - 180
    c.setFont("Helvetica-Bold", font_a)
    c.drawString(50, y_pos, "Esta Reunião está sendo presidida por:")
    c.setFont("Helvetica", font_a)
    c.drawString(280, y_pos, detalhes_dict.get('presidido', 'Não informado'))
    
    y_pos -= 20
    c.setFont("Helvetica-Bold", font_a)
    c.drawString(50, y_pos, "E dirigida por:")
    c.setFont("Helvetica", font_a)
    c.drawString(200, y_pos, detalhes_dict.get('dirigido', 'Não informado'))
    
    y_pos -= 20
    c.setFont("Helvetica-Bold", font_a)
    c.drawString(50, y_pos, "Como recepcionistas:")
    # Aqui você pode adicionar recepcionistas se tiver o campo
    
    y_pos -= 20
    c.drawString(50, y_pos, "Como pianista:")
    c.setFont("Helvetica", font_a)
    c.drawString(200, y_pos, detalhes_dict.get('pianista', 'Não informado'))
    
    y_pos -= 20
    c.setFont("Helvetica-Bold", font_a)
    c.drawString(50, y_pos, "E regente de música:")
    c.setFont("Helvetica", font_a)
    c.drawString(200, y_pos, detalhes_dict.get('regente_musica', 'Não informado'))
    
    # Linha divisória
    y_pos -= 20
    c.setStrokeColor(colors.HexColor("#E2E8F0"))  # Cinza claro
    c.setLineWidth(3)
    c.line(50, y_pos, width - 50, y_pos)
    y_pos -= 12

    # SEÇÃO: ABERTURA
    y_pos -= 20
    c.setFillColor(AZUL_IGREJA)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(50, y_pos, "ABERTURA (6 min)")
    
    y_pos -= 32
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold",font_a)
    c.drawString(50, y_pos, "Reconhecemos a Presença:")
    
    y_pos -= 20
    c.drawString(50, y_pos, "Temos como anúncios:")
    
    # Anúncios
    y_pos -= 20
    c.setFont("Helvetica", font_a)
    if detalhes_dict.get('anuncios'):
        for anuncio in detalhes_dict['anuncios']:
            if anuncio and anuncio.strip():
                p_anuncio = Paragraph(f"• {anuncio}", estilo_paragrafo)
                p_anuncio.wrapOn(c, width - 100, height)
                p_anuncio.drawOn(c, 65, y_pos)
                y_pos -= 15
    else:
        c.drawString(65, y_pos, "Nenhum anúncio informado")
        y_pos -= 15
    
    # Hino e Oração de Abertura
    y_pos -= 60
    table_encerramento = Table([
        ["CANTAREMOS O HINO DE ABERTURA:", 
         "E A PRIMEIRA ORAÇÃO SERÁ FEITA POR: "],
        [f"{detalhes_dict.get('hino_abertura', 'Não informado')}", 
         f"{detalhes_dict.get('oracao_abertura', 'Não informado')}"]
    ], colWidths=[250,250,250,250])
    
    table_encerramento.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), AZUL_CLARO),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    table_encerramento.wrapOn(c, width, height)
    table_encerramento.drawOn(c, 50, y_pos - 20)
    
    # Linha divisória
    y_pos -= 30
    c.setStrokeColor(colors.HexColor("#E2E8F0"))  # Cinza claro
    c.setLineWidth(3)
    c.line(50, y_pos, width - 50, y_pos)
    y_pos -= 12

    # SEÇÃO: AÇÕES
    y_pos -= 20
    c.setFillColor(AZUL_IGREJA)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(50, y_pos, "AÇÕES (5 min)")
    
    y_pos -= 30
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", font_a)
    c.drawString(50, y_pos, "DESOBRIGAÇÕES")
    
    y_pos -= 20
    c.setFont("Helvetica", 10)
    texto_desobrigacoes = "É proposto dar um voto de agradecimento aos serviços prestados pelo(a) irmã(o) [NOME] que serviu como [CHAMADO]. Todos os que desejam se manifestar, levantem a mão"
    p_desobrigacoes = Paragraph(texto_desobrigacoes, estilo_paragrafo)
    p_desobrigacoes.wrapOn(c, width - 100, height)
    p_desobrigacoes.drawOn(c, 50, y_pos - 30)
    
    y_pos -= 60
    c.setFont("Helvetica-Bold", font_a)
    c.drawString(50, y_pos, "APOIOS")
    
    y_pos -= 20
    c.setFont("Helvetica", 10)
    texto_apoios = "O(a) irmã(o) [NOME] está sendo chamado(a) como [CHAMADO]. Todos que forem a favor manifestem-se. Os que forem contrários, manifestem-se"
    p_apoios = Paragraph(texto_apoios, estilo_paragrafo)
    p_apoios.wrapOn(c, width - 100, height)
    p_apoios.drawOn(c, 50, y_pos - 20)

    # Confirmações Batismais
    y_pos -= 60
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", font_a)
    c.drawString(50, y_pos, "CONFIRMAÇÕES BATISMAIS")

    y_pos -= 20
    c.setFont("Helvetica", 10)
    texto_confirmacoes = "O(a) irmã(o) [NOME] foram batizados, gostaríamos de convida-los(a) para virem até o púlpito para que possamos fazer sua confirmação como Membro de A Igreja de Jesus Cristo dos Santos dos Ultimos Dias."
    p_confirmacoes = Paragraph(texto_confirmacoes, estilo_paragrafo)
    p_confirmacoes.wrapOn(c, width - 100, height)
    p_confirmacoes.drawOn(c, 50, y_pos - 20)
    
    c.showPage()  # Fim da página 1
    
    # ========== PÁGINA 2 (VERSO) ==========
    
    # SEÇÃO: AÇÕES (continuação)
    y_pos = height - 50
    c.setFillColor(AZUL_IGREJA)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(50, y_pos, "AÇÕES (continuação)")
    
    # Apoio a Novos Membros
    y_pos -= 30
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", font_a)
    c.drawString(50, y_pos, "APOIO A NOVOS MEMBROS")
    
    y_pos -= 15
    c.setFont("Helvetica", 10)
    texto_novos_membros = "O(a) irmã(o) [NOME] foi batizado e confirmado membro da igreja, e gostarámos do apoio de todos os irmãos de plena aceitação como mais novo membro da ala. Todos a favor, manifestem-se"
    p_novos_membros = Paragraph(texto_novos_membros, estilo_paragrafo)
    p_novos_membros.wrapOn(c, width - 100, height)
    p_novos_membros.drawOn(c, 50, y_pos - 40)
    
    # Benção de Crianças
    y_pos -= 70
    c.setFont("Helvetica-Bold", font_a)
    c.drawString(50, y_pos, "BENÇÃO DE CRIANÇAS")
    
    y_pos -= 20
    c.setFont("Helvetica", 10)
    texto_bencao = "Gostaríamos de chamar ao púlpito o irmão [NOME] que irá dar a benção de apresentação da(a) [NOME]"
    p_bencao = Paragraph(texto_bencao, estilo_paragrafo)
    p_bencao.wrapOn(c, width - 100, height)
    p_bencao.drawOn(c, 50, y_pos - 20)
    
    # Linha divisória
    y_pos -= 50
    c.setStrokeColor(colors.HexColor("#E2E8F0"))  # Cinza claro
    c.setLineWidth(3)
    c.line(50, y_pos, width - 50, y_pos)
    y_pos -= 12

    # SEÇÃO: SACRAMENTO
    y_pos -= 20
    c.setFillColor(AZUL_IGREJA)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(50, y_pos, "SACRAMENTO (10 min)")
    
    y_pos -= 30
    c.setFillColor(colors.black)
    c.setFont("Helvetica", font_a)
    texto_sacramento = f"Passaremos ao Sacramento, que é a parte mais importante de nossa reunião. Cantaremos como Hino Sacramental {detalhes_dict.get('hino_sacramental', 'Não informado')}, o Sacramento será abençoado e distribuído a todos"
    p_sacramento = Paragraph(texto_sacramento, estilo_paragrafo)
    p_sacramento.wrapOn(c, width - 100, height)
    p_sacramento.drawOn(c, 50, y_pos - 20)
    
    y_pos -= 50
    c.setFont("Helvetica-Bold", 10)
    hino_sacramento = f"HINO SACRAMENTAL (3 min): {detalhes_dict.get('hino_sacramental', 'Não informado')}"
    c.drawString(50, y_pos, hino_sacramento)
    
    # Linha divisória
    y_pos -= 20
    c.setStrokeColor(colors.HexColor("#E2E8F0"))  # Cinza claro
    c.setLineWidth(3)
    c.line(50, y_pos, width - 50, y_pos)
    y_pos -= 12

    # SEÇÃO: MENSAGENS
    y_pos -= 20
    c.setFillColor(AZUL_IGREJA)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(50, y_pos, "MENSAGENS (35 min)")
    
    y_pos -= 20
    c.setFillColor(colors.black)
    c.setFont("Helvetica", font_a)
    texto_mensagens = "Agradecemos a todos pela reverência durante o Sacramento. Passaremos agora a parte dos discursantes. Gostaria de lembrar todos que estejam assitindo a transmissão da reunião, que se identifiquem para que possamos contá-los também"
    p_mensagens = Paragraph(texto_mensagens, estilo_paragrafo)
    p_mensagens.wrapOn(c, width - 100, height)
    p_mensagens.drawOn(c, 50, y_pos - 20)
    
    # Discursantes
    y_pos -= 50
    if detalhes_dict.get('discursantes'):
        discursantes_data = []
        for i, discursante in enumerate(detalhes_dict['discursantes']):
            if discursante and discursante.strip():
                tempo = "3-5 min" if i == 0 else "5-7 min" if i == 1 else "8-10 min"
                discursantes_data.append([f"{i+1}º ORADOR ({tempo})", discursante])
        
        if discursantes_data:
            table_discursantes = Table(discursantes_data, colWidths=[120, 350])
            table_discursantes.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), AZUL_CLARO),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
            ]))
            table_discursantes.wrapOn(c, width, height)
            table_discursantes.drawOn(c, 50, y_pos - len(discursantes_data) * 20)
            y_pos -= len(discursantes_data) * 25
    
    # Hino Intermediário
    if detalhes_dict.get('hino_intermediario'):
        y_pos -= 20
        c.setFont("Helvetica-Bold", 12)
        c.drawString(50, y_pos, "HINO INTERMEDIÁRIO (3 min):")
        c.setFont("Helvetica", 12)
        c.drawString(230, y_pos, detalhes_dict.get('hino_intermediario', 'Não informado'))
    

    # Linha divisória
    y_pos -= 20
    c.setStrokeColor(colors.HexColor("#E2E8F0"))  # Cinza claro
    c.setLineWidth(3)
    c.line(50, y_pos, width - 50, y_pos)
    y_pos -= 12

    # SEÇÃO: AGRADECIMENTOS FINAIS
    y_pos -= 20
    c.setFillColor(AZUL_IGREJA)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(50, y_pos, "AGRADECIMENTOS FINAIS")
    
    y_pos -= 40
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 12)
    texto_agradecimentos = f"Agradecemos a presença e participação de todos, especialmente aqueles que contribuíram de alguma forma para que essa reunião acontecesse. E convidamos todos para que estejam aqui no próximo domingo. Ouviremos como último orador o(a) irmã(o) [NOME]. Logo após, cantaremos o hino {detalhes_dict.get('hino_encerramento', 'Não informado')}, e o(a) irmã(o) {detalhes_dict.get('oracao_encerramento', 'Não informado')} oferecerá a última oração. Desejamos a todos uma ótima semana e que o Espírito do Senhor os acompanhe."
    
    p_agradecimentos = Paragraph(texto_agradecimentos, estilo_paragrafo)
    p_agradecimentos.wrapOn(c, width - 100, height)
    p_agradecimentos.drawOn(c, 50, y_pos - 40)
    
    # SEÇÃO: ENCERRAMENTO
    y_pos -= 70
    c.setFillColor(AZUL_IGREJA)
    c.setFont("Helvetica-Bold", 15)
    c.drawString(50, y_pos, "ENCERRAMENTO (2 min)")
    
    # Hino e Oração de Abertura
    y_pos -= 20
    table_encerramento = Table([
        ["HINO DE ENCERRAMENTO:", 
         "ORAÇÃO DE ENCERRAMENTO:"],
        [f"{detalhes_dict.get('hino_encerramento', 'Não informado')}", 
         f"{detalhes_dict.get('oracao_encerramento', 'Não informado')}"]
    ], colWidths=[250, 250,250,250])
    
    table_encerramento.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), AZUL_CLARO),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    table_encerramento.wrapOn(c, width, height)
    table_encerramento.drawOn(c, 50, y_pos - 20)
    
    c.showPage()
    c.save()
    
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=f"ata_sacramental_{ata_id}.pdf", mimetype="application/pdf")

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