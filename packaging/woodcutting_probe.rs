//! Original fixtures through native content, item tags, policy and loot code.
//! No real Minecraft inputs, game world or original mod code are executed.
use horizon_client::{items::Items, mod_content::{self, ContentMod}};
use horizon_core::random::LegacyRandom;
use horizon_mods::{Content, Package};
use horizon_world::loot::{LootData, PackOverlay};
use std::{fs, path::Path};
mod woodcutting_rules;
use woodcutting_rules as rules;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    let root = Path::new(&args[5]);
    let base = root.join("base"); fs::create_dir_all(&base)?;
    fs::write(base.join("facts.json"), br#"{"states":[],"defaults":{}}"#)?;
    fs::write(base.join("gameplay-facts.json"), br#"{"states":[]}"#)?;
    let axes = ["wooden_axe","stone_axe","copper_axe","iron_axe","golden_axe","diamond_axe","netherite_axe"];
    let mut vanilla = serde_json::Map::new();
    for name in ["flint","wheat","stick","string","oak_planks","wooden_sword"]
        .into_iter().chain(axes) {
        let id = format!("minecraft:{name}");
        vanilla.insert(id.clone(), serde_json::json!({"minecraft:max_stack_size":64,
            "minecraft:item_model":id,"minecraft:item_name":{"text":name}}));
    }
    for name in std::iter::once("wooden_sword").chain(axes) {
        let tool = vanilla.get_mut(&format!("minecraft:{name}")).unwrap();
        tool["minecraft:max_stack_size"] = serde_json::json!(1);
        tool["minecraft:max_damage"] = serde_json::json!(59);
        tool["minecraft:repairable"] = serde_json::json!({"items":"minecraft:oak_planks"});
    }
    fs::write(base.join("items.json"), serde_json::to_vec(&vanilla)?)?;
    let item_tags=base.join("data/minecraft/tags/item");fs::create_dir_all(&item_tags)?;
    fs::write(item_tags.join("axes.json"),serde_json::to_vec(&serde_json::json!({
        "values":axes.map(|n|format!("minecraft:{n}"))}))?)?;
    let block_tags=base.join("data/minecraft/tags/block");fs::create_dir_all(&block_tags)?;
    fs::write(block_tags.join("logs.json"),br#"{"values":["minecraft:oak_log","minecraft:birch_log","minecraft:stripped_oak_log","minecraft:crimson_stem"]}"#)?;
    // Owned vanilla-shaped examples exercise the existing chance/count loader;
    // they are not imported Minecraft loot tables or proof of physical drops.
    let loot=base.join("data/minecraft/loot_table/blocks");fs::create_dir_all(&loot)?;
    for (name,chance,count) in [("oak_leaves",0.02,1),("dead_bush",1.0,2)] {
        fs::write(loot.join(format!("{name}.json")),serde_json::to_vec(&serde_json::json!({
            "type":"minecraft:block", "pools":[{"rolls":1,"entries":[{
                "type":"minecraft:item","name":"minecraft:stick"}],
                "conditions":[{"condition":"minecraft:random_chance","chance":chance}],
                "functions":[{"function":"minecraft:set_count","count":count}]}]}))?)?;
    }
    let mut mods=Vec::new();
    for index in [1,2] {
        let p=Path::new(&args[index]);let package=Package::read(p)?;
        mods.push(ContentMod{id:package.manifest.id.clone(),content:Content::read(p,&package.manifest)?});
    }
    let old=root.join("earlier-stages");mod_content::build(&base,&mods,&old)?;
    let p=Path::new(&args[3]);let package=Package::read(p)?;
    assert_eq!(package.manifest.id,"herspers_rl_woodcutting");assert!(package.wasm.is_none());
    let content=Content::read(p,&package.manifest)?;
    assert!(content.items.is_empty() && content.blocks.is_empty() && content.effects.is_empty());
    assert!(!content.files.iter().any(|n|n.contains("/recipe/")));
    mods.push(ContentMod{id:package.manifest.id.clone(),content});
    let all=root.join("all-stages");mod_content::build(&base,&mods,&all)?;
    let before=Items::catalog(&old,&PackOverlay::NONE)?;
    let items=Items::catalog(&all,&PackOverlay::NONE)?;
    assert!(!before.item_in_tag(rules::ENABLED_TAG,rules::HATCHET));
    assert!(items.item_in_tag(rules::ENABLED_TAG,rules::HATCHET));
    assert!(items.item_in_tag("herspers_rl_gathering:enabled","herspers_rl_flint:flint_knife"));
    assert_eq!(fs::read(old.join("items.json"))?,fs::read(all.join("items.json"))?);
    let input=|enabled,block:&str,item:Option<&str>,usable|rules::Input {
        enabled,game_mode:0,already_canceled:false,log:items.block_in_tag("minecraft:logs",block),
        main_hand_axe:item.is_some_and(|id|id==rules::HATCHET || items.item_in_tag("minecraft:axes",id)),
        main_hand_usable:usable};
    for block in ["minecraft:oak_log","minecraft:birch_log","minecraft:stripped_oak_log","minecraft:crimson_stem"] {
        assert!(rules::reject(input(true,block,None,false)));
        assert!(!rules::reject(input(false,block,None,false)));
        assert!(!rules::reject(input(true,block,Some(rules::HATCHET),true)));
        for axe in axes {assert!(!rules::reject(input(true,block,Some(&format!("minecraft:{axe}")),true)));}
        assert!(rules::reject(input(true,block,Some("herspers_rl_flint:flint_knife"),true)));
        assert!(rules::reject(input(true,block,Some(rules::HATCHET),false)));
    }
    for block in ["minecraft:oak_leaves","minecraft:dead_bush","minecraft:oak_planks","minecraft:stone"] {
        assert!(!rules::reject(input(true,block,None,false)));
    }
    let before_loot=LootData::load(&old,&PackOverlay::NONE)?;
    let after_loot=LootData::load(&all,&PackOverlay::NONE)?;
    for name in ["oak_leaves","dead_bush"] {
        assert_eq!(fs::read(old.join(format!("data/minecraft/loot_table/blocks/{name}.json")))?,
            fs::read(all.join(format!("data/minecraft/loot_table/blocks/{name}.json")))?);
        let mut found=false;
        for seed in 0..2048 {
            let mut a=LegacyRandom::new(seed*104729);let mut b=a.clone();
            let id=format!("minecraft:blocks/{name}");
            let left=before_loot.roll(&id,&mut a,0.0,None,None);
            let right=after_loot.roll(&id,&mut b,0.0,None,None);
            assert_eq!(left,right);
            found |= right.iter().any(|s|s.item=="minecraft:stick" && s.count>0);
        }
        assert!(found,"owned bootstrap stick table never produced sticks: {name}");
    }
    fs::write(&args[4],serde_json::to_vec_pretty(&serde_json::json!({
        "status":"passed","stage":3,"cases":["native_tag_only_package_no_new_items_or_recipes",
            "earlier_stages_do_not_enable_restriction","native_log_and_axe_tags_drive_policy",
            "hatchet_and_seven_owned_axe_fixtures_pass","nonlogs_and_bootstrap_plants_unrestricted",
            "all_existing_item_components_unchanged","owned_leaf_stick_loot_unchanged_and_evaluated",
            "owned_dead_bush_stick_loot_unchanged_and_evaluated"],
        "synthetic_resources":true,"gameplay_verified":false,"interactive_verified":false,
        "world_save_load_verified":false,"legitimate_resource_bootstrap_verified":false,
        "full_rlcraft_compatibility":false
    }))?)?;
    Ok(())
}
