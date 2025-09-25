from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from functools import wraps

# -------------------- CONFIG --------------------
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback123")

# Pega URL do banco do Render (já configurada no Environment Variables)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL").replace("postgres://", "postgresql://")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# -------------------- MODELS --------------------
class Usuario(db.Model):
    __tablename__ = "usuarios"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)
    data_criacao = db.Column(db.DateTime, server_default=db.func.now())

class Jovem(db.Model):
    __tablename__ = "jovens"
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(150), nullable=False)
    telefone = db.Column(db.String(50))
    email = db.Column(db.String(150))
    endereco = db.Column(db.String(200))
    data_nascimento = db.Column(db.String(50))

# -------------------- LOGIN REQUIRED --------------------
def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if "usuario" not in session:
            flash("Você precisa estar logado!")
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrap

# -------------------- LOGIN --------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        usuario = Usuario.query.filter_by(email=email).first()

        if usuario and check_password_hash(usuario.senha, senha):
            session["usuario"] = usuario.email
            session["nome"] = usuario.nome
            return redirect(url_for("dashboard"))
        else:
            flash("E-mail ou senha incorretos!")
    return render_template("login.html")

# -------------------- REGISTER --------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = generate_password_hash(request.form["senha"])

        try:
            novo_usuario = Usuario(nome=nome, email=email, senha=senha)
            db.session.add(novo_usuario)
            db.session.commit()
            flash("Cadastro realizado com sucesso!")
            return redirect(url_for("login"))
        except:
            db.session.rollback()
            flash("E-mail já cadastrado!")
    return render_template("register.html")

# -------------------- DASHBOARD --------------------
@app.route("/dashboard")
@login_required
def dashboard():
    jovens = Jovem.query.all()
    return render_template("dashboard.html", nome=session["nome"], jovens=jovens)

# -------------------- LOGOUT --------------------
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# -------------------- CADASTRAR JOVEM --------------------
@app.route("/cadastrar_jovem", methods=["GET", "POST"])
@login_required
def cadastrar_jovem():
    if request.method == "POST":
        jovem = Jovem(
            nome=request.form["nome"],
            telefone=request.form["telefone"],
            email=request.form["email"],
            endereco=request.form["endereco"],
            data_nascimento=request.form["data_nascimento"]
        )
        db.session.add(jovem)
        db.session.commit()
        flash("Jovem cadastrado com sucesso!")
        return redirect(url_for("dashboard"))
    return render_template("cadastrar_jovem.html")

# -------------------- LISTAR JOVENS --------------------
@app.route("/listar_jovens")
@login_required
def listar_jovens():
    jovens = Jovem.query.all()
    return render_template("listar_jovens.html", jovens=jovens)

# -------------------- EDITAR JOVEM --------------------
@app.route("/editar_jovem/<int:id>", methods=["GET", "POST"])
@login_required
def editar_jovem(id):
    jovem = Jovem.query.get(id)
    if not jovem:
        flash("Jovem não encontrado!")
        return redirect(url_for("listar_jovens"))

    if request.method == "POST":
        jovem.nome = request.form["nome"]
        jovem.telefone = request.form["telefone"]
        jovem.email = request.form["email"]
        jovem.endereco = request.form["endereco"]
        jovem.data_nascimento = request.form["data_nascimento"]
        db.session.commit()
        flash("Jovem atualizado com sucesso!")
        return redirect(url_for("listar_jovens"))

    return render_template("editar_jovem.html", jovem=jovem)

# -------------------- EXCLUIR JOVEM --------------------
@app.route("/excluir_jovem/<int:id>")
@login_required
def excluir_jovem(id):
    jovem = Jovem.query.get(id)
    if jovem:
        db.session.delete(jovem)
        db.session.commit()
        flash("Jovem excluído com sucesso!")
    return redirect(url_for("listar_jovens"))

# -------------------- CRIAR TABELAS --------------------
with app.app_context():
    db.create_all()

# -------------------- RODAR APP --------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
