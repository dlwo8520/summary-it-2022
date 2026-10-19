"""Meaningful checks for a static archival publication. No third-party packages."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import hashlib
import json
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / 'docs'


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = []
        self.refs = []
        self.active = []
        self.textareas = []
        self.feed(text)

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if 'id' in attrs:
            self.ids.append(attrs['id'])
        for key in ('href', 'src'):
            if attrs.get(key):
                self.refs.append(attrs[key])
        self.refs.extend(re.findall(r'url\([\'"]?([^\)\'\"]+)', attrs.get('style', '')))
        if tag in ('script', 'link') and (tag == 'script' or attrs.get('rel') == 'stylesheet'):
            self.active.append(attrs.get('src', attrs.get('href', '')))
        if tag == 'textarea':
            self.textareas.append(attrs)
        if tag == 'form':
            raise AssertionError('A static archive must not submit a form')


class ArchiveTests(unittest.TestCase):
    def test_original_files_are_preserved_exactly(self):
        manifest = json.loads((ROOT / 'archive/source-manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['project_created'], '2022-10')
        for item in manifest['files']:
            self.assertEqual(hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest(), item['sha256'], item['path'])

    def test_three_pages_identify_2022_and_have_no_server_templates(self):
        for filename in ('index.html', 'kr.html', 'en.html'):
            html = (DOCS / filename).read_text(encoding='utf-8')
            self.assertIn('2022년 프로젝트 · 최초 버전 아카이브', html)
            self.assertIn('October 2022', html)
            self.assertIn('2022년 프로젝트 원본 데모', html)
            self.assertNotIn('{%', html)
            self.assertNotIn('{{', html)
            parsed = Page(html)
            self.assertEqual(len(set(parsed.ids)), len(parsed.ids))
            if filename != 'index.html':
                self.assertEqual(len(parsed.textareas), 1)
                self.assertIn('readonly', parsed.textareas[0])

    def test_links_assets_fonts_and_fragments_resolve_without_cdn(self):
        for filename in ('index.html', 'kr.html', 'en.html'):
            html = (DOCS / filename).read_text(encoding='utf-8')
            parsed = Page(html)
            for active in parsed.active:
                self.assertFalse(urlsplit(active).scheme, active)
            for ref in parsed.refs:
                url = urlsplit(ref)
                if url.scheme:
                    continue
                self.assertFalse(ref.startswith('/'), ref)
                target = DOCS / unquote(url.path or filename)
                self.assertTrue(target.is_file(), str(target))
                if url.fragment:
                    self.assertIn(url.fragment, Page(target.read_text(encoding='utf-8')).ids)
        fonts = (DOCS / 'assets/css/fonts.css').read_text(encoding='utf-8')
        for ref in re.findall(r'url\(([^)]+)\)', fonts):
            font = DOCS / 'assets/css' / ref
            self.assertTrue(font.read_bytes().startswith(b'wOF2'))

    def test_fixed_results_and_provenance_are_present(self):
        fixtures = json.loads((ROOT / 'examples/fixed.json').read_text(encoding='utf-8'))
        self.assertEqual(fixtures['_provenance']['project_year'], 2022)
        self.assertEqual(fixtures['_provenance']['examples_prepared'], '2026-10-19')
        for language in ('kr', 'en'):
            html = (DOCS / f'{language}.html').read_text(encoding='utf-8')
            from html import unescape
            plain = unescape(html)
            self.assertIn(fixtures[language]['summary'], plain)
            self.assertLess(len(fixtures[language]['summary']), len(fixtures[language]['source']))
            self.assertIn('2022년 당시의 이용 기록이 아닌', plain)
        self.assertIn(fixtures['en']['translation'], unescape((DOCS / 'en.html').read_text(encoding='utf-8')))

    def test_no_inference_calls_secrets_database_or_weights_are_published(self):
        allowed = {'.html', '.css', '.js', '.jpg', '.ico', '.woff2'}
        for file in DOCS.rglob('*'):
            if not file.is_file():
                continue
            self.assertTrue(file.suffix in allowed or file.name == '.nojekyll', file.name)
            if file.suffix in {'.html', '.css', '.js'}:
                text = file.read_text(encoding='utf-8')
                self.assertNotRegex(text, r'\bfetch\s*\(|XMLHttpRequest|sendBeacon|WebSocket|localStorage|sessionStorage')
                self.assertNotRegex(text, r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_|cfat_|CLOUDFLARE_API_TOKEN\s*=')

    def test_rebuild_is_deterministic(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        from build import render
        for source, output, language in [('home.html', 'index.html', None), ('kr.html', 'kr.html', 'kr'), ('en.html', 'en.html', 'en')]:
            self.assertEqual(render(source, language), (DOCS / output).read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main(verbosity=2)
