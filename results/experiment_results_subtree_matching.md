# BÁO CÁO THỰC NGHIỆM ĐÁNH GIÁ TRUY VẤN TEXT-TO-SPATIAL SQL (SUBTREE MATCHING)

Báo cáo này được tự động tạo lập từ kết quả chạy đánh giá mô hình `vllm/Qwen3.6-35B-A3B-GGUF` kết hợp với API embedding `mirai-embedding` trên tập dữ liệu FloodSQL-Bench.

## 1. Bảng So sánh Hiệu năng Theo Cấp độ (L0 - L5)

Dưới đây là bảng thống kê điểm số trung bình của mô hình theo từng mức từ L0 (Dễ nhất) đến L5 (Khó nhất):

| Mức độ | Số lượng câu | Độ chính xác thực thi (Execution Acc) | Điểm tương đồng Subtree Matching (Subtree Matching Similarity) | Điểm tương đồng văn bản SQL (Text Similarity) |
| :--- | :---: | :---: | :---: | :---: |
| L0 | 50 | 78.00% | 51.62% | 53.68% |
| L1 | 100 | 59.00% | 44.11% | 39.69% |
| L2 | 150 | 40.67% | 54.19% | 32.63% |
| L3 | 50 | 12.00% | 34.75% | 27.68% |
| L4 | 43 | 2.33% | 28.34% | 19.01% |
| L5 | 50 | 0.00% | 14.83% | 8.72% |
| **Trung bình cộng** | **443** | **37.47%** | **42.48%** | **32.02%** |

* **Nhận xét chung**:
  - **Độ chính xác thực thi (Execution Accuracy)** phản ánh tỷ lệ câu chạy ra kết quả khớp 100% trên DuckDB.
  - **Điểm tương đồng Subtree Matching (Subtree Matching Similarity)** đo lường tỷ lệ các cây con trùng khớp chính xác (bao gồm cả cấu trúc và giá trị nhãn) giữa hai cây cú pháp AST đã chuẩn hóa.
  
  **Thuật toán Khớp cây con (Subtree Matching):**
  Thuật toán phân rã cây AST của truy vấn Ground Truth ($T_1$) và Predicted ($T_2$) thành các tập đa hợp (multi-sets) chứa tất cả các cây con có thể. Mỗi nút trong AST đóng vai trò là gốc của một cây con. Các cây con này sau đó được mã hóa (tuần tự hóa) thành dạng canonical string duy nhất để so sánh trực tiếp.
  
  **Công thức chuẩn hóa điểm tương đồng:**
  Sử dụng hệ số tương đồng Jaccard trên hai tập đa hợp các cây con $S_1$ và $S_2$:
  $$S = \frac{|S_1 \cap S_2|}{|S_1 \cup S_2|} = \frac{|S_1 \cap S_2|}{|S_1| + |S_2| - |S_1 \cap S_2|}$$
  *Trong đó:*
  - $|S_1 \cap S_2|$ là số lượng cây con trùng khớp hoàn hảo (giao của hai tập đa hợp).
  - $|S_1| + |S_2| - |S_1 \cap S_2|$ là kích thước hợp của hai tập đa hợp cây con.
  - Nếu cả hai cây đều rỗng ($|S_1| + |S_2| = 0$), $S = 1.0$.
  - **Điểm tương đồng văn bản (Text Similarity)** dựa trên từ vựng thuần túy, thường có xu hướng thấp hơn điểm AST do sự khác biệt nhỏ về cách viết thường/hoa, khoảng trắng hoặc alias không làm ảnh hưởng ngữ nghĩa nhưng làm lệch chữ.

## 2. Bảng So sánh 12 Cặp Spatial SQL Tiêu Biểu (L0 - L5)

Dưới đây là bảng thống kê 12 cặp truy vấn đại diện được trích xuất từ thực nghiệm để đánh giá chi tiết:

| Cặp số | Mã câu hỏi | Mức độ | Điểm tương đồng Subtree | Kết quả Thực thi | Nhận xét chi tiết nguyên nhân khác biệt |
| :---: | :--- | :---: | :---: | :---: | :--- |
| 1 | L0_0001 | L0 | 0.13 | Đúng | Tương đương kết quả: Khớp 6 cây con (độ tương đồng 13.0%), kết quả chạy khớp. |
| 2 | L0_0002 | L0 | 0.62 | Sai | Sai logic: Khác biệt cấu trúc (Khớp 16 trên tổng số 26 cây con). |
| 3 | L1_0001 | L1 | 0.45 | Đúng | Tương đương kết quả: Khớp 29 cây con (độ tương đồng 45.3%), kết quả chạy khớp. |
| 4 | L1_0004 | L1 | 0.76 | Sai | Sai logic: Khác biệt cấu trúc (Khớp 42 trên tổng số 55 cây con). |
| 5 | L2_0003 | L2 | 0.68 | Đúng | Tương đương kết quả: Khớp 42 cây con (độ tương đồng 67.7%), kết quả chạy khớp. |
| 6 | L2_0001 | L2 | 0.59 | Sai | Sai logic: Khác biệt cấu trúc (Khớp 23 trên tổng số 39 cây con). |
| 7 | L3_0013 | L3 | 0.36 | Đúng | Tương đương kết quả: Khớp 28 cây con (độ tương đồng 36.4%), kết quả chạy khớp. |
| 8 | L3_0002 | L3 | 0.32 | Sai | Sai logic: Khác biệt cấu trúc (Khớp 37 trên tổng số 116 cây con). |
| 9 | L4_0032 | L4 | 0.46 | Đúng | Tương đương kết quả: Khớp 30 cây con (độ tương đồng 46.2%), kết quả chạy khớp. |
| 10 | L4_0005 | L4 | 0.47 | Sai | Sai logic: Khác biệt cấu trúc (Khớp 35 trên tổng số 75 cây con). |
| 11 | L5_0001 | L5 | 0.62 | Sai | Sai logic: Khác biệt cấu trúc (Khớp 39 trên tổng số 63 cây con). |
| 12 | L4_0007 | L4 | 0.45 | Sai | Sai logic: Khác biệt cấu trúc (Khớp 31 trên tổng số 69 cây con). |

## 3. Phân tích Chi tiết 12 Cặp Truy vấn (AST & Trực quan hóa)


### Cặp 1: L0_0001 (Mức L0)
* **Câu hỏi**: In Harris County, Texas (identified by GEOID starting with 48201), how many NFIP claims have a dateOfLoss on or after 2010-01-01?
* **Điểm tương đồng Subtree**: 0.13
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
- **Nhận xét**: Tương đương kết quả: Khớp 6 cây con (độ tương đồng 13.0%), kết quả chạy khớp.
- **Tổng số cây con Ground Truth (Ground Truth Subtrees)**: 20
- **Tổng số cây con Predicted (Predicted Subtrees)**: 32
- **Số cây con trùng khớp (Matching Subtrees Count)**: 6
- **Top 5 cây con lớn nhất trùng khớp (Largest Matching Subtrees)**: `From(Table:claims(Identifier:claims))` (Số lượng: 1), `Table:claims(Identifier:claims)` (Số lượng: 1), `Identifier:dateOfLoss` (Số lượng: 1), `Literal:2010-01-01` (Số lượng: 1), `Identifier:claims` (Số lượng: 1)

---


### Cặp 2: L0_0002 (Mức L0)
* **Câu hỏi**: What is the total area of valid FEMA Flood Hazard Zone polygons in Florida (STATEFP = '12') labeled as AE?
* **Điểm tương đồng Subtree**: 0.62
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
- **Nhận xét**: Sai logic: Khác biệt cấu trúc (Khớp 16 trên tổng số 26 cây con).
- **Tổng số cây con Ground Truth (Ground Truth Subtrees)**: 24
- **Tổng số cây con Predicted (Predicted Subtrees)**: 18
- **Số cây con trùng khớp (Matching Subtrees Count)**: 16
- **Top 5 cây con lớn nhất trùng khớp (Largest Matching Subtrees)**: `And(EQ(Literal:12,Column(Identifier:STATEFP)),EQ(Literal:AE,Column(Identifier:FLD_ZONE)))` (Số lượng: 1), `Sum(Func:ST_AREA(Column(Identifier:geometry)))` (Số lượng: 1), `From(Table:floodplain(Identifier:floodplain))` (Số lượng: 1), `EQ(Literal:AE,Column(Identifier:FLD_ZONE))` (Số lượng: 1), `Func:ST_AREA(Column(Identifier:geometry))` (Số lượng: 1)

---


### Cặp 3: L1_0001 (Mức L1)
* **Câu hỏi**: Which non-null year had the highest total number of NFIP flood claims in Louisiana (STATEFP 22), based on a key-based join between claims and county tables? Return the year.
* **Điểm tương đồng Subtree**: 0.45
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
- **Nhận xét**: Tương đương kết quả: Khớp 29 cây con (độ tương đồng 45.3%), kết quả chạy khớp.
- **Tổng số cây con Ground Truth (Ground Truth Subtrees)**: 45
- **Tổng số cây con Predicted (Predicted Subtrees)**: 48
- **Số cây con trùng khớp (Matching Subtrees Count)**: 29
- **Top 5 cây con lớn nhất trùng khớp (Largest Matching Subtrees)**: `Join(Table:county(Identifier:county),EQ(Column(Identifier:GEOID,Identifier:county),Left(Column(Identifier:GEOID,Identifier:claims),Literal:5)))` (Số lượng: 1), `EQ(Column(Identifier:GEOID,Identifier:county),Left(Column(Identifier:GEOID,Identifier:claims),Literal:5))` (Số lượng: 1), `Not(Is(Column(Identifier:dateOfLoss,Identifier:claims),Null))` (Số lượng: 1), `Left(Column(Identifier:GEOID,Identifier:claims),Literal:5)` (Số lượng: 1), `Is(Column(Identifier:dateOfLoss,Identifier:claims),Null)` (Số lượng: 1)

---


### Cặp 4: L1_0004 (Mức L1)
* **Câu hỏi**: Which 3 Texas counties (STATEFP 48) have the highest non-null percentage of individuals with zero vulnerability components?
* **Điểm tương đồng Subtree**: 0.76
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
- **Nhận xét**: Sai logic: Khác biệt cấu trúc (Khớp 42 trên tổng số 55 cây con).
- **Tổng số cây con Ground Truth (Ground Truth Subtrees)**: 46
- **Tổng số cây con Predicted (Predicted Subtrees)**: 51
- **Số cây con trùng khớp (Matching Subtrees Count)**: 42
- **Top 5 cây con lớn nhất trùng khớp (Largest Matching Subtrees)**: `Join(Table:county(Identifier:county),EQ(Column(Identifier:GEOID,Identifier:county),Left(Column(Identifier:GEOID,Identifier:cre),Literal:5)))` (Số lượng: 1), `Where(And(EQ(Literal:48,Column(Identifier:STATEFP,Identifier:county)),Not(Is(Column(Identifier:PRED0_PE,Identifier:cre),Null))))` (Số lượng: 1), `And(EQ(Literal:48,Column(Identifier:STATEFP,Identifier:county)),Not(Is(Column(Identifier:PRED0_PE,Identifier:cre),Null)))` (Số lượng: 1), `EQ(Column(Identifier:GEOID,Identifier:county),Left(Column(Identifier:GEOID,Identifier:cre),Literal:5))` (Số lượng: 1), `Order(Ordered(Avg(Column(Identifier:PRED0_PE,Identifier:cre))))` (Số lượng: 1)

---


### Cặp 5: L2_0003 (Mức L2)
* **Câu hỏi**: Which census_tract in Hillsborough County, FL (identified by STATEFP = '12' and COUNTYFP = '057') has the largest total overlap area with all zcta polygons? Return its 11-digit GEOID.
* **Điểm tương đồng Subtree**: 0.68
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
- **Nhận xét**: Tương đương kết quả: Khớp 42 cây con (độ tương đồng 67.7%), kết quả chạy khớp.
- **Tổng số cây con Ground Truth (Ground Truth Subtrees)**: 58
- **Tổng số cây con Predicted (Predicted Subtrees)**: 46
- **Số cây con trùng khớp (Matching Subtrees Count)**: 42
- **Top 5 cây con lớn nhất trùng khớp (Largest Matching Subtrees)**: `Order(Ordered(Sum(Func:ST_AREA(Func:ST_INTERSECTION(Column(Identifier:geometry,Identifier:census_tracts),Column(Identifier:geometry,Identifier:zcta))))))` (Số lượng: 1), `Ordered(Sum(Func:ST_AREA(Func:ST_INTERSECTION(Column(Identifier:geometry,Identifier:census_tracts),Column(Identifier:geometry,Identifier:zcta)))))` (Số lượng: 1), `And(EQ(Literal:12,Column(Identifier:STATEFP,Identifier:census_tracts)),EQ(Literal:057,Column(Identifier:COUNTYFP,Identifier:census_tracts)))` (Số lượng: 1), `Sum(Func:ST_AREA(Func:ST_INTERSECTION(Column(Identifier:geometry,Identifier:census_tracts),Column(Identifier:geometry,Identifier:zcta))))` (Số lượng: 1), `Func:ST_AREA(Func:ST_INTERSECTION(Column(Identifier:geometry,Identifier:census_tracts),Column(Identifier:geometry,Identifier:zcta)))` (Số lượng: 1)

---


### Cặp 6: L2_0001 (Mức L2)
* **Câu hỏi**: How many census_tracts in Duval County, FL (identified by GEOID starting with 12031) intersect floodplain polygons?
* **Điểm tương đồng Subtree**: 0.59
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
- **Nhận xét**: Sai logic: Khác biệt cấu trúc (Khớp 23 trên tổng số 39 cây con).
- **Tổng số cây con Ground Truth (Ground Truth Subtrees)**: 37
- **Tổng số cây con Predicted (Predicted Subtrees)**: 25
- **Số cây con trùng khớp (Matching Subtrees Count)**: 23
- **Top 5 cây con lớn nhất trùng khớp (Largest Matching Subtrees)**: `Join(Table:floodplain(Identifier:floodplain),Func:ST_INTERSECTS(Column(Identifier:geometry,Identifier:census_tracts),Column(Identifier:geometry,Identifier:floodplain)))` (Số lượng: 1), `Func:ST_INTERSECTS(Column(Identifier:geometry,Identifier:census_tracts),Column(Identifier:geometry,Identifier:floodplain))` (Số lượng: 1), `Like(Column(Identifier:GEOID,Identifier:census_tracts),Literal:12031%)` (Số lượng: 1), `Count(Distinct(Column(Identifier:GEOID,Identifier:census_tracts)))` (Số lượng: 1), `Distinct(Column(Identifier:GEOID,Identifier:census_tracts))` (Số lượng: 1)

---


### Cặp 7: L3_0013 (Mức L3)
* **Câu hỏi**: How many Louisiana (STATEFP 22) census tracts with NFIP claims have both overall SVI relative vulnerability percentile across all themes above 0.8 and CRE population exceeding 10,000?
* **Điểm tương đồng Subtree**: 0.36
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
- **Nhận xét**: Tương đương kết quả: Khớp 28 cây con (độ tương đồng 36.4%), kết quả chạy khớp.
- **Tổng số cây con Ground Truth (Ground Truth Subtrees)**: 58
- **Tổng số cây con Predicted (Predicted Subtrees)**: 47
- **Số cây con trùng khớp (Matching Subtrees Count)**: 28
- **Top 5 cây con lớn nhất trùng khớp (Largest Matching Subtrees)**: `GT(Column(Identifier:RPL_THEMES,Identifier:svi),Literal:0.8)` (Số lượng: 1), `GT(Column(Identifier:POPUNI,Identifier:cre),Literal:10000)` (Số lượng: 1), `Column(Identifier:RPL_THEMES,Identifier:svi)` (Số lượng: 1), `Column(Identifier:POPUNI,Identifier:cre)` (Số lượng: 1), `Column(Identifier:GEOID,Identifier:svi)` (Số lượng: 1)

---


### Cặp 8: L3_0002 (Mức L3)
* **Câu hỏi**: In Florida (STATEFP 12), list the 5 census tracts with the highest population-weighted combined score of NRI total expected annual loss for riverine flooding and its average annual flood event frequency among tracts with NFIP claims.
* **Điểm tương đồng Subtree**: 0.32
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
- **Nhận xét**: Sai logic: Khác biệt cấu trúc (Khớp 37 trên tổng số 116 cây con).
- **Tổng số cây con Ground Truth (Ground Truth Subtrees)**: 88
- **Tổng số cây con Predicted (Predicted Subtrees)**: 65
- **Số cây con trùng khớp (Matching Subtrees Count)**: 37
- **Top 5 cây con lớn nhất trùng khớp (Largest Matching Subtrees)**: `Mul(Paren(Add(Column(Identifier:RFLD_EALT,Identifier:nri),Column(Identifier:RFLD_AFREQ,Identifier:nri))),Column(Identifier:POPUNI,Identifier:cre))` (Số lượng: 1), `Paren(Add(Column(Identifier:RFLD_EALT,Identifier:nri),Column(Identifier:RFLD_AFREQ,Identifier:nri)))` (Số lượng: 1), `Add(Column(Identifier:RFLD_EALT,Identifier:nri),Column(Identifier:RFLD_AFREQ,Identifier:nri))` (Số lượng: 1), `Column(Identifier:RFLD_AFREQ,Identifier:nri)` (Số lượng: 1), `Column(Identifier:RFLD_EALT,Identifier:nri)` (Số lượng: 1)

---


### Cặp 9: L4_0032 (Mức L4)
* **Câu hỏi**: In Dallas County, Texas (GEOID 48113), what is the total Expected annual loss for buildings caused by riverine flooding (USD) across all census tracts within that county, contingent on the county boundary also containing at least one hospital?
* **Điểm tương đồng Subtree**: 0.46
* **Độ chính xác thực thi**: Đúng

#### Truy vấn so sánh:
* **Ground Truth SQL**:
  ```sql
  SELECT SUM(n.RFLD_EALB) AS total_expected_loss FROM nri n JOIN county c ON LEFT(n.GEOID, 5) = c.GEOID WHERE c.GEOID = '48113' AND n.RFLD_EALB IS NOT NULL AND EXISTS (SELECT 1 FROM hospitals h WHERE ST_Contains(c.geometry, ST_Point(h.LON, h.LAT)));
  ```
* **Predicted SQL**:
  ```sql
  SELECT SUM(nri.RFLD_EALB) FROM nri JOIN county ON LEFT(nri.GEOID, 5) = county.GEOID WHERE county.GEOID = '48113' AND EXISTS ( SELECT 1 FROM hospitals WHERE hospitals.COUNTYFIPS = county.GEOID )
  ```

#### Trực quan hóa Cây AST chuẩn hóa:
```text
CÂY AST GROUND TRUTH:
└─ Select
  └─ Alias
    └─ Sum
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
      └─ Left
        └─ Column
          └─ Identifier
          └─ Identifier
        └─ Literal
  └─ Where
    └─ And
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
      └─ Exists
        └─ Select
          └─ Literal
          └─ From
            └─ Table
              └─ Identifier
          └─ Where
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

CÂY AST PREDICTED:
└─ Select
  └─ Sum
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
      └─ Exists
        └─ Select
          └─ Literal
          └─ From
            └─ Table
              └─ Identifier
          └─ Where
            └─ EQ
              └─ Column
                └─ Identifier
                └─ Identifier
              └─ Column
                └─ Identifier
                └─ Identifier
```

#### Phân tích lỗi và khác biệt:
- **Nhận xét**: Tương đương kết quả: Khớp 30 cây con (độ tương đồng 46.2%), kết quả chạy khớp.
- **Tổng số cây con Ground Truth (Ground Truth Subtrees)**: 54
- **Tổng số cây con Predicted (Predicted Subtrees)**: 41
- **Số cây con trùng khớp (Matching Subtrees Count)**: 30
- **Top 5 cây con lớn nhất trùng khớp (Largest Matching Subtrees)**: `Join(Table:county(Identifier:county),EQ(Column(Identifier:GEOID,Identifier:county),Left(Column(Identifier:GEOID,Identifier:nri),Literal:5)))` (Số lượng: 1), `EQ(Column(Identifier:GEOID,Identifier:county),Left(Column(Identifier:GEOID,Identifier:nri),Literal:5))` (Số lượng: 1), `EQ(Literal:48113,Column(Identifier:GEOID,Identifier:county))` (Số lượng: 1), `Left(Column(Identifier:GEOID,Identifier:nri),Literal:5)` (Số lượng: 1), `Sum(Column(Identifier:RFLD_EALB,Identifier:nri))` (Số lượng: 1)

---


### Cặp 10: L4_0005 (Mức L4)
* **Câu hỏi**: Which 5 Texas (STATEFP 12) counties have the highest number of hospitals located inside floodplain zones? Return their names.
* **Điểm tương đồng Subtree**: 0.47
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
- **Nhận xét**: Sai logic: Khác biệt cấu trúc (Khớp 35 trên tổng số 75 cây con).
- **Tổng số cây con Ground Truth (Ground Truth Subtrees)**: 61
- **Tổng số cây con Predicted (Predicted Subtrees)**: 49
- **Số cây con trùng khớp (Matching Subtrees Count)**: 35
- **Top 5 cây con lớn nhất trùng khớp (Largest Matching Subtrees)**: `StPoint(Column(Identifier:LON,Identifier:hospitals),Column(Identifier:LAT,Identifier:hospitals))` (Số lượng: 1), `Column(Identifier:COUNTYFIPS,Identifier:hospitals)` (Số lượng: 1), `Column(Identifier:geometry,Identifier:floodplain)` (Số lượng: 1), `Group(Column(Identifier:NAME,Identifier:county))` (Số lượng: 1), `Column(Identifier:STATEFP,Identifier:county)` (Số lượng: 1)

---


### Cặp 11: L5_0001 (Mức L5)
* **Câu hỏi**: How many hospitals are located within both FEMA floodplain polygons and census tract boundaries in Harris County, Texas (identified by the leftmost 5 digits of GEOID 48201 in the census_tract table)?
* **Điểm tương đồng Subtree**: 0.62
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
- **Nhận xét**: Sai logic: Khác biệt cấu trúc (Khớp 39 trên tổng số 63 cây con).
- **Tổng số cây con Ground Truth (Ground Truth Subtrees)**: 57
- **Tổng số cây con Predicted (Predicted Subtrees)**: 45
- **Số cây con trùng khớp (Matching Subtrees Count)**: 39
- **Top 5 cây con lớn nhất trùng khớp (Largest Matching Subtrees)**: `Join(Table:census_tracts(Identifier:census_tracts),Func:ST_CONTAINS(Column(Identifier:geometry,Identifier:census_tracts),StPoint(Column(Identifier:LON,Identifier:hospitals),Column(Identifier:LAT,Identifier:hospitals))))` (Số lượng: 1), `Join(Table:floodplain(Identifier:floodplain),Func:ST_CONTAINS(Column(Identifier:geometry,Identifier:floodplain),StPoint(Column(Identifier:LON,Identifier:hospitals),Column(Identifier:LAT,Identifier:hospitals))))` (Số lượng: 1), `Func:ST_CONTAINS(Column(Identifier:geometry,Identifier:census_tracts),StPoint(Column(Identifier:LON,Identifier:hospitals),Column(Identifier:LAT,Identifier:hospitals)))` (Số lượng: 1), `Func:ST_CONTAINS(Column(Identifier:geometry,Identifier:floodplain),StPoint(Column(Identifier:LON,Identifier:hospitals),Column(Identifier:LAT,Identifier:hospitals)))` (Số lượng: 1), `StPoint(Column(Identifier:LON,Identifier:hospitals),Column(Identifier:LAT,Identifier:hospitals))` (Số lượng: 2)

---


### Cặp 12: L4_0007 (Mức L4)
* **Câu hỏi**: In Texas (STATEFP 48), how many census tracts with Percentage of individuals with three plus components of social vulnerability higher than 40 intersect FEMA floodplain polygons?
* **Điểm tương đồng Subtree**: 0.45
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
- **Nhận xét**: Sai logic: Khác biệt cấu trúc (Khớp 31 trên tổng số 69 cây con).
- **Tổng số cây con Ground Truth (Ground Truth Subtrees)**: 59
- **Tổng số cây con Predicted (Predicted Subtrees)**: 41
- **Số cây con trùng khớp (Matching Subtrees Count)**: 31
- **Top 5 cây con lớn nhất trùng khớp (Largest Matching Subtrees)**: `Join(Table:floodplain(Identifier:floodplain),Func:ST_INTERSECTS(Column(Identifier:geometry,Identifier:census_tracts),Column(Identifier:geometry,Identifier:floodplain)))` (Số lượng: 1), `Func:ST_INTERSECTS(Column(Identifier:geometry,Identifier:census_tracts),Column(Identifier:geometry,Identifier:floodplain))` (Số lượng: 1), `EQ(Column(Identifier:GEOID,Identifier:census_tracts),Column(Identifier:GEOID,Identifier:cre))` (Số lượng: 1), `GT(Column(Identifier:PRED3_PE,Identifier:cre),Literal:40)` (Số lượng: 1), `Column(Identifier:geometry,Identifier:census_tracts)` (Số lượng: 1)

---

