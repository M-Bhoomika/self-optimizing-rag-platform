#include "hnsw_index.hpp"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <stdexcept>

#if defined(HNSWLIB_AVAILABLE)
#include "hnswlib/hnswlib.h"
#endif

namespace rag {

namespace {

float l2_distance(const std::vector<float>& a, const std::vector<float>& b) {
  float sum = 0.0f;
  for (std::size_t i = 0; i < a.size(); ++i) {
    const float d = a[i] - b[i];
    sum += d * d;
  }
  return sum;
}

}  // namespace

struct HNSWIndex::Impl {
#if defined(HNSWLIB_AVAILABLE)
  std::unique_ptr<hnswlib::SpaceInterface<float>> space;
  std::unique_ptr<hnswlib::HierarchicalNSW<float>> index;
#else
  int dim = 0;
  std::vector<std::vector<float>> vectors;
  std::vector<std::int64_t> ids;
#endif
};

HNSWIndex::HNSWIndex(int dim, std::size_t max_elements, int M, int ef_construction)
    : dim_(dim),
      max_elements_(max_elements),
      M_(M),
      ef_construction_(ef_construction),
      impl_(std::make_unique<Impl>()) {
  if (dim <= 0) {
    throw std::invalid_argument("dim must be positive");
  }
#if defined(HNSWLIB_AVAILABLE)
  impl_->space = std::make_unique<hnswlib::L2Space>(static_cast<std::size_t>(dim));
  impl_->index = std::make_unique<hnswlib::HierarchicalNSW<float>>(
      impl_->space.get(), max_elements, M, ef_construction);
#else
  impl_->dim = dim;
#endif
}

HNSWIndex::~HNSWIndex() = default;

void HNSWIndex::add_items(const std::vector<std::vector<float>>& vectors,
                          const std::vector<std::int64_t>& ids) {
  if (vectors.size() != ids.size()) {
    throw std::invalid_argument("vectors and ids must have the same length");
  }
#if defined(HNSWLIB_AVAILABLE)
  for (std::size_t i = 0; i < vectors.size(); ++i) {
    if (static_cast<int>(vectors[i].size()) != dim_) {
      throw std::invalid_argument("vector dimension mismatch");
    }
    impl_->index->addPoint(vectors[i].data(), ids[i]);
  }
#else
  for (std::size_t i = 0; i < vectors.size(); ++i) {
    if (static_cast<int>(vectors[i].size()) != dim_) {
      throw std::invalid_argument("vector dimension mismatch");
    }
    impl_->vectors.push_back(vectors[i]);
    impl_->ids.push_back(ids[i]);
  }
#endif
}

std::vector<SearchResult> HNSWIndex::search(const std::vector<float>& query_vector, int k,
                                            int ef) const {
  if (static_cast<int>(query_vector.size()) != dim_) {
    throw std::invalid_argument("query vector dimension mismatch");
  }
#if defined(HNSWLIB_AVAILABLE)
  impl_->index->setEf(ef);
  auto result = impl_->index->searchKnn(query_vector.data(), k);
  std::vector<SearchResult> out;
  out.reserve(result.size());
  while (!result.empty()) {
    out.emplace_back(result.top().second, result.top().first);
    result.pop();
  }
  std::reverse(out.begin(), out.end());
  return out;
#else
  std::vector<SearchResult> scored;
  scored.reserve(impl_->vectors.size());
  for (std::size_t i = 0; i < impl_->vectors.size(); ++i) {
    scored.emplace_back(impl_->ids[i], l2_distance(query_vector, impl_->vectors[i]));
  }
  std::sort(scored.begin(), scored.end(),
            [](const SearchResult& a, const SearchResult& b) { return a.second < b.second; });
  if (static_cast<int>(scored.size()) > k) {
    scored.resize(static_cast<std::size_t>(k));
  }
  return scored;
#endif
}

void HNSWIndex::save(const std::string& path) const {
#if defined(HNSWLIB_AVAILABLE)
  impl_->index->saveIndex(path);
#else
  std::ofstream out(path, std::ios::binary);
  if (!out) {
    throw std::runtime_error("failed to open path for save: " + path);
  }
  const std::size_t n = impl_->vectors.size();
  out.write(reinterpret_cast<const char*>(&n), sizeof(n));
  for (std::size_t i = 0; i < n; ++i) {
    out.write(reinterpret_cast<const char*>(&impl_->ids[i]), sizeof(impl_->ids[i]));
    out.write(reinterpret_cast<const char*>(impl_->vectors[i].data()), sizeof(float) * dim_);
  }
#endif
}

void HNSWIndex::load(const std::string& path) {
#if defined(HNSWLIB_AVAILABLE)
  impl_->index = std::make_unique<hnswlib::HierarchicalNSW<float>>(
      impl_->space.get(), path, false, max_elements_, true);
#else
  std::ifstream in(path, std::ios::binary);
  if (!in) {
    throw std::runtime_error("failed to open path for load: " + path);
  }
  std::size_t n = 0;
  in.read(reinterpret_cast<char*>(&n), sizeof(n));
  impl_->vectors.clear();
  impl_->ids.clear();
  impl_->vectors.reserve(n);
  impl_->ids.reserve(n);
  for (std::size_t i = 0; i < n; ++i) {
    std::int64_t id = 0;
    in.read(reinterpret_cast<char*>(&id), sizeof(id));
    std::vector<float> vec(static_cast<std::size_t>(dim_));
    in.read(reinterpret_cast<char*>(vec.data()), sizeof(float) * dim_);
    impl_->ids.push_back(id);
    impl_->vectors.push_back(std::move(vec));
  }
#endif
}

}  // namespace rag
