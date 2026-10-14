// Separador "Haste femoral (FEA)": imagens da SOLIDWORKS por material e malha, com a tabela de números ao lado.
import { useState, type ReactNode } from "react";
import { Cartao, DescricaoCartao, TituloCartao } from "@/componentes/ui/cartao";
import { Opcoes } from "@/componentes/ui/controlos";
import { APP } from "@/lib/dados";
import { num, pct } from "@/lib/formato";
import {
  ESCALA_MAPDL,
  IMAGEM_COMPARACAO_MAPDL,
  MALHAS_SW,
  MALHA_MAPDL,
  MATERIAIS_SW,
  NOTA_MAPDL,
  NOTA_VERIFICACAO,
  imagemMapdl,
  imagemSw,
  linhaMapdl,
  linhaSw,
  resumoMicromovimento,
  urlSimulacao,
  variacaoPercentual,
  type CorteMapdl,
  type VistaFea,
} from "@/lib/simulacao";
import { Ampliavel } from "./Ampliavel";
import { BlocoVideo } from "./BlocoVideo";

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

/** Cartão do micromovimento da haste (Ansys, contacto com atrito): a frase do relatório v11.1 (secção 8) e a ressalva. */
export function CartaoMicromovimento() {
  const r = resumoMicromovimento();
  if (!r) return null;
  const nenhum = r.fracaoAcimaLimiar === 0;
  return (
    <Cartao data-micromovimento>
      <TituloCartao>Verificação adicional: micromovimento na interface osso-haste</TituloCartao>
      <p className="mt-2 text-sm leading-relaxed">
        Como verificação adicional, e não como previsão clínica, repetiu-se a haste de {r.material} no Ansys com contacto com
        atrito entre a haste e o osso (μ = {num(r.mu, 1)}, contacto mais rígido): o deslocamento tangencial máximo na interface é de{" "}
        {num(r.maxUm, 1)} µm, a mediana é de {num(r.medianaUm, 1)} µm e {nenhum ? "nenhum nó (0 %)" : `${num(r.fracaoAcimaLimiar * 100, 1)} % dos nós`} passa os{" "}
        {num(r.limiarUm, 0)} µm, o valor a partir do qual, em cães, a fixação passa a ser por tecido conjuntivo e não por osso
        (Pilliar et al., 1986). Nas outras quatro variantes do contacto o máximo vai de {num(r.intervaloMinUm, 1)} a{" "}
        {num(r.intervaloMaxUm, 1)} µm, {nenhum ? "também sem nós acima de" : "com nós acima de"} {num(r.limiarUm, 0)} µm.
      </p>
      <dl className="mt-3 grid gap-x-6 sm:grid-cols-2 [&>*]:min-w-0">
        <Linha nome="Máximo (caso principal)">{num(r.maxUm, 1)} µm</Linha>
        <Linha nome="Intervalo do máximo nas outras variantes">
          {num(r.intervaloMinUm, 1)} a {num(r.intervaloMaxUm, 1)} µm
        </Linha>
        <Linha nome={`Nós acima de ${num(r.limiarUm, 0)} µm`}>{num(r.fracaoAcimaLimiar * 100, 0)} %</Linha>
      </dl>
      <p role="note" className="mt-3 rounded-md border border-aviso/40 bg-aviso/10 px-3 py-2 text-xs font-medium text-texto">
        {NOTA_VERIFICACAO} Não demonstra perda óssea nem descolamento: o micromovimento foi estimado só como verificação adicional
        (caso principal com interface colada, um só instante da marcha, osso isotrópico, sem remodelação); não houve validação
        experimental.
      </p>
      <p className="mt-2 text-xs leading-relaxed text-texto2">
        Limiar de 150 µm: Pilliar RM, Lee JM, Maniatopoulos C. Clin Orthop Relat Res 1986;(208):108-113 (só resumo).
      </p>
    </Cartao>
  );
}

export function SimulacaoFea() {
  const [chave, setChave] = useState(MATERIAIS_SW[1].chave);
  const [malha, setMalha] = useState(MALHAS_SW[0]);
  const [vista, setVista] = useState<VistaFea>("energia");
  const [corte, setCorte] = useState<CorteMapdl>("corte_coronal");

  const material = MATERIAIS_SW.find((m) => m.chave === chave) ?? MATERIAIS_SW[0];
  const l = linhaSw(material.chave, malha);
  const m = linhaMapdl(material.prefixo);
  const tensao = vista === "tensao";
  const e = moduloHaste(material.materialBase);
  const outra = MALHAS_SW.find((h) => h !== malha);
  const lOutra = outra ? linhaSw(material.chave, outra) : null;
  const intacto = material.chave === "Intacto";
  const legenda = tensao
    ? `${material.nome}, MAPDL, malha de ${num(MALHA_MAPDL, 1)} mm, ${corte === "frente" ? "vista de frente" : "corte coronal pelo centro do canal medular"}: tensão de von Mises (MPa) com a mesma escala de cores em todos os materiais, de ${num(ESCALA_MAPDL.min, 0)} a ${num(ESCALA_MAPDL.max, 0)} MPa (acima disso a cor satura). ${NOTA_MAPDL}`
    : vista === "energia"
      ? `${material.nome}, malha de ${malha} mm: densidade de energia de deformação por elemento (SEDENS, N·m/m³ = J/m³), forma deformada exagerada. A escala de cores é automática de cada estudo e vem na barra da própria figura: não é a mesma entre imagens.`
      : `${material.nome}, malha de ${malha} mm: malha de elementos finitos (gráfico Mesh Quality da SOLIDWORKS), sem escala de cores de tensão.`;
  const textoVista = tensao ? "tensão de von Mises" : vista === "energia" ? "energia de deformação" : "malha";
  const imagem = tensao ? imagemMapdl(material, corte) : imagemSw(material, malha, vista);

  return (
    <div className="space-y-6">
      <div className="grid gap-6 [&>*]:min-w-0 lg:grid-cols-[1fr_320px]">
        <Cartao>
          <TituloCartao>Haste femoral: análise por elementos finitos ({tensao ? "MAPDL" : "SOLIDWORKS Simulation"})</TituloCartao>
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
            {tensao ? (
              <Opcoes
                rotulo="Corte"
                valor={corte}
                aoMudar={setCorte}
                opcoes={[
                  { valor: "corte_coronal", texto: "Corte coronal" },
                  { valor: "frente", texto: "Vista de frente" },
                ]}
              />
            ) : (
              <Opcoes
                rotulo="Malha"
                valor={malha}
                aoMudar={setMalha}
                opcoes={MALHAS_SW.map((h) => ({ valor: h, texto: `Malha ${num(Number(h), 1)} mm` }))}
              />
            )}
            <Opcoes
              rotulo="Vista"
              valor={vista}
              aoMudar={setVista}
              opcoes={[
                { valor: "energia", texto: "Energia de deformação" },
                { valor: "tensao", texto: "Tensão de von Mises" },
                { valor: "malha", texto: "Malha" },
              ]}
            />
          </div>
          <div className="mt-4">
            <Ampliavel
              src={urlSimulacao(imagem)}
              alt={`FEA da haste, ${material.nome}, ${tensao ? `MAPDL, malha ${num(MALHA_MAPDL, 1)} mm` : `malha ${malha} mm`}, ${textoVista}`}
              legenda={legenda}
            />
            <p className="mt-2 text-xs leading-relaxed text-texto2">{legenda}</p>
          </div>
        </Cartao>

        <Cartao>
          <TituloCartao>{material.nome}</TituloCartao>
          <DescricaoCartao>
            {tensao ? `MAPDL, malha de ${num(MALHA_MAPDL, 1)} mm (tetraedros parabólicos)` : `Malha de ${num(Number(malha), 1)} mm (tetraedros parabólicos)`}
          </DescricaoCartao>
          {tensao && m ? (
            <>
              <dl className="mt-3" data-mapdl>
                <Linha nome="E da haste (GPa)">{m.eHasteGPa === null ? "n.d." : num(m.eHasteGPa, 1)}</Linha>
                {m.vmHaste !== null && <Linha nome="von Mises máxima na haste (MPa)">{num(m.vmHaste, 1)}</Linha>}
                <Linha nome="von Mises máxima no osso cortical (MPa)">{num(m.vmCortical, 1)}</Linha>
                <Linha nome="von Mises máxima no osso trabecular (MPa)">{num(m.vmTrabecular, 1)}</Linha>
                <Linha nome="Máximo global (MPa)">{num(m.vmGlobal, 1)}</Linha>
                <Linha nome="Nós / elementos">
                  {num(m.nos, 0)} / {num(m.elementos, 0)}
                </Linha>
              </dl>
              <p className="mt-3 text-xs leading-relaxed text-texto2">
                Máximos por corpo (média nodal feita dentro de cada corpo). {NOTA_MAPDL} Na vista de frente a haste quase não se
                vê, porque está dentro do osso: o corte coronal mostra-a por inteiro.
              </p>
            </>
          ) : l ? (
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
          {!tensao && (
            <p className="mt-3 text-xs leading-relaxed text-texto2">
              Razão ao intacto: energia de deformação do osso na zona de Gruen (1: lateral; 7: medial, calcar) com a haste, a
              dividir pela do fémur intacto com a mesma malha. 1 = igual ao osso natural; abaixo de 1 = stress shielding
              (stress shielding = 1 − razão). Acima de 1 no Ti-6Al-4V poroso é efeito do modelo (haste colada, rigidez igual à
              do osso cortical), não um ganho clínico.
            </p>
          )}
        </Cartao>
      </div>

      {tensao && (
        <Cartao>
          <TituloCartao>Tensão de von Mises: todos os materiais lado a lado</TituloCartao>
          <DescricaoCartao>
            Mesma câmara e mesma escala de cores (de {num(ESCALA_MAPDL.min, 0)} a {num(ESCALA_MAPDL.max, 0)} MPa). Clica na imagem para ampliar.
          </DescricaoCartao>
          <div className="mt-3">
            <Ampliavel
              src={urlSimulacao(IMAGEM_COMPARACAO_MAPDL)}
              alt="Tensão de von Mises na haste e no fémur, cinco materiais lado a lado, vista de frente e corte coronal"
              legenda={`MAPDL, malha de ${num(MALHA_MAPDL, 1)} mm. ${NOTA_MAPDL}`}
            />
          </div>
        </Cartao>
      )}

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

      <CartaoMicromovimento />

      <BlocoVideo separador="fea" />
    </div>
  );
}
