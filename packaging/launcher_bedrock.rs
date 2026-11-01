//! Independent GPLv3 launcher. Cinnabar is a separately licensed executable,
//! not linked into this launcher. Its notices and original filenames are retained.

use serde_json::{json, Value};
use sha2::{Digest, Sha256};
use std::collections::BTreeSet;
use std::env;
use std::ffi::OsString;
use std::fs::{self, File, Metadata};
use std::io::{self, Read};
#[cfg(windows)]
use std::io::IsTerminal;
use std::path::{Path, PathBuf};
use std::process::{self, Command};

const VERSION: &str = "0.3.0";
const ENGINE_VERSION: &str = "0.1.31";
const BEDROCK_VERSION: &str = "1.26.60";
const WIRE_PROTOCOL: u64 = 2225;
const MAX_MANIFEST: u64 = 4 * 1024 * 1024;
const MAX_FILES: usize = 12000;
const REQUIRED: &[&str] = &[
    "engine/cinnabar.exe",
    "engine/cinnabar-updater.exe",
    "engine/bedrock-core.exe",
    "engine/bedrock-local-server.exe",
    "engine/cinnabar-cxb.exe",
    "engine/dxcompiler.dll",
    "engine/resources/prep-kit/bin/assetc.exe",
];
const HELP: &str = "\
Herspers Bedrock 0.3.0 for Windows PCs

Usage: Herspers-Bedrock.exe [-- ENGINE_ARGUMENTS...]
       Herspers-Bedrock.exe --verify-install
       Herspers-Bedrock.exe --help
       Herspers-Bedrock.exe --version

The bundled Cinnabar client is a native Rust Bedrock implementation with a Go
networking helper. It targets Bedrock 1.26.60 (protocol 2225). It is not the Java
Edition build and does not run the official Minecraft client executable.

First launch opens the client's in-app setup. Review the Minecraft EULA there,
then let it download and prepare its supported vanilla resource files. No Java,
JDK, manual server.jar, Rust installation or Go installation is needed.

Cinnabar's original branding and PolyForm Noncommercial 1.0.0 license apply to
the engine. This independent launcher is GPLv3. Read the bundled licenses and
INSTALL-BEDROCK-WINDOWS.txt. User data stays in %LOCALAPPDATA%\\Herspers Bedrock.

--verify-install checks every engine payload file against the packaged SHA-256
manifest without starting the engine, accepting an EULA or accessing accounts.
Arguments after -- are passed literally to the engine; no shell is used.
";

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
    fn from(value: io::Error) -> Self { Self::new(value.to_string()) }
}

type Result<T> = std::result::Result<T, Failure>;

#[derive(Debug, PartialEq, Eq)]
enum Action {
    Help,
    Version,
    Verify,
    Run(Vec<OsString>),
}

fn parse_args(mut args: Vec<OsString>) -> Result<Action> {
    let action = match args.first().map(OsString::as_os_str) {
        Some(first) if first == "--help" || first == "-h" => Some(Action::Help),
        Some(first) if first == "--version" => Some(Action::Version),
        Some(first) if first == "--verify-install" => Some(Action::Verify),
        _ => None,
    };
    if let Some(action) = action {
        if args.len() != 1 {
            return Err(Failure { message: "This launcher option accepts no additional arguments. Use --help for usage.".into(), code: 2 });
        }
        return Ok(action);
    }
    if args.first().is_some_and(|arg| arg == "--") { args.remove(0); }
    Ok(Action::Run(args))
}

fn is_link(metadata: &Metadata) -> bool {
    #[cfg(windows)]
    {
        use std::os::windows::fs::MetadataExt;
        metadata.file_type().is_symlink() || metadata.file_attributes() & 0x400 != 0
    }
    #[cfg(not(windows))]
    { metadata.file_type().is_symlink() }
}

fn ordinary_file(path: &Path) -> Result<Metadata> {
    let metadata = fs::symlink_metadata(path)
        .map_err(|error| Failure::new(format!("Missing bundled file {}: {error}", path.display())))?;
    if is_link(&metadata) || !metadata.is_file() {
        return Err(Failure::new(format!("Expected an ordinary bundled file: {}", path.display())));
    }
    Ok(metadata)
}

fn safe_relative(name: &str) -> Result<PathBuf> {
    if name.len() > 1024 || !name.starts_with("engine/") || name.contains(['\\', ':', '\0']) {
        return Err(Failure::new(format!("Unsafe engine manifest path: {name:?}")));
    }
    let mut path = PathBuf::new();
    for part in name.split('/') {
        let stem = part.split('.').next().unwrap_or("").to_ascii_uppercase();
        let reserved = matches!(stem.as_str(), "CON" | "PRN" | "AUX" | "NUL")
            || (stem.len() == 4 && (stem.starts_with("COM") || stem.starts_with("LPT"))
                && stem.as_bytes()[3].is_ascii_digit());
        if part.is_empty() || part == "." || part == ".." || part.ends_with(['.', ' '])
            || part.chars().any(|c| c.is_control() || "<>\"|?*".contains(c)) || reserved {
            return Err(Failure::new(format!("Unsafe engine manifest path: {name:?}")));
        }
        path.push(part);
    }
    Ok(path)
}

fn payload_file(bundle: &Path, relative: &Path) -> Result<PathBuf> {
    let mut path = bundle.to_path_buf();
    for part in relative {
        path.push(part);
        let info = fs::symlink_metadata(&path)
            .map_err(|error| Failure::new(format!("Missing bundled path {}: {error}", path.display())))?;
        if is_link(&info) {
            return Err(Failure::new(format!("Engine payload contains a link or reparse point: {}", path.display())));
        }
    }
    ordinary_file(&path)?;
    Ok(path)
}

fn sha256(path: &Path) -> Result<String> {
    let mut stream = File::open(path)?;
    let mut digest = Sha256::new();
    let mut buffer = [0u8; 128 * 1024];
    loop {
        let read = stream.read(&mut buffer)?;
        if read == 0 { break; }
        digest.update(&buffer[..read]);
    }
    Ok(format!("{:x}", digest.finalize()))
}

fn collect_engine_files(bundle: &Path, directory: &Path, output: &mut BTreeSet<String>) -> Result<()> {
    let info = fs::symlink_metadata(directory)?;
    if is_link(&info) || !info.is_dir() {
        return Err(Failure::new(format!("Expected an ordinary engine directory: {}", directory.display())));
    }
    for entry in fs::read_dir(directory)? {
        let entry = entry?;
        let info = fs::symlink_metadata(entry.path())?;
        if is_link(&info) {
            return Err(Failure::new(format!("Engine payload contains a link or reparse point: {}", entry.path().display())));
        }
        if info.is_dir() {
            collect_engine_files(bundle, &entry.path(), output)?;
        } else if info.is_file() {
            let path = entry.path();
            let name = path.strip_prefix(bundle)
                .map_err(|_| Failure::new("Engine file escaped the package"))?
                .to_str().ok_or_else(|| Failure::new("Engine file name is not Unicode"))?
                .replace('\\', "/");
            safe_relative(&name)?;
            output.insert(name);
            if output.len() > MAX_FILES { return Err(Failure::new("Engine payload exceeds its file limit")); }
        } else {
            return Err(Failure::new("Engine payload contains a special file"));
        }
    }
    Ok(())
}

fn verify_bundle(bundle: &Path) -> Result<Value> {
    let manifest_path = bundle.join("bedrock-client.json");
    if ordinary_file(&manifest_path)?.len() > MAX_MANIFEST {
        return Err(Failure::new("Engine manifest exceeds its size limit"));
    }
    let manifest: Value = serde_json::from_slice(&fs::read(&manifest_path)?)
        .map_err(|error| Failure::new(format!("Invalid engine manifest JSON: {error}")))?;
    for (field, expected) in [("product_version", VERSION), ("engine", "cinnabar"),
        ("engine_version", ENGINE_VERSION), ("bedrock_version", BEDROCK_VERSION)] {
        if manifest.get(field).and_then(Value::as_str) != Some(expected) {
            return Err(Failure::new(format!("Engine manifest has an unexpected {field}; re-extract the complete matching package.")));
        }
    }
    if manifest.get("wire_protocol").and_then(Value::as_u64) != Some(WIRE_PROTOCOL) {
        return Err(Failure::new("Engine manifest has an unexpected Bedrock wire protocol"));
    }
    for (field, expected) in [("in_app_resource_downloads", true), ("game_assets_included", false)] {
        if manifest.get(field).is_some_and(|value| value.as_bool() != Some(expected)) {
            return Err(Failure::new(format!("Engine manifest has an unexpected {field}")));
        }
    }
    let files = manifest.get("files").and_then(Value::as_object)
        .filter(|files| !files.is_empty() && files.len() <= MAX_FILES)
        .ok_or_else(|| Failure::new("Engine manifest has no valid payload file table"))?;
    for required in REQUIRED {
        if !files.contains_key(*required) {
            return Err(Failure::new(format!("Engine manifest is missing required file {required}")));
        }
    }
    let mut expected_names = BTreeSet::new();
    let mut case_names = BTreeSet::new();
    for (name, expected) in files {
        let relative = safe_relative(name)?;
        if !case_names.insert(name.to_lowercase()) {
            return Err(Failure::new("Engine manifest contains colliding Windows file names"));
        }
        let expected = expected.as_str().filter(|value| value.len() == 64
            && value.bytes().all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte)))
            .ok_or_else(|| Failure::new(format!("Invalid SHA-256 for engine file {name}")))?;
        let file = payload_file(bundle, &relative)?;
        if sha256(&file)? != expected {
            return Err(Failure::new(format!("Engine file failed its SHA-256 check: {name}. Re-extract the matching complete download.")));
        }
        expected_names.insert(name.to_owned());
    }
    let mut actual_names = BTreeSet::new();
    collect_engine_files(bundle, &bundle.join("engine"), &mut actual_names)?;
    if actual_names != expected_names {
        return Err(Failure::new("Engine directory differs from its payload manifest; re-extract the complete package into a fresh folder."));
    }
    Ok(json!({
        "product": "Herspers Bedrock", "product_version": VERSION,
        "engine": "cinnabar", "engine_version": ENGINE_VERSION,
        "bedrock_version": BEDROCK_VERSION, "wire_protocol": WIRE_PROTOCOL,
        "client_language": "Rust", "network_helper_language": "Go",
        "engine_license": "PolyForm Noncommercial 1.0.0",
        "in_app_resource_downloads": true, "game_assets_included": false,
        "payload_file_count": files.len(), "payload_hashes_verified": true,
        "verification": "SHA-256 against packaged manifest", "gameplay_tested": false,
    }))
}

fn engine_command(bundle: &Path, arguments: &[OsString], profile: &Path) -> Command {
    let mut command = Command::new(bundle.join("engine/cinnabar.exe"));
    command
        .args(arguments).current_dir(bundle.join("engine"))
        .env("CINNABAR_USER_ROOT", profile)
        // Supported upstream opt-out: this independent portable distribution is
        // pinned and must not invoke the upstream MSI product's self-updater.
        .env("CINNABAR_UPDATE_CHECK", "0")
        .env("CINNABAR_WINDOW_TITLE", "Herspers Bedrock — powered by Cinnabar")
        // This profile must obtain its own user consent, not inherit an
        // unattended-accept flag intended for a different install or script.
        .env_remove("CINNABAR_ACCEPT_MOJANG_EULA");
    command
}

fn launch(bundle: &Path, arguments: &[OsString], local_app_data: &Path) -> Result<i32> {
    verify_bundle(bundle)?;
    if !local_app_data.is_absolute() {
        return Err(Failure::new("LOCALAPPDATA must identify an absolute user-data directory"));
    }
    let profile = local_app_data.join("Herspers Bedrock");
    fs::create_dir_all(&profile)?;
    let status = engine_command(bundle, arguments, &profile).status()?;
    Ok(status.code().unwrap_or(1))
}

fn run() -> Result<i32> {
    let action = parse_args(env::args_os().skip(1).collect())?;
    match action {
        Action::Help => { print!("{HELP}"); return Ok(0); }
        Action::Version => { println!("Herspers Bedrock {VERSION}"); return Ok(0); }
        _ => {}
    }
    let executable = env::current_exe()?;
    let bundle = executable.parent().ok_or_else(|| Failure::new("Cannot locate the application folder"))?;
    if action == Action::Verify {
        let report = verify_bundle(bundle)?;
        println!("{}", serde_json::to_string_pretty(&report).map_err(|error| Failure::new(error.to_string()))?);
        return Ok(0);
    }
    if !cfg!(windows) {
        return Err(Failure::new("This package requires Windows 10/11 Intel/AMD x64."));
    }
    let local = env::var_os("LOCALAPPDATA").filter(|value| !value.is_empty())
        .map(PathBuf::from).ok_or_else(|| Failure::new("Windows did not provide LOCALAPPDATA"))?;
    match action { Action::Run(arguments) => launch(bundle, &arguments, &local), _ => unreachable!() }
}

fn own_console() -> bool {
    #[cfg(windows)]
    {
        #[link(name = "kernel32")]
        unsafe extern "system" { fn GetConsoleProcessList(processes: *mut u32, count: u32) -> u32; }
        let mut processes = [0u32; 2];
        io::stdin().is_terminal() && unsafe { GetConsoleProcessList(processes.as_mut_ptr(), 2) } == 1
    }
    #[cfg(not(windows))]
    { false }
}

fn main() {
    let code = match run() {
        Ok(code) => code,
        Err(error) => { eprintln!("Herspers Bedrock: {}", error.message); error.code }
    };
    if code != 0 && own_console() {
        eprintln!("Press Enter to close this window.");
        let _ = io::stdin().read_line(&mut String::new());
    }
    process::exit(code);
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeMap;
    use std::sync::atomic::{AtomicUsize, Ordering};
    static NEXT: AtomicUsize = AtomicUsize::new(0);

    struct Scratch(PathBuf);
    impl Scratch {
        fn new() -> Self {
            let path = env::temp_dir().join(format!("herspers-bedrock-test-{}-{}", process::id(), NEXT.fetch_add(1, Ordering::Relaxed)));
            fs::create_dir(&path).unwrap(); Self(path)
        }
        fn bundle(&self) -> PathBuf {
            let bundle = self.0.join("bundle with spaces");
            for name in REQUIRED {
                let path = bundle.join(safe_relative(name).unwrap());
                fs::create_dir_all(path.parent().unwrap()).unwrap();
                fs::write(path, format!("fixture: {name}")).unwrap();
            }
            self.manifest(&bundle);
            bundle
        }
        fn manifest(&self, bundle: &Path) {
            let mut names = BTreeSet::new(); collect_engine_files(bundle, &bundle.join("engine"), &mut names).unwrap();
            let files: BTreeMap<_, _> = names.into_iter().map(|name| {
                let hash = sha256(&bundle.join(&name)).unwrap(); (name, hash)
            }).collect();
            fs::write(bundle.join("bedrock-client.json"), serde_json::to_vec(&json!({
                "product_version":VERSION,"engine":"cinnabar","engine_version":ENGINE_VERSION,
                "bedrock_version":BEDROCK_VERSION,"wire_protocol":WIRE_PROTOCOL,
                "in_app_resource_downloads":true,"game_assets_included":false,"files":files,
            })).unwrap()).unwrap();
        }
        fn edit(&self, bundle: &Path, change: impl FnOnce(&mut Value)) {
            let path = bundle.join("bedrock-client.json");
            let mut value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap(); change(&mut value);
            fs::write(path, serde_json::to_vec(&value).unwrap()).unwrap();
        }
    }
    impl Drop for Scratch { fn drop(&mut self) { let _ = fs::remove_dir_all(&self.0); } }

    #[test]
    fn manifest_verification_reports_exact_engine_and_every_payload() {
        let scratch = Scratch::new(); let bundle = scratch.bundle();
        let report = verify_bundle(&bundle).unwrap();
        assert_eq!(report["engine_version"], ENGINE_VERSION);
        assert_eq!(report["bedrock_version"], BEDROCK_VERSION);
        assert_eq!(report["payload_file_count"], REQUIRED.len());
        assert_eq!(report["game_assets_included"], false);
        assert_eq!(report["payload_hashes_verified"], true);
    }

    #[test]
    fn missing_file_and_tampered_payload_are_refused() {
        let scratch = Scratch::new(); let bundle = scratch.bundle();
        fs::write(bundle.join(REQUIRED[0]), b"changed").unwrap();
        assert!(verify_bundle(&bundle).unwrap_err().message.contains("SHA-256"));
        fs::remove_file(bundle.join(REQUIRED[0])).unwrap();
        assert!(verify_bundle(&bundle).is_err());
    }

    #[test]
    fn identities_and_required_files_cannot_be_silently_changed() {
        let scratch = Scratch::new(); let bundle = scratch.bundle();
        for field in ["product_version", "engine", "engine_version", "bedrock_version", "wire_protocol",
            "in_app_resource_downloads", "game_assets_included"] {
            scratch.manifest(&bundle);
            scratch.edit(&bundle, |value| { value[field] = json!("wrong"); });
            assert!(verify_bundle(&bundle).is_err(), "field {field}");
        }
        scratch.manifest(&bundle);
        scratch.edit(&bundle, |value| { value["files"].as_object_mut().unwrap().remove(REQUIRED[0]); });
        assert!(verify_bundle(&bundle).is_err());
    }

    #[test]
    fn paths_cannot_escape_or_collide_with_windows_names() {
        for name in ["/engine/x", "engine/../x", "engine//x", "engine/./x", "engine/C:/x",
            "engine\\x", "engine/CON.dll", "engine/folder./x", "engine/x:stream", "engine/x\n"] {
            assert!(safe_relative(name).is_err(), "{name:?}");
        }
        assert_eq!(safe_relative("engine/resources/fonts/é.ttf").unwrap(), PathBuf::from("engine/resources/fonts/é.ttf"));
    }

    #[test]
    fn extra_engine_files_and_bad_hashes_are_refused() {
        let scratch = Scratch::new(); let bundle = scratch.bundle();
        fs::write(bundle.join("engine/unexpected.dll"), b"not listed").unwrap();
        assert!(verify_bundle(&bundle).unwrap_err().message.contains("differs"));
        fs::remove_file(bundle.join("engine/unexpected.dll")).unwrap();
        scratch.edit(&bundle, |value| { value["files"][REQUIRED[0]] = json!("not a hash"); });
        assert!(verify_bundle(&bundle).is_err());
    }

    #[test]
    fn arguments_are_literal_and_launcher_options_are_unambiguous() {
        assert_eq!(parse_args(vec!["--".into(), "--import-pack".into(), "a $(literal) pack.mcpack".into()]).unwrap(),
            Action::Run(vec!["--import-pack".into(), "a $(literal) pack.mcpack".into()]));
        assert_eq!(parse_args(vec!["--verify-install".into()]).unwrap(), Action::Verify);
        assert_eq!(parse_args(vec!["--help".into(), "extra".into()]).unwrap_err().code, 2);
    }

    #[test]
    fn launch_requires_its_own_consent_and_disables_the_external_msi_updater() {
        let command = engine_command(Path::new("bundle"), &[], Path::new("isolated profile"));
        let settings: BTreeMap<_, _> = command.get_envs().collect();
        assert_eq!(settings.get(std::ffi::OsStr::new("CINNABAR_ACCEPT_MOJANG_EULA")), Some(&None));
        assert_eq!(settings.get(std::ffi::OsStr::new("CINNABAR_UPDATE_CHECK")), Some(&Some(std::ffi::OsStr::new("0"))));
        assert_eq!(settings.get(std::ffi::OsStr::new("CINNABAR_USER_ROOT")), Some(&Some(std::ffi::OsStr::new("isolated profile"))));
    }

    #[cfg(unix)]
    #[test]
    fn links_are_refused_even_when_their_contents_match() {
        use std::os::unix::fs::symlink;
        let scratch = Scratch::new(); let bundle = scratch.bundle();
        let outside = scratch.0.join("outside"); fs::write(&outside, fs::read(bundle.join(REQUIRED[0])).unwrap()).unwrap();
        fs::remove_file(bundle.join(REQUIRED[0])).unwrap();
        symlink(outside, bundle.join(REQUIRED[0])).unwrap();
        assert!(verify_bundle(&bundle).unwrap_err().message.contains("link"));
    }

    #[cfg(unix)]
    #[test]
    fn child_receives_isolated_profile_optout_and_literal_arguments() {
        use std::os::unix::fs::PermissionsExt;
        let scratch = Scratch::new(); let bundle = scratch.bundle();
        let engine = bundle.join(REQUIRED[0]);
        fs::write(&engine, "#!/bin/sh\nprintf '%s\\n' \"$CINNABAR_USER_ROOT\" \"$CINNABAR_UPDATE_CHECK\" \"$@\" > \"$CINNABAR_USER_ROOT/probe.txt\"\nexit 7\n").unwrap();
        fs::set_permissions(&engine, fs::Permissions::from_mode(0o755)).unwrap(); scratch.manifest(&bundle);
        let local = fs::canonicalize(&scratch.0).unwrap().join("local app data");
        fs::create_dir(&local).unwrap();
        assert_eq!(launch(&bundle, &["--import-pack".into(), "pack $(literal).mcpack".into()], &local).unwrap(), 7);
        let profile = local.join("Herspers Bedrock");
        let text = fs::read_to_string(profile.join("probe.txt")).unwrap();
        let lines: Vec<_> = text.lines().collect();
        assert_eq!(lines, [profile.to_str().unwrap(), "0", "--import-pack", "pack $(literal).mcpack"]);
    }
}
