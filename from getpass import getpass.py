from getpass import getpass
from app import app, db, User

def main():
    """Função principal para criar um usuário administrador."""
    with app.app_context():
        print("--- Criar Usuário Administrador ---")
        
        # Garante que as tabelas existam
        db.create_all()

        # Verifica se já existem usuários
        if User.query.count() > 0:
            print("Já existem usuários no banco de dados.")
            overwrite = input("Deseja criar um novo mesmo assim? (s/n): ").lower()
            if overwrite != 's':
                print("Operação cancelada.")
                return

        username = input("Digite o nome de usuário do administrador: ")
        if not username:
            print("Nome de usuário não pode ser vazio.")
            return

        if User.query.filter_by(username=username).first():
            print(f"Erro: O usuário '{username}' já existe.")
            return

        password = getpass("Digite a senha: ")
        password_confirm = getpass("Confirme a senha: ")

        if not password or password != password_confirm:
            print("As senhas não coincidem ou estão vazias.")
            return

        admin_user = User(username=username)
        admin_user.set_password(password)
        db.session.add(admin_user)
        db.session.commit()
        
        print(f"Usuário administrador '{username}' criado com sucesso!")

if __name__ == '__main__':
    main()