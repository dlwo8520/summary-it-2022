"""Render a buildless static archive from the retained 2022 UI templates.

Python standard library only. No network, model loading or translation calls.
"""
from html import escape
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
DATA = json.loads((ROOT / 'examples/fixed.json').read_text(encoding='utf-8'))
REPO = 'https://github.com/dlwo8520/summary-it-2022'


def banner():
    return f'''<aside class="archive-banner" aria-label="2022년 프로젝트 아카이브 안내">
  <strong>2022년 프로젝트 · 최초 버전 아카이브</strong>
  <p>2022년 10월 제작한 ‘요약해줘 / Summary it’의 원본 화면을 보존한 정적 예시 페이지입니다.
  새로운 글을 처리하지 않으며, 예시 본문·결과는 복원용으로 준비했습니다. <a href="{REPO}" target="_blank" rel="noopener noreferrer">GitHub</a></p>
</aside>'''


def reading(label):
    return f'''<div class="legacy-reading"><span>{label}</span><audio controls preload="none" aria-disabled="true" aria-label="{label} 원본 기능 — 정적 데모에서는 음성 파일 미제공"></audio></div>'''


def results(language, item):
    korean = language == 'kr'
    title, input_label, summary_label = ('결과', '입력 :', '요약 :') if korean else ('Result', 'Input :', 'Summary :')
    source_reading, summary_reading = ('입력 읽기 :', '요약 읽기 :') if korean else ('Input Reading :', 'Summary Reading :')
    translation = '' if korean else f'''<h4>Korean Translation :</h4><p class="saved-text" lang="ko">{escape(item['translation'])}</p>{reading('Trans Reading :')}'''
    return f'''<section id="result" class="archive-results" aria-labelledby="result-title">
  <h3 class="post-title" id="result-title">{title}</h3>
  <p class="saved-note">고정 예시 · {escape(item['model'])} 사전 생성 결과<br>2022년 당시의 이용 기록이 아닌, 아카이브 복원용 예시입니다.</p>
  <h4>{input_label}</h4><p class="saved-text">{escape(item['source'])}</p>{reading(source_reading)}
  <h4>{summary_label}</h4><p class="saved-text">{escape(item['summary'])}</p>{reading(summary_reading)}
  {translation}
  <p class="legacy-note">음성 읽기는 원본 서버에서 제공하던 기능입니다. 이 정적 데모에는 음성 파일이 포함되지 않습니다.
  {'영어 요약의 한국어 번역은 화면 복원을 위해 작성한 고정 예시이며 번역 API를 호출하지 않습니다.' if not korean else ''}
  모델이 생성한 요약은 원문과 함께 확인해 주세요.</p>
</section>'''


def render(template_name, language=None):
    text = (ROOT / 'archive/templates' / template_name).read_text(encoding='utf-8-sig')
    text = text.replace('{% load static %}', '').replace('{% csrf_token %}', '')
    # Original remote dependencies are replaced by local styles, fonts and a tiny nav script.
    text = re.sub(r'<script\b[^>]*>.*?</script>', '', text, flags=re.S)
    text = re.sub(r'<style>.*?</style>', '', text, flags=re.S)
    text = re.sub(r'<link\b[^>]*fonts\.googleapis\.com[^>]*>', '', text)
    text = re.sub(r'<link\b[^>]*\{% static[^>]*>', '<link href="assets/css/fonts.css" rel="stylesheet"><link href="assets/css/styles.css" rel="stylesheet"><link href="assets/css/archive.css" rel="stylesheet">', text)
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = text.replace('<html lang="en">', '<html lang="ko">' if language != 'en' else '<html lang="en">')
    page_title = {'kr': '요약해줘 (Korean)', 'en': 'Summary it (English)', None: '요약해줘 / Summary it'}[language]
    text = re.sub(r'<title>.*?</title>', f'<title>{page_title} | 2022년 프로젝트 원본 데모</title>', text)
    description = '2022년 10월에 제작한 요약해줘 / Summary it 프로젝트의 최초 UI를 보존한 고정 예시 아카이브입니다.'
    text = text.replace('<meta name="description" content="" />', f'<meta name="description" content="{description}" />')
    text = text.replace('<head>', '<head>\n<meta name="theme-color" content="#0085a1"><meta property="og:title" content="요약해줘 / Summary it — 2022년 프로젝트"><meta property="og:description" content="2022년 10월 제작 · 최초 버전 UI 아카이브 · 고정 예시">')
    text = text.replace("url('static/assets/img/home-bg.jpg')", "url('assets/img/home-bg.jpg')")
    text = text.replace('<div class="loading"></div>', '')
    text = text.replace('<body>', '<body>\n<a class="skip-link" href="#main-content">본문으로 건너뛰기</a>')
    if language:
        other_page, brand = ('en.html', 'Summary it(English.ver)') if language == 'kr' else ('kr.html', '요약해줘(Korean)')
    else:
        other_page, brand = ('index.html', '요약해줘/Summary it')
    nav = f'''<nav class="navbar navbar-expand-lg navbar-light" id="mainNav" aria-label="원본 페이지 메뉴"><div class="container px-4 px-lg-5 archive-navbar"><a class="navbar-brand" href="{other_page}">{brand}</a><ul class="navbar-nav"><li class="nav-item"><a class="nav-link" href="index.html">Home</a></li></ul></div></nav>'''
    text = re.sub(r'<nav\b.*?</nav>', nav, text, count=1, flags=re.S)
    text = text.replace('<div class="site-heading">', '<div class="site-heading"><p class="archive-year">2022년 10월 · FINAL PROJECT</p>')
    text = text.replace('</header>', '</header>\n' + banner(), 1)
    text = text.replace('<div class="container px-lg-5 px-lg-5" >', '<main id="main-content" class="container px-lg-5 px-lg-5">', 1)
    # The main container is the last div closed immediately before the footer.
    text = re.sub(r'</div>\s*(?:</center>\s*)?<footer', '</main>\n<footer', text, count=1)
    text = text.replace('<center>', '').replace('</center>', '')
    if language:
        item = DATA[language]
        text = re.sub(r'<form\b[^>]*>', '<section class="archive-form" aria-label="고정된 예시 본문">', text)
        text = text.replace('</form>', '</section>')
        textarea = f'''<p class="archive-input-note">읽기 전용 · 복원용 예시 본문입니다. 아래 버튼은 미리 저장한 결과로 이동합니다.</p><label class="visually-hidden-label" for="searchKeyword">{'한국어' if language == 'kr' else 'English'} 예시 본문 (읽기 전용)</label><textarea name="contents" rows="20" style="border:2.5px solid #63717f;border-radius:0 10px 20px 30px;font-size:12pt" id="searchKeyword" readonly spellcheck="false">{escape(item['source'])}</textarea>'''
        text = re.sub(r'<textarea\b.*?</textarea>', textarea, text, count=1, flags=re.S)
        text = re.sub(r'<div\s+align="right"><input.*?</div>', f'<div class="archive-count">{len(item["source"]):,} {"글자" if language == "kr" else "characters"}</div>', text, count=1, flags=re.S)
        text = re.sub(r'<button class="btn btn-primary">.*?</button>', f'<a class="btn btn-primary" href="#result">{"요약 예시 보기" if language == "kr" else "Summary example"}</a>', text, count=1)
        text = re.sub(r'<p class="post-meta">\s*<h3.*?</p>', results(language, item), text, count=1, flags=re.S)
    else:
        text = text.replace('class="container px-lg-5 px-lg-5"', 'class="container px-lg-5 px-lg-5 archive-home"')
        text = text.replace('id="main-content" class="container px-lg-5 px-lg-5"', 'id="main-content" class="container px-lg-5 px-lg-5 archive-home"')
        text = re.sub(r'<div class="post-preview">.*?</div>', '<div class="post-preview"><a class="btn btn-primary" href="kr.html">한국어</a><a class="btn btn-primary" href="en.html">English</a></div><p class="archive-caption">2022년 프로젝트의 원본 화면을 언어별로 둘러보세요.<br>현재 개선 버전은 <a href="https://dlwo8520.github.io/hannune-summary-demo/">한눈에 데모</a>에서 볼 수 있습니다.</p>', text, count=1, flags=re.S)
    text = re.sub(r'<ul class="list-inline text-center">.*?</ul>', '', text, flags=re.S)
    text = text.replace('>Final Project</div>', '>Final Project · October 2022</div><p class="archive-footer-links"><a href="index.html">2022 원본 홈</a><a href="' + REPO + '" target="_blank" rel="noopener noreferrer">GitHub</a><a href="https://dlwo8520.github.io/hannune-summary-demo/">개선 버전 보기</a></p>')
    text = text.replace('</body>', '<script src="assets/js/scripts.js" defer></script>\n</body>')
    text = re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+', '\n\n', text)
    assert '{%' not in text and '{{' not in text, template_name
    return text.strip() + '\n'


def build():
    for source, destination, language in [('home.html', 'index.html', None), ('kr.html', 'kr.html', 'kr'), ('en.html', 'en.html', 'en')]:
        (ROOT / 'docs' / destination).write_text(render(source, language), encoding='utf-8')
        print('Rendered', destination)
    original_js = (ROOT / 'archive/scripts.js').read_text(encoding='utf-8-sig')
    public_js = original_js.replace('console.log(123);', '').replace("classList.remove(['is-visible'])", "classList.remove('is-visible')")
    path = ROOT / 'docs/assets/js/scripts.js'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(public_js, encoding='utf-8')


if __name__ == '__main__':
    build()
