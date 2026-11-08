//! Actual pinned asset/model/metadata/PNG code; no Game, GPU or world simulation.
use horizon_assets::{bake::{bake_block_model, BlockModelTransform}, blockstate::{BlockStateDefinition, VariantSet},
    model::CuboidModel, resolve::ModelLibrary};
use std::{collections::{BTreeMap, BTreeSet}, fs, io::BufReader, path::{Path, PathBuf}};
mod native_pack_format;

fn asset(root: &Path, id: &str, kind: &str, suffix: &str) -> PathBuf {
    let (ns, path) = id.split_once(':').unwrap_or(("minecraft", id));
    root.join("assets").join(ns).join(kind).join(format!("{path}{suffix}"))
}
fn model_files(root: &Path, at: &Path, out: &mut BTreeMap<String, CuboidModel>) -> Result<(), Box<dyn std::error::Error>> {
    for entry in fs::read_dir(at)? {
        let p = entry?.path();
        if p.is_dir() { model_files(root, &p, out)?; }
        else if p.extension().is_some_and(|e| e == "json") {
            let rel=p.strip_prefix(root.join("assets"))?.to_string_lossy().replace('\\',"/");
            let (namespace, rest)=rel.split_once("/models/").ok_or("not a model path")?;
            let id=format!("{namespace}:{}",rest.trim_end_matches(".json"));
            out.insert(id,CuboidModel::from_json(&fs::read_to_string(p)?)?);
        }
    }
    Ok(())
}
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args:Vec<String>=std::env::args().collect();let root=Path::new(&args[1]);
    let manifest:serde_json::Value=serde_json::from_slice(&fs::read(&args[2])?)?;
    let meta:serde_json::Value=serde_json::from_slice(&fs::read(root.join("pack.mcmeta"))?)?;
    let current=horizon_core::version::RESOURCE_PACK_FORMAT;assert_eq!(current,(97,1));
    let (min,max)=native_pack_format::check(&meta["pack"]).map_err(|e|format!("native pack metadata: {e}"))?;
    assert_eq!((min,max),(current,current));
    let mut models=BTreeMap::new();
    for ns in ["minecraft","betterleaves"] {model_files(root,&root.join(format!("assets/{ns}/models")),&mut models)?;}
    assert_eq!(models.len(),64);
    // Owned empty parent stands in for vanilla's block/block display defaults.
    // It is only a fixture; the delivered pack uses legitimate vanilla resources.
    models.insert("minecraft:block/block".into(),CuboidModel::from_json("{}")?);
    let library=ModelLibrary::new(models)?;
    let mut variants=0;let mut quads_total=0;let mut tint_counts=BTreeMap::<i32,usize>::new();
    let mut sprites=BTreeSet::new();
    for block in manifest["target_blocks"].as_array().ok_or("targets missing")? {
        let id=format!("minecraft:{}",block.as_str().ok_or("bad block")?);
        let def=BlockStateDefinition::from_json(&fs::read_to_string(asset(root,&id,"blockstates",".json"))?)?;
        assert!(def.multipart.is_none());let map=def.variants.as_ref().ok_or("variants missing")?;
        assert_eq!(map.len(),1);assert_eq!(map[0].0,"");
        let VariantSet::Weighted(choices)=&map[0].1 else {panic!("expected native weighted leaves")};
        assert_eq!(choices.len(),16);
        for (variant,weight) in choices {
            assert_eq!(*weight,1);let resolved=library.resolve(&variant.model)?;
            assert!(resolved.unresolved_textures.is_empty());assert_eq!(resolved.elements().len(),3);
            let quads=bake_block_model(&resolved,BlockModelTransform::new(variant.rotations,variant.uv_lock))?;
            assert_eq!(quads.len(),10);assert_eq!(quads.iter().filter(|q|q.cull.is_none()).count(),4);
            assert!(quads.iter().any(|q|q.positions.iter().flatten().any(|v|*v<0.0||*v>1.0)),"no bush fringe");
            for q in &quads {
                assert!(q.positions.iter().flatten().all(|v|v.is_finite()&&(-2.0..=3.0).contains(v)));
                assert!(q.uv.iter().flatten().all(|v|v.is_finite()&&(-0.00001..=1.00001).contains(v)));
                assert!([-1,0].contains(&q.tint_index));*tint_counts.entry(q.tint_index).or_default()+=1;
                assert!(asset(root,&q.material.sprite,"textures",".png").is_file());
                sprites.insert(q.material.sprite.clone());
            }
            quads_total+=quads.len();variants+=1;
        }
    }
    assert_eq!(variants,224);assert_eq!(quads_total,2240);assert_eq!(sprites.len(),14);
    let mut alpha=serde_json::Map::new();
    for sprite in sprites {
        let mut decoder=png::Decoder::new(BufReader::new(fs::File::open(asset(root,&sprite,"textures",".png"))?));
        decoder.set_limits(png::Limits{bytes:1<<20});
        decoder.set_transformations(png::Transformations::EXPAND|png::Transformations::STRIP_16);
        let mut reader=decoder.read_info()?;let size=reader.output_buffer_size().ok_or("image too large")?;
        assert!(size<=4096);let mut bytes=vec![0;size];let info=reader.next_frame(&mut bytes)?;
        assert_eq!((info.width,info.height),(32,32));assert_eq!(info.color_type,png::ColorType::Rgba);
        assert_eq!(info.bit_depth,png::BitDepth::Eight);
        let pixels=&bytes[..info.buffer_size()];let transparent=pixels.chunks_exact(4).filter(|p|p[3]==0).count();
        let opaque=pixels.chunks_exact(4).filter(|p|p[3]==255).count();assert!(transparent>0&&opaque>0);
        alpha.insert(sprite,serde_json::json!({"width":32,"height":32,"transparent_pixels":transparent,"opaque_pixels":opaque}));
    }
    fs::write(&args[3],serde_json::to_vec_pretty(&serde_json::json!({
        "status":"passed","cases":["actual_native_pack_format_validator_97_1",
            "native_64_models_parent_and_texture_resolution","native_14_weighted_blockstates",
            "native_224_rotated_variants_2240_quads","four_unculled_bush_fringe_faces_per_variant",
            "finite_geometry_and_normalized_uv","native_tint_indices_preserved",
            "native_png_decoder_14_rgba_cutout_textures"],
        "models":64,"leaf_definitions":14,"variants":variants,"quads":quads_total,
        "tint_counts":tint_counts,"texture_alpha":alpha,"owned_vanilla_parent_fixture":true,
        "metadata_parser":"unmodified production packs.rs format helpers extracted by the verifier",
        "visual_verified":false,"gameplay_verified":false,"performance_verified":false,
        "game_pack_selection_ui_verified":false,"full_game_renderer_executed":false
    }))?)?;
    Ok(())
}
