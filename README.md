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

Recriar banco de dados:
```bash
# Delete o arquivo database/atas.db e reinicie a aplicação
```

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