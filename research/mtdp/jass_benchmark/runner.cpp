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

void run(const std::string& fen, std::uint64_t budget, const Order& prefix, bool initial_only, bool record_depth_ceiling) {
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
    limits.threads = 1;
    limits.node_limit_mode = jass::NodeLimitMode::Exact;
    limits.search_decision_trace = &trace;
    if (!prefix.empty()) {
        const auto csv = joined(order);
        const int scheduled_depths = initial_only ? 1 : limits.max_depth;
        for (int depth = 1; depth <= scheduled_depths; ++depth) {
            limits.root_order_schedule += (depth == 1 ? "" : ";") + std::to_string(depth) + ':' + csv;
        }
    }

#ifdef MTDP_JASS_INITIAL_ONLY
    limits.root_order_initial_only = initial_only && !prefix.empty();
#endif
    // The two-argument overload creates a fresh transposition table per search.
    const auto start = std::chrono::steady_clock::now();
    const auto result = jass::search(*position, limits);
    const auto elapsed = std::chrono::duration_cast<std::chrono::microseconds>(
        std::chrono::steady_clock::now() - start).count();
    const std::size_t expected_applications =
        prefix.empty() ? 0 : (initial_only ? 1 : trace.attempts.size());
    const bool depth_ceiling = record_depth_ceiling && result.nodes < budget
        && result.stop_reason == jass::SearchStopReason::None
        && result.completed_depth == limits.max_depth;
    if (result.nodes != budget && !depth_ceiling) {
        throw std::runtime_error("Node budget mismatch for " + fen + ": consumed "
            + std::to_string(result.nodes) + " of " + std::to_string(budget)
            + " (" + jass::search_stop_reason_name(result.stop_reason)
            + ", depth " + std::to_string(result.completed_depth) + ")");
    }
    if (result.root_order_failures != 0
        || result.root_order_applications != expected_applications
        || trace.attempts.empty() || trace.attempts.front().depth != 1
        || !trace.attempts.front().all_actions_searched
        || (initial_only && (!trace.attempts.front().completed || trace.attempts.back().depth < 2))) {
        throw std::runtime_error("Search violated the node or root-order contract");
    }
    Order traced_legal;
    for (const auto& move : trace.root_actions) traced_legal.push_back(jass_move_key(move));
    if (traced_legal != legal) throw std::runtime_error("Search changed the legal catalogue");

    Order pv;
    for (const auto& move : result.pv) pv.push_back(jass_move_key(move));
    std::cout << position->to_fen() << '\t' << budget << '\t' << result.nodes << '\t'
              << result.completed_depth << '\t'
              << (depth_ceiling ? "depth_ceiling" : jass::search_stop_reason_name(result.stop_reason))
              << '\t' << jass_move_key(result.best_move) << '\t' << result.score << '\t'
              << elapsed << '\t' << joined(pv) << '\t' << joined(legal) << '\t' << joined(order);
    Order adaptive = legal;
    const jass::SearchDecisionAttemptTrace* previous = nullptr;
    for (const auto& attempt : trace.attempts) {
        if (initial_only && previous && attempt.depth != previous->depth) {
            const auto best = jass_move_key(previous->best_move);
            const auto entry = std::find(adaptive.begin(), adaptive.end(), best);
            if (!previous->completed || attempt.depth != previous->depth + 1
                || entry == adaptive.end()) {
                throw std::runtime_error("Invalid transition between root depths for " + fen);
            }
            std::iter_swap(adaptive.begin(), entry);
        }
        const Order& expected = initial_only && attempt.depth > 1 ? adaptive : order;
        Order visited;
        for (const auto& action : attempt.actions) visited.push_back(jass_move_key(action.move));
        if ((initial_only || !prefix.empty() || !previous)
            && (visited.size() > expected.size()
                || !std::equal(visited.begin(), visited.end(), expected.begin())
                || (attempt.all_actions_searched && visited != expected))) {
            throw std::runtime_error("Observed root order differs from the requested schedule");
        }
        std::cout << '\t' << attempt.depth << ':' << attempt.attempt << ':'
                  << attempt.completed << ':' << attempt.all_actions_searched << ':'
                  << attempt.nodes_after << ':' << joined(visited);
        if (initial_only) {
            std::cout << ':' << jass_move_key(attempt.best_move) << ':' << joined(expected);
        }
        previous = &attempt;
    }
    std::cout << '\n';
}
}  // namespace

int main(int argc, char** argv) {
    try {
        const bool initial_only = argc >= 2 && std::string(argv[1]) == "--initial-only";
        const bool record_depth_ceiling = argc == 3 && initial_only
            && std::string(argv[2]) == "--record-depth-ceiling";
        if (argc != 1 && !(argc == 2 && initial_only) && !record_depth_ceiling) {
            throw std::runtime_error("Invalid benchmark option");
        }
#ifndef MTDP_JASS_INITIAL_ONLY
        if (initial_only) throw std::runtime_error("Runner built without initial-only support");
#endif
        for (std::string line; std::getline(std::cin, line);) {
            std::istringstream input(line);
            std::string fen;
            std::uint64_t budget = 0;
            if (!(input >> fen >> budget)) throw std::runtime_error("Invalid benchmark row");
            Order prefix;
            for (std::string key; input >> key;) prefix.push_back(key);
            run(fen, budget, prefix, initial_only, record_depth_ceiling);
        }
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
