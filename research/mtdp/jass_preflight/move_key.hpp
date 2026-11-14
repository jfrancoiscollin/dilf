// SPDX-License-Identifier: AGPL-3.0-or-later
#pragma once

#include "movegen.hpp"

#include <string>

inline std::string jass_move_key(const jass::Move& move) {
    const auto separator = move.is_capture() ? 'x' : '-';
    std::string result = std::to_string(move.from) + separator + std::to_string(move.to);
    for (auto squares = move.captured; squares;) {
        result += 'x' + std::to_string(jass::pop_lsb(squares));
    }
    return result;
}
