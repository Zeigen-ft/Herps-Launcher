// SPDX-License-Identifier: MIT
// Copyright (c) 2026 Herps Launcher contributors
// Original native progression policy; no Java mod source or assets.

pub const HATCHET: &str = "herspers_rl_flint:flint_hatchet";
pub const ENABLED_TAG: &str = "herspers_rl_woodcutting:enabled";

pub struct Input {
    pub enabled: bool,
    pub game_mode: i32,
    pub already_canceled: bool,
    pub log: bool,
    pub main_hand_axe: bool,
    pub main_hand_usable: bool,
}

/// Ask the existing hook to cancel, without changing blocks, drops or tools.
/// Earlier cancellation is left entirely with its owner. Only Survival opts in.
pub fn reject(input: Input) -> bool {
    !input.already_canceled && input.enabled && input.game_mode == 0 && input.log
        && !(input.main_hand_axe && input.main_hand_usable)
}

#[cfg(test)]
mod tests {
    use super::*;

    fn hand() -> Input {
        Input { enabled:true, game_mode:0, already_canceled:false, log:true,
            main_hand_axe:false, main_hand_usable:false }
    }
    #[test] fn empty_hand_cannot_break_logs() { assert!(reject(hand())); }
    #[test] fn disabled_stage_keeps_previous_log_behavior() {
        assert!(!reject(Input { enabled:false, ..hand() }));
    }
    #[test] fn other_modes_keep_vanilla_rules() {
        for mode in [-1,1,2,3,4] { assert!(!reject(Input { game_mode:mode, ..hand() })); }
    }
    #[test] fn leaves_bushes_planks_and_other_nonlogs_are_untouched() {
        assert!(!reject(Input { log:false, ..hand() }));
    }
    #[test] fn usable_flint_hatchet_or_tagged_axe_is_allowed() {
        assert!(!reject(Input { main_hand_axe:true, main_hand_usable:true, ..hand() }));
    }
    #[test] fn broken_or_empty_axe_cannot_bypass_progression() {
        assert!(reject(Input { main_hand_axe:true, main_hand_usable:false, ..hand() }));
    }
    #[test] fn knife_sword_or_pickaxe_is_not_an_axe() {
        assert!(reject(Input { main_hand_usable:true, ..hand() }));
    }
    #[test] fn offhand_axe_does_not_authorize_an_empty_main_hand() {
        // Only the actual main-hand facts enter this policy.
        assert!(reject(hand()));
    }
    #[test] fn earlier_cancel_is_not_reinterpreted_as_a_new_action() {
        assert!(!reject(Input { already_canceled:true, ..hand() }));
        assert!(!reject(Input { already_canceled:true, main_hand_axe:true,
            main_hand_usable:true, ..hand() }));
    }
}
