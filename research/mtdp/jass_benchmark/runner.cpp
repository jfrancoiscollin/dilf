// SPDX-License-Identifier: AGPL-3.0-or-later
#include "../jass_preflight/move_key.hpp"
#include "position.hpp"
#include "search.hpp"

#include <algorithm>
#include <chrono>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using Order = std::vector<std::string>;

std::string joined(const Order& keys) {
    std::string result;
    for (const auto& key : keys) result += (result.empty() ? "" : ",") + key;
    return result;
}

void run(const std::string& fen, std::uint64_t budget, const Order& prefix) {
    const auto position = jass::Position::from_fen(fen);
    if (!position || budget == 0) throw std::runtime_error("Invalid FEN or node budget");
    jass::MoveList moves;
    jass::generate_legal_moves(*position, moves);
    Order legal;
    for (const auto& move : moves) legal.push_back(jass_move_key(move));

    Order order = prefix;
    for (const auto& key : legal) {
        if (std::find(prefix.begin(), prefix.end(), key) == prefix.end()) order.push_back(key);
    }
    if (!std::is_permutation(legal.begin(), legal.end(), order.begin(), order.end())) {
        throw std::runtime_error("Requested root order changes the legal catalogue");
    }

    jass::SearchDecisionTrace trace;
    jass::SearchLimits limits;
    limits.max_depth = jass::MAX_PLY;
    limits.max_nodes = budget;
    limits.node_limit_mode = jass::NodeLimitMode::Exact;
    limits.search_decision_trace = &trace;
    if (!prefix.empty()) {
        const auto csv = joined(order);
        for (int depth = 1; depth <= limits.max_depth; ++depth) {
            limits.root_order_schedule += (depth == 1 ? "" : ";") + std::to_string(depth) + ':' + csv;
        }
    }

    const auto start = std::chrono::steady_clock::now();
    const auto result = jass::search(*position, limits);
    const auto elapsed = std::chrono::duration_cast<std::chrono::microseconds>(
        std::chrono::steady_clock::now() - start).count();
    if (result.nodes > budget || result.root_order_failures != 0
        || result.root_order_applications != (prefix.empty() ? 0 : trace.attempts.size())
        || (result.stop_reason == jass::SearchStopReason::Nodes && result.nodes != budget)
        || trace.attempts.empty() || trace.attempts.front().depth != 1
        || !trace.attempts.front().all_actions_searched) {
        throw std::runtime_error("Search violated the node or root-order contract");
    }
    Order traced_legal;
    for (const auto& move : trace.root_actions) traced_legal.push_back(jass_move_key(move));
    if (traced_legal != legal) throw std::runtime_error("Search changed the legal catalogue");

    Order pv;
    for (const auto& move : result.pv) pv.push_back(jass_move_key(move));
    std::cout << position->to_fen() << '\t' << budget << '\t' << result.nodes << '\t'
              << result.completed_depth << '\t' << jass::search_stop_reason_name(result.stop_reason)
              << '\t' << jass_move_key(result.best_move) << '\t' << result.score << '\t'
              << elapsed << '\t' << joined(pv) << '\t' << joined(legal) << '\t' << joined(order);
    for (const auto& attempt : trace.attempts) {
        Order visited;
        for (const auto& action : attempt.actions) visited.push_back(jass_move_key(action.move));
        if ((!prefix.empty() || &attempt == &trace.attempts.front())
            && (visited.size() > order.size()
                || !std::equal(visited.begin(), visited.end(), order.begin())
                || (attempt.all_actions_searched && visited != order))) {
            throw std::runtime_error("Observed root order differs from the requested schedule");
        }
        std::cout << '\t' << attempt.depth << ':' << attempt.attempt << ':'
                  << attempt.completed << ':' << attempt.all_actions_searched << ':'
                  << attempt.nodes_after << ':' << joined(visited);
    }
    std::cout << '\n';
}
}  // namespace

int main() {
    try {
        for (std::string line; std::getline(std::cin, line);) {
            std::istringstream input(line);
            std::string fen;
            std::uint64_t budget = 0;
            if (!(input >> fen >> budget)) throw std::runtime_error("Invalid benchmark row");
            Order prefix;
            for (std::string key; input >> key;) prefix.push_back(key);
            run(fen, budget, prefix);
        }
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
