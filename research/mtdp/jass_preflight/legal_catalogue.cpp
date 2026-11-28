// SPDX-License-Identifier: AGPL-3.0-or-later
#include "move_key.hpp"
#include "position.hpp"

#include <iostream>
#include <string>

int main() {
    // One input FEN and one output row per position, including terminal positions.
    for (std::string fen; std::getline(std::cin, fen);) {
        const auto position = jass::Position::from_fen(fen);
        if (!position) {
            std::cerr << "Invalid FEN: " << fen << '\n';
            return 1;
        }
        jass::MoveList moves;
        jass::generate_legal_moves(*position, moves);
        std::cout << position->to_fen();
        for (const auto& move : moves) {
            // Jass can set promotes for an existing king's capture on the back rank.
            const bool promotion = move.promotes && jass::is_man(position->piece_at(move.from));
            std::cout << '\t' << jass_move_key(move) << '=' << promotion;
        }
        std::cout << '\n';
    }
}
