#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "hnsw_index.hpp"

namespace py = pybind11;

PYBIND11_MODULE(hnsw_cpp, m) {
  m.doc() = "HNSW vector index bindings for the Self-Optimizing RAG Platform";

  py::class_<rag::HNSWIndex>(m, "HNSWIndex")
      .def(py::init<int, std::size_t, int, int>(), py::arg("dim"),
           py::arg("max_elements"), py::arg("M") = 16, py::arg("ef_construction") = 200)
      .def(
          "add_items",
          [](rag::HNSWIndex& index, py::array_t<float, py::array::c_style | py::array::forcecast> vectors,
             const std::vector<std::int64_t>& ids) {
            if (vectors.ndim() != 2) {
              throw std::invalid_argument("vectors must be a 2D array");
            }
            const auto rows = static_cast<std::size_t>(vectors.shape(0));
            const auto cols = static_cast<std::size_t>(vectors.shape(1));
            if (rows != ids.size()) {
              throw std::invalid_argument("vectors and ids length mismatch");
            }
            std::vector<std::vector<float>> items(rows, std::vector<float>(cols));
            const float* data = vectors.data();
            for (std::size_t i = 0; i < rows; ++i) {
              for (std::size_t j = 0; j < cols; ++j) {
                items[i][j] = data[i * cols + j];
              }
            }
            index.add_items(items, ids);
          },
          py::arg("vectors"), py::arg("ids"))
      .def(
          "search",
          [](const rag::HNSWIndex& index, py::array_t<float, py::array::c_style | py::array::forcecast> query,
             int k, int ef) {
            if (query.ndim() != 1) {
              throw std::invalid_argument("query_vector must be a 1D array");
            }
            std::vector<float> q(static_cast<std::size_t>(query.shape(0)));
            std::copy_n(query.data(), q.size(), q.begin());
            const auto results = index.search(q, k, ef);
            py::list out;
            for (const auto& item : results) {
              out.append(py::make_tuple(item.first, item.second));
            }
            return out;
          },
          py::arg("query_vector"), py::arg("k") = 10, py::arg("ef") = 50)
      .def("save", &rag::HNSWIndex::save, py::arg("path"))
      .def("load", &rag::HNSWIndex::load, py::arg("path"))
      .def_property_readonly("dim", &rag::HNSWIndex::dim);
}
