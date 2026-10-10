# Notas: normas_astm.csv e elementos_toxicidade.csv

Data de consulta de todas as fontes: 8 out 2026.

## Fontes e URLs exatos

### Normas ASTM (normas_astm.csv)
- Página de cada norma na loja da ASTM: `https://store.astm.org/standards/<norma>` (por exemplo,
  https://store.astm.org/standards/f67). O endereço www.astm.org/standards/f67 redireciona para o
  mesmo sítio. De cada página leu-se: título (etiqueta `<title>`), designação da edição atual
  (por exemplo, "ASTM F67-24"), etiqueta de estado ("Active") e data "Last Updated".
- Normas retiradas: a página mostra o título com "(Withdrawn AAAA)" e a última designação
  (F1341-99, F563-00, F745-07, F1873-98, F1876-98(2003)e1, F604-94).
- Equivalentes ISO: ficheiro de dados abertos da ISO (metadados oficiais das normas publicadas):
  https://isopublicstorageprod.blob.core.windows.net/opendata/_latest/iso_deliverables_metadata/json/iso_deliverables_metadata.jsonl
  (título, edição e fase: 60.60 publicada; 90.92 e 90.93 em vigor, em revisão ou confirmada; 95.99 retirada).
  As páginas www.iso.org/standard/... devolveram erro 403 (acesso bloqueado ao programa), por isso
  não foi possível ler nelas as correspondências com a ASTM.

### ICH Q3D(R2) (elementos_toxicidade.csv)
- PDF oficial: https://database.ich.org/sites/default/files/Q3D-R2_Guideline_Step4_2022_0308.pdf
  ("Guideline for Elemental Impurities Q3D(R2)", versão final adotada a 26 abr 2022).
- Classe: Tabela 5.1 ("Elements to be Considered in the Risk Assessment") e texto da secção 4
  (definição das classes 1, 2A, 2B e 3), p. 22 do PDF.
- PDE parentérica: Tabela A.2.1 ("Permitted Daily Exposures for Elemental Impurities"), Apêndice 2,
  p. 23 do PDF, em µg/dia (valores arredondados a 1 ou 2 algarismos significativos, nota 1 da tabela).

### IARC
- Página: https://monographs.iarc.who.int/list-of-classifications/
- Dados lidos do ficheiro que alimenta a tabela da página: https://webapi.iarc.who.int/loc/loc.app.js
  ("Agents Classified by the IARC Monographs, Volumes 1-142", "Last updated: 2026-07-23 14:08 (CET)";
  1128 agentes).

### Estado padrão e radioatividade
- PubChem, tabela periódica (CSV): https://pubchem.ncbi.nlm.nih.gov/rest/pug/periodictable/CSV
  (coluna StandardState).
- CIAAW (IUPAC), elementos radioativos: https://www.ciaaw.org/radioactive-elements.htm
  (lista dos isótopos mais estáveis dos elementos sem isótopos estáveis, segundo a NUBASE2020).
- CIAAW, bismuto: https://www.ciaaw.org/bismuth.htm (monoisotópico, Bi-209, com peso atómico padrão).
- Decaimento do Bi-209: de Marcillac P. et al., "Experimental detection of α-particles from the
  radioactive decay of natural bismuth", Nature 2003;422:876-878, doi:10.1038/nature01541
  (título, revista, volume e páginas confirmados na Crossref; o texto da Nature não abriu, por isso
  o CSV só indica "meia-vida da ordem de 10^19 anos"; o valor exato fica [confirmar] no artigo).

## Resultado

### Normas
- 73 normas ASTM confirmadas na página oficial (número, título e edição): 67 ativas e 6 retiradas.
- Todas as 25 normas pedidas estão incluídas e confirmadas. A F1873 (Y-TZP) foi retirada em 2007.
- Polímeros: F2026 (PEEK), F2820 (PEKK), F1925 (PLA semicristalino), F2579 (PLA amorfo e PLGA),
  F2313 (PGA e PGLA com 70 % ou mais de glicolido), F648, F2695, F2565, F2848 (UHMWPE), F451 (PMMA),
  F754 (PTFE), F702, F997, F1855, F2038, F2502 (placas e parafusos absorvíveis, especificação de
  dispositivo); retiradas F1876 (PEKEKK) e F604 (silicone).
- PCL: não se encontrou norma ASTM de especificação de policaprolactona para implantes.
- Magnésio: não se encontrou especificação ASTM de ligas de magnésio para implantes. Existem dois
  guias para metais absorvíveis, incluídos no CSV: F3160-21 (caracterização metalúrgica) e F3268-26
  (ensaios de degradação in vitro). Nenhum dos dois é especificação de material.
- Coluna extra "equivalente_ISO" (não pedida, acrescentada no fim). Só a ISO 5832-1:2024 tem
  correspondência declarada (UNS S31673 da F138 e F139), lida na descrição da página da ISO através
  de pesquisa; a página não abriu diretamente, por isso fica "A verificar". As restantes
  correspondências são por composição e ficam todas "A verificar". Edições ISO em vigor:
  5832-1:2024, 5832-2:2025, 5832-3:2021, 5832-4:2024, 5832-5:2022, 5832-6:2022, 5832-7:2024,
  5832-9:2019, 5832-11:2024, 5832-12:2019, 5832-14:2019 (Ti-15Mo-5Zr-3Al, sem norma ASTM no CSV),
  13782:2019 (Ta), 6474-1:2019 (alumina), 13356:2015 (Y-TZP), 5834-1:2025 e 5834-2:2025 (UHMWPE).
  Retiradas: 5832-8 (última edição 1997) e 5832-10 (última edição 1996).
- Os títulos da F1586, F3213 e F3302 têm na ASTM travessões (U+2013); foram trocados por hífenes,
  pela regra do projeto. O resto do texto dos títulos é o da ASTM.
- Colunas material e composicao_nominal: escritas a partir do título e do âmbito (secção 1.1) de cada
  norma. Os nomes comerciais entre parênteses (L605, MP35N, 316LVM, TMZF) são designações usuais,
  não constam dos títulos ASTM. As fórmulas da hidroxiapatite e do beta-TCP são as fórmulas químicas
  dos compostos, não valores da norma. Os limites de composição de cada norma não foram lidos
  (as normas são pagas).
- Ficaram de fora normas que não são de materiais (métodos de ensaio, terminologia, práticas):
  por exemplo F1408, F2005, F2602, F2759, F2902, F3335, F2183.

### Elementos
- 118 elementos. Classes ICH Q3D(R2): classe 1 = 4 (Cd, Pb, As, Hg); 2A = 3 (Co, V, Ni);
  2B = 10 (Tl, Au, Pd, Ir, Os, Rh, Ru, Se, Ag, Pt); 3 = 7 (Li, Sb, Ba, Mo, Cu, Sn, Cr); sem classe = 94.
  PDE parentérica preenchida para os 24 elementos com classe.
- Elementos sem PDE: a guideline diz que alguns elementos (por exemplo, Al, Mn, Zn, W) não estão
  abrangidos por terem baixa toxicidade intrínseca ou diferenças regionais; ficam vazios no CSV,
  o que não quer dizer que não sejam tóxicos.
- O histórico da guideline (correção de 2013) menciona que, na Tabela A.2.1, a classe do Ni foi
  mudada para 3; na versão R2 atual as Tabelas 5.1 e A.2.1 e o texto da secção 4 dão Ni = 2A.
  Usou-se 2A.
- Radioativos: 37 (Tc, Pm e Z de 84 a 118). Confere com a lista do CIAAW (que não inclui Th, Pa e U
  porque estes têm peso atómico padrão, mas também não têm isótopos estáveis).
- Bismuto: marcado "não (praticamente estável)". O CIAAW trata-o como monoisotópico com peso
  atómico padrão e não o inclui nos elementos radioativos; o Bi-209 decai por emissão alfa (de
  Marcillac et al. 2003).
- IARC: 24 elementos com classificação (grupo 1, 2A ou 2B). Critério: só agentes em que o elemento é
  o sujeito nomeado (o elemento, os seus compostos, óxidos, sais ou radionuclidos). A coluna diz o
  agente exato entre parênteses. Para P, Sr e I a classificação é só de radionuclidos (P-32, Sr-90,
  radioiodos); o elemento estável não está classificado.
- Agentes do IARC não atribuídos a nenhum elemento (para não classificar por inferência):
  produção de alumínio (grupo 1, exposição ocupacional), fundição de ferro e aço (grupo 1,
  exposição ocupacional), cisplatina (2A, fármaco com platina), complexo ferro-dextrano (2B),
  bromato de potássio (2B), arsenieto de gálio (remete para arsénio), radionuclidos emissores alfa
  ou beta depositados internamente (grupo 1, genérico).
- Agentes do IARC ligados a implantes, úteis para o funil (não estão no CSV por elemento):
  "Metallic implants prepared as thin smooth films" (2B); "Polymeric implant prepared as thin smooth
  films (with the exception of poly-glycolic acid)" (2B); "Implanted foreign bodies of metallic
  chromium or titanium and of cobalt-based, chromium-based, and titanium-based alloys, and stainless
  steel" (3); "Orthopaedic implants of complex composition and cardiac pacemakers" (3);
  "Ceramic implants" (3); "Silicone breast implants" (3).
- Estado padrão: valores do PubChem. Para Z de 100 a 118 o estado não foi determinado
  experimentalmente (o PubChem dá "Solid" até Mt e "Expected to be..." a partir de Ds); estes
  ficam com estado "A verificar" no campo do estado físico.
- Nomes em português: grafia usada em Portugal (por exemplo, azoto, árgon, crípton, xénon, rádon,
  ástato, tungsténio). Os nomes dos elementos 113 a 118 (nipónio, fleróvio, moscóvio, livermório,
  tenesso, oganésson) não foram confirmados numa fonte oficial portuguesa: [confirmar].

## O que ficou por confirmar
1. Correspondências ASTM-ISO (todas "A verificar"; a da ISO 5832-1 está quase confirmada).
2. Meia-vida exata do Bi-209 no artigo de Marcillac et al. 2003.
3. Estado físico de Z de 100 a 118 (valor do PubChem, não experimental).
4. Nomes portugueses dos elementos 113 a 118.
5. Existência de norma ASTM para PCL e para ligas de magnésio (não encontrada; a pesquisa na loja
   da ASTM foi por número e por pesquisa na web, não por catálogo completo).
