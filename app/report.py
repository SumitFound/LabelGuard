import json
from fpdf import FPDF

def make_report(scan):
    data = json.loads(scan.result_json)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    def write_line(value, size, height, bold=False):
        # Explicitly restore the left margin before every cell. With fpdf2,
        # multi_cell defaults to moving the cursor to the right edge.
        text = str(value).encode('latin-1', errors='replace').decode('latin-1')
        pdf.set_font('Helvetica', 'B' if bold else '', size)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pdf.epw, height, text, new_x='LMARGIN', new_y='NEXT')

    write_line('LabelGuard scan report', 16, 10, bold=True)
    write_line(
        f"Scan #{scan.id} | {scan.created_at.isoformat()} | Score {scan.score}/100 | {scan.verdict}",
        11, 8,
    )
    pdf.ln(4)
    for item in data['results']:
        write_line(f"{item['id']} - {item['status']}", 11, 7, bold=True)
        write_line(
            f"{item.get('explanation', '')} Reference: {item.get('reference', 'Not provided')} | "
            f"Verified: {item.get('verified', False)}",
            9, 6,
        )
        pdf.ln(2)
    output = pdf.output()
    return bytes(output) if isinstance(output, (bytes, bytearray)) else output.encode('latin-1')
