from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
from datetime import datetime

# Simulação da estrutura de vistoria com placeholders
class FakeFoto:
    def __init__(self, descricao, data_envio=None):
        self.descricao = descricao
        self.data_envio = data_envio

class FakeObra:
    nome = "Residencial Exemplo"

class FakeVistoria:
    data_1 = "01/08/2025"
    hora_1 = "10:30"
    nome_responsavel = "Maria Oliveira"
    cpf_responsavel = "987.654.321-00"
    tipo_vinculo = "Inquilina"
    rua = "Av. das Palmeiras"
    numero = "456"
    bairro = "Jardim das Rosas"
    municipio = "Campinas"
    tipo_imovel = "Apartamento"
    soleira = "Boa"
    calcada = "Regular"
    observacoes = "Há uma pequena infiltração na cozinha."
    obra = FakeObra()
    fotos = [FakeFoto(f"Foto {i+1}", datetime.now()) for i in range(6)]

# Gerar o PDF com placeholders no lugar das imagens
def gerar_pdf_placeholder(vistoria):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4
    y = 800

    def draw_wrapped_text(texto, x, y, width=100, line_height=15, font="Helvetica", font_size=11):
        c.setFont(font, font_size)
        for linha in texto.split("\n"):
            for wrapped in wrap(linha, width=width):
                c.drawString(x, y, wrapped)
                y -= line_height
        return y

    # Cabeçalho
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(largura / 2, y, "LAUDO DA VISTORIA CAUTELAR")
    y -= 40

    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Data da Vistoria: {vistoria.data_1 or 'N/A'} {vistoria.hora_1 or ''}")
    y -= 20
    c.drawString(50, y, f"Responsável: {vistoria.nome_responsavel or 'N/A'} - CPF: {vistoria.cpf_responsavel or 'N/A'}")
    y -= 20
    c.drawString(50, y, f"Vínculo: {vistoria.tipo_vinculo or 'N/A'}")
    y -= 20
    c.drawString(50, y, f"Endereço: {vistoria.rua}, {vistoria.numero} - {vistoria.bairro}, {vistoria.municipio}")
    y -= 20
    c.drawString(50, y, f"Tipo de Imóvel: {vistoria.tipo_imovel}")
    y -= 20
    c.drawString(50, y, f"Soleira: {vistoria.soleira}")
    y -= 20
    c.drawString(50, y, f"Calçada: {vistoria.calcada}")
    y -= 20
    obra_nome = vistoria.obra.nome if vistoria.obra else "Obra não especificada"
    c.drawString(50, y, f"Obra: {obra_nome}")
    y -= 30

    # Texto normativo
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Norma Técnica")
    y -= 20
    y = draw_wrapped_text(
        "ABNT NBR 12722:1992 - Discriminação de serviços para construção de edifícios.\n"
        "A vistoria resguarda os interesses das partes envolvidas e do público em geral, "
        "devendo ser realizada por profissional especializado, incluindo planta de localização, "
        "relatório descritivo e registros fotográficos.",
        50, y
    )
    y -= 10

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Informações Legais - LGPD")
    y -= 20
    y = draw_wrapped_text(
        "Em conformidade com a Lei Geral de Proteção de Dados (LGPD), realizamos a vistoria cautelar no imóvel, "
        "coletando apenas os dados necessários. As informações serão utilizadas exclusivamente para os fins da vistoria "
        "e não serão compartilhadas sem consentimento, salvo por exigência legal.",
        50, y
    )
    y -= 10

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Observações Finais:")
    y -= 20
    y = draw_wrapped_text(vistoria.observacoes or "Sem observações.", 50, y)
    y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Ciência do Morador quanto à Vistoria")
    y -= 20
    y = draw_wrapped_text(
        f"Eu, {vistoria.nome_responsavel or '________________'}, portador do CPF {vistoria.cpf_responsavel or '________________'}, "
        "declaro que forneci de livre e espontânea vontade todas as informações referentes ao meu imóvel e estou ciente "
        "das fotografias e observações registradas durante a vistoria. Confirmo que estou de acordo com o conteúdo deste laudo.",
        50, y
    )
    y -= 40
    c.drawString(50, y, "________________________________________")
    y -= 15
    c.drawString(50, y, "Assinatura do Responsável")

    # Página de fotos (placeholders)
    fotos = vistoria.fotos
    if fotos:
        c.showPage()
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(largura / 2, altura - 50, "REGISTRO FOTOGRÁFICO")

        img_width = 220
        img_height = 140
        space_x = 40
        space_y = 90
        margin_x = 50
        titulo_y = altura - 50
        margin_top = titulo_y - 160

        x_positions = [margin_x + (img_width + space_x) * col for col in range(2)]
        y_positions = [margin_top - (img_height + space_y) * row for row in range(3)]

        for index, foto in enumerate(fotos):
            col = index % 2
            row = (index // 2) % 3

            if index % 6 == 0 and index > 0:
                c.showPage()
                c.setFont("Helvetica-Bold", 14)
                c.drawCentredString(largura / 2, altura - 50, "REGISTRO FOTOGRÁFICO")

            x = x_positions[col]
            y = y_positions[row]

            c.setFillColor(colors.lightgrey)
            c.rect(x, y, img_width, img_height, fill=1)
            c.setFillColor(colors.black)
            c.setFont("Helvetica", 10)
            c.drawCentredString(x + img_width / 2, y + img_height / 2, f"Imagem {index + 1}")
            c.drawCentredString(x + img_width / 2, y - 14, foto.descricao)
            if foto.data_envio:
                c.setFont("Helvetica-Oblique", 8)
                c.drawCentredString(x + img_width / 2, y - 28, foto.data_envio.strftime("Enviada em %d/%m/%Y %H:%M"))

    c.save()
    buffer.seek(0)
    return buffer

# Gerar o PDF com placeholders
vistoria = FakeVistoria()
buffer = gerar_pdf_placeholder(vistoria)
pdf_placeholder_path = "Users\rmfne\Downloads>/laudo_com_placeholders.pdf"
with open(pdf_placeholder_path, "wb") as f:
    f.write(buffer.getvalue())

pdf_placeholder_path
