//! Trusted headless validation of our content against the pinned native engine.
//! Synthetic resource fixtures are NOT a real world, graphics or save/load test.
use horizon_mods::{Content, Package};
use std::{fs, path::Path};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    let path = Path::new(&args[1]);
    let package = Package::read(path)?;
    assert_eq!(package.manifest.id, "herspers_rl_chainmail");
    assert!(package.wasm.is_none());
    let content = Content::read(path, &package.manifest)?;
    assert_eq!(content.items.len(), 1);
    assert!(content.blocks.is_empty() && content.effects.is_empty());
    assert_eq!(content.items[0].template, "minecraft:iron_nugget");
    assert_eq!(content.items[0].id, "herspers_rl_chainmail:chainmail_plate");
    assert_eq!(content.files.iter().filter(|p| p.contains("/recipe/")).count(), 2);
    let mut cases = vec!["native_package_reader", "native_content_api_02", "one_item_two_recipes_no_code"];
    #[cfg(feature = "crafting")]
    crafting(content, Path::new(&args[3]), &mut cases)?;
    fs::write(&args[2], serde_json::to_vec_pretty(&serde_json::json!({
        "status": "passed", "cases": cases,
        "native_recipe_matcher_verified": cfg!(feature = "crafting"),
        "synthetic_resources": true, "interactive_verified": false,
        "gameplay_verified": false, "save_load_verified": false,
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
    // Owned minimal fixtures: no copied proprietary game data.
    let vanilla = json!({
        "minecraft:iron_nugget": {"minecraft:max_stack_size": 64,
            "minecraft:item_name": {"translate": "item.minecraft.iron_nugget"},
            "minecraft:item_model": "minecraft:iron_nugget"},
        "minecraft:chainmail_boots": {"minecraft:max_stack_size": 1},
        "minecraft:gold_nugget": {"minecraft:max_stack_size": 64}
    });
    fs::write(base.join("items.json"), serde_json::to_vec(&vanilla)?)?;
    let overlay = work.join("overlay");
    let mods = [ContentMod {id: "herspers_rl_chainmail".into(), content}];
    assert!(mod_content::build(&base, &mods, &overlay)?.is_empty());
    let table: serde_json::Value = serde_json::from_slice(&fs::read(overlay.join("items.json"))?)?;
    let plate = "herspers_rl_chainmail:chainmail_plate";
    assert_eq!(table[plate]["minecraft:max_stack_size"], 64);
    assert_eq!(table[plate]["minecraft:item_name"]["translate"], "item.herspers_rl_chainmail.chainmail_plate");
    assert_eq!(table[plate]["minecraft:item_model"], plate);
    assert_eq!(table["minecraft:chainmail_boots"], vanilla["minecraft:chainmail_boots"]);
    let items = Items::catalog(&overlay, &PackOverlay::NONE)?;
    assert!(items.get(plate).is_some());
    let recipes = Recipes::load(&overlay, &items, &PackOverlay::NONE)?;
    assert_eq!(recipes.crafting.len(), 2);
    let stack = |id: &str, count| Some(ItemStack {item: id.into(), count, damage: 0, extra: None});
    let nugget = || stack("minecraft:iron_nugget", 1);
    let four = vec![nugget(), nugget(), nugget(), nugget()];
    let result = recipes.craft(&four, 2).ok_or("plate recipe did not match")?;
    assert_eq!((&*result.item, result.count), (plate, 1));
    // Every possible offset in the crafting table; no extra ingredient allowed.
    for (x, y) in [(0, 0), (1, 0), (0, 1), (1, 1)] {
        let mut grid = vec![None; 9];
        for (dx, dy) in [(0, 0), (1, 0), (0, 1), (1, 1)] {
            grid[(y + dy) * 3 + x + dx] = nugget();
        }
        assert_eq!(&*recipes.craft(&grid, 3).ok_or("offset did not match")?.item, plate);
        let empty = grid.iter().position(Option::is_none).unwrap();
        grid[empty] = nugget();
        assert!(recipes.craft(&grid, 3).is_none());
    }
    let mut wrong = four.clone();
    wrong[0] = stack("minecraft:gold_nugget", 1);
    assert!(recipes.craft(&wrong, 2).is_none());
    wrong[0] = None;
    assert!(recipes.craft(&wrong, 2).is_none());
    for y in [0, 1] {
        let mut boots = vec![None; 9];
        for (x, dy) in [(0, 0), (2, 0), (0, 1), (2, 1)] {
            boots[(y + dy) * 3 + x] = stack(plate, 1);
        }
        let result = recipes.craft(&boots, 3).ok_or("boots did not match")?;
        assert_eq!((&*result.item, result.count), ("minecraft:chainmail_boots", 1));
        boots[y * 3 + 1] = stack(plate, 1);
        assert!(recipes.craft(&boots, 3).is_none());
    }
    // Stacked inputs still return one recipe's output. Actual shift-click
    // consumption/inventory updates belong to physical gameplay acceptance.
    let stacked = vec![stack("minecraft:iron_nugget", 4); 4];
    assert_eq!(recipes.craft(&stacked, 2).unwrap().count, 1);
    assert_eq!(stacked[0].as_ref().unwrap().count, 4);
    cases.extend(["native_content_overlay", "item_template_name_model_fallback",
        "vanilla_boots_unchanged", "native_plate_2x2_and_all_table_offsets",
        "native_boots_both_rows", "wrong_inputs_and_extra_cells_rejected",
        "stacked_match_output_count"]);
    Ok(())
}
