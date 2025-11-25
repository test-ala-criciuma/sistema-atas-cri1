-- Tabela de usuários (alas)
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL
);

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

-- Inserir usuários (alas)
INSERT OR IGNORE INTO users (id, username, password) VALUES 
(1, 'Criciuma1', 'cri1'),
(2, 'Criciuma2', 'cri2'),
(3, 'Criciuma3', 'cri3'),
(4, 'Ararangua', 'ara1'),
(5, 'Icara', 'ica1');

-- Criar índices para melhor performance
CREATE INDEX IF NOT EXISTS idx_atas_ala_id ON atas(ala_id);
CREATE INDEX IF NOT EXISTS idx_atas_data ON atas(data);
CREATE INDEX IF NOT EXISTS idx_atas_tipo ON atas(tipo);
CREATE INDEX IF NOT EXISTS idx_sacramental_ata_id ON sacramental(ata_id);
CREATE INDEX IF NOT EXISTS idx_batismo_ata_id ON batismo(ata_id);