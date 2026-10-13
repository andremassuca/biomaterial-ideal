// Separador "Haste femoral (FEA)": imagens da SOLIDWORKS por material e malha, com a tabela de números ao lado.
import { useState, type ReactNode } from "react";
import { Cartao, DescricaoCartao, TituloCartao } from "@/componentes/ui/cartao";
import { Opcoes } from "@/componentes/ui/controlos";
import { APP } from "@/lib/dados";
import { num, pct } from "@/lib/formato";
import { MALHAS_SW, MATERIAIS_SW, imagemSw, linhaSw, urlSimulacao, variacaoPercentual, type VistaSw } from "@/lib/simulacao";
import { Ampliavel } from "./Ampliavel";

/** Módulo de Young da haste (GPa) lido dos resultados da aplicação; null no fémur intacto. */
function moduloHaste(materialBase: string | null): number | null {
  if (!materialBase) return null;
  return APP.fea?.zonas.find((z) => z.material_base === materialBase)?.E_haste_GPa ?? null;
}

function Linha({ nome, children }: { nome: string; children: ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-3 border-t border-linha py-1.5 text-sm first:border-t-0">
      <dt className="text-texto2">{nome}</dt>
      <dd className="numero text-right font-medium text-texto">{children}</dd>
    </div>
  );
}

export function SimulacaoFea() {
  const [chave, setChave] = useState(MATERIAIS_SW[1].chave);
  const [malha, setMalha] = useState(MALHAS_SW[0]);
  const [vista, setVista] = useState<VistaSw>("energia");

  const material = MATERIAIS_SW.find((m) => m.chave === chave) ?? MATERIAIS_SW[0];
  const l = linhaSw(material.chave, malha);
  const e = moduloHaste(material.materialBase);
  const outra = MALHAS_SW.find((h) => h !== malha);
  const lOutra = outra ? linhaSw(material.chave, outra) : null;
  const intacto = material.chave === "Intacto";
  const legenda =
    vista === "energia"
      ? `${material.nome}, malha de ${malha} mm: densidade de energia de deformação por elemento (SEDENS, N·m/m³ = J/m³), forma deformada exagerada. A escala de cores é automática de cada estudo e vem na barra da própria figura: não é a mesma entre imagens.`
      : `${material.nome}, malha de ${malha} mm: malha de elementos finitos (gráfico Mesh Quality da SOLIDWORKS), sem escala de cores de tensão.`;

  return (
    <div className="space-y-6">
      <div className="grid gap-6 [&>*]:min-w-0 lg:grid-cols-[1fr_320px]">
        <Cartao>
          <TituloCartao>Haste femoral: análise por elementos finitos (SOLIDWORKS Simulation)</TituloCartao>
          <DescricaoCartao>
            Escolhe o material, a malha e a vista. Clica na imagem para ampliar.
          </DescricaoCartao>
          <div className="mt-3 flex flex-wrap gap-3">
            <Opcoes
              rotulo="Material"
              valor={chave}
              aoMudar={setChave}
              opcoes={MATERIAIS_SW.map((m) => ({ valor: m.chave, texto: m.nome }))}
            />
            <Opcoes
              rotulo="Malha"
              valor={malha}
              aoMudar={setMalha}
              opcoes={MALHAS_SW.map((h) => ({ valor: h, texto: `Malha ${num(Number(h), 1)} mm` }))}
            />
            <Opcoes
              rotulo="Vista"
              valor={vista}
              aoMudar={setVista}
              opcoes={[
                { valor: "energia", texto: "Energia de deformação" },
                { valor: "malha", texto: "Malha" },
              ]}
            />
          </div>
          <div className="mt-4">
            <Ampliavel
              src={urlSimulacao(imagemSw(material, malha, vista))}
              alt={`FEA da haste, ${material.nome}, malha ${malha} mm, ${vista === "energia" ? "energia de deformação" : "malha"}`}
              legenda={legenda}
            />
            <p className="mt-2 text-xs leading-relaxed text-texto2">{legenda}</p>
          </div>
        </Cartao>

        <Cartao>
          <TituloCartao>{material.nome}</TituloCartao>
          <DescricaoCartao>Malha de {num(Number(malha), 1)} mm (tetraedros parabólicos)</DescricaoCartao>
          {l ? (
            <dl className="mt-3">
              <Linha nome="E da haste (GPa)">{e === null ? "n.d." : num(e, 1)}</Linha>
              <Linha nome="Energia no osso, Gruen 1 (mJ)">{num(l.g1_mJ, 2)}</Linha>
              <Linha nome="Razão ao intacto, Gruen 1">{num(l.razao1, 2)}</Linha>
              <Linha nome="Energia no osso, Gruen 7 (mJ)">{num(l.g7_mJ, 2)}</Linha>
              <Linha nome="Razão ao intacto, Gruen 7">{num(l.razao7, 2)}</Linha>
              {!intacto && (
                <>
                  <Linha nome="Stress shielding, Gruen 1">{pct(l.shielding1 * 100)}</Linha>
                  <Linha nome="Stress shielding, Gruen 7">{pct(l.shielding7 * 100)}</Linha>
                </>
              )}
              <Linha nome="von Mises máxima no modelo (MPa)">{num(l.vm_max_MPa, 1)}</Linha>
              <Linha nome="Deslocamento máximo (mm)">{num(l.ures_max_mm, 2)}</Linha>
              <Linha nome="Nós / elementos">
                {num(l.nos, 0)} / {num(l.elementos, 0)}
              </Linha>
              {lOutra && outra && (
                <Linha nome={`Razão Gruen 1 com malha de ${num(Number(outra), 1)} mm (variação)`}>
                  {num(lOutra.razao1, 2)} ({num(variacaoPercentual(l.razao1, lOutra.razao1), 1)} %)
                </Linha>
              )}
            </dl>
          ) : (
            <p className="mt-3 text-sm text-texto2">Sem resultados para esta combinação.</p>
          )}
          <p className="mt-3 text-xs leading-relaxed text-texto2">
            Razão ao intacto: energia de deformação do osso na zona de Gruen (1: lateral; 7: medial, calcar) com a haste, a
            dividir pela do fémur intacto com a mesma malha. 1 = igual ao osso natural; abaixo de 1 = stress shielding
            (stress shielding = 1 − razão). Acima de 1 no Ti-6Al-4V poroso é efeito do modelo (haste colada, rigidez igual à
            do osso cortical), não um ganho clínico.
          </p>
        </Cartao>
      </div>

      <Cartao>
        <TituloCartao>Todos os materiais, malha de {num(Number(malha), 1)} mm</TituloCartao>
        <div className="mt-3 overflow-x-auto">
          <table className="tabela-limpa w-full text-left text-sm">
            <thead className="text-xs text-texto2">
              <tr>
                {["Material", "E (GPa)", "Razão G1", "Razão G7", "von Mises máx. (MPa)", "Deslocamento máx. (mm)"].map((c) => (
                  <th key={c} className="py-1 pr-3 font-medium">
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {MATERIAIS_SW.map((m) => {
                const x = linhaSw(m.chave, malha);
                const em = moduloHaste(m.materialBase);
                return (
                  <tr key={m.chave} className={`border-t border-linha ${m.chave === chave ? "bg-acento/10" : ""}`}>
                    <td className="py-1.5 pr-3 font-medium">{m.nome}</td>
                    <td className="numero py-1.5 pr-3">{em === null ? "n.d." : num(em, 1)}</td>
                    <td className="numero py-1.5 pr-3">{x ? num(x.razao1, 2) : "n.d."}</td>
                    <td className="numero py-1.5 pr-3">{x ? num(x.razao7, 2) : "n.d."}</td>
                    <td className="numero py-1.5 pr-3">{x ? num(x.vm_max_MPa, 1) : "n.d."}</td>
                    <td className="numero py-1.5 pr-3">{x ? num(x.ures_max_mm, 2) : "n.d."}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-texto2">Fonte: results/fea_haste_sw.json (resumo em results/fea_haste_sw.md).</p>
      </Cartao>

      <div className="grid gap-6 [&>*]:min-w-0 lg:grid-cols-2">
        <Cartao>
          <TituloCartao>Razão ao intacto nas zonas de Gruen 1 e 7</TituloCartao>
          <div className="mt-3">
            <Ampliavel
              src={urlSimulacao("fea_sw/gruen_razao_intacto.png")}
              alt="Razão da energia no osso ao fémur intacto, zonas de Gruen 1 e 7, por material"
              legenda="Razão da energia de deformação no osso (zonas de Gruen 1 e 7) ao fémur intacto, por material, SOLIDWORKS com a malha de 3,5 mm. A linha tracejada em 1 é o osso natural; abaixo de 1 há stress shielding."
            />
          </div>
          <p className="mt-2 text-xs leading-relaxed text-texto2">
            Barras da razão ao intacto, SOLIDWORKS, malha de 3,5 mm (título da figura). Eixo vertical: energia no osso a dividir pela do fémur intacto.
          </p>
        </Cartao>
        <Cartao>
          <TituloCartao>Mapa da energia de deformação no osso (corte coronal)</TituloCartao>
          <div className="mt-3">
            <Ampliavel
              src={urlSimulacao("fea/sed_corte_coronal.png")}
              alt="Corte coronal da densidade de energia de deformação no osso, fémur intacto e quatro hastes"
              legenda="Corte coronal pelo plano da haste (modelo em Python, fémur anatómico). Cinzento: haste e cabeça; tracejado: limites das zonas de Gruen. Barra de cores logarítmica da densidade de energia de deformação no osso (mJ/mm³), de 1e-5 a 3e-2."
            />
          </div>
          <p className="mt-2 text-xs leading-relaxed text-texto2">
            Densidade de energia de deformação no osso (mJ/mm³), escala logarítmica comum aos cinco painéis (barra na figura).
            Azul escuro: osso a trabalhar pouco; amarelo: osso muito solicitado.
          </p>
        </Cartao>
      </div>

      {APP.fea?.comparacao && (
        <Cartao>
          <TituloCartao>Duas ferramentas, a mesma ordem dos materiais</TituloCartao>
          <DescricaoCartao>
            Razão ao intacto calculada em Python (fémur anatómico, malha de {num(APP.fea.malha_mm, 2)} mm) e na SOLIDWORKS
            (fémur simplificado, malha de {MALHAS_SW[0]} mm). Verificação numérica cruzada entre programas, não validação clínica nem
            experimental.
          </DescricaoCartao>
          <div className="mt-3 grid gap-6 [&>*]:min-w-0 lg:grid-cols-2">
            <div className="overflow-x-auto">
              <table className="tabela-limpa w-full text-left text-sm">
                <thead className="text-xs text-texto2">
                  <tr>
                    {["Material", "G1 Python", "G1 SOLIDWORKS", "G7 Python", "G7 SOLIDWORKS"].map((c) => (
                      <th key={c} className="py-1 pr-3 font-medium">
                        {c}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {APP.fea.comparacao.map((c) => (
                    <tr key={c.material} className="border-t border-linha">
                      <td className="py-1.5 pr-3 font-medium">{c.material}</td>
                      <td className="numero py-1.5 pr-3">{num(c.G1_python, 2)}</td>
                      <td className="numero py-1.5 pr-3">{num(c.G1_solidworks, 2)}</td>
                      <td className="numero py-1.5 pr-3">{num(c.G7_python, 2)}</td>
                      <td className="numero py-1.5 pr-3">{num(c.G7_solidworks, 2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <Ampliavel
              src={urlSimulacao("fea/comparacao_ferramentas.png")}
              alt="Comparação das razões ao intacto entre Python e SOLIDWORKS"
              legenda="Razões ao intacto nas zonas de Gruen 1 e 7, Python contra SOLIDWORKS, por material."
            />
          </div>
        </Cartao>
      )}
    </div>
  );
}
