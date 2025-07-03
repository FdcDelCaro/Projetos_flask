import os
import json
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# --- CONFIGURAÇÃO DA APLICAÇÃO ---
app = Flask(__name__)

# Chave secreta para segurança das sessões (flash messages, etc.)
# Em produção, use uma chave mais complexa e guarde-a de forma segura.
app.config['SECRET_KEY'] = 'sua-chave-secreta-muito-segura'

# Carrega as configurações do banco de dados do arquivo JSON
try:
    with open('config.json') as config_file:
        config = json.load(config_file)
except FileNotFoundError:
    raise RuntimeError("Arquivo de configuração 'config.json' não encontrado. Crie um a partir do exemplo.")

# Configuração do banco de dados MySQL
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{config['DB_USER']}:{config['DB_PASSWORD']}@{config['DB_HOST']}/{config['DB_NAME']}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Rota para a qual usuários não logados são redirecionados
login_manager.login_message = "Por favor, faça o login para acessar esta página."

# --- MODELOS DO BANCO DE DADOS ---

# Modelo para os usuários do sistema (quem pode fazer login)
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Modelo para os alunos
class Aluno(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    idade = db.Column(db.Integer, nullable=False)
    curso = db.Column(db.String(100), nullable=False)

# --- CONFIGURAÇÃO DO FLASK-LOGIN ---

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROTAS DA APLICAÇÃO ---

@app.route('/')
@login_required
def dashboard():
    """Página principal que lista todos os alunos."""
    alunos = Aluno.query.all()
    return render_template('dashboard.html', alunos=alunos)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Usuário ou senha inválidos.')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Faz o logout do usuário."""
    logout_user()
    return redirect(url_for('login'))

@app.route('/add_student', methods=['GET', 'POST'])
@login_required
def add_student():
    """Página para adicionar um novo aluno."""
    if request.method == 'POST':
        nome = request.form['nome']
        idade = request.form['idade']
        curso = request.form['curso']

        novo_aluno = Aluno(nome=nome, idade=idade, curso=curso)
        db.session.add(novo_aluno)
        db.session.commit()

        flash('Aluno adicionado com sucesso!')
        return redirect(url_for('dashboard'))

    return render_template('add_student.html')


if __name__ == '__main__':
    # Cria o banco de dados e as tabelas se não existirem
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)