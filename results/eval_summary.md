# BẢNG THỐNG KÊ KẾT QUẢ ĐÁNH GIÁ (EVALUATION SUMMARY REPORT)

Báo cáo thống kê kết quả thực thi và đánh giá tương đồng ngữ nghĩa AST của mô hình trên tập dữ liệu FloodSQL-Bench.

## 1. Bảng Điểm Thực Thi (Execution Accuracy)

| Chỉ số | Số lượng câu | Tỷ lệ (%) |
| :--- | :---: | :---: |
| ✔️ Trả lời đúng (Khớp kết quả) | 169 | 38.15% |
| ❌ Chạy được nhưng sai kết quả | 104 | 23.48% |
| ⚠️ Bị lỗi cú pháp / Không viết | 170 | 38.37% |
| **Tổng số câu được chấm** | **443** | **100.00%** |

## 2. Bảng Điểm Tương Đồng Ngữ Nghĩa AST (AST Semantic Similarity)

* **Điểm tương đồng AST trung bình**: **56.39%**

### Thống kê sự thiếu hụt logic của AI (AST Mismatches):

| Loại thiếu hụt logic | Số câu bị thiếu |
| :--- | :---: |
| ❌ Thiếu bảng cần dùng (Missing Tables) | 37 |
| ❌ Thiếu điều kiện lọc (Missing Filters) | 306 |
| ❌ Thiếu điều kiện kết nối (Missing Joins) | 156 |
