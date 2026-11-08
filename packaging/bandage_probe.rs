//! Trusted native content/recipe/effect kernels with owned fixtures, not gameplay.
use horizon_client::{crafting::Recipes, effects::{EffectAction, EffectInstance, PlayerEffects},
    items::{ConsumeEffect, ItemStack, Items}, mod_content::{self, ContentMod}};
use horizon_mods::{Content, Package};
use horizon_world::{consumable::UseAnimation, loot::PackOverlay};
use serde_json::json;
use std::{fs, path::Path};

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().collect();
    let work = Path::new(&args[6]); let base = work.join("base");
    fs::create_dir_all(base.join("data/minecraft/recipe"))?;
    fs::write(base.join("facts.json"), br#"{"states":[],"defaults":{}}"#)?;
    fs::write(base.join("gameplay-facts.json"), br#"{"states":[]}"#)?;
    let mut vanilla = json!({
        "minecraft:paper":{"minecraft:max_stack_size":64},
        "minecraft:flint":{"minecraft:max_stack_size":64},
        "minecraft:wheat":{"minecraft:max_stack_size":64},
        "minecraft:stick":{"minecraft:max_stack_size":64},
        "minecraft:string":{"minecraft:max_stack_size":64},
        "minecraft:oak_planks":{"minecraft:max_stack_size":64},
        "minecraft:wooden_sword":{"minecraft:max_stack_size":1,"minecraft:max_damage":59,
            "minecraft:repairable":{"items":"minecraft:oak_planks"}},
        "minecraft:wooden_axe":{"minecraft:max_stack_size":1,"minecraft:max_damage":59,
            "minecraft:repairable":{"items":"minecraft:oak_planks"}},
        // Declare an owned vanilla-shaped consumable so the component validator
        // sees the same component vocabulary as legitimate prepared resources.
        "minecraft:apple":{"minecraft:max_stack_size":64,"minecraft:food":{"nutrition":4,"saturation":2.4},
            "minecraft:consumable":{"consume_seconds":1.6,"animation":"eat",
                "sound":"minecraft:entity.generic.eat","has_consume_particles":true,"on_consume_effects":[]}}
    });
    for (id, components) in vanilla.as_object_mut().unwrap() {
        components["minecraft:item_model"] = json!(id);
        components["minecraft:item_name"] = json!({"text":id});
    }
    fs::write(base.join("items.json"),serde_json::to_vec(&vanilla)?)?;
    fs::write(base.join("data/minecraft/recipe/owned.json"),serde_json::to_vec(&json!({
        "type":"minecraft:crafting_shapeless","ingredients":["minecraft:string","minecraft:string"],
        "result":{"id":"minecraft:stick","count":1}}))?)?;
    let mut mods=Vec::new();
    for n in [1,2,3] {
        let path=Path::new(&args[n]);let p=Package::read(path)?;
        mods.push(ContentMod{id:p.manifest.id.clone(),content:Content::read(path,&p.manifest)?});
    }
    let old=work.join("earlier");mod_content::build(&base,&mods,&old)?;
    let path=Path::new(&args[4]);let p=Package::read(path)?;
    assert_eq!(p.manifest.id,"herspers_rl_bandage");assert!(p.wasm.is_none());
    let content=Content::read(path,&p.manifest)?;
    assert_eq!(content.items.len(),1);assert!(content.blocks.is_empty()&&content.effects.is_empty());
    assert_eq!(content.creative_tabs.len(),1);assert_eq!(content.creative_tabs[0].items.len(),1);
    assert_eq!(content.files.iter().filter(|n|n.contains("/recipe/")).count(),1);
    mods.push(ContentMod{id:p.manifest.id.clone(),content});
    let all=work.join("all");mod_content::build(&base,&mods,&all)?;
    let old_table:serde_json::Value=serde_json::from_slice(&fs::read(old.join("items.json"))?)?;
    let table:serde_json::Value=serde_json::from_slice(&fs::read(all.join("items.json"))?)?;
    for (id, original) in old_table.as_object().unwrap(){assert_eq!(&table[id],original,"old item changed: {id}");}
    let items=Items::catalog(&all,&PackOverlay::NONE)?;
    assert!(items.item_in_tag("herspers_rl_gathering:enabled","herspers_rl_flint:flint_knife"));
    assert!(items.item_in_tag("herspers_rl_woodcutting:enabled","herspers_rl_flint:flint_hatchet"));
    let id="herspers_rl_bandage:plant_fiber_bandage";let info=items.get(id).ok_or("bandage not registered")?;
    assert_eq!(info.max_stack,16);assert_eq!(info.max_damage,0);assert!(info.food.is_none());
    assert!(info.use_remainder.is_none());assert_eq!(table[id]["minecraft:item_model"],id);
    let cons=info.consumable.as_ref().ok_or("missing consumable")?;
    assert_eq!(cons.ticks(),40);assert_eq!(cons.animation,UseAnimation::None);assert!(!cons.particles);
    assert_eq!(cons.sound,"minecraft:item.armor.equip_leather");
    let [ConsumeEffect::ApplyEffects{effects,probability}]=cons.effects.as_slice() else {panic!("wrong effect list")};
    assert_eq!(*probability,1.0);assert_eq!(effects.len(),1);
    let effect=&effects[0];assert_eq!(effect.id,"minecraft:regeneration");
    assert_eq!((effect.duration,effect.amplifier),(100,0));
    let recipes=Recipes::load(&all,&items,&PackOverlay::NONE)?;assert_eq!(recipes.crafting.len(),7);
    let stack=|id:&str,count|Some(ItemStack{item:id.into(),count,damage:0,extra:None});
    let fiber="herspers_rl_flint:plant_fiber";
    for size in [2,3] {
        for a in 0..size*size {for b in a+1..size*size {for c in b+1..size*size {for d in c+1..size*size {
            for string_slot in [a,b,c,d] {
                let mut grid=vec![None;size*size];
                for slot in [a,b,c,d]{grid[slot]=stack(if slot==string_slot{"minecraft:string"}else{fiber},16);}
                let out=recipes.craft(&grid,size).expect("shapeless bandage did not match");
                assert_eq!((&*out.item,out.count),(id,1));
                assert!(grid.iter().flatten().all(|s|s.count==16));
                grid[a]=stack("minecraft:paper",1);assert!(recipes.craft(&grid,size).is_none());
            }
        }}}}
    }
    for fibers in [0,1,2,4] {
        let mut grid=vec![None;9];grid[0]=stack("minecraft:string",1);
        for slot in 1..=fibers {grid[slot]=stack(fiber,1);}
        assert!(!recipes.craft(&grid,3).is_some_and(|s|&*s.item==id));
    }
    assert_eq!(&*recipes.craft(&[stack("minecraft:string",1),stack("minecraft:string",1),None,None],2).unwrap().item,"minecraft:stick");
    assert_eq!(&*recipes.craft(&[stack("minecraft:flint",1),None,None,None],2).unwrap().item,"herspers_rl_flint:flint_shard");
    // Actual native effect scheduler: no fake player health or invented Game run.
    let mut active=PlayerEffects::default();active.add(EffectInstance::new("regeneration",effect.duration,effect.amplifier));
    let saved=active.saved();let restored=PlayerEffects::from_saved(&saved);assert_eq!(restored.saved(),saved);
    let mut heals=Vec::new();for _ in 0..100{heals.extend(active.tick());}
    assert_eq!(heals,vec![EffectAction::Heal(1.0),EffectAction::Heal(1.0)]);assert!(active.get("regeneration").is_none());
    active.add(EffectInstance::new("regeneration",100,0));for _ in 0..10{active.tick();}
    active.add(EffectInstance::new("regeneration",100,0));assert_eq!(active.list.len(),1);
    assert_eq!(active.get("regeneration").unwrap().duration,100);
    active.add(EffectInstance::new("regeneration",200,1));active.add(EffectInstance::new("regeneration",100,0));
    assert_eq!(active.get("regeneration").unwrap().amplifier,1);
    fs::write(&args[5],serde_json::to_vec_pretty(&json!({"status":"passed","stage":4,
        "cases":["one_native_item_recipe_and_creative_tab_no_code","all_earlier_item_components_preserved",
            "gathering_and_woodcutting_tags_preserved","native_stack_limit_nonfood_and_no_remainder",
            "native_40_tick_nonparticle_consumable","native_regeneration_probability_duration_and_level",
            "all_2x2_and_3x3_shapeless_offsets_and_stacked_read_only","wrong_items_and_counts_rejected",
            "existing_recipes_preserved","native_effect_timing_and_expiry","native_effect_save_tuple_roundtrip",
            "native_effect_refresh_without_stacking_or_downgrading"],
        "synthetic_resources":true,"gameplay_verified":false,"interactive_verified":false,
        "world_save_load_verified":false,"held_use_execution_verified":false,
        "legitimate_resources_verified":false,"limb_healing_implemented":false,"full_rlcraft_compatibility":false}))?)?;
    Ok(())
}
