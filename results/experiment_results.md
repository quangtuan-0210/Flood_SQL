# BÁO CÁO THỰC NGHIỆM ĐÁNH GIÁ TRUY VẤN TEXT-TO-SPATIAL SQL

Báo cáo này được tự động tạo lập từ kết quả chạy đánh giá mô hình `vllm/Qwen3.6-35B-A3B-GGUF` kết hợp với API embedding `mirai-embedding` trên tập dữ liệu FloodSQL-Bench.

## 1. Bảng So sánh Hiệu năng Theo Cấp độ (L0 - L6)

Dưới đây là bảng thống kê điểm số trung bình của mô hình theo từng mức từ L0 (Dễ nhất) đến L5 (Khó nhất):

| Mức độ | Số lượng câu | Độ chính xác thực thi (Execution Acc) | Điểm tương đồng AST (AST Similarity) | Điểm tương đồng văn bản SQL (Text Similarity) |
| :--- | :---: | :---: | :---: | :---: |
| L0 | 50 | 78.00% | 79.32% | 52.85% |
| L1 | 100 | 58.00% | 64.92% | 41.07% |
| L2 | 150 | 40.67% | 57.28% | 32.58% |
| L3 | 31 | 19.35% | 58.20% | 32.63% |
| L4 | 30 | 6.67% | 46.35% | 28.23% |
| L5 | 43 | 0.00% | 55.54% | 35.36% |
| **Trung bình cộng** | **404** | **41.09%** | **60.97%** | **37.17%** |

* **Nhận xét chung**:
  - **Độ chính xác thực thi (Execution Accuracy)** phản ánh tỷ lệ câu chạy ra kết quả khớp 100% trên DuckDB.
  - **Điểm tương đồng AST (AST Similarity)** đo lường độ chính xác cấu trúc ngữ nghĩa (bỏ qua alias và thứ tự điều kiện), phản ánh sát nhất tư duy viết code của AI.
  - **Điểm tương đồng văn bản (Text Similarity)** dựa trên từ vựng thuần túy, thường có xu hướng thấp hơn điểm AST do sự khác biệt nhỏ về cách viết thường/hoa, khoảng trắng hoặc alias không làm ảnh hưởng ngữ nghĩa nhưng làm lệch chữ.

## 2. Bảng So sánh 12 Cặp Spatial SQL Tiêu Biểu (L0 - L5)

Dưới đây là bảng thống kê 12 cặp truy vấn đại diện được trích xuất từ thực nghiệm để đánh giá chi tiết:

| Cặp số | Mã câu hỏi | Mức độ | Điểm tương đồng AST | Kết quả Thực thi | Nhận xét chi tiết nguyên nhân khác biệt |
| :---: | :--- | :---: | :---: | :---: | :--- |
| 1 | L0_0001 | L0 | 0.45 | Đúng | Khác biệt cú pháp: Khác alias hoặc thứ tự bảng/mệnh đề điều kiện nhưng tương đương ngữ nghĩa. |
| 2 | L0_0002 | L0 | 0.80 | Sai | Thiếu bộ lọc: Thiếu các điều kiện lọc WHERE cần thiết. |
| 3 | L1_0001 | L1 | 0.60 | Đúng | Khác biệt cú pháp: Khác alias hoặc thứ tự bảng/mệnh đề điều kiện nhưng tương đương ngữ nghĩa. |
| 4 | L1_0004 | L1 | 0.90 | Sai | Sai logic: Khác biệt ở cấu trúc SELECT hoặc cách lập điều kiện. |
| 5 | L2_0003 | L2 | 0.62 | Đúng | Khác biệt cú pháp: Khác alias hoặc thứ tự bảng/mệnh đề điều kiện nhưng tương đương ngữ nghĩa. |
| 6 | L2_0001 | L2 | 0.70 | Sai | Thiếu bộ lọc: Thiếu các điều kiện lọc WHERE cần thiết. |
| 7 | L3_0013 | L3 | 0.63 | Đúng | Khác biệt cú pháp: Khác alias hoặc thứ tự bảng/mệnh đề điều kiện nhưng tương đương ngữ nghĩa. |
| 8 | L3_0002 | L3 | 0.38 | Sai | Thiếu kết nối: Câu lệnh thiếu điều kiện JOIN không gian hoặc khóa ngoại. |
| 9 | L4_0015 | L4 | 0.17 | Đúng | Khác biệt cú pháp: Khác alias hoặc thứ tự bảng/mệnh đề điều kiện nhưng tương đương ngữ nghĩa. |
| 10 | L4_0001 | L4 | 0.63 | Sai | Thiếu bộ lọc: Thiếu các điều kiện lọc WHERE cần thiết. |
| 11 | L5_0001 | L5 | 0.60 | Sai | Thiếu bộ lọc: Thiếu các điều kiện lọc WHERE cần thiết. |
| 12 | L4_0002 | L4 | 0.38 | Sai | Thiếu kết nối: Câu lệnh thiếu điều kiện JOIN không gian hoặc khóa ngoại. |

## 3. Phân tích Chi tiết 12 Cặp Truy vấn (AST & Trực quan hóa)


### Cặp 1: L0_0001 (Mức L0)
* **Câu hỏi**: In Harris County, Texas (identified by GEOID starting with 48201), how many NFIP claims have a dateOfLoss on or after 2010-01-01?
* **Điểm tương đồng AST**: 0.45
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
- **Nhận xét**: Khác biệt cú pháp: Khác alias hoặc thứ tự bảng/mệnh đề điều kiện nhưng tương đương ngữ nghĩa.
- **Thành phần khớp**: ["claims"]
- **Thành phần thiếu (Ground Truth có nhưng Predicted thiếu)**: ["GEOID LIKE '48201%'", "DATEOFLOSS >= CAST('2010-01-01' AS DATE)"]
- **Thành phần thừa (Predicted tự viết thêm)**: ["CLAIMS.DATEOFLOSS >= '2010-01-01'", "'48201' = COUNTY.GEOID", "COUNTY.GEOID = LEFT(CLAIMS.GEOID, 5)"]

---


### Cặp 2: L0_0002 (Mức L0)
* **Câu hỏi**: What is the total area of valid FEMA Flood Hazard Zone polygons in Florida (STATEFP = '12') labeled as AE?
* **Điểm tương đồng AST**: 0.80
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
- **Nhận xét**: Thiếu bộ lọc: Thiếu các điều kiện lọc WHERE cần thiết.
- **Thành phần khớp**: ["floodplain"]
- **Thành phần thiếu (Ground Truth có nhưng Predicted thiếu)**: ["ST_ISVALID(GEOMETRY)"]
- **Thành phần thừa (Predicted tự viết thêm)**: []

---


### Cặp 3: L1_0001 (Mức L1)
* **Câu hỏi**: Which non-null year had the highest total number of NFIP flood claims in Louisiana (STATEFP 22), based on a key-based join between claims and county tables? Return the year.
* **Điểm tương đồng AST**: 0.60
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
- **Nhận xét**: Khác biệt cú pháp: Khác alias hoặc thứ tự bảng/mệnh đề điều kiện nhưng tương đương ngữ nghĩa.
- **Thành phần khớp**: ["claims", "county"]
- **Thành phần thiếu (Ground Truth có nhưng Predicted thiếu)**: ["'22' = COUNTY.STATEFP"]
- **Thành phần thừa (Predicted tự viết thêm)**: ["'22' = CLAIMS.STATEFP"]

---


### Cặp 4: L1_0004 (Mức L1)
* **Câu hỏi**: Which 3 Texas counties (STATEFP 48) have the highest non-null percentage of individuals with zero vulnerability components?
* **Điểm tương đồng AST**: 0.90
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
- **Nhận xét**: Sai logic: Khác biệt ở cấu trúc SELECT hoặc cách lập điều kiện.
- **Thành phần khớp**: ["cre", "county"]
- **Thành phần thiếu (Ground Truth có nhưng Predicted thiếu)**: []
- **Thành phần thừa (Predicted tự viết thêm)**: []

---


### Cặp 5: L2_0003 (Mức L2)
* **Câu hỏi**: Which census_tract in Hillsborough County, FL (identified by STATEFP = '12' and COUNTYFP = '057') has the largest total overlap area with all zcta polygons? Return its 11-digit GEOID.
* **Điểm tương đồng AST**: 0.62
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
- **Nhận xét**: Khác biệt cú pháp: Khác alias hoặc thứ tự bảng/mệnh đề điều kiện nhưng tương đương ngữ nghĩa.
- **Thành phần khớp**: ["zcta", "census_tracts"]
- **Thành phần thiếu (Ground Truth có nhưng Predicted thiếu)**: ["ST_ISVALID(ZCTA.GEOMETRY)", "ST_ISVALID(CENSUS_TRACTS.GEOMETRY)", "ST_OVERLAPS(CENSUS_TRACTS.GEOMETRY, ZCTA.GEOMETRY)"]
- **Thành phần thừa (Predicted tự viết thêm)**: ["ST_INTERSECTS(CENSUS_TRACTS.GEOMETRY, ZCTA.GEOMETRY)"]

---


### Cặp 6: L2_0001 (Mức L2)
* **Câu hỏi**: How many census_tracts in Duval County, FL (identified by GEOID starting with 12031) intersect floodplain polygons?
* **Điểm tương đồng AST**: 0.70
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
- **Nhận xét**: Thiếu bộ lọc: Thiếu các điều kiện lọc WHERE cần thiết.
- **Thành phần khớp**: ["census_tracts", "floodplain"]
- **Thành phần thiếu (Ground Truth có nhưng Predicted thiếu)**: ["ST_ISVALID(CENSUS_TRACTS.GEOMETRY)", "ST_ISVALID(FLOODPLAIN.GEOMETRY)"]
- **Thành phần thừa (Predicted tự viết thêm)**: []

---


### Cặp 7: L3_0013 (Mức L3)
* **Câu hỏi**: How many Louisiana (STATEFP 22) census tracts with NFIP claims have both overall SVI relative vulnerability percentile across all themes above 0.8 and CRE population exceeding 10,000?
* **Điểm tương đồng AST**: 0.63
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
- **Nhận xét**: Khác biệt cú pháp: Khác alias hoặc thứ tự bảng/mệnh đề điều kiện nhưng tương đương ngữ nghĩa.
- **Thành phần khớp**: ["svi", "cre", "claims"]
- **Thành phần thiếu (Ground Truth có nhưng Predicted thiếu)**: ["CL.GEOID = CRE.GEOID", "CL.GEOID = SVI.GEOID"]
- **Thành phần thừa (Predicted tự viết thêm)**: ["'22' = CLAIMS.STATEFP", "CLAIMS.GEOID = CRE.GEOID", "CLAIMS.GEOID = SVI.GEOID"]

---


### Cặp 8: L3_0002 (Mức L3)
* **Câu hỏi**: In Florida (STATEFP 12), list the 5 census tracts with the highest population-weighted combined score of NRI total expected annual loss for riverine flooding and its average annual flood event frequency among tracts with NFIP claims.
* **Điểm tương đồng AST**: 0.38
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
- **Nhận xét**: Thiếu kết nối: Câu lệnh thiếu điều kiện JOIN không gian hoặc khóa ngoại.
- **Thành phần khớp**: ["claims", "cre", "nri"]
- **Thành phần thiếu (Ground Truth có nhưng Predicted thiếu)**: ["NOT NRI.RFLD_AFREQ IS NULL", "CRE.POPUNI > 0", "NOT NRI.RFLD_EALT IS NULL", "CL.GEOID = CRE.GEOID", "CL.GEOID = NRI.GEOID"]
- **Thành phần thừa (Predicted tự viết thêm)**: ["'12' = CENSUS_TRACTS.STATEFP", "NRI.GEOID IN (SELECT GEOID FROM CLAIMS)", "CRE.GEOID = NRI.GEOID", "CENSUS_TRACTS.GEOID = NRI.GEOID"]

---


### Cặp 9: L4_0015 (Mức L4)
* **Câu hỏi**: In Louisiana (STATEFP 22), what is the maximum Insurance payout amount (in USD) for structural building damage (amountPaidOnContentsClaim) across all census tracts that contain at least one hospital?
* **Điểm tương đồng AST**: 0.17
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
- **Nhận xét**: Khác biệt cú pháp: Khác alias hoặc thứ tự bảng/mệnh đề điều kiện nhưng tương đương ngữ nghĩa.
- **Thành phần khớp**: ["claims", "hospitals"]
- **Thành phần thiếu (Ground Truth có nhưng Predicted thiếu)**: ["'22' = HOSPITALS.STATEFP", "NOT CLAIMS.AMOUNTPAIDONCONTENTSCLAIM IS NULL", "ST_ISVALID(CENSUS_TRACTS.GEOMETRY)", "CENSUS_TRACTS.GEOID = CLAIMS.GEOID", "ST_CONTAINS(CENSUS_TRACTS.GEOMETRY, ST_POINT(HOSPITALS.LON, HOSPITALS.LAT))"]
- **Thành phần thừa (Predicted tự viết thêm)**: ["'22' = CLAIMS.STATEFP", "CLAIMS.STATEFP = HOSPITALS.STATEFP", "HOSPITALS.COUNTYFIPS = LEFT(CLAIMS.GEOID, 5)"]

---


### Cặp 10: L4_0001 (Mức L4)
* **Câu hỏi**: What is the average Relative percentile for Theme 1 (Socioeconomic) for census tracts in Texas (STATEFP 48) that intersect a FEMA floodplain polygon?
* **Điểm tương đồng AST**: 0.63
* **Độ chính xác thực thi**: Sai

#### Truy vấn so sánh:
* **Ground Truth SQL**:
  ```sql
  SELECT AVG(v.RPL_THEME1) AS avg_theme1_rank FROM svi v JOIN census_tracts t ON v.GEOID = t.GEOID JOIN floodplain f ON ST_Intersects(t.geometry, f.geometry) WHERE t.STATEFP='48' AND ST_IsValid(t.geometry) AND ST_IsValid(f.geometry) AND v.RPL_THEME1 IS NOT NULL AND v.RPL_THEME1 BETWEEN 0 AND 100;
  ```
* **Predicted SQL**:
  ```sql
  SELECT AVG(svi.RPL_THEME1) FROM svi JOIN census_tracts ON svi.GEOID = census_tracts.GEOID JOIN floodplain ON ST_Intersects(census_tracts.geometry, floodplain.geometry) WHERE census_tracts.STATEFP = '48'
  ```

#### Trực quan hóa Cây AST chuẩn hóa:
```text
CÂY AST GROUND TRUTH:
└─ Select
  └─ Alias
    └─ Avg
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
        └─ Not
          └─ Is
            └─ Column
              └─ Identifier
              └─ Identifier
            └─ Null
      └─ Between
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Literal
        └─ Literal

CÂY AST PREDICTED:
└─ Select
  └─ Avg
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
    └─ EQ
      └─ Literal
      └─ Column
        └─ Identifier
        └─ Identifier
```

#### Phân tích lỗi và khác biệt:
- **Nhận xét**: Thiếu bộ lọc: Thiếu các điều kiện lọc WHERE cần thiết.
- **Thành phần khớp**: ["svi", "census_tracts", "floodplain"]
- **Thành phần thiếu (Ground Truth có nhưng Predicted thiếu)**: ["SVI.RPL_THEME1 BETWEEN 0 AND 100", "ST_ISVALID(CENSUS_TRACTS.GEOMETRY)", "NOT SVI.RPL_THEME1 IS NULL", "ST_ISVALID(FLOODPLAIN.GEOMETRY)"]
- **Thành phần thừa (Predicted tự viết thêm)**: []

---


### Cặp 11: L5_0001 (Mức L5)
* **Câu hỏi**: How many hospitals are located within both FEMA floodplain polygons and census tract boundaries in Harris County, Texas (identified by the leftmost 5 digits of GEOID 48201 in the census_tract table)?
* **Điểm tương đồng AST**: 0.60
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
- **Nhận xét**: Thiếu bộ lọc: Thiếu các điều kiện lọc WHERE cần thiết.
- **Thành phần khớp**: ["hospitals", "census_tracts", "floodplain"]
- **Thành phần thiếu (Ground Truth có nhưng Predicted thiếu)**: ["ST_ISVALID(CENSUS_TRACTS.GEOMETRY)", "ST_ISVALID(FLOODPLAIN.GEOMETRY)"]
- **Thành phần thừa (Predicted tự viết thêm)**: []

---


### Cặp 12: L4_0002 (Mức L4)
* **Câu hỏi**: Which 5 Florida (STATEFP 12) counties have the highest number of hospitals located inside floodplain zones? Return their names.
* **Điểm tương đồng AST**: 0.38
* **Độ chính xác thực thi**: Sai

#### Truy vấn so sánh:
* **Ground Truth SQL**:
  ```sql
  SELECT c.NAME AS county_name FROM hospitals h JOIN county c ON LEFT(h.COUNTYFIPS,5)=c.GEOID JOIN floodplain f ON ST_Contains(f.geometry, ST_Point(h.LON, h.LAT)) WHERE c.STATEFP='12' AND ST_IsValid(f.geometry) AND ST_IsValid(c.geometry) GROUP BY c.NAME ORDER BY COUNT(*) DESC LIMIT 5;
  ```
* **Predicted SQL**:
  ```sql
  SELECT county.NAME FROM hospitals JOIN county ON hospitals.COUNTYFIPS = county.GEOID JOIN floodplain ON ST_Intersects(floodplain.geometry, ST_Point(hospitals.LON, hospitals.LAT)) WHERE county.STATEFP = '12' GROUP BY county.NAME ORDER BY COUNT(DISTINCT hospitals.HOSPITAL_ID) DESC LIMIT 5
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
        └─ Distinct
          └─ Column
            └─ Identifier
            └─ Identifier
```

#### Phân tích lỗi và khác biệt:
- **Nhận xét**: Thiếu kết nối: Câu lệnh thiếu điều kiện JOIN không gian hoặc khóa ngoại.
- **Thành phần khớp**: ["hospitals", "county", "floodplain"]
- **Thành phần thiếu (Ground Truth có nhưng Predicted thiếu)**: ["ST_ISVALID(COUNTY.GEOMETRY)", "ST_ISVALID(FLOODPLAIN.GEOMETRY)", "ST_CONTAINS(FLOODPLAIN.GEOMETRY, ST_POINT(HOSPITALS.LON, HOSPITALS.LAT))", "COUNTY.GEOID = LEFT(HOSPITALS.COUNTYFIPS, 5)"]
- **Thành phần thừa (Predicted tự viết thêm)**: ["ST_INTERSECTS(FLOODPLAIN.GEOMETRY, ST_POINT(HOSPITALS.LON, HOSPITALS.LAT))", "COUNTY.GEOID = HOSPITALS.COUNTYFIPS"]

---

