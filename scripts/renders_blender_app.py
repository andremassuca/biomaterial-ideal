"""Renders 3D realistas dos dispositivos no Blender (sem janela), com anatomia real e luz de estúdio.

Uso:
    blender -b --factory-startup -P scripts/renders_blender.py -- [--cenas anca,articulacao,stent,stent_arteria,
            scaffold,dentario] [--qualidade teste|rapida|final] [--variantes clara,escura] [--saida PASTA]

Cenas:
- anca: osso da anca e fémur proximal anatómicos (BodyParts3D) em corte coronal, com taça de titânio poroso,
  revestimento de polietileno, cabeça cerâmica inteira e haste (SolidWorks) dentro do canal medular;
- articulacao: a mesma cena, em plano aproximado da articulação;
- stent: stent de Co-Cr em losangos no balão, em plano aproximado com profundidade de campo;
- stent_arteria: stent expandido contra a parede de uma artéria em corte, com placa;
- scaffold: amostra cilíndrica (10 × 7 mm) em giroide, com barra de escala de 2 mm;
- dentario: implante (SolidWorks) com pilar e coroa anatómica de molar, na mandíbula (BodyParts3D) em secção
  bucolingual na zona do 1.º molar, com gengiva e canal mandibular.

O osso é gerado por campos de distância (SDF) a partir das malhas anatómicas: cortical com espessura variável,
esponjoso trabecular em 3D numa camada junto ao plano de corte (trabéculas de cerca de 0,2 mm e poros de cerca de
1 mm) e medula por trás. Luz: HDRI de estúdio (Poly Haven, CC0), três luzes de área e ciclorama. Fontes e
licenças: design/cad/fontes_anatomicas.md; recursos descarregados por scripts/obter_recursos.py.

Os modelos são ilustrações: junto de dados levam o rótulo "Ilustração".
"""

from __future__ import annotations

import argparse
import os
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "scripts"))
import geometria_3d as geo  # noqa: E402
import importlib.util as _ilu  # noqa: E402

_spec = _ilu.spec_from_file_location("cad_solidworks", RAIZ / "scripts" / "cad_solidworks.py")
cad = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(cad)

STL = RAIZ / "design" / "cad" / "stl"
RECURSOS = Path(r"recursos")
OBJ = RECURSOS / "bodyparts3d" / "obj"
PH = RECURSOS / "polyhaven"
FONTE = RAIZ / "design" / "fontes" / "Inter-Regular.ttf"
SAIDA_PADRAO = Path(r"partilha\renders")

QUALIDADE = {
    "teste": {"res": 700, "amostras": 24, "voxel": 2.0},
    "rapida": {"res": 1400, "amostras": 96, "voxel": 1.0},
    "final": {"res": 3840, "amostras": 256, "voxel": 0.7},
    "video": {"res": 1080, "amostras": 32, "voxel": 2.0},  # vídeos a 360°: o pormenor do 4K não se vê a 1080p
}
VOXEL = 1.0


# ---------------------------------------------------------------- campos de distância (nós de geometria)

class Campo:
    """Expressão escalar ligada a um socket dos nós de geometria (com +, -, * e /)."""

    def __init__(self, arv, socket):
        self.arv, self.s = arv, socket

    def _op(self, op, outro=None, troca=False):
        return self.arv.math(op, *((outro, self) if troca else (self, outro)))

    def __add__(self, o): return self._op("ADD", o)
    def __radd__(self, o): return self._op("ADD", o, True)
    def __sub__(self, o): return self._op("SUBTRACT", o)
    def __rsub__(self, o): return self._op("SUBTRACT", o, True)
    def __mul__(self, o): return self._op("MULTIPLY", o)
    def __rmul__(self, o): return self._op("MULTIPLY", o, True)
    def __truediv__(self, o): return self._op("DIVIDE", o)
    def __neg__(self): return self._op("MULTIPLY", -1.0)


class Arvore:
    """Construtor de árvores de nós: funções de distância com dimensões em mm (negativas dentro)."""

    def __init__(self, nome):
        self.ng = bpy.data.node_groups.new(nome, "GeometryNodeTree")
        self.ng.interface.new_socket("Geometria", in_out="OUTPUT", socket_type="NodeSocketGeometry")
        self.N, self.L = self.ng.nodes, self.ng.links
        self.p = self.N.new("GeometryNodeInputPosition").outputs[0]
        sep = self.N.new("ShaderNodeSeparateXYZ")
        self.L.new(self.p, sep.inputs[0])
        self.x, self.y, self.z = (Campo(self, sep.outputs[i]) for i in range(3))
        self._sdf = {}

    def _ligar(self, entrada, v):
        if isinstance(v, Campo):
            self.L.new(v.s, entrada)
        elif v is not None:
            entrada.default_value = v

    def math(self, op, a, b=None, c=None):
        n = self.N.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b, c)):
            self._ligar(n.inputs[i], v)
        return Campo(self, n.outputs[0])

    def vec(self, op, a, b=None, escala=None):
        n = self.N.new("ShaderNodeVectorMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (tuple, list, Vector, np.ndarray)):
                n.inputs[i].default_value = tuple(float(c) for c in v)
            else:
                self.L.new(v, n.inputs[i])
        if escala is not None:
            self._ligar(n.inputs["Scale"], escala)
        saida = n.outputs["Value"] if op in ("LENGTH", "DOT_PRODUCT", "DISTANCE") else n.outputs["Vector"]
        return Campo(self, saida) if saida.type == "VALUE" else saida

    def proj(self, origem, direcao):
        """Coordenada ao longo de uma direção: (p - origem) · direção."""
        return self.vec("DOT_PRODUCT", self.vec("SUBTRACT", self.p, tuple(origem)), tuple(direcao))

    def clamp(self, v, lo, hi):
        return self.math("MAXIMUM", self.math("MINIMUM", v, hi), lo)

    # primitivas
    def esfera(self, c, r):
        return self.vec("LENGTH", self.vec("SUBTRACT", self.p, tuple(c))) - r

    def capsula(self, a, b, r):
        a, b = Vector(tuple(a)), Vector(tuple(b))
        ba = b - a
        pa = self.vec("SUBTRACT", self.p, a)
        h = self.clamp(self.vec("DOT_PRODUCT", pa, ba) / ba.dot(ba), 0.0, 1.0)
        q = self.vec("SUBTRACT", pa, self.vec("SCALE", ba, escala=h))
        return self.vec("LENGTH", q) - r

    def uniao(self, a, b, k=0.0):
        return self.math("SMOOTH_MIN", a, b, k) if k else self.math("MINIMUM", a, b)

    def inter(self, *cs):
        r = cs[0]
        for c in cs[1:]:
            r = self.math("MAXIMUM", r, c)
        return r

    def menos(self, a, b):
        return self.math("MAXIMUM", a, -b)

    def sdf_objeto(self, ob, voxel, banda=60, suavizar=2):
        """Distância com sinal à superfície de uma malha fechada (grelha SDF amostrada na posição)."""
        chave = (ob.name, voxel)
        if chave in self._sdf:
            return self._sdf[chave]
        info = self.N.new("GeometryNodeObjectInfo")
        info.transform_space = "RELATIVE"
        info.inputs["Object"].default_value = ob
        grelha = self.N.new("GeometryNodeMeshToSDFGrid")
        self.L.new(info.outputs["Geometry"], grelha.inputs["Mesh"])
        grelha.inputs["Voxel Size"].default_value = voxel
        grelha.inputs["Band Width"].default_value = banda
        saida = grelha.outputs[0]
        if suavizar:
            lap = self.N.new("GeometryNodeSDFGridLaplacian")
            self.L.new(saida, lap.inputs["Grid"])
            lap.inputs["Iterations"].default_value = suavizar
            saida = lap.outputs[0]
        amostra = self.N.new("GeometryNodeSampleGrid")
        self.L.new(saida, amostra.inputs["Grid"])
        self.L.new(self.p, amostra.inputs["Position"])
        c = Campo(self, amostra.outputs["Value"])
        self._sdf[chave] = c
        return c

    def trabeculas(self, celula=1.0, espessura=0.22, furos=0.58):
        """Rede trabecular 3D: placas finas nas faces das células de Voronoi, perfuradas por um ruído.

        Em linguagem simples: o osso esponjoso é uma rede de placas e barras finas; aqui as placas ficam nas
        fronteiras entre células (tamanho 'celula', em mm) com a 'espessura' dada, e um ruído abre furos nas placas
        (onde o ruído passa de 'furos'), o que dá a mistura de placas e barras do osso real.
        """
        v = self.N.new("ShaderNodeTexVoronoi")
        v.voronoi_dimensions = "3D"
        v.feature = "DISTANCE_TO_EDGE"
        self.L.new(self.p, v.inputs["Vector"])
        v.inputs["Scale"].default_value = 1.0 / celula
        placas = Campo(self, v.outputs["Distance"]) * celula - espessura / 2
        r = self.N.new("ShaderNodeTexNoise")
        self.L.new(self.p, r.inputs["Vector"])
        r.inputs["Scale"].default_value = 0.9 / celula
        r.inputs["Detail"].default_value = 2.0
        ruido = Campo(self, r.outputs[0])
        return self.inter(placas, (ruido - furos) * (2.0 * celula))

    def malha(self, nome, d, minimo, maximo, voxel, nitido=False):
        """Converte o campo d (negativo dentro) num objeto com malha, por volume (cubo de voxels).

        Com nitido, as arestas com mais de 40° entre faces ficam vivas (faces de corte planas e nítidas)."""
        cubo = self.N.new("GeometryNodeVolumeCube")
        self.L.new((-d).s, cubo.inputs["Density"])
        cubo.inputs["Background"].default_value = -1e3
        cubo.inputs["Min"].default_value = tuple(float(v) for v in minimo)
        cubo.inputs["Max"].default_value = tuple(float(v) for v in maximo)
        voxel *= VOXEL
        for i, eixo in enumerate("XYZ"):
            cubo.inputs[f"Resolution {eixo}"].default_value = max(8, int((maximo[i] - minimo[i]) / voxel))
        v2m = self.N.new("GeometryNodeVolumeToMesh")
        self.L.new(cubo.outputs[0], v2m.inputs["Volume"])
        v2m.inputs["Threshold"].default_value = 0.0
        liso = self.N.new("GeometryNodeSetShadeSmooth")
        self.L.new(v2m.outputs[0], liso.inputs["Mesh"])
        self.L.new(liso.outputs[0], self.N.new("NodeGroupOutput").inputs[0])
        ob = bpy.data.objects.new(nome, bpy.data.meshes.new(nome))
        bpy.context.collection.objects.link(ob)
        ob.modifiers.new("Campo", "NODES").node_group = self.ng
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier="Campo")
        _normais_para_fora(ob, nitido)
        print(f"  malha {nome}: {len(ob.data.vertices)} vértices")
        return ob


def _normais_para_fora(ob, nitido=False):
    import bmesh

    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if nitido:
        limite = math.radians(40)
        for e in bm.edges:
            if len(e.link_faces) == 2 and e.calc_face_angle(0) > limite:
                e.smooth = False
    bm.to_mesh(ob.data)
    bm.free()


# ---------------------------------------------------------------- cena, render, luz e câmara

def limpar():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def configurar_render(qualidade: str):
    global VOXEL
    cena = bpy.context.scene
    q = QUALIDADE[qualidade]
    VOXEL = q["voxel"]
    cena.render.engine = "CYCLES"
    pref = bpy.context.preferences.addons["cycles"].preferences
    pref.compute_device_type = "OPTIX"
    pref.get_devices()
    for d in pref.devices:
        d.use = d.type == "OPTIX"
    cena.cycles.device = "GPU"
    cena.cycles.samples = q["amostras"]
    cena.cycles.use_denoising = True
    cena.cycles.denoiser = "OPTIX"
    cena.cycles.max_bounces = 16
    cena.cycles.transmission_bounces = 16
    cena.cycles.glossy_bounces = 8
    cena.render.resolution_y = q["res"]
    cena.render.resolution_x = int(q["res"] * 4 / 3)  # proporcao 4:3 para o cartao da app
    cena.render.film_transparent = False
    cena.render.image_settings.file_format = "PNG"
    cena.render.image_settings.color_mode = "RGB"
    cena.render.image_settings.color_depth = "16"
    cena.view_settings.view_transform = "AgX"
    try:
        cena.view_settings.look = "AgX - Medium High Contrast"
    except TypeError:
        pass


def mundo_hdri(variante: str):
    """Ambiente: HDRI de estúdio (Poly Haven), que dá reflexos claros aos metais nas duas variantes."""
    w = bpy.data.worlds.new("Estúdio")
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapa = nt.nodes.new("ShaderNodeMapping")
    mapa.inputs["Rotation"].default_value = (0, 0, math.radians(110))
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(str(PH / "studio_small_09" / "studio_small_09_2k.hdr"))
    fundo = nt.nodes.new("ShaderNodeBackground")
    fundo.inputs["Strength"].default_value = 0.9 if variante == "clara" else 0.7
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(coord.outputs["Generated"], mapa.inputs["Vector"])
    nt.links.new(mapa.outputs["Vector"], env.inputs["Vector"])
    nt.links.new(env.outputs["Color"], fundo.inputs["Color"])
    nt.links.new(fundo.outputs["Background"], out.inputs["Surface"])


def luz_area(nome, azimute, elevacao, distancia, potencia, tamanho, cor=(1, 1, 1)):
    dados = bpy.data.lights.new(nome, "AREA")
    dados.energy, dados.size, dados.color = potencia, tamanho, cor
    ob = bpy.data.objects.new(nome, dados)
    bpy.context.collection.objects.link(ob)
    a, e = math.radians(azimute), math.radians(elevacao)
    ob.location = (distancia * math.cos(e) * math.sin(a), -distancia * math.cos(e) * math.cos(a),
                   distancia * math.sin(e))
    ob.rotation_euler = (-ob.location).to_track_quat("-Z", "Y").to_euler()
    return ob


def tres_pontos(variante: str):
    luz_area("Luz principal", -40, 38, 6, 380, 3.0)
    luz_area("Luz de enchimento", 60, 10, 6, 110, 5.0)
    luz_area("Luz de recorte", 160, 40, 6, 600 if variante == "escura" else 320, 2.0, (0.92, 0.96, 1.0))


def ciclorama(z_chao: float, variante: str):
    """Fundo de estúdio curvo: chão que sobe para a parede de trás numa curva suave."""
    R, n = 4.0, 24
    perfil = [(-30.0, 0.0), (2.0, 0.0)]
    perfil += [(2.0 + R * math.sin(t), R - R * math.cos(t)) for t in np.linspace(0, math.pi / 2, n)[1:]]
    perfil += [(2.0 + R, 30.0)]
    verts, faces = [], []
    for x in (-40.0, 40.0):
        verts += [(x, y, z_chao + z) for y, z in perfil]
    k = len(perfil)
    faces = [(i, i + 1, k + i + 1, k + i) for i in range(k - 1)]
    ob = malha_de_pontos("Ciclorama", verts, faces)
    for p in ob.data.polygons:
        p.use_smooth = True
    m, _, b = _principled("Fundo")
    cor = (0.72, 0.72, 0.71) if variante == "clara" else (0.018, 0.019, 0.022)
    _set(b, cor=cor, rugosidade=0.55 if variante == "clara" else 0.35)
    aplicar(ob, m)
    return ob


def camara(pontos, azimute=20, elevacao=12, lente=100, margem=0.86, fstop=5.6, foco=None):
    """Câmara apontada à origem, à distância em que os pontos ocupam a fração 'margem' do enquadramento."""
    dados = bpy.data.cameras.new("Câmara")
    dados.lens = lente
    dados.clip_start, dados.clip_end = 0.01, 300
    ob = bpy.data.objects.new("Câmara", dados)
    bpy.context.collection.objects.link(ob)
    cena = bpy.context.scene
    cena.camera = ob
    a, e = math.radians(azimute), math.radians(elevacao)
    direcao = Vector((math.cos(e) * math.sin(a), -math.cos(e) * math.cos(a), math.sin(e)))
    centro = sum(pontos, Vector()) / len(pontos)
    d = 8.0
    for _ in range(5):
        ob.location = centro + direcao * d
        ob.rotation_euler = (-direcao).to_track_quat("-Z", "Y").to_euler()
        bpy.context.view_layer.update()
        ndc = [world_to_camera_view(cena, ob, p) for p in pontos]
        ext = max(max(v.x for v in ndc) - min(v.x for v in ndc), max(v.y for v in ndc) - min(v.y for v in ndc))
        d *= ext / margem
    ob.location = centro + direcao * d
    bpy.context.view_layer.update()
    ndc = [world_to_camera_view(cena, ob, p) for p in pontos]
    dados.shift_x = (max(v.x for v in ndc) + min(v.x for v in ndc)) / 2 - 0.5
    dados.shift_y = (max(v.y for v in ndc) + min(v.y for v in ndc)) / 2 - 0.5
    dados.dof.use_dof = True
    dados.dof.focus_distance = ((foco if foco is not None else centro) - ob.location).length
    dados.dof.aperture_fstop = fstop
    return ob


def pontos_de(objs, limite=6000):
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for o in objs:
        ev = o.evaluated_get(dg)
        if ev.type == "MESH":
            me = ev.to_mesh()
            passo = max(1, len(me.vertices) // limite)
            pts += [ev.matrix_world @ me.vertices[i].co for i in range(0, len(me.vertices), passo)]
            ev.to_mesh_clear()
        else:
            pts += [ev.matrix_world @ Vector(c) for c in ev.bound_box]
    return pts


def normalizar(objs, rotacao: Matrix):
    """Junta os objetos numa raiz, roda-os (matriz 3 × 3) e escala-os para caberem numa esfera de raio 1."""
    raiz = bpy.data.objects.new("Raiz", None)
    bpy.context.collection.objects.link(raiz)
    for o in objs:
        o.parent = raiz
    raiz.matrix_world = rotacao.to_4x4()
    bpy.context.view_layer.update()
    pts = pontos_de(objs, 3000)
    mn = Vector([min(p[i] for p in pts) for i in range(3)])
    mx = Vector([max(p[i] for p in pts) for i in range(3)])
    centro, raio = (mn + mx) / 2, (mx - mn).length / 2
    raiz.matrix_world = Matrix.Translation(-centro / raio) @ Matrix.Scale(1 / raio, 4) @ rotacao.to_4x4()
    bpy.context.view_layer.update()
    return raiz, (mn.z - centro.z) / raio


# ---------------------------------------------------------------- materiais PBR

def _principled(nome):
    m = bpy.data.materials.new(nome)
    m.use_nodes = True
    return m, m.node_tree, m.node_tree.nodes["Principled BSDF"]


def _set(bsdf, **kw):
    nomes = {"cor": "Base Color", "metal": "Metallic", "rugosidade": "Roughness", "aniso": "Anisotropic",
             "sss": "Subsurface Weight", "sss_raio": "Subsurface Radius", "sss_escala": "Subsurface Scale",
             "transmissao": "Transmission Weight", "ior": "IOR", "verniz": "Coat Weight",
             "verniz_rug": "Coat Roughness", "brilho": "Specular IOR Level", "alfa": "Alpha"}
    for k, v in kw.items():
        bsdf.inputs[nomes[k]].default_value = tuple(v) + (1,) if k == "cor" and len(v) == 3 else v


def _textura(nt, ficheiro, escala, cor=False):
    """Imagem em projeção de caixa sobre as coordenadas do objeto (mm), com a escala dada."""
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapa = nt.nodes.new("ShaderNodeMapping")
    mapa.inputs["Scale"].default_value = (escala, escala, escala)
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(ficheiro), check_existing=True)
    if not cor:
        tex.image.colorspace_settings.name = "Non-Color"
    tex.projection = "BOX"
    tex.projection_blend = 0.3
    nt.links.new(coord.outputs["Object"], mapa.inputs["Vector"])
    nt.links.new(mapa.outputs["Vector"], tex.inputs["Vector"])
    return tex


def _normal_map(nt, bsdf, ficheiro, escala, forca, bump_altura=None, bump_forca=0.0, bump_dist=0.05):
    tex = _textura(nt, ficheiro, escala)
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.inputs["Strength"].default_value = forca
    nt.links.new(tex.outputs["Color"], nm.inputs["Color"])
    normal = nm.outputs["Normal"]
    if bump_altura is not None:
        b = nt.nodes.new("ShaderNodeBump")
        b.inputs["Strength"].default_value = bump_forca
        b.inputs["Distance"].default_value = bump_dist
        nt.links.new(bump_altura, b.inputs["Height"])
        nt.links.new(normal, b.inputs["Normal"])
        normal = b.outputs["Normal"]
    nt.links.new(normal, bsdf.inputs["Normal"])


def _rugosidade_mapa(nt, bsdf, ficheiro, escala, lo, hi):
    tex = _textura(nt, ficheiro, escala)
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["To Min"].default_value, mr.inputs["To Max"].default_value = lo, hi
    nt.links.new(tex.outputs["Color"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], bsdf.inputs["Roughness"])


def mat_titanio_escovado():
    m, nt, b = _principled("Titânio escovado")
    _set(b, cor=(0.60, 0.58, 0.55), metal=1, aniso=0.8)
    _rugosidade_mapa(nt, b, PH / "metal_plate" / "metal_plate_rough_2k.jpg", 0.05, 0.20, 0.32)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    mapa = nt.nodes.new("ShaderNodeMapping")
    mapa.inputs["Scale"].default_value = (8, 0.06, 8)  # riscos ao longo do eixo y do modelo (eixo da peça)
    ruido = nt.nodes.new("ShaderNodeTexNoise")
    ruido.inputs["Scale"].default_value = 60
    ruido.inputs["Detail"].default_value = 10
    nt.links.new(coord.outputs["Object"], mapa.inputs["Vector"])
    nt.links.new(mapa.outputs["Vector"], ruido.inputs["Vector"])
    _normal_map(nt, b, PH / "metal_plate" / "metal_plate_nor_gl_2k.jpg", 0.05, 0.15, ruido.outputs[0], 0.12, 0.02)
    tang = nt.nodes.new("ShaderNodeTangent")
    tang.direction_type, tang.axis = "RADIAL", "Y"
    nt.links.new(tang.outputs["Tangent"], b.inputs["Tangent"])
    return m


def mat_cocr_polido():
    m, nt, b = _principled("Co-Cr polido")
    _set(b, cor=(0.76, 0.77, 0.80), metal=1)
    _rugosidade_mapa(nt, b, PH / "metal_plate" / "metal_plate_rough_2k.jpg", 0.4, 0.03, 0.07)
    return m


def mat_titanio_poroso():
    m, nt, b = _principled("Titânio poroso")
    _set(b, cor=(0.80, 0.81, 0.84), metal=1, rugosidade=0.07)
    return m


def mat_ceramica(nome, cor):
    m, nt, b = _principled(nome)
    _set(b, cor=cor, rugosidade=0.06, verniz=0.8, verniz_rug=0.02, sss=0.15, sss_raio=(0.8, 0.5, 0.35),
         sss_escala=0.4)
    return m


def mat_liner_espelhado():
    m, nt, b = _principled("Taça polida")
    _set(b, cor=(0.88, 0.89, 0.91), metal=1, rugosidade=0.05)
    return m


def mat_polietileno():
    m, nt, b = _principled("Polietileno")
    _set(b, cor=(0.96, 0.97, 0.98), rugosidade=0.18, verniz=0.4, verniz_rug=0.08, sss=0.8, sss_raio=(1.0, 1.0, 1.0), sss_escala=2.0)
    _normal_map(nt, b, PH / "clay_plaster" / "clay_plaster_nor_gl_2k.jpg", 0.3, 0.08)
    return m


def mat_osso_cortical():
    m, nt, b = _principled("Osso cortical")
    _set(b, cor=(0.74, 0.63, 0.45), rugosidade=0.62, sss=0.25, sss_raio=(1.0, 0.55, 0.3), sss_escala=1.0)
    _normal_map(nt, b, PH / "clay_plaster" / "clay_plaster_nor_gl_2k.jpg", 0.06, 0.6)
    return m


def mat_osso_esponjoso():
    """Trabéculas (geometria 3D): osso claro, um pouco mais rosado do que o cortical."""
    m, nt, b = _principled("Osso esponjoso")
    _set(b, cor=(0.80, 0.68, 0.50), rugosidade=0.7, sss=0.3, sss_raio=(1.0, 0.45, 0.25), sss_escala=0.5)
    return m


def mat_osso_esponjoso_textura(escala=0.6):
    """Face de corte do esponjoso longe da articulação (sem geometria trabecular): padrão de Voronoi."""
    m, nt, b = _principled("Osso esponjoso (face)")
    _set(b, rugosidade=0.7, sss=0.1, sss_raio=(1.0, 0.5, 0.3))
    coord = nt.nodes.new("ShaderNodeTexCoord")
    v = nt.nodes.new("ShaderNodeTexVoronoi")
    v.feature = "DISTANCE_TO_EDGE"
    v.inputs["Scale"].default_value = escala
    nt.links.new(coord.outputs["Object"], v.inputs["Vector"])
    rampa = nt.nodes.new("ShaderNodeValToRGB")
    els = rampa.color_ramp.elements
    els[0].position, els[0].color = 0.05, (0.84, 0.74, 0.57, 1)
    els[1].position, els[1].color = 0.12, (0.45, 0.14, 0.09, 1)
    nt.links.new(v.outputs["Distance"], rampa.inputs["Fac"])
    nt.links.new(rampa.outputs["Color"], b.inputs["Base Color"])
    return m


def mat_medula(amarela=False):
    """Medula: vermelha nos espaços do esponjoso, amarela no canal da diáfise."""
    m, _, b = _principled("Medula amarela" if amarela else "Medula vermelha")
    cor = (0.86, 0.62, 0.25) if amarela else (0.55, 0.09, 0.07)
    _set(b, cor=cor, rugosidade=0.45, sss=0.6, sss_raio=(1.0, 0.4, 0.2), sss_escala=1.5)
    return m


def mat_scaffold():
    m, nt, b = _principled("Cerâmica porosa")
    _set(b, cor=(0.80, 0.79, 0.76), rugosidade=0.78, sss=0.3, sss_raio=(0.3, 0.25, 0.2), sss_escala=0.25)
    _normal_map(nt, b, PH / "clay_plaster" / "clay_plaster_nor_gl_2k.jpg", 0.9, 0.7)
    return m


def mat_balao():
    m, _, b = _principled("Balão")
    _set(b, cor=(0.78, 0.82, 0.86), rugosidade=0.45, transmissao=0.8, ior=1.5, sss=0.25, sss_raio=(0.6, 0.8, 1.0),
         sss_escala=0.3)  # polímero de brilho mate
    return m


def mat_cateter():
    m, _, b = _principled("Cateter")
    _set(b, cor=(0.07, 0.20, 0.42), rugosidade=0.25, verniz=0.5)
    return m


def mat_gengiva(z_osso=-6.0, z_margem=3.0):
    """Gengiva: translúcida, mais vermelha junto ao osso e mais clara e rosada na margem, com textura de mucosa.

    O gradiente usa a coordenada z do objeto (eixo do dente no referencial da cena dentária, em mm)."""
    m, nt, b = _principled("Gengiva")
    _set(b, rugosidade=0.3, sss=0.75, sss_raio=(1.0, 0.25, 0.15), sss_escala=0.8, verniz=0.25, verniz_rug=0.15)
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.inputs["From Min"].default_value, mr.inputs["From Max"].default_value = z_osso, z_margem
    rampa = nt.nodes.new("ShaderNodeValToRGB")
    els = rampa.color_ramp.elements
    els[0].color = (0.60, 0.14, 0.17, 1)
    els[1].color = (0.92, 0.62, 0.62, 1)
    nt.links.new(coord.outputs["Object"], sep.inputs[0])
    nt.links.new(sep.outputs["Z"], mr.inputs["Value"])
    nt.links.new(mr.outputs["Result"], rampa.inputs["Fac"])
    nt.links.new(rampa.outputs["Color"], b.inputs["Base Color"])
    pontilhado = nt.nodes.new("ShaderNodeTexVoronoi")  # pontilhado da gengiva aderida
    pontilhado.inputs["Scale"].default_value = 6.0
    nt.links.new(coord.outputs["Object"], pontilhado.inputs["Vector"])
    _normal_map(nt, b, PH / "clay_plaster" / "clay_plaster_nor_gl_2k.jpg", 0.5, 0.2, pontilhado.outputs["Distance"],
                0.25, 0.05)
    return m


def mat_esmalte():
    m, _, b = _principled("Esmalte")
    _set(b, cor=(0.92, 0.89, 0.80), rugosidade=0.12, verniz=0.5, sss=0.35, sss_raio=(0.9, 0.7, 0.5), sss_escala=0.4)
    return m


def mat_nervo():
    m, _, b = _principled("Nervo")
    _set(b, cor=(0.93, 0.80, 0.42), rugosidade=0.5, sss=0.5, sss_raio=(1.0, 0.7, 0.3))
    return m


def mat_arteria():
    m, _, b = _principled("Parede arterial")
    _set(b, cor=(0.72, 0.18, 0.17), rugosidade=0.3, sss=0.7, sss_raio=(1.0, 0.25, 0.15), sss_escala=0.25,
         transmissao=0.15)
    return m


def mat_intima():
    m, _, b = _principled("Íntima")
    _set(b, cor=(0.86, 0.62, 0.60), rugosidade=0.25, sss=0.6, sss_raio=(1.0, 0.5, 0.4), sss_escala=0.15)
    return m


def mat_adventicia():
    m, _, b = _principled("Adventícia")
    _set(b, cor=(0.86, 0.72, 0.58), rugosidade=0.55, sss=0.5, sss_raio=(1.0, 0.7, 0.5), sss_escala=0.2)
    return m


def mat_placa():
    m, _, b = _principled("Placa")
    _set(b, cor=(0.92, 0.72, 0.30), rugosidade=0.45, sss=0.7, sss_raio=(1.0, 0.8, 0.4), sss_escala=0.4)
    return m


def mat_calcificacao():
    m, _, b = _principled("Calcificação")
    _set(b, cor=(0.95, 0.94, 0.90), rugosidade=0.8)
    return m


def mat_escala(variante):
    m, _, b = _principled("Barra de escala")
    _set(b, cor=(0.05, 0.05, 0.06) if variante == "clara" else (0.9, 0.9, 0.9), rugosidade=0.6)
    return m


def aplicar(ob, mat):
    ob.data.materials.clear()
    ob.data.materials.append(mat)
    return ob


# ---------------------------------------------------------------- geometria auxiliar

def malha_de_pontos(nome, verts, faces):
    me = bpy.data.meshes.new(nome)
    me.from_pydata([tuple(float(c) for c in v) for v in verts], [], faces)
    me.update()
    ob = bpy.data.objects.new(nome, me)
    bpy.context.collection.objects.link(ob)
    return ob


def revolucao(nome, perfil, segmentos=128):
    """Sólido de revolução de um perfil (r, h) à volta do eixo z (perfil a começar e acabar no eixo)."""
    import bmesh

    verts, faces = [], []
    n = len(perfil)
    for i in range(segmentos):
        a = 2 * math.pi * i / segmentos
        verts += [(r * math.cos(a), r * math.sin(a), h) for r, h in perfil]
    for i in range(segmentos):
        j = (i + 1) % segmentos
        faces += [(i * n + k, j * n + k, j * n + k + 1, i * n + k + 1) for k in range(n - 1)]
    ob = malha_de_pontos(nome, verts, faces)
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    for p in ob.data.polygons:
        p.use_smooth = True
    return ob


def esfera(nome, centro, r):
    perfil = [(r * math.sin(math.radians(a)), -r * math.cos(math.radians(a))) for a in np.linspace(0, 180, 91)]
    ob = revolucao(nome, perfil, 160)
    ob.location = tuple(float(c) for c in centro)
    return ob


def importar_stl(nome, matriz=None):
    """Importa um STL do SolidWorks e funde os vértices repetidos (o STL traz cada triângulo solto)."""
    import bmesh

    bpy.ops.wm.stl_import(filepath=str(STL / f"{nome}.STL"))
    ob = bpy.context.selected_objects[0]
    ob.name = nome
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        f.smooth = True
    for e in bm.edges:  # arestas vivas marcadas (a malha fica fechada, o que a grelha SDF exige)
        if len(e.link_faces) == 2 and e.calc_face_angle(0) > math.radians(35):
            e.smooth = False
    bm.to_mesh(ob.data)
    bm.free()
    if matriz is not None:
        ob.matrix_world = matriz
    return ob


def importar_obj(fj):
    """Importa uma malha do BodyParts3D (mm, z para cima), escondida: serve de fonte aos campos."""
    import bmesh

    bpy.ops.wm.obj_import(filepath=str(OBJ / f"{fj}.obj"), forward_axis="Y", up_axis="Z")
    ob = bpy.context.selected_objects[0]
    ob.name = fj
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(ob.data)
    bm.free()
    ob.hide_render = ob.hide_viewport = True
    return ob


def vertices(ob):
    return np.array([tuple(ob.matrix_world @ v.co) for v in ob.data.vertices])


def matriz_base(origem, ex, ey, ez):
    m = Matrix.Identity(4)
    for i, v in enumerate((ex, ey, ez)):
        m.col[i][:3] = [float(c) for c in v]
    m.col[3][:3] = [float(c) for c in origem]
    return m


def texto_3d(corpo, tamanho, mat):
    cu = bpy.data.curves.new("Texto", "FONT")
    cu.body = corpo
    cu.size = tamanho
    if FONTE.exists():
        cu.font = bpy.data.fonts.load(str(FONTE), check_existing=True)
    cu.align_x = "CENTER"
    cu.extrude = tamanho * 0.04
    ob = bpy.data.objects.new("Texto", cu)
    bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


# ---------------------------------------------------------------- cena da anca

def _cabeca_e_eixo(vf):
    topo = vf[:, 2].max()
    cand = vf[(vf[:, 2] > topo - 50) & (vf[:, 0] > np.percentile(vf[:, 0], 70))]
    H, r = geo.ajustar_esfera(cand)
    for _ in range(4):
        H, r = geo.ajustar_esfera(vf[np.abs(np.linalg.norm(vf - H, axis=1) - r) < 3])
    # eixo do canal na diáfise proximal (de 70 a 230 mm abaixo da cabeça), onde fica a haste
    C0, a = geo.eixo_principal(vf[(vf[:, 2] > H[2] - 230) & (vf[:, 2] < H[2] - 70)])
    return H, r, C0, a


def _montagem_anca():
    """Lê a anatomia e calcula as posições: centro da cabeça, eixo do canal, haste e taça.

    A cena passa para um referencial local: origem no centro da cabeça do fémur e plano y = 0 igual ao plano que
    contém o centro da cabeça e o eixo da diáfise (o plano médio da haste). O corte fica nesse plano (fica a metade
    de trás, y >= 0), e a câmara olha de frente (de y negativo). Medidas em mm."""
    femur, anca = importar_obj("FJ3365"), importar_obj("FJ3152")
    H, r, C0, a = _cabeca_e_eixo(vertices(femur))
    n = np.cross(H - C0, a)
    n /= np.linalg.norm(n)
    if n[1] > 0:  # normal do corte virada para a frente (anterior é y negativo no BodyParts3D)
        n = -n
    ey = -n
    ez = np.array([0, 0, 1.0]) - ey[2] * ey
    ez /= np.linalg.norm(ez)
    ex = np.cross(ey, ez)
    R = Matrix((tuple(ex), tuple(ey), tuple(ez)))
    local = Matrix.Translation(-(R @ Vector(tuple(H)))) @ R.to_4x4()
    for o in (femur, anca):
        o.matrix_world = local
    bpy.context.view_layer.update()
    H, r, C0, a = _cabeca_e_eixo(vertices(femur))
    Rn = np.array(R)
    cotas = cad.ler_cotas()
    colo = cad.eixo_colo(cotas)  # geometria da haste no referencial dela (x medial negativo, y ao longo da haste)
    T, s, med = geo.colocar_haste(H, C0, a, altura=colo["centro"][1], offset=cotas["haste_offset"])
    hx, hy = -med, s
    M = matriz_base(T, hx, hy, np.cross(hx, hy))
    d_colo = -colo["direcao"][0] * med + colo["direcao"][1] * s
    base_colo = T + colo["base"][1] * s - colo["base"][0] * med
    lateral = Rn @ np.array([-1.0, 0, 0])  # lado direito do corpo: lateral é x negativo
    anterior = Rn @ np.array([0, -1.0, 0])
    cima = Rn @ np.array([0, 0, 1.0])
    incl, antev = math.radians(40), math.radians(15)
    abertura = -math.cos(incl) * cima + math.sin(incl) * lateral
    abertura = math.cos(antev) * abertura + math.sin(antev) * anterior
    abertura /= np.linalg.norm(abertura)
    print(f"  cabeça femoral: centro local {H.round(2)}, raio {r:.1f} mm")
    return {"femur": femur, "anca": anca, "H": H, "r": r, "M": M, "T": T, "s": s, "med": med,
            "d_colo": d_colo, "base_colo": base_colo, "abertura": abertura, "anterior": np.array([0, -1.0, 0])}


def cena_anca(pormenor=False):
    g = _montagem_anca()
    H, s, T, anterior = g["H"], g["s"], g["T"], g["anterior"]
    haste = aplicar(importar_stl("haste_femoral_haste", g["M"]), mat_titanio_escovado())
    cabeca = aplicar(esfera("Cabeça", H, 16.0), mat_ceramica("Cerâmica (cabeça)", (0.91, 0.78, 0.76)))
    R_ext, R_int, R_pe = 27.0, 23.5, 16.1  # taça de 54 mm (acetábulo com raio de 27,4 mm na malha)

    def corte(a, d):  # corte coronal pelo centro da cabeça: fica a metade de trás
        return a.inter(d, a.proj(H, anterior))

    def femur_campos(a, interior=False):
        f = a.sdf_objeto(g["femur"], 0.5, 70)
        f = a.inter(f, a.proj(T - 100 * s, -s))  # corte da diáfise, 100 mm abaixo da ponta da haste
        # altura ao longo da haste medida a partir do centro da cabeça (anatomia), somada de 146 mm para manter os
        # limiares em relação à metáfise: esponjoso acima de h = 50 (96 mm abaixo da cabeça) e cortical a afinar
        # entre 91 e 51 mm abaixo da cabeça (valores de desenho)
        h = a.proj(H, s) + 146.0
        if interior:
            esp = a.clamp((95 - h) / 40, 0.0, 1.0) * 3.0 + 1.8  # cortical: 4,8 mm na diáfise, 1,8 mm em cima
            f = f + esp
        plano = a.proj(g["base_colo"] + 3 * g["d_colo"], g["d_colo"])
        eixo = a.capsula(g["base_colo"] - 60 * g["d_colo"], g["base_colo"] + 90 * g["d_colo"], 0.0)
        f = a.menos(f, a.inter(-plano, eixo - 24))  # osteotomia do colo (cilindro estreito: poupa o trocânter)
        return a.menos(f, a.sdf_objeto(haste, 0.3, 20, 0)), h

    def anca_campos(a, interior=False):
        d = a.sdf_objeto(g["anca"], 0.5, 70)
        if interior:
            d = d + 1.6
        return a.menos(d, a.esfera(H, R_ext))  # fresagem do acetábulo

    objs = [haste, cabeca]
    caixa = (H - np.array([95, 1, 285]), H + np.array([95, 70, 155]))  # só a metade de trás (depois do corte)
    # osso cortical (fémur e anca)
    a = Arvore("Cortical")
    f, _ = femur_campos(a)
    fi, _ = femur_campos(a, True)
    ac, aci = anca_campos(a), anca_campos(a, True)
    cort = a.uniao(a.menos(f, fi), a.menos(ac, aci))
    objs.append(aplicar(a.malha("Osso cortical", corte(a, cort), *caixa, 0.6), mat_osso_cortical()))
    # esponjoso: geometria trabecular numa camada de 2,5 mm atrás do corte, perto da articulação
    cam = 2.5
    perto = 55.0
    b = Arvore("Trabéculas")
    fi, h = femur_campos(b, True)
    regiao = b.uniao(b.inter(fi, 50 - h), anca_campos(b, True))
    camada = b.inter(corte(b, regiao), b.proj(H + cam * (-anterior), -anterior), b.esfera(H, perto))
    tmin, tmax = H - np.array([perto, 0.5, perto]), H + np.array([perto, cam + 0.5, perto])
    objs.append(aplicar(b.malha("Trabéculas", b.inter(camada, b.trabeculas(1.1, 0.2, 0.5)), tmin, tmax, 0.1),
                        mat_osso_esponjoso()))
    # medula vermelha atrás das trabéculas; face do esponjoso longe da articulação com textura
    c = Arvore("Medula")
    fi, h = femur_campos(c, True)
    regiao = c.uniao(c.inter(fi, 50 - h), anca_campos(c, True))
    atras = c.inter(regiao, c.proj(H + (cam - 0.6) * (-anterior), anterior))
    objs.append(aplicar(c.malha("Medula", c.inter(corte(c, atras), c.esfera(H, perto)), *caixa, 0.7),
                        mat_medula()))
    e = Arvore("Esponjoso (face)")
    fi, h = femur_campos(e, True)
    regiao = e.uniao(e.inter(fi, 50 - h), anca_campos(e, True))
    longe = e.inter(corte(e, regiao), -e.esfera(H, perto - 0.4))
    objs.append(aplicar(e.malha("Esponjoso (face)", longe, *caixa, 0.7), mat_osso_esponjoso_textura()))
    # canal medular da diáfise com medula amarela
    k = Arvore("Medula amarela")
    fi, h = femur_campos(k, True)
    objs.append(aplicar(k.malha("Medula amarela", corte(k, k.inter(fi, h - 50)), *caixa, 0.7), mat_medula(True)))
    # taça (titânio poroso) e revestimento (polietileno), cortados
    q = Arvore("Taça")
    q_ab = q.proj(H, g["abertura"])
    rug = q.N.new("ShaderNodeTexNoise")
    q.L.new(q.p, rug.inputs["Vector"])
    rug.inputs["Scale"].default_value = 1.6
    poros = Campo(q, rug.outputs[0]) * 0.5
    taca = q.inter(q.esfera(H, R_ext - 0.25) - poros, R_int - q.vec("LENGTH", q.vec("SUBTRACT", q.p, tuple(H))),
                   q_ab)
    objs.append(aplicar(q.malha("Taça", corte(q, taca), H - np.array([30, 0.5, 30]), H + 30, 0.15),
                        mat_titanio_poroso()))
    w = Arvore("Revestimento")
    w_ab = w.proj(H, g["abertura"])
    rev = w.inter(w.esfera(H, R_int - 0.05), R_pe - w.vec("LENGTH", w.vec("SUBTRACT", w.p, tuple(H))), w_ab - 1.5)
    objs.append(aplicar(w.malha("Revestimento", corte(w, rev), H - np.array([26, 0.5, 26]), H + 26, 0.12),
                        mat_liner_espelhado()))

    if pormenor == "haste":  # articulação com a haste inteira no canal
        ponto = [Vector(tuple(H + 34 * v)) for v in np.vstack([np.eye(3), -np.eye(3)])] + pontos_de([haste]) + [haste.matrix_world @ Vector(c) for c in haste.bound_box]
        ponto += [Vector(tuple(H + np.array([-25, 0, 25]))), Vector(tuple(H + np.array([55, 0, 45])))]
    elif pormenor == "meia":  # articulação com a haste inteira, vista rodada (rolamento) para encher o 4:3
        ponto = [Vector(tuple(H + 34 * v)) for v in np.vstack([np.eye(3), -np.eye(3)])] + pontos_de([haste]) + [haste.matrix_world @ Vector(c) for c in haste.bound_box]
        ponto += [Vector(tuple(H + np.array([-25, 0, 25]))), Vector(tuple(H + np.array([55, 0, 45])))]
    elif pormenor:  # articulação: cabeça, taça e acetábulo à volta, com a haste só até à base do colo
        ponto = [Vector(tuple(H + 38 * v)) for v in np.vstack([np.eye(3), -np.eye(3)])]
    else:  # conjunto: fémur da ponta da haste para cima, acetábulo e parte do ilíaco
        # o ponto 150 mm acima da cabeça mantém a crista ilíaca dentro do quadro
        ponto = [Vector(tuple(p)) for p in (H + np.array([60, 0, 75]), H + np.array([-70, 0, 75]),
                                            H + np.array([0, 0, 150]),
                                            T - 100 * s + np.array([0, 0, 0]), H + np.array([60, 0, -60]))]
    cam_cfg = {"azimute": 14, "elevacao": 6, "lente": 100, "fstop": 4.0 if pormenor else 8.0, "margem": float(os.environ.get("MARGEM", "0.82")) if pormenor in ("haste", "meia") else 0.8}
    roll = {"haste": float(os.environ.get("ROLL_ANCA", "0")), "meia": float(os.environ.get("ROLL_ART", "0"))}.get(pormenor, 0.0)
    return objs, Matrix.Rotation(math.radians(roll), 3, "Y"), cam_cfg, ponto, Vector(tuple(H))


# ---------------------------------------------------------------- outras cenas

def cena_stent(arteria=False):
    raio = 1.75 if arteria else 1.62
    linhas = geo.rede_stent(raio=raio, comprimento=16, n_coroas=8, n_picos=8, folga=0.0)
    cu = bpy.data.curves.new("Stent", "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.085
    cu.bevel_resolution = 4
    for pts in linhas:
        sp = cu.splines.new("POLY")
        sp.points.add(len(pts) - 1)
        for p, (x, y, z) in zip(sp.points, pts):
            p.co = (x, y, z - 8, 1)
    stent = bpy.data.objects.new("Stent", cu)
    bpy.context.collection.objects.link(stent)
    stent.data.materials.append(mat_cocr_polido())
    objs = [stent]
    if not arteria:
        perfil = geo.perfil_balao(raio=1.52, comprimento=19, cone=3, raio_cateter=0.45)
        objs.append(aplicar(revolucao("Balão", [(0.0, perfil[0][1] - 9.5)] + [(r, h - 9.5) for r, h in perfil]
                                      + [(0.0, perfil[-1][1] - 9.5)]), mat_balao()))
        objs.append(aplicar(revolucao("Cateter", [(0.0, -26), (0.42, -26), (0.42, 26), (0.0, 26)], 48),
                            mat_cateter()))
        for z in (-8.5, 8.5):
            objs.append(aplicar(revolucao("Marcador", [(0.0, z - 0.5), (0.5, z - 0.5), (0.5, z + 0.5),
                                                       (0.0, z + 0.5)], 48), mat_cocr_polido()))
        enquadrar = pontos_de([stent])
        rot = Matrix.Rotation(math.radians(90), 3, "Y")
        return objs, rot, {"azimute": 38, "elevacao": 16, "lente": 100, "fstop": 1.4, "margem": 0.95}, enquadrar, None
    # artéria em corte: parede em três camadas (íntima, média e adventícia) com placa excêntrica entre a íntima e a
    # média; o stent expandido fica embutido na placa até meio strut (espessuras: valores de desenho, ilustrativos)
    lumen = raio - 0.03
    camadas = [("Íntima", 0.0, 0.07, mat_intima()), ("Média", 0.07, 0.40, mat_arteria()),
               ("Adventícia", 0.40, 0.62, mat_adventicia())]

    def espessura_placa(a):
        r = a.vec("LENGTH", a.vec("MULTIPLY", a.p, (1, 1, 0)))
        cos_t = a.y / a.math("MAXIMUM", r, 1e-3)  # placa do lado de trás (+y), o que fica depois do corte
        janela = a.clamp(1.0 - (a.z / 7.0) * (a.z / 7.0), 0.0, 1.0)
        return r, a.math("POWER", a.clamp(cos_t, 0.0, 1.0), 1.5) * janela * 0.95

    for nome, e0, e1, mat in camadas:
        a = Arvore(nome)
        r, esp = espessura_placa(a)
        base = lumen + esp if nome != "Íntima" else lumen
        d = a.inter((base + e0 if nome != "Íntima" else lumen) - r, r - (base + e1 if nome != "Íntima" else lumen + e1),
                    a.math("ABSOLUTE", a.z) - 13.0, -a.y)
        objs.append(aplicar(a.malha(nome, d, (-3.6, -0.2, -13.2), (3.6, 3.6, 13.2), 0.03), mat))
    b = Arvore("Placa")
    r, esp = espessura_placa(b)
    placa = b.inter(lumen + 0.07 - r, r - (lumen + 0.07 + esp), 0.06 - esp, -b.y)
    pla = aplicar(b.malha("Placa", placa, (-3.2, -0.2, -8), (3.2, 3.2, 8), 0.025), mat_placa())
    c = Arvore("Calcificações")
    calc = c.esfera((0.3, raio + 0.45, -1.5), 0.28)
    for cc in ((-0.5, raio + 0.4, 1.8), (0.6, raio + 0.35, 3.2)):
        calc = c.uniao(calc, c.esfera(cc, 0.22), 0.1)
    cal = aplicar(c.malha("Calcificações", c.inter(calc, -c.y), (-1.2, raio, -2.2), (1.2, raio + 1, 4), 0.02),
                  mat_calcificacao())
    objs += [pla, cal]
    rot = Matrix.Rotation(math.radians(90), 3, "Y")
    # artéria inteira no quadro, mais apertada e vista mais de cima, com o lúmen e a placa à vista
    cam = {"azimute": 24, "elevacao": 22, "lente": 100, "fstop": 4.0, "margem": 0.97}
    return objs, rot, cam, None, None


def cena_scaffold(variante="clara"):
    """Amostra cilíndrica (10 × 7 mm) em giroide (porosidade 70 %, célula de 2 mm; valores de desenho)."""
    periodo, R, H = 2.0, 5.0, 7.0
    t = geo.limiar_para_porosidade(0.70)
    a = Arvore("Giroide")
    k = 2 * math.pi / periodo
    x, y, z = a.x * k, a.y * k, a.z * k
    termo = lambda u, v: a.math("SINE", u) * a.math("COSINE", v)  # noqa: E731
    d_giro = (t - (termo(x, y) + termo(y, z) + termo(z, x))) / k
    r = a.vec("LENGTH", a.vec("MULTIPLY", a.p, (1, 1, 0)))
    d = a.inter(d_giro, r - R, a.math("ABSOLUTE", a.z) - H / 2)
    ob = aplicar(a.malha("Scaffold", d, (-R - 0.2, -R - 0.2, -H / 2 - 0.2), (R + 0.2, R + 0.2, H / 2 + 0.2), 0.03,
                         nitido=True),
                 mat_scaffold())
    ob.rotation_euler = (math.radians(-90 + 28), 0, math.radians(18))  # deitado e rodado, mostra o topo
    bpy.context.view_layer.update()
    pts = np.array([tuple(p) for p in pontos_de([ob])])
    mn, mx = pts.min(0), pts.max(0)
    # barra de escala de 2 mm, à frente e à esquerda, no plano da frente da amostra
    mat = mat_escala(variante)
    barra = malha_de_pontos("Escala 2 mm", [(x0, y0, z0) for z0 in (0, 0.18) for x0, y0 in
                                             ((0, 0), (2, 0), (2, 0.18), (0, 0.18))],
                            [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)])
    aplicar(barra, mat)
    barra.location = (mn[0] - 0.5, mn[1] - 1.5, mn[2])
    rotulo = texto_3d("2 mm", 0.75, mat)
    rotulo.rotation_euler = (math.radians(90), 0, 0)
    rotulo.location = (mn[0] + 0.5, mn[1] - 1.5, mn[2] + 0.45)
    return [ob, barra, rotulo], Matrix.Identity(3), {"azimute": 18, "elevacao": 14, "lente": 100, "fstop": 5.6,
                                                   "exposicao": {"clara": -0.45}}, \
        None, None


def cena_dentario():
    """Implante com pilar e coroa anatómica na mandíbula, em secção bucolingual na zona do 1.º molar.

    Trabalha num referencial local: origem no centro do molar, z ao longo do eixo do dente (para oclusal),
    y mesiodistal (para distal, para longe da câmara) e x bucolingual. Assim as caixas dos volumes ficam justas."""
    man = importar_obj("FJ3289")
    molar, pre, seg = importar_obj("FJ1268"), importar_obj("FJ1269"), importar_obj("FJ1270")
    vm = vertices(molar)
    c_t, u = geo.eixo_principal(vm)
    t = vertices(seg).mean(0) - vertices(pre).mean(0)
    t -= (t @ u) * u
    t /= np.linalg.norm(t)
    bx = np.cross(t, u)
    R = Matrix((tuple(bx), tuple(t), tuple(u)))
    local = Matrix.Translation(-(R @ Vector(tuple(c_t)))) @ R.to_4x4()
    for o in (man, molar, pre, seg):
        o.matrix_world = local
    # o 2.º molar recua 0,4 mm para distal: as malhas tocam-se em área e fundiam as duas coroas; assim fica um ponto de
    # contacto nítido entre dois dentes distintos (ajuste de desenho)
    seg.matrix_world = Matrix.Translation((0, 0.4, 0)) @ local
    bpy.context.view_layer.update()
    vman, vm = vertices(man), vertices(molar)
    radial = np.hypot(vman[:, 0], vman[:, 1])
    perto = vman[(radial > 2.0) & (radial < 7.0)]
    crista = float(np.percentile(perto[:, 2], 85))  # altura da crista alveolar à volta do dente
    cej = crista + 1.5
    print(f"  crista a {crista:.1f} mm; topo do molar a {vm[:, 2].max():.1f} mm (eixo do dente)")
    M = matriz_base((0, 0, crista - 0.3 - 10.0), (1, 0, 0), (0, 0, 1), (0, -1, 0))  # implante: topo em y = 10
    impl = aplicar(importar_stl("implante_dentario_implante", M), mat_titanio_escovado())
    pilar = aplicar(importar_stl("implante_dentario_pilar", M), mat_titanio_escovado())

    def seccao(a, d):  # fica o lado distal (y >= 0): corte plano à frente, ponta distal e lados arredondados
        lados = a.math("SMOOTH_MAX", a.y - 22.0, a.math("ABSOLUTE", a.x) - 18.0, 3.0)
        return a.inter(a.math("SMOOTH_MAX", d, lados, 2.5), -a.y)

    def osso(a, interior=False):
        d = a.sdf_objeto(man, 0.25, 60)
        if interior:
            d = d + 2.0  # cortical de 2 mm (valor de desenho)
        d = a.menos(d, a.sdf_objeto(impl, 0.08, 20, 0))
        d = a.menos(d, a.sdf_objeto(seg, 0.2, 30))
        canal = a.capsula((-0.8, -30, crista - 15.0), (-0.8, 40, crista - 15.5), 1.4)  # canal mandibular
        return a.menos(d, canal), canal

    caixa = ((-18.5, -0.5, crista - 32), (18.5, 22.5, crista + 3))
    objs = [impl, pilar]
    a = Arvore("Cortical")
    o, _ = osso(a)
    oi, _ = osso(a, True)
    objs.append(aplicar(a.malha("Osso cortical", seccao(a, a.menos(o, oi)), *caixa, 0.12), mat_osso_cortical()))
    cam = 1.6
    q = Arvore("Trabéculas")
    oi, _ = osso(q, True)
    camada = q.inter(seccao(q, oi), q.y - cam)
    objs.append(aplicar(q.malha("Trabéculas", q.inter(camada, q.trabeculas(0.85, 0.2)),
                                (-18.5, -0.3, crista - 32), (18.5, cam + 0.3, crista + 1), 0.05),
                        mat_osso_esponjoso()))
    m_ = Arvore("Medula")
    oi, _ = osso(m_, True)
    objs.append(aplicar(m_.malha("Medula", m_.inter(seccao(m_, oi), (cam - 0.5) - m_.y), *caixa, 0.15),
                        mat_medula()))
    n_ = Arvore("Nervo")
    _, canal = osso(n_)
    objs.append(aplicar(n_.malha("Nervo alveolar", seccao(n_, canal + 0.35), *caixa, 0.08), mat_nervo()))
    # coroa anatómica: parte coronária do molar natural (acima da junção amelocementária)
    k = Arvore("Coroa")
    coroa_d = k.inter(k.sdf_objeto(molar, 0.04, 40, 0), cej - k.z)
    coroa_d = k.menos(coroa_d, k.sdf_objeto(pilar, 0.06, 20, 0) + 0.05)
    objs.append(aplicar(k.malha("Coroa", coroa_d, (-8, -8, cej - 0.3), (8, 8, vm[:, 2].max() + 0.5), 0.035),
                        mat_ceramica("Cerâmica (coroa)", (0.94, 0.91, 0.83))))
    v = Arvore("Dente vizinho")
    objs.append(aplicar(v.malha("2.º molar", v.inter(v.sdf_objeto(seg, 0.04, 40, 0), crista - 0.5 - v.z),
                                (-8, 3, crista - 1), (8, 22.5, crista + 12), 0.04), mat_esmalte()))
    # gengiva: manto de 2,4 mm sobre a crista, que sobe e abraça a coroa e o dente vizinho junto ao colo
    gg = Arvore("Gengiva")
    ob_ = gg.sdf_objeto(man, 0.25, 60)
    manto = gg.inter(gg.menos(ob_ - 2.4, ob_), (crista - 7.0) - gg.z)
    mol_d, seg_d = gg.sdf_objeto(molar, 0.05, 40, 0), gg.sdf_objeto(seg, 0.05, 40, 0)
    abraco = gg.inter(mol_d - 0.9, gg.z - (cej + 1.0), (crista - 1.0) - gg.z)
    abraco2 = gg.inter(seg_d - 0.9, gg.z - (crista + 2.0), (crista - 1.0) - gg.z)
    gengiva = gg.uniao(gg.uniao(manto, abraco, 0.9), abraco2, 0.9)
    gengiva = gg.inter(gengiva, gg.z - (cej + 1.0))
    gengiva = gg.menos(gengiva, gg.inter(mol_d, cej - gg.z))
    gengiva = gg.menos(gengiva, seg_d)
    gengiva = gg.menos(gengiva, gg.sdf_objeto(pilar, 0.06, 20, 0))
    objs.append(aplicar(gg.malha("Gengiva", seccao(gg, gengiva), (-18.5, -0.5, crista - 9), (18.5, 22.5, cej + 1.5),
                                 0.06), mat_gengiva(crista - 7.0, cej + 1.0)))
    return objs, Matrix.Identity(3), {"azimute": 22, "elevacao": 12, "lente": 100, "fstop": 6.3}, None, None


CENAS = {
    "anca": lambda v: cena_anca(False),
    "articulacao": lambda v: cena_anca("meia"),
    "anca_haste": lambda v: cena_anca("haste"),
    "stent": lambda v: cena_stent(False),
    "stent_arteria": lambda v: cena_stent(True),
    "scaffold": cena_scaffold,
    "dentario": lambda v: cena_dentario(),
}


def montar(cena: str, variante: str, qualidade: str):
    """Monta a cena (modelos, luz, câmara e fundo) sem fazer o render. Devolve a raiz dos modelos."""
    limpar()
    configurar_render(qualidade)
    luz = "clara" if variante == "transparente" else variante
    mundo_hdri(luz)
    objs, rot, cam, enquadrar, foco = CENAS[cena](luz)
    cam = dict(cam)
    exposicao = cam.pop("exposicao", {}).get(luz, 0.0)
    bpy.context.scene.view_settings.exposure = exposicao
    raiz, fundo = normalizar(objs, rot)
    tres_pontos(luz)
    mw = raiz.matrix_world
    pts = [mw @ Vector(tuple(p)) for p in enquadrar] if enquadrar is not None else         pontos_de([o for o in objs if not o.hide_render])
    camara(pts, foco=mw @ foco if foco is not None else None, **cam)
    if variante == "transparente":  # só a sombra de contacto, para o poster
        bpy.context.scene.render.film_transparent = True
        bpy.context.scene.render.image_settings.color_mode = "RGBA"
        bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, fundo - 0.003))
        bpy.context.active_object.is_shadow_catcher = True
    else:
        ciclorama(fundo - 0.003, variante)
    return raiz


def render(cena: str, variante: str, qualidade: str, saida: Path):
    print(f"cena {cena} ({variante})")
    montar(cena, variante, qualidade)
    saida.mkdir(parents=True, exist_ok=True)
    destino = saida / f"{cena}_{variante}.png"
    bpy.context.scene.render.filepath = str(destino)
    bpy.ops.render.render(write_still=True)
    print("render:", destino)


def video_360(cena: str, variante: str, saida: Path, segundos=8, fps=30):
    """Vídeo a rodar 360° (EEVEE, 1080p, MP4 H.264): os modelos rodam à volta do eixo vertical."""
    print(f"vídeo {cena} ({variante})")
    # a cena montada (osso por campos de distância, a parte lenta) fica guardada num .blend: se o vídeo tiver de
    # ser repetido, abre-se o .blend em vez de reconstruir a geometria
    guardada = saida / "cenas" / f"{cena}_{variante}.blend"
    if guardada.exists():
        bpy.ops.wm.open_mainfile(filepath=str(guardada))
        raiz = bpy.data.objects["Raiz"]
    else:
        raiz = montar(cena, variante, "video")
        guardada.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(guardada), copy=True)
    cena_b = bpy.context.scene
    for motor in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        try:
            cena_b.render.engine = motor
            break
        except TypeError:
            continue
    cena_b.render.resolution_x, cena_b.render.resolution_y = 1920, 1080
    cena_b.camera.data.dof.use_dof = False  # a rodar, o objeto sai do plano de foco: tudo nítido no vídeo
    cena_b.render.fps = fps
    cena_b.frame_start, cena_b.frame_end = 1, segundos * fps
    pivo = bpy.data.objects.new("Pivô", None)
    bpy.context.collection.objects.link(pivo)
    mw = raiz.matrix_world.copy()
    raiz.parent = pivo
    raiz.matrix_world = mw
    pivo.rotation_euler = (0, 0, 0)
    pivo.keyframe_insert("rotation_euler", frame=1)
    pivo.rotation_euler = (0, 0, 2 * math.pi)
    pivo.keyframe_insert("rotation_euler", frame=segundos * fps + 1)
    for fc in pivo.animation_data.action.fcurves if hasattr(pivo.animation_data.action, "fcurves") else []:
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR"
    try:
        for camada in pivo.animation_data.action.layers:
            for faixa in camada.strips:
                for cb in faixa.channelbags:
                    for fc in cb.fcurves:
                        for k in fc.keyframe_points:
                            k.interpolation = "LINEAR"
    except AttributeError:
        pass
    if hasattr(cena_b.render.image_settings, "media_type"):  # Blender 5: o vídeo é um tipo de media à parte
        cena_b.render.image_settings.media_type = "VIDEO"
    cena_b.render.image_settings.file_format = "FFMPEG"
    cena_b.render.ffmpeg.format = "MPEG4"
    cena_b.render.ffmpeg.codec = "H264"
    cena_b.render.ffmpeg.constant_rate_factor = "HIGH"
    saida.mkdir(parents=True, exist_ok=True)
    cena_b.render.filepath = str(saida / f"{cena}_360_{variante}.mp4")
    bpy.ops.render.render(animation=True)
    print("vídeo:", cena_b.render.filepath)


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--cenas", default=",".join(CENAS))
    ap.add_argument("--qualidade", default="rapida", choices=list(QUALIDADE))
    ap.add_argument("--variantes", default="clara,escura")
    ap.add_argument("--saida", default=None)
    ap.add_argument("--video", action="store_true", help="vídeo a 360° em EEVEE em vez de imagem")
    a = ap.parse_args(argv)
    saida = Path(a.saida) if a.saida else SAIDA_PADRAO / ("videos" if a.video else a.qualidade)
    for c in a.cenas.split(","):
        for v in a.variantes.split(","):
            (video_360 if a.video else render)(c, v, *(() if a.video else (a.qualidade,)), saida)


if __name__ == "__main__":
    main()
