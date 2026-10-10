// Visualizador 3D (React Three Fiber). Carrega o glTF de public/modelos/<modelo>.glb se existir (exportado do
// Blender por scripts/renders_blender.py, sem compressão Draco); se não existir, mostra um modelo simplificado
// feito aqui, com o aviso de que é só uma forma de referência.
import { Component, Suspense, useMemo, type ReactNode } from "react";
import { Canvas } from "@react-three/fiber";
import { Bounds, Center, OrbitControls, useGLTF } from "@react-three/drei";
import * as THREE from "three";
import { useDefinicoes } from "@/lib/definicoes";
import { cn } from "@/lib/utils";

export type ChaveModelo = "haste" | "stent" | "scaffold" | "par" | "dentario";

/**
 * Verifica se o ficheiro do modelo existe. A lista dos .glb de public/modelos é lida quando o Vite arranca
 * (__MODELOS_GLB__ em vite.config.ts): assim não se pede à rede um ficheiro que não existe (o pedido falhado
 * aparecia como erro 404 na consola da versão web).
 */
export function existeModelo(modelo: string, lista: readonly string[] = __MODELOS_GLB__): boolean {
  return lista.includes(modelo);
}

/** Se o glTF falhar ao carregar, mostra o modelo simplificado em vez de rebentar a página. */
class FalhaModelo extends Component<{ alternativa: ReactNode; children: ReactNode }, { falhou: boolean }> {
  state = { falhou: false };
  static getDerivedStateFromError() {
    return { falhou: true };
  }
  render() {
    return this.state.falhou ? this.props.alternativa : this.props.children;
  }
}

/** Verdadeiro se o navegador consegue criar um contexto WebGL (sem ele, o three.js lança um erro ao arrancar). */
let webglCache: boolean | null = null;
export function temWebGL(): boolean {
  if (webglCache !== null) return webglCache;
  try {
    const c = document.createElement("canvas");
    webglCache = !!(c.getContext("webgl2") ?? c.getContext("webgl"));
  } catch {
    webglCache = false;
  }
  return webglCache;
}

function ModeloGltf({ url }: { url: string }) {
  const { scene } = useGLTF(url, false);
  const copia = useMemo(() => scene.clone(true), [scene]);
  return <primitive object={copia} />;
}

/** Fração sólida de uma rede cúbica de barras quadradas de largura t (célula 1): 3t² - 2t³. */
function larguraBarra(porosidade: number): number {
  const solido = Math.min(0.999, Math.max(0.001, 1 - porosidade));
  let lo = 0;
  let hi = 1;
  for (let k = 0; k < 40; k++) {
    const t = (lo + hi) / 2;
    if (3 * t * t - 2 * t * t * t < solido) lo = t;
    else hi = t;
  }
  return (lo + hi) / 2;
}

function Rede({ porosidade, cor }: { porosidade: number; cor: string }) {
  const n = 4;
  const t = larguraBarra(porosidade);
  const barras: { pos: [number, number, number]; tam: [number, number, number] }[] = [];
  for (let a = 0; a <= n; a++) {
    for (let b = 0; b <= n; b++) {
      const u = a - n / 2;
      const v = b - n / 2;
      barras.push({ pos: [0, u, v], tam: [n + t, t, t] });
      barras.push({ pos: [u, 0, v], tam: [t, n + t, t] });
      barras.push({ pos: [u, v, 0], tam: [t, t, n + t] });
    }
  }
  return (
    <group scale={0.5}>
      {barras.map((b, i) => (
        <mesh key={i} position={b.pos}>
          <boxGeometry args={b.tam} />
          <meshStandardMaterial color={cor} roughness={0.55} metalness={0.1} />
        </mesh>
      ))}
    </group>
  );
}

/** Formas de referência quando ainda não há glTF. */
function ModeloSimples({ chave, cor, porosidade }: { chave: ChaveModelo; cor: string; porosidade: number }) {
  const metal = <meshStandardMaterial color={cor} roughness={0.3} metalness={0.75} />;
  switch (chave) {
    case "haste":
      return (
        <group rotation={[0, 0, 0.1]}>
          <mesh position={[0, -0.6, 0]}>
            <cylinderGeometry args={[0.32, 0.12, 3.2, 32]} />
            {metal}
          </mesh>
          <mesh position={[-0.45, 1.25, 0]} rotation={[0, 0, 0.75]}>
            <cylinderGeometry args={[0.14, 0.2, 1, 24]} />
            {metal}
          </mesh>
          <mesh position={[-0.85, 1.65, 0]}>
            <sphereGeometry args={[0.42, 32, 32]} />
            <meshStandardMaterial color={cor} roughness={0.15} metalness={0.9} />
          </mesh>
        </group>
      );
    case "stent":
      return (
        <mesh rotation={[0, 0, Math.PI / 2]}>
          <cylinderGeometry args={[0.8, 0.8, 3, 16, 8, true]} />
          <meshStandardMaterial color={cor} wireframe metalness={0.8} roughness={0.3} />
        </mesh>
      );
    case "scaffold":
      return <Rede porosidade={porosidade} cor={cor} />;
    case "par":
      return (
        <group>
          <mesh position={[0, -0.2, 0]}>
            <sphereGeometry args={[0.8, 48, 48]} />
            <meshStandardMaterial color={cor} roughness={0.1} metalness={0.6} />
          </mesh>
          <mesh position={[0, 0.05, 0]} rotation={[Math.PI, 0, 0]}>
            <sphereGeometry args={[1.05, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2]} />
            <meshStandardMaterial color="#d9dde2" roughness={0.6} side={THREE.DoubleSide} />
          </mesh>
        </group>
      );
    case "dentario":
      return (
        <group>
          <mesh>
            <cylinderGeometry args={[0.45, 0.35, 2.4, 32]} />
            {metal}
          </mesh>
          {Array.from({ length: 9 }, (_, k) => (
            <mesh key={k} position={[0, 0.95 - k * 0.24, 0]} rotation={[Math.PI / 2, 0, 0]}>
              <torusGeometry args={[0.44 - k * 0.01, 0.06, 12, 40]} />
              {metal}
            </mesh>
          ))}
          <mesh position={[0, -1.4, 0]} rotation={[Math.PI, 0, 0]}>
            <coneGeometry args={[0.35, 0.4, 32]} />
            {metal}
          </mesh>
        </group>
      );
  }
}

export function Visualizador3D({
  modelo,
  porosidade = 0.6,
  className,
  rotulo,
}: {
  modelo: ChaveModelo;
  porosidade?: number;
  className?: string;
  rotulo: string;
}) {
  const { escuro, reduzido } = useDefinicoes();
  // O scaffold com deslizador de porosidade usa sempre a rede feita aqui (o glTF não muda com a porosidade).
  // relativo à base do Vite ("/" na aplicação nativa, "./" na versão web publicada num subcaminho)
  const url = `${import.meta.env.BASE_URL}modelos/${modelo}.glb`;
  const existe = existeModelo(modelo);
  const usarGltf = existe === true && modelo !== "scaffold";
  const cor = escuro ? "#7CC6EF" : "#0595D1";
  const webgl = temWebGL();
  const simples = <ModeloSimples chave={modelo} cor={cor} porosidade={porosidade} />;

  return (
    <div className={cn("relative overflow-hidden rounded-lg border border-linha bg-superficie2", className)}>
      {webgl ? (
        <FalhaModelo alternativa={<SemWebGL rotulo={rotulo} />}>
          <Canvas camera={{ position: [3.2, 2.2, 4.2], fov: 40 }} dpr={[1, 2]} aria-label={rotulo} role="img">
            <ambientLight intensity={escuro ? 0.55 : 0.75} />
            <directionalLight position={[4, 6, 5]} intensity={1.4} />
            <directionalLight position={[-5, -2, -4]} intensity={0.4} />
            <Suspense fallback={null}>
              <Bounds fit clip observe margin={1.15}>
                <Center>{usarGltf ? <FalhaModelo alternativa={simples}><ModeloGltf url={url} /></FalhaModelo> : simples}</Center>
              </Bounds>
            </Suspense>
            <OrbitControls makeDefault autoRotate={!reduzido} autoRotateSpeed={1.2} enablePan={false} />
          </Canvas>
        </FalhaModelo>
      ) : (
        <SemWebGL rotulo={rotulo} />
      )}
      {webgl && (existe === false || modelo === "scaffold") ? (
        <p className="pointer-events-none absolute bottom-2 left-3 right-3 text-[0.7rem] text-texto2">
          {modelo === "scaffold"
            ? "Rede cúbica ilustrativa: a espessura das barras segue a porosidade escolhida."
            : `Forma simplificada. O modelo do Blender aparece aqui quando existir public/modelos/${modelo}.glb.`}
        </p>
      ) : null}
    </div>
  );
}

/** Sem WebGL (navegador antigo ou aceleração gráfica desligada): uma nota em vez do modelo, sem parar a aplicação. */
function SemWebGL({ rotulo }: { rotulo: string }) {
  return (
    <div role="img" aria-label={rotulo} className="flex h-full w-full items-center justify-center p-4 text-center text-sm text-texto2">
      O modelo 3D precisa de WebGL, que este navegador não tem ativo.
    </div>
  );
}
