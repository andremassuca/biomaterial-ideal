"""Dicionários do OpenFOAM (v2406) para a CFD do stent e para o teste de Poiseuille.

Em linguagem simples: o OpenFOAM lê um caso feito de ficheiros de texto (malha, propriedades do sangue,
condições de fronteira, esquemas numéricos e controlo do tempo). Estas funções escrevem esses textos a partir
dos parâmetros do stent e da malha, para os casos serem reproduzíveis só a partir do código.

Malha de fundo (blockMesh): setor de 180/n_losangos graus, com três blocos (um núcleo junto ao eixo e dois
blocos exteriores com células radiais que ficam mais finas junto à parede). O snappyHexMesh retira depois as
células dentro dos struts e refina à volta deles.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

CABECALHO = """/*--------------------------------*- C++ -*----------------------------------*\\
  Gerado por src/biomat_mcdm/cfd/openfoam.py
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       {classe};
    object      {objeto};
}}
"""


def ficheiro(classe: str, objeto: str, corpo: str) -> str:
    """Texto de um dicionário do OpenFOAM com o cabeçalho FoamFile."""
    return CABECALHO.format(classe=classe, objeto=objeto) + "\n" + corpo.strip() + "\n"


@dataclass(frozen=True)
class Malha:
    """Malha de fundo do setor (mm).

    delta_mm: tamanho das células junto à parede na zona do stent (circunferencial e axial); a célula radial
    junto à parede é metade; nivel_struts: níveis de refinamento do snappyHexMesh à volta dos struts
    (cada nível divide a célula ao meio).
    """

    raio_mm: float
    setor_rad: float
    comprimento_mm: float
    z_stent: tuple[float, float]
    delta_mm: float
    nivel_struts: int = 1
    fracao_nucleo: float = 0.3  # 0,5 dava 2,8 % de erro no perfil junto ao eixo; 0,3 dá 1,5 %


def contagens(m: Malha) -> dict:
    """Número de células por direção na malha de fundo (antes do snappyHexMesh).

    n_h: células em cada metade do arco da parede (delta na parede) e em cada lado do núcleo; n_r: células
    radiais nos blocos exteriores, em progressão geométrica do núcleo (3 delta) até à parede (delta / 2).
    Axial: delta na zona do stent; mais largas à entrada e à saída.
    """
    arco = m.raio_mm * m.setor_rad
    n_h = max(2, int(np.ceil(arco / m.delta_mm / 2)))
    espessura = m.raio_mm * (1 - m.fracao_nucleo)
    w_parede = m.delta_mm / 2
    w_dentro = 3 * m.delta_mm
    # progressão geométrica entre a célula de dentro e a da parede: comprimento ~ n (w1 + w2) / 2
    n_r = max(4, int(np.ceil(espessura / ((w_parede + w_dentro) / 2))))
    z0, z1 = m.z_stent
    n_meio = max(2, int(np.ceil((z1 - z0) / m.delta_mm)))
    n_ent = max(2, int(np.ceil(z0 / (2.5 * m.delta_mm))))
    n_sai = max(2, int(np.ceil((m.comprimento_mm - z1) / (2.5 * m.delta_mm))))
    return {"n_h": n_h, "n_r": n_r, "n_meio": n_meio, "n_ent": n_ent, "n_sai": n_sai,
            "razao_radial": w_parede / w_dentro,
            "n_celulas": (n_h * n_h + 2 * n_h * n_r) * (n_ent + n_meio + n_sai)}


def block_mesh(m: Malha, ciclico: bool = False) -> str:
    """blockMeshDict do setor em mm (convertToMeters 0,001): três blocos.

    Em linguagem simples: um bloco de núcleo junto ao eixo (um quadrilátero com um vértice no eixo) e dois
    blocos exteriores com células radiais que ficam mais finas junto à parede. Não há células degeneradas no
    eixo (uma primeira versão em coordenadas polares, com prismas no eixo, travava o escoamento junto ao eixo e
    falhou o teste de Poiseuille).
    Patches: entrada (z = 0), saida (z = comprimento), parede (r = R), simetria0 e simetria1 (planos dos lados).
    Com ciclico=True, a entrada e a saída ficam ligadas (escoamento periódico).
    """
    c = contagens(m)
    R, f, L = m.raio_mm, m.setor_rad, m.comprimento_mm
    rc = m.fracao_nucleo * R
    h = f / 2
    # vértices: 0 eixo, 1 A (núcleo, plano 0), 2 B (bissetriz), 3 C (núcleo, plano 1), 4-6 parede (0, meio, 1);
    # B fica a rc / cos(f/2) na bissetriz, para AB e BC serem perpendiculares aos planos de simetria
    b = rc / np.cos(h)
    pts2 = [(0.0, 0.0), (rc, 0.0), (b * np.cos(h), b * np.sin(h)), (rc * np.cos(f), rc * np.sin(f)),
            (R, 0.0), (R * np.cos(h), R * np.sin(h)), (R * np.cos(f), R * np.sin(f))]
    nv = len(pts2)
    vert = [(x, y, 0.0) for x, y in pts2] + [(x, y, L) for x, y in pts2]

    def hexa(a, b_, c_, d):
        return f"({a} {b_} {c_} {d} {a + nv} {b_ + nv} {c_ + nv} {d + nv})"

    z0, z1 = m.z_stent
    gz = (f"(({z0 / L:.6f} {c['n_ent']} 0.4) ({(z1 - z0) / L:.6f} {c['n_meio']} 1) "
          f"({(L - z1) / L:.6f} {c['n_sai']} 2.5))")
    nz = c["n_ent"] + c["n_meio"] + c["n_sai"]
    rr = c["razao_radial"]
    blocos = [
        f"hex {hexa(0, 1, 2, 3)} ({c['n_h']} {c['n_h']} {nz}) simpleGrading (1 1 {gz})",
        f"hex {hexa(1, 4, 5, 2)} ({c['n_r']} {c['n_h']} {nz}) simpleGrading ({rr:.6f} 1 {gz})",
        f"hex {hexa(2, 5, 6, 3)} ({c['n_r']} {c['n_h']} {nz}) simpleGrading ({rr:.6f} 1 {gz})",
    ]
    arcos = []
    for k, z in ((0, 0.0), (nv, L)):
        for a, b_, ang in ((4, 5, h / 2), (5, 6, 3 * h / 2)):
            arcos.append(f"arc {a + k} {b_ + k} ({R * np.cos(ang):.9f} {R * np.sin(ang):.9f} {z:.9f})")

    def patch(nome, tipo, faces, extra=""):
        fs = "\n".join(f"            ({' '.join(str(i) for i in q)})" for q in faces)
        return (f"    {nome}\n    {{\n        type {tipo};\n{extra}        faces\n        (\n{fs}\n        );\n"
                f"    }}\n")

    entrada = [(0, 3, 2, 1), (1, 2, 5, 4), (2, 3, 6, 5)]
    saida = [tuple(i + nv for i in q[::-1]) for q in entrada]
    parede = [(4, 5, 5 + nv, 4 + nv), (5, 6, 6 + nv, 5 + nv)]
    sim0 = [(0, 1, 1 + nv, nv), (1, 4, 4 + nv, 1 + nv)]
    sim1 = [(0, nv, 3 + nv, 3), (3, 3 + nv, 6 + nv, 6)]
    if ciclico:
        ent = (patch("entrada", "cyclic", entrada, "        neighbourPatch saida;\n")
               + patch("saida", "cyclic", saida, "        neighbourPatch entrada;\n"))
    else:
        ent = patch("entrada", "patch", entrada) + patch("saida", "patch", saida)
    corpo = (
        "convertToMeters 0.001;\n\nvertices\n(\n"
        + "\n".join(f"    ({x:.9f} {y:.9f} {z:.9f})" for x, y, z in vert)
        + "\n);\n\nblocks\n(\n" + "\n".join("    " + b_ for b_ in blocos) + "\n);\n\nedges\n(\n"
        + "\n".join("    " + a for a in arcos)
        + "\n);\n\nboundary\n(\n" + ent
        + patch("parede", "wall", parede)
        + patch("simetria0", "symmetryPlane", sim0)
        + patch("simetria1", "symmetryPlane", sim1)
        + ");\n"
    )
    return ficheiro("dictionary", "blockMeshDict", corpo)


def snappy(m: Malha, ponto_fluido_mm: tuple[float, float, float]) -> str:
    """snappyHexMeshDict: retira as células dentro dos struts (struts.stl) e refina à volta deles."""
    x, y, z = (v / 1000.0 for v in ponto_fluido_mm)
    n = m.nivel_struts
    corpo = f"""
castellatedMesh true;
snap            true;
addLayers       false;

geometry
{{
    struts.stl
    {{
        type triSurfaceMesh;
        name struts;
    }}
}}

castellatedMeshControls
{{
    maxLocalCells 20000000;
    maxGlobalCells 60000000;
    minRefinementCells 0;
    maxLoadUnbalance 0.10;
    nCellsBetweenLevels 3;
    features ();
    refinementSurfaces
    {{
        struts
        {{
            level ({n} {n});
            patchInfo {{ type wall; }}
        }}
    }}
    resolveFeatureAngle 30;
    refinementRegions
    {{
        struts
        {{
            mode distance;
            levels (({2 * m.delta_mm / 1000.0:.6e} {n}));
        }}
    }}
    locationInMesh ({x:.9e} {y:.9e} {z:.9e});
    allowFreeStandingZoneFaces true;
}}

snapControls
{{
    nSmoothPatch 3;
    tolerance 2.0;
    nSolveIter 50;
    nRelaxIter 5;
    nFeatureSnapIter 10;
    implicitFeatureSnap true;
    explicitFeatureSnap false;
    multiRegionFeatureSnap false;
}}

addLayersControls
{{
    relativeSizes true;
    layers {{}}
    expansionRatio 1.2;
    finalLayerThickness 0.5;
    minThickness 0.1;
    nGrow 0;
    featureAngle 60;
    nRelaxIter 3;
    nSmoothSurfaceNormals 1;
    nSmoothNormals 3;
    nSmoothThickness 10;
    maxFaceThicknessRatio 0.5;
    maxThicknessToMedialRatio 0.3;
    minMedialAxisAngle 90;
    nBufferCellsNoExtrude 0;
    nLayerIter 50;
}}

meshQualityControls
{{
    maxNonOrtho 65;
    maxBoundarySkewness 20;
    maxInternalSkewness 4;
    maxConcave 80;
    minVol 1e-30;
    minTetQuality 1e-30;
    minArea -1;
    minTwist 0.02;
    minDeterminant 0.001;
    minFaceWeight 0.05;
    minVolRatio 0.01;
    minTriangleTwist -1;
    nSmoothScale 4;
    errorReduction 0.75;
}}

mergeTolerance 1e-6;
"""
    return ficheiro("dictionary", "snappyHexMeshDict", corpo)


def fourier_expr(coef: list[tuple[float, float]], frequencia_hz: float) -> str:
    """Expressão do OpenFOAM para o fator da onda: 1 + soma(a_k cos(k w t) + b_k sin(k w t)), t = time()."""
    w = 2 * np.pi * frequencia_hz
    termos = " + ".join(f"({a:.8e})*cos({k}*{w:.10e}*time()) + ({b:.8e})*sin({k}*{w:.10e}*time())"
                        for k, (a, b) in enumerate(coef, start=1))
    return "1.0" + (" + " + termos if termos else "")


def campo_u(raio_m: float, u_media: float, fator_expr: str = "1.0", ciclico: bool = False,
            uniforme: bool = False) -> str:
    """0/U: perfil parabólico à entrada (velocidade média u_media vezes o fator da onda), sem deslizamento nas
    paredes e nos struts, simetria nos lados e saída livre. Com uniforme=True, a entrada tem a mesma velocidade
    em toda a secção (teste do escoamento a desenvolver-se num tubo)."""
    if uniforme:
        ent = (f"    entrada {{ type fixedValue; value uniform (0 0 {u_media:.9e}); }}\n"
               "    saida { type inletOutlet; inletValue uniform (0 0 0); value uniform (0 0 0); }\n")
    elif ciclico:
        ent = "    entrada { type cyclic; }\n    saida { type cyclic; }\n"
    else:
        ent = f"""    entrada
    {{
        type            exprFixedValue;
        value           uniform (0 0 0);
        variables
        (
            "R = {raio_m:.9e}"
            "Um = {u_media:.9e}*({fator_expr})"
        );
        valueExpr       #{{ vector(0, 0, 2*Um*max(1 - (sqr(pos().x()) + sqr(pos().y()))/sqr(R), 0)) #}};
    }}
    saida
    {{
        type            inletOutlet;
        inletValue      uniform (0 0 0);
        value           uniform (0 0 0);
    }}
"""
    corpo = f"""
dimensions      [0 1 -1 0 0 0 0];
internalField   uniform (0 0 {u_media if ciclico else 0.0:.9e});
boundaryField
{{
{ent}    "(parede|struts.*)" {{ type noSlip; }}
    "simetria.*" {{ type symmetryPlane; }}
}}
"""
    return ficheiro("volVectorField", "U", corpo)


def campo_p(ciclico: bool = False) -> str:
    """0/p (pressão cinemática, p/rho): zero à saída; gradiente nulo nas restantes fronteiras."""
    ent = ("    entrada { type cyclic; }\n    saida { type cyclic; }\n" if ciclico else
           "    entrada { type zeroGradient; }\n    saida { type fixedValue; value uniform 0; }\n")
    corpo = f"""
dimensions      [0 2 -2 0 0 0 0];
internalField   uniform 0;
boundaryField
{{
{ent}    "(parede|struts.*)" {{ type zeroGradient; }}
    "simetria.*" {{ type symmetryPlane; }}
}}
"""
    return ficheiro("volScalarField", "p", corpo)


def propriedades(nu_m2s: float) -> dict[str, str]:
    """constant/transportProperties (sangue newtoniano) e constant/turbulenceProperties (laminar)."""
    return {
        "constant/transportProperties": ficheiro(
            "dictionary", "transportProperties", f"transportModel Newtonian;\nnu {nu_m2s:.9e};"),
        "constant/turbulenceProperties": ficheiro(
            "dictionary", "turbulenceProperties", "simulationType laminar;"),
    }


def fv_schemes(transiente: bool) -> str:
    ddt = "backward" if transiente else "steadyState"
    div = "bounded Gauss linearUpwind grad(U)" if not transiente else "Gauss linearUpwind grad(U)"
    corpo = f"""
ddtSchemes {{ default {ddt}; }}
gradSchemes {{ default Gauss linear; grad(U) cellLimited Gauss linear 1; }}
divSchemes
{{
    default none;
    div(phi,U) {div};
    div((nuEff*dev2(T(grad(U))))) Gauss linear;
}}
laplacianSchemes {{ default Gauss linear corrected; }}
interpolationSchemes {{ default linear; }}
snGradSchemes {{ default corrected; }}
wallDist {{ method meshWave; }}
"""
    return ficheiro("dictionary", "fvSchemes", corpo)


def fv_solution(transiente: bool) -> str:
    if transiente:
        alg = """
PIMPLE
{
    nOuterCorrectors 10;
    nCorrectors 2;
    nNonOrthogonalCorrectors 1;
    consistent yes;
    pRefCell 0;
    pRefValue 0;
    residualControl
    {
        U { tolerance 1e-5; relTol 0; }
        p { tolerance 1e-4; relTol 0; }
    }
}
relaxationFactors
{
    fields { p 1; pFinal 1; }
    equations { U 0.9; UFinal 1; }
}
"""
    else:
        alg = """
SIMPLE
{
    nNonOrthogonalCorrectors 1;
    consistent yes;
    pRefCell 0;
    pRefValue 0;
    residualControl { p 1e-5; U 1e-6; }
}
relaxationFactors
{
    fields { p 1; }
    equations { U 0.9; }
}
"""
    # no estacionário, cada iteração só precisa de reduzir o resíduo (relTol); no transiente, a última correção
    # de cada passo resolve até à tolerância absoluta
    rel_p, rel_u = ("0.01", "0") if transiente else ("0.05", "0.1")
    corpo = f"""
solvers
{{
    p
    {{
        solver GAMG;
        smoother DICGaussSeidel;
        nCellsInCoarsestLevel 200;
        tolerance 1e-8;
        relTol {rel_p};
    }}
    pFinal {{ $p; relTol 0; tolerance 1e-8; }}
    U
    {{
        solver smoothSolver;
        smoother symGaussSeidel;
        tolerance 1e-9;
        relTol {rel_u};
    }}
    UFinal {{ $U; relTol 0; }}
}}
""" + alg
    return ficheiro("dictionary", "fvSolution", corpo)


def control_dict(solver: str, fim: float, dt: float, intervalo_escrita: float, inicio_media: float | None = None,
                 patches_parede: str = "(parede struts)") -> str:
    """controlDict com os objetos de função: tensão de corte na parede, médias no tempo e caudais."""
    transiente = inicio_media is not None
    media = ""
    if transiente:
        media = f"""
    magTensao
    {{
        type mag;
        libs (fieldFunctionObjects);
        field wallShearStress;
        executeControl timeStep;
        writeControl writeTime;
    }}
    tensaoParede
    {{
        type surfaceFieldValue;
        libs (fieldFunctionObjects);
        regionType patch;
        name parede;
        operation areaAverage;
        fields (mag(wallShearStress));
        writeControl timeStep;
        writeFields false;
        log false;
    }}
    medias
    {{
        type fieldAverage;
        libs (fieldFunctionObjects);
        timeStart {inicio_media:.9g};
        restartOnRestart false;
        writeControl writeTime;
        fields
        (
            wallShearStress {{ mean on; prime2Mean off; base time; }}
            mag(wallShearStress) {{ mean on; prime2Mean off; base time; }}
        );
    }}
"""
    corpo = f"""
application     {solver};
startFrom       latestTime;
startTime       0;
stopAt          endTime;
endTime         {fim:.9g};
deltaT          {dt:.9g};
writeControl    {"runTime" if solver == "pimpleFoam" else "timeStep"};
writeInterval   {intervalo_escrita:.9g};
purgeWrite      0;
writeFormat     binary;
writePrecision  10;
writeCompression off;
timeFormat      general;
timePrecision   8;
runTimeModifiable false;

functions
{{
    wallShearStress
    {{
        type wallShearStress;
        libs (fieldFunctionObjects);
        patches {patches_parede};
        executeControl timeStep;
        writeControl writeTime;
        log false;
    }}
{media}
    caudais
    {{
        type surfaceFieldValue;
        libs (fieldFunctionObjects);
        regionType patch;
        name entrada;
        operation sum;
        fields (phi);
        writeControl timeStep;
        writeFields false;
        log false;
    }}
    caudalSaida
    {{
        $caudais;
        name saida;
    }}
    pressaoEntrada
    {{
        type surfaceFieldValue;
        libs (fieldFunctionObjects);
        regionType patch;
        name entrada;
        operation areaAverage;
        fields (p);
        writeControl timeStep;
        writeFields false;
        log false;
    }}
}}
"""
    return ficheiro("dictionary", "controlDict", corpo)


def decompose(n: int) -> str:
    return ficheiro("dictionary", "decomposeParDict", f"numberOfSubdomains {n};\nmethod scotch;")


def escrever(pasta: Path, ficheiros: dict[str, str]) -> None:
    """Grava os dicionários na pasta do caso (fins de linha Unix, para o OpenFOAM no contentor)."""
    for rel, texto in ficheiros.items():
        p = Path(pasta) / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(texto)
