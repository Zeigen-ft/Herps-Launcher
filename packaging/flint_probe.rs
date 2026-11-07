//! Trusted native-engine probe. Owned fixtures are not gameplay or world saves.
use horizon_mods::{Content, Package};
use std::{fs, path::Path};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    let path = Path::new(&args[1]);
    let package = Package::read(path)?;
    assert_eq!(package.manifest.id, "herspers_rl_flint");
    assert!(package.wasm.is_none());
    let content = Content::read(path, &package.manifest)?;
    assert_eq!(content.items.len(), 4);
    assert!(content.blocks.is_empty() && content.effects.is_empty());
    assert_eq!(content.creative_tabs.len(), 1);
    assert_eq!(content.creative_tabs[0].items.len(), 4);
    assert_eq!(content.files.iter().filter(|p| p.contains("/recipe/")).count(), 5);
    let cases = vec!["native_package_reader", "four_items_five_recipes_no_code", "native_creative_tab"];
    #[cfg(feature = "crafting")]
    let cases = {
        let mut completed = cases;
        crafting(content, Path::new(&args[3]), &mut completed)?;
        completed
    };
    fs::write(&args[2], serde_json::to_vec_pretty(&serde_json::json!({
        "status": "passed", "stage": 1, "cases": cases,
        "native_recipe_matcher_verified": cfg!(feature = "crafting"),
        "native_tool_components_verified": cfg!(feature = "crafting"),
        "synthetic_resources": true, "interactive_verified": false,
        "gameplay_verified": false, "world_save_load_verified": false,
        "prepared_legitimate_resources_verified": false
    }))?)?;
    Ok(())
}

#[cfg(feature = "crafting")]
fn crafting(content: Content, work: &Path, cases: &mut Vec<&str>) -> Result<(), Box<dyn std::error::Error>> {
    use horizon_client::{crafting::Recipes, items::{Items, ItemStack}, mod_content::{self, ContentMod}};
    use horizon_world::loot::PackOverlay;
    use serde_json::json;
    let base = work.join("base");
    fs::create_dir_all(base.join("data/minecraft/recipe"))?;
    fs::write(base.join("facts.json"), br#"{"states":[],"defaults":{}}"#)?;
    fs::write(base.join("gameplay-facts.json"), br#"{"states":[]}"#)?;
    // Independently authored minimal resource facts, not copied Minecraft data.
    let mut vanilla = json!({
        "minecraft:flint": {"minecraft:max_stack_size": 64},
        "minecraft:wheat": {"minecraft:max_stack_size": 64},
        "minecraft:stick": {"minecraft:max_stack_size": 64},
        "minecraft:string": {"minecraft:max_stack_size": 64},
        "minecraft:wooden_sword": {"minecraft:max_stack_size": 1, "minecraft:max_damage": 59,
            "minecraft:weapon": {"item_damage_per_attack": 1},
            "minecraft:repairable": {"items": "minecraft:oak_planks"},
            "minecraft:attribute_modifiers": [{"type": "minecraft:attack_damage",
                "id": "minecraft:base_attack_damage", "amount": 3.0,
                "operation": "add_value", "slot": "mainhand"}]},
        "minecraft:wooden_axe": {"minecraft:max_stack_size": 1, "minecraft:max_damage": 59,
            "minecraft:weapon": {"item_damage_per_attack": 2},
            "minecraft:repairable": {"items": "minecraft:oak_planks"},
            "minecraft:tool": {"default_mining_speed": 1.0, "damage_per_block": 1,
                "rules": [{"blocks": ["minecraft:oak_log"], "speed": 2.0, "correct_for_drops": true}]},
            "minecraft:attribute_modifiers": [{"type": "minecraft:attack_damage",
                "id": "minecraft:base_attack_damage", "amount": 6.0,
                "operation": "add_value", "slot": "mainhand"}]}
    });
    // Prepared Minecraft templates have model/name components. Include those
    // relevant defaults in our owned fixtures so identifier rewriting is tested.
    for (id, components) in vanilla.as_object_mut().unwrap() {
        components["minecraft:item_model"] = json!(id);
        components["minecraft:item_name"] = json!({"translate": format!("item.minecraft.{}", id.trim_start_matches("minecraft:"))});
    }
    fs::write(base.join("items.json"), serde_json::to_vec(&vanilla)?)?;
    let vanilla_recipe = json!({"type": "minecraft:crafting_shapeless",
        "ingredients": ["minecraft:string", "minecraft:string"],
        "result": {"id": "minecraft:stick", "count": 1}});
    fs::write(base.join("data/minecraft/recipe/owned_preservation.json"), serde_json::to_vec(&vanilla_recipe)?)?;
    let overlay = work.join("overlay");
    let mods = [ContentMod {id: "herspers_rl_flint".into(), content}];
    assert!(mod_content::build(&base, &mods, &overlay)?.is_empty());
    let table: serde_json::Value = serde_json::from_slice(&fs::read(overlay.join("items.json"))?)?;
    for (id, original) in vanilla.as_object().unwrap() {
        assert_eq!(&table[id], original, "existing vanilla item changed: {id}");
    }
    let items = Items::catalog(&overlay, &PackOverlay::NONE)?;
    let shard = "herspers_rl_flint:flint_shard";
    let fiber = "herspers_rl_flint:plant_fiber";
    let knife = "herspers_rl_flint:flint_knife";
    let hatchet = "herspers_rl_flint:flint_hatchet";
    for id in [shard, fiber, knife, hatchet] {
        let info = items.get(id).ok_or("native item was not registered")?;
        assert_eq!(&*info.id, id);
        assert_eq!(table[id]["minecraft:item_model"], id);
    }
    for (id, original, durability) in [(knife, "minecraft:wooden_sword", 32), (hatchet, "minecraft:wooden_axe", 48)] {
        let info = items.get(id).unwrap();
        assert_eq!(info.max_stack, 1);
        assert_eq!(info.max_damage, durability);
        assert_eq!(info.attack_damage, items.get(original).unwrap().attack_damage);
        assert_eq!(info.weapon_damage, items.get(original).unwrap().weapon_damage);
        assert!(!info.components.iter().any(|c| c == "minecraft:repairable"));
    }
    let stack = |id: &str, count| Some(ItemStack {item: id.into(), count, damage: 0, extra: None});
    assert_eq!(items.mining_speed(stack(hatchet, 1).as_ref(), "minecraft:oak_log"), 2.0);
    assert_eq!(items.mining_speed(stack(hatchet, 1).as_ref(), "minecraft:stone"), 1.0);
    assert!(items.correct_for_drops(stack(hatchet, 1).as_ref(), "minecraft:oak_log"));
    let recipes = Recipes::load(&overlay, &items, &PackOverlay::NONE)?;
    assert_eq!(recipes.crafting.len(), 6);
    let check = |grid: &[Option<ItemStack>], size, id: &str, count| {
        let result = recipes.craft(grid, size).expect("native recipe failed to match");
        assert_eq!((&*result.item, result.count), (id, count));
    };
    for size in [2, 3] {
        for slot in 0..size*size {
            let mut grid = vec![None; size*size];
            grid[slot] = stack("minecraft:flint", 1); check(&grid, size, shard, 2);
            grid[slot] = stack("minecraft:wheat", 1); check(&grid, size, fiber, 3);
            grid[slot] = stack("minecraft:stick", 1); assert!(recipes.craft(&grid, size).is_none());
        }
        for x in 0..size {
            for y in 0..size-1 {
                let mut grid = vec![None; size*size];
                grid[y*size+x] = stack(shard, 1);
                grid[(y+1)*size+x] = stack("minecraft:stick", 1);
                check(&grid, size, knife, 1);
                grid[y*size+x] = stack("minecraft:flint", 1);
                assert!(recipes.craft(&grid, size).is_none());
            }
        }
        for x in 0..size-1 {
            for y in 0..size-1 {
                for mirrored in [false, true] {
                    let mut grid = vec![None; size*size];
                    let a = if mirrored {1} else {0};
                    let b = 1-a;
                    grid[y*size+x+a] = stack(shard, 1);
                    grid[y*size+x+b] = stack("minecraft:string", 1);
                    grid[(y+1)*size+x+b] = stack("minecraft:stick", 1);
                    check(&grid, size, hatchet, 1);
                    grid[(y+1)*size+x+a] = stack("minecraft:stick", 1);
                    assert!(recipes.craft(&grid, size).is_none());
                }
            }
        }
    }
    for empty in 0..4 {
        let mut grid = vec![stack(fiber, 1); 4]; grid[empty] = None;
        check(&grid, 2, "minecraft:string", 1);
        grid[empty] = stack(fiber, 1); assert!(recipes.craft(&grid, 2).is_none());
    }
    check(&[stack("minecraft:string", 1), stack("minecraft:string", 1), None, None], 2, "minecraft:stick", 1);
    let mut stacked = vec![None; 4]; stacked[0] = stack("minecraft:flint", 16);
    check(&stacked, 2, shard, 2);
    assert_eq!(stacked[0].as_ref().unwrap().count, 16); // matcher is read-only
    cases.extend(["native_content_overlay_and_vanilla_preservation", "native_tool_durability_and_weapon_components",
        "native_hatchet_mining_rules", "native_shard_and_fiber_all_grid_offsets",
        "native_knife_all_offsets", "native_hatchet_all_offsets_and_mirrors",
        "native_fiber_string_and_wrong_counts", "native_existing_recipe_preserved",
        "wrong_inputs_extra_cells_rejected", "stacked_match_is_read_only"]);
    Ok(())
}
