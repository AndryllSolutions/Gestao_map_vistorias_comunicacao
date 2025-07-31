LOGO_PATH = r"E:\Dev\static\img\LogoEnotec.png"

from flask import send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import black
from io import BytesIO
from textwrap import wrap

def gerar_laudo_vistoria_pdf(vistoria):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4
    y = 800

    def draw_wrapped_text(texto, x, y, width=100, line_height=15, font="Helvetica", font_size=11):
        c.setFont(font, font_size)
        for linha in wrap(texto, width=width):
            c.drawString(x, y, linha)
            y -= line_height
        return y

    # Cabeçalho
    
    try:
        logo = ImageReader(LOGO_PATH)
        c.drawImage(logo, 50, altura - 60, width=100, preserveAspectRatio=True, mask='auto')
    except Exception as e:
        print("Erro ao carregar o logo:", e)

    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(largura / 2, y, "LAUDO DA VISTORIA CAUTELAR")
    y -= 40

    # Dados principais
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

    # Normas e LGPD
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

    # Observações
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Observações Finais:")
    y -= 20
    observacoes = vistoria.observacoes or "Sem observações."
    y = draw_wrapped_text(observacoes, 50, y)

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Ciência do Morador quanto à Vistoria")
    y -= 20
    ciencia_texto = (
        f"Eu, {vistoria.nome_responsavel or '________________'}, portador do CPF {vistoria.cpf_responsavel or '________________'}, "
        "declaro que forneci de livre e espontânea vontade todas as informações referentes ao meu imóvel e estou ciente "
        "das fotografias e observações registradas durante a vistoria. Confirmo que estou de acordo com o conteúdo deste laudo."
    )
    y = draw_wrapped_text(ciencia_texto, 50, y)

    y -= 40
    c.drawString(50, y, "________________________________________")
    y -= 15
    c.drawString(50, y, "Assinatura do Responsável")

    # Bloco de fotos
    c.showPage()  # força nova página antes de iniciar o bloco de fotos
    fotos = vistoria.fotos
    if fotos:
        img_width = 220
        img_height = 140
        cols = 2
        rows = 3
        space_x = 40
        space_y = 90
        margin_x = 50
        TITULO_Y = altura - 50
        margin_top = TITULO_Y - 160

        x_positions = [margin_x + (img_width + space_x) * col for col in range(cols)]
        y_positions = [margin_top - (img_height + space_y) * row for row in range(rows)]

        for index, foto in enumerate(fotos):
            col = index % cols
            row = (index // cols) % rows

            if index % 6 == 0:
                if index > 0:
                    c.showPage()
                c.setFont("Helvetica-Bold", 14)
                c.drawCentredString(largura / 2, TITULO_Y, "REGISTRO FOTOGRÁFICO")

            x = x_positions[col]
            y = y_positions[row]

            try:
                img = ImageReader(foto.url)
                c.drawImage(img, x, y, width=img_width, height=img_height, preserveAspectRatio=True, anchor='n')
                c.setStrokeColor(black)
                c.rect(x, y, img_width, img_height, fill=0)

                legenda = foto.descricao or "Sem título"
                c.setFont("Helvetica", 10)
                c.drawCentredString(x + img_width / 2, y - 14, f"Foto {index + 1}: {legenda}")

                if foto.data_envio:
                    data_formatada = foto.data_envio.strftime("%d/%m/%Y %H:%M")
                    c.setFont("Helvetica-Oblique", 8)
                    c.drawCentredString(x + img_width / 2, y - 28, f"Enviada em {data_formatada}")

            except Exception as e:
                print("Erro ao carregar imagem no PDF:", e)

    c.save()
    buffer.seek(0)
    return buffer
