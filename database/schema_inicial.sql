PRAGMA foreign_keys = OFF;
BEGIN TRANSACTION;

-- Tabela de usuários (alas)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username varchar NOT NULL,
    password varchar NOT NULL
);

INSERT OR IGNORE INTO users (id, username, password) VALUES 
(1, 'Criciuma_1', 'scrypt:32768:8:1$zx2BC50zAAp0yYHb$2b13f9bdd7bcaf99f076d961108cba509161a23f952588cb151bb9ac34e1c7450342824af8442b0987b9ac415ef2ce2423264ff49f2c269e6115827ef53c96a6'),
(2, 'Criciuma_2', 'scrypt:32768:8:1$PR9qBBAPKbrQrGJl$f63f9be2ae16260686925e73300462b6636859f92175096b5f027e9a1932b5f2c2c42b3732b06109d9571d5a7cea5433f6dd9e74f40f9670a3403186d6cd8c15'),
(3, 'Criciuma_3', 'scrypt:32768:8:1$1zhuO5nXbJPSUUx3$f783607d3c51a513a9e29a3ed3b7705290cd8e3e8acd3ee409794509db272ea461503786b725cf17586e89e632f83754119cf0c7157bd0fdab3671f61667a0c7'),
(4, 'Içara', 'scrypt:32768:8:1$nrFQEYeq3Q44cS6s$5c789a66d2c281c33cf08f6a3745a4f7f6881beb8e6a6c2b588052709812af0aa4a7c348cf9dce2e27ea3853e832ba38a7f339e962e0832208c501e1f6ab914b'),
(5, 'Ararangua','scrypt:32768:8:1$WfEHhMNDm0xTWhaB$6b81e6efda0478fd40e20a92a25f16da3abe152a192f631a6250d1e04c63868de144b8534f61a128fcd1cfb682bc0c5a2b89f19931d191bb626a93a7ee00a607');

/* Criciuma_1 - Criciuma1.33@2033
Criciuma_2 - Criciuma2.88@2088
Criciuma_3 - Criciuma3.66@2066
Içara - Içara4.99@2099
Ararangua - Ararangua5.10@2010 */

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
    discursante_1 TEXT,
    discursante_2 TEXT,
    outros TEXT,
    tema_1 TEXT,
    tema_2 TEXT,
    tema_ultimo TEXT,
    obs_1 TEXT,
    obs_2 TEXT,
    obs_ultimo TEXT,
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

ALTER TABLE unidades ADD COLUMN recepcionista TEXT;
ALTER TABLE unidades ADD COLUMN pianista TEXT;
ALTER TABLE unidades ADD COLUMN regente_musica TEXT;