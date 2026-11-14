// SPDX-License-Identifier: AGPL-3.0-or-later
#include "move_key.hpp"
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
    for (const auto& move : ordered) keys.push_back(jass_move_key(move));
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
#ifdef MTDP_JASS_INITIAL_ONLY
    return "1:" + moves;
#else
    std::string result;
    for (int depth = 1; depth <= jass::MAX_PLY; ++depth) {
        result += (depth == 1 ? "" : ";") + std::to_string(depth) + ':' + moves;
    }
    return result;
#endif
}

#ifdef MTDP_JASS_INITIAL_ONLY
void hoist(Order& order, const std::string& best) {
    const auto found = std::find(order.begin(), order.end(), best);
    require(found != order.end(), "previous iteration returned an illegal move");
    std::iter_swap(order.begin(), found);
}

void print_order(const Order& order) {
    for (std::size_t i = 0; i < order.size(); ++i) {
        if (i != 0) std::cout << ',';
        std::cout << order[i];
    }
}

bool check_initial_trace(const jass::Position& position, const Order& legal,
                         const Order& seeded, std::uint64_t budget, const char* arm,
                         const jass::SearchDecisionTrace& trace) {
    Order adaptive = legal;
    const auto& first = trace.attempts.front();
    require(first.completed && first.all_actions_searched, "depth one did not complete");
    require(trace.attempts.size() > 1, "missing native recovery at depth two");
    bool distinguishes_persistence = false;
    for (std::size_t i = 0; i < trace.attempts.size(); ++i) {
        const auto& attempt = trace.attempts[i];
        if (i != 0 && attempt.depth != trace.attempts[i - 1].depth) {
            const auto& previous = trace.attempts[i - 1];
            require(previous.completed && previous.depth + 1 == attempt.depth,
                    "invalid trace across completed depths");
            hoist(adaptive, jass_move_key(previous.best_move));
        }
        const Order& expected = attempt.depth == 1 ? seeded : adaptive;
        Order visited;
        for (const auto& action : attempt.actions) visited.push_back(jass_move_key(action.move));
        require(visited.size() <= expected.size()
                && std::equal(visited.begin(), visited.end(), expected.begin())
                && (!attempt.all_actions_searched || visited == expected),
                "visited order disagrees with initial-only/native ordering");
        if (attempt.depth == 2 && attempt.all_actions_searched) {
            Order leaked = seeded;
            hoist(leaked, jass_move_key(first.best_move));
            distinguishes_persistence = visited != leaked;
        }
        const bool completed_depth = attempt.completed
            && (i + 1 == trace.attempts.size() ? trace.completed_depth == attempt.depth
                : trace.attempts[i + 1].depth != attempt.depth);
        std::cout << position.to_fen() << '\t' << arm << '\t' << budget << '\t'
                  << attempt.depth << '\t' << attempt.attempt << '\t'
                  << completed_depth << '\t' << attempt.all_actions_searched << '\t'
                  << attempt.nodes_after << '\t' << jass_move_key(attempt.best_move)
                  << "\tfresh-1MiB\t";
        print_order(legal);
        std::cout << '\t';
        print_order(expected);
        std::cout << '\t';
        print_order(visited);
        std::cout << '\n';
    }
    return distinguishes_persistence;
}
#endif

bool check_arm(const jass::Position& position, const Order& legal, const Order& order,
               std::uint64_t budget, const char* arm, bool expect_node_stop) {
    jass::SearchDecisionTrace trace;
    jass::SearchLimits limits;
    limits.max_depth = jass::MAX_PLY;
    limits.max_nodes = budget;
    limits.node_limit_mode = jass::NodeLimitMode::Exact;
    limits.threads = 1;
    limits.search_decision_trace = &trace;
    if (!order.empty()) limits.root_order_schedule = schedule(order);
#ifdef MTDP_JASS_INITIAL_ONLY
    limits.root_order_initial_only = !order.empty();
#endif

    // The two-argument overload starts with a fresh transposition table.
    const auto result = jass::search(position, limits);
    require(result.nodes <= budget, "node budget exceeded");
    require(result.root_order_failures == 0, "root schedule rejected");
    const std::size_t expected_applications = order.empty() ? 0 :
#ifdef MTDP_JASS_INITIAL_ONLY
        1;
#else
        trace.attempts.size();
#endif
    require(result.root_order_applications == expected_applications,
            "wrong number of root order applications");
    if (expect_node_stop || result.stop_reason == jass::SearchStopReason::Nodes) {
        require(result.stop_reason == jass::SearchStopReason::Nodes && result.nodes == budget,
                "expected an exact node stop");
    }
    Order catalogue;
    for (const auto& move : trace.root_actions) catalogue.push_back(jass_move_key(move));
    require(catalogue == legal, "search changed the generated legal move catalogue");
    require(std::find(legal.begin(), legal.end(), jass_move_key(result.best_move)) != legal.end(),
            "search returned an illegal move");
    require(!trace.attempts.empty(), "missing root trace");
    const auto& first = trace.attempts.front();
    require(first.depth == 1 && first.all_actions_searched, "incomplete depth-one root coverage");
#ifdef MTDP_JASS_INITIAL_ONLY
    return check_initial_trace(position, legal, order.empty() ? legal : order, budget, arm, trace);
#else
    for (const auto& attempt : trace.attempts) {
        if (order.empty() && (attempt.depth != first.depth || attempt.attempt != first.attempt)) {
            continue;
        }
        const Order& expected = order.empty() ? legal : order;
        Order visited;
        for (const auto& action : attempt.actions) visited.push_back(jass_move_key(action.move));
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
              << jass_move_key(result.best_move) << '\t' << result.root_order_applications << '\n';
    return false;
#endif
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
#ifdef MTDP_JASS_INITIAL_ONLY
        std::cout << "fen\tarm\tbudget\tdepth\tattempt\tcompleted_depth\tall_actions_searched"
                     "\tnodes_after\tbest_move\ttt_at_search_start\tlegal\texpected\tvisited\n";
        bool distinguishes_persistence = false;
#else
        std::cout << "fen\tarm\tbudget\tnodes\tcompleted_depth\tstop\tbest_move\torder_applications\n";
#endif
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
#ifdef MTDP_JASS_INITIAL_ONLY
                // The two-move fixture can reach the depth ceiling before the node cap.
                if (fen == fixtures[1] && budget != budgets.front()) continue;
                check_arm(*position, legal, {}, budget, "native", true);
                const bool detected = check_arm(
                    *position, legal, promote(reversed, legal), budget, "fixture-top3", true);
                distinguishes_persistence |= detected;
                check_arm(*position, legal, promote(canonical, legal), budget, "canonical-top3", true);
#else
                const bool expect_stop = fen == fixtures.front();
                check_arm(*position, legal, {}, budget, "native", expect_stop);
                check_arm(*position, legal, promote(reversed, legal), budget, "fixture-top3", expect_stop);
                check_arm(*position, legal, promote(canonical, legal), budget, "canonical-top3", expect_stop);
#endif
            }
        }
#ifdef MTDP_JASS_INITIAL_ONLY
        require(distinguishes_persistence, "fixtures cannot detect a leaked first permutation");
#endif
    } catch (const std::exception& error) {
        std::cerr << "MTDP Jass preflight failed: " << error.what() << '\n';
        return 1;
    }
}
