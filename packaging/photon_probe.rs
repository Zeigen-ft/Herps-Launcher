// SPDX-License-Identifier: MIT
// Original test code; no third-party shader, image or other pack contents.
#[cfg(test)]
mod private_photon_input {
    use super::{environment::Sky, lightmap};

    #[test]
    fn private_fragment_enables_full_light_and_replacement_restores_normal_light() {
        let root = std::path::PathBuf::from(std::env::var_os("HERPS_TEST_PHOTON_ROOT").unwrap());
        let path = root.join("assets/minecraft/shaders/core/lightmap.fsh");
        let original = std::fs::read(&path).unwrap();
        let sky = Sky {
            sky_light_factor: 1.0,
            sky_light_color: [1.0; 3],
            block_light_tint: [1.0; 3],
            ..Default::default()
        };
        let normal = lightmap::pixels(&sky, 0.0, 0.0, 0.0, 0.0, 0.0, false);
        assert!(lightmap::fullbright_override(&root));
        assert_eq!(lightmap::pixels(&sky, 1.0, 1.0, 1.0, 0.5, 1.0,
            lightmap::fullbright_override(&root)), [255; 1024]);
        assert_eq!(std::fs::read(&path).unwrap(), original);
        // Emulate a different effective overlay, not the resource-pack UI itself.
        std::fs::write(&path, b"owned unrelated effective lightmap fixture").unwrap();
        assert!(!lightmap::fullbright_override(&root));
        assert_eq!(lightmap::pixels(&sky, 0.0, 0.0, 0.0, 0.0, 0.0,
            lightmap::fullbright_override(&root)), normal);
        std::fs::write(&path, &original).unwrap();
        assert!(lightmap::fullbright_override(&root));
        std::fs::remove_file(&path).unwrap();
        assert!(!lightmap::fullbright_override(&root));
        // The separate Fullbright option remains independent of any pack.
        assert_eq!(lightmap::pixels(&sky, 1.0, 0.0, 0.0, 0.0, 0.0, true), [255; 1024]);
    }
}
