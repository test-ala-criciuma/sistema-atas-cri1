from werkzeug.security import generate_password_hash

senha_simples = 'jorge1234'
hash_gerado = generate_password_hash(senha_simples) 
print(hash_gerado)