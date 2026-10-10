//! Versão web: o núcleo `mcdm` compilado para WebAssembly, com os mesmos pedidos e respostas dos comandos Tauri
//! (src-tauri/src/lib.rs). Os pedidos e as respostas passam como texto JSON, para não acrescentar dependências.
//!
//! A preparação dos pedidos (pesos, exclusões, η) é a mesma da aplicação nativa; está repetida aqui porque a do
//! Tauri depende do próprio Tauri. Os testes deste crate comparam as duas com o mesmo pedido.

use std::collections::BTreeMap;
use std::sync::OnceLock;

use mcdm::metodos::{avaliar, avaliar_com_pesos, Metodo};
use mcdm::monte_carlo::{monte_carlo, OpcoesMonteCarlo, Variar};
use mcdm::perfis::{avaliar_perfil, excluir, Perfil, ResultadoPerfil};
use mcdm::pesos::{combinar_pesos, pesos_desvio_padrao, renormalizar};
use mcdm::{Caso, Problema, Ranking};
use serde::{Deserialize, Serialize};
use wasm_bindgen::prelude::*;

const DADOS: [(&str, &str); 5] = [
    ("Haste", include_str!("../../../dados/caso_haste.json")),
    ("Stent", include_str!("../../../dados/caso_stent.json")),
    ("Scaffold", include_str!("../../../dados/caso_scaffold.json")),
    ("Par articular", include_str!("../../../dados/caso_par_articular.json")),
    ("Implante dentário", include_str!("../../../dados/caso_implante_dentario.json")),
];

/// No navegador o Monte Carlo corre na linha da interface: limite mais baixo do que na aplicação nativa.
const MAX_ITERACOES: usize = 50_000;

fn casos() -> &'static BTreeMap<String, Caso> {
    static CASOS: OnceLock<BTreeMap<String, Caso>> = OnceLock::new();
    CASOS.get_or_init(|| {
        DADOS
            .iter()
            .map(|(n, t)| (n.to_string(), Caso::de_json(t).expect("dados dos casos inválidos")))
            .collect()
    })
}

fn caso(nome: &str) -> Result<&'static Caso, String> {
    casos().get(nome).ok_or_else(|| format!("caso desconhecido: {nome}"))
}

#[derive(Debug, Clone, Deserialize)]
pub struct PedidoCaso {
    pub caso: String,
    pub cenario: String,
    #[serde(default)]
    pub pesos: Option<Vec<f64>>,
    #[serde(default)]
    pub eta: Option<f64>,
    #[serde(default)]
    pub excluir: Vec<String>,
}

/// Igual a `preparar` da aplicação nativa: pesos do utilizador, exclusões e, por fim, η.
pub fn preparar(caso: &Caso, pedido: &PedidoCaso) -> Result<(Problema, Vec<String>), String> {
    let mut p = caso.problema(&pedido.cenario).map_err(|e| e.0)?.clone();
    if let Some(w) = &pedido.pesos {
        if w.len() != p.n() {
            return Err(format!("são precisos {} pesos e chegaram {}", p.n(), w.len()));
        }
        if w.iter().any(|v| !v.is_finite() || *v < 0.0) || w.iter().sum::<f64>() <= 0.0 {
            return Err("os pesos têm de ser positivos ou zero, e não podem ser todos zero".into());
        }
        p.pesos = renormalizar(w);
    }
    let excluidos = if pedido.excluir.is_empty() { Vec::new() } else { excluir(&mut p, &pedido.excluir).map_err(|e| e.0)? };
    if let Some(eta) = pedido.eta {
        if eta < 1.0 {
            let objetivos = pesos_desvio_padrao(&p.x_tipico, &p.tipos).map_err(|e| e.0)?;
            p.pesos = combinar_pesos(&p.pesos, &objetivos, eta).map_err(|e| e.0)?;
        }
    }
    Ok((p, excluidos))
}

#[derive(Debug, Clone, Serialize)]
pub struct RespostaCaso {
    pub problema: Problema,
    pub ranking: Ranking,
    pub excluidos: Vec<String>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct PedidoDoente {
    pub caso: String,
    pub cenario: String,
    pub perfil: Perfil,
}

#[derive(Debug, Clone, Serialize)]
pub struct RespostaDoente {
    pub base_problema: Problema,
    pub base: Ranking,
    pub resultado: ResultadoPerfil,
}

#[derive(Debug, Clone, Deserialize)]
pub struct PedidoMonteCarlo {
    #[serde(flatten)]
    pub base: PedidoCaso,
    pub n_iter: usize,
    pub variar: String,
    #[serde(default)]
    pub spread: Option<f64>,
    #[serde(default)]
    pub semente: Option<u64>,
}

#[derive(Debug, Clone, Serialize)]
pub struct ResumoMetodo {
    pub metodo: String,
    pub pct_primeiro: Vec<f64>,
    pub pct_segundo: Vec<f64>,
    pub posicao_media: Vec<f64>,
}

#[derive(Debug, Clone, Serialize)]
pub struct ResumoMonteCarlo {
    pub alternativas: Vec<String>,
    pub pedidas: usize,
    pub feitas: usize,
    pub parado: bool,
    pub metodos: Vec<ResumoMetodo>,
}

/// Ranking de um caso (TOPSIS, WASPAS, VIKOR e Borda), como o comando `avaliar_caso`.
pub fn avaliar_caso_json(pedido: &str) -> Result<String, String> {
    let pedido: PedidoCaso = serde_json::from_str(pedido).map_err(|e| e.to_string())?;
    let (problema, excluidos) = preparar(caso(&pedido.caso)?, &pedido)?;
    let ranking = avaliar_com_pesos(&problema, &problema.pesos);
    serde_json::to_string(&RespostaCaso { problema, ranking, excluidos }).map_err(|e| e.to_string())
}

/// Caso de base e resultado com o perfil do doente, como o comando `avaliar_doente`.
pub fn avaliar_doente_json(pedido: &str) -> Result<String, String> {
    let pedido: PedidoDoente = serde_json::from_str(pedido).map_err(|e| e.to_string())?;
    let c = caso(&pedido.caso)?;
    let base_problema = c.problema(&pedido.cenario).map_err(|e| e.0)?.clone();
    let base = avaliar(&base_problema);
    let resultado = avaliar_perfil(c, &pedido.perfil, &pedido.cenario).map_err(|e| e.0)?;
    serde_json::to_string(&RespostaDoente { base_problema, base, resultado }).map_err(|e| e.to_string())
}

/// Monte Carlo sem progresso nem paragem (no navegador corre de uma vez), como o comando `monte_carlo`.
pub fn monte_carlo_json(pedido: &str) -> Result<String, String> {
    let pedido: PedidoMonteCarlo = serde_json::from_str(pedido).map_err(|e| e.to_string())?;
    if pedido.n_iter < 1 || pedido.n_iter > MAX_ITERACOES {
        return Err(format!("no navegador o número de iterações tem de estar entre 1 e {MAX_ITERACOES}"));
    }
    let c = caso(&pedido.base.caso)?;
    let (problema, _) = preparar(c, &pedido.base)?;
    let omissao = OpcoesMonteCarlo::default();
    let variar = match pedido.variar.as_str() {
        "propriedades" => Variar::Propriedades,
        "pesos" => Variar::Pesos,
        outro => return Err(format!("o Monte Carlo varia \"propriedades\" ou \"pesos\", não {outro:?}")),
    };
    let op = OpcoesMonteCarlo {
        n_iter: pedido.n_iter,
        semente: pedido.semente.unwrap_or(omissao.semente),
        variar,
        spread: pedido.spread.unwrap_or(omissao.spread),
        incerteza_valor_unico: c.parametro("incerteza_valor_unico", omissao.incerteza_valor_unico),
    };
    let r = monte_carlo(&problema, &op).map_err(|e| e.0)?;
    let metodos = Metodo::TODOS
        .iter()
        .map(|&m| ResumoMetodo {
            metodo: m.nome().to_string(),
            pct_primeiro: r.pct_posicao(m, 1),
            pct_segundo: r.pct_posicao(m, 2),
            posicao_media: r.posicao_media(m),
        })
        .collect();
    let feitas = r.n_iter();
    serde_json::to_string(&ResumoMonteCarlo { alternativas: r.alternativas.clone(), pedidas: op.n_iter, feitas, parado: false, metodos })
        .map_err(|e| e.to_string())
}

#[wasm_bindgen]
pub fn avaliar_caso(pedido: &str) -> Result<String, JsValue> {
    avaliar_caso_json(pedido).map_err(|e| JsValue::from_str(&e))
}

#[wasm_bindgen]
pub fn avaliar_doente(pedido: &str) -> Result<String, JsValue> {
    avaliar_doente_json(pedido).map_err(|e| JsValue::from_str(&e))
}

#[wasm_bindgen]
pub fn monte_carlo_web(pedido: &str) -> Result<String, JsValue> {
    monte_carlo_json(pedido).map_err(|e| JsValue::from_str(&e))
}

#[cfg(test)]
mod testes {
    use super::*;

    #[test]
    fn ranking_da_haste_igual_ao_do_nucleo() {
        let r: serde_json::Value =
            serde_json::from_str(&avaliar_caso_json(r#"{"caso":"Haste","cenario":"A"}"#).unwrap()).unwrap();
        let p = caso("Haste").unwrap().problema("A").unwrap();
        let direto = avaliar(p);
        let c: Vec<f64> = serde_json::from_value(r["ranking"]["c_topsis"].clone()).unwrap();
        assert_eq!(c.len(), direto.c_topsis.len());
        for (a, b) in c.iter().zip(&direto.c_topsis) {
            assert!((a - b).abs() < 1e-12);
        }
    }

    #[test]
    fn erros_legiveis() {
        assert!(avaliar_caso_json(r#"{"caso":"Joelho","cenario":"A"}"#).unwrap_err().contains("caso desconhecido"));
        let e = monte_carlo_json(r#"{"caso":"Haste","cenario":"A","n_iter":0,"variar":"pesos"}"#).unwrap_err();
        assert!(e.contains("iterações"));
    }

    #[test]
    fn monte_carlo_curto() {
        let r: serde_json::Value = serde_json::from_str(
            &monte_carlo_json(r#"{"caso":"Stent","cenario":"A","n_iter":200,"variar":"propriedades"}"#).unwrap(),
        )
        .unwrap();
        assert_eq!(r["feitas"], 200);
        assert_eq!(r["metodos"].as_array().unwrap().len(), 3);
    }
}
