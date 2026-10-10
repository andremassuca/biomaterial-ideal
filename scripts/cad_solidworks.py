"""Modelos CAD da haste femoral e do implante dentário no SolidWorks, criados por script (API COM).

Uso (com o SolidWorks aberto):
    python scripts/cad_solidworks.py [haste|implante|todos]

Saída: design/cad/haste_femoral.SLDPRT e design/cad/implante_dentario.SLDPRT (árvore de operações com nomes em
português) e um STL binário por corpo em design/cad/stl/, para o Blender (o SolidWorks 2025 não exporta glTF).

As cotas vêm de design/cad/cotas.md (com fonte, ou "valor de desenho, ilustrativo"). As funções puras (ler as
cotas e calcular os perfis) estão separadas das que falam com o SolidWorks, para poderem ser testadas sem ele.
Medidas em mm nas funções puras; a API do SolidWorks usa metros (conversão em _m).
"""

from __future__ import annotations

import math
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
COTAS = RAIZ / "design" / "cad" / "cotas.md"
SAIDA = RAIZ / "design" / "cad"


# ---------------------------------------------------------------- funções puras (testadas)

def ler_cotas(caminho: Path = COTAS) -> dict[str, float]:
    """Lê as cotas da tabela de design/cad/cotas.md.

    Em linguagem simples: percorre as linhas das tabelas em Markdown, fica com as que têm uma chave em minúsculas
    na 1.ª coluna e um número na 2.ª (com vírgula decimal) e devolve um dicionário chave → valor em mm ou graus.
    """
    cotas = {}
    for linha in Path(caminho).read_text(encoding="utf-8").splitlines():
        partes = [p.strip() for p in linha.strip().strip("|").split("|")]
        if len(partes) >= 2 and re.fullmatch(r"[a-z_]+", partes[0]) and re.fullmatch(r"-?\d+(,\d+)?", partes[1]):
            cotas[partes[0]] = float(partes[1].replace(",", "."))
    return cotas


def eixo_colo(c: dict) -> dict:
    """Pontos do colo da haste no plano frontal (x mediolateral, y ao longo da haste; ponta em y = 0).

    Em linguagem simples: o colo sai da haste para o lado medial (x negativo) com o ângulo cervicodiafisário; o
    eixo do colo cruza o eixo da haste à altura B do catálogo e o centro da cabeça fica à distância do offset C do
    eixo da haste (leitura do desenho do catálogo da Corail). Devolve a direção do colo, o centro da cabeça e
    a base do colo (onde o colo encontra o corpo), a uma distância igual ao comprimento do colo.
    """
    a = math.radians(180 - c["haste_ccd"])  # inclinação do colo em relação ao eixo da haste
    d = (-math.sin(a), math.cos(a))
    # o eixo do colo cruza o eixo da haste à altura B do catálogo; o centro da cabeça fica ao offset C dessa linha
    altura_centro = c["haste_comprimento_b"] + c["haste_offset"] / math.tan(a)
    centro = (-c["haste_offset"], altura_centro)
    base = (centro[0] - c["haste_colo"] * d[0], centro[1] - c["haste_colo"] * d[1])
    return {"direcao": d, "centro": centro, "base": base}


def contorno_haste(c: dict) -> list[tuple[float, float]]:
    """Contorno do corpo da haste visto de frente (plano frontal), em mm, fechado.

    Em linguagem simples: a haste afina da largura do ombro até à ponta; o bordo lateral é quase direito e o bordo
    medial curva para dentro (curva do calcar) até à base do colo. Devolve pontos no sentido anti-horário, a
    começar na ponta lateral; o último ponto é igual ao primeiro.
    """
    L, wo, wp = c["haste_comprimento"], c["haste_largura_ombro"], c["haste_largura_ponta"]
    base = eixo_colo(c)["base"]
    lateral = [(wp / 2, 0.0), (wo / 2 - 1.5, 0.75 * L), (wo / 2, L - 6)]
    topo = [(wo / 2 - 4, L), (base[0] + 5, min(base[1] + 8, L - 1))]
    medial = [(base[0], base[1]), (-wo / 2 + 3.5, 0.55 * L), (-wp / 2 - 0.8, 0.22 * L), (-wp / 2, 0.0)]
    pts = lateral + topo + medial
    return pts + [pts[0]]


def perfil_implante(c: dict) -> list[tuple[float, float]]:
    """Meio perfil (raio, altura) do núcleo do implante, para revolução à volta do eixo y. Ápice em y = 0.

    Em linguagem simples: o núcleo tem o diâmetro menor da rosca (diâmetro menos duas profundidades), afina no
    ápice até ao núcleo apical e acaba no topo num colo liso com o diâmetro do implante e um chanfro até à
    conexão. A rosca acrescenta-se depois por varrimento ao longo de uma hélice.
    """
    L, D = c["implante_comprimento"], c["implante_diametro"]
    r_nucleo = D / 2 - c["rosca_profundidade"]
    r_apice = c["apice_nucleo"] / 2
    zona_conica = c["parte_conica"]
    return [
        (0.0, 0.0),
        (r_apice, 0.0),
        (r_nucleo, zona_conica),
        (r_nucleo, L - c["rosca_inicio"]),
        (D / 2, L - c["rosca_inicio"] + 0.4),
        (D / 2, L - c["chanfro_topo"]),
        (c["plataforma_diametro"] / 2, L),
        (0.0, L),
    ]


def perfil_rosca(c: dict) -> list[tuple[float, float]]:
    """Secção do filete da rosca (trapézio) em coordenadas (raio, altura) relativas ao início da hélice.

    Em linguagem simples: o filete sai do núcleo com a profundidade da rosca; os flancos fazem o ângulo do flanco
    com a perpendicular ao eixo. A base entra 0,05 mm no núcleo para os dois sólidos se unirem.
    """
    r0 = c["implante_diametro"] / 2 - c["rosca_profundidade"] - 0.05
    r1 = c["implante_diametro"] / 2
    crista = 0.10  # valor de desenho: largura da crista do filete
    meia_base = crista / 2 + (r1 - r0) * math.tan(math.radians(c["rosca_angulo_flanco"]))
    if 2 * meia_base >= c["rosca_passo"]:
        raise ValueError("o filete é mais largo do que o passo")
    return [(r0, -meia_base), (r1, -crista / 2), (r1, crista / 2), (r0, meia_base)]


def perfil_pilar(c: dict) -> list[tuple[float, float]]:
    """Meio perfil (raio, altura) do pilar, por cima do topo do implante (y = comprimento do implante).

    Em linguagem simples: o pilar alarga na altura gengival até ao seu diâmetro e depois sobe, ligeiramente
    cónico, até à altura total; o topo é arredondado por um chanfro.
    """
    y0 = c["implante_comprimento"]
    r_base = c["conexao_diametro"] / 2
    r = c["pilar_diametro"] / 2
    h, hg = c["pilar_altura"], c["pilar_altura_gengival"]
    return [(0.0, y0), (r_base, y0), (r, y0 + hg), (r * 0.78, y0 + h - 0.4), (r * 0.7, y0 + h), (0.0, y0 + h)]


def perfil_coroa(c: dict) -> list[tuple[float, float]]:
    """Meio perfil (raio, altura) de uma coroa de molar simplificada, para revolução.

    Em linguagem simples: a coroa sai estreita junto à gengiva (perfil de emergência), alarga até à largura da
    coroa a cerca de metade da altura e fecha em cima com a superfície oclusal, mais baixa no centro (fossa).
    As cúspides e os sulcos acrescentam-se depois com cortes.
    """
    y0 = c["implante_comprimento"] + c["pilar_altura_gengival"]
    R, H = c["coroa_largura"] / 2, c["coroa_altura"]
    return [
        (c["pilar_diametro"] / 2 + 0.3, y0),
        (R * 0.86, y0 + 0.30 * H),
        (R, y0 + 0.55 * H),
        (R * 0.93, y0 + 0.82 * H),
        (R * 0.62, y0 + 0.99 * H),
        (R * 0.30, y0 + 0.93 * H),
        (0.0, y0 + 0.86 * H),
    ]


# ---------------------------------------------------------------- SolidWorks (API COM)

def _m(v: float) -> float:
    return v / 1000.0


class Sw:
    """Ligação ao SolidWorks aberto, com conversão dos objetos para as interfaces tipadas."""

    def __init__(self):
        import pythoncom
        from win32com.client import gencache

        self.pythoncom = pythoncom
        self.mod = gencache.EnsureModule("{83A33D31-27C5-11CE-BFD4-00400513BB57}", 0, 33, 0)
        self.c = gencache.EnsureModule("{4687F359-55D0-4CD3-B6CF-2EB42C11F989}", 0, 33, 0).constants
        unk = pythoncom.GetActiveObject("SldWorks.Application")
        self.app = self.mod.ISldWorks(unk.QueryInterface(pythoncom.IID_IDispatch))

    def t(self, obj, interface: str):
        if obj is None:
            return None
        return getattr(self.mod, interface)(obj._oleobj_ if hasattr(obj, "_oleobj_") else obj)

    def nova_peca(self):
        tpl = self.app.GetUserPreferenceStringValue(self.c.swDefaultTemplatePart)
        self.m = self.t(self.app.NewDocument(tpl, 0, 0, 0), "IModelDoc2")
        self.ext = self.t(self.m.Extension, "IModelDocExtension")
        self.sk = self.t(self.m.SketchManager, "ISketchManager")
        self.fm = self.t(self.m.FeatureManager, "IFeatureManager")
        self.sk.AddToDB = True  # cria a geometria sem inferências nem cotas automáticas
        planos, f = [], self.t(self.m.FirstFeature(), "IFeature")
        while f is not None:
            if f.GetTypeName2() == "RefPlane":
                planos.append(f.Name)
            f = self.t(f.GetNextFeature(), "IFeature")
        self.frontal, self.superior, self.direito = planos[:3]

    def ultima(self, nome: str):
        f = self.t(self.m.FeatureByPositionReverse(0), "IFeature")
        f.Name = nome
        return f

    def selecionar(self, nome: str, tipo: str, append=False, marca=0):
        self.ext.SelectByID2(nome, tipo, 0, 0, 0, append, marca, None, 0)

    def esboco(self, plano: str, nome: str, desenhar):
        self.m.ClearSelection2(True)
        self.selecionar(plano, "PLANE")
        self.sk.InsertSketch(True)
        desenhar(self.sk)
        self.sk.InsertSketch(True)
        return self.ultima(nome)

    def polilinha(self, pts, fechar=False):
        p = list(pts) + ([pts[0]] if fechar and pts[0] != pts[-1] else [])
        for a, b in zip(p, p[1:]):
            self.sk.CreateLine(_m(a[0]), _m(a[1]), 0, _m(b[0]), _m(b[1]), 0)

    def spline(self, pts):
        from win32com.client import VARIANT

        dados = [v for x, y in pts for v in (_m(x), _m(y), 0.0)]
        self.sk.CreateSpline2(VARIANT(self.pythoncom.VT_ARRAY | self.pythoncom.VT_R8, dados), True)

    def revolucao(self, esboco: str, nome: str, juntar=True, corte=False):
        self.m.ClearSelection2(True)
        self.selecionar(esboco, "SKETCH")
        f = self.fm.FeatureRevolve2(True, True, False, corte, False, False, 0, 0, 2 * math.pi, 0, False, False,
                                    0, 0, 0, 0, 0, juntar, False, True)
        if f is None:
            raise RuntimeError(f"a revolução '{nome}' falhou")
        self.t(f, "IFeature").Name = nome

    def extrusao_simetrica(self, esboco: str, nome: str, espessura: float, juntar=True):
        self.m.ClearSelection2(True)
        self.selecionar(esboco, "SKETCH")
        mp = self.c.swEndCondMidPlane
        f = self.fm.FeatureExtrusion3(True, False, False, mp, 0, _m(espessura), 0, False, False, False, False,
                                      0, 0, False, False, False, False, juntar, False, True, 0, 0, False)
        if f is None:
            raise RuntimeError(f"a extrusão '{nome}' falhou")
        self.t(f, "IFeature").Name = nome

    def corte_atravessar(self, esboco: str, nome: str):
        self.m.ClearSelection2(True)
        self.selecionar(esboco, "SKETCH")
        tb = self.c.swEndCondThroughAllBoth
        f = self.fm.FeatureCut4(True, False, False, tb, tb, 0, 0, False, False, False, False, 0, 0, False, False,
                                False, False, False, False, True, False, True, False, 0, 0, False, False)
        if f is None:
            raise RuntimeError(f"o corte '{nome}' falhou")
        self.t(f, "IFeature").Name = nome

    def plano_desfasado(self, plano: str, distancia: float, nome: str):
        self.m.ClearSelection2(True)
        self.selecionar(plano, "PLANE")
        if self.fm.InsertRefPlane(self.c.swRefPlaneReferenceConstraint_Distance, _m(distancia), 0, 0, 0, 0) is None:
            raise RuntimeError(f"o plano '{nome}' falhou")
        self.ultima(nome)

    def corpos(self):
        """Corpos sólidos ordenados de baixo para cima (pela altura mínima da caixa envolvente)."""
        parte = self.t(self.m, "IPartDoc")
        corpos = [self.t(b, "IBody2") for b in (parte.GetBodies2(self.c.swSolidBody, False) or [])]
        return sorted(corpos, key=lambda b: (b.GetBodyBox()[1], b.GetBodyBox()[4]))

    def selecionar_arestas(self, filtro):
        """Seleciona as arestas cujo ponto médio cumpre o filtro (x, y, z em mm). Devolve quantas."""
        n = 0
        self.m.ClearSelection2(True)
        for corpo in self.corpos():
            for e in corpo.GetEdges() or []:
                aresta = self.t(e, "IEdge")
                curva = self.t(aresta.GetCurve(), "ICurve")
                par = aresta.GetCurveParams3()
                p = self.t(par, "ICurveParamData") if par is not None else None
                if p is None:
                    continue
                t = (p.UMinValue + p.UMaxValue) / 2
                xyz = curva.Evaluate2(t, 0)
                if xyz and filtro(*(1000 * v for v in xyz[:3])):
                    self.t(aresta, "IEntity").Select4(True, None)
                    n += 1
        return n

    def boleado(self, nome: str, raio: float, filtro):
        """Boleado das arestas escolhidas; se falhar, tenta raios menores (até 35 % do pedido)."""
        for r in (raio, 0.7 * raio, 0.5 * raio, 0.35 * raio):
            if self.selecionar_arestas(filtro) == 0:
                return
            f = self.fm.FeatureFillet3(195, _m(r), 0, 0, 0, 0, 0, None, None, None, None, None, None, None)
            if f is not None:
                self.t(f, "IFeature").Name = nome
                if r != raio:
                    print(f"nota: '{nome}' feito com raio {r:.2f} mm em vez de {raio} mm")
                return
        print(f"aviso: o boleado '{nome}' falhou")

    def chanfro(self, nome: str, distancia: float, filtro):
        if self.selecionar_arestas(filtro) == 0:
            return
        f = self.fm.InsertFeatureChamfer(4, self.c.swChamferAngleDistance, _m(distancia), math.radians(45),
                                         0, 0, 0, 0)
        if f is not None:
            self.t(f, "IFeature").Name = nome
        else:
            print(f"aviso: o chanfro '{nome}' falhou")

    def nomear_corpos(self, nomes):
        for corpo, nome in zip(self.corpos(), nomes):
            corpo.Name = nome

    def guardar(self, nome: str, nomes_corpos):
        SAIDA.mkdir(parents=True, exist_ok=True)
        (SAIDA / "stl").mkdir(exist_ok=True)
        self.m.ForceRebuild3(False)
        self.m.ShowNamedView2("*Isometric", 7)
        self.m.ViewZoomtofit2()
        self.ext.SaveAs3(str(SAIDA / f"{nome}.SLDPRT"), 0, 1, None, None, 0, 0)
        app = self.app
        app.SetUserPreferenceIntegerValue(self.c.swSTLQuality, self.c.swSTLQuality_Custom)
        app.SetUserPreferenceDoubleValue(self.c.swSTLDeviation, 0.00001)
        app.SetUserPreferenceDoubleValue(self.c.swSTLAngleTolerance, math.radians(3))
        app.SetUserPreferenceToggle(self.c.swSTLBinaryFormat, True)
        app.SetUserPreferenceToggle(self.c.swSTLDontTranslateToPositive, True)
        app.SetUserPreferenceIntegerValue(self.c.swExportStlUnits, 0)  # mm
        corpos = self.corpos()
        for i, corpo in enumerate(corpos):
            for j, outro in enumerate(corpos):
                outro.HideBody(j != i)
            destino = SAIDA / "stl" / f"{nome}_{nomes_corpos[i]}.stl"
            self.ext.SaveAs3(str(destino), 0, 1, None, None, 0, 0)
            print("STL", destino.name, destino.exists())
        for corpo in corpos:
            corpo.HideBody(False)
        self.m.Save3(1, 0, 0)


def criar_implante(sw: Sw, c: dict):
    """Implante dentário com rosca helicoidal, pilar e coroa (três corpos)."""
    sw.nova_peca()
    L = c["implante_comprimento"]

    def nucleo(sk):
        sk.CreateCenterLine(0, 0, 0, 0, _m(L + 2), 0)
        sw.polilinha(perfil_implante(c), fechar=True)

    sw.esboco(sw.frontal, "Esboço do perfil do implante", nucleo)
    sw.revolucao("Esboço do perfil do implante", "Revolução do núcleo do implante")

    # hélice: começa no fim do ápice cónico e acaba no colo liso
    y_ini, y_fim = 0.6, L - c["rosca_inicio"] - 0.3
    r_nucleo = c["implante_diametro"] / 2 - c["rosca_profundidade"]
    sw.plano_desfasado(sw.superior, y_ini, "Plano do início da rosca")
    sw.esboco("Plano do início da rosca", "Esboço da base da hélice",
              lambda sk: sk.CreateCircleByRadius(0, 0, 0, _m(r_nucleo)))
    sw.m.ClearSelection2(True)
    sw.selecionar("Esboço da base da hélice", "SKETCH")
    sw.m.InsertHelix(False, True, False, True, sw.c.swHelixDefinedByHeightAndPitch, _m(y_fim - y_ini),
                     _m(c["rosca_passo"]), 0, 0, 0)
    sw.ultima("Hélice da rosca")

    def filete(sk):
        sw.polilinha([(x, y_ini + y) for x, y in perfil_rosca(c)], fechar=True)

    sw.esboco(sw.frontal, "Esboço do perfil do filete", filete)
    sw.m.ClearSelection2(True)
    sw.selecionar("Esboço do perfil do filete", "SKETCH", marca=1)
    sw.selecionar("Hélice da rosca", "REFERENCECURVES", append=True, marca=4)
    f = sw.fm.InsertProtrusionSwept4(False, False, 0, False, False, 0, 0, False, 0, 0, 0, 0, True, False, True,
                                     0, True, False, 0, 0)
    if f is None:
        raise RuntimeError("a rosca (varrimento) falhou")
    sw.t(f, "IFeature").Name = "Rosca helicoidal"

    def apice(sk):
        # tudo o que fica fora do cone do ápice (do diâmetro da rosca apical até ao diâmetro do implante) sai
        sk.CreateCenterLine(0, 0, 0, 0, _m(L), 0)
        r_ap, R = c["apice_rosca"] / 2, c["implante_diametro"] / 2 + 0.2
        h = c["parte_conica"]
        sw.polilinha([(r_ap, -0.01), (R + 0.5, -0.01), (R + 0.5, h), (R, h)], fechar=False)
        sk.CreateLine(_m(R), _m(h), 0, _m(r_ap), _m(-0.01), 0)

    sw.esboco(sw.frontal, "Esboço do ápice cónico", apice)
    sw.revolucao("Esboço do ápice cónico", "Corte do ápice cónico", corte=True)

    sw.chanfro("Chanfro do ápice", 0.2, lambda x, y, z: abs(y) < 0.05)

    sw.esboco(sw.frontal, "Esboço do perfil do pilar", lambda sk: (
        sk.CreateCenterLine(0, _m(L), 0, 0, _m(L + 8), 0), sw.polilinha(perfil_pilar(c), fechar=True)))
    sw.revolucao("Esboço do perfil do pilar", "Revolução do pilar", juntar=False)

    def coroa(sk):
        y0 = L + c["pilar_altura_gengival"]
        sk.CreateCenterLine(0, _m(y0), 0, 0, _m(y0 + 10), 0)
        p = perfil_coroa(c)
        sw.spline(p)
        sk.CreateLine(_m(p[-1][0]), _m(p[-1][1]), 0, 0, _m(y0), 0)
        sk.CreateLine(0, _m(y0), 0, _m(p[0][0]), _m(p[0][1]), 0)

    sw.esboco(sw.frontal, "Esboço do perfil da coroa", coroa)
    sw.revolucao("Esboço do perfil da coroa", "Revolução da coroa", juntar=False)

    # sulcos oclusais: dois cortes estreitos cruzados vistos de cima (só cortam a coroa, que é o corpo de cima)
    y_top = L + c["pilar_altura_gengival"] + c["coroa_altura"]
    sw.plano_desfasado(sw.superior, y_top + 1, "Plano acima da coroa")

    def sulcos(sk):
        # um só contorno em cruz (dois retângulos sobrepostos dariam um contorno inválido)
        w, a = 0.35, 0.62 * c["coroa_largura"] / 2
        sw.polilinha([(w, w), (a, w), (a, -w), (w, -w), (w, -a), (-w, -a), (-w, -w), (-a, -w), (-a, w), (-w, w),
                      (-w, a), (w, a)], fechar=True)

    sw.esboco("Plano acima da coroa", "Esboço dos sulcos oclusais", sulcos)
    sw.m.ClearSelection2(True)
    sw.selecionar("Esboço dos sulcos oclusais", "SKETCH")
    prof = 1 + 0.9  # 1 mm de folga até à coroa mais 0,9 mm de sulco (valor de desenho)
    for inverter in (True, False):
        sw.m.ClearSelection2(True)
        sw.selecionar("Esboço dos sulcos oclusais", "SKETCH")
        f = sw.fm.FeatureCut4(True, False, inverter, 0, 0, _m(prof + 0.6), 0, False, False, False, False, 0, 0,
                              False, False, False, False, False, False, True, False, True, False, 0, 0, False, False)
        if f is not None:
            sw.t(f, "IFeature").Name = "Corte dos sulcos oclusais"
            break
    else:
        print("aviso: o corte dos sulcos oclusais falhou")
    sw.boleado("Boleado dos sulcos", 0.3, lambda x, y, z: y > y_top - 2.5 and abs(x) < 4 and abs(z) < 4)
    sw.nomear_corpos(["Implante", "Pilar", "Coroa"])
    sw.guardar("implante_dentario", ["implante", "pilar", "coroa"])


def criar_haste(sw: Sw, c: dict):
    """Haste femoral: corpo afilado com colo e cone 12/14 (um corpo)."""
    sw.nova_peca()
    L = c["haste_comprimento"]
    col = eixo_colo(c)
    d, base, centro = col["direcao"], col["base"], col["centro"]

    sw.esboco(sw.frontal, "Esboço do contorno da haste", lambda sk: sw.spline_fechada(contorno_haste(c)))
    sw.extrusao_simetrica("Esboço do contorno da haste", "Extrusão do corpo da haste", c["haste_espessura"])

    def afilamento(sk):
        # vista lateral (plano direito: x do esboço = eixo z do modelo): fora da linha que vai de
        # meia espessura no ombro até meia espessura na ponta, de cada lado
        e1, e0 = c["haste_espessura"] / 2, c["haste_espessura_ponta"] / 2
        for s in (1, -1):
            sw.polilinha([(s * e0, -1), (s * (e1 + 10), -1), (s * (e1 + 10), L + 30), (s * e1, L + 30),
                          (s * e1, 0.6 * L)], fechar=False)
            sk.CreateLine(_m(s * e1), _m(0.6 * L), 0, _m(s * e0), _m(-1), 0)

    sw.esboco(sw.direito, "Esboço do afilamento anteroposterior", afilamento)
    sw.corte_atravessar("Esboço do afilamento anteroposterior", "Corte do afilamento anteroposterior")
    sw.boleado("Boleado das arestas do corpo", 2.5, lambda x, y, z: y < L - 2)

    s_cone0 = c["haste_colo"] - c["cone_comprimento"] + 3  # o cone acaba 3 mm além do centro da cabeça

    def colo(sk):
        ini = (base[0] + 12 * d[0] * -1, base[1] + 12 * d[1] * -1)
        fim = (base[0] + s_cone0 * d[0], base[1] + s_cone0 * d[1])
        sk.CreateCenterLine(_m(ini[0]), _m(ini[1]), 0, _m(fim[0]), _m(fim[1]), 0)
        n = (d[1], -d[0])
        r0, r1 = 7.5, 6.4  # valor de desenho: colo cónico, de 15 mm junto ao corpo a 12,8 mm junto ao cone
        q = [ini, (ini[0] + r0 * n[0], ini[1] + r0 * n[1]), (fim[0] + r1 * n[0], fim[1] + r1 * n[1]), fim]
        sw.polilinha(q, fechar=True)

    sw.esboco(sw.frontal, "Esboço do colo", colo)
    sw.revolucao("Esboço do colo", "Revolução do colo")

    def cone(sk):
        a = (base[0] + s_cone0 * d[0], base[1] + s_cone0 * d[1])
        b = (a[0] + c["cone_comprimento"] * d[0], a[1] + c["cone_comprimento"] * d[1])
        sk.CreateCenterLine(_m(a[0]), _m(a[1]), 0, _m(b[0]), _m(b[1]), 0)
        n = (d[1], -d[0])
        R0, R1 = c["cone_maior"] / 2, c["cone_menor"] / 2
        sw.polilinha([a, (a[0] + R0 * n[0], a[1] + R0 * n[1]), (b[0] + R1 * n[0], b[1] + R1 * n[1]), b],
                     fechar=True)

    sw.esboco(sw.frontal, "Esboço do cone 12/14", cone)
    sw.revolucao("Esboço do cone 12/14", "Revolução do cone 12/14")
    ponta = (base[0] + (s_cone0 + c["cone_comprimento"]) * d[0], base[1] + (s_cone0 + c["cone_comprimento"]) * d[1])
    sw.chanfro("Chanfro do cone", 0.8,
               lambda x, y, z: math.hypot(x - ponta[0], y - ponta[1]) < c["cone_menor"] / 2 + 0.5)
    sw.nomear_corpos(["Haste"])
    sw.guardar("haste_femoral", ["haste"])


def _spline_fechada(self, pts):
    from win32com.client import VARIANT

    # contorno em segmentos de spline suaves: lateral, topo e medial (cantos vivos entre eles)
    lateral, topo, medial, ponta = pts[0:3], pts[2:5], pts[4:-1], pts[-2:]
    for troco in (lateral, medial):
        dados = [v for x, y in troco for v in (_m(x), _m(y), 0.0)]
        self.sk.CreateSpline2(VARIANT(self.pythoncom.VT_ARRAY | self.pythoncom.VT_R8, dados), True)
    self.polilinha(topo)
    self.polilinha(ponta)


Sw.spline_fechada = _spline_fechada


def main(argv=None):
    qual = (argv or sys.argv[1:] or ["todos"])[0]
    c = ler_cotas()
    sw = Sw()
    if qual in ("implante", "todos"):
        criar_implante(sw, c)
    if qual in ("haste", "todos"):
        criar_haste(sw, c)


if __name__ == "__main__":
    main()
