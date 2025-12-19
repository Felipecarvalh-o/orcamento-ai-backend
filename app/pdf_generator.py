# app/pdf_generator.py

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from datetime import datetime
import io


def gerar_pdf_orcamento(
    nome_profissional: str,
    descricao: str,
    materiais: list,
    tempo_estimado: str,
    valor_total: float,
    plano: str,
    logo_path: str | None = None
):
    """
    Gera um PDF profissional de orçamento.
    Retorna bytes do PDF.
    """

    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    largura, altura = A4

    y = altura - 2 * cm

    # Logo (apenas premium)
    if plano == "premium" and logo_path:
        pdf.drawImage(logo_path, 2 * cm, y - 2 * cm, width=4 * cm, preserveAspectRatio=True)
        y -= 3 * cm

    # Título
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(2 * cm, y, "ORÇAMENTO DE SERVIÇO")
    y -= 1.2 * cm

    # Profissional
    pdf.setFont("Helvetica", 11)
    pdf.drawString(2 * cm, y, f"Profissional: {nome_profissional}")
    y -= 0.8 * cm

    pdf.drawString(2 * cm, y, f"Data: {datetime.now().strftime('%d/%m/%Y')}")
    y -= 1.2 * cm

    # Descrição
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(2 * cm, y, "Descrição do Serviço:")
    y -= 0.6 * cm

    pdf.setFont("Helvetica", 11)
    pdf.drawString(2 * cm, y, descricao)
    y -= 1.2 * cm

    # Materiais
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(2 * cm, y, "Materiais:")
    y -= 0.6 * cm

    pdf.setFont("Helvetica", 11)
    for mat in materiais:
        linha = f"- {mat['nome']} | Qtde: {mat['quantidade']} | R$ {mat['valor_estimado']}"
        pdf.drawString(2 * cm, y, linha)
        y -= 0.5 * cm

    y -= 0.8 * cm

    # Tempo
    pdf.drawString(2 * cm, y, f"Tempo estimado: {tempo_estimado}")
    y -= 1 * cm

    # Valor final
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(2 * cm, y, f"VALOR TOTAL: R$ {valor_total:.2f}")

    pdf.showPage()
    pdf.save()

    buffer.seek(0)
    return buffer.read()
