//! Estruturas de dados lidas dos JSON de `app-nativa/dados/` (scripts/exportar_app_json.py).

use std::collections::BTreeMap;
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::{erro, Erro};

/// Tipo de critério (Petković et al. 2025): benefício, custo ou alvo.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Tipo {
    /// Maior é melhor.
    #[serde(rename = "benefit")]
    Beneficio,
    /// Menor é melhor.
    #[serde(rename = "cost")]
    Custo,
    /// Mais próximo do valor-alvo é melhor.
    #[serde(rename = "target")]
    Alvo,
}

/// Um problema de decisão pronto para os métodos (equivalente ao DecisionProblem do Python).
///
/// As matrizes guardam uma linha por material e uma coluna por critério.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Problema {
    pub alternativas: Vec<String>,
    pub criterios: Vec<String>,
    pub tipos: Vec<Tipo>,
    pub alvos: Vec<Option<f64>>,
    pub pesos: Vec<f64>,
    pub x_min: Vec<Vec<f64>>,
    pub x_max: Vec<Vec<f64>>,
    /// Valores usados nos métodos (o típico da base).
    pub x_tipico: Vec<Vec<f64>>,
    /// Critérios ordinais (1-5): não variam no Monte Carlo.
    pub ordinal: Vec<bool>,
}

impl Problema {
    /// Número de materiais (linhas).
    pub fn m(&self) -> usize {
        self.alternativas.len()
    }

    /// Número de critérios (colunas).
    pub fn n(&self) -> usize {
        self.criterios.len()
    }

    /// Verifica se as dimensões batem certo (um tipo, alvo, peso e coluna por critério).
    pub fn validar(&self) -> Result<(), Erro> {
        let (m, n) = (self.m(), self.n());
        if self.tipos.len() != n || self.alvos.len() != n || self.pesos.len() != n || self.ordinal.len() != n {
            return erro("o número de tipos, alvos, pesos ou marcas ordinais não é igual ao de critérios");
        }
        for x in [&self.x_min, &self.x_max, &self.x_tipico] {
            if x.len() != m || x.iter().any(|l| l.len() != n) {
                return erro("as matrizes têm de ter uma linha por material e uma coluna por critério");
            }
        }
        for (j, t) in self.tipos.iter().enumerate() {
            if *t == Tipo::Alvo && self.alvos[j].is_none() {
                return erro(format!("critério-alvo sem valor-alvo: {}", self.criterios[j]));
            }
        }
        Ok(())
    }
}

/// Mínimo, máximo e típico de uma propriedade de um material.
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct Intervalo {
    pub min: f64,
    pub max: f64,
    pub tipico: f64,
}

/// Uma regra de data/perfis_doente.csv (as colunas de texto podem vir vazias).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Regra {
    pub id: String,
    pub dispositivo: String,
    #[serde(default)]
    pub condicao: Option<String>,
    pub condicao_codigo: String,
    pub efeito: String,
    pub alvo_do_efeito: String,
    #[serde(default)]
    pub valor: Option<String>,
    #[serde(default)]
    pub justificacao: Option<String>,
    #[serde(default)]
    pub fonte: Option<String>,
    #[serde(default)]
    pub doi_url: Option<String>,
    #[serde(default)]
    pub estado: Option<String>,
}

/// Um perfil de exemplo (casos de referência da especificação da aplicação).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct PerfilReferencia {
    pub descricao: String,
    pub perfil: crate::perfis::Perfil,
}

/// Tudo o que a aplicação precisa de um caso (um ficheiro caso_*.json).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Caso {
    pub caso: String,
    pub caso_componente: String,
    pub parametros: BTreeMap<String, f64>,
    /// Problemas dos cenários ("A", "B").
    pub cenarios: BTreeMap<String, Problema>,
    /// Propriedades pedidas pelas regras "critério acrescentado": propriedade -> material -> valores.
    pub propriedades_extra: BTreeMap<String, BTreeMap<String, Intervalo>>,
    /// Critérios do problema crítico por ligação ("direta", "indireta").
    pub problemas_criticos: BTreeMap<String, Vec<String>>,
    pub regras: Vec<Regra>,
    pub perfis_referencia: BTreeMap<String, PerfilReferencia>,
}

impl Caso {
    /// Lê um caso de texto JSON.
    pub fn de_json(texto: &str) -> Result<Caso, Erro> {
        let caso: Caso = serde_json::from_str(texto).map_err(|e| Erro(format!("JSON inválido: {e}")))?;
        for p in caso.cenarios.values() {
            p.validar()?;
        }
        Ok(caso)
    }

    /// Lê um caso de um ficheiro JSON.
    pub fn ler(caminho: impl AsRef<Path>) -> Result<Caso, Erro> {
        let texto = std::fs::read_to_string(caminho.as_ref())
            .map_err(|e| Erro(format!("não foi possível ler {}: {e}", caminho.as_ref().display())))?;
        Caso::de_json(&texto)
    }

    /// Problema de um cenário ("A" ou "B").
    pub fn problema(&self, cenario: &str) -> Result<&Problema, Erro> {
        match self.cenarios.get(cenario) {
            Some(p) => Ok(p),
            None => erro(format!("cenário desconhecido neste caso: {cenario:?}")),
        }
    }

    /// Parâmetro de desenho (data/parametros.csv), com um valor por omissão.
    pub fn parametro(&self, nome: &str, omissao: f64) -> f64 {
        self.parametros.get(nome).copied().unwrap_or(omissao)
    }
}
