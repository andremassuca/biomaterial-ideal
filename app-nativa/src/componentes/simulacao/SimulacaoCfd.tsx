// Separador "Stent (CFD)": TAWSS, fração de área abaixo do limiar e OSI por material, mapas e verificações.
import { useState } from "react";
import { Cartao, DescricaoCartao, Etiqueta, TituloCartao } from "@/componentes/ui/cartao";
import { Opcoes } from "@/componentes/ui/controlos";
import { CFD } from "@/lib/dados";
import { num, pct } from "@/lib/formato";
import {
  LIMIAR_TAWSS_PA,
  NOTA_VERIFICACAO,
  comparacaoFluent,
  linhasCarreau,
  malhasCfd,
  materiaisCfd,
  urlSimulacao,
  verificacoesCfd,
} from "@/lib/simulacao";
import { Ampliavel } from "./Ampliavel";
import { BlocoVideo } from "./BlocoVideo";

/** Percentagem com uma casa decimal (36,8 %), como no relatório; o `pct` geral arredonda às unidades. */
function pct1(fracao: number): string {
  return `${num(fracao * 100, 1)} %`;
}

/** Cartão da repetição do fluxo pulsátil com sangue de Carreau: tabela e a frase do relatório v11.1 (secção 8). */
export function CartaoCarreau() {
  const linhas = linhasCarreau();
  if (linhas.length < 2) return null;
  const [fino, grosso] = linhas;
  return (
    <Cartao data-carreau>
      <TituloCartao>Verificação adicional: sangue não newtoniano (Carreau)</TituloCartao>
      <p className="mt-2 text-sm leading-relaxed">
        Como verificação adicional, repetiu-se o escoamento pulsátil com o sangue de Carreau, não newtoniano: a área da parede
        abaixo de {num(LIMIAR_TAWSS_PA, 1)} Pa passa de {pct1(fino.fracaoNewtoniano)} para {pct1(fino.fracaoCarreau)} com o strut de{" "}
        {num(fino.espessura_um, 0)} µm e de {pct1(grosso.fracaoNewtoniano)} para {pct1(grosso.fracaoCarreau)} com o de{" "}
        {num(grosso.espessura_um, 0)} µm, e a TAWSS média é de {num(fino.tauCarreau, 3)} e {num(grosso.tauCarreau, 3)} Pa; os
        valores absolutos mudam, mas a ordem entre as duas espessuras mantém-se.
      </p>
      <div className="mt-3 overflow-x-auto">
        <table className="tabela-limpa w-full text-left text-sm">
          <thead className="text-xs text-texto2">
            <tr>
              {[
                "Strut",
                "Área < 0,4 Pa, newtoniano",
                "Área < 0,4 Pa, Carreau",
                "TAWSS média, newtoniano (Pa)",
                "TAWSS média, Carreau (Pa)",
              ].map((c) => (
                <th key={c} className="py-1 pr-3 font-medium">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {linhas.map((l) => (
              <tr key={l.material} className="border-t border-linha">
                <td className="py-1.5 pr-3 font-medium">
                  {num(l.espessura_um, 0)} µm ({l.material})
                </td>
                <td className="numero py-1.5 pr-3">{pct1(l.fracaoNewtoniano)}</td>
                <td className="numero py-1.5 pr-3">{pct1(l.fracaoCarreau)}</td>
                <td className="numero py-1.5 pr-3">{num(l.tauNewtoniano, 3)}</td>
                <td className="numero py-1.5 pr-3">{num(l.tauCarreau, 3)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p role="note" className="mt-3 rounded-md border border-aviso/40 bg-aviso/10 px-3 py-2 text-xs font-medium text-texto">
        {NOTA_VERIFICACAO} Não demonstra reestenose nem trombose: geometria idealizada, sem lesão e parede rígida; {num(LIMIAR_TAWSS_PA, 1)} Pa
        é um limiar operacional deste estudo; não houve validação experimental.
      </p>
    </Cartao>
  );
}

/** Barra horizontal simples (0 a 1) para uma fração, com o valor escrito ao lado. */
export function BarraFracao({ fracao, rotulo }: { fracao: number; rotulo: string }) {
  const largura = Math.max(0, Math.min(1, fracao)) * 100;
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-linha" role="img" aria-label={`${rotulo}: ${pct(fracao * 100)}`}>
        <div className="h-full bg-acento" style={{ width: `${largura}%` }} />
      </div>
      <span className="numero w-14 text-right text-sm font-medium">{pct(fracao * 100)}</span>
    </div>
  );
}

/** Artigos que o projeto já usa para o limiar e para a hipótese de sangue newtoniano (docs/CFD_STENT.md). */
const FONTES = [
  "Malek AM, Alper SL, Izumo S. JAMA 1999;282:2035-42, doi:10.1001/jama.282.21.2035 (só resumo): abaixo de cerca de 0,4 Pa o endotélio passa a um fenótipo aterogénico.",
  "LaDisa JF et al. Am J Physiol Heart Circ Physiol 2005;288:H2465-75, doi:10.1152/ajpheart.01107.2004 (só resumo): em stents, as zonas de tensão de corte baixa associam-se à hiperplasia da neoíntima.",
  "Boldock et al., 2022 (viscosidade do sangue de 3,5 mPa·s) e Thondapu V et al. Front Cardiovasc Med 2022;9:835270 (sangue newtoniano acima de cerca de 100 a 200 1/s; um modelo não newtoniano daria menos área de corte baixo).",
];

export function SimulacaoCfd() {
  const materiais = materiaisCfd(CFD);
  const [material, setMaterial] = useState(materiais[0] ?? "");
  const r = CFD && material ? CFD[material] : null;
  const fluent = comparacaoFluent(material);
  const v = verificacoesCfd();

  return (
    <div className="space-y-6">
      <Cartao>
        <TituloCartao>O que é o TAWSS e porque se olha para 0,4 Pa</TituloCartao>
        <div className="mt-2 space-y-2 text-sm leading-relaxed">
          <p>
            O sangue a correr roça na parede da artéria, como a água num cano, e esse atrito chama-se tensão de corte na
            parede (WSS). O coração bate, por isso o atrito muda ao longo do ciclo: o TAWSS é a média no tempo dessa tensão
            num batimento. Zonas onde o TAWSS é baixo, como as que ficam entre e atrás dos struts, são onde o sangue quase não
            se renova, e associam-se a pior cicatrização e a mais crescimento de tecido dentro do stent.
          </p>
          <p>
            Usa-se {num(LIMIAR_TAWSS_PA, 1)} Pa como limiar: é um limiar operacional deste estudo, não um valor clínico
            exato. O resultado principal é a fração da parede, entre os struts, com TAWSS abaixo desse limiar. O OSI (índice de
            corte oscilatório) diz se o atrito muda de sentido: 0 quando aponta sempre para o mesmo lado, 0,5 quando muda
            de sentido metade do tempo.
          </p>
        </div>
        <details className="mt-3 text-sm">
          <summary className="cursor-pointer text-texto2">Fontes do limiar e das hipóteses</summary>
          <ul className="mt-2 list-disc space-y-1 pl-5 text-xs leading-relaxed text-texto2">
            {FONTES.map((f) => (
              <li key={f}>{f}</li>
            ))}
          </ul>
        </details>
      </Cartao>

      {CFD && r ? (
        <div className="grid gap-6 [&>*]:min-w-0 lg:grid-cols-[1fr_340px]">
          <Cartao>
            <TituloCartao>Mapas de TAWSS na parede da artéria, strut fino contra strut grosso</TituloCartao>
            <DescricaoCartao>Clica na imagem para ampliar.</DescricaoCartao>
            <div className="mt-3">
              <Ampliavel
                src={urlSimulacao("cfd/tawss_mapas.png")}
                alt="Mapas de TAWSS na parede da artéria com o strut fino e com o strut grosso"
                legenda="TAWSS (Pa) na parede da artéria, desenrolada, com os struts em branco. O sangue corre da esquerda para a direita. Barra de cores viridis de 0 a 1 Pa (na figura): roxo escuro é atrito baixo, amarelo é atrito alto. Em cima o strut fino, em baixo o grosso."
              />
            </div>
            <p className="mt-2 text-xs leading-relaxed text-texto2">
              TAWSS em Pa, escala de cores de 0 (roxo) a 1 Pa (amarelo), igual nos dois mapas; a barra vem na figura. Eixos: comprimento ao longo da artéria e arco, em mm.
            </p>
          </Cartao>

          <Cartao>
            <TituloCartao>Resultados por material</TituloCartao>
            <div className="mt-3">
              <Opcoes
                rotulo="Material do stent"
                valor={material}
                aoMudar={setMaterial}
                opcoes={materiais.map((m) => ({ valor: m, texto: m }))}
              />
            </div>
            <dl className="mt-3 space-y-2 text-sm">
              <div className="flex justify-between gap-3">
                <dt className="text-texto2">Espessura do strut (µm)</dt>
                <dd className="numero font-medium">{num(r.espessura_um, 0)}</dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-texto2">TAWSS média (Pa)</dt>
                <dd className="numero font-medium">{num(r.tau_media, 2)}</dd>
              </div>
              <div>
                <dt className="text-texto2">Parede com TAWSS abaixo de {num(LIMIAR_TAWSS_PA, 1)} Pa</dt>
                <dd>
                  <BarraFracao fracao={r.fracao_baixa} rotulo="Parede com TAWSS baixo" />
                </dd>
              </div>
              <div className="flex justify-between gap-3">
                <dt className="text-texto2">OSI médio</dt>
                <dd className="numero font-medium">{num(r.osi_media, 3)}</dd>
              </div>
              <div>
                <dt className="text-texto2">Parede com OSI acima de 0,1</dt>
                <dd>
                  <BarraFracao fracao={r.fracao_osi} rotulo="Parede com OSI alto" />
                </dd>
              </div>
            </dl>
            <p className="mt-3 text-xs leading-relaxed text-texto2">
              Fluxo pulsátil, malha média, sangue newtoniano (results/cfd_pulsatil.json). Com o OSI quase nulo por construção
              (onda de um só harmónico, sem inversão do caudal), o resultado que informa é a TAWSS.
            </p>
          </Cartao>
        </div>
      ) : (
        <Cartao>
          <Etiqueta tom="aviso">Sem resultados</Etiqueta>
          <p className="mt-2 text-sm">Os resultados da CFD ainda não foram exportados (app-nativa/dados/cfd_stent.json).</p>
        </Cartao>
      )}

      {CFD && (
        <Cartao>
          <TituloCartao>Os dois stents lado a lado</TituloCartao>
          <div className="mt-3 overflow-x-auto">
            <table className="tabela-limpa w-full text-left text-sm">
              <thead className="text-xs text-texto2">
                <tr>
                  {["Material", "Strut (µm)", "TAWSS média (Pa)", "Área com TAWSS baixo", "OSI médio", "Área com OSI alto"].map((c) => (
                    <th key={c} className="py-1 pr-3 font-medium">
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {materiais.map((m) => {
                  const x = CFD?.[m];
                  if (!x) return null;
                  return (
                    <tr key={m} className={`border-t border-linha ${m === material ? "bg-acento/10" : ""}`}>
                      <td className="py-1.5 pr-3 font-medium">{m}</td>
                      <td className="numero py-1.5 pr-3">{num(x.espessura_um, 0)}</td>
                      <td className="numero py-1.5 pr-3">{num(x.tau_media, 3)}</td>
                      <td className="numero py-1.5 pr-3">{pct(x.fracao_baixa * 100)}</td>
                      <td className="numero py-1.5 pr-3">{num(x.osi_media, 3)}</td>
                      <td className="numero py-1.5 pr-3">{pct(x.fracao_osi * 100)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </Cartao>
      )}

      <div className="grid gap-6 [&>*]:min-w-0 lg:grid-cols-2">
        <Cartao>
          <TituloCartao>Verificação: tubo sem stent (Poiseuille)</TituloCartao>
          <div className="mt-3">
            <Ampliavel
              src={urlSimulacao("cfd/poiseuille.png")}
              alt="Perfil de velocidade num tubo: teoria de Poiseuille e CFD"
              legenda="Velocidade axial (cm/s) contra a distância ao eixo (mm): solução teórica de Poiseuille (linha) e células da CFD (pontos)."
            />
          </div>
          <p className="mt-2 text-xs leading-relaxed text-texto2">
            Erros da CFD face à teoria: tensão de corte na parede {pct(v.erroTau * 100)}, queda de pressão{" "}
            {pct(v.erroQuedaPressao * 100)}, perfil de velocidade até {pct(v.erroPerfilMax * 100)} da velocidade no eixo.
          </p>
        </Cartao>

        <Cartao>
          <TituloCartao>Convergência da malha e segunda ferramenta</TituloCartao>
          <div className="mt-3 overflow-x-auto">
            <table className="tabela-limpa w-full text-left text-sm">
              <thead className="text-xs text-texto2">
                <tr>
                  {["Malha", "Células", "Junto à parede (µm)", "TAWSS (Pa)", "Área abaixo do limiar"].map((c) => (
                    <th key={c} className="py-1 pr-3 font-medium">
                      {c}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {malhasCfd(material).map((l) => (
                  <tr key={l.malha} className="border-t border-linha">
                    <td className="py-1.5 pr-3 font-medium">{l.malha}</td>
                    <td className="numero py-1.5 pr-3">{num(l.celulas, 0)}</td>
                    <td className="numero py-1.5 pr-3">{num(l.delta_um, 0)}</td>
                    <td className="numero py-1.5 pr-3">{num(l.tau_media, 3)}</td>
                    <td className="numero py-1.5 pr-3">{pct(l.fracao_baixa * 100)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {fluent && (
            <p className="mt-3 text-xs leading-relaxed text-texto2">
              Escoamento estacionário, malha média, {material}: OpenFOAM {pct(fluent.of_fracao_baixa * 100)} de área abaixo do
              limiar, Fluent {pct(fluent.fracao_baixa * 100)} (diferença de {num(Math.abs(fluent.diferencaFracaoPontos), 1)} pontos
              percentuais); TAWSS média {num(fluent.of_tau_media, 3)} contra {num(fluent.tau_media, 3)} Pa. Variação máxima
              da área entre malhas: {pct(v.variacaoMalhaArea * 100)}; ao dobrar os passos de tempo por ciclo: {pct(v.variacaoPassoArea * 100)}.
            </p>
          )}
        </Cartao>
      </div>

      <CartaoCarreau />

      <BlocoVideo separador="cfd" />

      <Cartao>
        <TituloCartao>O que ainda não existe nos resultados</TituloCartao>
        <ul className="mt-2 space-y-2 text-sm">
          <li className="flex flex-wrap items-center gap-2">
            <Etiqueta tom="aviso">Por gerar</Etiqueta>
            <span>Render em 4K do escoamento no stent.</span>
          </li>
        </ul>
      </Cartao>
    </div>
  );
}
