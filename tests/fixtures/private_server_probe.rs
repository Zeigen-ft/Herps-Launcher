//! Development-only fixture: verify the private config with the real engine preflight.
#[allow(dead_code)]
#[path = "../../packaging/private_server.rs"]
mod private_server;

fn main() {
    let directory = std::env::args_os().nth(1).expect("server folder");
    let (ip, port) = private_server::parse_address("100.64.1.2:25565").unwrap();
    let report = private_server::configure(std::path::Path::new(&directory), ip, port).unwrap();
    assert!(!report.eula_agreed, "the fixture must never accept an EULA");
    assert!(report.backup.is_none(), "a fresh or already-correct fixture must not be rewritten");
    println!("{}", report.config_path.display());
}
