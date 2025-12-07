from werkzeug.security import generate_password_hash

# Você fornece a senha simples:
senha_simples = 'jorge1234'

# O sistema faz todo o trabalho:
hash_gerado = generate_password_hash(senha_simples) 
print(hash_gerado)

# hash_gerado será algo como 'pbkdf2:sha256:600000$g40u5j9r$907409f583...'