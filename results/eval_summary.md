# BẢNG THỐNG KÊ KẾT QUẢ ĐÁNH GIÁ (EVALUATION SUMMARY REPORT)

Báo cáo thống kê kết quả thực thi và đánh giá tương đồng ngữ nghĩa AST của mô hình trên tập dữ liệu FloodSQL-Bench.

## 1. Bảng Điểm Thực Thi (Execution Accuracy)

| Chỉ số | Số lượng câu | Tỷ lệ (%) |
| :--- | :---: | :---: |
| ✔️ Trả lời đúng (Khớp kết quả) | 169 | 38.15% |
| ❌ Chạy được nhưng sai kết quả | 126 | 28.44% |
| ⚠️ Bị lỗi cú pháp / Không viết | 148 | 33.41% |
| **Tổng số câu được chấm** | **443** | **100.00%** |

## 2. Bảng Điểm Tương Đồng Ngữ Nghĩa (Semantic Similarity)

* **Điểm tương đồng Weighted AST trung bình**: **52.39%**
* **Điểm tương đồng Tree Edit Distance (TED) trung bình**: **66.06%**

### Thống kê sự thiếu hụt logic của AI (Weighted AST Mismatches):

| Loại thiếu hụt logic | Số câu bị thiếu |
| :--- | :---: |
| ❌ Thiếu bảng cần dùng (Missing Tables) | 36 |
| ❌ Thiếu điều kiện lọc (Missing Filters) | 285 |
| ❌ Thiếu điều kiện kết nối (Missing Joins) | 139 |
