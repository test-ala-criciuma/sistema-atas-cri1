from werkzeug.security import generate_password_hash

senha_simples = 'Obra1.33@2026'
hash_gerado = generate_password_hash(senha_simples) 
print(hash_gerado)