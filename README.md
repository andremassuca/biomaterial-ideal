<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="design/logo/logo_completo_fundo_escuro.svg">
    <img src="design/logo/logo_completo.svg" alt="Biomaterial ideal" width="420">
  </picture>
</p>

# Qual é o biomaterial ideal?

Seleção multicritério de biomateriais com **critérios-alvo** e **análise de robustez**, aplicada a cinco componentes implantáveis: haste femoral, par articular da anca, stent coronário, scaffold ósseo e implante dentário.

**Versão web interativa:** <https://andremassuca.github.io/biomaterial-ideal/>

Trabalho de André Oliveira Massuça (Engenharia Biomédica, Universidade Lusófona) para a unidade curricular de Próteses e Órgãos Artificiais. Docente: Prof. Pedro Sampaio.

> Este trabalho não é uma ferramenta clínica nem uma recomendação terapêutica.

## Pergunta

A escolha do biomaterial mantém-se quando mudam o método de decisão, os pesos e a incerteza nas propriedades?

## Método

```
dados com fonte (CSV) → critérios-alvo → TOPSIS · WASPAS · VIKOR (e consenso de Borda)
                      → Monte Carlo das propriedades e dos pesos → resposta e grau de confiança
```

Base metodológica: Petković, Madić e Mitković, *Appl. Sci.* 2025, 15(16), 9198 (doi:10.3390/app15169198). Cada valor da base tem fonte e estado ("Verificado", "A verificar" ou "Valor de modelação"); 114 dos 300 valores estão verificados em fontes primárias.

## Resultados (relatório v11, 11 out 2026)

| Caso | Resposta |
|---|---|
| Haste femoral | Ti-6Al-4V ELI em haste não cimentada (a conclusão mais estável: 1.º com os três métodos e em pelo menos 9 999 de 10 000 repetições do Monte Carlo) |
| Stent coronário | Pt-Cr e L605 praticamente equivalentes: o Pt-Cr é favorecido pelo TOPSIS, pelo VIKOR e pela radiopacidade; o L605 pelo WASPAS e por ter todas as propriedades em fichas de fornecedor. Sem vencedor universal. |
| Scaffold ósseo | Depende da carga: compósito PCL/β-TCP impresso quando o defeito suporta carga (1.º no ranking direto em 5 das 6 combinações); β-TCP poroso quando não suporta (mais vezes 1.º na incerteza dos dados). |
| Par articular | ZTA/ZTA com a melhor pontuação (análise semiquantitativa, centrada no desgaste) |
| Implante dentário | Titânio comercialmente puro de grau 4 (análise semiquantitativa) |

As simulações de elementos finitos (haste) e de escoamento (stent) são exploratórias e foram verificadas numericamente entre ferramentas (Python, SOLIDWORKS e Ansys; OpenFOAM e Ansys Fluent); não foram validadas experimentalmente.

## Estrutura

```
data/             CSV (fonte de verdade) e leia_me.md; o .xlsx é gerado por scripts/exportar_xlsx.py
src/biomat_mcdm/  leitura dos dados, normalização, pesos, TOPSIS, WASPAS, VIKOR, robustez e perfis de doente
scripts/          run_all.py (todos os cenários), figuras, tabelas do relatório, verificadores e auditoria
results/          rankings, Monte Carlo, robustez e figuras gerados
relatorio/        rascunhos e tabelas do relatório (sem o PDF)
app-nativa/       aplicação (Tauri 2, React e TypeScript, núcleo em Rust e WebAssembly) e versão web
tests/            testes automáticos (pytest)
```

## Como reproduzir

```bash
pip install -e ".[dev]"
pytest -q
python scripts/run_all.py
```

## Licenças

Código: MIT (LICENSE). Dados, resultados e textos: CC BY 4.0 (LICENCA_DADOS.md).

## Autor

André Oliveira Massuça, ORCID [0009-0005-1527-843X](https://orcid.org/0009-0005-1527-843X)
