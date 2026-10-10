//! Núcleo de cálculo da aplicação "Biomaterial Ideal".
//!
//! Reimplementa em Rust as funções de `src/biomat_mcdm` (Python), que são a referência:
//! normalização com critérios-alvo, TOPSIS, WASPAS e VIKOR (Petković et al., Appl. Sci. 2025,
//! 15(16), 9198), consenso de Borda, pesos objetivos do desvio-padrão e nível de confiança η,
//! Monte Carlo das propriedades e dos pesos, e perfis de doente (data/perfis_doente.csv).
//!
//! Os dados entram por JSON, gerado por `scripts/exportar_app_json.py` (um ficheiro por caso em
//! `app-nativa/dados/`). Os testes comparam os resultados com o Python até 1e-6.

pub mod dados;
pub mod metodos;
pub mod monte_carlo;
pub mod normalizacao;
pub mod perfis;
pub mod pesos;

pub use dados::{Caso, Problema, Tipo};
pub use metodos::{avaliar, Metodo, Ranking};
pub use monte_carlo::{monte_carlo, OpcoesMonteCarlo, ResultadoMonteCarlo, Variar};
pub use perfis::{avaliar_perfil, Perfil, ResultadoPerfil, ValorPerfil};

/// Erro do núcleo, com uma mensagem em português.
#[derive(Debug, Clone, PartialEq)]
pub struct Erro(pub String);

impl std::fmt::Display for Erro {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str(&self.0)
    }
}

impl std::error::Error for Erro {}

/// Atalho para criar um erro a partir de texto.
pub(crate) fn erro<T>(msg: impl Into<String>) -> Result<T, Erro> {
    Err(Erro(msg.into()))
}
