-- Tabela de usuários
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL
);

INSERT OR IGNORE INTO users (id,username, password) VALUES 
(1, 'Criciuma1', 'cri1'),
(2, 'Criciuma2', 'cri2'),
(3, 'Criciuma3', 'cri3'),
(4, 'Ararangua', 'ara1'),
(5, 'Icara', 'ica1');

-- Tabela principal de atas
CREATE TABLE IF NOT EXISTS atas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo TEXT NOT NULL,
    data TEXT NOT NULL,
    status TEXT DEFAULT 'pendente',
    ala_id INTEGER NOT NULL,
    FOREIGN KEY(ala_id) REFERENCES users(id)
);

-- Tabela para atas de reuniões sacramentais
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

-- Tabela para unidades
CREATE TABLE IF NOT EXISTS unidades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ala_id INTEGER NOT NULL,
    nome TEXT ,
    bispo TEXT ,
    conselheiros TEXT,
    estaca TEXT DEFAULT "Criciúma",
    horario TEXT ,
    FOREIGN KEY(ala_id) REFERENCES users(id)
);

INSERT OR IGNORE INTO unidades (id,ala_id, nome, bispo, conselheiros, horario) VALUES
(1,1,'Ala Criciúma 1', 'Julio Davila', 'Antonio Carlos de Souza, Ari Cesar Albeche Lopes', '09:30 - 10:30'),
(2,2,'Ala Criciúma 2', 'alterar', 'alterar','alterar'),
(3,3,'Ala Criciúma 3', 'alterar', 'alterar', 'alterar'),
(4,4,'Ala Içara', 'alterar', 'alterar', 'alterar'),
(5,5,'Ala Araranguá', 'alterar', 'alterar', 'alterar');

-- Tabela para padrôes escritos nas atas
CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_template TEXT NOT NULL,
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

INSERT OR IGNORE INTO templates (
    tipo_template,nome,boas_vindas,desobrigacoes,apoios,confirmacoes_batismo,apoio_membro_novo,bencao_crianca,sacramento,mensagens,live,encerramento) 
VALUES
(
    1,
    "Sacramental Padrão",
    "Bom dia irmãos e irmãs! Gostariamos de fazer todos muito bem vindos a mais uma Reunião Sacramental da ALA [NOME], Estaca Criciúma, neste dia [DATA]. Desejamos que todos se sintam bem entre nós, especialmente aqueles que nos visitam.",
    "É proposto dar um voto de agradecimento aos serviços prestados pelo(a) irmã(o) [NOME] que serviu como [CHAMADO]. Todos os que desejam se manifestar, levantem a mão",
    "O(a) irmã(o) [NOME] está sendo chamado(a) como [CHAMADO]. Todos que forem a favor manifestem-se. Os que forem contrários, manifestem-se",
    "O(a) irmã(o) [NOME] foram batizados, gostaríamos de convida-los(a) para virem até o púlpito para que possamos fazer sua confirmação como Membro de A Igreja de Jesus Cristo dos Santos dos Ultimos Dias.",
    "O(a) irmã(o) [NOME] foi batizado e confirmado membro da igreja, e gostariámos do apoio de todos os irmãos de plena aceitação como mais novo membro da ala. Todos a favor, manifestem-se",
    "Gostaríamos de chamar ao púlpito o irmão [NOME] que irá dar a benção de apresentação da(o) [NOME DA CRIANÇA], filho(a) de [NOME DOS PAIS].",
    "Passaremos ao Sacramento, que é a parte mais importante de nossa reunião. Cantaremos como Hino Sacramental [NOME] , o Sacramento será abençoado e distribuido a todos",
    "Agradecemos a todos pela reverência durante o Sacramento. Passaremos agora a parte dos discursantes. Ouviremos primeiro o(a) irmã(o) [NOME]. Depois, ouviremos o(a) irmã(o) [NOME]. Em seguida cantaremos o hino [NOME], em pé, ao sinal do(a) regente.",
    "Gostaria de lembrar todos que estejam assitindo a trasmissão da reunião, que se identifiquem para que possamos contá-los também",
    "Agradecemos a presença e participação de todos, especialmente aqueles que contribuiram de alguma forma para que essa reunião acontecesse. E convidamos todos para que estejam aqui no próximo domingo. Ouviremos como último orador o(a) irmã(o) [NOME]. Logo após, cantaremos teremos o hino [NOME], e o (a) irmã (o) [NOME] oferecerá a última oração. Desejamos a todos uma ótima semana e que o Espírito do Senhor os acompanhe."
    ),
(
    2,
    "Testemunhos",
    "Bom dia irmãos e irmãs! Gostariamos de fazer todos muito bem vindos a mais uma Reunião Sacramental da ALA [NOME], Estaca Criciúma, neste dia [DATA]. Desejamos que todos se sintam bem entre nós, especialmente aqueles que nos visitam.",
    "É proposto dar um voto de agradecimento aos serviços prestados pelo(a) irmã(o) [NOME] que serviu como [CHAMADO]. Todos os que desejam se manifestar, levantem a mão",
    "O(a) irmã(o) [NOME] está sendo chamado(a) como [CHAMADO]. Todos que forem a favor manifestem-se. Os que forem contrários, manifestem-se",
    "O(a) irmã(o) [NOME] foram batizados, gostaríamos de convida-los(a) para virem até o púlpito para que possamos fazer sua confirmação como Membro de A Igreja de Jesus Cristo dos Santos dos Ultimos Dias.",
    "O(a) irmã(o) [NOME] foi batizado e confirmado membro da igreja, e gostariámos do apoio de todos os irmãos de plena aceitação como mais novo membro da ala. Todos a favor, manifestem-se",
    "Gostaríamos de chamar ao púlpito o irmão [NOME] que irá dar a benção de apresentação da(o) [NOME DA CRIANÇA], filho(a) de [NOME DOS PAIS].",
    "Passaremos ao Sacramento, que é a parte mais importante de nossa reunião. Cantaremos como Hino Sacramental [NOME] , o Sacramento será abençoado e distribuido a todos",
    "Agradecemos a todos pela reverência durante o Sacramento. Hoje é nossa reunião de Jejum e Testemunhos. Gostaríamos de convidar todos a prestar seus testemunhos de forma breve e direta, dando assim tempo para que o máximo de irmãos tenham este privilégio.",
    "Gostaria de lembrar todos que estejam assitindo a trasmissão da reunião, que se identifiquem para que possamos contá-los também",
    "Agradecemos a presença e participação de todos, especialmente aqueles que contribuiram de alguma forma para que essa reunião acontecesse. E convidamos todos para que estejam aqui no próximo domingo. Cantaremos o último hino [NOME] e o(a) irmã(o) [NOME] oferecerá a última oração."
);

-- Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_atas_ala_id ON atas(ala_id);
CREATE INDEX IF NOT EXISTS idx_atas_data ON atas(data);
CREATE INDEX IF NOT EXISTS idx_atas_tipo ON atas(tipo);
CREATE INDEX IF NOT EXISTS idx_sacramental_ata_id ON sacramental(ata_id);
CREATE INDEX IF NOT EXISTS idx_batismo_ata_id ON batismo(ata_id);

ALTER TABLE sacramental ADD COLUMN recepcionistas TEXT;
ALTER TABLE sacramental ADD COLUMN reconhecemos_presenca TEXT;
ALTER TABLE sacramental ADD COLUMN desobrigacoes TEXT;
ALTER TABLE sacramental ADD COLUMN apoios TEXT;
ALTER TABLE sacramental ADD COLUMN confirmacoes_batismo TEXT;
ALTER TABLE sacramental ADD COLUMN apoio_membros TEXT;
ALTER TABLE sacramental ADD COLUMN bencao_criancas TEXT;
ALTER TABLE sacramental ADD COLUMN ultimo_discursante TEXT;