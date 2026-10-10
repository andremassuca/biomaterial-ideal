//! Normalização linear com critérios benefício, custo e alvo (eq. 2 de Petković et al. 2025),
//! igual a `src/biomat_mcdm/normalization.py`.
//!
//! r_ij = 1 - |x_ij - T_j| / (max(x_j^max, T_j) - min(x_j^min, T_j)), com r em [0, 1] e 1 = melhor.

use crate::dados::Tipo;

/// Coluna j de uma matriz guardada por linhas.
pub fn coluna(x: &[Vec<f64>], j: usize) -> Vec<f64> {
    x.iter().map(|l| l[j]).collect()
}

/// Máximo de uma lista.
pub fn maximo(v: &[f64]) -> f64 {
    v.iter().copied().fold(f64::NEG_INFINITY, f64::max)
}

/// Mínimo de uma lista.
pub fn minimo(v: &[f64]) -> f64 {
    v.iter().copied().fold(f64::INFINITY, f64::min)
}

/// Valor de referência T_j: o máximo (benefício), o mínimo (custo) ou o valor-alvo (alvo).
pub fn valor_referencia(col: &[f64], tipo: Tipo, alvo: Option<f64>) -> f64 {
    match tipo {
        Tipo::Beneficio => maximo(col),
        Tipo::Custo => minimo(col),
        Tipo::Alvo => alvo.expect("critério-alvo sem valor-alvo"),
    }
}

/// Normaliza uma coluna com a eq. 2; coluna constante e igual a T dá 1 em todas.
pub fn normalizar_coluna(col: &[f64], tipo: Tipo, alvo: Option<f64>) -> Vec<f64> {
    let t = valor_referencia(col, tipo, alvo);
    let denom = maximo(col).max(t) - minimo(col).min(t);
    if denom == 0.0 {
        return vec![1.0; col.len()];
    }
    col.iter().map(|x| 1.0 - (x - t).abs() / denom).collect()
}

/// Normaliza a matriz (m, n) coluna a coluna; devolve outra matriz por linhas.
pub fn normalizar_matriz(x: &[Vec<f64>], tipos: &[Tipo], alvos: &[Option<f64>]) -> Vec<Vec<f64>> {
    let m = x.len();
    let n = tipos.len();
    let mut r = vec![vec![0.0; n]; m];
    for j in 0..n {
        let c = normalizar_coluna(&coluna(x, j), tipos[j], alvos[j]);
        for i in 0..m {
            r[i][j] = c[i];
        }
    }
    r
}

#[cfg(test)]
mod testes {
    use super::*;

    #[test]
    fn beneficio_custo_e_alvo() {
        let c = [1.0, 2.0, 3.0];
        assert_eq!(normalizar_coluna(&c, Tipo::Beneficio, None), vec![0.0, 0.5, 1.0]);
        assert_eq!(normalizar_coluna(&c, Tipo::Custo, None), vec![1.0, 0.5, 0.0]);
        assert_eq!(normalizar_coluna(&c, Tipo::Alvo, Some(2.0)), vec![0.5, 1.0, 0.5]);
        // alvo fora do intervalo: o denominador inclui o próprio alvo
        assert_eq!(normalizar_coluna(&c, Tipo::Alvo, Some(5.0)), vec![0.0, 0.25, 0.5]);
    }

    #[test]
    fn coluna_constante_igual_ao_alvo_da_uns() {
        assert_eq!(normalizar_coluna(&[4.0, 4.0], Tipo::Beneficio, None), vec![1.0, 1.0]);
    }
}
