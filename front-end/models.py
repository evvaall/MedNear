from base_dados.db import base
from datetime import datetime, date
from flask_login import LoginManager, UserMixin
from sqlalchemy import UniqueConstraint


class Farmacia(base.Model, UserMixin):
    __tablename__ = "farmacia"
    id = base.Column(base.Integer, primary_key=True)
    nome = base.Column(base.String(50), nullable=False)
    email = base.Column(base.String(50), nullable=False, unique=True)
    senha = base.Column(base.String(255), nullable=False)
    localizacao = base.Column(base.String(100), nullable=False)
    nif = base.Column(base.String, nullable=False, unique=True)
    telefone_whatsapp = base.Column(base.String(15), nullable=False)
    medicamento = base.relationship("Medicamento", backref="dono", lazy=True)
    historico = base.relationship("Historia", backref= "dono", lazy=True)
    vendas = base.relationship("Vendas", backref= "dono", lazy=True)
    def __init__(self, nome, email, senha, localizacao, nif, telefone):
        self.nome = nome
        self.email = email
        self.senha = senha
        self.localizacao = localizacao
        self.nif = nif
        self.telefone_whatsapp = telefone

    def __repr__(self):
        return f"<{self.nome}>"


class Medicamento(base.Model):
    __tablename__ = "medicamento"
    id = base.Column(base.Integer, primary_key=True)
    nome = base.Column(base.String(50), nullable=False)
    categoria = base.Column(base.String(50), nullable=False)
    preço = base.Column(base.Float, nullable=False)
    quantidade = base.Column(base.Integer, nullable=False, default=0)
    user_id = base.Column(base.Integer, base.ForeignKey('farmacia.id'), nullable=False)
    validade = base.Column(base.String(50), nullable=False)
    def __init__(self, nome, categoria, preço, quantidade, user_id, validade):
        self.nome = nome
        self.categoria = categoria
        self.preço = preço
        self.quantidade = quantidade
        self.user_id = user_id
        self.validade = validade
    __table_args__ = (UniqueConstraint('nome', 'user_id', name='_nome_user_uc'),)
    def __repr__(self):
        return f"<{self.nome}>"

class Vendas(base.Model):
    __tablename__ ="vendas"
    id = base.Column(base.Integer, primary_key=True)
    nome = base.Column(base.String(50), nullable=False)
    preço = base.Column(base.Float, nullable=False)
    quantidade = base.Column(base.Integer, nullable=False, default=0)
    data = base.Column(base.DateTime, default=date.today())
    user_id = base.Column(base.Integer, base.ForeignKey('farmacia.id'), nullable=False)
    obs =  base.Column(base.String(50), nullable=False)
    def __init__(self, nome, preço, quantidade, user_id, data, obs):
        self.nome = nome
        self.user_id = user_id
        self.quantidade = quantidade
        self.data = data
        self.obs = obs
        self.preço=preço
    def __repr__(self):
        return f"<{self.nome}>"
    

class Historia(base.Model):
    __tablename__ = "historia"
    id = base.Column(base.Integer, primary_key=True)
    descricao = base.Column(base.String(250), nullable=False)
    data = base.Column(base.DateTime, default= datetime.now())
    user_id = base.Column(base.Integer, base.ForeignKey('farmacia.id'), nullable=False)
    tipo = base.Column(base.String(50), nullable=False)
    def __init__(self,tipo, data, descricao, user_id):
        self.descricao = descricao
        self.data = data
        self.tipo = tipo
        self.user_id = user_id
    def __repr__(self):
        return f"<Historia: {self.descricao} em {self.data}>"
    
class Funcionario(base.Model):
    __tablename__ = "funcionario"
    id = base.Column(base.Integer, primary_key=True)
    nome = base.Column(base.String(50), nullable=False)
    user_id = base.Column(base.Integer, base.ForeignKey('farmacia.id'), nullable=False)
    def __init__(self, nome, user_id, ):
        self.nome = nome
        self.user_id = user_id