//! Owned resource fixtures, not gameplay. Exercises the real native tag loader.
use horizon_client::{items::Items, mod_content::{self, ContentMod}};
use horizon_mods::{Content, Package};
use horizon_world::loot::PackOverlay;
use std::{fs, path::Path};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    let starter = Package::read(Path::new(&args[1]))?;
    let addon = Package::read(Path::new(&args[2]))?;
    assert_eq!(addon.manifest.id, "herspers_rl_gathering");
    assert!(addon.wasm.is_none());
    let content = Content::read(Path::new(&args[2]), &addon.manifest)?;
    assert!(content.items.is_empty() && content.blocks.is_empty() && content.effects.is_empty());
    assert!(content.files.iter().any(|p| p.ends_with("tags/item/enabled.json")));
    let root = Path::new(&args[4]);
    let base = root.join("base"); fs::create_dir_all(&base)?;
    fs::write(base.join("facts.json"), br#"{"states":[],"defaults":{}}"#)?;
    fs::write(base.join("gameplay-facts.json"), br#"{"states":[]}"#)?;
    let mut vanilla = serde_json::Map::new();
    for name in ["flint", "wheat", "stick", "string", "wooden_sword", "wooden_axe"] {
        let id = format!("minecraft:{name}");
        vanilla.insert(id.clone(), serde_json::json!({"minecraft:max_stack_size":64,
            "minecraft:item_model":id, "minecraft:item_name":{"text":name}}));
    }
    // The starter removes the inherited repair ingredient. The native content
    // validator learns valid component names from the vanilla table, so our
    // owned sword/axe fixtures must include that relevant real-world default.
    for name in ["wooden_sword", "wooden_axe"] {
        let tool = vanilla.get_mut(&format!("minecraft:{name}")).unwrap();
        tool["minecraft:max_stack_size"] = serde_json::json!(1);
        tool["minecraft:max_damage"] = serde_json::json!(59);
        tool["minecraft:repairable"] = serde_json::json!({"items":"minecraft:oak_planks"});
    }
    fs::write(base.join("items.json"), serde_json::to_vec(&vanilla)?)?;
    let mut mods = vec![ContentMod { id: starter.manifest.id.clone(),
        content: Content::read(Path::new(&args[1]), &starter.manifest)? }];
    let tag = "herspers_rl_gathering:enabled";
    let shard = "herspers_rl_flint:flint_shard";
    let old = root.join("starter-only"); mod_content::build(&base, &mods, &old)?;
    assert!(!Items::catalog(&old, &PackOverlay::NONE)?.item_in_tag(tag, shard));
    mods.push(ContentMod { id: addon.manifest.id.clone(), content });
    let both = root.join("both"); mod_content::build(&base, &mods, &both)?;
    let items = Items::catalog(&both, &PackOverlay::NONE)?;
    for name in ["flint_shard", "plant_fiber", "flint_knife"] {
        let id = format!("herspers_rl_flint:{name}");
        assert!(items.get(&id).is_some()); assert!(items.item_in_tag(tag, &id));
    }
    assert_eq!(fs::read(old.join("items.json"))?, fs::read(both.join("items.json"))?);
    fs::write(&args[3], serde_json::to_vec_pretty(&serde_json::json!({
        "status":"passed", "stage":2,
        "cases":["native_addon_package_no_code_or_new_items", "starter_alone_has_no_opt_in_tag",
            "enabled_addon_resolves_existing_items_in_native_tag_loader", "all_existing_item_components_unchanged"],
        "synthetic_resources":true, "gameplay_verified":false, "interactive_verified":false,
        "world_save_load_verified":false, "full_rlcraft_compatibility":false
    }))?)?;
    Ok(())
}
