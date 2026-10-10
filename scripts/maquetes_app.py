"""Arquivado a 6 out 2026 (não se usa; a aplicação passa a ser construída diretamente em Tauri).

Fase A da aplicação nativa: maquetes no estilo B, nos temas claro e escuro, em computador (1440 × 900) e
telemóvel (390 × 844). Ecrãs: Início, Doente (passos e resultado), Caso (stent), Robustez e Definições.

HTML renderizado pelo Chrome sem janela; os números vêm de results/ e do pacote. O exemplo do ecrã Doente usa a
regra H-OST de data/perfis_doente.csv (peso do módulo de Young multiplicado por 2 e renormalizado).
Saída: partilha\\amanha\\maquetes_app\\<ecra>_<computador|telemovel>_<claro|escuro>.png e uma folha
de contactos.
Uso: python scripts/maquetes_app.py
"""
from __future__ import annotations

import colorsys
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))
sys.path.insert(0, str(RAIZ / "scripts"))
import design_direcoes as dd  # noqa: E402
from ilustracoes import NOMES, svg_icone  # noqa: E402

from biomat_mcdm.io import build_problem  # noqa: E402
from biomat_mcdm.pipeline import consenso_borda, rank_all_methods  # noqa: E402
from biomat_mcdm.robustness import com_peso  # noqa: E402

SAIDA = Path(r"partilha\amanha\maquetes_app")
HTML = RAIZ / "design" / "arquivo" / "maquetes"
AVISO = "Ferramenta educativa de exploração de critérios. Não é um dispositivo médico e não substitui a decisão clínica."

TEMAS = {
    "claro": {"fundo": "#f4f6f9", "superficie": "#ffffff", "superficie2": "#eef2f6", "texto": "#0f1720",
              "texto2": "#55606b", "linha": "#dbe2e9", "acento": "#0595D1", "acento_texto": "#0477A8",
              "sobre_acento": "#ffffff", "quente": "#E8833A", "quente_fundo": "#fdf0e6", "lateral": "#0b1b2e",
              "lateral_texto": "#c9d6e2", "lateral_ativo": "#16304d"},
    "escuro": {"fundo": "#0b1b2e", "superficie": "#13263d", "superficie2": "#1a3150", "texto": "#e8eef4",
               "texto2": "#a7b6c4", "linha": "#2a4766", "acento": "#4FB8EA", "acento_texto": "#4FB8EA",
               "sobre_acento": "#0b1b2e", "quente": "#F2A35E", "quente_fundo": "#2e2a2a", "lateral": "#08141f",
               "lateral_texto": "#a7b6c4", "lateral_ativo": "#16304d"},
}


# --------------------------------------------------------------- cores
def _lum(h: str) -> float:
    c = [int(h.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contraste(a: str, b: str) -> float:
    """Razão de contraste WCAG entre duas cores."""
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def cor_material(cor: str, tema: str, minimo: float = 3.0) -> str:
    """Cor de um material no tema: a mesma tonalidade, mais clara no escuro até ter contraste ≥ 3:1 com a superfície."""
    if tema == "claro":
        return cor
    fundo = TEMAS["escuro"]["superficie"]
    r, g, b = (int(cor.lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4))
    h, l_, s = colorsys.rgb_to_hls(r, g, b)
    while True:
        out = "#%02x%02x%02x" % tuple(round(255 * v) for v in colorsys.hls_to_rgb(h, l_, s))
        if contraste(out, fundo) >= minimo or l_ >= 0.95:
            return out
        l_ = min(0.95, l_ + 0.02)


# --------------------------------------------------------------- números
def dados() -> dict:
    """Tudo o que as maquetes mostram, lido de results/ e do pacote."""
    stent = build_problem("Stent vascular", "A")
    haste = build_problem("Prótese da anca | Haste femoral", "A")
    j = haste.criteria.index("Módulo de Young")
    w0 = float(haste.weights[j])
    perfil = com_peso(haste, "Módulo de Young", 2 * w0 / (1 + w0))
    return {"casos": dd.numeros_espectro(), "mc": dd.mc_stent(), "dc": dd.delta_stent(),
            "stent": stent, "stent_rank": consenso_borda(rank_all_methods(stent)),
            "haste": haste, "haste_base": consenso_borda(rank_all_methods(haste)),
            "haste_perfil": consenso_borda(rank_all_methods(perfil)), "perfil": perfil, "j_modulo": j}


def pt(x: float, casas: int = 0) -> str:
    return dd.pt(x, casas)


CURTO = {**dd.CURTO, "Aço inox 316L": "316L", "Co-Cr-Mo forjado": "Co-Cr-Mo", "Ti-13Nb-13Zr": "Ti-13Nb-13Zr",
         "Co-Cr L605": "L605", "Co-Ni-Cr-Mo MP35N": "MP35N"}


def curto(m: str) -> str:
    return CURTO.get(m, m)


# --------------------------------------------------------------- ícones de navegação (traço, currentColor)
NAV_ICONES = {
    "inicio": '<path d="M4 11 L12 4 L20 11 V20 H14 V14 H10 V20 H4 Z"/>',
    "doente": '<circle cx="12" cy="8" r="4"/><path d="M4 21 C4 16 8 14 12 14 C16 14 20 16 20 21"/>',
    "casos": '<rect x="3" y="4" width="18" height="16" rx="3"/><path d="M7 15 V11 M12 15 V8 M17 15 V12"/>',
    "robustez": '<path d="M3 12 H7 L10 5 L14 19 L17 12 H21"/>',
    "fichas": '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 8 H15 M9 12 H15 M9 16 H13"/>',
    "gibson": '<path d="M4 4 C6 14 12 18 20 20"/><path d="M4 20 H20 M4 4 V20"/>',
    "definicoes": '<circle cx="12" cy="12" r="3"/><path d="M12 2 V5 M12 19 V22 M2 12 H5 M19 12 H22 M5 5 L7 7 M17 17 '
                  'L19 19 M5 19 L7 17 M17 7 L19 5"/>',
    "sobre": '<circle cx="12" cy="12" r="9"/><path d="M12 11 V17 M12 7.5 V8"/>',
    "lua": '<path d="M20 14 A8 8 0 1 1 10 4 A6.5 6.5 0 0 0 20 14 Z"/>',
    "sol": '<circle cx="12" cy="12" r="4"/><path d="M12 2 V4 M12 20 V22 M2 12 H4 M20 12 H22 M5 5 L6.5 6.5 M17.5 17.5 '
           'L19 19 M5 19 L6.5 17.5 M17.5 6.5 L19 5"/>',
    "mais": '<circle cx="5" cy="12" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="19" cy="12" r="1.5"/>',
    "exportar": '<path d="M12 3 V15 M7 10 L12 15 L17 10 M5 20 H19"/>',
    "info": '<circle cx="12" cy="12" r="9"/><path d="M12 11 V17 M12 7.5 V8"/>',
    "seta": '<path d="M9 6 L15 12 L9 18"/>',
}
NAV = [("inicio", "Início"), ("doente", "Doente"), ("casos", "Casos"), ("robustez", "Robustez"),
       ("fichas", "Fichas dos materiais"), ("gibson", "Gibson e Ashby"), ("definicoes", "Definições"),
       ("sobre", "Sobre")]
NAV_MOVEL = [("inicio", "Início"), ("doente", "Doente"), ("casos", "Casos"), ("robustez", "Robustez"),
             ("mais", "Mais")]


def ico(nome: str, tam: int = 22, traco: float = 1.8) -> str:
    return (f'<svg width="{tam}" height="{tam}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="{traco}" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
            f'{NAV_ICONES[nome]}</svg>')


# --------------------------------------------------------------- CSS
def css(t: dict, movel: bool) -> str:
    base = dd.css_base().replace("background:#fff;", "")
    v = ";".join(f"--{k.replace('_', '-')}:{c}" for k, c in t.items() if isinstance(c, str))
    return base + f""":root{{{v}}}
body{{background:var(--fundo);color:var(--texto);font-size:{15 if movel else 16}px}}
.cartao{{background:var(--superficie);border:1px solid var(--linha);border-radius:16px;padding:{16 if movel else 24}px}}
.rot{{font-size:13px;color:var(--texto2);letter-spacing:.06em;text-transform:uppercase;font-weight:700}}
.t2{{color:var(--texto2)}}
.tit{{font-size:{24 if movel else 32}px;font-weight:700;line-height:1.15;letter-spacing:-.01em}}
.h3{{font-size:{17 if movel else 18}px;font-weight:700}}
.chip{{display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border-radius:999px;border:1px solid var(--linha);
 font-size:14px;background:var(--superficie)}}
.chip.on{{background:var(--acento);border-color:var(--acento);color:var(--sobre-acento);font-weight:700}}
.seg{{display:inline-flex;border:1px solid var(--linha);border-radius:12px;overflow:hidden;background:var(--superficie2)}}
.seg span{{padding:8px 14px;font-size:14px}}
.seg span.on{{background:var(--superficie);color:var(--acento-texto);font-weight:700;box-shadow:0 0 0 1px var(--linha)}}
.bt{{display:inline-flex;align-items:center;gap:8px;padding:10px 18px;border-radius:12px;font-weight:700;font-size:15px}}
.bt.pri{{background:var(--acento);color:var(--sobre-acento)}}
.bt.sec{{border:1px solid var(--linha);background:var(--superficie)}}
.aviso{{display:flex;gap:10px;align-items:flex-start;background:var(--quente-fundo);border:1px solid var(--quente);
 border-radius:12px;padding:10px 14px;font-size:14px;line-height:1.35}}
.campo{{border:1px solid var(--linha);border-radius:10px;padding:10px 12px;background:var(--superficie);font-size:15px}}
.interruptor{{width:44px;height:26px;border-radius:13px;background:var(--linha);position:relative;flex:none}}
.interruptor::after{{content:"";position:absolute;left:3px;top:3px;width:20px;height:20px;border-radius:50%;background:#fff}}
.interruptor.on{{background:var(--acento)}}
.interruptor.on::after{{left:21px}}
.link{{color:var(--acento-texto);font-weight:700}}
"""


def casca(corpo: str, ativo: str, titulo: str, t: dict, tema: str, movel: bool) -> str:
    """Moldura da aplicação: barra lateral (computador) ou barra de separadores (telemóvel), com o botão sol/lua."""
    lua_sol = ico("lua" if tema == "claro" else "sol", 20)
    botao_tema = (f'<div title="Mudar para o tema {"escuro" if tema == "claro" else "claro"}" style="width:40px;'
                  f'height:40px;border-radius:12px;border:1px solid var(--linha);display:flex;align-items:center;'
                  f'justify-content:center;background:var(--superficie)">{lua_sol}</div>')
    if movel:
        tabs = "".join(f'<div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:3px;font-size:11px;'
                       f'{"color:var(--acento-texto);font-weight:700" if k == ativo else "color:var(--texto2)"}">'
                       f'{ico(k, 22)}{n}</div>' for k, n in NAV_MOVEL)
        return f"""
<div style="display:flex;flex-direction:column;height:100%">
 <div style="height:56px;flex:none;display:flex;align-items:center;justify-content:space-between;padding:0 16px;
  background:var(--superficie);border-bottom:1px solid var(--linha)">
  <div style="font-weight:700;font-size:17px">{titulo}</div>{botao_tema}</div>
 <div style="flex:1;overflow:hidden;padding:16px;display:flex;flex-direction:column;gap:12px">{corpo}</div>
 <div style="height:68px;flex:none;display:flex;align-items:center;background:var(--superficie);
  border-top:1px solid var(--linha);padding-bottom:6px">{tabs}</div>
</div>"""
    itens = "".join(f'<div style="display:flex;align-items:center;gap:12px;padding:10px 14px;border-radius:10px;'
                    f'font-size:15px;{"background:var(--lateral-ativo);color:#fff;font-weight:700" if k == ativo else ""}">'
                    f'{ico(k, 20)}{n}</div>' for k, n in NAV)
    return f"""
<div style="display:flex;height:100%">
 <div style="width:248px;flex:none;background:var(--lateral);color:var(--lateral-texto);padding:20px 14px;
  display:flex;flex-direction:column;gap:4px">
  <div style="display:flex;align-items:center;gap:10px;padding:4px 8px 18px">{dd.logos(40, True)}</div>
  <div style="font-size:12px;letter-spacing:.08em;text-transform:uppercase;padding:0 14px 8px;color:#7f9ab0">Biomaterial Ideal</div>
  {itens}
  <div style="margin-top:auto;font-size:12px;color:#7f9ab0;padding:0 14px">Versão 1.0.0</div>
 </div>
 <div style="flex:1;display:flex;flex-direction:column;min-width:0">
  <div style="height:68px;flex:none;display:flex;align-items:center;justify-content:space-between;padding:0 32px;
   border-bottom:1px solid var(--linha);background:var(--superficie)">
   <div style="font-weight:700;font-size:18px">{titulo}</div>{botao_tema}</div>
  <div style="flex:1;overflow:hidden;padding:28px 32px;display:flex;flex-direction:column;gap:20px">{corpo}</div>
 </div>
</div>"""


# --------------------------------------------------------------- gráficos com as cores do tema
def espectro(d: dict, t: dict, largura: int) -> str:
    """Espectro de confiança (versão do poster) com as cores do tema."""
    guardar = {k: getattr(dd, k) for k in ("TEXTO", "CINZA", "LINHA", "AZUL_FE", "QUENTE")}
    dd.TEXTO, dd.CINZA, dd.LINHA, dd.AZUL_FE, dd.QUENTE = t["texto"], t["texto2"], t["linha"], t["acento"], t["quente"]
    try:
        s = dd.svg_espectro(d["casos"], largura, 15)
    finally:
        for k, v in guardar.items():
            setattr(dd, k, v)
    return s.replace('fill="#fff"', f'fill="{t["superficie"]}"').replace('stroke="#fff"', f'stroke="{t["superficie"]}"')


def espectro_compacto(d: dict, t: dict, largura: int) -> str:
    """Eixo do ΔC com um ponto numerado por caso (telemóvel); a lista por baixo dá os nomes."""
    m, y = 18, 34
    x = lambda dc: m + (largura - 2 * m) * (1 - min(dc, dd.DC_MAX) / dd.DC_MAX)  # noqa: E731
    p = [f'<svg viewBox="0 0 {largura} 78" width="{largura}" height="78" font-family="Inter">',
         f'<line x1="{x(dd.LIMIAR):.1f}" y1="{y - 18}" x2="{x(dd.LIMIAR):.1f}" y2="{y + 10}" stroke="{t["quente"]}" '
         f'stroke-width="2" stroke-dasharray="4 4"/>',
         f'<line x1="{m}" y1="{y}" x2="{largura - m}" y2="{y}" stroke="{t["texto2"]}" stroke-width="2"/>']
    for v in (0.2, 0.1, 0.0):
        p.append(f'<text x="{x(v):.1f}" y="{y + 26}" font-size="12" fill="{t["texto2"]}" text-anchor="middle">'
                 f'{pt(v, 1) if v else "0"}</text>')
    p.append(f'<text x="{largura / 2}" y="{y + 44}" font-size="12" fill="{t["texto2"]}" text-anchor="middle">'
             f'margem entre o 1.º e o 2.º (ΔC, TOPSIS)</text>')
    for i, c in enumerate(d["casos"], 1):
        xc = x(c["dc"])
        yy = y - 14 if i % 2 else y + 0
        estilo = (f'fill="{t["superficie"]}" stroke="{t["texto2"]}" stroke-dasharray="3 2.5"' if c["semi"] else
                  f'fill="{t["acento"]}" stroke="{t["superficie"]}"')
        p.append(f'<circle cx="{xc:.1f}" cy="{y}" r="10" {estilo} stroke-width="2.5"/>'
                 f'<text x="{xc:.1f}" y="{y + 4}" font-size="11" font-weight="700" text-anchor="middle" '
                 f'fill="{t["texto2"] if c["semi"] else t["sobre_acento"]}">{i}</text>')
        del yy
    p.append("</svg>")
    return "".join(p)


def barras_mc(d: dict, t: dict, tema: str, largura: int, fs: int, h: int, gap: int) -> str:
    """% de vitórias por método no Monte Carlo do stent, com rótulo direto em cada segmento."""
    mats = ["Pt-Cr", "Co-Cr L605", "Co-Ni-Cr-Mo MP35N"]
    x0 = fs * 4.6
    w = largura - x0 - fs * 2.6
    y0 = fs * 2.0
    alt = int(y0 + 3 * h + 2 * gap + 2)
    p = [f'<svg viewBox="0 0 {largura} {alt}" width="{largura}" height="{alt}" font-family="Inter">']
    xl = 0.0
    for mat in mats:
        c = cor_material(dd.COR["Stent"][mat], tema)
        p.append(f'<rect x="{xl}" y="{fs * 0.2:.1f}" width="{fs * 0.85:.1f}" height="{fs * 0.85:.1f}" rx="3" fill="{c}"/>'
                 f'<text x="{xl + fs * 1.2:.1f}" y="{fs * 0.95:.1f}" font-size="{fs}" font-weight="700" '
                 f'fill="{t["texto"]}">{curto(mat)}</text>')
        xl += fs * 1.2 + len(curto(mat)) * fs * 0.62 + fs * 1.2
    for k, met in enumerate(("TOPSIS", "WASPAS", "VIKOR")):
        y = y0 + k * (h + gap)
        p.append(f'<text x="{x0 - 10}" y="{y + h / 2 + fs * 0.36:.1f}" font-size="{fs}" fill="{t["texto2"]}" '
                 f'text-anchor="end">{met}</text>')
        esq = 0.0
        for mat in mats:
            v = float(d["mc"][met].get(mat, 0))
            c = cor_material(dd.COR["Stent"][mat], tema)
            xa, wa = x0 + w * esq / 100, w * v / 100
            p.append(f'<rect x="{xa:.1f}" y="{y}" width="{wa:.1f}" height="{h}" fill="{c}"/>')
            rot = f"{pt(v)} %"
            dentro = "#ffffff" if contraste("#ffffff", c) >= 3 else "#0b1b2e"
            if wa >= len(rot) * fs * 0.62 + 8:
                p.append(f'<text x="{xa + wa / 2:.1f}" y="{y + h / 2 + fs * 0.36:.1f}" font-size="{fs}" font-weight="700" '
                         f'fill="{dentro}" text-anchor="middle">{rot}</text>')
            else:
                xr = x0 + w + 10
                p.append(f'<path d="M{xa + wa / 2:.1f} {y + h / 2} H{xr - 4}" stroke="{t["texto"]}" stroke-width="1.3"/>'
                         f'<text x="{xr}" y="{y + h / 2 + fs * 0.36:.1f}" font-size="{fs}" font-weight="700" '
                         f'fill="{t["texto"]}">{rot}</text>')
            esq += v
    p.append("</svg>")
    return "".join(p)


def barras_ranking(nomes: list[str], valores: list[float], cores: list[str], t: dict, largura: int, fs: int,
                   h: int, casas: int = 3, maximo: float = 1.0, destaque: int = 0) -> str:
    """Barras horizontais ordenadas, com nome à esquerda e valor à direita."""
    x0 = fs * 6.2
    w = largura - x0 - fs * 3.6
    alt = int(len(nomes) * (h + 10))
    p = [f'<svg viewBox="0 0 {largura} {alt}" width="{largura}" height="{alt}" font-family="Inter">']
    for i, (n, v, c) in enumerate(zip(nomes, valores, cores)):
        y = i * (h + 10)
        peso = 700 if i == destaque else 400
        p.append(f'<text x="{x0 - 10}" y="{y + h / 2 + fs * 0.36:.1f}" font-size="{fs}" font-weight="{peso}" '
                 f'fill="{t["texto"]}" text-anchor="end">{n}</text>'
                 f'<rect x="{x0}" y="{y}" width="{w:.1f}" height="{h}" rx="{h / 2}" fill="{t["superficie2"]}"/>'
                 f'<rect x="{x0}" y="{y}" width="{max(w * v / maximo, h):.1f}" height="{h}" rx="{h / 2}" fill="{c}"/>'
                 f'<text x="{x0 + w + 10}" y="{y + h / 2 + fs * 0.36:.1f}" font-size="{fs}" font-weight="{peso}" '
                 f'fill="{t["texto"]}">{pt(v, casas)}</text>')
    p.append("</svg>")
    return "".join(p)


# --------------------------------------------------------------- ecrãs
def ecra_inicio(d: dict, t: dict, tema: str, movel: bool) -> tuple[str, str, str]:
    casos = d["casos"]
    if movel:
        linhas = "".join(
            f'<div style="display:flex;gap:12px;align-items:center;padding:10px 0;border-top:1px solid var(--linha)">'
            f'<div style="width:24px;height:24px;border-radius:50%;flex:none;display:flex;align-items:center;'
            f'justify-content:center;font-size:12px;font-weight:700;'
            f'{"border:2px dashed var(--texto2);color:var(--texto2)" if c["semi"] else "background:var(--acento);color:var(--sobre-acento)"}">'
            f'{i}</div><div style="color:var(--texto);--fundo:var(--superficie)">{svg_icone(c["chave"], 40, 2.6)}</div>'
            f'<div style="flex:1;min-width:0"><div style="font-weight:700;font-size:15px">{NOMES[c["chave"]]}</div>'
            f'<div class="t2" style="font-size:13px">{curto(c["vencedor"])} · ΔC {pt(c["dc"], 3)}'
            f'{" · indicação" if c["semi"] else ""}</div></div></div>'
            for i, c in enumerate(casos, 1))
        corpo = f"""
<div class="tit">Cinco dispositivos, cinco graus de confiança</div>
<div class="cartao" style="padding:12px 14px">
 <div class="rot" style="margin-bottom:6px">Espectro de confiança</div>
 {espectro_compacto(d, t, 330)}
 <div style="margin-top:6px">{linhas}</div>
</div>"""
        return corpo, "inicio", "Biomaterial Ideal"
    cartoes = "".join(
        f'<div class="cartao" style="padding:14px 16px;display:flex;gap:12px;align-items:center;--fundo:var(--superficie)">'
        f'<div style="color:var(--texto);flex:none">{svg_icone(c["chave"], 48, 2.4)}</div>'
        f'<div style="flex:1;min-width:0"><div style="font-weight:700;font-size:15px">{NOMES[c["chave"]]}</div>'
        f'<div style="font-size:14px">{curto(c["vencedor"])}</div>'
        f'<div class="t2" style="font-size:13px">ΔC {pt(c["dc"], 3)}{" · indicação" if c["semi"] else ""}</div></div>'
        f'<div style="color:var(--acento-texto);flex:none">{ico("seta", 18)}</div></div>' for c in casos)
    corpo = f"""
<div style="display:flex;justify-content:space-between;align-items:flex-end">
 <div><div class="rot">Qual é o biomaterial ideal?</div>
 <div class="tit" style="margin-top:6px">Cinco dispositivos, cinco graus de confiança</div></div>
 <div class="bt pri">{ico("doente", 18)} Criar um perfil de doente</div></div>
<div class="cartao" style="padding:18px 24px 6px;--fundo:var(--superficie)">
 <div style="display:flex;justify-content:space-between"><div class="h3">Espectro de confiança</div>
 <div class="t2" style="font-size:14px">posição: ΔC do TOPSIS no cenário A</div></div>
 {espectro(d, t, 1060)}
</div>
<div style="display:grid;grid-template-columns:repeat(5,1fr);gap:16px">{cartoes}</div>"""
    return corpo, "inicio", "Início"


PASSOS_DOENTE = ["Dispositivo", "Dados gerais", "Específicos", "Problema", "Resultado"]


def passos(atual: int, movel: bool) -> str:
    out = []
    for i, n in enumerate(PASSOS_DOENTE, 1):
        if i < atual:
            circ = "background:var(--acento);color:var(--sobre-acento)"
        elif i == atual:
            circ = "border:2px solid var(--acento);color:var(--acento-texto)"
        else:
            circ = "border:2px solid var(--linha);color:var(--texto2)"
        rot = "" if movel and i != atual else (f'<span style="font-size:14px;{"font-weight:700" if i == atual else ""};'
                                               f'{"" if i <= atual else "color:var(--texto2)"}">{n}</span>')
        out.append(f'<div style="display:flex;align-items:center;gap:8px;flex:none"><div style="width:28px;height:28px;'
                   f'border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:13px;'
                   f'font-weight:700;{circ}">{"✓" if i < atual else i}</div>{rot}</div>')
        if i < len(PASSOS_DOENTE):
            out.append('<div style="flex:1;height:2px;background:var(--linha);min-width:8px"></div>')
    return f'<div style="display:flex;align-items:center;gap:8px">{"".join(out)}</div>'


EXEMPLOS = [("H1", "jovem ativo"), ("H2", "idosa com osteoporose"), ("H3", "IMC 38"), ("S1", "alergia ao níquel"),
            ("D1", "gengiva fina"), ("D2", "bruxismo")]


def ecra_doente_passos(d: dict, t: dict, tema: str, movel: bool) -> tuple[str, str, str]:
    chips = "".join(f'<span class="chip{" on" if k == "H2" else ""}"><b>{k}</b> {n}</span>' for k, n in EXEMPLOS)
    alergias = "".join(f'<span class="chip">{a}</span>' for a in ("níquel", "cobalto ou crómio", "titânio"))

    def campo(rot, conteudo):
        return f'<div><div class="t2" style="font-size:13px;margin-bottom:6px">{rot}</div>{conteudo}</div>'

    seg = lambda ops, on: '<div class="seg">' + "".join(  # noqa: E731
        f'<span class="{"on" if o == on else ""}">{o}</span>' for o in ops) + "</div>"
    tog = lambda rot, on: (f'<div style="display:flex;align-items:center;justify-content:space-between;gap:12px;'  # noqa: E731
                           f'padding:10px 0;border-top:1px solid var(--linha)"><span>{rot}</span>'
                           f'<div class="interruptor{" on" if on else ""}"></div></div>')
    campos = [campo("Idade", '<div class="campo">72 anos</div>'), campo("Sexo", seg(["Feminino", "Masculino"], "Feminino")),
              campo("IMC", '<div class="campo">27 kg/m²</div>'),
              campo("Atividade", seg(["Baixa", "Moderada", "Alta"], "Baixa"))]
    rodape = (f'<div class="t2" style="font-size:13px;display:flex;gap:8px;align-items:center">{ico("info", 16)} '
              f'Nada é guardado nem enviado. Não há campos de identificação.</div>')
    botoes = '<div style="display:flex;gap:12px;justify-content:flex-end"><div class="bt sec">Voltar</div><div class="bt pri">Seguinte</div></div>'
    if movel:
        corpo = f"""
{passos(2, True)}
<div><div class="h3">Dados gerais</div><div class="t2" style="font-size:13px">Haste femoral</div></div>
<div style="display:flex;gap:8px;overflow:hidden;flex-wrap:nowrap">{chips}</div>
<div class="cartao" style="display:flex;flex-direction:column;gap:12px">
 {"".join(campos)}
 <div>{tog("Tabagismo", False)}{tog("Diabetes", False)}</div>
 {campo("Alergias", '<div style="display:flex;gap:6px;flex-wrap:wrap">' + alergias + "</div>")}
</div>
{rodape}
<div style="display:flex;gap:10px"><div class="bt sec" style="flex:1;justify-content:center">Voltar</div><div class="bt pri" style="flex:1;justify-content:center">Seguinte</div></div>"""
        return corpo, "doente", "Doente"
    corpo = f"""
<div style="display:flex;justify-content:space-between;align-items:flex-end">
 <div><div class="rot">Perfil de doente · Haste femoral</div><div class="tit" style="margin-top:6px">Dados gerais</div></div>
 <div style="display:flex;gap:8px;align-items:center"><span class="t2" style="font-size:14px">Exemplos:</span>{chips}</div></div>
<div class="cartao" style="padding:18px 24px">{passos(2, False)}</div>
<div style="display:grid;grid-template-columns:2fr 1fr;gap:20px">
 <div class="cartao" style="display:grid;grid-template-columns:1fr 1fr;gap:20px 28px;align-content:start">
  {"".join(campos)}
  <div style="grid-column:span 2">{tog("Tabagismo", False)}{tog("Diabetes", False)}</div>
  <div style="grid-column:span 2">{campo("Alergias", '<div style="display:flex;gap:8px">' + alergias + "</div>")}</div>
 </div>
 <div class="cartao" style="display:flex;flex-direction:column;gap:12px">
  <div class="h3">Como se usa o perfil</div>
  <div style="font-size:15px;line-height:1.45">Cada dado ativa regras com fonte (pesos, alvos, exclusões ou leitura do
  problema). O resultado mostra o que mudou face ao caso de base e de onde vem cada alteração.</div>
  <div class="t2" style="font-size:14px">Passo seguinte: dados da haste (osteoporose, qualidade óssea).</div>
 </div>
</div>
{rodape}
{botoes}"""
    return corpo, "doente", "Doente"


def _lista_rank(df, col_pos: str, base, t: dict, compacto: bool) -> str:
    linhas = []
    for _, r in df.sort_values(col_pos).iterrows():
        p_base = int(base.set_index("material").loc[r["material"], col_pos])
        dif = p_base - int(r[col_pos])
        seta = (f'<span style="color:var(--acento-texto);font-weight:700">▲{dif}</span>' if dif > 0 else
                f'<span style="color:var(--quente);font-weight:700">▼{-dif}</span>' if dif < 0 else
                '<span class="t2">=</span>')
        linhas.append(f'<div style="display:flex;justify-content:space-between;gap:8px;padding:{5 if compacto else 7}px 0;'
                      f'border-top:1px solid var(--linha);font-size:{14 if compacto else 15}px">'
                      f'<span><b>{int(r[col_pos])}.</b> {curto(r["material"])}</span>{seta}</div>')
    return "".join(linhas)


def ecra_doente_resultado(d: dict, t: dict, tema: str, movel: bool) -> tuple[str, str, str]:
    base, perf = d["haste_base"], d["haste_perfil"]
    h, q, j = d["haste"], d["perfil"], d["j_modulo"]
    vence = perf.sort_values("pos_Borda")["material"].iloc[0]
    aviso = f'<div class="aviso">{ico("info", 18)}<span>{AVISO}</span></div>'
    mudou = (f'<div style="display:flex;justify-content:space-between;align-items:center;gap:12px;padding:10px 0;'
             f'border-top:1px solid var(--linha)"><div><div style="font-weight:700">Módulo de Young: peso '
             f'{pt(h.weights[j], 2)} → {pt(q.weights[j], 2)}</div><div class="t2" style="font-size:14px">Osteoporose · '
             f'regra H-OST · ×2 e renormalizado · Sychterz e Engh (1996)</div></div>'
             f'<div class="link" style="font-size:14px;display:flex;align-items:center;flex:none">Fonte {ico("seta", 16)}</div></div>'
             f'<div style="padding:10px 0;border-top:1px solid var(--linha)"><div style="font-weight:700">Restantes '
             f'critérios: peso × {pt((1 - q.weights[j]) / (1 - h.weights[j]), 2)}</div><div class="t2" '
             f'style="font-size:14px">Renormalização (soma dos pesos = 1)</div></div>')
    metodos = [("TOPSIS", "pos_TOPSIS"), ("WASPAS", "pos_WASPAS"), ("VIKOR", "pos_VIKOR"), ("Consenso", "pos_Borda")]
    if movel:
        corpo = f"""
{passos(5, True)}
<div><div class="rot">Haste femoral · perfil H2</div>
<div style="font-size:22px;font-weight:700;margin-top:4px">{curto(vence)} mantém o 1.º lugar</div></div>
{aviso}
<div class="cartao" style="padding:12px 14px"><div style="display:flex;justify-content:space-between">
 <div class="h3">Consenso</div><div class="seg"><span class="on">Perfil</span><span>Base</span></div></div>
 {_lista_rank(perf, "pos_Borda", base, t, True)}</div>
<div class="cartao" style="padding:12px 14px"><div class="h3">O que mudou face ao caso de base</div>{mudou}</div>
<div style="display:flex;gap:10px"><div class="bt sec" style="flex:1;justify-content:center">Comparar</div>
<div class="bt pri" style="flex:1;justify-content:center">{ico("exportar", 18)} Exportar</div></div>"""
        return corpo, "doente", "Resultado"
    colunas = "".join(f'<div class="cartao" style="padding:16px 18px"><div class="h3" style="margin-bottom:4px">{n}</div>'
                      f'{_lista_rank(perf, c, base, t, False)}</div>' for n, c in metodos)
    corpo = f"""
<div style="display:flex;justify-content:space-between;align-items:flex-end">
 <div><div class="rot">Haste femoral · perfil H2: idosa com osteoporose</div>
 <div class="tit" style="margin-top:6px">{curto(vence)} mantém o 1.º lugar; o Ti-13Nb-13Zr sobe</div></div>
 <div style="display:flex;gap:12px"><div class="bt sec">Comparar com o caso de base</div>
 <div class="bt pri">{ico("exportar", 18)} Exportar</div></div></div>
{aviso}
<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:16px">{colunas}</div>
<div class="cartao" style="padding:16px 24px"><div class="h3">O que mudou face ao caso de base</div>{mudou}</div>
<div class="t2" style="font-size:13px">▲ / ▼: posições ganhas ou perdidas face ao caso de base (cenário A).</div>"""
    return corpo, "doente", "Doente"


def ecra_caso(d: dict, t: dict, tema: str, movel: bool) -> tuple[str, str, str]:
    r = d["stent_rank"].sort_values("C_TOPSIS", ascending=False)
    nomes = [curto(m) for m in r["material"]]
    cores = [cor_material(dd.COR["Stent"].get(m, "#999999"), tema) for m in r["material"]]
    p = d["stent"]
    crit_curto = {"Índice material de recuo elástico σy/E (proxy)": "Recuo elástico (σy/E)",
                  "Espessura típica de strut": "Espessura de strut", "Alongamento na rotura": "Alongamento",
                  "Resistência à tração": "Resistência à tração", "Módulo de Young": "Módulo de Young",
                  "Radiopacidade (ordinal 1-5)": "Radiopacidade", "Compatibilidade com RM (ordinal 1-5)": "RM",
                  "Compatibilidade com esterilização (ordinal 1-5)": "Esterilização",
                  "Custo relativo de material e fabrico (1-5, 5 = mais caro)": "Custo",
                  "Fabricabilidade (ordinal 1-5)": "Fabricabilidade"}
    dca = d["dc"][0][0]
    rob_stent = next(c for c in d["casos"] if c["chave"] == "stent")["robustez"][0]
    titulo = "O Pt-Cr ganha mais vezes, mas a margem sobre o L605 é mínima"

    def cursor(nome, w, largura):
        return (f'<div style="display:grid;grid-template-columns:{largura}px 1fr 44px;align-items:center;gap:10px;'
                f'font-size:14px;padding:5px 0"><span>{nome}</span><div style="height:6px;border-radius:3px;'
                f'background:var(--superficie2);position:relative"><div style="position:absolute;left:0;top:0;bottom:0;'
                f'width:{w / 0.4 * 100:.0f}%;background:var(--acento);border-radius:3px"></div><div style="position:absolute;'
                f'left:calc({w / 0.4 * 100:.0f}% - 8px);top:-5px;width:16px;height:16px;border-radius:50%;'
                f'background:var(--superficie);border:2px solid var(--acento)"></div></div>'
                f'<span style="text-align:right;font-weight:700">{pt(w, 2)}</span></div>')
    pesos = "".join(cursor(crit_curto.get(c, c), w, 150 if not movel else 110) for c, w in zip(p.criteria, p.weights))
    tabs = '<div class="seg"><span class="on">TOPSIS</span><span>WASPAS</span><span>VIKOR</span></div>'
    cen = '<div class="seg"><span class="on">Cenário A</span><span>Cenário B</span></div>'
    if movel:
        corpo = f"""
<div><div class="rot">Stent coronário</div><div style="font-size:21px;font-weight:700;margin-top:4px;line-height:1.2">{titulo}</div></div>
<div style="display:flex;gap:8px">{tabs}</div>
<div class="cartao" style="padding:14px">
 {barras_ranking(nomes, list(r["C_TOPSIS"]), cores, t, 326, 14, 22)}
 <div class="t2" style="font-size:13px;margin-top:4px">C do TOPSIS · ΔC = {pt(dca, 3)} (empate se &lt; 0,01)</div></div>
<div class="cartao" style="padding:12px 14px"><div class="h3" style="margin-bottom:4px">Pesos</div>{"".join(cursor(crit_curto.get(c, c), w, 110) for c, w in list(zip(p.criteria, p.weights))[:5])}
 <div class="t2" style="font-size:13px;margin-top:4px">+ {len(p.criteria) - 5} critérios</div></div>"""
        return corpo, "casos", "Stent coronário"
    corpo = f"""
<div style="display:flex;justify-content:space-between;align-items:flex-end;gap:24px">
 <div><div class="rot">Stent coronário</div><div class="tit" style="margin-top:6px">{titulo}</div></div>
 <div style="display:flex;gap:12px;flex:none">{cen}<div class="bt sec">{ico("exportar", 18)} Exportar</div></div></div>
<div style="display:grid;grid-template-columns:1.35fr 1fr;gap:20px">
 <div class="cartao" style="display:flex;flex-direction:column;gap:14px">
  <div style="display:flex;justify-content:space-between;align-items:center">{tabs}
   <span class="t2" style="font-size:14px;display:flex;align-items:center;gap:6px">O que é o TOPSIS? {ico("info", 16)}</span></div>
  {barras_ranking(nomes, list(r["C_TOPSIS"]), cores, t, 600, 16, 30)}
  <div style="display:flex;gap:16px">
   <div style="flex:1;background:var(--superficie2);border-radius:12px;padding:12px 16px"><div class="t2" style="font-size:13px">ΔC (1.º − 2.º)</div>
    <div style="font-size:28px;font-weight:700;color:var(--acento-texto)">{pt(dca, 3)}</div></div>
   <div style="flex:2;background:var(--superficie2);border-radius:12px;padding:12px 16px;font-size:14px;line-height:1.4">
    Margem acima do limiar de empate (0,01), mas pequena: no Monte Carlo o {curto(r["material"].iloc[0])} ganha
    {rob_stent} das vezes.</div></div>
 </div>
 <div class="cartao"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
  <div class="h3">Pesos dos critérios</div><span class="t2" style="font-size:13px">soma = 1</span></div>{pesos}</div>
</div>"""
    return corpo, "casos", "Casos"


def ecra_robustez(d: dict, t: dict, tema: str, movel: bool) -> tuple[str, str, str]:
    (dca, va), (dcb, vb) = d["dc"]
    progresso = (f'<div style="display:flex;align-items:center;gap:14px"><div style="flex:1;height:8px;border-radius:4px;'
                 f'background:var(--acento)"></div><span style="font-size:14px;font-weight:700">10 000 / 10 000</span>'
                 f'<div class="bt sec" style="padding:8px 14px">Correr de novo</div></div>')
    cartoes = (f'<div style="flex:1;background:var(--superficie2);border-radius:12px;padding:12px 16px"><div class="t2" '
               f'style="font-size:13px">ΔC no cenário A</div><div style="font-size:28px;font-weight:700;'
               f'color:var(--acento-texto)">{pt(dca, 3)}</div><div style="font-size:14px">{curto(va)} à frente</div></div>'
               f'<div style="flex:1;background:var(--quente-fundo);border-radius:12px;padding:12px 16px"><div class="t2" '
               f'style="font-size:13px">ΔC no cenário B</div><div style="font-size:28px;font-weight:700;'
               f'color:var(--quente)">{pt(dcb, 3)}</div><div style="font-size:14px">empate: ΔC &lt; 0,01</div></div>')
    tipo = '<div class="seg"><span class="on">Propriedades</span><span>Pesos</span></div>'
    if movel:
        corpo = f"""
<div><div class="rot">Robustez · stent coronário</div><div style="font-size:21px;font-weight:700;margin-top:4px;line-height:1.2">Quem ganha quando os dados variam?</div></div>
{tipo}
<div class="cartao" style="padding:14px">{barras_mc(d, t, tema, 326, 13, 30, 12)}
 <div class="t2" style="font-size:13px;margin-top:6px">% de vitórias em 10 000 iterações (cenário A)</div></div>
<div class="cartao" style="padding:14px">{progresso.replace("Correr de novo", "De novo")}</div>
<div style="display:flex;gap:10px">{cartoes}</div>"""
        return corpo, "robustez", "Robustez"
    corpo = f"""
<div style="display:flex;justify-content:space-between;align-items:flex-end">
 <div><div class="rot">Robustez · stent coronário</div><div class="tit" style="margin-top:6px">Quem ganha quando os dados variam?</div></div>
 <div style="display:flex;gap:12px">{tipo}<div class="seg"><span class="on">Stent</span><span>Haste</span><span>Scaffold</span></div></div></div>
<div style="display:grid;grid-template-columns:1.5fr 1fr;gap:20px">
 <div class="cartao" style="display:flex;flex-direction:column;gap:16px">
  <div class="h3">% de vitórias em 10 000 iterações (cenário A)</div>
  {barras_mc(d, t, tema, 640, 16, 54, 22)}
  {progresso}
 </div>
 <div style="display:flex;flex-direction:column;gap:20px">
  <div class="cartao" style="display:flex;gap:16px">{cartoes}</div>
  <div class="cartao" style="font-size:15px;line-height:1.45"><div class="h3" style="margin-bottom:6px">Como ler</div>
   Cada iteração sorteia as propriedades dentro dos intervalos da base de dados (±{pt(100 * dd.an.incerteza())} % nos
   valores únicos) e volta a
   ordenar os materiais. Uma frequência alta não é uma probabilidade clínica.</div>
 </div>
</div>"""
    return corpo, "robustez", "Robustez"


def ecra_definicoes(d: dict, t: dict, tema: str, movel: bool) -> tuple[str, str, str]:
    def linha(rot, desc, ctrl):
        return (f'<div style="display:flex;justify-content:space-between;align-items:center;gap:16px;padding:14px 0;'
                f'border-top:1px solid var(--linha)"><div><div style="font-weight:700">{rot}</div>'
                f'<div class="t2" style="font-size:13px">{desc}</div></div><div style="flex:none">{ctrl}</div></div>')

    seg = lambda ops, on: '<div class="seg">' + "".join(  # noqa: E731
        f'<span class="{"on" if o == on else ""}">{o}</span>' for o in ops) + "</div>"
    tema_on = "Claro" if tema == "claro" else "Escuro"
    itens = [
        linha("Tema", "Guardado entre sessões", seg(["Sistema", "Claro", "Escuro"], tema_on)),
        linha("Modo apresentação", "Letra e gráficos maiores, para projetar", '<div class="interruptor"></div>'),
        linha("Tamanho da letra", "", seg(["Normal", "Grande", "Muito grande"] if not movel else ["N", "G", "MG"], "Normal")),
        linha("Movimento", "Por omissão, o do sistema", seg(["Sistema", "Completo", "Reduzido"], "Sistema")),
        linha("Idioma", "Inglês em preparação", seg(["Português"], "Português")),
    ]
    sobre = (f'<div class="cartao" style="padding:{14 if movel else 20}px"><div class="h3">Sobre</div>'
             f'<div style="font-size:14px;line-height:1.5;margin-top:6px">Biomaterial Ideal 1.0.0 · {dd.AUTOR}<br>'
             f'Universidade Lusófona, Faculdade de Engenharia · Próteses e Órgãos Artificiais</div>'
             f'<div class="aviso" style="margin-top:10px">{ico("info", 18)}<span>{AVISO}</span></div></div>')
    if movel:
        corpo = f'<div class="cartao" style="padding:0 14px">{"".join(itens)}</div>{sobre}'
        return corpo, "mais", "Definições"
    corpo = f"""
<div><div class="rot">Aplicação</div><div class="tit" style="margin-top:6px">Definições</div></div>
<div style="display:grid;grid-template-columns:1.4fr 1fr;gap:20px;align-items:start">
 <div class="cartao" style="padding:6px 24px">{"".join(itens)}</div>{sobre}</div>"""
    return corpo, "definicoes", "Definições"


ECRAS = [("01_inicio", ecra_inicio), ("02_doente_passos", ecra_doente_passos),
         ("03_doente_resultado", ecra_doente_resultado), ("04_caso_stent", ecra_caso),
         ("05_robustez", ecra_robustez), ("06_definicoes", ecra_definicoes)]
FORMATOS = {"computador": (1440, 900, False), "telemovel": (390, 844, True)}


def renderizar(html: str, destino: Path, w: int, h: int) -> None:
    HTML.mkdir(parents=True, exist_ok=True)
    f = HTML / (destino.stem + ".html")
    f.write_text(html, encoding="utf-8")
    subprocess.run([dd.CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                    f"--window-size={w},{h}", "--force-device-scale-factor=2", f"--screenshot={destino}", f.as_uri()],
                   check=True, capture_output=True, timeout=120)


def folha_contactos(ficheiros: list[Path], destino: Path) -> None:
    """Uma imagem com todas as maquetes (reduzidas), por ecrã e por tema."""
    from PIL import Image, ImageDraw, ImageFont
    ims = {f.stem: Image.open(f) for f in ficheiros}
    esc = 0.18
    lw, lh = int(2880 * esc), int(1800 * esc)
    mw, mh = int(780 * esc), int(1688 * esc)
    cel_w = lw + mw + 30
    W = 40 + 2 * cel_w + 40
    H = 40 + len(ECRAS) * (max(lh, mh) + 50)
    folha = Image.new("RGB", (W, H), "#e9edf2")
    fonte = ImageFont.truetype(str(dd.FONTES / "Inter-Bold.ttf"), 16)
    dr = ImageDraw.Draw(folha)
    for i, (nome, _) in enumerate(ECRAS):
        y = 40 + i * (max(lh, mh) + 50)
        for k, tema in enumerate(("claro", "escuro")):
            x = 40 + k * cel_w
            dr.text((x, y - 24), f"{nome[3:].replace('_', ' ')} · {tema}", fill="#0f1720", font=fonte)
            folha.paste(ims[f"{nome}_computador_{tema}"].resize((lw, lh)), (x, y))
            folha.paste(ims[f"{nome}_telemovel_{tema}"].resize((mw, mh)), (x + lw + 12, y))
    folha.save(destino)


def main() -> None:
    d = dados()
    SAIDA.mkdir(parents=True, exist_ok=True)
    feitos = []
    for nome, fn in ECRAS:
        for formato, (w, h, movel) in FORMATOS.items():
            for tema, t in TEMAS.items():
                corpo, ativo, titulo = fn(d, t, tema, movel)
                html = dd.pagina(casca(corpo, ativo, titulo, t, tema, movel), css(t, movel), w, h)
                destino = SAIDA / f"{nome}_{formato}_{tema}.png"
                renderizar(html, destino, w, h)
                feitos.append(destino)
                print(destino.name)
    folha_contactos(feitos, SAIDA / "00_folha_de_contactos.png")


if __name__ == "__main__":
    main()
