"""Valida referencias locais do Natflix sem dependencias externas."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import re
import sys

ROOT = Path(sys.argv[1] if len(sys.argv) > 1 else "_site").resolve()
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
        self.in_title = False
        self.title_text = ""
        self.anchor_depth = 0
        self.charset = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "title":
            self.title = True
            self.in_title = True
        if tag == "a":
            if self.anchor_depth: errors.append(f"{self.source}: links a aninhados")
            self.anchor_depth += 1
        if tag == "meta" and "charset" in attrs:
            if attrs["charset"].strip().lower() == "utf-8": self.charset = True
            else: errors.append(f"{self.source}: charset deve ser UTF-8")
        for attr in ("href", "src"):
            if attr in attrs: check(self.source, attrs[attr])

    def handle_endtag(self, tag):
        if tag == "title": self.in_title = False
        if tag == "a": self.anchor_depth = max(0, self.anchor_depth - 1)
    def handle_data(self, data):
        if self.in_title: self.title_text += data

for name in ("index.html", "pagina2.html", "pagina3.html", "pagina4.html", "pagina5.html", "resenha.html", "resenha2.html", "sobre.html"):
    if name not in FILES: errors.append(f"Pagina obrigatoria ausente: {name}")
for name in sorted(FILES):
    if name.endswith(".html"):
        parser = Page(name)
        try:
            parser.feed((ROOT / name).read_text(encoding="utf-8"))
        except UnicodeDecodeError:
            errors.append(f"{name}: arquivo nao pode ser decodificado como UTF-8")
        if not parser.title or not parser.title_text.strip() or not parser.charset: errors.append(f"{name}: title vazio/ausente ou declaracao UTF-8 ausente")
    elif name.endswith(".css"):
        for match in re.finditer(r"url\(\s*['\"]?([^)'\"]+)", (ROOT / name).read_text(encoding="utf-8")):
            check(name, match.group(1).strip())
if errors:
    print("\n".join(errors))
    sys.exit(1)
print("Validacao concluida: paginas e referencias locais verificadas.")
