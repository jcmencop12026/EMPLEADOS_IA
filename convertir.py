from pathlib import Path
from docx import Document

entrada = Path(r"D:\empleados_ia\Docs")
salida = Path(r"D:\empleados_ia\Markdown")
salida.mkdir(exist_ok=True)

for archivo in entrada.glob("*.docx"):
    doc = Document(archivo)
    texto = "\n".join(p.text for p in doc.paragraphs)

    (salida / (archivo.stem + ".txt")).write_text(
        texto,
        encoding="utf-8"
    )

print("Listo.")