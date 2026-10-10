//! TOPSIS, WASPAS e VIKOR com critérios-alvo e consenso de Borda, iguais a
//! `src/biomat_mcdm/methods/` e `src/biomat_mcdm/pipeline.py`.

use serde::{Deserialize, Serialize};

use crate::dados::{Problema, Tipo};
use crate::normalizacao::{coluna, maximo, minimo, normalizar_matriz, valor_referencia};

/// Os três métodos, pela ordem do Python (METODOS).
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Metodo {
    Topsis,
    Waspas,
    Vikor,
}

impl Metodo {
    pub const TODOS: [Metodo; 3] = [Metodo::Topsis, Metodo::Waspas, Metodo::Vikor];

    /// Nome como no Python ("TOPSIS", "WASPAS", "VIKOR").
    pub fn nome(self) -> &'static str {
        match self {
            Metodo::Topsis => "TOPSIS",
            Metodo::Waspas => "WASPAS",
            Metodo::Vikor => "VIKOR",
        }
    }

    /// Maior pontuação é melhor? (C e Q sim; P do VIKOR não.)
    pub fn maior_e_melhor(self) -> bool {
        !matches!(self, Metodo::Vikor)
    }
}

/// TOPSIS: devolve C_i (proximidade relativa à solução ideal); maior C = melhor.
///
/// Normaliza (eq. 2), multiplica pelos pesos, mede a distância euclidiana à melhor e à pior
/// solução de cada coluna e calcula C = D- / (D+ + D-).
pub fn topsis(x: &[Vec<f64>], pesos: &[f64], tipos: &[Tipo], alvos: &[Option<f64>]) -> Vec<f64> {
    let r = normalizar_matriz(x, tipos, alvos);
    let (m, n) = (x.len(), pesos.len());
    let v: Vec<Vec<f64>> = r.iter().map(|l| l.iter().zip(pesos).map(|(a, w)| a * w).collect()).collect();
    let mut v_pos = vec![f64::NEG_INFINITY; n];
    let mut v_neg = vec![f64::INFINITY; n];
    for l in &v {
        for j in 0..n {
            v_pos[j] = v_pos[j].max(l[j]);
            v_neg[j] = v_neg[j].min(l[j]);
        }
    }
    (0..m)
        .map(|i| {
            let mut dp = 0.0;
            let mut dn = 0.0;
            for j in 0..n {
                dp += (v[i][j] - v_pos[j]).powi(2);
                dn += (v[i][j] - v_neg[j]).powi(2);
            }
            let (dp, dn) = (dp.sqrt(), dn.sqrt());
            dn / (dp + dn)
        })
        .collect()
}

/// Normalização própria do WASPAS (eqs. 9-13); r em [0, 1], 1 = melhor.
///
/// Benefício: x / máx; custo: mín / x; alvo abaixo de todos: 1 - (x - T) / máx; alvo acima de
/// todos: 1 - (T - x) / T; alvo no meio: 1 - |x - T| / (máx - mín); alvo igual ao máximo ou
/// ao mínimo: como benefício ou custo; custo com mínimo 0: eq. 11 com T = 0, 1 - x / máx (coluna toda a
/// zero: 1).
pub fn normalizar_waspas(x: &[Vec<f64>], tipos: &[Tipo], alvos: &[Option<f64>]) -> Vec<Vec<f64>> {
    let m = x.len();
    let mut r = vec![vec![0.0; tipos.len()]; m];
    for (j, &t) in tipos.iter().enumerate() {
        let c = coluna(x, j);
        let (lo, hi) = (minimo(&c), maximo(&c));
        let tv = valor_referencia(&c, t, alvos[j]);
        for i in 0..m {
            let xi = c[i];
            r[i][j] = if t == Tipo::Beneficio || (t == Tipo::Alvo && tv == hi) {
                xi / hi
            } else if t == Tipo::Custo && lo <= 0.0 {
                if hi > 0.0 { 1.0 - xi / hi } else { 1.0 }
            } else if t == Tipo::Custo || (t == Tipo::Alvo && tv == lo) {
                lo / xi
            } else if tv < lo {
                1.0 - (xi - tv) / hi
            } else if tv > hi {
                1.0 - (tv - xi) / tv
            } else {
                1.0 - (xi - tv).abs() / (hi - lo)
            };
        }
    }
    r
}

/// WASPAS: Q_i = λ·soma pesada + (1 - λ)·produto pesado (eq. 16), com λ = 0,5; maior Q = melhor.
pub fn waspas(x: &[Vec<f64>], pesos: &[f64], tipos: &[Tipo], alvos: &[Option<f64>]) -> Vec<f64> {
    waspas_lambda(x, pesos, tipos, alvos, 0.5)
}

/// WASPAS com λ à escolha (λ em [0, 1]).
pub fn waspas_lambda(x: &[Vec<f64>], pesos: &[f64], tipos: &[Tipo], alvos: &[Option<f64>], lam: f64) -> Vec<f64> {
    let r = normalizar_waspas(x, tipos, alvos);
    r.iter()
        .map(|l| {
            let q1: f64 = l.iter().zip(pesos).map(|(a, w)| a * w).sum();
            let q2: f64 = l.iter().zip(pesos).map(|(a, w)| a.powf(*w)).product();
            lam * q1 + (1.0 - lam) * q2
        })
        .collect()
}

/// Resultado do VIKOR: S, R e P (menor é melhor nos três).
#[derive(Debug, Clone, PartialEq)]
pub struct Vikor {
    pub s: Vec<f64>,
    pub r: Vec<f64>,
    pub p: Vec<f64>,
}

/// Igual a numpy.isclose com as tolerâncias por omissão (rtol 1e-5, atol 1e-8).
fn quase_igual(a: f64, b: f64) -> bool {
    (a - b).abs() <= 1e-8 + 1e-5 * b.abs()
}

/// VIKOR abrangente com critérios-alvo (eqs. 17-19), com v = 0,5.
///
/// Para cada material mede a distância ao valor ideal em cada critério, numa escala de 0 a 1
/// exponencial; S soma essas distâncias pesadas, R guarda a pior e P mistura os dois.
pub fn vikor(x: &[Vec<f64>], pesos: &[f64], tipos: &[Tipo], alvos: &[Option<f64>]) -> Vikor {
    let (m, n) = (x.len(), pesos.len());
    let mut t = vec![0.0; n];
    let mut a = vec![0.0; n];
    for j in 0..n {
        let c = coluna(x, j);
        t[j] = valor_referencia(&c, tipos[j], alvos[j]);
        let aj = maximo(&c).max(t[j]) - minimo(&c).min(t[j]);
        a[j] = if aj == 0.0 { 1.0 } else { aj };
    }
    let mut s = vec![0.0; m];
    let mut r = vec![f64::NEG_INFINITY; m];
    for i in 0..m {
        for j in 0..n {
            let e = pesos[j] * (1.0 - (-(x[i][j] - t[j]).abs() / a[j]).exp());
            s[i] += e;
            r[i] = r[i].max(e);
        }
    }
    let (s_min, s_max, r_min, r_max) = (minimo(&s), maximo(&s), minimo(&r), maximo(&r));
    let (s_const, r_const) = (quase_igual(s_max, s_min), quase_igual(r_max, r_min));
    let v = 0.5;
    let p = (0..m)
        .map(|i| {
            if s_const && r_const {
                0.0
            } else if s_const {
                (r[i] - r_min) / (r_max - r_min)
            } else if r_const {
                (s[i] - s_min) / (s_max - s_min)
            } else {
                (s[i] - s_min) / (s_max - s_min) * v + (r[i] - r_min) / (r_max - r_min) * (1.0 - v)
            }
        })
        .collect();
    Vikor { s, r, p }
}

/// Converte pontuações em posições (1 = melhor); empates ficam com a mesma posição (a menor),
/// como scipy.stats.rankdata(method="min").
pub fn posicoes(pontuacoes: &[f64], maior_e_melhor: bool) -> Vec<u32> {
    pontuacoes
        .iter()
        .map(|&a| {
            let melhores = pontuacoes
                .iter()
                .filter(|&&b| if maior_e_melhor { b > a } else { b < a })
                .count();
            1 + melhores as u32
        })
        .collect()
}

/// Pontuação de um método: C (TOPSIS), Q (WASPAS) ou P (VIKOR).
pub fn pontuacao(metodo: Metodo, x: &[Vec<f64>], pesos: &[f64], tipos: &[Tipo], alvos: &[Option<f64>]) -> Vec<f64> {
    match metodo {
        Metodo::Topsis => topsis(x, pesos, tipos, alvos),
        Metodo::Waspas => waspas(x, pesos, tipos, alvos),
        Metodo::Vikor => vikor(x, pesos, tipos, alvos).p,
    }
}

/// Resultado dos três métodos e do consenso de Borda para um problema.
#[derive(Debug, Clone, PartialEq, Serialize, Deserialize)]
pub struct Ranking {
    pub alternativas: Vec<String>,
    pub c_topsis: Vec<f64>,
    pub q_waspas: Vec<f64>,
    pub s_vikor: Vec<f64>,
    pub r_vikor: Vec<f64>,
    pub p_vikor: Vec<f64>,
    pub pos_topsis: Vec<u32>,
    pub pos_waspas: Vec<u32>,
    pub pos_vikor: Vec<u32>,
    pub pontos_borda: Vec<u32>,
    pub pos_borda: Vec<u32>,
}

/// Consenso de Borda: cada método dá (m - posição) pontos; ordena pela soma e, em caso de
/// empate, pela posição no TOPSIS (e depois pela ordem dos materiais). Devolve (pontos, posições).
pub fn borda(pos: [&[u32]; 3], pos_topsis: &[u32]) -> (Vec<u32>, Vec<u32>) {
    let m = pos_topsis.len() as u32;
    let pontos: Vec<u32> = (0..pos_topsis.len()).map(|i| pos.iter().map(|p| m - p[i]).sum()).collect();
    let mut ordem: Vec<usize> = (0..pontos.len()).collect();
    ordem.sort_by(|&a, &b| pontos[b].cmp(&pontos[a]).then(pos_topsis[a].cmp(&pos_topsis[b])));
    let mut pos_borda = vec![0; pontos.len()];
    for (k, &i) in ordem.iter().enumerate() {
        pos_borda[i] = k as u32 + 1;
    }
    (pontos, pos_borda)
}

/// Corre os três métodos e o consenso de Borda sobre um problema (com os pesos do problema).
pub fn avaliar(p: &Problema) -> Ranking {
    avaliar_com_pesos(p, &p.pesos)
}

/// Como `avaliar`, mas com outros pesos (ex.: η < 1 ou pesos ajustados na aplicação).
pub fn avaliar_com_pesos(p: &Problema, pesos: &[f64]) -> Ranking {
    let x = &p.x_tipico;
    let c = topsis(x, pesos, &p.tipos, &p.alvos);
    let q = waspas(x, pesos, &p.tipos, &p.alvos);
    let v = vikor(x, pesos, &p.tipos, &p.alvos);
    let (pt, pw, pv) = (posicoes(&c, true), posicoes(&q, true), posicoes(&v.p, false));
    let (pontos, pb) = borda([&pt, &pw, &pv], &pt);
    Ranking {
        alternativas: p.alternativas.clone(),
        c_topsis: c,
        q_waspas: q,
        s_vikor: v.s,
        r_vikor: v.r,
        p_vikor: v.p,
        pos_topsis: pt,
        pos_waspas: pw,
        pos_vikor: pv,
        pontos_borda: pontos,
        pos_borda: pb,
    }
}

#[cfg(test)]
mod testes {
    use super::*;

    #[test]
    fn posicoes_com_empates() {
        assert_eq!(posicoes(&[0.2, 0.9, 0.9, 0.1], true), vec![3, 1, 1, 4]);
        assert_eq!(posicoes(&[0.2, 0.9, 0.0], false), vec![2, 3, 1]);
    }

    #[test]
    fn borda_desempata_pelo_topsis() {
        // a: 1, 3, 2 ; b: 2, 1, 3 ; c: 3, 2, 1 -> todos com 3 pontos; ganha o melhor no TOPSIS
        let (pts, pb) = borda([&[1, 2, 3], &[3, 1, 2], &[2, 3, 1]], &[1, 2, 3]);
        assert_eq!(pts, vec![3, 3, 3]);
        assert_eq!(pb, vec![1, 2, 3]);
    }

    #[test]
    fn vikor_e_waspas_casos_simples() {
        let x = vec![vec![1.0, 5.0], vec![2.0, 10.0]];
        let t = [Tipo::Beneficio, Tipo::Custo];
        let a = [None, None];
        let w = [0.5, 0.5];
        let v = vikor(&x, &w, &t, &a);
        assert!((v.s[0] - v.s[1]).abs() < 1e-12); // simétrico: S igual
        assert_eq!(v.p, vec![0.0, 0.0]);
        let q = waspas(&x, &w, &t, &a);
        assert!((q[0] - q[1]).abs() < 1e-12);
        let c = topsis(&x, &w, &t, &a);
        assert!((c[0] - 0.5).abs() < 1e-12);
    }

    #[test]
    fn waspas_custo_com_minimo_zero() {
        // teor de níquel 0, 9 e 35 %: eq. 11 com T = 0 (1 - x / máx); coluna toda a zero dá 1
        let x = vec![vec![0.0], vec![9.0], vec![35.0]];
        let r = normalizar_waspas(&x, &[Tipo::Custo], &[None]);
        assert!((r[0][0] - 1.0).abs() < 1e-12);
        assert!((r[1][0] - (1.0 - 9.0 / 35.0)).abs() < 1e-12);
        assert!(r[2][0].abs() < 1e-12);
        let z = normalizar_waspas(&[vec![0.0], vec![0.0]], &[Tipo::Custo], &[None]);
        assert!(z.iter().all(|l| (l[0] - 1.0).abs() < 1e-12));
    }
}
