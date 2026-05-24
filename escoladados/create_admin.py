# Este é um script de linha de comando para criar um usuário administrador inicial.
# Ele deve ser executado separadamente, no terminal: python create_admin.py

from getpass import getpass  # Importa getpass para ler a senha sem exibi-la no terminal.
from flask_app import app, db, User  # Importa a instância da app, o db e o modelo User do arquivo principal.

def main():
    """Função principal para criar um usuário administrador."""
    # O 'app_context' é necessário para que o script tenha acesso às configurações
    # da aplicação Flask, como a conexão com o banco de dados.
    with app.app_context():
        print("--- Criar Usuário Administrador ---")
        
        # Garante que a estrutura do banco de dados (tabelas) exista antes de tentar inserir dados.
        db.create_all()

        # Verifica se já existem usuários
        if User.query.count() > 0:
            print("Já existem usuários no banco de dados.")
            # Pergunta se o usuário deseja continuar mesmo assim.
            overwrite = input("Deseja criar um novo mesmo assim? (s/n): ").lower()
            if overwrite != 's':
                print("Operação cancelada.")
                return # Encerra a execução do script.

        # Solicita o nome de usuário.
        username = input("Digite o nome de usuário do administrador: ")
        if not username:
            print("Nome de usuário não pode ser vazio.")
            return

        # Verifica se o nome de usuário já está em uso.
        if User.query.filter_by(username=username).first():
            print(f"Erro: O usuário '{username}' já existe.")
            return

        # Solicita a senha duas vezes para confirmação.
        password = getpass("Digite a senha: ")
        password_confirm = getpass("Confirme a senha: ")

        # Valida se a senha não está vazia e se as duas digitações coincidem.
        if not password or password != password_confirm:
            print("As senhas não coincidem ou estão vazias.")
            return

        # Cria uma nova instância do usuário.
        admin_user = User(username=username)
        admin_user.set_password(password) # Usa o método do modelo para criptografar e definir a senha.
        db.session.add(admin_user) # Adiciona o novo usuário à sessão do banco de dados.
        db.session.commit() # Salva as mudanças no banco de dados.
        
        print(f"Usuário administrador '{username}' criado com sucesso!")

if __name__ == '__main__':
    main()