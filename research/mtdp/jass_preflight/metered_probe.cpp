// SPDX-License-Identifier: AGPL-3.0-or-later
// Research-only hard-capped depth-one adapter. It never supplies a Scan score
// or an archived native winner. Each input line creates a fresh search TT.
#include "move_key.hpp"
#include "movegen.hpp"
#include "position.hpp"
#include "search.hpp"

#include <algorithm>
#include <cstdint>
#include <exception>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
using Keys = std::vector<std::string>;

std::string csv(const Keys& moves) {
    std::string out;
    for (const auto& key : moves) out += (out.empty() ? "" : ",") + key;
    return out;
}

void run(const std::string& mode, const std::string& fen,
         const std::uint64_t limit, const Keys& prefix) {
    if ((mode != "preliminary" && mode != "probe") || limit == 0)
        throw std::invalid_argument("Expected preliminary|probe and positive hard cap");
    const auto position = jass::Position::from_fen(fen);
    if (!position) throw std::invalid_argument("Invalid FMJD FEN");
    jass::MoveList legal_moves;
    jass::generate_legal_moves(*position, legal_moves);
    Keys legal;
    for (const auto& m : legal_moves) {
        const auto key = jass_move_key(m);
        if (std::find(legal.begin(), legal.end(), key) != legal.end())
            throw std::runtime_error("Duplicate live Jass action key");
        legal.push_back(key);
    }
    if (legal.empty()) throw std::runtime_error("No legal root action");
    if (mode == "probe" && prefix.size() != 1)
        throw std::invalid_argument("Probe requires exactly one live legal key");

    Keys order = prefix;
    if (order.size() > legal.size())
        throw std::invalid_argument("Prefix longer than live legal catalogue");
    for (const auto& key : legal) {
        if (std::find(prefix.begin(), prefix.end(), key) == prefix.end())
            order.push_back(key);
    }
    if (!std::is_permutation(legal.begin(), legal.end(), order.begin(), order.end()))
        throw std::invalid_argument("Requested prefix is illegal or duplicated");

    jass::SearchDecisionTrace trace;
    jass::SearchLimits limits;
    limits.max_depth = 1;
    limits.threads = 1;
    limits.max_nodes = limit;
    limits.node_limit_mode = jass::NodeLimitMode::Exact;
    limits.search_decision_trace = &trace;
    limits.root_order_schedule = "1:" + csv(order);
    limits.research_first_root_action_only = (mode == "probe");

    // The two-argument search creates a fresh transposition table.
    const auto result = jass::search(*position, limits);
    if (result.nodes > limit || trace.nodes != result.nodes
        || result.root_order_failures || result.root_order_applications != 1
        || trace.root_actions.size() != legal.size()
        || trace.attempts.size() != 1)
        throw std::runtime_error("Invalid hard-cap or root-trace execution");

    Keys reported;
    for (const auto& m : trace.root_actions) reported.push_back(jass_move_key(m));
    if (reported != legal) throw std::runtime_error("Search changed native live legal order");

    const auto& attempt = trace.attempts.front();
    if (attempt.depth != 1 || attempt.nodes_after != result.nodes
        || attempt.actions.size() > legal.size()
        || (mode == "probe" && attempt.actions.size() > 1))
        throw std::runtime_error("Unexpected depth-one trace");

    const jass::SearchDecisionActionTrace* first = nullptr;
    if (!attempt.actions.empty()) first = &attempt.actions.front();
    if (mode == "probe" && first && jass_move_key(first->move) != prefix.front())
        throw std::runtime_error("Probe searched a different first root action");

    const bool whole = attempt.completed && attempt.all_actions_searched
        && result.completed_depth == 1
        && result.stop_reason == jass::SearchStopReason::None
        && attempt.bound == jass::SearchDecisionBound::Exact;
    const bool one = first && first->completed
        && result.completed_depth == 1
        && result.stop_reason == jass::SearchStopReason::None
        && first->bound == jass::SearchDecisionBound::Exact
        && first->alpha == -jass::INF_SCORE && first->beta == jass::INF_SCORE;
    const bool completed = mode == "probe" ? one : whole;
    if (completed && result.nodes == 0)
        throw std::runtime_error("Completed search cannot report zero nodes");

    const auto key = mode == "probe" ? prefix.front()
        : (completed ? jass_move_key(attempt.best_move) : std::string{"-"});
    const int score = mode == "probe" && first ? first->score : attempt.score;
    const int alpha = mode == "probe" && first ? first->alpha : attempt.alpha;
    const int beta = mode == "probe" && first ? first->beta : attempt.beta;
    const auto bound = mode == "probe" && first ? first->bound : attempt.bound;

    // TSV schema v1: status, mode, fen, issued limit, measured nodes, complete,
    // live best/move, score, full-window endpoints, bound, stop reason,
    // number of searched actions, number of legal actions, live native order.
    std::cout << "mtdp-probe-v1" << '\t' << mode << '\t' << fen << '\t'
              << limit << '\t' << result.nodes << '\t' << (completed ? 1 : 0)
              << '\t' << key << '\t' << score << '\t' << alpha << '\t' << beta
              << '\t' << jass::search_decision_bound_name(bound)
              << '\t' << jass::search_stop_reason_name(result.stop_reason)
              << '\t' << attempt.actions.size() << '\t' << legal.size()
              << '\t' << csv(legal) << '\n';
}
}

int main() {
    try {
        std::string line;
        while (std::getline(std::cin, line)) {
            if (line.empty()) continue;
            std::istringstream input(line);
            std::string mode, fen;
            std::uint64_t limit = 0;
            if (!(input >> mode >> fen >> limit))
                throw std::invalid_argument("Expected mode FEN node_limit [root_prefix...]");
            Keys prefix;
            std::string key;
            while (input >> key) prefix.push_back(key);
            run(mode, fen, limit, prefix);
        }
    } catch (const std::exception& error) {
        std::cerr << "MTDP metered probe failure: " << error.what() << '\n';
        return 1;
    }
}
