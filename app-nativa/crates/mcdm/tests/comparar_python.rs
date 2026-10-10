//! Compara o núcleo Rust com o Python (ficheiros de tests/referencias/, gerados por
//! scripts/referencias_rust.py): pontuações até 1e-6, posições, Borda, pesos objetivos, η e
//! Monte Carlo (estatisticamente equivalente: outro gerador aleatório).

mod comum;

use comum::{crate_dir, ler_caso, perto};
use mcdm::metodos::{avaliar, avaliar_com_pesos, Metodo};
use mcdm::monte_carlo::{monte_carlo, OpcoesMonteCarlo, Variar};
use mcdm::pesos::{combinar_pesos, pesos_desvio_padrao};
use serde_json::Value;

const TOL: f64 = 1e-6;
/// Diferença máxima aceite na % de 1.º lugar (pontos percentuais) com 10 000 iterações de cada
/// lado: o desvio-padrão da diferença é no máximo cerca de 0,7 pontos; 3 pontos são mais de 4 desvios.
const TOL_PCT: f64 = 3.0;
const TOL_POS_MEDIA: f64 = 0.05;

fn lista(v: &Value) -> Vec<f64> {
    v.as_array().expect("lista").iter().map(|x| x.as_f64().expect("número")).collect()
}

fn lista_u32(v: &Value) -> Vec<u32> {
    v.as_array().expect("lista").iter().map(|x| x.as_u64().expect("inteiro") as u32).collect()
}

fn referencia(caso: &str, cenario: &str) -> Value {
    let f = crate_dir().join("tests").join("referencias").join(format!("referencia_{caso}_{cenario}.json"));
    let texto = std::fs::read_to_string(&f)
        .unwrap_or_else(|e| panic!("{}: {e}; corra python scripts/referencias_rust.py", f.display()));
    serde_json::from_str(&texto).expect("JSON de referência inválido")
}

fn comparar(caso: &str, nome_caso: &str, cenario: &str) {
    let r = referencia(caso, cenario);
    let dados = ler_caso(nome_caso);
    let p = dados.problema(cenario).unwrap();
    let rot = |s: &str| format!("{caso} {cenario} {s}");
    let alts: Vec<String> = r["alternativas"].as_array().unwrap().iter().map(|a| a.as_str().unwrap().to_string()).collect();
    assert_eq!(p.alternativas, alts, "{}", rot("alternativas"));

    let k = avaliar(p);
    perto(&rot("C_TOPSIS"), &k.c_topsis, &lista(&r["C_TOPSIS"]), TOL);
    perto(&rot("Q_WASPAS"), &k.q_waspas, &lista(&r["Q_WASPAS"]), TOL);
    perto(&rot("S_VIKOR"), &k.s_vikor, &lista(&r["S_VIKOR"]), TOL);
    perto(&rot("R_VIKOR"), &k.r_vikor, &lista(&r["R_VIKOR"]), TOL);
    perto(&rot("P_VIKOR"), &k.p_vikor, &lista(&r["P_VIKOR"]), TOL);
    assert_eq!(k.pos_topsis, lista_u32(&r["pos_TOPSIS"]), "{}", rot("pos_TOPSIS"));
    assert_eq!(k.pos_waspas, lista_u32(&r["pos_WASPAS"]), "{}", rot("pos_WASPAS"));
    assert_eq!(k.pos_vikor, lista_u32(&r["pos_VIKOR"]), "{}", rot("pos_VIKOR"));
    assert_eq!(k.pontos_borda, lista_u32(&r["pontos_Borda"]), "{}", rot("pontos_Borda"));
    assert_eq!(k.pos_borda, lista_u32(&r["pos_Borda"]), "{}", rot("pos_Borda"));

    if !r["pesos_objetivos"].is_null() {
        let wo = pesos_desvio_padrao(&p.x_tipico, &p.tipos).unwrap();
        perto(&rot("pesos objetivos"), &wo, &lista(&r["pesos_objetivos"]), TOL);
        let e = &r["eta"];
        let w = combinar_pesos(&p.pesos, &wo, e["eta"].as_f64().unwrap()).unwrap();
        perto(&rot("pesos η"), &w, &lista(&e["pesos"]), TOL);
        let ke = avaliar_com_pesos(p, &w);
        perto(&rot("C η"), &ke.c_topsis, &lista(&e["C_TOPSIS"]), TOL);
        perto(&rot("Q η"), &ke.q_waspas, &lista(&e["Q_WASPAS"]), TOL);
        perto(&rot("P η"), &ke.p_vikor, &lista(&e["P_VIKOR"]), TOL);
    }

    let mc = &r["monte_carlo"];
    for (variar, nome) in [(Variar::Propriedades, "propriedades"), (Variar::Pesos, "pesos")] {
        let op = OpcoesMonteCarlo {
            n_iter: mc["n_iter"].as_u64().unwrap() as usize,
            semente: 7,
            variar,
            spread: mc["spread"].as_f64().unwrap(),
            incerteza_valor_unico: mc["incerteza_valor_unico"].as_f64().unwrap(),
        };
        let res = monte_carlo(p, &op).unwrap();
        for m in Metodo::TODOS {
            let chave = format!("{nome}_{}", m.nome());
            perto(&rot(&format!("MC {chave} % 1.º")), &res.pct_primeiro(m), &lista(&mc[&chave]["pct_primeiro"]), TOL_PCT);
            perto(&rot(&format!("MC {chave} posição média")), &res.posicao_media(m),
                  &lista(&mc[&chave]["posicao_media"]), TOL_POS_MEDIA);
        }
    }
}

#[test]
fn haste_a() {
    comparar("haste", "Haste", "A");
}

#[test]
fn haste_b() {
    comparar("haste", "Haste", "B");
}

#[test]
fn stent_a() {
    comparar("stent", "Stent", "A");
}

#[test]
fn stent_b() {
    comparar("stent", "Stent", "B");
}

#[test]
fn scaffold_a() {
    comparar("scaffold", "Scaffold", "A");
}

#[test]
fn scaffold_b() {
    comparar("scaffold", "Scaffold", "B");
}

#[test]
fn monte_carlo_para_quando_se_pede() {
    let dados = ler_caso("Stent");
    let p = dados.problema("A").unwrap();
    let op = OpcoesMonteCarlo { n_iter: 100, ..Default::default() };
    let res = mcdm::monte_carlo::monte_carlo_com_progresso(p, &op, |k| k < 10).unwrap();
    assert_eq!(res.n_iter(), 10);
    let mesma = monte_carlo(p, &op).unwrap();
    assert_eq!(mesma, monte_carlo(p, &op).unwrap(), "a mesma semente dá o mesmo resultado");
}
