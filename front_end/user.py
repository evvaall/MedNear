from flask import Flask, render_template, redirect, request, flash, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager,login_user, login_required, logout_user, current_user
import calendar
from flask_migrate import Migrate
from datetime import datetime, date
from base_dados.db import base
from models import Farmacia, Medicamento, Historia, Vendas, Funcionario
from sqlalchemy import func
from relatorios import GerarRelatorios
import os 
from dotenv import load_dotenv


load_dotenv()


app = Flask(__name__)
uri = os.getenv("DATABASE_URL", "sqlite:///mednear.db")
uri = uri.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = uri
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["LOGIN_VIEW"] = "login"
base.init_app(app)
migrate = Migrate(app, base)
login_manager = LoginManager()
login_manager.init_app(app)

print(uri)
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
        data=str(date.today()),
        user_id=current_user.id,
        tipo=tipo,
        descricao=acao,
        hora=str(datetime.now().strftime("%H:%M:%S"))
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
        funcionario = base.session.query(Funcionario).filter_by(nome=session.get("funcionario_nome"), user_id=current_user.id).scalar()
        historico = base.session.query(Historia).filter(Historia.user_id == current_user.id, Historia.data == str(date.today())).all()
        med = Medicamento.query.filter_by(user_id = current_user.id).all()
        vlr_inventario = base.session.query(func.sum(Medicamento.quantidade).filter(Medicamento.user_id == current_user.id)).scalar() or 0
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
            funcionario = funcionario
            )
    return render_template(
        "base.html",
        )

@app.route("/sign-in", methods = ["GET", "POST"])
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
        log(f'Farmácia {farmacia.nome} Criou uma conta', 'Conta criada')
        return redirect(url_for('gerente_funcionarios'))

    return render_template("registrar.html")
@app.route("/", methods = ["GET", "POST"])
def login():
    if request.method == "POST":
        entr_email = request.form.get("email")
        entr_senha = request.form.get("password")
        senha = entr_senha if entr_senha else ""
        email = entr_email if entr_email else ""
        farmacia = Farmacia.query.filter_by(email=email).first()
        if farmacia and check_password_hash(farmacia.senha, senha): 
            login_user(farmacia)
            log(f'Farmácia {farmacia.nome} Efetuou login', 'login')
            return redirect(url_for('gerente_funcionarios'))
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
            log(acao=f"{session.get('funcionario_nome')} adicionou {qnt}unid. de {nome}", tipo="Entrada")
        except:
            pass
    if request.method == "DELETE":
        return {}
    med = Medicamento.query.filter_by(user_id = current_user.id).all()  
    return render_template(
        "stock.html", 
        lista_medicamentos = med,
        user = current_user,
        funcionario = session.get('funcionario_nome')
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
        funionario = base.session.query(Funcionario).filter_by(nome=session.get("funcionario_nome"), user_id=current_user.id).scalar()
        if medicamento:
            if medicamento.quantidade >= quantidade:
                medicamento.quantidade -= quantidade
                registro_de_vendidos = Vendas(nome=nome_medicamento, hora=str(datetime.now().strftime("%H:%M:%S")), quantidade=quantidade, user_id=current_user.id, data=str(date.today()), obs=obs, preço=preco, categoria=medicamento.categoria, adicionado_por_id=session.get("funcionario_id"), funcionario=funionario)
                base.session.add(registro_de_vendidos)
                base.session.commit()
                log(f"{session.get('funcionario_nome')} vendeu {quantidade}unid. de {nome_medicamento}", "Venda")
    att = base.session.query(
        Medicamento.categoria,
        func.count(Medicamento.id).label('total_tipos'),
        func.sum(Medicamento.preço * Medicamento.quantidade).label('valor_total') 
    ).group_by(Medicamento.categoria).filter(Medicamento.user_id == current_user.id).all()
    product = base.session.query(
        Medicamento.nome, 
        func.sum(Medicamento.quantidade).label('quantidade') 
    ).group_by(Medicamento.nome).filter(Medicamento.user_id == current_user.id).filter(Medicamento.quantidade < 11).all() 
    vlr_inventario = base.session.query(func.sum(Medicamento.quantidade).filter(Medicamento.user_id == current_user.id)).scalar() or 0
    valor_em_stock = base.session.query(func.sum(Medicamento.preço * Medicamento.quantidade).filter(Medicamento.user_id == current_user.id)).scalar() or 0
    vendidos_dia = base.session.query(
        Vendas.categoria,
        func.count(Vendas.id).label("total"),
        func.sum(Vendas.preço * Vendas.quantidade).label("valor_total")
    ).group_by(Vendas.categoria).filter(Vendas.user_id == current_user.id, Vendas.data == str(date.today())).all()
    
    category = {
        'nome':[x.categoria for x in att],
        'valor_total':[x.valor_total for x in att],
    }
    produtos = {
        'nome':[x.nome for x in product],
        'quantidade':[x.quantidade for x in product],
    }
    vendas_dia = {
        'categoria':[x.categoria for x in vendidos_dia],
        'total':[x.total for x in vendidos_dia],
        'valor_total':[x.valor_total for x in vendidos_dia],
    }
    
    funcionario = base.session.query(Funcionario).filter_by(nome=session.get("funcionario_nome"), user_id=current_user.id).scalar()
    return render_template(
        "estatistics.html",
        user = current_user,
        vlr_inventario = vlr_inventario,
        valor_em_stock = valor_em_stock,
        categoria = category,
        produtos = produtos,
        vendas_dia = vendas_dia,
        funcionario = funcionario
    )

@app.route('/imprimir')
@login_required
def imprimir_relatorio():
    valor_vendas = base.session.query(func.sum(Vendas.quantidade * Vendas.preço).filter(Vendas.user_id == current_user.id, Vendas.data == date.today())).scalar()
    vendas_dia = base.session.query(func.count(Vendas.id).filter(Vendas.user_id == current_user.id, Vendas.data == str(date.today()))).scalar()
    nomes = base.session.query(
        Vendas.nome,
        Vendas.categoria,
        func.count(Vendas.id).label('total'),
        func.sum(Vendas.preço * Vendas.quantidade).label("valor_total"),
    ).group_by(Vendas.nome).filter(Vendas.user_id == current_user.id, Vendas.data == str(date.today())).all()
    
    todos = {
        'nome':[],
        'categoria':[],
        'quantidade':[],
        'valor':[],
    }
    for x in nomes:
        todos["nome"].append(x.nome)
        todos["categoria"].append(x.categoria)
        todos["quantidade"].append(x.total)
        todos["valor"].append(x.valor_total)

    gerar_relatorio = GerarRelatorios(
        quantidade=vendas_dia,
        nome=current_user.nome,
        medicamentos=nomes,
        valor=valor_vendas,
        dia=str(date.today())
        )
    return ''

@app.route("/definicoes", methods = ["POST", "GET"])
@login_required
def definicoes():
    if request.method == "POST":
        try:
            nome = request.form.get('Nome')
            senha = request.form.get('Senha')
            nivel = request.form.get('Nivel')
            tel = request.form.get('Tel')
            funcionario = Funcionario(nome=nome, user_id=current_user.id, senha=senha, nivel_acesso=nivel, telefone_whatsapp=tel)
            base.session.add(funcionario)
            base.session.commit()
            log(f'Foi adicionado mais um funcionário', 'login')
            return redirect(url_for('definicoes'))
        except AttributeError:
            return redirect(url_for("erro", erro='um'))
    todos_funcionario = base.session.query(Funcionario).filter(Funcionario.user_id == current_user.id)
    funcionario = base.session.query(Funcionario).filter_by(nome=session.get("funcionario_nome"), user_id=current_user.id).scalar()
    return render_template(
        'definicoes.html',
        user = current_user,
        lista_funcionarios = todos_funcionario,
        funcionario = funcionario
    )

@app.route("/definicoes/verificar-funcionario", methods = ["POST"])
@login_required
def verificar():
    if request.method == "POST":
        try:
            check_box = request.form.get('nome')
            nome = check_box
            session["funcionario_nome"] = nome
            funcionario = Funcionario.query.filter_by(user_id = current_user.id, nome = nome).first()
            session["funcionario_id"] = funcionario.id
            return redirect(url_for('home'))
        except AttributeError:
            return redirect(url_for("erro", erro='um'))

@app.route('/definicoes/apagar-funcionario', methods = ["POST", "GET"])
@login_required
def excluir_nome():
    nome = request.form.get('Nome')
    medicamento = Funcionario.query.filter_by(
        nome=nome, 
        user_id=current_user.id
    ).first()
    if medicamento:
        base.session.delete(medicamento)
        base.session.commit()
        flash(f"O medicamento foi removido com sucesso!")
    else:
        flash("Medicamento não encontrado.")

    return redirect(url_for('definicoes'))

@app.route('/adicionar-funcionario', methods = ["POST", "GET"])
@login_required
def gerente_funcionarios():
    lista = base.session.query(Funcionario).filter(Funcionario.user_id == current_user.id).all()
    if request.method == 'POST':
        if lista:
            check_box = request.form.get('nome')
            nome = check_box
            session["funcionario_nome"] = nome
            funcionario = Funcionario.query.filter_by(user_id = current_user.id, nome = nome).first()
            session["funcionario_id"] = funcionario.id
            log(f'Farmácia {session.get("funcionario_nome")} está ativo', 'login')
            return redirect(url_for('home'))
        else:
            nome = request.form.get('Nome')
            senha = request.form.get('Senha')
            tel = request.form.get('Tel')
            funcionario = Funcionario(nome=nome, user_id=current_user.id, senha=senha, nivel_acesso=2, telefone_whatsapp=tel)
            base.session.add(funcionario)
            base.session.commit()
            log(f'Farmácia {session.get('funcionario_nome')} está ativo', 'login')
            return redirect(url_for('gerente_funcionarios'))
    if request.method == "GET":
        return render_template(
            'gerente_funcionarios.html',
            lista_func = lista,
            user  = current_user
        )

@app.route('/erro/<string:erro>', methods = ["POST", "GET"])
def erro(erro):
    if erro == 'um':
        return render_template('erros/erro_um.html')
    elif erro == "dois":
        return render_template('erros/erro_dois.html')
@app.route('/historia', methods = ["POST", "GET"])
@login_required
def historia():
    try:
        historico = base.session.query(Historia).filter(Historia.user_id == current_user.id).all()
        funcionario = base.session.query(Funcionario).filter_by(nome=session.get("funcionario_nome"), user_id=current_user.id).scalar()
        actividades_funcionarios = base.session.query(
            Vendas.nome,
            func.sum(Vendas.quantidade).label("quantidade"),
            func.sum(Vendas.quantidade * Vendas.preço).label("valor"),
            ).group_by(Vendas.nome).filter(Vendas.user_id == current_user.id, Vendas.funcionario == funcionario, Vendas.data == str(date.today())).all()
        valor = base.session.query(func.sum(Vendas.quantidade * Vendas.preço)).filter(Vendas.user_id == current_user.id, Vendas.funcionario == funcionario, Vendas.data == str(date.today())).scalar() or 0
        total = base.session.query(func.count(Vendas.id)).filter(Vendas.user_id == current_user.id, Vendas.funcionario == funcionario, Vendas.data == str(date.today())).scalar() or 0
        
        return render_template(
        'historia.html',
        user = current_user,
        lista_historia = historico,
        historia_funcionario = actividades_funcionarios,
        funcionario = funcionario,
        valor_entrado = valor,
        Vendas_feitas = total
    )
    except TypeError:
        return redirect(url_for("erro", erro='dois'))

if __name__ == "__main__":
    with app.app_context():
        base.create_all()
    app.run(debug=True)