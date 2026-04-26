from jinja2 import Template
from weasyprint import HTML

def GerarRelatorios(nome, quantidade, medicamentos, dia, valor):
    html_template = open("templates/relatorios.html").read()
    pagina = Template(html_template)

    html_final = pagina.render(
        nome = nome,
        quantidade_vendas = quantidade,
        medicamentos_vendidos = medicamentos,
        dia = dia,
        valor_total = valor
    )
    
    print(quantidade)
    return HTML(string=html_final).write_pdf("relatorio.pdf")
