# Fontes externas dos renders (malhas anatómicas, HDRI e texturas)

Os ficheiros não estão no repositório: descarregam-se com `python scripts/obter_recursos.py` para
recursos. Consultado a 6 out 2026.

## Linhas de atribuição (para o poster, a apresentação e a aplicação)

> Modelos anatómicos: BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0
> International. Modificados (secções, cortical e esponjoso gerados por campo de distância).
>
> Iluminação e texturas: Poly Haven (CC0).

## Malhas anatómicas: BodyParts3D (DBCLS)

- Base de dados: BodyParts3D, The Database Center for Life Science (DBCLS), versão 4.0, pacotes OBJ com
  "polygon reduction rate = 99 %": https://dbarchive.biosciencedbc.jp/en/bodyparts3d/download.html
- Licença: Creative Commons Attribution 4.0 International (CC BY 4.0), segundo a página de licença
  (atualizada a 27 fev 2025): https://dbarchive.biosciencedbc.jp/en/bodyparts3d/lic.html. A atribuição pedida é
  a da linha acima.
- Nota: o cabeçalho dos ficheiros OBJ ainda traz a licença antiga (CC BY-SA 2.1 Japão). Prevalece a página de
  licença atual (CC BY 4.0). Não é CC BY-SA, como estava no pedido.
- Modificações: secção coronal (anca) e bucolingual (mandíbula); osso cortical, esponjoso trabecular e canal
  medular gerados por campo de distância a partir da superfície; osteotomia do colo e fresagem do acetábulo; a
  coroa do implante usa a parte coronária do molar.

| ficheiro | estrutura | conceito FMA | pacote |
|---|---|---|---|
| FJ3152.obj | osso da anca direito (right hip bone) | FMA16586 | partof_BP3D_4.0_obj_99.zip |
| FJ3365.obj | fémur direito (right femur) | FMA24474 | partof_BP3D_4.0_obj_99.zip |
| FJ3289.obj | mandíbula (mandible) | FMA52748 | partof_BP3D_4.0_obj_99.zip |
| FJ1268.obj | 1.º molar inferior direito permanente | FMA55705 | isa_BP3D_4.0_obj_99.zip |
| FJ1269.obj | 1.º pré-molar inferior direito permanente | FMA55694 | isa_BP3D_4.0_obj_99.zip |
| FJ1270.obj | 2.º molar inferior direito permanente | FMA55706 | isa_BP3D_4.0_obj_99.zip |

Z-Anatomy (CC BY-SA 4.0) não foi usado: os modelos dele derivam do BodyParts3D, e a fonte original tem licença
mais simples (CC BY 4.0).

## HDRI e texturas: Poly Haven

- Licença: CC0 (domínio público), sem obrigação de atribuição; atribui-se na mesma, por cortesia:
  https://polyhaven.com/license
- HDRI "Studio Small 09" (studio_small_09, 2k, .hdr): https://polyhaven.com/a/studio_small_09
- Textura "Metal Plate" (metal_plate; mapas de rugosidade e de normais, 2k): https://polyhaven.com/a/metal_plate
  (micro-rugosidade do titânio e do Co-Cr)
- Textura "Clay Plaster" (clay_plaster; mapas de rugosidade e de normais, 2k): https://polyhaven.com/a/clay_plaster
  (micro-rugosidade da cerâmica e da superfície do osso)

A Poly Haven não tem texturas de metal escovado, de cerâmica médica nem de osso. Os riscos do escovado são
procedimentais (anisotropia e ruído esticado) e o osso esponjoso é geometria 3D, não textura.

## Modelos próprios

- Haste femoral e implante dentário (corpo, rosca, pilar): SolidWorks, scripts/cad_solidworks.py, cotas em
  design/cad/cotas.md.
- Stent, balão, artéria e placa, scaffold em giroide e trabéculas: procedimentais (scripts/geometria_3d.py e
  scripts/renders_blender.py).
