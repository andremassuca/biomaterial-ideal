//! Pesos objetivos (desvio-padrão) e combinação com o nível de confiança η (eq. 1),
//! iguais a `src/biomat_mcdm/weights.py`.

use crate::dados::Tipo;
use crate::{erro, Erro};

/// Pesos objetivos pelo método do desvio-padrão.
///
/// Cada coluna é posta na mesma escala (benefício e alvo: x / máx; custo: mín / x), mede-se a
/// dispersão (desvio-padrão) e os pesos são as dispersões divididas pela sua soma.
pub fn pesos_desvio_padrao(x: &[Vec<f64>], tipos: &[Tipo]) -> Result<Vec<f64>, Erro> {
    let m = x.len();
    if m == 0 || x.iter().any(|l| l.len() != tipos.len()) {
        return erro("x tem de ser (m, n) com um tipo por coluna");
    }
    if x.iter().flatten().any(|&v| v <= 0.0) {
        return erro("o método do desvio-padrão usado aqui exige valores positivos");
    }
    let mut sigma = Vec::with_capacity(tipos.len());
    for (j, t) in tipos.iter().enumerate() {
        let c: Vec<f64> = x.iter().map(|l| l[j]).collect();
        let esc: Vec<f64> = match t {
            Tipo::Beneficio | Tipo::Alvo => {
                let mx = c.iter().copied().fold(f64::NEG_INFINITY, f64::max);
                c.iter().map(|v| v / mx).collect()
            }
            Tipo::Custo => {
                let mn = c.iter().copied().fold(f64::INFINITY, f64::min);
                c.iter().map(|v| mn / v).collect()
            }
        };
        let media = esc.iter().sum::<f64>() / m as f64;
        let var = esc.iter().map(|v| (v - media).powi(2)).sum::<f64>() / m as f64;
        sigma.push(var.sqrt());
    }
    let soma: f64 = sigma.iter().sum();
    if soma == 0.0 {
        return erro("todas as colunas são constantes: pesos objetivos indefinidos");
    }
    Ok(sigma.iter().map(|s| s / soma).collect())
}

/// Combinação linear w = η·w_subjetivo + (1 - η)·w_objetivo (eq. 1), com η em [0, 1].
pub fn combinar_pesos(subjetivos: &[f64], objetivos: &[f64], eta: f64) -> Result<Vec<f64>, Erro> {
    if !(0.0..=1.0).contains(&eta) {
        return erro("η tem de estar entre 0 e 1");
    }
    if subjetivos.len() != objetivos.len() {
        return erro("os dois vetores de pesos têm de ter o mesmo tamanho");
    }
    for (nome, w) in [("subjetivos", subjetivos), ("objetivos", objetivos)] {
        if w.iter().any(|&v| v < 0.0) || (w.iter().sum::<f64>() - 1.0).abs() > 1e-3 {
            return erro(format!("os pesos {nome} têm de ser ≥ 0 e somar 1"));
        }
    }
    Ok(subjetivos.iter().zip(objetivos).map(|(s, o)| eta * s + (1.0 - eta) * o).collect())
}

/// Divide os pesos pela sua soma, para que voltem a somar 1.
pub fn renormalizar(pesos: &[f64]) -> Vec<f64> {
    let soma: f64 = pesos.iter().sum();
    pesos.iter().map(|w| w / soma).collect()
}

#[cfg(test)]
mod testes {
    use super::*;

    #[test]
    fn coluna_constante_tem_peso_zero() {
        let x = vec![vec![1.0, 5.0], vec![2.0, 5.0]];
        let w = pesos_desvio_padrao(&x, &[Tipo::Beneficio, Tipo::Custo]).unwrap();
        assert_eq!(w, vec![1.0, 0.0]);
    }

    #[test]
    fn eta_extremos() {
        let s = [0.7, 0.3];
        let o = [0.2, 0.8];
        assert_eq!(combinar_pesos(&s, &o, 1.0).unwrap(), s.to_vec());
        assert_eq!(combinar_pesos(&s, &o, 0.0).unwrap(), o.to_vec());
        assert!(combinar_pesos(&s, &o, 1.5).is_err());
    }

    #[test]
    fn valores_nao_positivos_dao_erro() {
        assert!(pesos_desvio_padrao(&[vec![0.0], vec![1.0]], &[Tipo::Custo]).is_err());
    }
}
