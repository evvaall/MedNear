from flask import Flask, render_template, redirect, request, flash, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager,login_user, login_required, logout_user, current_user
import calendar
from flask_migrate import Migrate
from datetime import datetime, date
from base_dados.db import base
from models import Farmacia, Medicamento, Historia, Vendas
from sqlalchemy import func
from relatorios import GerarRelatorios

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///mednear.db"
app.config["SECRET_KEY"] = "805080"
app.config["LOGIN_VIEW"] = "login"
base.init_app(app)


migrate = Migrate(app, base)


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def login_2(user_id):
    restorno = base.session.get(Farmacia, int(user_id))
    return restorno

months = [
    "janeiro",
    "Fevereiro",
    "Março",
    "Abril",
    "Maio",
    "Junho",
    "Julho",
    "Agosto",
    "Setembro",
    "Outubro",
    "Novembro",
    "Dezembro"
]
now = datetime.now()
year = now.year
month = now.month
today = now.day
cal  = calendar.monthcalendar(year,  month)
month = months[month - 1]

def log(acao, tipo):
    his = Historia(
        data=datetime.now(),
        user_id=current_user.id,
        tipo=tipo,
        descricao=acao
    )
    base.session.add(his)
    base.session.commit()


@app.route("/hora", methods = ["GET", "POST"])
def hora():
    agora = datetime.now().strftime("%H:%M:%S")
    return {"hora":agora}


@app.route("/home", methods = ["GET", "POST"])
@login_required
def home():
    if request.method == "GET":
        historico = Historia.query.filter_by(user_id = current_user.id).all()
        med = Medicamento.query.filter_by(user_id = current_user.id).all()
        vlr_inventario = base.session.query(func.sum(Medicamento.quantidade).filter(Medicamento.user_id == current_user.id)).scalar() or 0 # type: ignore
        valor_em_stock = base.session.query(func.sum(Medicamento.preço * Medicamento.quantidade).filter(Medicamento.user_id == current_user.id)).scalar() or 0 #type: ignore
        return render_template(
            "base.html",
            historico = historico,
            lista_medicamentos = med,
            calendar = cal,
            month = month,
            year = year,
            today = today,
            vlr_inventario = vlr_inventario,
            valor_em_stock = valor_em_stock,
            user = current_user,
            )
    return render_template(
        "base.html",
        )
@app.route("/registrar", methods = ["GET", "POST"])
def registrar():
    if request.method == 'POST':
        nome = request.form.get('nome_farmacia')
        email = request.form.get('email')
        licenca = request.form.get('licenca')
        senha = request.form.get('password') or ""
        conf_senha = request.form.get('confirm_password')
        telefone = request.form.get("telefone")
        localizacao = request.form.get("localizacao")

        if senha != conf_senha:
            flash('As palavras-passe não coincidem!')
            return redirect(url_for('registrar'))
        
        senha_encriptada = generate_password_hash(senha)


        nova_farmacia = Farmacia(nome=nome, email=email, nif=licenca, senha=senha_encriptada, localizacao=localizacao, telefone=telefone)
        base.session.add(nova_farmacia)
        base.session.commit()
        farmacia = Farmacia.query.filter_by(email=email).first()
        login_user(farmacia)
        log(f'Farmácia {farmacia.nome} Criou uma conta', 'Conta criada') # pyright: ignore[reportOptionalMemberAccess]
        return redirect(url_for('home'))

    return render_template("registrar.html")
@app.route("/login", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        entr_email = request.form.get("email")
        entr_senha = request.form.get("password")
        senha = entr_senha if entr_senha else ""
        email = entr_email if entr_email else ""
        farmacia = Farmacia.query.filter_by(email=email).first()
        if farmacia and check_password_hash(farmacia.senha, senha): # type: ignore
            login_user(farmacia)
            log(f'Farmácia {farmacia.nome} Efetuou login', 'login')
            print("Login efetuado com sucesso!success")
            return redirect(url_for('home'))
        else:
            flash("Email ou senha incorretos.")
    return render_template(
            "login.html"
        )

@app.route('/logout')
@login_required
def logout():
    log(f"Farmácia {current_user.nome} fez logout", "Logout")
    logout_user()
    return redirect(url_for('login'))

@app.route("/stock", methods = ["GET", "POST", "DELETE"])
@login_required
def stock():
    if request.method == "POST":
        nome = request.form.get("Nome")
        categoria = request.form.get("Categoria")
        preco_float = request.form.get("Preço")
        qnt_int = request.form.get("Quantidade")
        validade = request.form.get("Validade")
        qnt = int(qnt_int) if qnt_int  else 0
        preco = float(preco_float) if preco_float else 0.0
        try:
            novo_midicamento = Medicamento(nome=nome, categoria=categoria, preço=preco, quantidade=qnt, validade=validade, user_id=current_user.id)
            base.session.add(novo_midicamento)
            base.session.commit()
            log(acao=f"Foi adicionado mais {qnt}unid. de {nome}", tipo="Entrada")
        except:
            pass
    if request.method == "DELETE":
        return {}
    med = Medicamento.query.filter_by(user_id = current_user.id).all()  
    return render_template(
        "stock.html", 
        lista_medicamentos = med,
        user = current_user
        )

@app.route("/estatisticas", methods = [ "GET", "POST"])
@login_required
def estatistics():
    if request.method == "POST":
        nome_medicamento = request.form.get("Nome")
        quantidade = int(request.form.get("Quantidade", 0))
        preco = float(request.form.get("Preço", 0))
        obs = request.form.get("Obs")
        medicamento = Medicamento.query.filter_by(
            nome=nome_medicamento, 
            user_id=current_user.id
        ).first_or_404()
        print(medicamento)
        if medicamento:
            if medicamento.quantidade >= quantidade:
                medicamento.quantidade -= quantidade
                registro_de_vendidos = Vendas(nome=nome_medicamento, quantidade=quantidade, user_id=current_user.id, data=date.today(), obs=obs, preço=preco)
                base.session.add(registro_de_vendidos)
                base.session.commit()
                log(f"foi Vendido {quantidade}unid. de {nome_medicamento}", "Venda")
    att = base.session.query(
        Medicamento.categoria, # type: ignore
        func.count(Medicamento.id).label('total_tipos'),
        func.sum(Medicamento.preço * Medicamento.quantidade).label('valor_total') # type: ignore
    ).group_by(Medicamento.categoria).filter(Medicamento.user_id == current_user.id).all() # type: ignore

    nome = {
        'nome':[],
        'valor':[]
    }
    for x in att:
        nome["nome"].append(x.categoria)
        nome["valor"].append(x.valor_total)

    produtos_em_stock = {
        "nome":[],
        "quantidade":[]
    }
    product = base.session.query(
        Medicamento.nome, # type: ignore
        func.sum(Medicamento.quantidade).label('quantidade') #type:ignore
    ).group_by(Medicamento.nome).filter(Medicamento.user_id == current_user.id).filter(Medicamento.quantidade < 11).all() #type:ignore
    for x in product:
        produtos_em_stock["nome"].append(x.nome)
        produtos_em_stock["quantidade"].append(x.quantidade)
        
    vlr_inventario = base.session.query(func.sum(Medicamento.quantidade).filter(Medicamento.user_id == current_user.id)).scalar() or 0 # type: ignore
    valor_em_stock = base.session.query(func.sum(Medicamento.preço * Medicamento.quantidade).filter(Medicamento.user_id == current_user.id)).scalar() or 0 #type: ignore
    return render_template(
        "estatistics.html",
        user = current_user,
        vlr_inventario = vlr_inventario,
        valor_em_stock = valor_em_stock,
        valor = nome["valor"],
        nome = nome["nome"],
        produto = produtos_em_stock["nome"],
        quantidade = produtos_em_stock["quantidade"]
    )


@app.route('/imprimir')
@login_required
def imprimir_relatorio():
    total_vendas = base.session.query(func.sum(Vendas.quantidade * Vendas.preço).filter(Vendas.user_id == current_user.id,)).filter(Vendas.user_id == current_user.id).scalar() or 0
    gerar_relatorio = GerarRelatorios(
        quantidade=Vendas.quantidade,
        nome=current_user.nome,
        medicamentos=Vendas.nome,
        valor=total_vendas,
        dia=date.today()
        )
    return redirect(
        url_for("home")
    )

"""@app.route("/estatistics", methods = ["POST"])
@login_required
def vender():


    return render_template(
        'estatistics.html',
        user = current_user
    )"""
if __name__ == "__main__":
    with app.app_context():
        base.create_all()
    app.run(debug=True)