# functions/pdf_exporters.py
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import json 
from typing import Optional

# Tenta registrar DejaVuSans para acentuação; cai para Helvetica se não existir
try:
    pdfmetrics.registerFont(TTFont("DejaVuSans", "DejaVuSans.ttf"))
    pdfmetrics.registerFont(TTFont("DejaVuSansBold", "DejaVuSans-Bold.ttf")) # Registro para o Negrito
    DEFAULT_FONT = "DejaVuSans"
except Exception:
    DEFAULT_FONT = "Helvetica"

PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 15 * mm

ACCENT_COLOR = colors.HexColor("#0b4b71")
SECONDARY_COLOR = colors.HexColor("#2f855a")
LIGHT_GRAY = colors.HexColor("#f8f9fa")
DARK_TEXT = colors.HexColor("#1a202c")

styles = getSampleStyleSheet()

# 1. Definições de Estilo (Atualização dos estilos existentes)
styles['Normal'].fontName = DEFAULT_FONT
styles['Normal'].fontSize = 11
styles['Normal'].leading = 14
styles['Normal'].alignment = TA_LEFT
styles['Normal'].textColor = DARK_TEXT

# CORREÇÃO: Atualiza Heading4 (em vez de tentar adicioná-lo) para usar a fonte customizada em negrito.
# O ReportLab já carrega Heading4, então apenas atualizamos suas propriedades.
styles['Heading4'].fontName = "DejaVuSansBold" if DEFAULT_FONT == "DejaVuSans" else "Helvetica-Bold"
styles['Heading4'].fontSize = 12
styles['Heading4'].leading = 15
styles['Heading4'].alignment = TA_LEFT
styles['Heading4'].textColor = DARK_TEXT

# NOVO ESTILO: BodyStandard (13pt) para reduzir espaçamento e permitir 2 páginas
styles.add(ParagraphStyle(name='BodyStandard', 
                          parent=styles['Normal'],
                          fontName=DEFAULT_FONT, 
                          fontSize=13, 
                          leading=15)) # 13pt * 1.15 aprox.

# =========================================================================
# FUNÇÃO AUXILIAR PARA FORMATAR DATA (BASEADA NO SEU FILTRO JINJA)
# =========================================================================
def _format_date_for_pdf(value: str) -> str:
    """Converte 'AAAA-MM-DD' (formato DB) para 'DD/MM/AAAA'."""
    # O valor vem do DB como 'AAAA-MM-DD'.
    parts = value.split('-')
    if len(parts) == 3:
        # Formato: DD/MM/AAAA (parts[2]/parts[1]/parts[0])
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return value

# A função espera um argumento 'text' do tipo 'str'
def _replace_placeholders(text: str, ata: dict, detalhes: dict):
    if not text:
        return ""
    res = str(text)
    nome = ata.get("ala_nome") or ata.get("ala") or ""
    data = ata.get("data") or ""
    # Aplica formatação de data no placeholder [DATA]
    formatted_data = _format_date_for_pdf(data) 
    
    tema = (detalhes or {}).get("tema") or ""
    # NOTE: per user request, do NOT substitute [NOME] placeholders here; leave them verbatim in template texts.
    res = res.replace("[DATA]", formatted_data) # <--- Linha modificada
    res = res.replace("[TEMA]", tema)
    return res

def _wrap_text_lines(text, font_name, font_size, max_width):
    if not text:
        return []
    words = text.replace("\r", "").split()
    lines = []
    line = ""
    for w in words:
        candidate = w if line == "" else f"{line} {w}"
        width = pdfmetrics.stringWidth(candidate, font_name, font_size)
        if width <= max_width:
            line = candidate
        else:
            lines.append(line)
            line = w
    if line:
        lines.append(line)
    return lines


def _ensure_sequence(value):
    """Normaliza um valor que pode ser lista, JSON-string, newline-separated, ou vírgula-separated.
    Sempre retorna uma lista de strings limpas (sem entradas vazias).
    """
    if value is None:
        return []
    # Already a list/tuple
    if isinstance(value, (list, tuple)):
        return [str(v).strip() for v in value if v and str(v).strip()]

    # Strings: try to detect JSON array
    if isinstance(value, str):
        s = value.strip()
        # JSON array like '["nome"]'
        if s.startswith("[") and s.endswith("]"):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(v).strip() for v in parsed if v and str(v).strip()]
            except Exception:
                pass
        # newline-separated lines
        lines = [ln.strip() for ln in s.splitlines() if ln.strip()]
        if lines:
            return lines
        # comma-separated fallback
        if "," in s:
            parts = [p.strip() for p in s.split(",") if p.strip()]
            if parts:
                return parts
        # single value
        return [s]

    # Fallback para outros tipos
    return [str(value)]

# Aumentada a fonte padrão para 14pt, conforme solicitação
def _draw_wrapped(c, text, x, y, width, font_name=DEFAULT_FONT, font_size=13, leading=None, color=DARK_TEXT):
    if leading is None:
        leading = font_size * 1.2
    
    c.setFillColor(color)
    paragraphs = str(text).split("\n")
    
    # 1. Inicia o objeto de texto (essencial para setWordSpace)
    text_obj = c.beginText(x, y)
    text_obj.setFont(font_name, font_size)
    text_obj.setFillColor(color)

    y_current = y

    for p in paragraphs:
        p = p.strip()
        if p == "":
            # Lida com quebras de linha vazias
            y_current -= leading
            text_obj.moveCursor(0, -leading)
        else:
            lines = _wrap_text_lines(p, font_name, font_size, width)
            for i, ln in enumerate(lines):
                is_last_line = (i == len(lines) - 1)

                if not is_last_line:
                    line_width = pdfmetrics.stringWidth(ln, font_name, font_size)
                    space_needed = width - line_width
                    num_spaces = ln.count(' ')
                    
                    if num_spaces > 0 and space_needed > 0:
                        word_space_extra = space_needed / num_spaces
                        text_obj.setWordSpace(word_space_extra)
                    else:
                        text_obj.setWordSpace(0)
                            
                else:
                    text_obj.setWordSpace(0)

                text_obj.textLine(ln)
                y_current -= leading
                
                # Lógica de quebra de página
                if y_current < MARGIN:
                    c.drawText(text_obj)
                    c.showPage()
                    
                    y_current = PAGE_HEIGHT - MARGIN
                    text_obj = c.beginText(x, y_current)
                    text_obj.setFont(font_name, font_size)
                    text_obj.setFillColor(color)
                    text_obj.setWordSpace(0)

        text_obj.setWordSpace(0)

    # 4. Finaliza o último objeto de texto no canvas
    c.drawText(text_obj)
    
    return y_current

def _get_bold_font(font_name):
    """Retorna o nome da fonte em negrito apropriado."""
    if font_name == 'Helvetica':
        return 'Helvetica-Bold'
    return font_name + 'Bold'

# NOVA FUNÇÃO AUXILIAR PARA DESENHAR RÓTULO EM NEGRITO + VALOR (usado em ABERTURA, AÇÕES, ENCERRAMENTO)
def _draw_labeled_line(c, x, y, prefix, value, font_size=13, leading_extra=0):
    """Desenha um rótulo em negrito seguido por um valor na mesma linha, gerenciando Y e quebra de página."""
    leading = font_size * 1.2
    
    # 0. Quebra de página (check simples)
    if y - leading < MARGIN:
        c.showPage()
        y = PAGE_HEIGHT - MARGIN
    
    # 1. Desenha o prefixo (Negrito)
    c.setFont(_get_bold_font(DEFAULT_FONT), font_size) 
    c.setFillColor(DARK_TEXT)
    c.drawString(x, y, prefix)
    
    # 2. Calcula a largura do rótulo
    prefix_width = pdfmetrics.stringWidth(prefix, _get_bold_font(DEFAULT_FONT), font_size)
    
    # 3. Desenha o valor (Normal)
    value_x = x + prefix_width
    
    c.setFont(DEFAULT_FONT, font_size)
    # Nota: Assumindo que o valor é curto e não precisa de quebra de linha ou justificação
    c.drawString(value_x, y, str(value))
    
    # 4. Ajusta Y para a próxima linha
    return y - leading - leading_extra

def _section_title(c, text, x, y, font_name=DEFAULT_FONT, size=14, alignment=TA_CENTER):
    
    x_center = PAGE_WIDTH / 2
    
    c.setFillColor(ACCENT_COLOR)
    c.setFont(font_name, size) 
    
    c.drawCentredString(x_center, y, text) 
    
    # Espaçamento vertical reduzido para compactar (28 pontos)
    y -= 28
    c.setFillColor(DARK_TEXT)
    
    return y

def _check_space(c, y, min_height):
    """Verifica se há espaço suficiente para min_height, se não, força uma nova página."""
    if y - min_height < MARGIN:
        c.showPage()
        y = PAGE_HEIGHT - MARGIN
        return y
    return y

# Increased size from 11 to 13
def _section_label(c, text, x, y, font_name=DEFAULT_FONT, size=13):
    c.setFont(font_name, size)
    c.setFillColor(ACCENT_COLOR)
    c.drawString(x, y, text)
    c.setFillColor(DARK_TEXT)
    return y - (size * 1.3)

def _add_section(canvas, y, title_style, body_style, title_text="", body_text=""):
    """Adiciona um título e um parágrafo (body) no canvas, garantindo quebras de linha."""
    
    # 1. Adicionar o Título (se houver)
    if title_text:
        # Usa o Paragraph para lidar com texto formatado (bold, cor, etc.)
        p_title = Paragraph(title_text, title_style)
        w, h = p_title.wrapOn(canvas, PAGE_WIDTH - 2 * MARGIN, PAGE_HEIGHT)
        y -= h
        # Verifica se precisa de nova página antes de desenhar
        if y < MARGIN + h:
            canvas.showPage()
            y = PAGE_HEIGHT - MARGIN
            # Desenha o título na nova página
            p_title.drawOn(canvas, MARGIN, y - h)
            y -= h
        else:
            p_title.drawOn(canvas, MARGIN, y)
        y -= 3 # Espaçamento compacto
    
    # 2. Adicionar o Corpo do Texto (Body)
    if body_text:
        p_body = Paragraph(body_text, body_style)
        w, h = p_body.wrapOn(canvas, PAGE_WIDTH - 2 * MARGIN, PAGE_HEIGHT)
        
        # Verifica se o texto precisa de uma nova página
        if y < MARGIN + h:
            canvas.showPage()
            y = PAGE_HEIGHT - MARGIN
        
        y -= h # Subtrai a altura do texto antes de desenhar
        p_body.drawOn(canvas, MARGIN, y)
        y -= 3 # Espaçamento compacto
        
    return y

def _create_pdf_from_ata(ata: dict, detalhes: dict, template: Optional[dict]=None):
    if detalhes is None:
        detalhes = {}
    out = io.BytesIO()
    c = canvas.Canvas(out, pagesize=A4)
    
    # TRECHO CRÍTICO CORRIGIDO (Manter 'x' e 'y' inicializados)
    x = MARGIN
    y = PAGE_HEIGHT - MARGIN
    # FIM DO TRECHO CRÍTICO
    
    ala_nome = ata.get("ala_nome") or ata.get("ala") or "Ala Desconhecida"
    # Constante para quebra de página (baseada no novo tamanho de fonte)
    MIN_SECTION_HEIGHT = 45

    # =====================================
    # = HEADER (CENTRALIZADO - AMBOS 20pt)
    # =====================================

    # --- Conteúdo e Espaçamento ---
    title_text = f"Ata {str(ata.get('tipo') or '').capitalize()} - {str(ala_nome)} |"
    data_str = ata.get('data') or ''
    # 💥 LINHA MODIFICADA AQUI: Aplica a nova formatação
    date_text = _format_date_for_pdf(data_str) 
    space_width = 2 * mm 

    # --- 1. Cálculo da Largura Total ---
    W_title = pdfmetrics.stringWidth(title_text, DEFAULT_FONT, 18)
    W_date = pdfmetrics.stringWidth(date_text, DEFAULT_FONT, 18) # Usa date_text formatada

    W_total = W_title + space_width + W_date

    # --- 2. Cálculo do Ponto de Partida X (para centralização) ---
    X_center = PAGE_WIDTH / 2
    X_start_new = X_center - (W_total / 2)

    # --- 3. Desenho (Começa no novo X centralizado) ---

    X_current = X_start_new
    Y_base = y 

    # Título Principal (18pt, ACCENT_COLOR)
    c.setFont(DEFAULT_FONT, 18) 
    c.setFillColor(ACCENT_COLOR)
    c.drawString(X_current, Y_base, title_text)

    # Atualiza X para a posição da Data
    X_current += W_title + space_width 

    # Data ao Lado (18pt, colors.gray)
    c.setFont(DEFAULT_FONT, 18) 
    c.setFillColor(colors.gray)
    c.drawString(X_current, Y_base, date_text) # Usa date_text formatada

    # --- 4. Finalização ---

    y -= 16 
    x = MARGIN 
    c.setFillColor(DARK_TEXT) 

    y -= 12

    # =====================================
    # = BOAS VINDAS
    # =====================================

    y = _check_space(c, y, MIN_SECTION_HEIGHT)
    
    # CORREÇÃO Pylance (reportArgumentType - Linha 336): Garante que a string passada não é None
    # Show Boas Vindas if there is template text OR there are any of the small fields to display
    if template or any(detalhes.get(k) for k in ('presidido','dirigido','recepcionistas','pianista','regente_musica')):
        y = _section_title(c, "BOAS VINDAS", x, y)
        
        # Garante que 'boas_vindas' é uma string vazia se não existir ou se template for None
        boas_vindas_text = template.get('boas_vindas', "") if template else ""
        
        if boas_vindas_text:
            boas = _replace_placeholders(boas_vindas_text, ata, detalhes)
            y = _draw_wrapped(c, boas, x, y, PAGE_WIDTH - 2*MARGIN)
            y -= 12 # Ajuste do shift para 13pt (compactado)
        else:
            # Pequeno espaçamento caso não exista texto de boas-vindas
            y -= 4

        # Sempre exibir campos correspondentes (Presidido por, Dirigido por, Recepcionistas, Pianista, Regente de Música) se existirem
        if detalhes.get('presidido'):
            y = _draw_labeled_line(c, x, y, "Presidido por: ", detalhes.get('presidido'))
        if detalhes.get('dirigido'):
            y = _draw_labeled_line(c, x, y, "Dirigido por: ", detalhes.get('dirigido'))
        if detalhes.get('recepcionistas'):
            y = _draw_labeled_line(c, x, y, "Recepcionistas: ", detalhes.get('recepcionistas'))
        if detalhes.get('pianista'):
            y = _draw_labeled_line(c, x, y, "Pianista: ", detalhes.get('pianista'))
        if detalhes.get('regente_musica'):
            y = _draw_labeled_line(c, x, y, "Regente de Música: ", detalhes.get('regente_musica'))
        y -= 8

    # =====================================
    # = ABERTURA (REFATORADO PARA NEGRITO)
    # =====================================

    y = _check_space(c, y, MIN_SECTION_HEIGHT)
    
    # CORREÇÃO: Ocultar o título se for PDF Simples
    if template:
        y = _section_title(c, "ABERTURA", x, y)

    # Substituído o '\n'.join() por chamadas _draw_labeled_line individuais
    # (Presidido/Dirigido/Recepcionistas agora exibidos após Boas Vindas para melhor leitura)
    # Reconhecemos a presença: lista ou string (normalizar com _ensure_sequence)
    reconhecemos = _ensure_sequence(detalhes.get('reconhecemos_presenca'))
    for nome in reconhecemos:
        y = _draw_labeled_line(c, x, y, "Reconhecemos: ", nome)
    if detalhes.get('hino_abertura'):
        y = _draw_labeled_line(c, x, y, "Hino: ", detalhes.get('hino_abertura'))
    # Exibir Oração de Abertura (vazia quando ausente)
    y = _draw_labeled_line(c, x, y, "Oração: ", detalhes.get('oracao_abertura') or '')
    y -= 12 # Espaçamento final após o bloco ABERTURA (compactado)


    # ... código após a seção ABERTURA
    if detalhes.get('anuncios'):
        y = _check_space(c, y, MIN_SECTION_HEIGHT)
        anuncios = _ensure_sequence(detalhes.get('anuncios'))
        y = _section_label(c, "Anúncios:", x, y)
        for anuncio in anuncios:
            y = _draw_wrapped(c, anuncio, x, y, PAGE_WIDTH - 2*MARGIN)
        y -= 12 # Espaçamento final após o bloco (compactado)

    # =====================================
    # = AÇÕES (DISTANCIAMENTO REDUZIDO)
    # =====================================
    from reportlab.lib.enums import TA_JUSTIFY
    styles['BodyStandard'].alignment = TA_JUSTIFY

    action_fields = [
        ("desobrigacoes", "desobrigacoes", "Desobrigações"),
        ("apoios", "apoios", "Apoios"),
        ("confirmacoes_batismo", "confirmacoes_batismo", "Confirmações Batismais"),
        ("apoio_membro_novo", "apoio_membros", "Apoio a Novos Membros"),
        ("bencao_crianca", "bencao_criancas", "Bênção de Crianças"),
    ]

    def _has_names_for(key):
        seq = _ensure_sequence(detalhes.get(key))
        return bool(seq)

    has_real_data = any(_has_names_for(d_key) for _, d_key, _ in action_fields)

    # Se não houver nomes em nenhuma das AÇÕES, pulamos toda a seção AÇÕES (não mostrar título nem texto)
    if has_real_data:
        y = _check_space(c, y, MIN_SECTION_HEIGHT)

        for t_key, d_key, label in action_fields:
            detalhe_itens = detalhes.get(d_key)
            
            if detalhe_itens:
                seq = _ensure_sequence(detalhe_itens)
                if not seq: continue

                # Header da seção (ex.: "Desobrigações:") seguido de linha em branco
                full_text = f'<b><font size="13" color="{ACCENT_COLOR.hexval()}">{label}:</font></b><br/><br/>'

                # Texto do template (em itálico) com linha em branco após, se existir
                template_text = (template.get(t_key, "") if template else "")
                if template_text:
                    try:
                        final_template_text = _replace_placeholders(template_text, ata, detalhes={})
                        final_template_text = str(final_template_text).replace('\n', '<br/>').replace('\r', '')
                        full_text += f'<i>{final_template_text}</i><br/><br/>'
                    except: pass

                # Lista de nomes: cada um aparece em sua própria linha como "Nome n: <nome>", com 'Nome n:' em negrito (fonte explícita)
                bold_font = _get_bold_font(DEFAULT_FONT)
                names_lines = [f"<font name=\"{bold_font}\">Nome {i+1}:</font> {n}" for i, n in enumerate(seq)]
                full_text += '<br/>'.join(names_lines)

                final_content = str(full_text).replace('\n', '<br/>')

                try:
                    y = _add_section(c, y, styles['BodyStandard'], styles['BodyStandard'], "", final_content)
                    y -= 12 
                except Exception as e:
                    print(f"Erro na renderização: {e}")
        y -= 10
    else:
        # não imprime nada (seção omitida)
        pass

    # =====================================
    # = SACRAMENTO (AJUSTE PREVENTIVO)
    # =====================================

    # ===== SACRAMENTO: MEDIÇÃO PRECISA E QUEBRA PREVENTIVA =====
    # Usamos Paragraph.wrap para medir com precisão a altura necessária para o texto do sacramento
    # (mais robusto que contar linhas manualmente), e somamos a altura estimada do hino e do título.
    sacramento_text_raw = template.get('sacramento', "") if template else ""
    sacramento_text = _replace_placeholders(sacramento_text_raw, ata, detalhes) if sacramento_text_raw else ""

    sac_body_height = 0
    try:
        if sacramento_text:
            # Wrap sem desenhar para medir altura real do parágrafo
            p = Paragraph(str(sacramento_text).replace('\r\n', '\n'), styles['BodyStandard'])
            w, h = p.wrap(PAGE_WIDTH - 2 * MARGIN, PAGE_HEIGHT)
            sac_body_height = h
    except Exception:
        # fallback: estimativa por linhas caso Paragraph falhe
        est_lines = 0
        if sacramento_text:
            for p_txt in str(sacramento_text).split('\n'):
                if not p_txt.strip():
                    est_lines += 1
                else:
                    est_lines += len(_wrap_text_lines(p_txt, DEFAULT_FONT, 13, PAGE_WIDTH - 2*MARGIN))
        sac_body_height = est_lines * (13 * 1.2)

    # Hino ocupa aproximadamente uma linha (leading)
    hino_height = (13 * 1.2) if detalhes.get('hino_sacramental') else 0

    title_height = 28 if template else 0
    padding = 12
    estimated_height = title_height + sac_body_height + hino_height + padding

    # Se não couber todo o bloco SACRAMENTO na página atual, pula para a próxima
    if y - estimated_height < MARGIN:
        c.showPage()
        y = PAGE_HEIGHT - MARGIN

    # Agora desenhar a seção como antes
    if template:
        y = _section_title(c, "SACRAMENTO", x, y)

    if sacramento_text:
        y = _check_space(c, y, MIN_SECTION_HEIGHT)
        y = _draw_wrapped(c, str(sacramento_text), x, y, PAGE_WIDTH - 2*MARGIN)
        # Espaçamento extra: linha em branco antes do Hino Sacramental
        y -= 8

    # Desenhamos o hino separadamente com o prefixo negrito
    if detalhes.get('hino_sacramental'):
        y = _check_space(c, y, MIN_SECTION_HEIGHT)
        y = _draw_labeled_line(c, x, y, "Hino Sacramental: ", detalhes.get('hino_sacramental'))

    y -= 12 # Espaçamento final (compactado)
    # =====================================
    # = MENSAGENS (CORRIGIDO)
    # =====================================

    y = _check_space(c, y, MIN_SECTION_HEIGHT)
    
    # CORREÇÃO: Ocultar o título se for PDF Simples
    if template:
        y = _section_title(c, "MENSAGENS", x, y)
        
    # CORREÇÃO Pylance (reportArgumentType - Linha 527): Garante que a string passada não é None
    if template:
        mensagens_text = template.get('mensagens', "") # Garante string vazia
        if mensagens_text:
            msg_text = _replace_placeholders(mensagens_text, ata, detalhes)
            y = _draw_wrapped(c, msg_text, x, y, PAGE_WIDTH - 2*MARGIN)
            y -= 10 

    # Discursantes, temas e observações
    discursantes_seq = _ensure_sequence(detalhes.get('discursantes'))

    # Se não houver 'discursantes' normalizados, tentar montar a partir das colunas individuais
    if not any(discursantes_seq) and any(k in (detalhes or {}) for k in ('discursante_1', 'discursante_2', 'ultimo_discursante')):
        constructed = [detalhes.get('discursante_1', ''), detalhes.get('discursante_2', ''), detalhes.get('ultimo_discursante', '')]
        discursantes_seq = [s for s in constructed if s and str(s).strip()]

    # Tenta recuperar temas/obs como listas ('temas'/'obs'), senão usa tema_1.. e obs_1..
    temas_raw = detalhes.get('temas')
    if temas_raw:
        temas = _ensure_sequence(temas_raw)
    else:
        temas = [detalhes.get(f'tema_{i+1}', '') for i in range(len(discursantes_seq))]

    obs_raw = detalhes.get('obs')
    if obs_raw:
        obs = _ensure_sequence(obs_raw)
    else:
        obs = [detalhes.get(f'obs_{i+1}', '') for i in range(len(discursantes_seq))]

    if any(discursantes_seq):
        # Exibe um rótulo para os discursantes mesmo sem texto de 'mensagens'
        y = _section_label(c, "Discursantes:", x, y)
        # Remover o último discursante apenas nesta sessão (será exibido no ENCERRAMENTO como 'Último Discursante')
        msg_discursantes = discursantes_seq[:-1] if len(discursantes_seq) > 1 else []

        # Construir conteúdo HTML com apenas o nome em negrito (sem temas/obs)
        from html import escape
        lines = []
        for i, d in enumerate(msg_discursantes):
            if d and str(d).strip():
                name = escape(str(d).strip())
                lines.append(f"{i+1}º - <b>{name}</b>")

        if lines:
            body_html = '<br/>'.join(lines)
            try:
                y = _add_section(c, y, styles['BodyStandard'], styles['BodyStandard'], "", body_html)
                y -= 3
            except Exception as e:
                # Fallback para desenho linha a linha em caso de erro
                for i, d in enumerate(msg_discursantes):
                    if d and str(d).strip():
                        linha = f"{i+1}º - {d}"
                        y = _draw_wrapped(c, linha, x, y, PAGE_WIDTH - 2*MARGIN)
                y -= 10

    # Hino Intermediário (Agora usando a nova função)
    if detalhes.get('hino_intermediario'):
        y -= 10
        y = _draw_labeled_line(c, x, y, "Hino Intermediário: ", detalhes.get('hino_intermediario'))
        y -= 12
    
    # =====================================
    # = ENCERRAMENTO (REFATORADO PARA NEGRITO)
    # =====================================

    y = _check_space(c, y, MIN_SECTION_HEIGHT)
    
    # CORREÇÃO: Ocultar o título se for PDF Simples
    if template:
        y = _section_title(c, "ENCERRAMENTO", x, y)

    # 1. Texto de Encerramento do Template
    # CORREÇÃO Pylance (reportArgumentType - Linha 562): Garante que a string passada não é None
    if template:
        encerramento_text = template.get('encerramento', "") # Garante string vazia
        if encerramento_text:
            enc_text = _replace_placeholders(encerramento_text, ata, detalhes)
            y = _draw_wrapped(c, enc_text, x, y, PAGE_WIDTH - 2*MARGIN)
            y -= 12 # Espaçamento após o texto do encerramento (compactado)

    if detalhes.get('ultimo_discursante'):
        y = _draw_labeled_line(c, x, y, "Último Discursante: ", detalhes.get('ultimo_discursante'))
        y -= 10 

    # 2. Hino de Encerramento (Usando _draw_labeled_line)
    if detalhes.get('hino_encerramento'):
        y = _draw_labeled_line(c, x, y, "Hino de Encerramento: ", detalhes.get('hino_encerramento'))
        y -= 10 # Espaçamento vertical compacto

    # 3. Oração de Encerramento — exibir (vazia quando ausente)
    y = _draw_labeled_line(c, x, y, "Oração de Encerramento: ", detalhes.get('oracao_encerramento') or '')
    y -= 10 # Espaçamento vertical compacto
    
    # =====================================
    # = FOOTER 
    # =====================================
    
    # Nota: O bloco do footer está comentado na sua versão original. 
    
    # c.showPage()
    c.save()
    out.seek(0)
    return out

# API pública
def exportar_pdf_bytes(ata, detalhes=None, template=None, filename="ata.pdf"):
    """
    Gera PDF e retorna (BytesIO_buffer, filename, mimetype).
    """
    if not isinstance(ata, dict):
        html_string = str(ata or "")
        buf = io.BytesIO()
        c = canvas.Canvas(buf, pagesize=A4)
        c.setFont(DEFAULT_FONT, 13) # Ajustado para 13pt
        y = PAGE_HEIGHT - MARGIN
        for ln in html_string.splitlines():
            c.drawString(MARGIN, y, ln[:200])
            y -= 12 # Ajustado e compactado
            if y < MARGIN:
                c.showPage()
                c.setFont(DEFAULT_FONT, 13) # Ajustado para 13pt
                y = PAGE_HEIGHT - MARGIN
        c.save()
        buf.seek(0)
        return buf, filename, "application/pdf"

    buffer = _create_pdf_from_ata(ata, detalhes or {}, template)
    buffer.seek(0)
    return buffer, filename, "application/pdf"

def exportar_sacramental_bytes(ata, detalhes=None, template=None, filename="ata_sacramental.pdf"):
    return exportar_pdf_bytes(ata, detalhes=detalhes, template=template, filename=filename)