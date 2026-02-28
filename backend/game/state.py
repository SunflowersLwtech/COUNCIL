"""Game phase state machine with validated transitions."""

from backend.models.game_models import GameState

# Valid phase transitions
TRANSITIONS = {
    "lobby": ["discussion"],
    "discussion": ["voting"],
    "voting": ["reveal"],
    "reveal": ["night", "ended"],
    "night": ["discussion"],
    "ended": [],
}


class InvalidTransition(Exception):
    """Raised when an invalid phase transition is attempted."""
    pass


def validate_transition(current: str, target: str) -> bool:
    """Check if a phase transition is valid."""
    return target in TRANSITIONS.get(current, [])


def transition(state: GameState, target: str) -> GameState:
    """Transition the game to a new phase, raising on invalid transitions."""
    if not validate_transition(state.phase, target):
        raise InvalidTransition(
            f"Cannot transition from '{state.phase}' to '{target}'. "
            f"Valid targets: {TRANSITIONS.get(state.phase, [])}"
        )
    previous = state.phase
    state.phase = target
    if target == "discussion" and previous != "lobby":
        # New round when returning to discussion from reveal or night
        state.round += 1
    return state


def advance_to_discussion(state: GameState) -> GameState:
    """Move from lobby, reveal, or night to discussion phase."""
    if state.phase == "lobby":
        state.phase = "discussion"
    elif state.phase in ("reveal", "night"):
        state.phase = "discussion"
        state.round += 1
    else:
        raise InvalidTransition(
            f"Cannot start discussion from '{state.phase}'."
        )
    # Clear votes for new round
    state.votes = []
    return state


def advance_to_night(state: GameState) -> GameState:
    """Move from reveal to night phase."""
    if state.phase != "reveal":
        raise InvalidTransition(
            f"Cannot start night from '{state.phase}'."
        )
    state.phase = "night"
    state.night_actions = []
    return state


def advance_to_voting(state: GameState) -> GameState:
    """Move from discussion to voting phase."""
    if state.phase != "discussion":
        raise InvalidTransition(
            f"Cannot start voting from '{state.phase}'."
        )
    state.phase = "voting"
    state.votes = []
    return state


def advance_to_reveal(state: GameState) -> GameState:
    """Move from voting to reveal phase."""
    if state.phase != "voting":
        raise InvalidTransition(
            f"Cannot reveal from '{state.phase}'."
        )
    state.phase = "reveal"
    return state


def end_game(state: GameState, winner: str) -> GameState:
    """End the game with a winner."""
    state.phase = "ended"
    state.winner = winner
    return state


def eliminate_character(state: GameState, character_id: str) -> GameState:
    """Mark a character (or the player) as eliminated."""
    # Handle player elimination
    if character_id == "player" and state.player_role:
        state.player_role.is_eliminated = True
        if "player" not in state.eliminated:
            state.eliminated.append("player")
        return state

    if character_id not in state.eliminated:
        state.eliminated.append(character_id)
    for char in state.characters:
        if char.id == character_id:
            char.is_eliminated = True
            break
    return state


def get_alive_characters(state: GameState):
    """Return list of characters that have not been eliminated."""
    return [c for c in state.characters if not c.is_eliminated]
