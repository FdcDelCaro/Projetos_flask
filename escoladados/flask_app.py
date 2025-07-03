# --- IMPORTAÇÕES DE BIBLIOTECAS ---
import os
import json
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy  # ORM para interagir com o banco de dados
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user # Gerenciamento de sessão de usuário
from werkzeug.security import generate_password_hash, check_password_hash # Funções para criptografar e verificar senhas

# --- CONFIGURAÇÃO DA APLICAÇÃO ---
app = Flask(__name__) # Cria a instância principal da aplicação Flask

# Chave secreta para segurança das sessões (flash messages, etc.)
# Em produção, use uma chave mais complexa e guarde-a de forma segura.
app.config['SECRET_KEY'] = 'sua-chave-secreta-muito-segura'

# Define o caminho absoluto para o diretório onde este script está localizado.
basedir = os.path.abspath(os.path.dirname(__file__))

# Carrega as configurações do banco de dados do arquivo JSON
try:
    # Boa prática: separar configurações sensíveis do código principal.
    # Usar o caminho absoluto garante que o arquivo seja encontrado, não importa de onde o script é executado.
    config_path = os.path.join(basedir, 'config.json')
    with open(config_path) as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    raise RuntimeError(f"Arquivo de configuração 'config.json' não encontrado. Verifique se ele existe em: {basedir}")

# Configuração do banco de dados MySQL usando os dados do config.json
# O formato da string é 'dialeto+driver://usuario:senha@host/banco_de_dados'
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{config['DB_USER']}:{config['DB_PASSWORD']}@{config['DB_HOST']}/{config['DB_NAME']}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Desativa um recurso do Flask-SQLAlchemy que não usaremos, para economizar recursos.

db = SQLAlchemy(app) # Inicializa a extensão SQLAlchemy, conectando-a com a nossa app Flask.
login_manager = LoginManager(app) # Inicializa o gerenciador de login.
login_manager.login_view = 'login' # Informa ao Flask-Login qual é a rota de login. Se um usuário tentar acessar uma página protegida sem estar logado, ele será redirecionado para cá.
login_manager.login_message = "Por favor, faça o login para acessar esta página." # Mensagem que será exibida ao usuário redirecionado.

# --- MODELOS DO BANCO DE DADOS ---
# Modelos são representações das tabelas do nosso banco de dados em formato de classes Python.

# Modelo para os usuários do sistema (quem pode fazer login)
class User(UserMixin, db.Model):
    # UserMixin é uma classe do Flask-Login que já implementa propriedades como is_authenticated, is_active, etc.
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False) # Armazena a senha criptografada, nunca a senha em texto puro.

    def set_password(self, password):
        """Cria um hash seguro da senha e o armazena."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Verifica se a senha fornecida corresponde ao hash armazenado."""
        return check_password_hash(self.password_hash, password)

# Modelo para os alunos
class Aluno(db.Model):
    # Esta classe irá gerar uma tabela chamada 'aluno' no banco de dados.
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    curso = db.Column(db.String(100), nullable=False)

# --- CONFIGURAÇÃO DO FLASK-LOGIN ---

@login_manager.user_loader
def load_user(user_id):
    """Esta função é usada pelo Flask-Login para recarregar o objeto do usuário a partir do ID do usuário armazenado na sessão."""
    return User.query.get(int(user_id))

# --- ROTAS DA APLICAÇÃO ---

@app.route('/')
@login_required
def dashboard():
    """Página principal (dashboard) que lista todos os alunos.
    O decorador @login_required garante que apenas usuários logados possam acessar esta rota.
    """
    alunos = Aluno.query.all() # Busca todos os registros da tabela Aluno.
    return render_template('dashboard.html', alunos=alunos) # Renderiza o template e passa a lista de alunos para ele.

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login."""
    # Se o usuário já estiver logado, redireciona para o dashboard.
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    # Se o método da requisição for POST, significa que o formulário de login foi enviado.
    if request.method == 'POST':
        # Pega os dados enviados no formulário.
        username = request.form['username']
        password = request.form['password']
        # Procura um usuário com o username fornecido.
        user = User.query.filter_by(username=username).first()

        # Verifica se o usuário existe e se a senha está correta.
        if user and user.check_password(password):
            login_user(user) # Registra o usuário como logado na sessão.
            return redirect(url_for('dashboard')) # Redireciona para o dashboard.
        else:
            # Se os dados estiverem errados, exibe uma mensagem de erro.
            flash('Usuário ou senha inválidos.') 

    # Se o método for GET (primeiro acesso à página), apenas mostra o template de login.
    return render_template('login.html') 

@app.route('/logout')
@login_required
def logout():
    """Faz o logout do usuário."""
    logout_user() # Função do Flask-Login que limpa a sessão do usuário.
    return redirect(url_for('login')) # Redireciona para a página de login.

@app.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    """Página para adicionar um novo aluno."""
    # Se o formulário de adicionar aluno foi enviado (método POST).
    if request.method == 'POST':
        # Pega os dados do formulário.
        nome = request.form['nome']
        idade = request.form['idade']
        curso = request.form['curso']

        # Cria uma nova instância do modelo Aluno com os dados recebidos.
        novo_aluno = Aluno(nome=nome, idade=idade, curso=curso)
        db.session.add(novo_aluno) # Adiciona o novo aluno à sessão do banco de dados.
        db.session.commit() # Confirma a transação, salvando o aluno no banco de dados.

        flash('Aluno adicionado com sucesso!') # Exibe uma mensagem de sucesso.
        return redirect(url_for('dashboard')) # Redireciona de volta para o dashboard.

    # Se o método for GET, apenas mostra a página com o formulário para adicionar aluno.
    return render_template('add_student.html')


# --- EXECUÇÃO DA APLICAÇÃO ---
if __name__ == '__main__':
    # Este bloco só é executado quando o script é rodado diretamente (python app.py)
    with app.app_context():
        # Garante que o banco de dados e as tabelas sejam criados antes de a aplicação rodar pela primeira vez.
        db.create_all() 
    
    # Inicia o servidor de desenvolvimento do Flask.
    # debug=True ativa o modo de depuração, que reinicia o servidor a cada mudança e mostra erros detalhados.
    app.run(debug=True) 