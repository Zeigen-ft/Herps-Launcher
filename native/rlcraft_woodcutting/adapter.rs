// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Herps Launcher contributors
// Existing authoritative dig-start and destroy hooks; no custom drop/save path.
use super::{Game, herspers_woodcutting_rules as rules};
use horizon_client::text::Text;
use horizon_world::registry::BlockStateId;

impl Game<'_> {
    pub(super) fn herspers_woodcutting_guard(&mut self, state: BlockStateId, canceled: &mut bool) {
        if *canceled { return; }
        let Some(actor) = self.native_acting_player() else { return; };
        let items = self.items();
        let enabled = items.get(rules::HATCHET).is_some()
            && items.item_in_tag(rules::ENABLED_TAG, rules::HATCHET);
        if !enabled || actor.game_mode != 0 { return; }
        let name = self.res.facts().get(state).name.clone();
        // Digging always uses the main hand, regardless of an axe in the off hand.
        let held = self.inventory.get(self.selected).and_then(Option::as_ref);
        let main_hand_axe = held.is_some_and(|s| &*s.item == rules::HATCHET
            || items.item_in_tag("minecraft:axes", &s.item));
        let main_hand_usable = held.is_some_and(|s| s.count > 0 && items.get(&s.item)
            .is_some_and(|i| i.max_damage == 0 || s.damage < i.max_damage));
        if rules::reject(rules::Input { enabled, game_mode:actor.game_mode,
            already_canceled:*canceled, log:items.block_in_tag("minecraft:logs", &name),
            main_hand_axe, main_hand_usable }) {
            *canceled = true;
            let _ = self.native_action_bar(actor.uuid,
                Text::literal("Use a Flint Hatchet or an axe to cut logs."));
        }
    }
}
