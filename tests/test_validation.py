import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

VALIDATOR = Path(__file__).resolve().parents[1] / "scripts/validate_site.py"
PAGES = ["index.html", "pagina2.html", "pagina3.html", "pagina4.html", "pagina5.html", "resenha.html", "resenha2.html", "sobre.html"]

class ValidationTests(unittest.TestCase):
    def run_case(self, html, expected):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as directory:
            for page in PAGES:
                Path(directory, page).write_bytes(html)
            result = subprocess.run([sys.executable, str(VALIDATOR), directory], capture_output=True)
            self.assertEqual(result.returncode, expected, result.stdout.decode(errors="replace"))
    def test_valid(self):
        self.run_case(b'<meta charset="UTF-8"><title>Natflix</title><a href="pagina2.html?q=1#top">Abrir</a>', 0)
    def test_empty_title(self):
        self.run_case(b'<meta charset="utf-8"><title>  </title>', 1)
    def test_wrong_charset(self):
        self.run_case(b'<meta charset="latin1"><title>Natflix</title>', 1)
    def test_nested_links(self):
        self.run_case(b'<meta charset="utf-8"><title>Natflix</title><a href="#"><a href="#">X</a></a>', 1)
    def test_invalid_utf8(self):
        self.run_case(b'<meta charset="utf-8"><title>\xff</title>', 1)
    def test_missing_resource(self):
        self.run_case(b'<meta charset="utf-8"><title>Natflix</title><img src="missing.png">', 1)
