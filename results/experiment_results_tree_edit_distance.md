# BÁO CÁO THỰC NGHIỆM ĐÁNH GIÁ TRUY VẤN TEXT-TO-SPATIAL SQL (TREE EDIT DISTANCE)

Báo cáo này được tự động tạo lập từ kết quả chạy đánh giá mô hình `vllm/Qwen3.6-35B-A3B-GGUF` kết hợp với API embedding `mirai-embedding` trên tập dữ liệu FloodSQL-Bench.

## 1. Bảng So sánh Hiệu năng Theo Cấp độ (L0 - L6)

Dưới đây là bảng thống kê điểm số trung bình của mô hình theo từng mức từ L0 (Dễ nhất) đến L6 (Khó nhất):

| Mức độ | Số lượng câu | Độ chính xác thực thi (Execution Acc) | Điểm tương đồng Tree Edit Distance (TED Similarity) | Điểm tương đồng văn bản SQL (Text Similarity) |
| :--- | :---: | :---: | :---: | :---: |
| L0 | 50 | 78.00% | 80.65% | 53.68% |
| L1 | 100 | 60.00% | 70.79% | 39.69% |
| L2 | 150 | 40.67% | 82.28% | 32.63% |
| L3 | 50 | 14.00% | 55.84% | 27.68% |
| L4 | 43 | 4.65% | 44.32% | 19.01% |
| L5 | 50 | 0.00% | 22.29% | 8.72% |
| **Trung bình cộng** | **443** | **38.15%** | **66.06%** | **32.02%** |

* **Nhận xét chung**:
  - **Độ chính xác thực thi (Execution Accuracy)** phản ánh tỷ lệ câu chạy ra kết quả khớp 100% trên DuckDB.
  - **Điểm tương đồng Tree Edit Distance (TED Similarity)** đo lường số bước sửa đổi tối thiểu (thêm, xóa, thay thế nút) trên cây cú pháp AST đã chuẩn hóa để biến đổi truy vấn Predicted thành Ground Truth, cho điểm số phản ánh độ chính xác phân cấp cấu trúc.
  - **Điểm tương đồng văn bản (Text Similarity)** dựa trên từ vựng thuần túy, thường có xu hướng thấp hơn điểm AST do sự khác biệt nhỏ về cách viết thường/hoa, khoảng trắng hoặc alias không làm ảnh hưởng ngữ nghĩa nhưng làm lệch chữ.

## 2. Bảng So sánh 12 Cặp Spatial SQL Tiêu Biểu (L0 - L5)

Dưới đây là bảng thống kê 12 cặp truy vấn đại diện được trích xuất từ thực nghiệm để đánh giá chi tiết:

| Cặp số | Mã câu hỏi | Mức độ | Điểm tương đồng TED | Kết quả Thực thi | Nhận xét chi tiết nguyên nhân khác biệt |
| :---: | :--- | :---: | :---: | :---: | :--- |
| 1 | L0_0001 | L0 | 0.54 | Đúng | Tương đương kết quả: Khác biệt cấu trúc nhẹ (Khoảng cách = 24.0), kết quả chạy khớp. |
| 2 | L0_0002 | L0 | 0.86 | Sai | Khác biệt logic: Cấu trúc AST khác biệt đáng kể (Edit distance = 6.0 trên tổng 42 nút). |
| 3 | L1_0001 | L1 | 0.86 | Đúng | Tương đương kết quả: Khác biệt cấu trúc nhẹ (Khoảng cách = 13.0), kết quả chạy khớp. |
| 4 | L1_0004 | L1 | 0.92 | Sai | Khác biệt logic: Cấu trúc AST khác biệt đáng kể (Edit distance = 8.0 trên tổng 97 nút). |
| 5 | L2_0003 | L2 | 0.88 | Đúng | Tương đương kết quả: Khác biệt cấu trúc nhẹ (Khoảng cách = 13.0), kết quả chạy khớp. |
| 6 | L2_0001 | L2 | 0.81 | Sai | Khác biệt logic: Cấu trúc AST khác biệt đáng kể (Edit distance = 12.0 trên tổng 62 nút). |
| 7 | L3_0013 | L3 | 0.75 | Đúng | Tương đương kết quả: Khác biệt cấu trúc nhẹ (Khoảng cách = 26.0), kết quả chạy khớp. |
| 8 | L3_0002 | L3 | 0.53 | Sai | Khác biệt logic: Cấu trúc AST khác biệt đáng kể (Edit distance = 72.0 trên tổng 153 nút). |
| 9 | L4_0015 | L4 | 0.55 | Đúng | Tương đương kết quả: Khác biệt cấu trúc nhẹ (Khoảng cách = 40.0), kết quả chạy khớp. |
| 10 | L4_0005 | L4 | 0.82 | Sai | Khác biệt logic: Cấu trúc AST khác biệt đáng kể (Edit distance = 20.0 trên tổng 110 nút). |
| 11 | L5_0001 | L5 | 0.87 | Sai | Khác biệt logic: Cấu trúc AST khác biệt đáng kể (Edit distance = 13.0 trên tổng 102 nút). |
| 12 | L4_0007 | L4 | 0.70 | Sai | Khác biệt logic: Cấu trúc AST khác biệt đáng kể (Edit distance = 30.0 trên tổng 100 nút). |

## 3. Phân tích Chi tiết 12 Cặp Truy vấn (AST & Trực quan hóa)


### Cặp 1: L0_0001 (Mức L0)
* **Câu hỏi**: In Harris County, Texas (identified by GEOID starting with 48201), how many NFIP claims have a dateOfLoss on or after 2010-01-01?
* **Điểm tương đồng TED**: 0.54
* **Độ chính xác thực thi**: Đúng

#### Truy vấn so sánh:
* **Ground Truth SQL**:
  ```sql
  SELECT COUNT(*) AS num_claims FROM claims WHERE GEOID LIKE '48201%' AND dateOfLoss >= DATE '2010-01-01';
  ```
* **Predicted SQL**:
  ```sql
  SELECT COUNT(claims.id) FROM claims JOIN county ON LEFT(claims.GEOID, 5) = county.GEOID WHERE county.GEOID = '48201' AND claims.dateOfLoss >= '2010-01-01'
  ```

#### Trực quan hóa Cây AST chuẩn hóa:
```text
CÂY AST GROUND TRUTH:
└─ Select
  └─ Alias
    └─ Count
      └─ Star
    └─ Identifier
  └─ From
    └─ Table
      └─ Identifier
  └─ Where
    └─ And
      └─ Like
        └─ Column
          └─ Identifier
        └─ Literal
      └─ GTE
        └─ Column
          └─ Identifier
        └─ Cast
          └─ Literal
          └─ DataType

CÂY AST PREDICTED:
└─ Select
  └─ Count
    └─ Column
      └─ Identifier
      └─ Identifier
  └─ From
    └─ Table
      └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ EQ
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Left
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Literal
  └─ Where
    └─ And
      └─ EQ
        └─ Literal
        └─ Column
          └─ Identifier
          └─ Identifier
      └─ GTE
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Literal
```

#### Phân tích lỗi và khác biệt:
- **Nhận xét**: Tương đương kết quả: Khác biệt cấu trúc nhẹ (Khoảng cách = 24.0), kết quả chạy khớp.
- **Khoảng cách hiệu chỉnh cây (Tree Edit Distance)**: 24.0
- **Kích thước cây Ground Truth (Ground Truth AST Size)**: 20 nút
- **Kích thước cây Predicted (Predicted AST Size)**: 32 nút
- **Tổng số nút tối đa (Max Possible Distance)**: 52

---


### Cặp 2: L0_0002 (Mức L0)
* **Câu hỏi**: What is the total area of valid FEMA Flood Hazard Zone polygons in Florida (STATEFP = '12') labeled as AE?
* **Điểm tương đồng TED**: 0.86
* **Độ chính xác thực thi**: Sai

#### Truy vấn so sánh:
* **Ground Truth SQL**:
  ```sql
  SELECT SUM(ST_Area(geometry)) AS total_ae_area FROM floodplain WHERE STATEFP='12' AND FLD_ZONE='AE' AND ST_IsValid(geometry);
  ```
* **Predicted SQL**:
  ```sql
  SELECT SUM(ST_Area(geometry)) FROM floodplain WHERE STATEFP = '12' AND FLD_ZONE = 'AE'
  ```

#### Trực quan hóa Cây AST chuẩn hóa:
```text
CÂY AST GROUND TRUTH:
└─ Select
  └─ Alias
    └─ Sum
      └─ Anonymous
        └─ Column
          └─ Identifier
    └─ Identifier
  └─ From
    └─ Table
      └─ Identifier
  └─ Where
    └─ And
      └─ And
        └─ EQ
          └─ Literal
          └─ Column
            └─ Identifier
        └─ EQ
          └─ Literal
          └─ Column
            └─ Identifier
      └─ Anonymous
        └─ Column
          └─ Identifier

CÂY AST PREDICTED:
└─ Select
  └─ Sum
    └─ Anonymous
      └─ Column
        └─ Identifier
  └─ From
    └─ Table
      └─ Identifier
  └─ Where
    └─ And
      └─ EQ
        └─ Literal
        └─ Column
          └─ Identifier
      └─ EQ
        └─ Literal
        └─ Column
          └─ Identifier
```

#### Phân tích lỗi và khác biệt:
- **Nhận xét**: Khác biệt logic: Cấu trúc AST khác biệt đáng kể (Edit distance = 6.0 trên tổng 42 nút).
- **Khoảng cách hiệu chỉnh cây (Tree Edit Distance)**: 6.0
- **Kích thước cây Ground Truth (Ground Truth AST Size)**: 24 nút
- **Kích thước cây Predicted (Predicted AST Size)**: 18 nút
- **Tổng số nút tối đa (Max Possible Distance)**: 42

---


### Cặp 3: L1_0001 (Mức L1)
* **Câu hỏi**: Which non-null year had the highest total number of NFIP flood claims in Louisiana (STATEFP 22), based on a key-based join between claims and county tables? Return the year.
* **Điểm tương đồng TED**: 0.86
* **Độ chính xác thực thi**: Đúng

#### Truy vấn so sánh:
* **Ground Truth SQL**:
  ```sql
  SELECT STRFTIME('%Y', cl.dateOfLoss) AS year FROM claims cl JOIN county c ON LEFT(cl.GEOID, 5) = c.GEOID WHERE c.STATEFP = '22' AND cl.dateOfLoss IS NOT NULL GROUP BY year ORDER BY COUNT(*) DESC LIMIT 1;
  ```
* **Predicted SQL**:
  ```sql
  SELECT strftime(c.dateOfLoss, '%Y') FROM claims c JOIN county co ON LEFT(c.GEOID, 5) = co.GEOID WHERE c.STATEFP = '22' AND c.dateOfLoss IS NOT NULL GROUP BY strftime(c.dateOfLoss, '%Y') ORDER BY COUNT(c.id) DESC LIMIT 1
  ```

#### Trực quan hóa Cây AST chuẩn hóa:
```text
CÂY AST GROUND TRUTH:
└─ Select
  └─ Alias
    └─ TimeToStr
      └─ Literal
      └─ Column
        └─ Identifier
        └─ Identifier
    └─ Identifier
  └─ Limit
    └─ Literal
  └─ From
    └─ Table
      └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ EQ
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Left
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Literal
  └─ Where
    └─ And
      └─ EQ
        └─ Literal
        └─ Column
          └─ Identifier
          └─ Identifier
      └─ Not
        └─ Is
          └─ Column
            └─ Identifier
            └─ Identifier
          └─ Null
  └─ Group
    └─ Column
      └─ Identifier
  └─ Order
    └─ Ordered
      └─ Count
        └─ Star

CÂY AST PREDICTED:
└─ Select
  └─ TimeToStr
    └─ Column
      └─ Identifier
      └─ Identifier
    └─ Literal
  └─ Limit
    └─ Literal
  └─ From
    └─ Table
      └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ EQ
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Left
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Literal
  └─ Where
    └─ And
      └─ EQ
        └─ Literal
        └─ Column
          └─ Identifier
          └─ Identifier
      └─ Not
        └─ Is
          └─ Column
            └─ Identifier
            └─ Identifier
          └─ Null
  └─ Group
    └─ TimeToStr
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Literal
  └─ Order
    └─ Ordered
      └─ Count
        └─ Column
          └─ Identifier
          └─ Identifier
```

#### Phân tích lỗi và khác biệt:
- **Nhận xét**: Tương đương kết quả: Khác biệt cấu trúc nhẹ (Khoảng cách = 13.0), kết quả chạy khớp.
- **Khoảng cách hiệu chỉnh cây (Tree Edit Distance)**: 13.0
- **Kích thước cây Ground Truth (Ground Truth AST Size)**: 45 nút
- **Kích thước cây Predicted (Predicted AST Size)**: 48 nút
- **Tổng số nút tối đa (Max Possible Distance)**: 93

---


### Cặp 4: L1_0004 (Mức L1)
* **Câu hỏi**: Which 3 Texas counties (STATEFP 48) have the highest non-null percentage of individuals with zero vulnerability components?
* **Điểm tương đồng TED**: 0.92
* **Độ chính xác thực thi**: Sai

#### Truy vấn so sánh:
* **Ground Truth SQL**:
  ```sql
  SELECT c.NAME AS county_name FROM cre cr JOIN county c ON LEFT(cr.GEOID, 5) = c.GEOID WHERE c.STATEFP = '48' AND cr.PRED0_PE IS NOT NULL GROUP BY c.NAME ORDER BY AVG(cr.PRED0_PE) DESC LIMIT 3;
  ```
* **Predicted SQL**:
  ```sql
  SELECT county.NAME, AVG(cre.PRED0_PE) FROM cre JOIN county ON LEFT(cre.GEOID, 5) = county.GEOID WHERE county.STATEFP = '48' AND cre.PRED0_PE IS NOT NULL GROUP BY county.NAME, county.GEOID ORDER BY AVG(cre.PRED0_PE) DESC LIMIT 3
  ```

#### Trực quan hóa Cây AST chuẩn hóa:
```text
CÂY AST GROUND TRUTH:
└─ Select
  └─ Alias
    └─ Column
      └─ Identifier
      └─ Identifier
    └─ Identifier
  └─ Limit
    └─ Literal
  └─ From
    └─ Table
      └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ EQ
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Left
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Literal
  └─ Where
    └─ And
      └─ EQ
        └─ Literal
        └─ Column
          └─ Identifier
          └─ Identifier
      └─ Not
        └─ Is
          └─ Column
            └─ Identifier
            └─ Identifier
          └─ Null
  └─ Group
    └─ Column
      └─ Identifier
      └─ Identifier
  └─ Order
    └─ Ordered
      └─ Avg
        └─ Column
          └─ Identifier
          └─ Identifier

CÂY AST PREDICTED:
└─ Select
  └─ Column
    └─ Identifier
    └─ Identifier
  └─ Avg
    └─ Column
      └─ Identifier
      └─ Identifier
  └─ Limit
    └─ Literal
  └─ From
    └─ Table
      └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ EQ
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Left
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Literal
  └─ Where
    └─ And
      └─ EQ
        └─ Literal
        └─ Column
          └─ Identifier
          └─ Identifier
      └─ Not
        └─ Is
          └─ Column
            └─ Identifier
            └─ Identifier
          └─ Null
  └─ Group
    └─ Column
      └─ Identifier
      └─ Identifier
    └─ Column
      └─ Identifier
      └─ Identifier
  └─ Order
    └─ Ordered
      └─ Avg
        └─ Column
          └─ Identifier
          └─ Identifier
```

#### Phân tích lỗi và khác biệt:
- **Nhận xét**: Khác biệt logic: Cấu trúc AST khác biệt đáng kể (Edit distance = 8.0 trên tổng 97 nút).
- **Khoảng cách hiệu chỉnh cây (Tree Edit Distance)**: 8.0
- **Kích thước cây Ground Truth (Ground Truth AST Size)**: 46 nút
- **Kích thước cây Predicted (Predicted AST Size)**: 51 nút
- **Tổng số nút tối đa (Max Possible Distance)**: 97

---


### Cặp 5: L2_0003 (Mức L2)
* **Câu hỏi**: Which census_tract in Hillsborough County, FL (identified by STATEFP = '12' and COUNTYFP = '057') has the largest total overlap area with all zcta polygons? Return its 11-digit GEOID.
* **Điểm tương đồng TED**: 0.88
* **Độ chính xác thực thi**: Đúng

#### Truy vấn so sánh:
* **Ground Truth SQL**:
  ```sql
  SELECT a.GEOID AS census_tracts_id FROM census_tracts a JOIN zcta b ON ST_Overlaps(a.geometry, b.geometry) WHERE a.STATEFP = '12' AND a.COUNTYFP = '057' AND ST_IsValid(a.geometry) AND ST_IsValid(b.geometry) GROUP BY a.GEOID ORDER BY SUM(ST_Area(ST_Intersection(a.geometry, b.geometry))) DESC LIMIT 1;
  ```
* **Predicted SQL**:
  ```sql
  SELECT ct.GEOID FROM census_tracts ct JOIN zcta z ON ST_Intersects(ct.geometry, z.geometry) WHERE ct.STATEFP = '12' AND ct.COUNTYFP = '057' GROUP BY ct.GEOID ORDER BY SUM(ST_Area(ST_Intersection(ct.geometry, z.geometry))) DESC LIMIT 1
  ```

#### Trực quan hóa Cây AST chuẩn hóa:
```text
CÂY AST GROUND TRUTH:
└─ Select
  └─ Alias
    └─ Column
      └─ Identifier
      └─ Identifier
    └─ Identifier
  └─ Limit
    └─ Literal
  └─ From
    └─ Table
      └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ Anonymous
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ Where
    └─ And
      └─ And
        └─ And
          └─ EQ
            └─ Literal
            └─ Column
              └─ Identifier
              └─ Identifier
          └─ EQ
            └─ Literal
            └─ Column
              └─ Identifier
              └─ Identifier
        └─ Anonymous
          └─ Column
            └─ Identifier
            └─ Identifier
      └─ Anonymous
        └─ Column
          └─ Identifier
          └─ Identifier
  └─ Group
    └─ Column
      └─ Identifier
      └─ Identifier
  └─ Order
    └─ Ordered
      └─ Sum
        └─ Anonymous
          └─ Anonymous
            └─ Column
              └─ Identifier
              └─ Identifier
            └─ Column
              └─ Identifier
              └─ Identifier

CÂY AST PREDICTED:
└─ Select
  └─ Column
    └─ Identifier
    └─ Identifier
  └─ Limit
    └─ Literal
  └─ From
    └─ Table
      └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ Anonymous
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ Where
    └─ And
      └─ EQ
        └─ Literal
        └─ Column
          └─ Identifier
          └─ Identifier
      └─ EQ
        └─ Literal
        └─ Column
          └─ Identifier
          └─ Identifier
  └─ Group
    └─ Column
      └─ Identifier
      └─ Identifier
  └─ Order
    └─ Ordered
      └─ Sum
        └─ Anonymous
          └─ Anonymous
            └─ Column
              └─ Identifier
              └─ Identifier
            └─ Column
              └─ Identifier
              └─ Identifier
```

#### Phân tích lỗi và khác biệt:
- **Nhận xét**: Tương đương kết quả: Khác biệt cấu trúc nhẹ (Khoảng cách = 13.0), kết quả chạy khớp.
- **Khoảng cách hiệu chỉnh cây (Tree Edit Distance)**: 13.0
- **Kích thước cây Ground Truth (Ground Truth AST Size)**: 58 nút
- **Kích thước cây Predicted (Predicted AST Size)**: 46 nút
- **Tổng số nút tối đa (Max Possible Distance)**: 104

---


### Cặp 6: L2_0001 (Mức L2)
* **Câu hỏi**: How many census_tracts in Duval County, FL (identified by GEOID starting with 12031) intersect floodplain polygons?
* **Điểm tương đồng TED**: 0.81
* **Độ chính xác thực thi**: Sai

#### Truy vấn so sánh:
* **Ground Truth SQL**:
  ```sql
  SELECT COUNT(DISTINCT a.GEOID) AS num_census_tracts FROM census_tracts a JOIN floodplain b ON ST_Intersects(a.geometry, b.geometry) WHERE a.GEOID LIKE '12031%' AND ST_IsValid(a.geometry) AND ST_IsValid(b.geometry);
  ```
* **Predicted SQL**:
  ```sql
  SELECT COUNT(DISTINCT ct.GEOID) FROM census_tracts ct JOIN floodplain fp ON ST_Intersects(ct.geometry, fp.geometry) WHERE ct.GEOID LIKE '12031%'
  ```

#### Trực quan hóa Cây AST chuẩn hóa:
```text
CÂY AST GROUND TRUTH:
└─ Select
  └─ Alias
    └─ Count
      └─ Distinct
        └─ Column
          └─ Identifier
          └─ Identifier
    └─ Identifier
  └─ From
    └─ Table
      └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ Anonymous
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ Where
    └─ And
      └─ And
        └─ Like
          └─ Column
            └─ Identifier
            └─ Identifier
          └─ Literal
        └─ Anonymous
          └─ Column
            └─ Identifier
            └─ Identifier
      └─ Anonymous
        └─ Column
          └─ Identifier
          └─ Identifier

CÂY AST PREDICTED:
└─ Select
  └─ Count
    └─ Distinct
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ From
    └─ Table
      └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ Anonymous
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ Where
    └─ Like
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Literal
```

#### Phân tích lỗi và khác biệt:
- **Nhận xét**: Khác biệt logic: Cấu trúc AST khác biệt đáng kể (Edit distance = 12.0 trên tổng 62 nút).
- **Khoảng cách hiệu chỉnh cây (Tree Edit Distance)**: 12.0
- **Kích thước cây Ground Truth (Ground Truth AST Size)**: 37 nút
- **Kích thước cây Predicted (Predicted AST Size)**: 25 nút
- **Tổng số nút tối đa (Max Possible Distance)**: 62

---


### Cặp 7: L3_0013 (Mức L3)
* **Câu hỏi**: How many Louisiana (STATEFP 22) census tracts with NFIP claims have both overall SVI relative vulnerability percentile across all themes above 0.8 and CRE population exceeding 10,000?
* **Điểm tương đồng TED**: 0.75
* **Độ chính xác thực thi**: Đúng

#### Truy vấn so sánh:
* **Ground Truth SQL**:
  ```sql
  SELECT COUNT(DISTINCT cl.GEOID) AS num_tracts FROM (SELECT DISTINCT GEOID, STATEFP FROM claims WHERE STATEFP='22') cl JOIN svi s ON cl.GEOID = s.GEOID JOIN cre cr ON cl.GEOID = cr.GEOID WHERE s.RPL_THEMES > 0.8 AND cr.POPUNI > 10000;
  ```
* **Predicted SQL**:
  ```sql
  SELECT COUNT(DISTINCT c.GEOID) FROM claims c JOIN svi s ON c.GEOID = s.GEOID JOIN cre cr ON c.GEOID = cr.GEOID WHERE c.STATEFP = '22' AND s.RPL_THEMES > 0.8 AND cr.POPUNI > 10000
  ```

#### Trực quan hóa Cây AST chuẩn hóa:
```text
CÂY AST GROUND TRUTH:
└─ Select
  └─ Alias
    └─ Count
      └─ Distinct
        └─ Column
          └─ Identifier
          └─ Identifier
    └─ Identifier
  └─ From
    └─ Subquery
      └─ Select
        └─ Distinct
        └─ Column
          └─ Identifier
        └─ Column
          └─ Identifier
        └─ From
          └─ Table
            └─ Identifier
        └─ Where
          └─ EQ
            └─ Literal
            └─ Column
              └─ Identifier
      └─ TableAlias
        └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ EQ
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ EQ
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ Where
    └─ And
      └─ GT
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Literal
      └─ GT
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Literal

CÂY AST PREDICTED:
└─ Select
  └─ Count
    └─ Distinct
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ From
    └─ Table
      └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ EQ
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ EQ
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ Where
    └─ And
      └─ And
        └─ EQ
          └─ Literal
          └─ Column
            └─ Identifier
            └─ Identifier
        └─ GT
          └─ Column
            └─ Identifier
            └─ Identifier
          └─ Literal
      └─ GT
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Literal
```

#### Phân tích lỗi và khác biệt:
- **Nhận xét**: Tương đương kết quả: Khác biệt cấu trúc nhẹ (Khoảng cách = 26.0), kết quả chạy khớp.
- **Khoảng cách hiệu chỉnh cây (Tree Edit Distance)**: 26.0
- **Kích thước cây Ground Truth (Ground Truth AST Size)**: 58 nút
- **Kích thước cây Predicted (Predicted AST Size)**: 47 nút
- **Tổng số nút tối đa (Max Possible Distance)**: 105

---


### Cặp 8: L3_0002 (Mức L3)
* **Câu hỏi**: In Florida (STATEFP 12), list the 5 census tracts with the highest population-weighted combined score of NRI total expected annual loss for riverine flooding and its average annual flood event frequency among tracts with NFIP claims.
* **Điểm tương đồng TED**: 0.53
* **Độ chính xác thực thi**: Sai

#### Truy vấn so sánh:
* **Ground Truth SQL**:
  ```sql
  SELECT cl.GEOID FROM (SELECT DISTINCT GEOID, STATEFP FROM claims WHERE STATEFP = '12') cl JOIN nri n ON cl.GEOID = n.GEOID JOIN cre cr ON cr.GEOID = cl.GEOID WHERE n.RFLD_EALT IS NOT NULL AND n.RFLD_AFREQ IS NOT NULL AND cr.POPUNI > 0 GROUP BY cl.GEOID ORDER BY SUM((n.RFLD_EALT + n.RFLD_AFREQ) * cr.POPUNI) / SUM(cr.POPUNI) DESC LIMIT 5;
  ```
* **Predicted SQL**:
  ```sql
  SELECT nri.GEOID, (nri.RFLD_EALT + nri.RFLD_AFREQ) * cre.POPUNI AS score FROM nri JOIN census_tracts ON nri.GEOID = census_tracts.GEOID JOIN cre ON nri.GEOID = cre.GEOID WHERE census_tracts.STATEFP = '12' AND nri.GEOID IN (SELECT GEOID FROM claims) ORDER BY score DESC LIMIT 5
  ```

#### Trực quan hóa Cây AST chuẩn hóa:
```text
CÂY AST GROUND TRUTH:
└─ Select
  └─ Column
    └─ Identifier
    └─ Identifier
  └─ Limit
    └─ Literal
  └─ From
    └─ Subquery
      └─ Select
        └─ Distinct
        └─ Column
          └─ Identifier
        └─ Column
          └─ Identifier
        └─ From
          └─ Table
            └─ Identifier
        └─ Where
          └─ EQ
            └─ Literal
            └─ Column
              └─ Identifier
      └─ TableAlias
        └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ EQ
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ EQ
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ Where
    └─ And
      └─ And
        └─ Not
          └─ Is
            └─ Column
              └─ Identifier
              └─ Identifier
            └─ Null
        └─ Not
          └─ Is
            └─ Column
              └─ Identifier
              └─ Identifier
            └─ Null
      └─ GT
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Literal
  └─ Group
    └─ Column
      └─ Identifier
      └─ Identifier
  └─ Order
    └─ Ordered
      └─ Div
        └─ Sum
          └─ Mul
            └─ Paren
              └─ Add
                └─ Column
                  └─ Identifier
                  └─ Identifier
                └─ Column
                  └─ Identifier
                  └─ Identifier
            └─ Column
              └─ Identifier
              └─ Identifier
        └─ Sum
          └─ Column
            └─ Identifier
            └─ Identifier

CÂY AST PREDICTED:
└─ Select
  └─ Column
    └─ Identifier
    └─ Identifier
  └─ Alias
    └─ Mul
      └─ Paren
        └─ Add
          └─ Column
            └─ Identifier
            └─ Identifier
          └─ Column
            └─ Identifier
            └─ Identifier
      └─ Column
        └─ Identifier
        └─ Identifier
    └─ Identifier
  └─ Limit
    └─ Literal
  └─ From
    └─ Table
      └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ EQ
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ EQ
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ Where
    └─ And
      └─ EQ
        └─ Literal
        └─ Column
          └─ Identifier
          └─ Identifier
      └─ In
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Subquery
          └─ Select
            └─ Column
              └─ Identifier
            └─ From
              └─ Table
                └─ Identifier
  └─ Order
    └─ Ordered
      └─ Column
        └─ Identifier
```

#### Phân tích lỗi và khác biệt:
- **Nhận xét**: Khác biệt logic: Cấu trúc AST khác biệt đáng kể (Edit distance = 72.0 trên tổng 153 nút).
- **Khoảng cách hiệu chỉnh cây (Tree Edit Distance)**: 72.0
- **Kích thước cây Ground Truth (Ground Truth AST Size)**: 88 nút
- **Kích thước cây Predicted (Predicted AST Size)**: 65 nút
- **Tổng số nút tối đa (Max Possible Distance)**: 153

---


### Cặp 9: L4_0015 (Mức L4)
* **Câu hỏi**: In Louisiana (STATEFP 22), what is the maximum Insurance payout amount (in USD) for structural building damage (amountPaidOnContentsClaim) across all census tracts that contain at least one hospital?
* **Điểm tương đồng TED**: 0.55
* **Độ chính xác thực thi**: Đúng

#### Truy vấn so sánh:
* **Ground Truth SQL**:
  ```sql
  SELECT MAX(CAST(cl.amountPaidOnContentsClaim AS DOUBLE)) AS max_building_claim FROM hospitals h JOIN census_tracts t ON ST_Contains(t.geometry, ST_Point(h.LON, h.LAT)) JOIN claims cl ON cl.GEOID = t.GEOID WHERE h.STATEFP='22' AND ST_IsValid(t.geometry) AND cl.amountPaidOnContentsClaim IS NOT NULL;
  ```
* **Predicted SQL**:
  ```sql
  SELECT MAX(claims.amountPaidOnContentsClaim) FROM claims JOIN hospitals ON LEFT(claims.GEOID, 5) = hospitals.COUNTYFIPS AND claims.STATEFP = hospitals.STATEFP WHERE claims.STATEFP = '22'
  ```

#### Trực quan hóa Cây AST chuẩn hóa:
```text
CÂY AST GROUND TRUTH:
└─ Select
  └─ Alias
    └─ Max
      └─ Cast
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ DataType
    └─ Identifier
  └─ From
    └─ Table
      └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ Anonymous
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ StPoint
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Column
          └─ Identifier
          └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ EQ
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ Where
    └─ And
      └─ And
        └─ EQ
          └─ Literal
          └─ Column
            └─ Identifier
            └─ Identifier
        └─ Anonymous
          └─ Column
            └─ Identifier
            └─ Identifier
      └─ Not
        └─ Is
          └─ Column
            └─ Identifier
            └─ Identifier
          └─ Null

CÂY AST PREDICTED:
└─ Select
  └─ Max
    └─ Column
      └─ Identifier
      └─ Identifier
  └─ From
    └─ Table
      └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ And
      └─ EQ
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Left
          └─ Column
            └─ Identifier
            └─ Identifier
          └─ Literal
      └─ EQ
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Column
          └─ Identifier
          └─ Identifier
  └─ Where
    └─ EQ
      └─ Literal
      └─ Column
        └─ Identifier
        └─ Identifier
```

#### Phân tích lỗi và khác biệt:
- **Nhận xét**: Tương đương kết quả: Khác biệt cấu trúc nhẹ (Khoảng cách = 40.0), kết quả chạy khớp.
- **Khoảng cách hiệu chỉnh cây (Tree Edit Distance)**: 40.0
- **Kích thước cây Ground Truth (Ground Truth AST Size)**: 54 nút
- **Kích thước cây Predicted (Predicted AST Size)**: 34 nút
- **Tổng số nút tối đa (Max Possible Distance)**: 88

---


### Cặp 10: L4_0005 (Mức L4)
* **Câu hỏi**: Which 5 Texas (STATEFP 12) counties have the highest number of hospitals located inside floodplain zones? Return their names.
* **Điểm tương đồng TED**: 0.82
* **Độ chính xác thực thi**: Sai

#### Truy vấn so sánh:
* **Ground Truth SQL**:
  ```sql
  SELECT c.NAME AS county_name FROM hospitals h JOIN county c ON LEFT(h.COUNTYFIPS,5)=c.GEOID JOIN floodplain f ON ST_Contains(f.geometry, ST_Point(h.LON, h.LAT)) WHERE c.STATEFP='12' AND ST_IsValid(f.geometry) AND ST_IsValid(c.geometry) GROUP BY c.NAME ORDER BY COUNT(*) DESC LIMIT 5;
  ```
* **Predicted SQL**:
  ```sql
  SELECT c.NAME FROM hospitals h JOIN county c ON h.COUNTYFIPS = c.GEOID JOIN floodplain f ON ST_Intersects(f.geometry, ST_Point(h.LON, h.LAT)) WHERE c.STATEFP = '48' GROUP BY c.NAME ORDER BY count(h.HOSPITAL_ID) DESC LIMIT 5
  ```

#### Trực quan hóa Cây AST chuẩn hóa:
```text
CÂY AST GROUND TRUTH:
└─ Select
  └─ Alias
    └─ Column
      └─ Identifier
      └─ Identifier
    └─ Identifier
  └─ Limit
    └─ Literal
  └─ From
    └─ Table
      └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ EQ
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Left
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Literal
  └─ Join
    └─ Table
      └─ Identifier
    └─ Anonymous
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ StPoint
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Column
          └─ Identifier
          └─ Identifier
  └─ Where
    └─ And
      └─ And
        └─ EQ
          └─ Literal
          └─ Column
            └─ Identifier
            └─ Identifier
        └─ Anonymous
          └─ Column
            └─ Identifier
            └─ Identifier
      └─ Anonymous
        └─ Column
          └─ Identifier
          └─ Identifier
  └─ Group
    └─ Column
      └─ Identifier
      └─ Identifier
  └─ Order
    └─ Ordered
      └─ Count
        └─ Star

CÂY AST PREDICTED:
└─ Select
  └─ Column
    └─ Identifier
    └─ Identifier
  └─ Limit
    └─ Literal
  └─ From
    └─ Table
      └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ EQ
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ Anonymous
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ StPoint
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Column
          └─ Identifier
          └─ Identifier
  └─ Where
    └─ EQ
      └─ Literal
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ Group
    └─ Column
      └─ Identifier
      └─ Identifier
  └─ Order
    └─ Ordered
      └─ Count
        └─ Column
          └─ Identifier
          └─ Identifier
```

#### Phân tích lỗi và khác biệt:
- **Nhận xét**: Khác biệt logic: Cấu trúc AST khác biệt đáng kể (Edit distance = 20.0 trên tổng 110 nút).
- **Khoảng cách hiệu chỉnh cây (Tree Edit Distance)**: 20.0
- **Kích thước cây Ground Truth (Ground Truth AST Size)**: 61 nút
- **Kích thước cây Predicted (Predicted AST Size)**: 49 nút
- **Tổng số nút tối đa (Max Possible Distance)**: 110

---


### Cặp 11: L5_0001 (Mức L5)
* **Câu hỏi**: How many hospitals are located within both FEMA floodplain polygons and census tract boundaries in Harris County, Texas (identified by the leftmost 5 digits of GEOID 48201 in the census_tract table)?
* **Điểm tương đồng TED**: 0.87
* **Độ chính xác thực thi**: Sai

#### Truy vấn so sánh:
* **Ground Truth SQL**:
  ```sql
  SELECT COUNT(DISTINCT h.UNIQUE_ID) AS num_hospitals FROM hospitals h JOIN floodplain f ON ST_Within(ST_Point(h.LON, h.LAT), f.geometry) JOIN census_tracts t ON ST_Within(ST_Point(h.LON, h.LAT), t.geometry) WHERE LEFT(t.GEOID,5)='48201' AND ST_IsValid(f.geometry) AND ST_IsValid(t.geometry);
  ```
* **Predicted SQL**:
  ```sql
  SELECT COUNT(DISTINCT h.HOSPITAL_ID) FROM hospitals h JOIN floodplain f ON ST_Contains(f.geometry, ST_Point(h.LON, h.LAT)) JOIN census_tracts ct ON ST_Contains(ct.geometry, ST_Point(h.LON, h.LAT)) WHERE LEFT(ct.GEOID, 5) = '48201'
  ```

#### Trực quan hóa Cây AST chuẩn hóa:
```text
CÂY AST GROUND TRUTH:
└─ Select
  └─ Alias
    └─ Count
      └─ Distinct
        └─ Column
          └─ Identifier
          └─ Identifier
    └─ Identifier
  └─ From
    └─ Table
      └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ Anonymous
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ StPoint
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Column
          └─ Identifier
          └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ Anonymous
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ StPoint
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Column
          └─ Identifier
          └─ Identifier
  └─ Where
    └─ And
      └─ And
        └─ EQ
          └─ Literal
          └─ Left
            └─ Column
              └─ Identifier
              └─ Identifier
            └─ Literal
        └─ Anonymous
          └─ Column
            └─ Identifier
            └─ Identifier
      └─ Anonymous
        └─ Column
          └─ Identifier
          └─ Identifier

CÂY AST PREDICTED:
└─ Select
  └─ Count
    └─ Distinct
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ From
    └─ Table
      └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ Anonymous
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ StPoint
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Column
          └─ Identifier
          └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ Anonymous
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ StPoint
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Column
          └─ Identifier
          └─ Identifier
  └─ Where
    └─ EQ
      └─ Literal
      └─ Left
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Literal
```

#### Phân tích lỗi và khác biệt:
- **Nhận xét**: Khác biệt logic: Cấu trúc AST khác biệt đáng kể (Edit distance = 13.0 trên tổng 102 nút).
- **Khoảng cách hiệu chỉnh cây (Tree Edit Distance)**: 13.0
- **Kích thước cây Ground Truth (Ground Truth AST Size)**: 57 nút
- **Kích thước cây Predicted (Predicted AST Size)**: 45 nút
- **Tổng số nút tối đa (Max Possible Distance)**: 102

---


### Cặp 12: L4_0007 (Mức L4)
* **Câu hỏi**: In Texas (STATEFP 48), how many census tracts with Percentage of individuals with three plus components of social vulnerability higher than 40 intersect FEMA floodplain polygons?
* **Điểm tương đồng TED**: 0.70
* **Độ chính xác thực thi**: Sai

#### Truy vấn so sánh:
* **Ground Truth SQL**:
  ```sql
  SELECT COUNT(*) AS num_high_vuln_tracts FROM cre r JOIN census_tracts t ON r.GEOID=t.GEOID JOIN floodplain f ON ST_Intersects(f.geometry,t.geometry) WHERE LEFT(t.GEOID,2)='48' AND r.PRED3_PE>40 AND r.PRED3_PE BETWEEN 0 AND 100 AND ST_IsValid(f.geometry) AND ST_IsValid(t.geometry);
  ```
* **Predicted SQL**:
  ```sql
  SELECT COUNT(DISTINCT ct.GEOID) FROM census_tracts ct JOIN cre c ON ct.GEOID = c.GEOID JOIN floodplain fp ON ST_Intersects(ct.geometry, fp.geometry) WHERE ct.STATEFP = '48' AND c.PRED3_PE > 40
  ```

#### Trực quan hóa Cây AST chuẩn hóa:
```text
CÂY AST GROUND TRUTH:
└─ Select
  └─ Alias
    └─ Count
      └─ Star
    └─ Identifier
  └─ From
    └─ Table
      └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ EQ
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ Anonymous
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ Where
    └─ And
      └─ And
        └─ And
          └─ And
            └─ EQ
              └─ Literal
              └─ Left
                └─ Column
                  └─ Identifier
                  └─ Identifier
                └─ Literal
            └─ GT
              └─ Column
                └─ Identifier
                └─ Identifier
              └─ Literal
          └─ Between
            └─ Column
              └─ Identifier
              └─ Identifier
            └─ Literal
            └─ Literal
        └─ Anonymous
          └─ Column
            └─ Identifier
            └─ Identifier
      └─ Anonymous
        └─ Column
          └─ Identifier
          └─ Identifier

CÂY AST PREDICTED:
└─ Select
  └─ Count
    └─ Distinct
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ From
    └─ Table
      └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ EQ
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ Join
    └─ Table
      └─ Identifier
    └─ Anonymous
      └─ Column
        └─ Identifier
        └─ Identifier
      └─ Column
        └─ Identifier
        └─ Identifier
  └─ Where
    └─ And
      └─ EQ
        └─ Literal
        └─ Column
          └─ Identifier
          └─ Identifier
      └─ GT
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Literal
```

#### Phân tích lỗi và khác biệt:
- **Nhận xét**: Khác biệt logic: Cấu trúc AST khác biệt đáng kể (Edit distance = 30.0 trên tổng 100 nút).
- **Khoảng cách hiệu chỉnh cây (Tree Edit Distance)**: 30.0
- **Kích thước cây Ground Truth (Ground Truth AST Size)**: 59 nút
- **Kích thước cây Predicted (Predicted AST Size)**: 41 nút
- **Tổng số nút tối đa (Max Possible Distance)**: 100

---

