"""Valida referencias locais do Natflix sem dependencias externas."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
FILES = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts}
errors = []

def check(source, value):
    if not value.strip():
        errors.append(f"{source}: referencia vazia")
        return
    url = urlsplit(value)
    if url.scheme or url.netloc or not url.path:
        return
    if url.path.startswith("/"):
        errors.append(f"{source}: caminho absoluto incompativel com subdiretorio Pages: {value}")
        return
    import posixpath
    target = posixpath.normpath(str(Path(source).parent.as_posix()) + "/" + unquote(url.path))
    if target not in FILES:
        errors.append(f"{source}: arquivo ausente ou capitalizacao incorreta: {value}")

class Page(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.source = source
        self.title = False
        self.charset = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title": self.title = True
        if tag == "meta" and attrs.get("charset"): self.charset = True
        for attr in ("href", "src"):
            if attr in attrs: check(self.source, attrs[attr])

for name in ("index.html", "pagina2.html", "pagina3.html", "pagina4.html", "pagina5.html", "resenha.html", "resenha2.html", "sobre.html"):
    if name not in FILES: errors.append(f"Pagina obrigatoria ausente: {name}")
for name in sorted(FILES):
    if name.endswith(".html"):
        parser = Page(name)
        parser.feed((ROOT / name).read_text(encoding="utf-8"))
        if not parser.title or not parser.charset: errors.append(f"{name}: falta title ou charset")
    elif name.endswith(".css"):
        for match in re.finditer(r"url\(\s*['\"]?([^)'\"]+)", (ROOT / name).read_text(encoding="utf-8")):
            check(name, match.group(1).strip())
if errors:
    print("\n".join(errors))
    sys.exit(1)
print("Validacao concluida: paginas e referencias locais verificadas.")
