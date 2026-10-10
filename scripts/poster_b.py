"""Poster A2 billboard (três passos, para quem não é da área) e folheto A4, no estilo B.

Uso:
    python scripts/poster_b.py [--url URL]

Saída em poster/: poster_b_A2.pdf, poster_b_A3.pdf (o A2 reduzido, vetorial), folheto_b_A4.pdf e as pré-visualizações
em poster/imagens_b/ (poster inteiro, recorte a 100 % do A3 e folheto). O HTML é impresso pelo Chrome sem janela.

Desenho (#betterposter): faixa de título; passo 1, o problema, com os cinco renders; a conclusão numa frase; passo 2,
como decidimos, com o funil; passo 3, o que descobrimos, com o espectro de confiança; em baixo, os pormenores técnicos
em letra pequena, a extensão dos perfis de doente com o aviso, o código QR e as referências. Tamanhos de letra no A2:
título 76 pt, frase central 50 pt, cabeçalhos 40 pt, texto 24 pt e notas 17 pt (no A3: cerca de 17 e 12 pt).
Os números vêm de results/ e de data/ (scripts/apresentacao.py e scripts/apresentacao_b.py).
O código QR só é gerado com --url; sem URL fica um marcador até o repositório público existir.
"""
from __future__ import annotations

import argparse
import html
import math
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
sys.path.insert(0, str(RAIZ / "src"))
import apresentacao_b as ab  # noqa: E402
from figuras import curto  # noqa: E402

POSTER = RAIZ / "poster"
PREVIA = POSTER / "imagens_b"
CACHE = POSTER / "recursos_b"
FONTES = RAIZ / "design" / "fontes"
CHROME = Path(r"<pasta local>")
RENDERS = [Path(r"partilha\renders\final"), Path(r"partilha\renders\rapida_8out")]

REFERENCIAS = [  # forma curta no poster; as referências completas estão no relatório
    "Petković D. L. et al. (2025). Applied Sciences 15(16), 9198.",
    "Jain A. et al. (2013). APL Materials 1, 011002 (Materials Project).",
    "ICH (2022). Guideline for elemental impurities Q3D(R2).",
    "Gibson L. J., Ashby M. F. (1997). Cellular solids, 2.ª ed. Cambridge University Press.",
    "Navarro M. et al. (2008). J. R. Soc. Interface 5(27), 1137-1158.",
]

# tokens: primitivos -> semânticos -> componentes (só os componentes usam os semânticos; nada de cores soltas)
TOKENS = """
:root {
  /* primitivos */
  --noite-900: #0b1b2e; --azul-200: #b9dff1; --azul-300: #6cbfe5; --azul-500: #0595d1; --azul-700: #0477a8; --tinta-900: #0f1720; --cinza-600: #55606b;
  --cinza-100: #f2f5f8; --linha-200: #d5dde5; --noite-300: #9fb6c9; --laranja-500: #e8833a; --laranja-50: #fdf0e6;
  --papel: #fdfdfc;
  --t-display: 64pt; --t-frase: 42pt; --t-cab: 36pt; --t-texto: 22pt; --t-nota: 16pt;
  --e-1: 4mm; --e-2: 8mm; --e-3: 14mm; --e-4: 22mm; --raio: 4mm; --funil-w: 56mm;
  /* semânticos */
  --cor-fundo: var(--papel); --cor-texto: var(--tinta-900); --cor-texto-2: var(--cinza-600);
  --cor-marca: var(--azul-500); --cor-marca-texto: var(--azul-700); --cor-destaque: var(--laranja-500);
  --cor-destaque-fundo: var(--laranja-50); --cor-superficie: var(--cinza-100); --cor-escura: var(--noite-900);
  --cor-escura-texto-2: var(--noite-300); --cor-linha: var(--linha-200);
  /* componentes */
  --faixa-fundo: var(--cor-escura); --cartao-fundo: var(--cor-superficie); --frase-fundo: var(--cor-destaque-fundo);
  --chip-solida: var(--cor-marca); --chip-fragil: var(--cor-destaque); --chip-indicacao: var(--cor-texto-2);
}
"""


# ---------------------------------------------------------------- dados (funções puras, testadas)

def render(cena: str, candidatas: list[Path] = RENDERS) -> Path:
    """Render transparente de uma cena: o 4K final, se existir, senão o da passagem rápida."""
    for p in candidatas:
        f = p / f"{cena}_transparente.png"
        if f.exists():
            return f
    raise FileNotFoundError(f"sem render transparente de {cena}")


def larguras_funil(ns: list[int], minimo: float = 0.18) -> list[float]:
    """Largura relativa de cada degrau do funil (escala logarítmica, a primeira é 1 e nenhuma fica abaixo do mínimo).

    Em linguagem simples: os números vão de centenas de milhares a 5; numa escala normal só se veria a primeira barra,
    por isso a largura segue o número de algarismos e o número exato fica escrito."""
    topo = math.log10(max(ns) + 1)
    return [minimo + (1 - minimo) * math.log10(n + 1) / topo for n in ns]


def degraus_funil(fu: dict[str, int]) -> list[tuple[int, str]]:
    """Os degraus do funil do poster (número, texto simples)."""
    return [(fu["mp"], "compostos numa base aberta"),
            (fu["nivel2"], "sem tóxicos, estáveis e com a rigidez certa"),
            (fu["base"], "com norma ou uso clínico e fontes publicadas"),
            (fu["final"], "recomendados: um por implante")]


def numero(n: int) -> str:
    """Número com espaço fino inseparável nos milhares (271 325)."""
    return f"{n:,}".replace(",", "\u202f")


def qr(url: str | None, pasta: Path = CACHE) -> Path | None:
    if not url:
        return None
    import qrcode
    pasta.mkdir(parents=True, exist_ok=True)
    d = pasta / "qr.png"
    qrcode.make(url, border=1, box_size=20).save(d)
    return d


# ---------------------------------------------------------------- HTML

def _css(largura_mm: float, altura_mm: float) -> str:
    fonte = lambda f: (FONTES / f).as_uri()  # noqa: E731
    return TOKENS + f"""
@font-face {{ font-family: Inter; font-weight: 400; src: url('{fonte("Inter-Regular.ttf")}'); }}
@font-face {{ font-family: Inter; font-weight: 700; src: url('{fonte("Inter-Bold.ttf")}'); }}
@page {{ size: {largura_mm}mm {altura_mm}mm; margin: 0; }}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html, body {{ width: {largura_mm}mm; }}
body {{ font-family: Inter, 'Segoe UI', sans-serif; color: var(--cor-texto); background: var(--cor-fundo);
       font-size: var(--t-texto); line-height: 1.3; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.pagina {{ width: 100%; min-height: {altura_mm}mm; display: flex; flex-direction: column; }}
.faixa {{ background: var(--faixa-fundo); color: var(--cor-fundo); padding: var(--e-2) 18mm var(--e-3);
         display: grid; grid-template-columns: 1fr auto; gap: var(--e-2); align-items: end; }}
.faixa .topo {{ grid-column: 1 / -1; display: flex; align-items: center; gap: var(--e-2); }}
.faixa .topo img {{ height: 17mm; }}
.faixa .kicker {{ font-size: var(--t-nota); color: var(--cor-escura-texto-2); margin-left: var(--e-1); }}
.faixa h1 {{ font-size: var(--t-display); font-weight: 700; letter-spacing: -0.02em; line-height: 1.02; }}
.faixa .sub {{ font-size: var(--t-texto); color: var(--cor-escura-texto-2); margin-top: var(--e-1); }}
.faixa .autor {{ text-align: right; font-size: var(--t-texto); line-height: 1.35; }}
.faixa .autor b {{ display: block; }}
.faixa .autor span {{ color: var(--cor-escura-texto-2); font-size: var(--t-nota); }}
.corpo {{ flex: 1; padding: var(--e-2) 18mm var(--e-1); display: flex; flex-direction: column; gap: var(--e-2); }}
.passo h2 {{ font-size: var(--t-cab); font-weight: 700; letter-spacing: -0.01em; line-height: 1.1;
            display: flex; align-items: baseline; gap: var(--e-2); }}
.passo h2 .n {{ color: var(--cor-marca); }}
.passo .lead {{ color: var(--cor-texto-2); margin-top: 2mm; max-width: 300mm; }}
.implantes {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: var(--e-2); margin-top: var(--e-2); }}
.implante {{ display: flex; flex-direction: column; }}
.implante .img {{ height: 62mm; display: flex; align-items: flex-end; justify-content: center; }}
.implante img {{ max-width: 100%; max-height: 100%; }}
.implante b {{ margin-top: var(--e-1); font-size: var(--t-texto); }}
.implante span {{ color: var(--cor-texto-2); font-size: var(--t-nota); line-height: 1.3; }}
.frase {{ background: var(--frase-fundo); border-radius: var(--raio); padding: var(--e-2) var(--e-3);
         font-size: var(--t-frase); font-weight: 700; line-height: 1.12; letter-spacing: -0.015em; }}
.frase em {{ font-style: normal; color: var(--cor-destaque); }}
.dois {{ display: grid; grid-template-columns: 0.82fr 1.18fr; gap: var(--e-3); }}
.funil {{ margin-top: var(--e-2); display: flex; flex-direction: column; gap: 3mm; }}
.degrau {{ display: grid; grid-template-columns: var(--funil-w) 1fr; align-items: center; gap: var(--e-2); }}
.degrau .barra {{ height: 14mm; border-radius: 2mm; justify-self: center; }}
.degrau b {{ display: block; font-size: var(--t-cab); line-height: 1; letter-spacing: -0.01em; }}
.degrau span {{ color: var(--cor-texto-2); font-size: var(--t-nota); line-height: 1.25; display: block; margin-top: 1.5mm; }}
.metodo {{ margin-top: var(--e-2); background: var(--cartao-fundo); border-radius: var(--raio); padding: var(--e-2);
          font-size: var(--t-nota); line-height: 1.35; color: var(--cor-texto-2); }}
.metodo b {{ color: var(--cor-texto); }}
.espectro {{ margin-top: var(--e-2); display: flex; flex-direction: column; gap: 3mm; }}
.linha {{ display: grid; grid-template-columns: 56mm 1fr; gap: var(--e-2); align-items: center;
         background: var(--cartao-fundo); border-radius: var(--raio); padding: 2.5mm var(--e-2); }}
.chip {{ color: var(--cor-fundo); font-weight: 700; font-size: var(--t-nota); border-radius: 99mm; padding: 2mm 3mm;
        text-align: center; }}
.chip.solida {{ background: var(--chip-solida); }} .chip.fragil {{ background: var(--chip-fragil); }}
.chip.indicacao {{ background: var(--chip-indicacao); }}
.linha b {{ font-size: var(--t-texto); }} .linha .mat {{ color: var(--cor-marca-texto); font-weight: 700; }}
.linha span {{ display: block; color: var(--cor-texto-2); font-size: var(--t-nota); line-height: 1.25; }}
.rodape {{ border-top: 0.4mm solid var(--cor-linha); margin: 0 18mm; padding: var(--e-2) 0 10mm;
          display: grid; grid-template-columns: 1fr 1.25fr auto; gap: var(--e-3); font-size: var(--t-nota);
          line-height: 1.32; color: var(--cor-texto-2); }}
.rodape h3 {{ font-size: var(--t-nota); color: var(--cor-texto); font-weight: 700; margin-bottom: 1.5mm; }}
.rodape ol {{ padding-left: 5mm; }} .rodape li {{ margin-bottom: 1mm; }}
.aviso {{ display: inline-block; margin-top: 2.5mm; background: var(--cor-destaque-fundo); color: var(--cor-texto);
         font-weight: 700; border-radius: 2mm; padding: 1.5mm 3mm; }}
.qr {{ width: 46mm; text-align: center; }}
.qr .caixa {{ width: 46mm; height: 46mm; border: 0.5mm dashed var(--cor-linha); border-radius: 2mm; display: flex;
            align-items: center; justify-content: center; color: var(--cor-texto-2); padding: 3mm; }}
.qr img {{ width: 46mm; height: 46mm; }}
"""


def _cabecalho(n, logo_branco: Path) -> str:
    return f"""<header class="faixa">
  <div class="topo"><img src="{logo_branco.as_uri()}" alt="Universidade Lusófona">
    <img src="{(ab.ap.LOGOS / 'fe.png').as_uri()}" alt="Faculdade de Engenharia">
    <span class="kicker">{html.escape(ab.CABECALHO)}</span></div>
  <div><h1>Qual é o biomaterial ideal?</h1>
    <p class="sub">Escolher o material de cinco implantes com dados verificados</p></div>
  <div class="autor"><b>{ab.AUTOR}</b><span>Orientador: {ab.ORIENTADOR}</span></div>
</header>"""


def _passo1(imgs: dict[str, Path]) -> str:
    cols = "".join(
        f'<div class="implante"><div class="img">'
        f'<img src="{imgs[c].as_uri()}" alt="{nome}"></div><b>{nome}</b><span>{desafio}</span></div>'
        for c, nome, desafio in ab.DISPOSITIVOS)
    return f"""<section class="passo"><h2><span class="n">1</span>Que material pôr dentro do corpo?</h2>
  <div class="implantes">{cols}</div>
  <p class="lead" style="font-size:var(--t-nota);text-align:right">Ilustrações feitas para o trabalho</p></section>"""


def _passo2(n, fu) -> str:
    ns = [d[0] for d in degraus_funil(fu)]
    ws = larguras_funil(ns)
    cores = ["var(--azul-200)", "var(--azul-300)", "var(--azul-500)", "var(--azul-700)"]
    degraus = "".join(
        f'<div class="degrau"><div class="barra" style="width:calc(var(--funil-w) * {w:.3f});background:{cor}"></div>'
        f'<div><b>{numero(v)}</b><span>{txt}</span></div></div>'
        for (v, txt), w, cor in zip(degraus_funil(fu), ws, cores))
    return f"""<section class="passo"><h2><span class="n">2</span>Como decidimos</h2>
  <div class="funil">{degraus}</div>
  <div class="metodo"><b>Três métodos</b> ordenam os candidatos e <b>{ab.mil(n.n_iter)} repetições</b> com os dados a
  variar testam se a escolha resiste. A nota máxima vai para o valor certo, não para o maior.</div></section>"""


def _passo3(n) -> str:
    classe = {"Sólida": "solida", "Empate técnico": "fragil", "Depende da leitura": "fragil", "Indicação": "indicacao",
              "Provável": "solida"}
    linhas = "".join(
        f'<div class="linha"><div class="chip {classe[nivel]}">{nivel}</div>'
        f'<div><b>{disp}: <span class="mat" style="display:inline">{html.escape(mat)}</span></b>'
        f'<span>{frase}</span></div></div>'
        for disp, mat, nivel, frase in ab.confianca(n, True))
    return f"""<section class="passo"><h2><span class="n">3</span>O que descobrimos</h2>
  <div class="espectro">{linhas}</div></section>"""


def _rodape(n, fu, qr_img: Path | None) -> str:
    refs = "".join(f"<li>{html.escape(r)}</li>" for r in REFERENCIAS)
    qr_html = (f'<img src="{qr_img.as_uri()}" alt="Código QR do repositório público">' if qr_img else
               '<div class="caixa">Código QR do repositório público (a criar)</div>')
    return f"""<footer class="rodape">
  <div><h3>Pormenores técnicos</h3>TOPSIS, WASPAS e VIKOR com critérios-alvo; consenso de Borda; Monte Carlo.
  Triagem com {fu['elementos']} elementos (ICH Q3D(R2), IARC) e {fu['normas']} normas ASTM; as propriedades do
  Materials Project são calculadas e só filtram. {ab.n_regras()} regras de perfis de doente, com fonte.
  <br><span class="aviso">{ab.AVISO}</span></div>
  <div><h3>Referências</h3><ol>{refs}</ol></div>
  <div class="qr">{qr_html}<p style="margin-top:2mm">Código, dados e aplicação</p></div>
</footer>"""


def html_poster(n=None, url: str | None = None) -> str:
    n = n or ab.ap.ler_numeros()
    fu = ab.funil()
    imgs = {c: ab.imagem_reduzida(ab.recortar_transparente(render(c), CACHE), 1400, CACHE) for c, _, _ in ab.DISPOSITIVOS}
    logo = ab.logotipo_branco(ab.ap.LOGOS / "lusofona.png", CACHE)
    corpo = (f'{_passo1(imgs)}<div class="frase">Não há um material ideal para tudo: há o melhor para cada implante, '
             f'e <em>uma medida de quanto confiar nele.</em></div>'
             f'<div class="dois">{_passo2(n, fu)}{_passo3(n)}</div>')
    return (f'<!doctype html><html lang="pt-PT"><head><meta charset="utf-8"><title>Poster</title>'
            f'<style>{_css(420, 594)}</style></head><body><div class="pagina">{_cabecalho(n, logo)}'
            f'<main class="corpo">{corpo}</main>{_rodape(n, fu, qr(url))}</div></body></html>')


# ---------------------------------------------------------------- impressão

def imprimir(html_txt: str, pdf: Path, chrome: Path = CHROME) -> Path:
    """Grava o HTML ao lado do PDF e imprime-o com o Chrome sem janela."""
    pdf.parent.mkdir(parents=True, exist_ok=True)
    h = pdf.with_suffix(".html")
    h.write_text(html_txt, encoding="utf-8")
    import tempfile
    pdf.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory() as perfil:  # perfil próprio: não colide com um Chrome já aberto
        subprocess.run([str(chrome), "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                        "--allow-file-access-from-files", f"--user-data-dir={perfil}", f"--print-to-pdf={pdf}",
                        h.as_uri()], check=True, capture_output=True, timeout=180)
        import time
        for _ in range(120):  # o Chrome pode devolver o controlo antes de acabar de escrever
            if pdf.exists() and pdf.stat().st_size > 0:
                time.sleep(1)
                break
            time.sleep(0.5)
    if not pdf.exists():
        raise RuntimeError(f"o Chrome não criou {pdf}")
    return pdf


def reduzir(pdf: Path, destino: Path, largura_mm: float = 297, altura_mm: float = 420) -> Path:
    """Reduz a primeira página para outro formato com a mesma proporção (vetorial; A2 para A3)."""
    import pymupdf
    pt = 72 / 25.4
    origem = pymupdf.open(pdf)
    novo = pymupdf.open()
    p = novo.new_page(width=largura_mm * pt, height=altura_mm * pt)
    p.show_pdf_page(p.rect, origem, 0)
    novo.save(destino)
    return destino


def paginas(pdf: Path) -> int:
    """Número de páginas do PDF: mais de uma quer dizer que o conteúdo não coube no formato."""
    import pymupdf
    return pymupdf.open(pdf).page_count


def previas(a2: Path, a3: Path, a4: Path, pasta: Path = PREVIA) -> list[Path]:
    """Poster inteiro (A2 a 40 ppp), recorte a 100 % do A3 (96 ppp, zona do título e do passo 1) e folheto."""
    import pymupdf
    pasta.mkdir(parents=True, exist_ok=True)
    saida = []
    d = pymupdf.open(a2)
    d[0].get_pixmap(dpi=40).save(pasta / "poster_inteiro.png")
    saida.append(pasta / "poster_inteiro.png")
    d = pymupdf.open(a3)
    r = d[0].rect
    clip = pymupdf.Rect(0, r.height * 0.13, r.width * 0.62, r.height * 0.42)
    d[0].get_pixmap(dpi=96, clip=clip).save(pasta / "recorte_A3_100.png")
    saida.append(pasta / "recorte_A3_100.png")
    d = pymupdf.open(a4)
    d[0].get_pixmap(dpi=80).save(pasta / "folheto.png")
    saida.append(pasta / "folheto.png")
    return saida


def main() -> None:
    a = argparse.ArgumentParser()
    a.add_argument("--url", default=None)
    args = a.parse_args()
    n = ab.ap.ler_numeros()
    a2 = imprimir(html_poster(n, args.url), POSTER / "poster_b_A2.pdf")
    a3 = reduzir(a2, POSTER / "poster_b_A3.pdf")
    a4 = reduzir(a2, POSTER / "folheto_b_A4.pdf", 210, 297)  # folheto: o poster reduzido a A4
    for p in (a2,):
        if paginas(p) != 1:
            print(f"AVISO: {p.name} tem {paginas(p)} páginas (o conteúdo não cabe)")
    for p in (a2, a3, a4, *previas(a2, a3, a4)):
        print(p.relative_to(RAIZ))


if __name__ == "__main__":
    main()
