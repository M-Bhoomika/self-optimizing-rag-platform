#pragma once

#include <cstdint>
#include <memory>
#include <string>
#include <utility>
#include <vector>

namespace rag {

/// Search result: (id, distance).
using SearchResult = std::pair<std::int64_t, float>;

/// HNSW index wrapper with hnswlib-compatible semantics.
///
/// When compiled with HNSWLIB_AVAILABLE, delegates to hnswlib. Otherwise
/// provides a minimal brute-force fallback for build/test without the library.
class HNSWIndex {
 public:
  HNSWIndex(int dim, std::size_t max_elements, int M = 16, int ef_construction = 200);
  ~HNSWIndex();

  HNSWIndex(const HNSWIndex&) = delete;
  HNSWIndex& operator=(const HNSWIndex&) = delete;

  void add_items(const std::vector<std::vector<float>>& vectors,
                 const std::vector<std::int64_t>& ids);

  std::vector<SearchResult> search(const std::vector<float>& query_vector, int k = 10,
                                   int ef = 50) const;

  void save(const std::string& path) const;
  void load(const std::string& path);

  int dim() const { return dim_; }

 private:
  int dim_;
  std::size_t max_elements_;
  int M_;
  int ef_construction_;

  struct Impl;
  std::unique_ptr<Impl> impl_;
};

}  // namespace rag
