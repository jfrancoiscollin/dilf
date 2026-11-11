// SPDX-License-Identifier: AGPL-3.0-or-later
#include "movegen.hpp"
#include "position.hpp"
#include "search.hpp"

#include <algorithm>
#include <array>
#include <iostream>
#include <stdexcept>
#include <string>
#include <string_view>
#include <tuple>
#include <vector>

namespace {

using Order = std::vector<std::string>;

std::string key(const jass::Move& move) {
    const auto separator = move.is_capture() ? 'x' : '-';
    std::string result = std::to_string(move.from) + separator + std::to_string(move.to);
    for (auto squares = move.captured; squares;) {
        result += 'x' + std::to_string(jass::pop_lsb(squares));
    }
    return result;
}

void require(bool condition, const char* detail) {
    if (!condition) throw std::runtime_error(detail);
}

Order legal_order(const jass::Position& position, bool canonical = false) {
    jass::MoveList moves;
    jass::generate_legal_moves(position, moves);
    std::vector<jass::Move> ordered(moves.begin(), moves.end());
    if (canonical) {
        const auto identity = [](const jass::Move& move) {
            return std::tie(move.from, move.to, move.captured, move.promotes);
        };
        std::sort(ordered.begin(), ordered.end(), [&](const auto& a, const auto& b) {
            return identity(a) < identity(b);
        });
    }
    Order keys;
    for (const auto& move : ordered) keys.push_back(key(move));
    return keys;
}

Order promote(const Order& ranking, const Order& legal) {
    const auto count = std::min<std::size_t>(3, ranking.size());
    Order order(ranking.begin(), ranking.begin() + static_cast<Order::difference_type>(count));
    for (const auto& action : legal) {
        if (std::find(order.begin(), order.end(), action) == order.end()) {
            order.push_back(action);
        }
    }
    require(std::is_permutation(order.begin(), order.end(), legal.begin(), legal.end()),
            "promotion changed the legal root moves");
    return order;
}

std::string schedule(const Order& order) {
    std::string moves;
    for (const auto& action : order) moves += (moves.empty() ? "" : ",") + action;
    std::string result;
    for (int depth = 1; depth <= jass::MAX_PLY; ++depth) {
        result += (depth == 1 ? "" : ";") + std::to_string(depth) + ':' + moves;
    }
    return result;
}

void check_arm(const jass::Position& position, const Order& legal, const Order& order,
               std::uint64_t budget, const char* arm, bool expect_node_stop) {
    jass::SearchDecisionTrace trace;
    jass::SearchLimits limits;
    limits.max_depth = jass::MAX_PLY;
    limits.max_nodes = budget;
    limits.node_limit_mode = jass::NodeLimitMode::Exact;
    limits.threads = 1;
    limits.search_decision_trace = &trace;
    if (!order.empty()) limits.root_order_schedule = schedule(order);

    // The two-argument overload starts with a fresh transposition table.
    const auto result = jass::search(position, limits);
    require(result.nodes <= budget, "node budget exceeded");
    require(result.root_order_failures == 0, "root schedule rejected");
    require(result.root_order_applications == (order.empty() ? 0 : trace.attempts.size()),
            "wrong number of root order applications");
    if (expect_node_stop || result.stop_reason == jass::SearchStopReason::Nodes) {
        require(result.stop_reason == jass::SearchStopReason::Nodes && result.nodes == budget,
                "expected an exact node stop");
    }
    Order catalogue;
    for (const auto& move : trace.root_actions) catalogue.push_back(key(move));
    require(catalogue == legal, "search changed the generated legal move catalogue");
    require(std::find(legal.begin(), legal.end(), key(result.best_move)) != legal.end(),
            "search returned an illegal move");
    require(!trace.attempts.empty(), "missing root trace");
    const auto& first = trace.attempts.front();
    require(first.depth == 1 && first.all_actions_searched, "incomplete depth-one root coverage");
    for (const auto& attempt : trace.attempts) {
        if (order.empty() && (attempt.depth != first.depth || attempt.attempt != first.attempt)) {
            continue;
        }
        const Order& expected = order.empty() ? legal : order;
        Order visited;
        for (const auto& action : attempt.actions) visited.push_back(key(action.move));
        require(visited.size() <= expected.size()
                && std::equal(visited.begin(), visited.end(), expected.begin()),
                "visited root order disagrees with expected order");
        if (attempt.all_actions_searched) {
            require(visited == expected, "full attempt omitted a legal move");
        }
    }
    std::cout << position.to_fen() << '\t' << arm << '\t' << budget << '\t'
              << result.nodes << '\t' << result.completed_depth << '\t'
              << jass::search_stop_reason_name(result.stop_reason) << '\t'
              << key(result.best_move) << '\t' << result.root_order_applications << '\n';
}

}  // namespace

int main() {
    try {
        constexpr std::array<std::string_view, 4> fixtures{
            "W:W31-50:B1-20",           // Quiet start with more than three actions.
            "W:W31:B20",               // Fewer than three actions.
            "W:W7,8:B40",              // Promotion.
            "W:W40,43,K2:B8,18,29,30", // Multiple captures with distinct square sets.
        };
        std::cout << "fen\tarm\tbudget\tnodes\tcompleted_depth\tstop\tbest_move\torder_applications\n";
        constexpr std::array<std::uint64_t, 3> budgets{10000, 50000, 200000};
        for (const auto fen : fixtures) {
            const auto position = jass::Position::from_fen(fen);
            require(position.has_value(), "invalid fixture FEN");
            const Order legal = legal_order(*position);
            require(!legal.empty(), "terminal smoke fixture");
            const Order canonical = legal_order(*position, true);
            // Deliberately different fixture ordering. No Scan scores or
            // experimental positions are used in the integration test.
            const Order reversed(canonical.rbegin(), canonical.rend());
            for (const auto budget : budgets) {
                const bool expect_stop = fen == fixtures.front();
                check_arm(*position, legal, {}, budget, "native", expect_stop);
                check_arm(*position, legal, promote(reversed, legal), budget, "fixture-top3", expect_stop);
                check_arm(*position, legal, promote(canonical, legal), budget, "canonical-top3", expect_stop);
            }
        }
    } catch (const std::exception& error) {
        std::cerr << "MTDP Jass preflight failed: " << error.what() << '\n';
        return 1;
    }
}
