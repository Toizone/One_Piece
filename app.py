from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import jwt  # Para gerar o token de login
import datetime
import hashlib

app = Flask(__name__)
CORS(app)

# ==============================================
# 🔗 BANCO DE DADOS — Usamos SQLite (simples e gratuito)
# ==============================================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///piratas.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'chave_secreta_do_jogo_123'  # Mude isso depois!

db = SQLAlchemy(app)

# ==============================================
# 👤 TABELA DE USUÁRIOS
# ==============================================
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome_usuario = db.Column(db.String(50), unique=True, nullable=False)
    senha_hash = db.Column(db.String(255), nullable=False)
    moedas = db.Column(db.Integer, default=500)
    gemas = db.Column(db.Integer, default=10)
    
    # Ligação com os personagens do jogador
    personagens = db.relationship('PersonagemJogador', backref='usuario', lazy=True)

# ==============================================
# 🃏 TABELA DE PERSONAGENS DO JOGADOR
# ==============================================
class PersonagemJogador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False)
    
    # Dados do personagem
    personagem_id = db.Column(db.Integer, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    vidaMaxima = db.Column(db.Integer, nullable=False)
    ataque = db.Column(db.Integer, nullable=False)
    nivel = db.Column(db.Integer, default=1)
    imagem = db.Column(db.String(50))

# ==============================================
# 🔐 FUNÇÕES DE SEGURANÇA
# ==============================================
def gerar_token(usuario_id):
    payload = {
        'id': usuario_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7)  # Válido 7 dias
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

def verificar_token(token):
    try:
        dados = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return dados['id']
    except:
        return None

# ==============================================
# 📋 API — ROTAS PÚBLICAS
# ==============================================

# Cadastro
@app.route('/api/cadastro', methods=['POST'])
def cadastro():
    dados = request.json
    usuario_existe = Usuario.query.filter_by(nome_usuario=dados['usuario']).first()
    
    if usuario_existe:
        return jsonify({"status": "erro", "mensagem": "Usuário já existe"}), 400
    
    # Criptografa a senha
    senha_hash = hashlib.sha256(dados['senha'].encode()).hexdigest()
    
    novo_usuario = Usuario(
        nome_usuario=dados['usuario'],
        senha_hash=senha_hash
    )
    
    db.session.add(novo_usuario)
    db.session.commit()
    
    # Dá os 5 personagens iniciais para o jogador novo
    personagens_iniciais = [
        {"id": 1, "nome": "Monkey D. Luffy", "vida": 120, "ataque": 25, "img": "luffy"},
        {"id": 2, "nome": "Roronoa Zoro", "vida": 110, "ataque": 30, "img": "zoro"},
        {"id": 3, "nome": "Nami", "vida": 90, "ataque": 20, "img": "nami"},
        {"id": 4, "nome": "Sanji", "vida": 100, "ataque": 28, "img": "sanji"},
        {"id": 5, "nome": "Tony Tony Chopper", "vida": 130, "ataque": 15, "img": "chopper"}
    ]
    
    for p in personagens_iniciais:
        novo_pers = PersonagemJogador(
            usuario_id=novo_usuario.id,
            personagem_id=p["id"],
            nome=p["nome"],
            vidaMaxima=p["vida"],
            ataque=p["ataque"],
            imagem=p["img"]
        )
        db.session.add(novo_pers)
    
    db.session.commit()
    
    token = gerar_token(novo_usuario.id)
    return jsonify({
        "status": "sucesso",
        "mensagem": "Conta criada!",
        "token": token,
        "usuario": novo_usuario.nome_usuario
    })

# Login
@app.route('/api/login', methods=['POST'])
def login():
    dados = request.json
    usuario = Usuario.query.filter_by(nome_usuario=dados['usuario']).first()
    
    if not usuario:
        return jsonify({"status": "erro", "mensagem": "Usuário não encontrado"}), 404
    
    senha_hash = hashlib.sha256(dados['senha'].encode()).hexdigest()
    if usuario.senha_hash != senha_hash:
        return jsonify({"status": "erro", "mensagem": "Senha incorreta"}), 401
    
    token = gerar_token(usuario.id)
    return jsonify({
        "status": "sucesso",
        "mensagem": "Bem-vindo!",
        "token": token,
        "usuario": usuario.nome_usuario,
        "moedas": usuario.moedas,
        "gemas": usuario.gemas
    })

# ==============================================
# 🔒 ROTAS PROTEGIDAS (precisa de token)
# ==============================================

@app.route('/api/meus-personagens', methods=['GET'])
def meus_personagens():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({"status": "erro", "mensagem": "Sem token"}), 401
    
    usuario_id = verificar_token(token.replace("Bearer ", ""))
    if not usuario_id:
        return jsonify({"status": "erro", "mensagem": "Token inválido"}), 401
    
    usuario = Usuario.query.get(usuario_id)
    if not usuario:
        return jsonify({"status": "erro", "mensagem": "Usuário não existe"}), 404
    
    lista = []
    for p in usuario.personagens:
        lista.append({
            "id": p.personagem_id,
            "nome": p.nome,
            "vidaMaxima": p.vidaMaxima,
            "ataque": p.ataque,
            "nivel": p.nivel,
            "imagem": p.imagem
        })
    
    return jsonify({
        "status": "sucesso",
        "usuario": usuario.nome_usuario,
        "moedas": usuario.moedas,
        "gemas": usuario.gemas,
        "quantidade": len(lista),
        "personagens": lista
    })

# ==============================================
# INICIAR BANCO E SERVIDOR
# ==============================================
with app.app_context():
    db.create_all()  # Cria o banco de dados automaticamente

if __name__ == '__main__':
    print("🏴‍☠️ Servidor One Piece iniciado!")
    app.run(debug=True)