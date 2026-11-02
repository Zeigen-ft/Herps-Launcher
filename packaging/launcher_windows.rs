//! Native, dependency-free Windows entrypoint for the packaged desktop client.
//! Compile with rustc --edition=2021 --target x86_64-pc-windows-msvc.

use std::env;
use std::ffi::{OsStr, OsString};
use std::fs::{self, File};
use std::io::{self, Write};
#[cfg(windows)]
use std::io::IsTerminal;
use std::path::{Path, PathBuf};
use std::process::{self, Command, ExitStatus, Stdio};
use std::time::{SystemTime, UNIX_EPOCH};

mod private_server;

const VERSION: &str = "0.2.2";
const HELP: &str = "Herspers Minecraft for Windows\n\
Usage: Herspers-Minecraft.exe [-- <game arguments>]\n\
       Herspers-Minecraft.exe --setup [server.jar] [minecraft-folder]\n\
       Herspers-Minecraft.exe --host-tailscale [--server-dir PATH] [--port PORT] [--accept-eula]\n\
       Herspers-Minecraft.exe --join-tailscale [100.x.y.z:PORT] [--name PLAYER]\n\
First launch: install JDK 25, launch your own Minecraft Java Edition 26.3 once,\n\
then run --setup and select or paste the matching official 26.3 server JAR path.\n\
The default Minecraft folder is %APPDATA%\\.minecraft.\n\
Game data and preparation caches are kept in %LOCALAPPDATA%\\Herspers Minecraft.\n\
No Rust, Python, administrator access, or running Minecraft server is required.\n\
Host-Tailscale.cmd starts your own private server on your Tailscale IPv4 address.\n\
Join-Tailscale.cmd asks for the host's address and your player name. Both PCs need Tailscale access.\n\
Options: --help, --version, --setup, --host-tailscale, --join-tailscale\n";

#[derive(Debug, PartialEq, Eq)]
enum Action {
    Help,
    Version,
    Setup { server: Option<PathBuf>, minecraft: Option<PathBuf> },
    HostPrivate { directory: Option<PathBuf>, port: u16, accept_eula: bool },
    JoinPrivate { address: Option<String>, name: Option<String> },
    Play(Vec<OsString>),
}

#[derive(Debug)]
struct Failure {
    message: String,
    code: i32,
}

impl Failure {
    fn new(message: impl Into<String>) -> Self {
        Self { message: message.into(), code: 1 }
    }
}

impl From<io::Error> for Failure {
    fn from(error: io::Error) -> Self { Self::new(error.to_string()) }
}

type Result<T> = std::result::Result<T, Failure>;

fn parse_args(mut args: Vec<OsString>) -> Result<Action> {
    match args.first().map(OsString::as_os_str) {
        Some(first) if first == "--help" || first == "-h" => Ok(Action::Help),
        Some(first) if first == "--version" => Ok(Action::Version),
        Some(first) if first == "--setup" => {
            if args.len() > 3 {
                return Err(Failure { message: "Usage: Herspers-Minecraft.exe --setup [server.jar] [minecraft-folder]".into(), code: 2 });
            }
            Ok(Action::Setup {
                server: args.get(1).map(PathBuf::from),
                minecraft: args.get(2).map(PathBuf::from),
            })
        }
        Some(first) if first == "--host-tailscale" => {
            let (mut directory, mut port, mut accept_eula) = (None, 25565, false);
            let mut remaining = args.into_iter().skip(1);
            while let Some(option) = remaining.next() {
                if option == "--server-dir" {
                    directory = Some(PathBuf::from(remaining.next().ok_or_else(|| usage("--server-dir needs a folder"))?));
                } else if option == "--port" {
                    port = remaining.next().and_then(|v| v.to_str().and_then(|s| s.parse::<u16>().ok()))
                        .filter(|p| *p != 0).ok_or_else(|| usage("--port needs a number from 1 to 65535"))?;
                } else if option == "--accept-eula" {
                    accept_eula = true;
                } else {
                    return Err(usage("Unknown private hosting option; use --help"));
                }
            }
            Ok(Action::HostPrivate { directory, port, accept_eula })
        }
        Some(first) if first == "--join-tailscale" => {
            let (mut address, mut name) = (None, None);
            let mut remaining = args.into_iter().skip(1);
            while let Some(option) = remaining.next() {
                if option == "--name" {
                    let value = remaining.next().and_then(|v| v.into_string().ok())
                        .ok_or_else(|| usage("--name needs a player name"))?;
                    validate_player_name(&value)?;
                    name = Some(value);
                } else if address.is_none() && !option.to_string_lossy().starts_with('-') {
                    let value = option.into_string().map_err(|_| usage("Enter a Tailscale IPv4 address"))?;
                    private_server::parse_address(&value).map_err(usage)?;
                    address = Some(value);
                } else {
                    return Err(usage("Usage: --join-tailscale [100.x.y.z:PORT] [--name PLAYER]"));
                }
            }
            Ok(Action::JoinPrivate { address, name })
        }
        _ => {
            if args.first().is_some_and(|a| a == "--") { args.remove(0); }
            Ok(Action::Play(args))
        }
    }
}

fn usage(message: impl Into<String>) -> Failure {
    Failure { message: message.into(), code: 2 }
}

fn validate_player_name(name: &str) -> Result<()> {
    if !(3..=16).contains(&name.len()) || !name.bytes().all(|c| c.is_ascii_alphanumeric() || c == b'_') {
        return Err(usage("Use a player name of 3-16 letters, numbers or underscores. Each friend needs a different name."));
    }
    Ok(())
}

fn required_env_path(name: &str) -> Result<PathBuf> {
    match env::var_os(name).filter(|value| !value.is_empty()) {
        Some(value) => Ok(PathBuf::from(value)),
        None => Err(Failure::new(format!("Windows did not provide {name}; cannot choose a safe data folder."))),
    }
}

fn normal_file(path: &Path) -> Result<()> {
    let info = fs::symlink_metadata(path)
        .map_err(|error| Failure::new(format!("Cannot access required file {}: {error}", path.display())))?;
    if !info.file_type().is_file() {
        return Err(Failure::new(format!("Expected an ordinary file: {}", path.display())));
    }
    Ok(())
}

fn normal_directory(path: &Path) -> Result<()> {
    let info = fs::symlink_metadata(path)?;
    if !info.file_type().is_dir() {
        return Err(Failure::new(format!("Expected an ordinary directory: {}", path.display())));
    }
    Ok(())
}

fn copy_inputs(source: &Path, destination: &Path) -> Result<()> {
    normal_directory(source)?;
    for item in fs::read_dir(source)? {
        let item = item?;
        let kind = item.file_type()?;
        let target = destination.join(item.file_name());
        if kind.is_dir() {
            fs::create_dir(&target)?;
            copy_inputs(&item.path(), &target)?;
        } else if kind.is_file() {
            // The entire target tree is newly created by this process.
            fs::copy(item.path(), target)?;
        } else {
            return Err(Failure::new(format!("Preparation inputs contain a link or special file: {}", item.path().display())));
        }
    }
    Ok(())
}

fn preparation_id(bundle: &Path) -> Result<String> {
    let file = bundle.join("preparation-id.txt");
    normal_file(&file)?;
    let id = fs::read_to_string(file)?.trim().to_owned();
    if id.len() != 64 || !id.bytes().all(|b| b.is_ascii_digit() || (b'a'..=b'f').contains(&b)) {
        return Err(Failure::new("The bundled preparation identity is invalid. Download and extract the complete Windows package again."));
    }
    Ok(id)
}

fn writable_preparation(bundle: &Path, support: &Path) -> Result<PathBuf> {
    let source = bundle.join("preparation");
    normal_directory(&source)?;
    normal_file(&source.join("research-lock.json"))?;
    let parent = support.join("preparation");
    fs::create_dir_all(&parent)?;
    normal_directory(&parent)?;
    let target = parent.join(preparation_id(bundle)?);
    if target.exists() {
        normal_directory(&target)?;
        normal_file(&target.join("research-lock.json"))?;
        return Ok(target);
    }
    let stamp = SystemTime::now().duration_since(UNIX_EPOCH)
        .map_err(|error| Failure::new(error.to_string()))?.as_nanos();
    let stage = parent.join(format!(".inputs-{}-{stamp}", process::id()));
    fs::create_dir(&stage)?;
    let copied = copy_inputs(&source, &stage);
    if let Err(error) = copied {
        let _ = fs::remove_dir_all(&stage);
        return Err(error);
    }
    if let Err(error) = fs::rename(&stage, &target) {
        let _ = fs::remove_dir_all(&stage);
        // Another setup process may have completed the identical input cache.
        if !target.exists() { return Err(error.into()); }
        normal_directory(&target)?;
        normal_file(&target.join("research-lock.json"))?;
    }
    Ok(target)
}

fn read_pasted_path(line: &str) -> Result<PathBuf> {
    let text = line.trim();
    let text = if (text.starts_with('"') && text.ends_with('"'))
        || (text.starts_with('\'') && text.ends_with('\'')) {
        text.get(1..text.len().saturating_sub(1)).unwrap_or("")
    } else { text };
    if text.is_empty() || text.contains('\0') {
        return Err(Failure::new("No server JAR path was entered. Run --setup again and provide the matching official 26.3 server JAR."));
    }
    Ok(PathBuf::from(text))
}

fn prompt_server() -> Result<PathBuf> {
    println!("Setup needs JDK 25, your installed Minecraft Java Edition 26.3, and its matching official server JAR.");
    print!("Paste the full path to the server JAR, then press Enter: ");
    io::stdout().flush()?;
    let mut line = String::new();
    io::stdin().read_line(&mut line)?;
    read_pasted_path(&line)
}

fn child_code(status: ExitStatus) -> i32 { status.code().unwrap_or(1) }

fn helper(bundle: &Path, name: &str) -> Result<PathBuf> {
    let binary = bundle.join("bin").join(name);
    normal_file(&binary)?;
    Ok(binary)
}

fn prepare_command(bundle: &Path, support: &Path) -> Result<Command> {
    let mut command = Command::new(helper(bundle, "horizon-prepare.exe")?);
    command.env("HORIZON_HOME", support)
        .env("HORIZON_LAUNCHER_NO_SELF_UPDATE", "1");
    Ok(command)
}

fn check_resources(bundle: &Path, support: &Path, root: &Path) -> Result<ExitStatus> {
    let log = support.join("logs").join("resources-check.log");
    fs::create_dir_all(log.parent().unwrap())?;
    let output = File::create(log)?;
    prepare_command(bundle, support)?
        .args([OsStr::new("--check"), OsStr::new("--root")])
        .arg(root).arg("--output").arg(support.join("resources").join("26.3"))
        .stdout(Stdio::from(output.try_clone()?))
        .stderr(Stdio::from(output))
        .status().map_err(Failure::from)
}

fn setup(bundle: &Path, support: &Path, server: PathBuf, minecraft: PathBuf) -> Result<i32> {
    normal_file(&server)?;
    normal_directory(&minecraft)?;
    let root = writable_preparation(bundle, support)?;
    let resources = support.join("resources").join("26.3");
    fs::create_dir_all(resources.parent().unwrap())?;
    println!("Preparing game resources. This can take several minutes; keep this window open.");
    let status = prepare_command(bundle, support)?
        .arg("--root").arg(&root).arg("--output").arg(&resources)
        .args(["--prepare", "--complete", "--server-jar"]).arg(server)
        .arg("--minecraft-dir").arg(minecraft)
        .status()?;
    if !status.success() {
        return Err(Failure { message: "Resource preparation failed. Read the preparer's error above; verify JDK 25 and the matching official Java Edition 26.3 files.".into(), code: child_code(status) });
    }
    let checked = check_resources(bundle, support, &root)?;
    if !checked.success() {
        return Err(Failure { message: format!("Prepared resources are incomplete. See {}", support.join("logs/resources-check.log").display()), code: child_code(checked) });
    }
    println!("Resources are ready. You can now open Herspers-Minecraft.exe.");
    Ok(0)
}

fn require_resources(bundle: &Path, support: &Path) -> Result<()> {
    let check = check_resources(bundle, support, &bundle.join("preparation"))?;
    if !check.success() {
        return Err(Failure {
            message: format!("Game resources need preparation.\nRun Herspers-Minecraft.exe --setup first.\nSetup needs JDK 25, your installed Minecraft Java Edition 26.3 and its matching server JAR.\nSee INSTALL-WINDOWS.txt and {}", support.join("logs/resources-check.log").display()),
            code: child_code(check),
        });
    }
    Ok(())
}

fn play(bundle: &Path, support: &Path, arguments: &[OsString]) -> Result<i32> {
    require_resources(bundle, support)?;
    let game = support.join("game");
    fs::create_dir_all(&game)?;
    let log = support.join("logs/launcher.log");
    let output = File::create(&log)?;
    println!("Starting Herspers Minecraft. Startup log: {}", log.display());
    let status = Command::new(helper(bundle, "horizon-client.exe")?)
        .arg("--resources").arg(support.join("resources/26.3"))
        .arg("--game-dir").arg(&game)
        .args(arguments).current_dir(&game)
        .env("HORIZON_HOME", support)
        .env("HORIZON_LAUNCHER_NO_SELF_UPDATE", "1")
        .stdout(Stdio::from(output.try_clone()?)).stderr(Stdio::from(output))
        .status()?;
    if !status.success() {
        return Err(Failure { message: format!("The game exited with an error. See {}", log.display()), code: child_code(status) });
    }
    Ok(child_code(status))
}

fn prompt_line(label: &str) -> Result<String> {
    print!("{label}");
    io::stdout().flush()?;
    let mut line = String::new();
    io::stdin().read_line(&mut line)?;
    let text = line.trim().to_owned();
    if text.is_empty() { return Err(usage("No response was entered.")); }
    Ok(text)
}

fn private_server_command(bundle: &Path, support: &Path, directory: &Path) -> Result<Command> {
    let mut command = Command::new(helper(bundle, "horizon-client.exe")?);
    command.arg("--resources").arg(support.join("resources/26.3"))
        .arg("--game-dir").arg(directory)
        .arg("--home").arg(directory)
        // Dedicated-server arguments must come last: the engine forwards all
        // arguments after --dedicated directly to its server preflight.
        .args(["--dedicated", "--nogui"]).current_dir(directory)
        .env("HORIZON_HOME", directory)
        .env("HORIZON_NO_AUDIO", "1")
        .env("HORIZON_LAUNCHER_NO_SELF_UPDATE", "1");
    Ok(command)
}

fn available_server_port(ip: std::net::Ipv4Addr, port: u16) -> Result<()> {
    std::net::TcpListener::bind((ip, port)).map(drop).map_err(|error| Failure::new(format!(
        "Cannot listen on {ip}:{port}: {error}.\nConnect Tailscale and stop any old server on this port first (type stop in its console), then retry."
    )))
}

fn host_private(bundle: &Path, support: &Path, directory: Option<PathBuf>, port: u16, accept_eula: bool) -> Result<i32> {
    require_resources(bundle, support)?;
    let ip = private_server::tailscale_ipv4().map_err(Failure::new)?;
    available_server_port(ip, port)?;
    let directory = directory.unwrap_or_else(|| private_server::server_directory(support));
    let directory = if directory.is_absolute() { directory } else { env::current_dir()?.join(directory) };
    let report = private_server::configure(&directory, ip, port).map_err(Failure::new)?;
    println!("Private server folder: {}", directory.display());
    println!("Configuration: {}", report.config_path.display());
    if let Some(path) = report.backup { println!("Original configuration backed up: {}", path.display()); }
    if !report.eula_agreed {
        println!("Read the Minecraft EULA: https://aka.ms/MinecraftEULA");
        if !accept_eula {
            let agreed = prompt_line("If you agree, type I AGREE and press Enter: ")?;
            if !agreed.eq_ignore_ascii_case("I AGREE") {
                return Err(Failure::new("Server not started. The EULA was not accepted."));
            }
        }
        private_server::agree_eula(&directory).map_err(Failure::new)?;
    }
    println!("\nHOST AND FRIEND JOIN THIS ADDRESS: {ip}:{port}");
    println!("This server listens only on Tailscale and uses private player names, without Microsoft account authentication.");
    println!("Your friend must have access to this PC in Tailscale. Use Join-Tailscale.cmd on both PCs.");
    println!("Keep this window open. Type stop here to save and shut down the server.\n");
    let status = private_server_command(bundle, support, &directory)?.status()?;
    if !status.success() {
        return Err(Failure { message: format!("Private server exited with an error. Check the output above and {}", directory.join("logs/latest.log").display()), code: child_code(status) });
    }
    Ok(child_code(status))
}

fn join_private(bundle: &Path, support: &Path, address: Option<String>, name: Option<String>) -> Result<i32> {
    let address = match address {
        Some(value) => value,
        None => prompt_line("Host's Tailscale IPv4 address (100.x.y.z:25565): ")?,
    };
    let (ip, port) = private_server::parse_address(&address).map_err(usage)?;
    private_server::tailscale_ipv4().map_err(Failure::new)?;
    let name = match name {
        Some(value) => value,
        None => prompt_line("Your player name (3-16 letters, numbers or underscores): ")?,
    };
    validate_player_name(&name)?;
    let arguments = vec!["--server".into(), format!("{ip}:{port}").into(), "--name".into(), name.into()];
    play(bundle, support, &arguments)
}

fn run() -> Result<i32> {
    let action = parse_args(env::args_os().skip(1).collect())?;
    match action {
        Action::Help => { print!("{HELP}"); return Ok(0); }
        Action::Version => { println!("Herspers Minecraft {VERSION}"); return Ok(0); }
        _ => {}
    }
    if !cfg!(target_os = "windows") {
        return Err(Failure::new("This launcher requires 64-bit Windows 10 or 11."));
    }
    let executable = env::current_exe()?;
    let bundle = executable.parent().ok_or_else(|| Failure::new("Cannot locate the application folder."))?;
    let support = required_env_path("LOCALAPPDATA")?.join("Herspers Minecraft");
    fs::create_dir_all(&support)?;
    match action {
        Action::Setup { server, minecraft } => {
            let server = match server { Some(path) => path, None => prompt_server()? };
            let minecraft = match minecraft {
                Some(path) => path,
                None => match env::var_os("HORIZON_MINECRAFT_DIR") {
                    Some(path) if !path.is_empty() => PathBuf::from(path),
                    _ => required_env_path("APPDATA")?.join(".minecraft"),
                },
            };
            setup(bundle, &support, server, minecraft)
        }
        Action::Play(arguments) => play(bundle, &support, &arguments),
        Action::HostPrivate { directory, port, accept_eula } => host_private(bundle, &support, directory, port, accept_eula),
        Action::JoinPrivate { address, name } => join_private(bundle, &support, address, name),
        _ => unreachable!(),
    }
}

fn launched_in_own_console() -> bool {
    #[cfg(windows)]
    {
        #[link(name = "kernel32")]
        extern "system" { fn GetConsoleProcessList(processes: *mut u32, count: u32) -> u32; }
        let mut processes = [0u32; 2];
        // A console created by double-clicking the exe contains only this process.
        // Existing terminals and redirected CI input must never be paused.
        io::stdin().is_terminal() && unsafe { GetConsoleProcessList(processes.as_mut_ptr(), 2) } == 1
    }
    #[cfg(not(windows))]
    { false }
}

fn main() {
    let own_console = launched_in_own_console();
    let code = match run() {
        Ok(code) => code,
        Err(error) => {
            eprintln!("Herspers Minecraft: {}", error.message);
            error.code
        }
    };
    if own_console {
        println!("Press Enter to close this window.");
        let _ = io::stdin().read_line(&mut String::new());
    }
    process::exit(code);
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicUsize, Ordering};
    static NEXT: AtomicUsize = AtomicUsize::new(0);

    struct Scratch(PathBuf);
    impl Scratch {
        fn new() -> Self {
            let path = env::temp_dir().join(format!("herspers-launcher-test-{}-{}-{}", process::id(),
                SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos(), NEXT.fetch_add(1, Ordering::Relaxed)));
            fs::create_dir(&path).unwrap(); Self(path)
        }
        fn bundle(&self) -> PathBuf {
            let bundle = self.0.join("bundle with spaces");
            fs::create_dir_all(bundle.join("preparation/nested")).unwrap();
            fs::write(bundle.join("preparation/research-lock.json"), b"pins").unwrap();
            fs::write(bundle.join("preparation/nested/source.rs"), b"source").unwrap();
            fs::write(bundle.join("preparation-id.txt"), format!("{}\n", "a".repeat(64))).unwrap();
            bundle
        }
    }
    impl Drop for Scratch { fn drop(&mut self) { let _ = fs::remove_dir_all(&self.0); } }

    #[test]
    fn setup_arguments_preserve_spaces_and_unicode() {
        let action = parse_args(vec!["--setup".into(), "C:\\My Downloads\\serveur é.jar".into(), "C:\\My Game".into()]).unwrap();
        assert_eq!(action, Action::Setup { server: Some(PathBuf::from("C:\\My Downloads\\serveur é.jar")), minecraft: Some(PathBuf::from("C:\\My Game")) });
        assert_eq!(parse_args(vec!["--setup".into()]).unwrap(), Action::Setup { server: None, minecraft: None });
        assert_eq!(parse_args(vec!["--setup".into(), "a".into(), "b".into(), "c".into()]).unwrap_err().code, 2);
    }

    #[test]
    fn game_arguments_are_forwarded_without_reparsing() {
        assert_eq!(parse_args(vec!["--".into(), "--world".into(), "My World".into()]).unwrap(), Action::Play(vec!["--world".into(), "My World".into()]));
        assert_eq!(parse_args(vec!["--help".into()]).unwrap(), Action::Help);
        assert_eq!(parse_args(vec!["--version".into()]).unwrap(), Action::Version);
    }

    #[test]
    fn private_host_options_keep_paths_literal_and_require_valid_ports() {
        assert_eq!(parse_args(vec!["--host-tailscale".into()]).unwrap(), Action::HostPrivate {
            directory: None, port: 25565, accept_eula: false,
        });
        let folder = PathBuf::from("C:\\My Server $(literal)\\世界");
        assert_eq!(parse_args(vec!["--host-tailscale".into(), "--server-dir".into(), folder.clone().into_os_string(),
            "--port".into(), "25566".into(), "--accept-eula".into()]).unwrap(), Action::HostPrivate {
                directory: Some(folder), port: 25566, accept_eula: true,
        });
        for options in [vec!["--port", "0"], vec!["--port", "65536"], vec!["--port", "not-a-number"],
            vec!["--server-dir"], vec!["--unknown"]] {
            let mut args: Vec<OsString> = vec!["--host-tailscale".into()];
            args.extend(options.into_iter().map(OsString::from));
            assert_eq!(parse_args(args).unwrap_err().code, 2);
        }
    }

    #[test]
    fn private_join_needs_a_tailnet_address_and_unambiguous_player_name() {
        assert_eq!(parse_args(vec!["--join-tailscale".into()]).unwrap(), Action::JoinPrivate { address: None, name: None });
        assert_eq!(parse_args(vec!["--join-tailscale".into(), "100.80.12.34:25566".into(), "--name".into(), "Player_1".into()]).unwrap(),
            Action::JoinPrivate { address: Some("100.80.12.34:25566".into()), name: Some("Player_1".into()) });
        for address in ["8.8.8.8", "localhost", "0.0.0.0", "100.80.12.34:0"] {
            assert_eq!(parse_args(vec!["--join-tailscale".into(), address.into()]).unwrap_err().code, 2);
        }
        for name in ["", "aa", "a name", "player;command", "a_name_more_than_16"] { assert!(validate_player_name(name).is_err()); }
    }

    #[test]
    fn private_server_keeps_game_flags_before_dedicated_and_worlds_separate() {
        let scratch = Scratch::new();
        let bundle = scratch.bundle();
        fs::create_dir(bundle.join("bin")).unwrap();
        fs::write(bundle.join("bin/horizon-client.exe"), b"fixture, never executed").unwrap();
        let support = scratch.0.join("support");
        let server = scratch.0.join("server $(literal)");
        fs::create_dir(&server).unwrap();
        let command = private_server_command(&bundle, &support, &server).unwrap();
        let args: Vec<_> = command.get_args().collect();
        let split = args.iter().position(|a| *a == OsStr::new("--dedicated")).unwrap();
        assert!(args[..split].windows(2).any(|p| p == [OsStr::new("--game-dir"), server.as_os_str()]));
        assert!(args[..split].windows(2).any(|p| p == [OsStr::new("--home"), server.as_os_str()]));
        assert!(args[..split].windows(2).any(|p| p == [OsStr::new("--resources"), support.join("resources/26.3").as_os_str()]));
        assert_eq!(&args[split..], [OsStr::new("--dedicated"), OsStr::new("--nogui")]);
        assert_eq!(command.get_current_dir(), Some(server.as_path()));
        assert!(command.get_envs().any(|(key,value)| key == "HORIZON_NO_AUDIO" && value == Some(OsStr::new("1"))));
        assert!(!support.join("game").exists());
    }

    #[test]
    fn occupied_port_is_reported_without_interfering_with_the_other_server() {
        let listener = std::net::TcpListener::bind((std::net::Ipv4Addr::LOCALHOST, 0)).unwrap();
        let port = listener.local_addr().unwrap().port();
        let failure = available_server_port(std::net::Ipv4Addr::LOCALHOST, port).unwrap_err();
        assert!(failure.message.contains("stop any old server"));
        assert_eq!(listener.local_addr().unwrap().port(), port);
        drop(listener);
        // Parallel fork/exec fixtures may briefly inherit the just-released
        // socket on Unix; use a fresh free port for the success path.
        assert!(available_server_port(std::net::Ipv4Addr::LOCALHOST, 0).is_ok());
    }

    #[test]
    fn quoted_pasted_paths_are_literal_and_empty_paths_fail() {
        assert_eq!(read_pasted_path("  \"C:\\My Files\\server.jar\"\r\n").unwrap(), PathBuf::from("C:\\My Files\\server.jar"));
        assert_eq!(read_pasted_path("'/tmp/with spaces.jar'").unwrap(), PathBuf::from("/tmp/with spaces.jar"));
        assert!(read_pasted_path("\"\"").is_err());
        assert!(read_pasted_path("").is_err());
        assert!(read_pasted_path("a\0b").is_err());
    }

    #[test]
    fn preparation_identity_rejects_paths_and_non_hash_text() {
        let scratch = Scratch::new(); let bundle = scratch.bundle();
        for invalid in ["../elsewhere".to_owned(), "a".repeat(63), "A".repeat(64), "g".repeat(64)] {
            fs::write(bundle.join("preparation-id.txt"), invalid).unwrap();
            assert!(preparation_id(&bundle).is_err());
        }
    }

    #[test]
    fn preparation_is_copied_once_and_existing_outputs_are_preserved() {
        let scratch = Scratch::new(); let bundle = scratch.bundle();
        let support = scratch.0.join("support");
        let root = writable_preparation(&bundle, &support).unwrap();
        assert_eq!(fs::read(root.join("nested/source.rs")).unwrap(), b"source");
        fs::write(root.join("generated.cache"), b"keep").unwrap();
        fs::write(bundle.join("preparation/nested/source.rs"), b"changed").unwrap();
        assert_eq!(writable_preparation(&bundle, &support).unwrap(), root);
        assert_eq!(fs::read(root.join("generated.cache")).unwrap(), b"keep");
        assert_eq!(fs::read(root.join("nested/source.rs")).unwrap(), b"source");
    }

    #[test]
    fn preparation_cannot_replace_an_existing_file() {
        let scratch = Scratch::new(); let bundle = scratch.bundle();
        let support = scratch.0.join("support");
        fs::create_dir_all(support.join("preparation")).unwrap();
        let target = support.join("preparation").join("a".repeat(64));
        fs::write(&target, b"preserve").unwrap();
        assert!(writable_preparation(&bundle, &support).is_err());
        assert_eq!(fs::read(target).unwrap(), b"preserve");
    }

    #[cfg(unix)]
    #[test]
    fn preparation_rejects_links_and_cleans_only_its_own_staging_folder() {
        use std::os::unix::fs::symlink;
        let scratch = Scratch::new(); let bundle = scratch.bundle();
        let outside = scratch.0.join("outside"); fs::write(&outside, b"private").unwrap();
        symlink(&outside, bundle.join("preparation/link")).unwrap();
        let support = scratch.0.join("support");
        assert!(writable_preparation(&bundle, &support).is_err());
        assert_eq!(fs::read(outside).unwrap(), b"private");
        assert_eq!(fs::read_dir(support.join("preparation")).unwrap().count(), 0);
    }

    #[cfg(unix)]
    #[test]
    fn helper_failure_status_is_preserved_and_game_is_not_started() {
        use std::os::unix::fs::PermissionsExt;
        let scratch = Scratch::new(); let bundle = scratch.bundle();
        fs::create_dir(bundle.join("bin")).unwrap();
        let helper = bundle.join("bin/horizon-prepare.exe");
        fs::write(&helper, "#!/bin/sh\nprintf 'missing test resources\\n'\nexit 7\n").unwrap();
        fs::set_permissions(&helper, fs::Permissions::from_mode(0o755)).unwrap();
        let support = scratch.0.join("support");
        let failure = play(&bundle, &support, &[]).unwrap_err();
        assert_eq!(failure.code, 7);
        assert!(failure.message.contains("--setup"));
        assert!(fs::read_to_string(support.join("logs/resources-check.log")).unwrap().contains("missing test resources"));
        assert!(!support.join("game").exists());
    }

    #[cfg(unix)]
    fn script(path: &Path, text: &str) {
        use std::os::unix::fs::PermissionsExt;
        fs::write(path, text).unwrap();
        fs::set_permissions(path, fs::Permissions::from_mode(0o755)).unwrap();
    }

    #[cfg(unix)]
    #[test]
    fn setup_passes_server_and_installation_paths_as_literal_arguments() {
        let scratch = Scratch::new(); let bundle = scratch.bundle();
        fs::create_dir(bundle.join("bin")).unwrap();
        script(&bundle.join("bin/horizon-prepare.exe"), "#!/bin/sh\nprintf '%s\\n' BEGIN \"$@\" >> \"$HORIZON_HOME/prepare-args.txt\"\nexit 0\n");
        let server = scratch.0.join("server $(literal).jar");
        let minecraft = scratch.0.join("my minecraft installation");
        fs::write(&server, b"fake fixture").unwrap(); fs::create_dir(&minecraft).unwrap();
        let support = scratch.0.join("support with spaces");
        assert_eq!(setup(&bundle, &support, server.clone(), minecraft.clone()).unwrap(), 0);
        let args = fs::read_to_string(support.join("prepare-args.txt")).unwrap();
        let lines: Vec<_> = args.lines().collect();
        assert!(lines.windows(2).any(|p| p == ["--server-jar", server.to_str().unwrap()]));
        assert!(lines.windows(2).any(|p| p == ["--minecraft-dir", minecraft.to_str().unwrap()]));
        assert_eq!(lines.iter().filter(|l| **l == "--check").count(), 1);
        assert_eq!(lines.iter().filter(|l| **l == "--complete").count(), 1);
    }

    #[cfg(unix)]
    #[test]
    fn game_uses_isolated_folder_literal_arguments_and_preserves_failure_code() {
        let scratch = Scratch::new(); let bundle = scratch.bundle();
        fs::create_dir(bundle.join("bin")).unwrap();
        script(&bundle.join("bin/horizon-prepare.exe"), "#!/bin/sh\nexit 0\n");
        script(&bundle.join("bin/horizon-client.exe"), "#!/bin/sh\nprintf '%s\\n' \"$PWD\" \"$@\"\nexit 9\n");
        let support = scratch.0.join("support");
        let failure = play(&bundle, &support, &["--world".into(), "world $(literal)".into()]).unwrap_err();
        assert_eq!(failure.code, 9);
        let log = fs::read_to_string(support.join("logs/launcher.log")).unwrap();
        let lines: Vec<_> = log.lines().collect();
        assert_eq!(PathBuf::from(lines[0]), fs::canonicalize(support.join("game")).unwrap());
        assert!(lines.windows(2).any(|p| p == ["--world", "world $(literal)"]));
        assert!(lines.windows(2).any(|p| p == ["--game-dir", support.join("game").to_str().unwrap()]));
    }
}
