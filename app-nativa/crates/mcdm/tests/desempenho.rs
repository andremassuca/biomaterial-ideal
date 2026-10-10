//! Teste de desempenho simples: 10 000 iterações de Monte Carlo do stent (propriedades, três
//! métodos). Mede e reporta sempre; só exige menos de 1 s quando compilado em release
//! (cargo test --release).

mod comum;

use std::time::Instant;

use comum::ler_caso;
use mcdm::monte_carlo::{monte_carlo, OpcoesMonteCarlo};

#[test]
fn monte_carlo_do_stent_10000_iteracoes() {
    let caso = ler_caso("Stent");
    for cenario in ["A", "B"] {
        let p = caso.problema(cenario).unwrap();
        let op = OpcoesMonteCarlo {
            n_iter: 10_000,
            incerteza_valor_unico: caso.parametro("incerteza_valor_unico", 0.0),
            ..Default::default()
        };
        let t0 = Instant::now();
        let r = monte_carlo(p, &op).unwrap();
        let dt = t0.elapsed();
        assert_eq!(r.n_iter(), 10_000);
        println!("Monte Carlo do stent, cenário {cenario}: 10 000 iterações x 3 métodos em {:.1} ms ({})",
                 dt.as_secs_f64() * 1000.0, if cfg!(debug_assertions) { "debug" } else { "release" });
        if !cfg!(debug_assertions) {
            assert!(dt.as_secs_f64() < 1.0, "demasiado lento: {dt:?}");
        }
    }
}
