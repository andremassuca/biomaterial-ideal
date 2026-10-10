//! Monte Carlo das propriedades e dos pesos, como `src/biomat_mcdm/robustness.py`
//! (monte_carlo, sample_matrix uniforme, sample_weights, alargar_valores_unicos).
//!
//! O gerador é outro (xoshiro256** com semente expandida por SplitMix64), por isso os sorteios
//! não são os do numpy: o resultado é estatisticamente equivalente, não igual bit a bit.
//! Como no Python, a mesma semente dá os mesmos sorteios aos três métodos; aqui cada matriz
//! sorteada é avaliada pelos três métodos de uma vez.

use serde::{Deserialize, Serialize};

use crate::dados::Problema;
use crate::metodos::{pontuacao, posicoes, Metodo};
use crate::{erro, Erro};

/// Gerador pseudoaleatório xoshiro256** (rápido, reprodutível com a mesma semente).
#[derive(Debug, Clone)]
pub struct Gerador {
    s: [u64; 4],
}

impl Gerador {
    /// Cria o gerador a partir de uma semente (expandida com SplitMix64).
    pub fn new(semente: u64) -> Gerador {
        let mut z = semente;
        let mut s = [0u64; 4];
        for v in s.iter_mut() {
            z = z.wrapping_add(0x9E37_79B9_7F4A_7C15);
            let mut x = z;
            x = (x ^ (x >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
            x = (x ^ (x >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
            *v = x ^ (x >> 31);
        }
        Gerador { s }
    }

    /// Próximo inteiro de 64 bits.
    pub fn proximo(&mut self) -> u64 {
        let r = self.s[1].wrapping_mul(5).rotate_left(7).wrapping_mul(9);
        let t = self.s[1] << 17;
        self.s[2] ^= self.s[0];
        self.s[3] ^= self.s[1];
        self.s[1] ^= self.s[2];
        self.s[0] ^= self.s[3];
        self.s[2] ^= t;
        self.s[3] = self.s[3].rotate_left(45);
        r
    }

    /// Número real uniforme em [0, 1).
    pub fn uniforme01(&mut self) -> f64 {
        (self.proximo() >> 11) as f64 * (1.0 / (1u64 << 53) as f64)
    }

    /// Número real uniforme em [lo, hi) (igual a lo quando lo = hi).
    pub fn uniforme(&mut self, lo: f64, hi: f64) -> f64 {
        lo + (hi - lo) * self.uniforme01()
    }
}

/// O que varia no Monte Carlo.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Variar {
    /// Cada propriedade sorteada (uniforme) entre o mínimo e o máximo da base.
    Propriedades,
    /// Cada peso multiplicado por um fator em [1 - spread, 1 + spread] e renormalizado.
    Pesos,
}

/// Opções do Monte Carlo (os valores por omissão são os de scripts/run_all.py).
#[derive(Debug, Clone, Copy, PartialEq, Serialize, Deserialize)]
pub struct OpcoesMonteCarlo {
    pub n_iter: usize,
    pub semente: u64,
    pub variar: Variar,
    /// Perturbação dos pesos (0,2 = ±20 %).
    pub spread: f64,
    /// Propriedades quantitativas com mín. = máx. variam ±incerteza à volta do típico.
    pub incerteza_valor_unico: f64,
}

impl Default for OpcoesMonteCarlo {
    fn default() -> Self {
        OpcoesMonteCarlo { n_iter: 10_000, semente: 42, variar: Variar::Propriedades, spread: 0.2, incerteza_valor_unico: 0.0 }
    }
}

/// Posições de cada iteração para os três métodos (`posicoes[metodo][iteracao][material]`).
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct ResultadoMonteCarlo {
    pub alternativas: Vec<String>,
    pub posicoes: [Vec<Vec<u32>>; 3],
}

impl ResultadoMonteCarlo {
    /// Número de iterações feitas (pode ser menor que o pedido se a aplicação mandou parar).
    pub fn n_iter(&self) -> usize {
        self.posicoes[0].len()
    }

    fn indice(metodo: Metodo) -> usize {
        Metodo::TODOS.iter().position(|&m| m == metodo).unwrap()
    }

    /// % de iterações em que cada material fica na posição k (1 = melhor); empates contam para todos.
    pub fn pct_posicao(&self, metodo: Metodo, k: u32) -> Vec<f64> {
        let p = &self.posicoes[Self::indice(metodo)];
        let n = p.len().max(1) as f64;
        (0..self.alternativas.len())
            .map(|i| 100.0 * p.iter().filter(|l| l[i] == k).count() as f64 / n)
            .collect()
    }

    /// % de iterações em 1.º lugar.
    pub fn pct_primeiro(&self, metodo: Metodo) -> Vec<f64> {
        self.pct_posicao(metodo, 1)
    }

    /// Posição média de cada material.
    pub fn posicao_media(&self, metodo: Metodo) -> Vec<f64> {
        let p = &self.posicoes[Self::indice(metodo)];
        let n = p.len().max(1) as f64;
        (0..self.alternativas.len()).map(|i| p.iter().map(|l| l[i] as f64).sum::<f64>() / n).collect()
    }
}

/// Igual a numpy.isclose com as tolerâncias por omissão.
fn quase_igual(a: f64, b: f64) -> bool {
    (a - b).abs() <= 1e-8 + 1e-5 * b.abs()
}

/// Dá um intervalo ±incerteza às células quantitativas com mín. = máx. (os ordinais ficam como estão).
pub fn alargar_valores_unicos(p: &Problema, incerteza: f64) -> Result<Problema, Erro> {
    if !(0.0..1.0).contains(&incerteza) {
        return erro("incerteza tem de estar em [0, 1)");
    }
    let mut q = p.clone();
    for i in 0..p.m() {
        for j in 0..p.n() {
            if !p.ordinal[j] && quase_igual(p.x_min[i][j], p.x_max[i][j]) {
                let lo = p.x_min[i][j] * (1.0 - incerteza);
                let hi = p.x_max[i][j] * (1.0 + incerteza);
                q.x_min[i][j] = lo.min(hi);
                q.x_max[i][j] = lo.max(hi);
            }
        }
    }
    Ok(q)
}

/// Pesos perturbados: cada um multiplicado por um fator em [1 - spread, 1 + spread] e renormalizados.
pub fn sortear_pesos(pesos: &[f64], g: &mut Gerador, spread: f64) -> Vec<f64> {
    let p: Vec<f64> = pesos.iter().map(|w| w * g.uniforme(1.0 - spread, 1.0 + spread)).collect();
    let s: f64 = p.iter().sum();
    p.iter().map(|w| w / s).collect()
}

/// Corre o Monte Carlo com os três métodos; `continuar(k)` é chamado antes de cada iteração
/// e, se devolver false, o cálculo para (botão "parar" da aplicação; barra de progresso).
pub fn monte_carlo_com_progresso(
    p: &Problema,
    op: &OpcoesMonteCarlo,
    mut continuar: impl FnMut(usize) -> bool,
) -> Result<ResultadoMonteCarlo, Erro> {
    if op.n_iter < 1 {
        return erro("n_iter tem de ser ≥ 1");
    }
    p.validar()?;
    let base = if op.variar == Variar::Propriedades && op.incerteza_valor_unico != 0.0 {
        alargar_valores_unicos(p, op.incerteza_valor_unico)?
    } else {
        p.clone()
    };
    let mut g = Gerador::new(op.semente);
    let mut out: [Vec<Vec<u32>>; 3] = [Vec::with_capacity(op.n_iter), Vec::with_capacity(op.n_iter), Vec::with_capacity(op.n_iter)];
    let mut x = base.x_tipico.clone();
    for k in 0..op.n_iter {
        if !continuar(k) {
            break;
        }
        let pesos = match op.variar {
            Variar::Propriedades => {
                for i in 0..base.m() {
                    for j in 0..base.n() {
                        x[i][j] = g.uniforme(base.x_min[i][j], base.x_max[i][j]);
                    }
                }
                base.pesos.clone()
            }
            Variar::Pesos => sortear_pesos(&base.pesos, &mut g, op.spread),
        };
        for (idx, m) in Metodo::TODOS.iter().enumerate() {
            let s = pontuacao(*m, &x, &pesos, &base.tipos, &base.alvos);
            out[idx].push(posicoes(&s, m.maior_e_melhor()));
        }
    }
    Ok(ResultadoMonteCarlo { alternativas: base.alternativas.clone(), posicoes: out })
}

/// Monte Carlo sem progresso (corre todas as iterações).
pub fn monte_carlo(p: &Problema, op: &OpcoesMonteCarlo) -> Result<ResultadoMonteCarlo, Erro> {
    monte_carlo_com_progresso(p, op, |_| true)
}

#[cfg(test)]
mod testes {
    use super::*;

    #[test]
    fn gerador_reprodutivel_e_em_0_1() {
        let mut a = Gerador::new(42);
        let mut b = Gerador::new(42);
        for _ in 0..1000 {
            let u = a.uniforme01();
            assert_eq!(u, b.uniforme01());
            assert!((0.0..1.0).contains(&u));
        }
        let media: f64 = (0..100_000).map(|_| a.uniforme01()).sum::<f64>() / 100_000.0;
        assert!((media - 0.5).abs() < 0.01);
    }

    #[test]
    fn pesos_sorteados_somam_1() {
        let mut g = Gerador::new(1);
        let w = sortear_pesos(&[0.5, 0.3, 0.2], &mut g, 0.2);
        assert!((w.iter().sum::<f64>() - 1.0).abs() < 1e-12);
    }
}
