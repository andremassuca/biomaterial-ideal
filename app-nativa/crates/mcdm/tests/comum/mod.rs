//! Funções comuns aos testes: caminhos dos dados e leitura simples de CSV.
#![allow(dead_code)]

use std::path::PathBuf;

use mcdm::Caso;

/// Pasta do crate (app-nativa/crates/mcdm).
pub fn crate_dir() -> PathBuf {
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
}

/// Raiz do repositório.
pub fn raiz() -> PathBuf {
    crate_dir().join("..").join("..").join("..")
}

/// Ficheiro JSON de um caso em app-nativa/dados (scripts/exportar_app_json.py).
pub fn ficheiro_caso(caso: &str) -> PathBuf {
    let nome = match caso {
        "Haste" => "caso_haste.json",
        "Stent" => "caso_stent.json",
        "Scaffold" => "caso_scaffold.json",
        "Par articular" => "caso_par_articular.json",
        "Implante dentário" => "caso_implante_dentario.json",
        outro => panic!("caso desconhecido: {outro}"),
    };
    crate_dir().join("..").join("..").join("dados").join(nome)
}

/// Lê um caso; falha com uma indicação de como gerar os dados.
pub fn ler_caso(caso: &str) -> Caso {
    let f = ficheiro_caso(caso);
    Caso::ler(&f).unwrap_or_else(|e| panic!("{e}; corra python scripts/exportar_app_json.py"))
}

/// Divide uma linha de CSV (aspas duplas, "" dentro de aspas) em campos.
pub fn campos_csv(linha: &str) -> Vec<String> {
    let mut out = Vec::new();
    let mut atual = String::new();
    let mut aspas = false;
    let mut it = linha.chars().peekable();
    while let Some(c) = it.next() {
        match (c, aspas) {
            ('"', true) if it.peek() == Some(&'"') => {
                atual.push('"');
                it.next();
            }
            ('"', _) => aspas = !aspas,
            (',', false) => out.push(std::mem::take(&mut atual)),
            _ => atual.push(c),
        }
    }
    out.push(atual);
    out
}

/// Lê um CSV (sem quebras de linha dentro dos campos) como lista de linhas nome -> valor.
pub fn ler_csv(texto: &str) -> Vec<std::collections::HashMap<String, String>> {
    let mut linhas = texto.lines().filter(|l| !l.trim().is_empty());
    let cab = campos_csv(linhas.next().expect("CSV vazio"));
    linhas
        .map(|l| cab.iter().cloned().zip(campos_csv(l)).collect())
        .collect()
}

/// Compara duas listas de números com uma tolerância absoluta.
pub fn perto(rotulo: &str, a: &[f64], b: &[f64], tol: f64) {
    assert_eq!(a.len(), b.len(), "{rotulo}: tamanhos diferentes");
    for (i, (x, y)) in a.iter().zip(b).enumerate() {
        assert!((x - y).abs() <= tol, "{rotulo}[{i}]: Rust {x} vs Python {y} (tolerância {tol})");
    }
}
