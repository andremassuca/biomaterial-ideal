//! Perfis de doente: mesmas regras que `src/biomat_mcdm/perfis.py` (data/perfis_doente.csv).
//!
//! Ordem de aplicação: 1) exclusões; 2) fatores de peso ("peso multiplicado" e "leitura do
//! problema"), com o maior fator quando várias regras mexem no mesmo critério, e uma única
//! renormalização; 3) critério acrescentado, com o peso exato da tabela; as notas só se
//! devolvem. Sem regra para o sexo.

use std::collections::BTreeMap;

use serde::{Deserialize, Serialize};

use crate::dados::{Caso, Problema, Regra, Tipo};
use crate::metodos::{avaliar, Ranking};
use crate::pesos::renormalizar;
use crate::{erro, Erro};

/// Valor de um dado do doente: número (idade, IMC, mm) ou texto ("sim", "alta", "com_carga").
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
#[serde(untagged)]
pub enum ValorPerfil {
    Num(f64),
    Texto(String),
}

/// Dados do doente: nome do dado -> valor (ex.: "idade" -> 40, "osteoporose" -> "sim").
pub type Perfil = BTreeMap<String, ValorPerfil>;

/// Converte para número (aceita vírgula decimal).
fn numero(v: &ValorPerfil) -> Option<f64> {
    match v {
        ValorPerfil::Num(x) => Some(*x),
        ValorPerfil::Texto(s) => texto_numero(s),
    }
}

fn texto_numero(s: &str) -> Option<f64> {
    s.trim().replace(',', ".").parse::<f64>().ok()
}

fn texto(v: &ValorPerfil) -> String {
    match v {
        ValorPerfil::Num(x) => x.to_string(),
        ValorPerfil::Texto(s) => s.clone(),
    }
}

/// Diz se o perfil cumpre um condicao_codigo (condições separadas por "; ", todas obrigatórias).
/// Um dado que falta no perfil conta como "não se verifica".
pub fn condicao_cumprida(codigo: &str, perfil: &Perfil) -> Result<bool, Erro> {
    for parte in codigo.split(';') {
        let parte = parte.trim();
        if parte.is_empty() {
            continue;
        }
        let pos = match parte.find(['<', '>', '=']) {
            Some(p) => p,
            None => return erro(format!("condição ilegível: {parte:?}")),
        };
        let chave = parte[..pos].trim();
        let resto = &parte[pos..];
        let op = if resto.starts_with("<=") || resto.starts_with(">=") { &resto[..2] } else { &resto[..1] };
        let esperado = resto[op.len()..].trim();
        if chave.is_empty() || !chave.chars().all(|c| c.is_alphanumeric() || c == '_') || esperado.is_empty() {
            return erro(format!("condição ilegível: {parte:?}"));
        }
        let dado = match perfil.get(chave) {
            Some(d) => d,
            None => return Ok(false),
        };
        if op == "=" {
            let iguais = match (numero(dado), texto_numero(esperado)) {
                (Some(a), Some(b)) => a == b,
                _ => texto(dado).trim().to_lowercase() == esperado.to_lowercase(),
            };
            if !iguais {
                return Ok(false);
            }
            continue;
        }
        let (a, b) = match (numero(dado), texto_numero(esperado)) {
            (Some(a), Some(b)) => (a, b),
            _ => return erro(format!("comparação numérica com valor não numérico: {parte:?}")),
        };
        let ok = match op {
            "<" => a < b,
            "<=" => a <= b,
            ">" => a > b,
            _ => a >= b,
        };
        if !ok {
            return Ok(false);
        }
    }
    Ok(true)
}

/// Regras do caso que o doente ativa, pela ordem da tabela.
pub fn regras_ativas(caso: &Caso, perfil: &Perfil) -> Result<Vec<Regra>, Erro> {
    let mut out = Vec::new();
    for r in caso.regras.iter().filter(|r| r.dispositivo == caso.caso_componente) {
        if condicao_cumprida(&r.condicao_codigo, perfil)? {
            out.push(r.clone());
        }
    }
    Ok(out)
}

fn valor_regra(r: &Regra) -> Result<f64, Erro> {
    match r.valor.as_deref().and_then(texto_numero) {
        Some(v) => Ok(v),
        None => erro(format!("regra {} sem valor numérico", r.id)),
    }
}

/// Tira materiais do problema; devolve os que saíram de facto. Erro se ficarem menos de dois.
pub fn excluir(p: &mut Problema, materiais: &[String]) -> Result<Vec<String>, Erro> {
    let ficam: Vec<usize> = (0..p.m()).filter(|&i| !materiais.contains(&p.alternativas[i])).collect();
    if ficam.len() < 2 {
        return erro("a exclusão deixa menos de dois materiais");
    }
    let sai: Vec<String> = p.alternativas.iter().filter(|a| materiais.contains(a)).cloned().collect();
    p.alternativas = ficam.iter().map(|&i| p.alternativas[i].clone()).collect();
    p.x_min = ficam.iter().map(|&i| p.x_min[i].clone()).collect();
    p.x_max = ficam.iter().map(|&i| p.x_max[i].clone()).collect();
    p.x_tipico = ficam.iter().map(|&i| p.x_tipico[i].clone()).collect();
    Ok(sai)
}

/// Multiplica o peso de cada critério pelo seu fator e renormaliza (soma 1).
pub fn multiplicar_pesos(p: &mut Problema, fatores: &BTreeMap<String, f64>) -> Result<(), Erro> {
    let mut w = p.pesos.clone();
    for (crit, &f) in fatores {
        if f <= 0.0 {
            return erro("o fator tem de ser positivo");
        }
        match p.criterios.iter().position(|c| c == crit) {
            Some(j) => w[j] *= f,
            None => return erro(format!("critério da regra não existe no problema: {crit:?}")),
        }
    }
    p.pesos = renormalizar(&w);
    Ok(())
}

/// Separa "Teor de níquel (custo)" em ("Teor de níquel", Custo).
fn criterio_acrescentado(alvo: &str) -> Result<(String, Tipo), Erro> {
    let alvo = alvo.trim();
    for (suf, t) in [("(custo)", Tipo::Custo), ("(benefício)", Tipo::Beneficio)] {
        if let Some(nome) = alvo.strip_suffix(suf) {
            return Ok((nome.trim().to_string(), t));
        }
    }
    erro(format!("critério acrescentado sem tipo (custo ou benefício): {alvo:?}"))
}

/// Acrescenta um critério com o peso dado; os outros ficam com (1 - peso) na mesma proporção.
pub fn acrescentar_criterio(p: &mut Problema, caso: &Caso, propriedade: &str, tipo: Tipo, peso: f64) -> Result<(), Erro> {
    if !(peso > 0.0 && peso < 1.0) {
        return erro("o peso do critério acrescentado tem de estar em ]0, 1[");
    }
    let valores = match caso.propriedades_extra.get(propriedade) {
        Some(v) => v,
        None => return erro(format!("{propriedade:?} não está nos dados do caso")),
    };
    let falta: Vec<&String> = p.alternativas.iter().filter(|a| !valores.contains_key(*a)).collect();
    if !falta.is_empty() {
        return erro(format!("{propriedade:?} sem valor para: {falta:?}"));
    }
    if tipo == Tipo::Custo && p.alternativas.iter().any(|a| valores[a].min < 0.0) {
        return erro(format!("{propriedade:?} tem valores negativos num critério de custo"));
    }
    for (i, a) in p.alternativas.iter().enumerate() {
        let v = valores[a];
        p.x_min[i].push(v.min);
        p.x_max[i].push(v.max);
        p.x_tipico[i].push(v.tipico);
    }
    p.criterios.push(propriedade.to_string());
    p.tipos.push(tipo);
    p.alvos.push(None);
    p.ordinal.push(propriedade.contains("ordinal") || propriedade.contains("(1-5"));
    p.pesos = p.pesos.iter().map(|w| w * (1.0 - peso)).chain(std::iter::once(peso)).collect();
    Ok(())
}

/// Ligações do problema crítico pedidas por uma regra "leitura do problema".
fn leitura(alvo: &str) -> Result<&'static [&'static str], Erro> {
    if alvo.contains("leitura literal") {
        Ok(&["direta"])
    } else if alvo.contains("leitura ampla") {
        Ok(&["direta", "indireta"])
    } else {
        erro(format!("leitura do problema desconhecida: {alvo:?}"))
    }
}

/// Resultado de um perfil: problema ajustado, ranking e o que mudou.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ResultadoPerfil {
    pub problema: Problema,
    pub ranking: Ranking,
    pub regras: Vec<Regra>,
    pub excluidos: Vec<String>,
    pub notas: Vec<String>,
}

/// Aplica as regras ativas a um problema; devolve (problema ajustado, excluídos, notas).
pub fn aplicar_regras(base: &Problema, caso: &Caso, regras: &[Regra]) -> Result<(Problema, Vec<String>, Vec<String>), Erro> {
    let mut p = base.clone();
    let (mut excluidos, mut notas) = (Vec::new(), Vec::new());
    let mut fatores: BTreeMap<String, f64> = BTreeMap::new();
    let mut acrescentar = Vec::new();
    for r in regras {
        match r.efeito.as_str() {
            "exclusão" => {
                let lista: Vec<String> = r.alvo_do_efeito.split(';').map(|s| s.trim().to_string()).collect();
                excluidos.extend(excluir(&mut p, &lista)?);
            }
            "nota" => notas.push(r.alvo_do_efeito.clone()),
            "peso multiplicado" => {
                let f = valor_regra(r)?;
                let e = fatores.entry(r.alvo_do_efeito.clone()).or_insert(0.0);
                *e = e.max(f);
            }
            "leitura do problema" => {
                let f = valor_regra(r)?;
                for lig in leitura(&r.alvo_do_efeito)? {
                    for crit in caso.problemas_criticos.get(*lig).into_iter().flatten() {
                        if p.criterios.contains(crit) {
                            let e = fatores.entry(crit.clone()).or_insert(0.0);
                            *e = e.max(f);
                        }
                    }
                }
            }
            "critério acrescentado" => acrescentar.push(r),
            outro => return erro(format!("efeito desconhecido: {outro:?}")),
        }
    }
    if !fatores.is_empty() {
        multiplicar_pesos(&mut p, &fatores)?;
    }
    for r in acrescentar {
        let (prop, tipo) = criterio_acrescentado(&r.alvo_do_efeito)?;
        acrescentar_criterio(&mut p, caso, &prop, tipo, valor_regra(r)?)?;
    }
    Ok((p, excluidos, notas))
}

/// Ponto de entrada: ranking de um caso e cenário para um doente. Perfil vazio = caso de base.
pub fn avaliar_perfil(caso: &Caso, perfil: &Perfil, cenario: &str) -> Result<ResultadoPerfil, Erro> {
    let base = caso.problema(cenario)?;
    let regras = regras_ativas(caso, perfil)?;
    let (problema, excluidos, notas) = aplicar_regras(base, caso, &regras)?;
    let ranking = avaliar(&problema);
    Ok(ResultadoPerfil { problema, ranking, regras, excluidos, notas })
}

#[cfg(test)]
mod testes {
    use super::*;

    fn perfil(pares: &[(&str, ValorPerfil)]) -> Perfil {
        pares.iter().map(|(k, v)| (k.to_string(), v.clone())).collect()
    }

    #[test]
    fn condicoes() {
        use ValorPerfil::*;
        let p = perfil(&[("idade", Num(40.0)), ("atividade", Texto("Alta".into())), ("imc", Texto("34,9".into()))]);
        assert!(condicao_cumprida("idade<60; atividade=alta", &p).unwrap());
        assert!(!condicao_cumprida("idade<40", &p).unwrap());
        assert!(condicao_cumprida("idade<=40", &p).unwrap());
        assert!(!condicao_cumprida("imc>=35", &p).unwrap());
        assert!(!condicao_cumprida("osteoporose=sim", &p).unwrap()); // dado em falta
        assert!(condicao_cumprida("idade ~ 3", &p).is_err());
        assert!(condicao_cumprida("atividade<3", &p).is_err());
    }

    #[test]
    fn criterio_acrescentado_le_o_tipo() {
        assert_eq!(criterio_acrescentado("Teor de níquel (custo)").unwrap(), ("Teor de níquel".to_string(), Tipo::Custo));
        assert!(criterio_acrescentado("Teor de níquel").is_err());
    }
}
