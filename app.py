from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
from functools import wraps
from datetime import date, datetime

# -------------------- CONFIG --------------------
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback123")

# Banco no Render
app.config['SQLALCHEMY_DATABASE_URI'] = "postgresql+psycopg2://site_cadastro_db_user:OwOjfgF4i7cFdmAgXaN7bdSg2ebylq2z@dpg-d3a9vp24d50c73d3qtpg-a.oregon-postgres.render.com:5432/site_cadastro_db_bc15"
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

class Presenca(db.Model):
    __tablename__ = "presencas"
    id = db.Column(db.Integer, primary_key=True)
    jovem_id = db.Column(db.Integer, db.ForeignKey("jovens.id"), nullable=False)
    data_culto = db.Column(db.Date, nullable=False, default=date.today)
    presente = db.Column(db.Boolean, nullable=False)

    jovem = db.relationship("Jovem", backref=db.backref("presencas", lazy=True))

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

# -------------------- REGISTRAR PRESENÇA --------------------
@app.route("/registrar_presenca", methods=["GET", "POST"])
@login_required
def registrar_presenca():
    jovens = Jovem.query.all()

    if request.method == "POST":
        data_culto = datetime.strptime(request.form["data_culto"], "%Y-%m-%d").date()
        presencas_ids = request.form.getlist("presente")

        # Apaga registros do dia para evitar duplicatas
        Presenca.query.filter_by(data_culto=data_culto).delete()

        # Adiciona presenças de todos os jovens
        for jovem in jovens:
            presente = str(jovem.id) in presencas_ids
            nova_presenca = Presenca(
                jovem_id=jovem.id,
                data_culto=data_culto,
                presente=presente
            )
            db.session.add(nova_presenca)

        db.session.commit()
        flash("Presenças registradas com sucesso!")
        return redirect(url_for("dashboard"))

    return render_template("registrar_presenca.html", jovens=jovens)

# -------------------- CONSULTAR PRESENÇAS --------------------
@app.route("/consultar_presencas")
@login_required
def consultar_presencas():
    # Pega apenas presenças marcadas como presente=True
    presencas = (
        db.session.query(Presenca, Jovem)
        .join(Jovem, Presenca.jovem_id == Jovem.id)
        .filter(Presenca.presente == True)
        .order_by(Presenca.data_culto.desc(), Jovem.nome)
        .all()
    )

    presencas_grouped = {}
    for presenca, jovem in presencas:
        data_formatada = presenca.data_culto.strftime("%d/%m/%Y")
        if data_formatada not in presencas_grouped:
            presencas_grouped[data_formatada] = []
        presencas_grouped[data_formatada].append({
            "id": presenca.id,
            "nome": jovem.nome,
            "presente": presenca.presente
        })

    return render_template("consultar_presencas.html", presencas_grouped=presencas_grouped)

# -------------------- EDITAR PRESENÇAS POR DIA --------------------
@app.route("/editar_presenca/<data_culto>", methods=["GET", "POST"])
@login_required
def editar_presenca(data_culto):
    data_culto = data_culto.replace("-", "/")
    data_obj = datetime.strptime(data_culto, "%d/%m/%Y").date()
    presencas = Presenca.query.filter_by(data_culto=data_obj).all()
    jovens = Jovem.query.all()

    if request.method == "POST":
        presencas_ids = request.form.getlist("presente")

        # Atualiza presenças existentes ou cria novas se não houver
        for jovem in jovens:
            presenca = next((p for p in presencas if p.jovem_id == jovem.id), None)
            presente = str(jovem.id) in presencas_ids
            if presenca:
                presenca.presente = presente
            else:
                nova_presenca = Presenca(
                    jovem_id=jovem.id,
                    data_culto=data_obj,
                    presente=presente
                )
                db.session.add(nova_presenca)

        db.session.commit()
        flash("Presenças atualizadas com sucesso!")
        return redirect(url_for("consultar_presencas"))

    jovens_status = []
    for jovem in jovens:
        presenca = next((p for p in presencas if p.jovem_id == jovem.id), None)
        jovens_status.append({
            "id": jovem.id,
            "nome": jovem.nome,
            "presente": presenca.presente if presenca else False
        })

    return render_template("editar_presenca.html", jovens_status=jovens_status, data_culto=data_culto)

# -------------------- EXCLUIR TODAS AS PRESENÇAS DE UM DIA --------------------
@app.route("/excluir_dia/<data>", methods=["POST"])
@login_required
def excluir_dia(data):
    data = data.replace("-", "/")
    try:
        data_formatada = datetime.strptime(data, "%d/%m/%Y").date()
    except ValueError:
        flash("Data inválida!")
        return redirect(url_for("consultar_presencas"))

    presencas = Presenca.query.filter_by(data_culto=data_formatada).all()
    if presencas:
        for p in presencas:
            db.session.delete(p)
        db.session.commit()
        flash(f"Todas as presenças do dia {data_formatada.strftime('%d/%m/%Y')} foram excluídas.")
    else:
        flash("Nenhuma presença encontrada para essa data.")

    return redirect(url_for("consultar_presencas"))

# -------------------- CRIAR TABELAS --------------------
with app.app_context():
    db.create_all()

# -------------------- RODAR APP --------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
