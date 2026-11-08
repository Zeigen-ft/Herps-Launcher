// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Herps Launcher contributors
// Uses the existing authoritative item-use hook and inventory/block helpers.
use super::{Game, herspers_gathering_rules as rules};
use horizon_client::items::ItemStack;
use horizon_world::registry::BlockStateId;

struct ActingWorld<'a, 'b> { game: &'a mut Game<'b>, pos: [i32; 3], state: BlockStateId }

impl rules::World for ActingWorld<'_, '_> {
    type Inventory = (Vec<Option<ItemStack>>, Option<ItemStack>);
    fn snapshot(&self) -> Self::Inventory {
        (self.game.inventory.clone(), self.game.offhand.clone())
    }
    fn restore(&mut self, before: Self::Inventory) {
        self.game.inventory = before.0;
        self.game.offhand = before.1;
    }
    fn room(&mut self, item: &str) -> u32 { self.game.native_room_for(item) }
    fn consume_flint_in_acting_hand(&mut self) -> bool {
        let hand = self.game.held_mut();
        let Some(s) = hand.as_mut() else { return false; };
        if &*s.item != "minecraft:flint" || s.count == 0 || s.damage != 0 || s.extra.is_some() {
            return false;
        }
        s.count -= 1;
        if s.count == 0 { *hand = None; }
        true
    }
    fn give(&mut self, item: &str, count: u32) -> u32 { self.game.native_give_items(item, count) }
    fn remove_target_plant(&mut self) -> bool {
        if self.game.world.block(self.pos[0], self.pos[1], self.pos[2]) != self.state {
            return false;
        }
        let Some(air) = self.game.pack.assets.registry.default_state("minecraft:air") else { return false; };
        let dimension = self.game.dim.id();
        self.game.native_set_block(dimension, self.pos, air, 3)
    }
    fn wear_knife(&mut self) { self.game.damage_held(1); }
}

impl Game<'_> {
    pub(super) fn herspers_gathering_use_on(
        &mut self, stack: &ItemStack, pos: [i32; 3], face: [i32; 3], claimed: &mut bool,
    ) {
        // Respect earlier native claims and run only on the authoritative actor.
        if *claimed || self.native_acting_player().is_none_or(|p| p.game_mode != 0) {
            return;
        }
        let items = self.items();
        // This tag comes only from the enabled, separate content add-on.
        // The starter alone never enables these new interactions.
        let enabled = [rules::SHARD, rules::FIBER, rules::KNIFE].iter().all(|id|
            items.get(id).is_some() && items.item_in_tag(rules::ENABLED_TAG, id));
        if !enabled { return; }
        let state = self.world.block(pos[0], pos[1], pos[2]);
        let name = self.res.facts().get(state).name.clone();
        let input = rules::Input { enabled, survival: true, item: &stack.item,
            plain: stack.damage == 0 && stack.extra.is_none(), block: &name,
            top_face: face == [0, 1, 0] };
        if rules::use_on(&mut ActingWorld { game: self, pos, state }, input) {
            *claimed = true;
        }
    }
}
