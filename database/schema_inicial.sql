PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

-- Tabela de usuários (alas)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL
);

INSERT OR IGNORE INTO users (id, username, password) VALUES 
(1, 'Criciuma1', 'scrypt:32768:8:1$Av2eL7POeM8pIjem$10f0849f66f978e9b6a740eb4f8190e76b01ee286de26d54e1a12f0b17cd046998b989782f903c03db1d4602c899758c13e4c1234264a0fdca4c4f889ad88977'),
(2, 'Criciuma2', 'scrypt:32768:8:1$8T7tT04Dnwk8IWvK$f87a5358a7775d528b332049c484ef52b03126bf696efceb864f6f126b83a96df02e3499211d4610713c6bdb82cb525d4952e3f68c7084db31860964e4076a9c'),
(3, 'Criciuma3', 'scrypt:32768:8:1$sgpjqh5btXTxh1kv$607fd4904209e39a530fd15d0279c9c5ee60e60d193d7478870f768f2cbd89f32cd9046d3dafa8d70ca82dd6cb4fee74d6353a4bba431de3626e9b2559fcaf88'),
(4, 'Icara', 'scrypt:32768:8:1$RDiEo0O2r0R9SPh7$90f0a2d9be031a70d95903b7773b2bc78cca59821ef42345787b6d13571bd20d77de22325ab37da8887be697539f4ee22e02919ba6265d2da3c7ea2706866abb'),
(5, 'Ararangua', 'scrypt:32768:8:1$tBlo6LHwDF2QIiCP$a93ba9f3c8f87617cc0a8ffbdf2b9001cb581098198740cbb07de1265f3621405aa2738816492fd7d012f73ca102cde21ab17b9997612bc6302eeb83839e554f');

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

-- Tabela para templates corrigida
CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ala_id INTEGER NOT NULL, -- Coluna necessária para o filtro do Python
    tipo_template INTEGER NOT NULL, -- 1: Sacramental, 2: Batismo/Testemunhos
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
    encerramento TEXT NOT NULL,
    FOREIGN KEY (ala_id) REFERENCES users(id)
);

INSERT OR IGNORE INTO templates (ala_id, tipo_template, nome, boas_vindas, desobrigacoes, apoios, confirmacoes_batismo, apoio_membro_novo, bencao_crianca, sacramento, mensagens, live, encerramento) 
VALUES
(
    0,
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
    0,
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