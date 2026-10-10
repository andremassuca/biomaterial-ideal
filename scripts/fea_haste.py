"""FEA da haste femoral (extensão exploratória): stress shielding nas zonas de Gruen 1 e 7.

Uso:
    python scripts/fea_haste.py                      # malhas de 2,0, 1,5, 1,0 e 0,75 mm (completo)
    python scripts/fea_haste.py --malhas 2.0 1.5     # só as malhas dadas (teste rápido)

Fémur direito do BodyParts3D (FJ3365) intacto e com a haste Corail tamanho 8 na posição dos renders; quatro
materiais da haste; carga do pico da marcha (contacto da anca e abdutores); corte da diáfise encastrado.
Resultados: results/fea_haste.csv, results/fea_haste.md e results/figures/fea/. Hipóteses em
docs/FEA_HASTE.md.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from biomat_mcdm.fea import cargas, geometria as geo_fea, gruen, malha, materiais, posproc, solver  # noqa: E402
from biomat_mcdm.fea._scripts import cad, geo  # noqa: E402

OBJ_FEMUR = Path(r"recursos\bodyparts3d\obj\FJ3365.obj")
STL_HASTE = RAIZ / "design" / "cad" / "stl" / "haste_femoral_haste.STL"
SAIDA_CSV = RAIZ / "results" / "fea_haste.csv"
SAIDA_MD = RAIZ / "results" / "fea_haste.md"
SAIDA_VERIFICACOES = RAIZ / "results" / "fea_haste_verificacoes.md"
SAIDA_SENSIBILIDADE = RAIZ / "results" / "fea_haste_sensibilidade.md"
FIGURAS = RAIZ / "results" / "figures" / "fea"
MALHAS = (2.0, 1.5, 1.0, 0.75)
PASSO_FINO = 0.375  # passo máximo da grelha fina das regiões (mm): geometria quase igual em todas as malhas
MATERIAL_CABECA = "Co-Cr-Mo"  # cabeça da prótese: o mesmo em todos os casos (hipótese)


def preparar():
    """Lê o fémur, a haste e as cotas e calcula a montagem no referencial da haste."""
    vf, ff = geo.ler_obj(OBJ_FEMUR)
    cotas = cad.ler_cotas()
    g = geo_fea.montagem(vf, cotas)
    hv, hf = geo_fea.ler_stl(STL_HASTE)
    return g, ff, hv, hf, cotas


def modelo(g, ff, hv, hf, cotas, h: float, implantado: bool):
    """Etiquetas, malha de vóxeis e nós de carga de um modelo (intacto ou implantado) com passo h."""
    fator = max(2, int(np.ceil(h / PASSO_FINO - 1e-9)))
    origem, forma, forma_fina = geo_fea.grelha(g["vf"], h, fator)
    fina = geo_fea.etiquetas(g["vf"], ff, hv, hf, g, origem, h / fator, forma_fina, implantado,
                             cotas["cabeca_diametro"] / 2)
    # prioridade nos empates: haste e cabeça, depois cortical, trabecular e vazio
    grossa = malha.etiquetas_grossas(fina, fator, prioridade=[0, 3, 2, 4, 5])
    del fina
    ativos = malha.maior_componente(grossa > 0)
    pontos, lig, ijk = malha.malha_voxeis(ativos, origem, h)
    et = grossa[tuple(ijk.T)]
    return {"pontos": pontos, "lig": lig, "ijk": ijk, "et": et, "origem": origem, "forma": forma, "h": h}


def cargas_modelo(m, g, implantado: bool, peso_kg: float):
    """Vetor de forças nodais (contacto da anca + abdutores) e nós presos (corte da diáfise)."""
    p, lig, et = m["pontos"], m["lig"], m["et"]
    n = len(p)
    sup = cargas.nos_superficie(lig, n)
    f = cargas.forcas_marcha(peso_kg)
    Fc = cargas.para_referencial(f["contacto"], g["medial"], g["anterior"], g["proximal"])
    Fa = cargas.para_referencial(f["abdutores"], g["medial"], g["anterior"], g["proximal"])
    osso = np.zeros(n, bool)
    osso[np.unique(lig[np.isin(et, [geo_fea.CORTICAL, geo_fea.TRABECULAR])])] = True
    if implantado:
        cabeca = np.zeros(n, bool)
        cabeca[np.unique(lig[et == geo_fea.CABECA])] = True
        nc = cargas.nos_calote(p, sup & cabeca, g["centro_haste"], Fc, raio_max=1e9)
    else:
        nc = cargas.nos_calote(p, sup & osso, g["H"], Fc, raio_max=g["r"] + 2 * m["h"])
    # trocânter: nós de osso à superfície perto do topo do trocânter (lado lateral do eixo da haste)
    na = cargas.nos_trocanter(p, sup & osso, cargas.topo_trocanter(g["vf"]), raio=10.0)
    fvec = cargas.distribuir(nc, Fc, n) + cargas.distribuir(na, Fa, n)
    base = np.flatnonzero(p[:, 1] < p[:, 1].min() + 1e-6)  # nós do corte da diáfise (encastrados)
    return fvec, base, {"n_contacto": len(nc), "n_abdutores": len(na), "n_fixos": len(base)}


def propriedades(et, E_haste: float, nu_haste: float, osso: dict, cabeca: tuple):
    """E e nu de cada elemento a partir da etiqueta."""
    E = np.zeros(len(et))
    nu = np.zeros(len(et))
    for rot, (Ev, nv) in {geo_fea.CORTICAL: osso["cortical"], geo_fea.TRABECULAR: osso["trabecular"],
                          geo_fea.HASTE: (E_haste, nu_haste), geo_fea.CABECA: cabeca}.items():
        E[et == rot], nu[et == rot] = Ev, nv
    return E, nu


def correr_malha(h, g, ff, hv, hf, cotas, peso_kg, figura=False, e_trabecular_mpa=None):
    """Resolve o fémur intacto e os quatro materiais numa malha de passo h; devolve linhas da tabela.

    e_trabecular_mpa: módulo do osso trabecular (por defeito, o do caso principal; outro valor serve para a
    análise de sensibilidade)."""
    t0 = time.time()
    osso = materiais.materiais_osso() if e_trabecular_mpa is None else materiais.materiais_osso(e_trabecular_mpa)
    mats = materiais.materiais_haste()
    cab = mats[MATERIAL_CABECA]
    L = gruen.comprimento_intraosseo(g["base_colo"], g["d_colo"], geo_fea.OSTEOTOMIA_ALEM_BASE)
    vol = h ** 3

    mi = modelo(g, ff, hv, hf, cotas, h, implantado=False)
    fi, di, info_i = cargas_modelo(mi, g, False, peso_kg)
    Ei, nui = propriedades(mi["et"], 0, 0.3, osso, cab)
    ui = solver.resolver_voxeis(mi["lig"], Ei, nui, h, mi["pontos"], fi, di)
    Wi = solver.energia_voxeis(mi["lig"], Ei, nui, h, ui)
    print(f"  h = {h} mm: intacto com {len(mi['lig'])} elementos, {3 * len(mi['pontos'])} graus "
          f"({info_i}); {time.time() - t0:.0f} s", flush=True)

    mimp = modelo(g, ff, hv, hf, cotas, h, implantado=True)
    fimp, dimp, info_m = cargas_modelo(mimp, g, True, peso_kg)
    centros = mimp["origem"] + h * (mimp["ijk"] + 0.5)
    zonas = gruen.zonas_gruen(centros, L)
    osso_imp = np.isin(mimp["et"], [geo_fea.CORTICAL, geo_fea.TRABECULAR])
    par = posproc.corresponder(mi["ijk"], mimp["ijk"], mi["forma"])
    comparavel = osso_imp & (par >= 0)
    comparavel[comparavel] &= np.isin(mi["et"][par[comparavel]], [geo_fea.CORTICAL, geo_fea.TRABECULAR])
    W_intacto_mesmo = np.zeros(len(mimp["et"]))
    W_intacto_mesmo[comparavel] = Wi[par[comparavel]]
    ref = posproc.energia_por_zona(W_intacto_mesmo, vol, zonas, comparavel, lista=range(1, 8))

    linhas = [{"malha_mm": h, "material": "Fémur intacto", "E_haste_GPa": np.nan, "zona": z,
               "energia_mJ": ref[z][0], "energia_por_volume_mJ_mm3": ref[z][1], "razao": 1.0,
               "stress_shielding": 0.0, "elementos": len(mi["lig"]), "graus_liberdade": 3 * len(mi["pontos"])}
              for z in ref]
    campos = {"Fémur intacto": (mi, Wi)}
    for nome, (E, nu) in mats.items():
        Em, num = propriedades(mimp["et"], E, nu, osso, cab)
        u = solver.resolver_voxeis(mimp["lig"], Em, num, h, mimp["pontos"], fimp, dimp)
        W = solver.energia_voxeis(mimp["lig"], Em, num, h, u)
        res = posproc.energia_por_zona(W, vol, zonas, comparavel, lista=range(1, 8))
        for z in res:
            r, ss = posproc.razao_e_shielding(res[z][0], ref[z][0])
            linhas.append({"malha_mm": h, "material": nome, "E_haste_GPa": E / 1000, "zona": z,
                           "energia_mJ": res[z][0], "energia_por_volume_mJ_mm3": res[z][1], "razao": r,
                           "stress_shielding": ss, "elementos": len(mimp["lig"]),
                           "graus_liberdade": 3 * len(mimp["pontos"])})
        campos[nome] = (mimp, W)
        print(f"    {nome}: Gruen 1 = {res[1][0]:.2f} mJ (razão {res[1][0] / ref[1][0]:.3f}), Gruen 7 = "
              f"{res[7][0]:.2f} mJ (razão {res[7][0] / ref[7][0]:.3f}); {time.time() - t0:.0f} s", flush=True)
    print(f"    cargas: intacto {info_i}; implantado {info_m}", flush=True)
    if figura:
        figura_corte(campos, g, L)
        figura_diapositivo(campos, L)
    return linhas


def figura_corte(campos: dict, g, L):
    """Mapa de cores da densidade de energia de deformação no corte coronal (plano da haste, z = 0)."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm

    FIGURAS.mkdir(parents=True, exist_ok=True)
    nomes = list(campos)
    fig, eixos = plt.subplots(1, len(nomes), figsize=(3.2 * len(nomes), 6.4), sharey=True)
    norm = LogNorm(vmin=1e-5, vmax=3e-2)
    for ax, nome in zip(eixos, nomes):
        m, W = campos[nome]
        img, implante, ext = _imagem_corte(m, W)
        im = ax.imshow(img, origin="lower", extent=ext, norm=norm, cmap="viridis", interpolation="nearest")
        ax.imshow(implante, origin="lower", extent=ext, cmap="Greys", vmin=0, vmax=1.6, interpolation="nearest")
        for y in (L / 3, 2 * L / 3):
            ax.axhline(y, color="0.5", lw=0.6, ls="--")
        ax.axvline(0, color="0.5", lw=0.6, ls="--")
        ax.set_title(nome, fontsize=10)
        ax.set_xlabel("x (mm), lateral +")
        ax.set_aspect("equal")
    eixos[0].set_ylabel("y ao longo da haste (mm)")
    fig.colorbar(im, ax=eixos, shrink=0.7, label="densidade de energia de deformação no osso (mJ/mm³)")
    fig.suptitle("Corte coronal pelo plano da haste; cinzento: haste e cabeça; tracejado: limites das zonas de Gruen",
                 fontsize=10)
    for ext in ("png", "svg"):
        fig.savefig(FIGURAS / f"sed_corte_coronal.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)


def _imagem_corte(m, W):
    """Imagem (linhas = y, colunas = x) da densidade de energia no osso e máscara do implante no plano z = 0."""
    h = m["h"]
    k0 = int(np.floor((0.0 - m["origem"][2]) / h))
    sel = m["ijk"][:, 2] == k0
    ijk = m["ijk"][sel]
    osso = np.isin(m["et"][sel], [geo_fea.CORTICAL, geo_fea.TRABECULAR])
    img = np.full((m["forma"][1], m["forma"][0]), np.nan)
    img[ijk[osso, 1], ijk[osso, 0]] = W[sel][osso] / h ** 3
    implante = np.full(img.shape, np.nan)
    implante[ijk[~osso, 1], ijk[~osso, 0]] = 1.0
    ext = [m["origem"][0], m["origem"][0] + h * m["forma"][0], m["origem"][1], m["origem"][1] + h * m["forma"][1]]
    return img, implante, ext


PAINEIS_DIAPOSITIVO = ("Fémur intacto", "Co-Cr-Mo", "Ti-6Al-4V poroso")


def titulos_diapositivo() -> list[str]:
    """Títulos dos três painéis do diapositivo, com os nomes simples dos materiais (scripts/nomes_simples.py)."""
    from biomat_mcdm.fea._scripts import _carregar

    ns = _carregar("nomes_simples")
    return ["Fémur intacto", ns.com_codigo("Co-Cr-Mo forjado"), f"{ns.nome('Ti-6Al-4V ELI')} porosa (17 GPa)"]


def figura_diapositivo(campos: dict, L: float, caminho=None):
    """Versão para diapositivo do mapa de energia: 3 painéis, 7,6 x 4,6 polegadas, 300 ppp, letra de 14 pt.

    Em linguagem simples: só o fémur intacto, o cobalto-crómio e a liga de titânio porosa, sem eixos nem título
    geral; as linhas a tracejado marcam o início das zonas de Gruen 1 (lateral) e 7 (medial) e a barra de cor
    diz "energia de deformação no osso" em escala logarítmica.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LogNorm

    caminho = Path(caminho) if caminho else FIGURAS / "sed_corte_coronal_diap"
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with plt.rc_context({"font.size": 14}):
        fig, eixos = plt.subplots(1, 3, figsize=(7.6, 4.6), gridspec_kw={"wspace": 0.02})
        fig.subplots_adjust(left=0.01, right=0.99, top=0.86, bottom=0.28)
        norm = LogNorm(vmin=1e-5, vmax=3e-2)
        y0 = 2 * L / 3  # limite inferior das zonas de Gruen 1 (lateral) e 7 (medial)
        for ax, chave, titulo in zip(eixos, PAINEIS_DIAPOSITIVO, titulos_diapositivo()):
            m, W = campos[chave]
            img, implante, ext = _imagem_corte(m, W)
            im = ax.imshow(img, origin="lower", extent=ext, norm=norm, cmap="viridis", interpolation="nearest")
            ax.imshow(implante, origin="lower", extent=ext, cmap="Greys", vmin=0, vmax=1.6, interpolation="nearest")
            ax.plot([-34, 30], [y0, y0], color="0.15", lw=1.2, ls="--")
            ax.text(29, y0 + 3, "G1", fontsize=14, ha="right", va="bottom")
            ax.text(-34, y0 + 3, "G7", fontsize=14, ha="left", va="bottom")
            ax.set_xlim(-64, 30)
            ax.set_ylim(-20, 158)
            ax.set_title(titulo.replace(" (", "\n("), fontsize=14)
            ax.set_axis_off()
        cax = fig.add_axes([0.12, 0.19, 0.76, 0.04])
        barra = fig.colorbar(im, cax=cax, orientation="horizontal")
        barra.set_label("energia de deformação no osso (escala logarítmica)", fontsize=14)
        barra.set_ticks([1e-4, 1e-2])
        barra.set_ticklabels(["baixa", "alta"])
        barra.ax.tick_params(labelsize=14)
        barra.ax.minorticks_off()
        for ext in ("png", "svg"):
            fig.savefig(caminho.with_suffix(f".{ext}"), dpi=300)
        plt.close(fig)
    return caminho


def verificacoes(h, g, ff, hv, hf, cotas, peso_kg, hastes=("Ti-6Al-4V", "Co-Cr-Mo")) -> dict:
    """Verificações de sanidade: equilíbrio, deformações principais no cortical e deslocamentos.

    Em linguagem simples: (a) as reações no corte da diáfise têm de ser iguais e de sinal contrário à soma das
    cargas aplicadas; (c) as deformações principais no osso cortical do fémur intacto comparam-se com a gama
    da marcha da literatura; (d) regista-se o deslocamento máximo, onde ocorre e o do centro da cabeça.
    """
    osso = materiais.materiais_osso()
    mats = materiais.materiais_haste()
    cab = mats[MATERIAL_CABECA]
    saida = {}
    casos = [("Fémur intacto", False, (0.0, 0.3))] + [(n, True, mats[n]) for n in hastes]
    for nome, implantado, mat in casos:
        m = modelo(g, ff, hv, hf, cotas, h, implantado)
        f, presos, _ = cargas_modelo(m, g, implantado, peso_kg)
        E, nu = propriedades(m["et"], mat[0], mat[1], osso, cab)
        u = solver.resolver_voxeis(m["lig"], E, nu, h, m["pontos"], f, presos)
        n = len(m["pontos"])
        fint = solver.forcas_internas(m["lig"], E, nu, h, u, n).reshape(n, 3)
        fn = f.reshape(n, 3)
        reacao = fint[presos].sum(0)  # nos nós presos, K u é a força que o apoio faz sobre o osso
        aplicada = fn.sum(0)
        livres = np.setdiff1d(np.arange(n), presos)
        U = u.reshape(n, 3)
        d = np.linalg.norm(U, axis=1)
        imax = int(np.argmax(d))
        centro = g["centro_haste"] if implantado else g["H"]
        perto = np.argsort(np.linalg.norm(m["pontos"] - centro, axis=1))[:8]
        r = {"aplicada_N": aplicada, "reacao_N": reacao,
             "erro_equilibrio_pct": 100 * np.linalg.norm(reacao + aplicada) / np.linalg.norm(aplicada),
             "residuo_max_N": float(np.abs(fint[livres] - fn[livres]).max()),
             "desloc_max_mm": float(d[imax]), "ponto_max": m["pontos"][imax], "desloc_cabeca_mm": U[perto].mean(0)}
        if not implantado:
            cort = m["et"] == geo_fea.CORTICAL
            centros = m["origem"] + h * (m["ijk"] + 0.5)
            # diáfise: de 10 mm acima do encastramento até à altura da ponta da haste (y = 0)
            diaf = cort & (centros[:, 1] > m["origem"][1] + 10) & (centros[:, 1] < 0)
            eps = solver.deformacoes_centro(m["lig"][diaf], h, u)
            ep = solver.deformacoes_principais(eps)
            # lado lateral e medial em cada fatia de 5 mm (x acima ou abaixo da média da fatia); deformação axial eps_yy
            yb = np.floor(centros[diaf, 1] / 5.0)
            xm = pd.Series(centros[diaf, 0]).groupby(yb).transform("mean").to_numpy()
            lateral = centros[diaf, 0] > xm
            r["axial_lateral_ue"] = 1e6 * float(np.median(eps[lateral, 1, 1]))
            r["axial_medial_ue"] = 1e6 * float(np.median(eps[~lateral, 1, 1]))
            r["eps_max_ue"] = 1e6 * np.percentile(ep[:, 2], [50, 95, 99, 100])
            r["eps_min_ue"] = 1e6 * np.percentile(ep[:, 0], [50, 5, 1, 0])
            epc = solver.deformacoes_principais(solver.deformacoes_centro(m["lig"][cort], h, u))
            r["eps_cortical_todo_ue"] = (1e6 * np.percentile(epc[:, 2], 99), 1e6 * np.percentile(epc[:, 0], 1))
        saida[nome] = r
        print(f"  {nome}: aplicada {aplicada.round(1)} N, reação {reacao.round(1)} N, erro "
              f"{r['erro_equilibrio_pct']:.2e} %; deslocamento máximo {d[imax]:.2f} mm em "
              f"{m['pontos'][imax].round(1)}; cabeça {r['desloc_cabeca_mm'].round(2)} mm", flush=True)
    return saida


def texto_verificacoes(v: dict, h: float) -> str:
    """Texto de results/fea_haste_verificacoes.md com os números das verificações."""
    linhas = ["# FEA da haste: verificações de sanidade", "",
              f"Gerado por scripts/fea_haste.py --verificacoes (malha de {num(h, 'g')} mm). Unidades: mm, N, MPa, mJ. "
              "Referencial da haste: x lateral, y ao longo da haste (ponta em y = 0), z normal ao plano da haste.", "",
              "## Equilíbrio (soma das cargas aplicadas e soma das reações no corte da diáfise)", "",
              "| Modelo | Cargas aplicadas (x; y; z, N) | Reações (x; y; z, N) | Erro (%) | Resíduo nodal máximo (N) |",
              "|---|---|---|---|---|"]
    for nome, r in v.items():
        a = "; ".join(num(x, ".1f") for x in r["aplicada_N"])
        b = "; ".join(num(x, ".1f") for x in r["reacao_N"])
        linhas.append(f"| {nome} | {a} | {b} | {num(r['erro_equilibrio_pct'], '.1e')} | "
                      f"{num(r['residuo_max_N'], '.1e')} |")
    linhas += ["", "## Deslocamentos", "",
               "| Modelo | Máximo (mm) | Onde (x; y; z, mm) | Centro da cabeça (ux; uy; uz, mm) |", "|---|---|---|---|"]
    for nome, r in v.items():
        linhas.append(f"| {nome} | {num(r['desloc_max_mm'], '.2f')} | "
                      f"{'; '.join(num(x, '.0f') for x in r['ponto_max'])} | "
                      f"{'; '.join(num(x, '.2f') for x in r['desloc_cabeca_mm'])} |")
    r = v["Fémur intacto"]
    linhas += ["", "## Deformações principais no osso cortical do fémur intacto (microdeformações)", "",
               "Diáfise (de 10 mm acima do encastramento até à altura da ponta da haste):", "",
               "| Grandeza | Mediana | Percentil 95 (ou 5) | Percentil 99 (ou 1) | Extremo |", "|---|---|---|---|---|",
               "| Máxima (tração) | " + " | ".join(num(x, ".0f") for x in r["eps_max_ue"]) + " |",
               "| Mínima (compressão) | " + " | ".join(num(x, ".0f") for x in r["eps_min_ue"]) + " |", "",
               f"Todo o cortical: percentil 99 da máxima {num(r['eps_cortical_todo_ue'][0], '.0f')}; percentil 1 da "
               f"mínima {num(r['eps_cortical_todo_ue'][1], '.0f')}.", "",
               f"Deformação axial (ao longo da haste) mediana na diáfise: lado lateral {num(r['axial_lateral_ue'], '.0f')}, "
               f"lado medial {num(r['axial_medial_ue'], '.0f')} (positivo = tração)."]
    return "\n".join(linhas) + "\n"


def texto_sensibilidade(sens: pd.DataFrame, base: pd.DataFrame, e_sens: float, e_base: float, h: float) -> str:
    """Tabela das razões em Gruen 1 e 7 com o E do trabecular do caso principal e com o da sensibilidade.

    Em linguagem simples: põe lado a lado a razão implantado / intacto com os dois módulos do osso trabecular e
    diz se a ordem dos materiais muda.
    """
    linhas = ["# FEA da haste: sensibilidade ao módulo do osso trabecular", "",
              f"Gerado por scripts/fea_haste.py --sensibilidade-trabecular {num(e_sens, 'g')} (malha de "
              f"{num(h, 'g')} mm). Caso principal: {num(e_base / 1000, 'g')} GPa; sensibilidade: "
              f"{num(e_sens / 1000, 'g')} GPa.", "",
              f"| Material da haste | Razão G1 ({num(e_base / 1000, 'g')} GPa) | Razão G1 ({num(e_sens / 1000, 'g')} GPa) "
              f"| Razão G7 ({num(e_base / 1000, 'g')} GPa) | Razão G7 ({num(e_sens / 1000, 'g')} GPa) |",
              "|---|---|---|---|---|"]
    b = base[base["malha_mm"] == h]
    s = sens[sens["malha_mm"] == h]
    ordens = {}
    for nome in s["material"].unique():
        if nome == "Fémur intacto":
            continue
        val = [d[(d["material"] == nome) & (d["zona"] == z)]["razao"].iloc[0] for z in (1, 7) for d in (b, s)]
        linhas.append(f"| {nome} | " + " | ".join(num(v) for v in val) + " |")
    for rotulo, d in (("principal", b), ("sensibilidade", s)):
        for z in (1, 7):
            dz = d[(d["zona"] == z) & (d["material"] != "Fémur intacto")].sort_values("energia_mJ", ascending=False)
            ordens[(rotulo, z)] = list(dz["material"])
    linhas += [""]
    for z in (1, 7):
        igual = ordens[("principal", z)] == ordens[("sensibilidade", z)]
        linhas.append(f"- Gruen {z}: ordem {'igual' if igual else 'diferente'} (sensibilidade: "
                      + " > ".join(ordens[("sensibilidade", z)]) + ").")
    return "\n".join(linhas) + "\n"


def num(x: float, fmt: str = ".3f") -> str:
    """Número com vírgula decimal (português) e sem "-0"."""
    t = format(x + 0.0, fmt)
    if re.fullmatch(r"-0[.,]?0*(e[+-]\d+)?", t):
        t = t[1:]
    return t.replace(".", ",")


def tabela_md(df: pd.DataFrame, malhas) -> str:
    """Texto de results/fea_haste.md: tabela por material na malha mais fina e convergência."""
    fina, anterior = malhas[-1], malhas[-2] if len(malhas) > 1 else None
    d = df[df["malha_mm"] == fina]
    linhas = [
        "# FEA da haste femoral: energia de deformação no osso nas zonas de Gruen 1 e 7",
        "",
        "Gerado por scripts/fea_haste.py. Hipóteses e fontes em docs/FEA_HASTE.md. Extensão exploratória: "
        "modelo linear, estático, osso isotrópico e interface colada.",
        "",
        f"Malha mais fina: {num(fina, 'g')} mm (hexaedros de vóxel). Energia em mJ (N·mm); por volume em mJ/mm³.",
        "Razão = implantado / intacto no mesmo osso; stress shielding = 1 - razão.",
        "",
        "| Material da haste | E (GPa) | Gruen 1: energia | Gruen 1: por volume | Gruen 1: razão | Gruen 1: SS "
        "| Gruen 7: energia | Gruen 7: por volume | Gruen 7: razão | Gruen 7: SS |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for nome in d["material"].unique():
        a = d[(d["material"] == nome) & (d["zona"] == 1)].iloc[0]
        b = d[(d["material"] == nome) & (d["zona"] == 7)].iloc[0]
        E = "" if np.isnan(a["E_haste_GPa"]) else num(a["E_haste_GPa"], ".1f")
        linhas.append(f"| {nome} | {E} | {num(a['energia_mJ'])} | {num(a['energia_por_volume_mJ_mm3'], '.2e')} | "
                      f"{num(a['razao'])} | {num(a['stress_shielding'])} | {num(b['energia_mJ'])} | "
                      f"{num(b['energia_por_volume_mJ_mm3'], '.2e')} | {num(b['razao'])} | {num(b['stress_shielding'])} |")
    linhas += ["", "## Convergência da malha", "",
               "| Malha (mm) | Elementos (implantado) | Graus de liberdade | Material | Gruen 1 (mJ) | Gruen 7 (mJ) "
               "| Razão G1 | Razão G7 |", "|---|---|---|---|---|---|---|---|"]
    for h in malhas:
        for nome in df["material"].unique():
            a = df[(df["malha_mm"] == h) & (df["material"] == nome) & (df["zona"] == 1)].iloc[0]
            b = df[(df["malha_mm"] == h) & (df["material"] == nome) & (df["zona"] == 7)].iloc[0]
            linhas.append(f"| {num(h, 'g')} | {a['elementos']} | {a['graus_liberdade']} | {nome} | "
                          f"{num(a['energia_mJ'])} | {num(b['energia_mJ'])} | {num(a['razao'])} | {num(b['razao'])} |")
    if anterior is not None:
        linhas += ["", f"Variação entre as duas malhas mais finas ({num(anterior, 'g')} e {num(fina, 'g')} mm), em %:", "",
                   "| Material | Gruen 1 (energia) | Gruen 7 (energia) | Razão G1 | Razão G7 |", "|---|---|---|---|---|"]
        maximos = {"energia": 0.0, "razao": 0.0}
        for nome in df["material"].unique():
            v = []
            for z in (1, 7):
                a = df[(df["malha_mm"] == fina) & (df["material"] == nome) & (df["zona"] == z)].iloc[0]
                b = df[(df["malha_mm"] == anterior) & (df["material"] == nome) & (df["zona"] == z)].iloc[0]
                v.append((posproc.variacao_relativa(a["energia_mJ"], b["energia_mJ"]),
                          posproc.variacao_relativa(a["razao"], b["razao"])))
            linhas.append(f"| {nome} | {num(v[0][0], '.1f')} | {num(v[1][0], '.1f')} | {num(v[0][1], '.1f')} | "
                          f"{num(v[1][1], '.1f')} |")
            maximos["energia"] = max(maximos["energia"], v[0][0], v[1][0])
            maximos["razao"] = max(maximos["razao"], v[0][1], v[1][1])
        ok = {k: "cumpre" if m < 5 else "não cumpre" for k, m in maximos.items()}
        linhas += ["", f"Critério (variação abaixo de 5 % entre as duas malhas mais finas): a razão implantado / "
                   f"intacto (e portanto o stress shielding) {ok['razao']} (máximo {num(maximos['razao'], '.1f')} %); "
                   f"a energia absoluta {ok['energia']} (máximo {num(maximos['energia'], '.1f')} %)."]
    linhas += ["", "Ordem pela energia de deformação no osso (malha mais fina, do maior para o menor):", ""]
    for z in (1, 7):
        dz = d[(d["zona"] == z) & (d["material"] != "Fémur intacto")].sort_values("energia_mJ", ascending=False)
        linhas.append(f"- Gruen {z}: " + " > ".join(dz["material"]))
    linhas += ["", NOTA_POROSO]
    return "\n".join(linhas) + "\n"


NOTA_POROSO = ("Haste de Ti-6Al-4V poroso (17 GPa, valor de desenho): com interface colada e rigidez igual à do osso "
               "cortical, a energia no osso fica próxima da do osso intacto (razão perto de 1); uma razão acima de 1 "
               "quer dizer só que o osso à volta trabalha um pouco mais do que no fémur intacto.")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--malhas", type=float, nargs="+", default=list(MALHAS))
    ap.add_argument("--peso", type=float, default=cargas.PESO_DESENHO_KG)
    ap.add_argument("--sem-gravar", action="store_true")
    ap.add_argument("--verificacoes", action="store_true",
                    help="só as verificações de sanidade, na malha mais fina dada (results/fea_haste_verificacoes.md)")
    ap.add_argument("--sensibilidade-trabecular", type=float, default=None, metavar="E_MPA",
                    help="sensibilidade com outro E do trabecular, em MPa (results/fea_haste_sensibilidade.md)")
    ap.add_argument("--so-figuras", action="store_true", help="só refaz as figuras na malha mais fina dada")
    a = ap.parse_args(argv)
    malhas = sorted(a.malhas, reverse=True)
    g, ff, hv, hf, cotas = preparar()
    print(f"cabeça anatómica no referencial da haste: {g['H'].round(2)}, raio {g['r']:.1f} mm; "
          f"centro da cabeça da haste {g['centro_haste'].round(2)}")
    if a.so_figuras:
        return correr_malha(malhas[-1], g, ff, hv, hf, cotas, a.peso, figura=True)
    if a.verificacoes:
        v = verificacoes(malhas[-1], g, ff, hv, hf, cotas, a.peso)
        texto = texto_verificacoes(v, malhas[-1])
        if not a.sem_gravar:
            SAIDA_VERIFICACOES.write_text(texto, encoding="utf-8")
        print(texto)
        return v
    if a.sensibilidade_trabecular is not None:
        sens = pd.DataFrame([l for h in malhas for l in correr_malha(
            h, g, ff, hv, hf, cotas, a.peso, e_trabecular_mpa=a.sensibilidade_trabecular)])
        texto = texto_sensibilidade(sens, pd.read_csv(SAIDA_CSV), a.sensibilidade_trabecular,
                                    materiais.E_TRABECULAR_MPA, malhas[-1])
        if not a.sem_gravar:
            SAIDA_SENSIBILIDADE.write_text(texto, encoding="utf-8")
        print(texto)
        return sens
    linhas = []
    for h in malhas:
        linhas += correr_malha(h, g, ff, hv, hf, cotas, a.peso, figura=(h == malhas[-1] and not a.sem_gravar))
    df = pd.DataFrame(linhas)
    if not a.sem_gravar:
        SAIDA_CSV.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(SAIDA_CSV, index=False, encoding="utf-8")
        SAIDA_MD.write_text(tabela_md(df, malhas), encoding="utf-8")
    print(tabela_md(df, malhas))
    return df


if __name__ == "__main__":
    main()
