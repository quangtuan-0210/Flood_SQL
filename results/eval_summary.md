# BẢNG THỐNG KÊ KẾT QUẢ ĐÁNH GIÁ (EVALUATION SUMMARY REPORT)

Báo cáo thống kê kết quả thực thi và đánh giá tương đồng ngữ nghĩa AST của mô hình trên tập dữ liệu FloodSQL-Bench.

## 1. Bảng Điểm Thực Thi (Execution Accuracy)

| Chỉ số | Số lượng câu | Tỷ lệ (%) |
| :--- | :---: | :---: |
| ✔️ Trả lời đúng (Khớp kết quả) | 167 | 40.73% |
| ❌ Chạy được nhưng sai kết quả | 122 | 29.76% |
| ⚠️ Bị lỗi cú pháp / Không viết | 121 | 29.51% |
| **Tổng số câu được chấm** | **410** | **100.00%** |

## 2. Bảng Điểm Tương Đồng Ngữ Nghĩa AST (AST Semantic Similarity)

* **Điểm tương đồng AST trung bình**: **60.49%**

### Thống kê sự thiếu hụt logic của AI (AST Mismatches):

| Loại thiếu hụt logic | Số câu bị thiếu |
| :--- | :---: |
| ❌ Thiếu bảng cần dùng (Missing Tables) | 37 |
| ❌ Thiếu điều kiện lọc (Missing Filters) | 303 |
| ❌ Thiếu điều kiện kết nối (Missing Joins) | 154 |
