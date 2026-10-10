// Sem janela de consola nas versões de distribuição no Windows.
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

fn main() {
    biomaterial_ideal_lib::run()
}
