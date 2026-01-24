Sistema web para gerenciamento de atas de reuniões.

**📋 Funcionalidades**
---

Autenticação por Unidades cadastradas: Login separado para cada unidade.

Gestão de atas de reuniões: Criação, edição e visualização de atas.

Exportação para PDF: Geração de PDFs formatados para atas.

Sincronização em Tempo Real: Edição colaborativa em tempo real usando WebSockets

Filtro por Mês: Visualização de atas por mês específico

Próxima Reunião: Lembretes automáticos da próxima reunião na página inicial.

**🚀 Tecnologias Utilizadas**
---

Backend: Flask (Python)

Frontend: HTML5, CSS3, JavaScript

Banco de Dados: SQLite

Tempo Real: Flask-SocketIO

PDF: ReportLab

Deploy: 

**📦 Instalação**
---

Pré-requisitos
Python 3.8+

pip (gerenciador de pacotes Python)

*Passos para instalação:*

Clone o repositório

```bash
git clone <url-do-repositorio>
cd sistema-atas
```

Crie um ambiente virtual

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scriptsctivate  # Windows
```

Instale as dependências

```bash
pip install -r requirements.txt
```

Configure o banco de dados

```bash
# O banco será criado automaticamente na primeira execução
mkdir database
```

Execute a aplicação

```bash
python app.py
```

Acesse no navegador

```
http://localhost:5000
```


**🗃️ Estrutura do Banco de Dados**
---
**Tabelas Principais**
- `users`: Usuários do sistema
- `atas`: Registros principais das atas
- `sacramental`: Detalhes das atas sacramentais
- `batismo`: Detalhes dos serviços batismais

**Campos das Atas Sacramentais**
- Presidido por
- Dirigido por
- Pianista
- Regente de música
- Anúncios
- Hinos (abertura, sacramental, intermediário, encerramento)
- Orações (abertura, encerramento)
- Discursantes

**Campos dos Batismos**
- Presidido por
- Dirigido por
- Dedicado a
- Pessoas batizadas
- Testemunhas

**🎯 Como Usar**
---
1. **Login**
   - Acesse o sistema com as credenciais da sua ala
   - Cada ala só visualiza e gerencia suas próprias atas

2. **Criar Nova Ata**
   - Clique em "Criar Nova Ata"
   - Selecione o tipo (Sacramental ou Batismo)
   - Escolha a data da reunião/evento

3. **Preencher Formulário**
   - Preencha todos os campos relevantes
   - Use o botão "+" para adicionar múltiplos discursantes/anúncios/batizados
   - Os campos são sincronizados em tempo real para edição colaborativa

4. **Visualizar e Editar**
   - Visualize atas existentes na página inicial
   - Use o filtro por mês para encontrar atas específicas
   - Edite atas clicando no botão de edição

5. **Exportar PDF**
   - Gere PDFs formatados para atas sacramentais
   - Exporte PDFs simples para batismos

🔧 Desenvolvimento
---
**Estrutura de Arquivos**
```text
sistema-atas/
├── app.py                 # Aplicação principal Flask
├── requirements.txt       # Dependências Python
├── render.yaml            # Configuração de deploy
├── database/
│   └── schema.sql         # Esquema do banco de dados
├── templates/             # Templates HTML
│   ├── base.html
│   ├── login.html
│   ├── index.html
│   ├── nova_ata.html
│   ├── sacramental.html
│   ├── batismo.html
│   ├── visualizar_ata.html
│   └── _atas_list.html
└── static/
    └── css/
        └── style.css      # Estilos CSS
```

**Variáveis de Ambiente**
```bash
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=False
PORT=5000
```

**Comandos Úteis**
Executar em modo desenvolvimento:
```bash
python app.py
```

Executar em produção:
```bash
gunicorn app:app
```

Recriar banco de dados (local):
```bash
# Delete o arquivo database/atas.db e reinicie a aplicação
```

Railway — Persistent Disk (Recomendado para deploy) 🔧

- Crie um **Persistent Disk** no painel do Railway e faça o mount no serviço (ex: `/data`).
- Defina a variável de ambiente do serviço `DB_PATH` com o caminho desejado, por exemplo `DB_PATH=/data/atas.db`.
- Faça deploy; a aplicação irá escrever o arquivo de SQLite em `DB_PATH` e ele permanecerá entre deploys.

Como semear o DB existente (opção simples):

1. Baixe o backup atual usando o endpoint de backup do app (recomendado usar variável de ambiente `BACKUP_PASSWORD`):

- Defina a variável (no Railway UI -> Variables):
  - `BACKUP_PASSWORD=uma-senha-secreta` 

- Em seguida faça a requisição de download do backup (exemplo usando a variável local):

```bash
# download sem login, usando BACKUP_PASSWORD
curl -L -X POST -F "password=$BACKUP_PASSWORD" https://SEU_APP/configuracoes/backup -o atas.db
```

# Alternativa (quando você está logado no app — RECOMENDADO)
- A forma mais simples é realizar o download pelo navegador:
  1. Faça login no app via browser.
  2. Vá em **Configurações** → **Ferramentas do Sistema** → clique no botão **Backup** (o download será iniciado sem precisar informar senha).

> Observação: se você não estiver logado via UI, o prompt solicitará a senha — ele vem pré‑preenchido com `Lucas@2001` por conveniência. Não existe fallback para `BACKUP_PASSWORD` no servidor; se `BACKUP_PASSWORD` não estiver definida, a chamada por API retornará erro 500.
2. Hospede `atas.db` temporariamente (ex: S3, GitHub releases, transfer.sh).
3. Conecte-se ao container do Railway e baixe o arquivo para o `DB_PATH`:
```bash
railway run bash
# no shell do container:
curl -o "$DB_PATH" https://LINK_PARA_SEU/atas.db
```

Iniciar o DB do zero (ex.: Railway)

> Criamos scripts utilitários em `scripts/` para facilitar: `scripts/check_db.sh` e `scripts/reset_db.sh`.

1. Fazer backup / reset (UI shell ou CLI)

- Pelo UI (recomendado — abre shell no container com o volume montado):
  - Project → Service `web` → **Connect / Open Shell**
  - No shell, rode:
    ```bash
    # Verificar caminho e conteúdo
    echo "$DB_PATH"
    ls -la "$(dirname "$DB_PATH")" || true
    ls -la "$(dirname "$DB_PATH")/backups" || true

    # Checar DB
    bash scripts/check_db.sh

    # Para restaurar o BACKUP mais recente (após validar):
    bash scripts/restore_from_latest.sh

    # Rodar reset (cria backup automático e recria DB) se preferir criar um DB limpo
    bash scripts/reset_db.sh
    ```

- Fazer download do backup para sua máquina local:
  ```bash
  export BACKUP_PASSWORD='sua_senha'
  ./scripts/download_backup.sh ./atas.db
  # Verifique localmente:
  python3 - <<PY
  b=open('atas.db','rb').read(64)
  print('is SQLite?', b.startswith(b"SQLite format 3\\x00"))
  PY
  ```

- Se quiser enviar um backup local para o serviço:
  ```bash
  ./scripts/upload_backup_to_service.sh ./atas.db
  ```

Automatic scheduled job (Railway) 🕘

- Create a scheduled job in Railway that runs the backup daily. Set these environment variables in the **Service** Environment in Railway:
  - `BACKUP_PASSWORD` (required)
  - `BACKUP_URL` (optional, defaults to https://to-gather.up.railway.app/configuracoes/backup)
  - `BACKUP_DIR` (optional, defaults to /data/backups)
  - `BACKUP_RETENTION` (optional, how many backup files to keep, default 7)

- Command to run in the scheduled job (use the UI to add a job that runs this command):
  ```bash
  bash scripts/backup_job.sh
  ```

- The job will save validated backups to `/data/backups` and keep last `BACKUP_RETENTION` files.


- Via CLI (quando o `railway run` monta volumes no ambiente que você precisa):
  ```bash
  # executa o reset no serviço web
  railway run --service web bash -lc 'bash scripts/reset_db.sh'

  # lista tabelas
  railway run --service web bash -lc 'bash scripts/check_db.sh'
  ```

2. Comandos diretos (sem scripts):
```bash
# criar backup (manual)
railway run --service web bash -lc 'if [ -f "$DB_PATH" ]; then mkdir -p "$(dirname "$DB_PATH")/backups" && cp "$DB_PATH" "$(dirname "$DB_PATH")/backups/atas.db.bak.$(date +%Y%m%d_%H%M%S)"; fi'

# resetar via utilitário do projeto
railway run --service web bash -lc 'python reset_db.py'

# listar tabelas
railway run --service web bash -lc 'sqlite3 "$DB_PATH" "SELECT name FROM sqlite_master WHERE type=\'table\' ORDER BY name;"'
```

3. Tornar scripts executáveis localmente (opcional)
```bash
chmod +x scripts/check_db.sh scripts/reset_db.sh
```

Observação: não commite o arquivo `database/atas.db` no repositório — mantenha-o em `.gitignore` (já está configurado).


**🐛 Solução de Problemas**
---
**Erros Comuns**
- Erro de importação:
```bash
pip install -r requirements.txt
```
- Erro de banco de dados:
```bash
rm database/atas.db
# Reinicie a aplicação
```
- Erro de porta em uso:
```bash
# Altere a porta no app.py ou use:
python app.py --port 5001
```

**Logs**
- Desenvolvimento:
  - Os logs aparecem no terminal

**🔄 Fluxo de Trabalho**
- Login: Usuário faz login com credenciais da ala
- Dashboard: Visualiza atas existentes e próxima reunião
- Criação: Seleciona tipo de ata e data
- Preenchimento: Preenche formulário específico (sacramental/batismo)
- Salvamento: Dados são salvos no banco com ID da ala
- Visualização: Pode visualizar, editar ou exportar a ata
- Exportação: Gera PDF formatado para impressão

**🛠️ API Endpoints**

| Método     | Rota                                              | Descrição                          |
|-------------|-------------------------------------|-----------------------------|
| GET            | /                                                   | Página de login                 |
| POST          | /                                                   | Processar login                 |
| GET            | /index                                           | Dashboard principal         |
| GET            | /logout                                         | Logout do sistema            |
| GET/POST  | /ata/nova                                     | Criar nova ata                    |
| GET/POST  | /ata/form                                     | Formulário de ata              |
| GET            | /ata/<id>                                     | Visualizar ata                     |
| GET            | /ata/editar/<id>                          | Editar ata                           |
| GET            | /ata/excluir/<id>                         | Excluir ata                          |
| GET            | /ata/exportar/<id>                      | Exportar PDF simples         |
| GET            | /ata/exportar_sacramental/<id> | Exportar PDF formatado    |
| GET            | /atas/mes/<mes>                        | Listar atas por mês (AJAX) |

**🔒 Segurança**
- Autenticação por sessão
- Separação de dados por ala
- Proteção contra CSRF
- Validação de entrada de dados



**🤝 Suporte**
Para suporte ou problemas técnicos, entre em contato com:
Thales - Desenvolvedor

Versão: 1.0
Última atualização: Outubro 2025