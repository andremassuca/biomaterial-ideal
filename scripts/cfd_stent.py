"""CFD do stent coronário (extensão exploratória): struts finos (Pt-Cr) contra grossos (316L).

Uso:
    python scripts/cfd_stent.py poiseuille          # teste analítico (tubo sem stent, escoamento periódico)
    python scripts/cfd_stent.py malhas              # convergência da malha (estacionário, caudal médio)
    python scripts/cfd_stent.py pulsatil            # fluxo pulsátil, dois ciclos, médias no segundo
    python scripts/cfd_stent.py resumo              # tabelas e figuras a partir dos resultados gravados

Ferramenta: OpenFOAM v2406 (gratuito, GPL), na imagem opencfd/openfoam-default:2406 do Docker. Os casos
correm numa pasta de trabalho fora do repositório (TRABALHO); os resultados que interessam (tabelas e figuras)
vão para results/. Hipóteses e fontes em docs/CFD_STENT.md.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "src"))

from biomat_mcdm.cfd import analitico as an  # noqa: E402
from biomat_mcdm.cfd import geometria as geo  # noqa: E402
from biomat_mcdm.cfd import onda as on  # noqa: E402
from biomat_mcdm.cfd import openfoam as of  # noqa: E402

TRABALHO = Path(r"trabalho_cfd")
RESULTS = RAIZ / "results"
FIG = RESULTS / "figures" / "cfd"
IMAGEM = "opencfd/openfoam-default:2406"
NPROC = 8
DOCKER = shutil.which("docker") or r"<pasta local>"

# Sangue newtoniano (Boldock L et al. PLoS One 2022;17:e0271469, CFD de stents coronários: 0,0035 Pa.s e
# 1060 kg/m3); Newtoniano acima de 100-200 1/s (Thondapu V et al. Front Cardiovasc Med 2022;9:835270)
RHO = 1060.0
MU = 0.0035
NU = MU / RHO
LIMIAR_PA = 0.4  # corte baixo: Malek AM et al. JAMA 1999;282:2035 (< 4 dyn/cm2)

# Geometria (valores de desenho, os mesmos nos dois stents; só muda a espessura dos struts)
RAIO_MM = 1.5  # lúmen de 3,0 mm (tamanho de stent 3,00 mm da ficha SYNERGY em data/materiais.csv)
N_LOSANGOS = 8  # células à volta (como nos renders)
N_ANEIS = 6  # três losangos ao longo do eixo
LARGURA_UM = 90.0
Z0_MM = 1.0
SAIDA_MM = 3.0
MATERIAIS = {"Pt-Cr": "Pt-Cr", "316L": "Aço inox 316L"}  # rótulo curto: nome em data/materiais.csv
COMP_POISEUILLE_MM = 1.0
JANELA_POISEUILLE_MM = (0.25, 0.75)
MALHAS_UM = {"grossa": 28.0, "media": 20.0, "fina": 14.0}


def espessura_um(material: str) -> float:
    """Espessura típica do strut (µm), coluna "tipico" de data/materiais.csv."""
    d = pd.read_csv(RAIZ / "data" / "materiais.csv")
    linha = d[(d["caso"] == "Stent vascular") & (d["material"] == material)
              & (d["propriedade"] == "Espessura típica de strut")]
    return float(linha["tipico"].iloc[0])


def stent(rotulo: str) -> geo.Stent:
    arco = RAIO_MM * np.pi / N_LOSANGOS
    return geo.Stent(raio_mm=RAIO_MM, n_losangos=N_LOSANGOS, altura_anel_mm=arco, n_aneis=N_ANEIS, z0_mm=Z0_MM,
                     espessura_um=espessura_um(MATERIAIS[rotulo]), largura_um=LARGURA_UM)


def malha(st: geo.Stent | None, delta_um: float, comprimento_mm: float | None = None,
          janela_mm: tuple[float, float] | None = None) -> of.Malha:
    if st is None:
        return of.Malha(raio_mm=RAIO_MM, setor_rad=np.pi / N_LOSANGOS, comprimento_mm=comprimento_mm,
                        z_stent=janela_mm, delta_mm=delta_um / 1000)
    z1 = st.z0_mm + st.comprimento_mm
    return of.Malha(raio_mm=RAIO_MM, setor_rad=st.setor_rad, comprimento_mm=z1 + SAIDA_MM,
                    z_stent=(st.z0_mm - 0.3, z1 + 0.6), delta_mm=delta_um / 1000)


def ponto_fluido(m: of.Malha) -> tuple[float, float, float]:
    """Um ponto no lúmen (perto do eixo, na bissetriz do setor) para o snappyHexMesh saber o lado do fluido."""
    r = 0.3 * m.raio_mm
    return (r * np.cos(m.setor_rad / 2), r * np.sin(m.setor_rad / 2), 0.37 * m.comprimento_mm)


def preparar(nome: str, st: geo.Stent | None, m: of.Malha, *, transiente: bool, ciclico: bool = False,
             fim: float = 3000, dt: float = 1, escrita: float = 3000, inicio_media: float | None = None,
             onda: on.Onda | None = None, uniforme: bool = False) -> Path:
    """Escreve a pasta do caso: malha de fundo, struts (STL), condições de fronteira e controlo."""
    pasta = TRABALHO / nome
    if pasta.exists():
        shutil.rmtree(pasta)
    u_media = onda.u_media if onda else on.onda_coronaria().u_media
    fator = of.fourier_expr(onda.coeficientes(), onda.frequencia_hz) if onda else "1.0"
    fic = {"system/blockMeshDict": of.block_mesh(m, ciclico=ciclico),
           "system/fvSchemes": of.fv_schemes(transiente), "system/fvSolution": of.fv_solution(transiente),
           "system/decomposeParDict": of.decompose(NPROC),
           "system/controlDict": of.control_dict("pimpleFoam" if transiente else "simpleFoam", fim, dt, escrita,
                                                 inicio_media, "(parede struts)" if st else "(parede)"),
           "0/U": of.campo_u(RAIO_MM / 1000, u_media, fator, ciclico=ciclico, uniforme=uniforme), "0/p": of.campo_p(ciclico)}
    fic.update(of.propriedades(NU))
    if ciclico:
        fic["constant/fvOptions"] = of.ficheiro("dictionary", "fvOptions", f"""
forca
{{
    type meanVelocityForce;
    selectionMode all;
    fields (U);
    Ubar (0 0 {u_media:.9e});
}}""")
    if st is not None:
        fic["system/snappyHexMeshDict"] = of.snappy(m, ponto_fluido(m))
    of.escrever(pasta, fic)
    if st is not None:
        v, f = geo.solido_struts(st, tamanho_mm=min(0.02, m.delta_mm))
        (pasta / "constant" / "triSurface").mkdir(parents=True, exist_ok=True)
        geo.escrever_stl(pasta / "constant" / "triSurface" / "struts.stl", v, f)
    meta = {"nome": nome, "delta_um": m.delta_mm * 1000, "contagens": of.contagens(m), "transiente": transiente,
            "stent": None if st is None else {k: getattr(st, k) for k in st.__dataclass_fields__},
            "u_media": u_media, "rho": RHO, "mu": MU, "malha": {k: getattr(m, k) for k in m.__dataclass_fields__}}
    (pasta / "caso.json").write_text(json.dumps(meta, indent=1, default=float), encoding="utf-8")
    return pasta


def correr(nome: str, passos: list[str], copiar_de: str | None = None) -> int:
    """Corre os passos do OpenFOAM no contentor; o caso é copiado para o disco do contentor e voltam os registos,
    o postProcessing, os VTK e o último instante."""
    script = " && ".join([
        f"mkdir -p /work && cp -r /dados/{nome} /work/{nome}", f"cd /work/{nome}",
        *([f"cp -r /dados/{copiar_de} /work/{copiar_de}"] if copiar_de else []),
        *passos])
    fim = (f"; cd /work/{nome}; rm -rf processor*; ult=$(foamListTimes -latestTime 2>/dev/null | tail -1); "
           f"cp -r log.* postProcessing VTK caso.json /dados/{nome}/ 2>/dev/null; "
           f"[ -n \"$ult\" ] && rm -rf /dados/{nome}/ultimo && cp -r $ult /dados/{nome}/ultimo; "
           f"cp -r constant/polyMesh /dados/{nome}/polyMesh_final 2>/dev/null; true")
    cmd = [DOCKER, "run", "--rm", "-v", f"{TRABALHO.as_posix()}:/dados", IMAGEM, "bash", "-lc",
           "set -o pipefail; (" + script + ")" + "; estado=$?" + fim + "; exit $estado"]
    print(nome, "...", flush=True)
    return subprocess.run(cmd).returncode


def mpi(app: str, log: str) -> str:
    return f"mpirun --allow-run-as-root --oversubscribe -np {NPROC} {app} -parallel > log.{log} 2>&1"


def passos_malha(st: bool) -> list[str]:
    p = ["blockMesh > log.blockMesh 2>&1"]
    if st:
        p.append("snappyHexMesh -overwrite > log.snappyHexMesh 2>&1")
    p += ["checkMesh -allGeometry -allTopology > log.checkMesh 2>&1 || true"]
    return p


def poiseuille() -> int:
    """Teste analítico: tubo sem stent, com a mesma malha (tipo e célula junto à parede) da malha média.

    Escoamento periódico (a saída liga à entrada) com a velocidade média do ciclo imposta por uma força de
    pressão (meanVelocityForce): é o escoamento de Poiseuille plenamente desenvolvido, que o OpenFOAM tem de
    encontrar sozinho a partir de um perfil uniforme. Compara-se o perfil, a tensão de corte e a queda de pressão.
    """
    m = malha(None, MALHAS_UM["media"], comprimento_mm=COMP_POISEUILLE_MM, janela_mm=JANELA_POISEUILLE_MM)
    preparar("poiseuille", None, m, transiente=False, ciclico=True, fim=4000, escrita=4000)
    return correr("poiseuille", passos_malha(False) + [
        "simpleFoam > log.simpleFoam 2>&1",
        "foamToVTK -latestTime -fields '(U p wallShearStress)' > log.foamToVTK 2>&1"])


def caso_estacionario(rotulo: str, nome_malha: str) -> int:
    st = stent(rotulo)
    m = malha(st, MALHAS_UM[nome_malha])
    nome = f"estacionario_{rotulo}_{nome_malha}"
    preparar(nome, st, m, transiente=False, fim=3000, escrita=3000)
    return correr(nome, passos_malha(True) + [
        "decomposePar > log.decomposePar 2>&1", mpi("simpleFoam", "simpleFoam"),
        "reconstructPar -latestTime > log.reconstructPar 2>&1",
        "foamToVTK -latestTime -no-internal -patches '(parede struts)' -fields '(wallShearStress U p)' "
        "> log.foamToVTK 2>&1"])


def caso_pulsatil(rotulo: str, nome_malha: str = "media", passos_por_ciclo: int = 1000, ciclos: int = 2) -> int:
    st = stent(rotulo)
    m = malha(st, MALHAS_UM[nome_malha])
    o = on.onda_coronaria()
    T = o.periodo_s
    nome = f"pulsatil_{rotulo}_{nome_malha}_{passos_por_ciclo}"
    preparar(nome, st, m, transiente=True, fim=ciclos * T, dt=T / passos_por_ciclo, escrita=T,
             inicio_media=(ciclos - 1) * T, onda=o)
    return correr(nome, passos_malha(True) + [
        "decomposePar > log.decomposePar 2>&1", mpi("pimpleFoam", "pimpleFoam"),
        "reconstructPar -latestTime > log.reconstructPar 2>&1",
        "foamToVTK -latestTime -no-internal -patches '(parede struts)' "
        "-fields '(wallShearStress wallShearStressMean mag(wallShearStress)Mean U p)' > log.foamToVTK 2>&1"])


# ------------------------------------------------------------------ resultados

def vtk_ultimo(nome: str) -> Path | None:
    """Pasta VTK do último instante gravado de um caso (ou None se não correu)."""
    pastas = [p for p in (TRABALHO / nome / "VTK").glob(f"{nome}_*") if p.is_dir()]
    pastas.sort(key=lambda p: float(p.name.split("_")[-1]))
    return pastas[-1] if pastas else None


def resultado_poiseuille() -> dict | None:
    """Erros do teste de Poiseuille face à teoria (perfil, tensão de corte e queda de pressão)."""
    from biomat_mcdm.cfd import posproc as pp
    d = vtk_ultimo("poiseuille")
    if d is None:
        return None
    meta = json.loads((TRABALHO / "poiseuille" / "caso.json").read_text(encoding="utf-8"))
    U, R = meta["u_media"], RAIO_MM / 1000
    z0, z1 = 0.0, COMP_POISEUILLE_MM / 1000  # periódico: todo o tubo
    m = pp.ler(d / "internal.vtu")
    c = np.asarray(m.cell_centers().points)
    k = pp.janela_z(c, z0, z1)
    r, _ = pp.raio_e_angulo(c[k])
    uz = np.asarray(m.cell_data["U"])[k, 2]
    # queda de pressão: a força por unidade de volume que a meanVelocityForce teve de aplicar (última iteração)
    gp = None
    for linha in (TRABALHO / "poiseuille" / "log.simpleFoam").read_text(encoding="utf-8").splitlines():
        if "pressure gradient =" in linha:
            gp = float(linha.split("pressure gradient =")[1]) * RHO
    w = pp.ler(d / "boundary" / "parede.vtp").compute_cell_sizes()
    kw = pp.janela_z(np.asarray(w.cell_centers().points), z0, z1)
    tau = pp.magnitude_tensao(np.asarray(w.cell_data["wallShearStress"]), RHO)[kw]
    area = np.asarray(w.cell_data["Area"])[kw]
    teo = an.tensao_corte_poiseuille(MU, R, U)
    gp_teo = an.gradiente_pressao_poiseuille(MU, R, U)
    perfil = pp.erro_perfil(r, uz, R, U)
    return {"u_media": U, "celulas": int(m.n_cells), "erro_perfil_max": perfil["erro_max"],
            "erro_perfil_rms": perfil["erro_rms"], "tau_teo": teo, "tau_cfd": float((tau * area).sum() / area.sum()),
            "erro_tau_max": float(np.abs(tau / teo - 1).max()), "gp_teo": gp_teo, "gp_cfd": gp,
            "r": r, "uz": uz}


def metricas_parede(nome: str, campo: str = "wallShearStress") -> dict | None:
    """Tensão de corte na parede da artéria na zona do stent: média, fração da área abaixo de 0,4 Pa e mapa."""
    from biomat_mcdm.cfd import posproc as pp
    d = vtk_ultimo(nome)
    if d is None:
        return None
    meta = json.loads((TRABALHO / nome / "caso.json").read_text(encoding="utf-8"))
    st = meta["stent"]
    z0, z1 = st["z0_mm"] / 1000, (st["z0_mm"] + st["n_aneis"] * st["altura_anel_mm"]) / 1000
    w = pp.ler(d / "boundary" / "parede.vtp").compute_cell_sizes()
    c = np.asarray(w.cell_centers().points)
    area = np.asarray(w.cell_data["Area"])
    if campo == "TAWSS":
        tau = RHO * np.asarray(w.cell_data["mag(wallShearStress)Mean"])
        osi = pp.osi(np.asarray(w.cell_data["wallShearStressMean"]), tau / RHO)
    else:
        tau = pp.magnitude_tensao(np.asarray(w.cell_data[campo]), RHO)
        osi = None
    k = pp.janela_z(c, z0, z1)
    out = {"nome": nome, "celulas": None, "tau_media": float((tau[k] * area[k]).sum() / area[k].sum()),
           "fracao_baixa": pp.fracao_abaixo(tau[k], area[k], LIMIAR_PA), "area_mm2": float(area[k].sum() * 1e6),
           "espessura_um": st["espessura_um"], "delta_um": meta["delta_um"], "z0": z0, "z1": z1,
           "poligonos": [pp.desenrolar(np.asarray(w.get_cell(i).points), RAIO_MM / 1000) * 1000
                         for i in range(w.n_cells)], "tau": tau, "osi": osi}
    if osi is not None:
        out["osi_media"] = float((osi[k] * area[k]).sum() / area[k].sum())
        out["fracao_osi"] = pp.fracao_abaixo(-osi[k], area[k], -0.1)  # fração com OSI > 0,1
    log = TRABALHO / nome / "log.checkMesh"
    if log.exists():
        for linha in log.read_text(encoding="utf-8").splitlines():
            if linha.strip().startswith("cells:"):
                out["celulas"] = int(linha.split()[-1])
                break
    return out


def fmt(x: float, casas: int = 2) -> str:
    return f"{x:.{casas}f}".replace(".", ",")


def resumo() -> None:
    """Grava results/cfd_stent.md e as figuras a partir dos casos já corridos."""
    from biomat_mcdm.cfd import posproc as pp
    FIG.mkdir(parents=True, exist_ok=True)
    linhas = ["# CFD do stent coronário: struts finos (Pt-Cr) contra grossos (316L)", "",
              "Gerado por scripts/cfd_stent.py resumo. Hipóteses e fontes em docs/CFD_STENT.md. Extensão "
              "exploratória: OpenFOAM v2406, sangue newtoniano, parede rígida, setor de "
              f"{180 / N_LOSANGOS:.1f}° com planos de simetria.", ""]
    verif: dict = {}
    p = resultado_poiseuille()
    if p:
        verif["poiseuille"] = {"erro_perfil_max": p["erro_perfil_max"], "erro_tau": abs(p["tau_cfd"] / p["tau_teo"] - 1),
                               "erro_dp": abs(p["gp_cfd"] / p["gp_teo"] - 1)}
        linhas += ["## 1. Teste analítico: Poiseuille num tubo", "",
                   f"Tubo de {fmt(2 * RAIO_MM, 1)} mm, escoamento periódico com a velocidade média do ciclo "
                   f"({fmt(p['u_media'] * 100, 1)} cm/s), malha média ({p['celulas']} células).", "",
                   "| Grandeza | Teoria | CFD | Erro |", "|---|---|---|---|",
                   f"| Tensão de corte na parede (Pa) | {fmt(p['tau_teo'], 4)} | {fmt(p['tau_cfd'], 4)} | "
                   f"{fmt(100 * abs(p['tau_cfd'] / p['tau_teo'] - 1))} % (máximo local "
                   f"{fmt(100 * p['erro_tau_max'])} %) |",
                   f"| Queda de pressão (Pa/m) | {fmt(p['gp_teo'], 2)} | {fmt(p['gp_cfd'], 2)} | "
                   f"{fmt(100 * abs(p['gp_cfd'] / p['gp_teo'] - 1))} % |",
                   f"| Perfil de velocidade | parábola | {p['celulas']} células | máximo "
                   f"{fmt(100 * p['erro_perfil_max'])} %, médio quadrático {fmt(100 * p['erro_perfil_rms'])} % "
                   "(em fração da velocidade no eixo) |", "",
                   "Critério: erro abaixo de 2 %. " + ("Cumpre." if max(p["erro_perfil_max"], abs(
                       p["tau_cfd"] / p["tau_teo"] - 1)) < 0.02 else "NÃO CUMPRE."), ""]
        figura_poiseuille(p)
    # convergência
    tab = []
    for mat in MATERIAIS:
        for nm in MALHAS_UM:
            r = metricas_parede(f"estacionario_{mat}_{nm}")
            if r:
                tab.append({"material": mat, "malha": nm, **{k: r[k] for k in
                            ("celulas", "delta_um", "tau_media", "fracao_baixa", "espessura_um")}})
    if tab:
        t = pd.DataFrame(tab)
        t.to_csv(RESULTS / "cfd_malhas.csv", index=False)
        linhas += ["## 2. Convergência da malha (estacionário, caudal médio)", "",
                   "Tensão de corte na parede da artéria na zona do stent (sem a superfície dos struts).", "",
                   "| Material | Malha | Célula junto à parede (µm) | Células | Tensão média (Pa) | "
                   "Área abaixo de 0,4 Pa |", "|---|---|---|---|---|---|"]
        linhas += [f"| {r.material} | {r.malha} | {fmt(r.delta_um, 0)} | {r.celulas} | {fmt(r.tau_media, 3)} | "
                   f"{fmt(100 * r.fracao_baixa, 1)} % |" for r in t.itertuples()]
        linhas += [""]
        for mat in MATERIAIS:
            s = t[t.material == mat].set_index("malha")
            if all(n in s.index for n in MALHAS_UM):
                for col, rot in (("tau_media", "tensão média"), ("fracao_baixa", "área abaixo de 0,4 Pa")):
                    g = pp.indice_convergencia(s.loc["fina", col], s.loc["media", col], s.loc["grossa", col],
                                               MALHAS_UM["media"] / MALHAS_UM["fina"])
                    if col == "fracao_baixa":
                        verif["malha_max_variacao_area"] = max(verif.get("malha_max_variacao_area", 0.0),
                                                               g["variacao_fina"])
                    linhas.append(f"- {mat}, {rot}: variação da malha média para a fina {fmt(100 * g['variacao_fina'], 1)} %"
                                  + ("; as diferenças entre malhas não diminuem, por isso a ordem e o GCI não se "
                                     "calculam" if np.isnan(g["ordem"]) else
                                     f"; ordem observada {fmt(g['ordem'], 1)}; GCI da malha fina "
                                     f"{fmt(100 * g['gci_fina'], 1)} %"))
        linhas += [""]
    # pulsátil
    puls = {mat: metricas_parede(f"pulsatil_{mat}_media_{PASSOS}", "TAWSS") for mat in MATERIAIS}
    puls = {k: v for k, v in puls.items() if v}
    if puls:
        linhas += ["## 3. Fluxo pulsátil (malha média, segundo ciclo)", "",
                   "| Material | Espessura do strut (µm) | TAWSS média (Pa) | Área com TAWSS abaixo de 0,4 Pa | "
                   "OSI médio | Área com OSI acima de 0,1 |", "|---|---|---|---|---|---|"]
        linhas += [f"| {m} | {fmt(r['espessura_um'], 0)} | {fmt(r['tau_media'], 3)} | "
                   f"{fmt(100 * r['fracao_baixa'], 1)} % | {fmt(r['osi_media'], 3)} | {fmt(100 * r['fracao_osi'], 1)} % |"
                   for m, r in puls.items()]
        linhas += [""]
        json.dump({m: {k: r[k] for k in ("espessura_um", "tau_media", "fracao_baixa", "osi_media", "fracao_osi",
                                         "area_mm2")} for m, r in puls.items()},
                  open(RESULTS / "cfd_pulsatil.json", "w", encoding="utf-8"), indent=1)
        figura_mapas(puls)
        figura_mapas_diap(puls)
        linhas += ["Repetição entre ciclos (tensão média na parede no mesmo instante do 1.º e do 2.º ciclo, "
                   "na última metade do ciclo):", ""]
        for mat in puls:
            d = diferenca_ciclos(f"pulsatil_{mat}_media_{PASSOS}")
            if d is not None:
                verif["ciclos_max"] = max(verif.get("ciclos_max", 0.0), d)
                linhas.append(f"- {mat}: diferença máxima {fmt(100 * d, 1)} %")
        linhas += [""]
    passo = {p: metricas_parede(f"pulsatil_316L_grossa_{p}", "TAWSS") for p in (1000, 2000)}
    if all(passo.values()):
        a, b = passo[1000], passo[2000]
        verif["passo_variacao_area"] = abs(a["fracao_baixa"] - b["fracao_baixa"])
        linhas += ["## 4. Passo de tempo (316L, malha grossa)", "",
                   "| Passos por ciclo | TAWSS média (Pa) | Área abaixo de 0,4 Pa |", "|---|---|---|",
                   f"| 1000 | {fmt(a['tau_media'], 3)} | {fmt(100 * a['fracao_baixa'], 1)} % |",
                   f"| 2000 | {fmt(b['tau_media'], 3)} | {fmt(100 * b['fracao_baixa'], 1)} % |", "",
                   f"Variação: TAWSS {fmt(100 * abs(a['tau_media'] / b['tau_media'] - 1), 2)} %; área "
                   f"{fmt(100 * abs(a['fracao_baixa'] - b['fracao_baixa']), 2)} pontos percentuais.", ""]
    if puls:
        verif["pulsatil"] = {m: {k: r[k] for k in ("espessura_um", "tau_media", "fracao_baixa", "osi_media")}
                             for m, r in puls.items()}
    (RESULTS / "cfd_verificacoes.json").write_text(json.dumps(verif, indent=1), encoding="utf-8")
    (RESULTS / "cfd_stent.md").write_text("\n".join(linhas) + "\n", encoding="utf-8")
    print("\n".join(linhas))


PASSOS = 1000


def diferenca_ciclos(nome: str) -> float | None:
    """Maior diferença relativa da tensão média na parede entre o 1.º e o 2.º ciclo, no mesmo instante do ciclo
    (na segunda metade do ciclo, depois do arranque). Junta as pastas 0/ e a do instante de retoma (1.06/
    no 316L), quando o caso foi retomado."""
    from biomat_mcdm.cfd import posproc as pp
    d = pp.juntar_series(TRABALHO / nome / "postProcessing" / "tensaoParede")
    if d is None:
        return None
    t, v = d[:, 0], d[:, 1]
    T = on.onda_coronaria().periodo_s
    k1 = (t > 0.5 * T) & (t <= T)
    v2 = np.interp(t[k1] + T, t, v)
    return float(np.max(np.abs(v2 - v[k1]) / np.abs(v2).max()))


def figura_poiseuille(p: dict) -> None:
    sys.path.insert(0, str(RAIZ / "scripts"))
    import estilo_graficos as eg
    import matplotlib.pyplot as plt
    eg.aplicar("clara")
    fig, ax = plt.subplots(figsize=(5, 3.4))
    R = RAIO_MM / 1000
    r = np.linspace(0, R, 200)
    ax.plot(r * 1000, an.perfil_poiseuille(r, R, p["u_media"]) * 100, color="#55595e", lw=1.5, label="Teoria")
    sel = np.random.default_rng(0).choice(len(p["r"]), size=min(1500, len(p["r"])), replace=False)
    ax.scatter(p["r"][sel] * 1000, p["uz"][sel] * 100, s=3, color="#0072B2", label="CFD (células)")
    ax.set_xlabel("Distância ao eixo (mm)")
    ax.set_ylabel("Velocidade axial (cm/s)")
    ax.xaxis.set_major_formatter(eg.virgula(1))
    ax.legend(frameon=False)
    eg.gravar(fig, "poiseuille", FIG, formatos=("png", "svg"))
    plt.close(fig)


def figura_mapas(puls: dict) -> None:
    """Mapa da TAWSS na parede desenrolada (um setor espelhado para mostrar o losango inteiro)."""
    sys.path.insert(0, str(RAIZ / "scripts"))
    import estilo_graficos as eg
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.colors import Normalize
    eg.aplicar("clara")
    fig, axs = plt.subplots(len(puls), 1, figsize=(8, 1.9 * len(puls) + 0.6), sharex=True)
    axs = np.atleast_1d(axs)
    norm = Normalize(0, 1.0)
    for ax, (mat, r) in zip(axs, puls.items()):
        pol = r["poligonos"]
        espelho = [q * np.array([-1, 1]) for q in pol]
        cores = np.concatenate([r["tau"], r["tau"]])
        pc = PolyCollection([q[:, ::-1] for q in pol + espelho], array=cores, cmap="viridis", norm=norm,
                            edgecolors="face", linewidths=0.1)
        ax.add_collection(pc)
        ax.set_facecolor("#9aa0a6")  # struts (sem parede exposta)
        ax.set_xlim(r["z0"] * 1000 - 0.6, r["z1"] * 1000 + 1.5)
        a = RAIO_MM * np.pi / N_LOSANGOS
        ax.set_ylim(-a, a)
        ax.set_title(f"{rotulo_espessura(mat, r['espessura_um'])}; área abaixo de 0,4 Pa "
                     f"{fmt(100 * r['fracao_baixa'], 0)} %", fontsize=10, loc="left")
        ax.set_ylabel("Arco (mm)")
    axs[-1].set_xlabel("Comprimento ao longo da artéria (mm); o sangue corre da esquerda para a direita")
    cb = fig.colorbar(pc, ax=axs, shrink=0.9, pad=0.01)
    cb.set_label("TAWSS (Pa)")
    eg.gravar(fig, "tawss_mapas", FIG, formatos=("png", "svg"))
    plt.close(fig)


def figura_mapas_diap(puls: dict) -> Path:
    """Mapa para o diapositivo (6,9 x 4,3 pol, letra de 14 pt): parede desenrolada com o corte baixo a laranja.

    Em linguagem simples: corta-se a artéria ao comprido e abre-se como uma folha. Cinzento: os struts; laranja:
    parede onde o sangue roça devagar (TAWSS abaixo de 0,4 Pa); azul: o resto (mais escuro = mais corte).
    """
    sys.path.insert(0, str(RAIZ / "scripts"))
    import estilo_graficos as eg
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    from matplotlib.colors import LinearSegmentedColormap, Normalize
    eg.aplicar("clara")
    azul = LinearSegmentedColormap.from_list("azul", ["#cfe8f7", "#0595D1", "#0B3A5B"])
    fig, axs = plt.subplots(len(puls), 1, figsize=(6.9, 4.3), dpi=300, sharex=True)
    axs = np.atleast_1d(axs)
    a = RAIO_MM * np.pi / N_LOSANGOS
    for ax, (mat, r) in zip(axs, puls.items()):
        pol = r["poligonos"]
        # o setor (s de 0 a a) espelhado nos dois planos de simetria e repetido: s de -2a a 2a (dois losangos)
        todos = pol + [q * np.array([-1, 1]) for q in pol] + [q * np.array([-1, 1]) + [2 * a, 0] for q in pol] \
            + [q + [-2 * a, 0] for q in pol]
        tau = np.tile(r["tau"], 4)
        cores = azul(Normalize(LIMIAR_PA, 1.6)(tau))
        cores[tau < LIMIAR_PA] = (0.902, 0.443, 0.0, 1.0)  # laranja
        ax.add_collection(PolyCollection([q[:, ::-1] for q in todos], facecolors=cores, edgecolors="face",
                                         linewidths=0.05))
        ax.set_facecolor("#8c9196")
        ax.set_xlim(r["z0"] * 1000 - 0.4, r["z1"] * 1000 + 1.2)
        ax.set_ylim(-2 * a, 2 * a)
        ax.set_yticks([])
        ax.set_title(rotulo_espessura(mat, r["espessura_um"]), fontsize=14, loc="left")
        for lado in ("top", "right", "left"):
            ax.spines[lado].set_visible(False)
    axs[-1].set_xlabel("Ao longo da artéria (mm); o sangue corre da esquerda para a direita", fontsize=12)
    axs[-1].tick_params(labelsize=12)
    fig.tight_layout()
    destino = FIG / "tawss_mapas_diap.png"
    fig.savefig(destino, facecolor="white")
    plt.close(fig)
    return destino


ESPESSURA_ROTULO = {"Pt-Cr": ("Strut fino", "DES atual"), "316L": ("Strut grosso", "1.ª geração")}


def rotulo_espessura(mat: str, espessura_um: float) -> str:
    """Título de cada mapa pela espessura do strut (o efeito é da espessura, não da liga).

    Em linguagem simples: os dois casos simulados diferem só na espessura do strut (79 µm, a do Pt-Cr na base,
    e 135 µm, a do 316L de 1.ª geração); o título diz a espessura e a geração, não o material.
    """
    nome, geracao = ESPESSURA_ROTULO.get(mat, ("Strut", mat))
    return f"{nome}, {fmt(espessura_um, 0)} µm ({geracao})"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("acao", choices=["poiseuille", "malhas", "pulsatil", "um", "so_malha", "resumo"])
    ap.add_argument("--material", default="Pt-Cr")
    ap.add_argument("--malha", default="media")
    ap.add_argument("--passos", type=int, default=PASSOS)
    a = ap.parse_args()
    TRABALHO.mkdir(parents=True, exist_ok=True)
    if a.acao == "poiseuille":
        sys.exit(poiseuille())
    if a.acao == "so_malha":
        st = stent(a.material)
        nome = f"malha_{a.material}_{a.malha}"
        preparar(nome, st, malha(st, MALHAS_UM[a.malha]), transiente=False)
        sys.exit(correr(nome, passos_malha(True) + ["foamToVTK -no-internal -patches '(parede struts)' "
                                                    "> log.foamToVTK 2>&1"]))
    if a.acao == "um":
        sys.exit(caso_estacionario(a.material, a.malha))
    if a.acao == "malhas":
        for mat in MATERIAIS:
            for nm in MALHAS_UM:
                caso_estacionario(mat, nm)
    if a.acao == "pulsatil":
        sys.exit(caso_pulsatil(a.material, a.malha, a.passos))
    if a.acao == "resumo":
        resumo()


if __name__ == "__main__":
    main()
