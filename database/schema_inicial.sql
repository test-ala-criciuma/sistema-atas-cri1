PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

-- Tabela de usuários (alas)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL
);

INSERT OR IGNORE INTO users (id, username, password) VALUES 
(1, 'Criciuma1', 'scrypt:32768:8:1$Qu1BZhRMR349TZiY$c322fadd87d3fd4519be46176f79c94186ea48cf3a93344a0cea289fbbc485405259d101a58c052cd02cd80d017b6a3602278922b384ac730681890986ccd1b4'),
(2, 'Criciuma2', 'scrypt:32768:8:1$S6rVkZQbtDYIFqLz$0c168cc1d6f7bc072e88c58e564ad67e13da439f1e6f53c7b517cb09816e7bb6f09175bf041c1e56b8ec6ac6ac5ed0f0b524167e6fb13b2ffb2c292145481868'),
(3, 'Criciuma3', 'scrypt:32768:8:1$5SQoZ5M4XzCvm3jZ$fbdab8cd2ff635753488b50a18947ae2a545e5cd620f8d399816647a7ebf28ec3e7f60e2a9f3ab0ac678f4026e0fc8f75d08b681cf0cfabfecc1474885973ba2'),
(4, 'Ararangua', 'scrypt:32768:8:1$qy8eJW1FycasTUrt$e59a1a7f661dfcd642850b0fd38e9b3b533a02d0818aede85df179a93f47bd47abf821a5718fab0676bf95e0a35ea9a189a3fd3224215dd8dacfb7fffea2e554'),
(5, 'Icara', 'scrypt:32768:8:1$w3AcozJUGDUxmgtS$f2fef123c2a55b88f5e59adeda5936e6cd5186c082d96f0b0075a751301960ec871499fbfce9a21eb19c682517b4a9037bde07ac9fcbccc99a07562b1fb1c706');

-- Tabela principal de atas
CREATE TABLE IF NOT EXISTS atas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    data TEXT NOT NULL,
    status TEXT DEFAULT 'pendente',
    ala_id INTEGER NOT NULL,
    FOREIGN KEY(ala_id) REFERENCES users(id)
);

-- Tabela para atas sacramentais
CREATE TABLE IF NOT EXISTS sacramental (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ata_id INTEGER,
    presidido TEXT,
    dirigido TEXT,
    pianista TEXT,
    regente_musica TEXT,
    anuncios TEXT,
    hinos TEXT,
    hino_sacramental TEXT,
    hino_intermediario TEXT,
    oracoes TEXT,
    discursantes TEXT,
    recepcionistas TEXT,
    reconhecemos_presenca TEXT,
    desobrigacoes TEXT,
    apoios TEXT,
    confirmacoes_batismo TEXT,
    apoio_membros TEXT,
    bencao_criancas TEXT,
    ultimo_discursante TEXT,
    id_tipo INTEGER,
    tema TEXT,
    FOREIGN KEY(ata_id) REFERENCES atas(id),
    FOREIGN KEY(id_tipo) REFERENCES templates(id)
);

-- Tabela para atas de batismo
CREATE TABLE IF NOT EXISTS batismo (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ata_id INTEGER,
    dedicado TEXT,
    presidido TEXT,
    dirigido TEXT,
    batizados TEXT,
    testemunha1 TEXT,
    testemunha2 TEXT,
    FOREIGN KEY(ata_id) REFERENCES atas(id) ON DELETE CASCADE
);

-- Tabela para estacas
CREATE TABLE IF NOT EXISTS estacas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL UNIQUE,
    presidente TEXT,
    primeiro_conselheiro TEXT,
    segundo_conselheiro TEXT
);

INSERT OR IGNORE INTO estacas (id, nome, presidente, primeiro_conselheiro, segundo_conselheiro) VALUES
(1, 'Criciúma', 'Alexandre Goulart Pacheco', 'Rafael Atanázio Duarte de Sá', 'Mateus Dal Toé');

-- Tabela para unidades (alas)
CREATE TABLE IF NOT EXISTS unidades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ala_id INTEGER NOT NULL,
    nome TEXT,
    bispo TEXT,
    primeiro_conselheiro TEXT,
    segundo_conselheiro TEXT,
    estaca_id INTEGER NOT NULL DEFAULT 1,
    horario TEXT,
    FOREIGN KEY(ala_id) REFERENCES users(id),
    FOREIGN KEY(estaca_id) REFERENCES estacas(id)
);

INSERT OR IGNORE INTO unidades (id, ala_id, nome, bispo, primeiro_conselheiro, segundo_conselheiro, estaca_id, horario) VALUES
(1, 1, 'Ala Criciúma 1', 'Julio Davila', 'Antonio Carlos de Souza', 'Ari Cesar Albeche Lopes', 1, '09:30 - 10:30'),
(2, 2, 'Ala Criciúma 2', 'alterar', 'alterar', 'alterar', 1, 'alterar'),
(3, 3, 'Ala Criciúma 3', 'alterar', 'alterar', 'alterar', 1, 'alterar'),
(4, 4, 'Ala Içara', 'alterar', 'alterar', 'alterar', 1, 'alterar'),
(5, 5, 'Ala Araranguá', 'alterar', 'alterar', 'alterar', 1, 'alterar');

-- Tabela para templates (padrões de atas)
CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_template INTEGER NOT NULL,
    nome TEXT NOT NULL,
    boas_vindas TEXT NOT NULL,
    desobrigacoes TEXT NOT NULL,
    apoios TEXT,
    confirmacoes_batismo TEXT NOT NULL,
    apoio_membro_novo TEXT NOT NULL,
    bencao_crianca TEXT NOT NULL,
    sacramento TEXT NOT NULL,
    mensagens TEXT NOT NULL,
    live TEXT NOT NULL,
    encerramento TEXT NOT NULL
);

INSERT OR IGNORE INTO templates (tipo_template, nome, boas_vindas, desobrigacoes, apoios, confirmacoes_batismo, apoio_membro_novo, bencao_crianca, sacramento, mensagens, live, encerramento) 
VALUES
(
    1,
    'Sacramental Padrão',
    'Bom dia irmãos e irmãs! Gostaríamos de fazer todos muito bem vindos a mais uma Reunião Sacramental da ALA [NOME], Estaca Criciúma, neste dia [DATA]. Desejamos que todos se sintam bem entre nós, especialmente aqueles que nos visitam.',
    'É proposto dar um voto de agradecimento aos serviços prestados pelo(a) irmã(o) [NOME] que serviu como [CHAMADO]. Todos os que desejam se manifestar, levantem a mão',
    'O(a) irmã(o) [NOME] está sendo chamado(a) como [CHAMADO]. Todos que forem a favor manifestem-se. Os que forem contrários, manifestem-se',
    'O(a) irmã(o) [NOME] foram batizados, gostaríamos de convida-los(a) para virem até o púlpito para que possamos fazer sua confirmação como Membro de A Igreja de Jesus Cristo dos Santos dos Ultimos Dias.',
    'O(a) irmã(o) [NOME] foi batizado e confirmado membro da igreja, e gostaríamos do apoio de todos os irmãos de plena aceitação como mais novo membro da ala. Todos a favor, manifestem-se',
    'Gostaríamos de chamar ao púlpito o irmão [NOME] que irá dar a benção de apresentação da(o) [NOME DA CRIANÇA], filho(a) de [NOME DOS PAIS].',
    'Passaremos ao Sacramento, que é a parte mais importante de nossa reunião. Cantaremos como Hino Sacramental [NOME], o Sacramento será abençoado e distribuído a todos',
    'Agradecemos a todos pela reverência durante o Sacramento. Passaremos agora a parte dos discursantes. Ouviremos primeiro o(a) irmã(o) [NOME]. Depois, ouviremos o(a) irmã(o) [NOME]. Em seguida cantaremos o hino [NOME], em pé, ao sinal do(a) regente.',
    'Gostaria de lembrar todos que estejam assistindo a transmissão da reunião, que se identifiquem para que possamos contá-los também',
    'Agradecemos a presença e participação de todos, especialmente aqueles que contribuíram de alguma forma para que essa reunião acontecesse. E convidamos todos para que estejam aqui no próximo domingo. Ouviremos como último orador o(a) irmã(o) [NOME]. Logo após, cantaremos o hino [NOME], e o(a) irmã(o) [NOME] oferecerá a última oração. Desejamos a todos uma ótima semana e que o Espírito do Senhor os acompanhe.'
),
(
    2,
    'Testemunhos',
    'Bom dia irmãos e irmãs! Gostaríamos de fazer todos muito bem vindos a mais uma Reunião Sacramental da ALA [NOME], Estaca Criciúma, neste dia [DATA]. Desejamos que todos se sintam bem entre nós, especialmente aqueles que nos visitam.',
    'É proposto dar um voto de agradecimento aos serviços prestados pelo(a) irmã(o) [NOME] que serviu como [CHAMADO]. Todos os que desejam se manifestar, levantem a mão',
    'O(a) irmã(o) [NOME] está sendo chamado(a) como [CHAMADO]. Todos que forem a favor manifestem-se. Os que forem contrários, manifestem-se',
    'O(a) irmã(o) [NOME] foram batizados, gostaríamos de convida-los(a) para virem até o púlpito para que possamos fazer sua confirmação como Membro de A Igreja de Jesus Cristo dos Santos dos Ultimos Dias.',
    'O(a) irmã(o) [NOME] foi batizado e confirmado membro da igreja, e gostaríamos do apoio de todos os irmãos de plena aceitação como mais novo membro da ala. Todos a favor, manifestem-se',
    'Gostaríamos de chamar ao púlpito o irmão [NOME] que irá dar a benção de apresentação da(o) [NOME DA CRIANÇA], filho(a) de [NOME DOS PAIS].',
    'Passaremos ao Sacramento, que é a parte mais importante de nossa reunião. Cantaremos como Hino Sacramental [NOME], o Sacramento será abençoado e distribuído a todos',
    'Agradecemos a todos pela reverência durante o Sacramento. Hoje é nossa reunião de Jejum e Testemunhos. Gostaríamos de convidar todos a prestar seus testemunhos de forma breve e direta, dando assim tempo para que o máximo de irmãos tenham este privilégio.',
    'Gostaria de lembrar todos que estejam assistindo a transmissão da reunião, que se identifiquem para que possamos contá-los também',
    'Agradecemos a presença e participação de todos, especialmente aqueles que contribuíram de alguma forma para que essa reunião acontecesse. E convidamos todos para que estejam aqui no próximo domingo. Cantaremos o último hino [NOME] e o(a) irmã(o) [NOME] oferecerá a última oração.'
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_atas_ala_id ON atas(ala_id);
CREATE INDEX IF NOT EXISTS idx_atas_data ON atas(data);
CREATE INDEX IF NOT EXISTS idx_atas_tipo ON atas(tipo);
CREATE INDEX IF NOT EXISTS idx_sacramental_ata_id ON sacramental(ata_id);
CREATE INDEX IF NOT EXISTS idx_batismo_ata_id ON batismo(ata_id);
CREATE INDEX IF NOT EXISTS idx_unidades_ala_id ON unidades(ala_id);
CREATE INDEX IF NOT EXISTS idx_unidades_estaca_id ON unidades(estaca_id);

COMMIT;
PRAGMA foreign_keys = OFF;