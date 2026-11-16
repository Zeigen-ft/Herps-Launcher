//! Trusted parse-only probe. Never executes a datapack or Java bytecode.
use horizon_command::{Registries, vanilla};
use std::{fs, path::Path};

fn main() {
    let root = std::env::args().nth(1).expect("reviewed function folder");
    let files: Vec<_> = fs::read_dir(&root).unwrap().map(|e| e.unwrap().path()).collect();
    let mut reg = Registries { permission: 2, ..Registries::default() };
    reg.functions = files.iter().map(|p| format!("herps_dl:{}", p.file_stem().unwrap().to_str().unwrap())).collect();
    reg.entity_types = ["minecraft:player", "minecraft:item", "minecraft:marker"].map(str::to_owned).to_vec();
    reg.summonable = vec!["minecraft:marker".into()];
    reg.dimensions = ["overworld", "the_nether", "the_end"].map(|s| format!("minecraft:{s}")).to_vec();
    reg.item_tags = [15,14,10,7].map(|n| format!("herps_dl:level{n}")).to_vec();
    reg.objectives = vec!["herps_dl".into()];
    reg.blocks.insert("minecraft:air".into(), vec![]);
    reg.blocks.insert("minecraft:light".into(), vec![
        ("level".into(), (0..=15).map(|n| n.to_string()).collect()),
        ("waterlogged".into(), vec!["true".into(), "false".into()]),
    ]);
    let dispatcher = vanilla::release_dispatcher();
    let mut checked = 0;
    for path in &files {
        assert_eq!(path.extension().unwrap(), "mcfunction");
        for (index, line) in fs::read_to_string(path).unwrap().lines().enumerate() {
            let parsed = dispatcher.parse(line, &reg);
            if let Err(error) = parsed.executable() {
                panic!("{}:{}: {line}\n{:?}", Path::new(path).display(), index+1, error);
            }
            checked += 1;
        }
    }
    // Confirm this is a real syntax check, including the two unsafe legacy forms.
    for bad in ["align xyz run kill @s", "setblock ~ ~ ~ minecraft:air replace minecraft:light",
                "execute as @a run definitely_not_a_command"] {
        assert!(dispatcher.parse(bad, &reg).executable().is_err(), "accepted: {bad}");
    }
    println!("PASS: {checked} commands parsed at native permission 2; 3 invalid commands rejected. Runtime/gameplay NOT RUN.");
}
