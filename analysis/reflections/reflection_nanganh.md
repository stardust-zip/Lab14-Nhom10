# 📋 Báo cáo Cá nhân — Lab Day 14: AI Evaluation Factory

## Thông tin cá nhân

| Mục | Chi tiết |
| :--- | :--- |
| **Họ và tên** | nanganh |
| **Email** | nanganh@student.edu.vn |
| **Vai trò trong nhóm** | Nhóm DevOps/Analyst — Regression Release Gate |
| **Branch làm việc** | `regression-testing-auto-gate` |
| **Commit chính** | `e86155f` — _feat: implement Auto-Gate release logic and comprehensive metrics_ |

---

## 1. Engineering Contribution (Đóng góp kỹ thuật)

### 1.1. Auto-Gate System & Regression Analysis — `main.py`

**Mô tả:** Triển khai module so sánh động (Regression Analysis) để đánh giá chất lượng Agent V1 (Baseline) và Agent V2 (Optimized), từ đó tạo ra Auto-Gate Release - quyết định chặn hoặc cho phép phát hành Agent mới.

**Các điểm kỹ thuật nổi bật:**

- **Tính toán Delta tự động:** So sánh điểm số đầu ra của giám khảo (`avg_score`) để tìm mức độ tăng trưởng (Delta). Nếu `Delta < 0` => Regression, phiên bản mới tệ hơn.
- **Auto-Gate Rules Engine:** Thiết lập hệ thống kiểm duyệt gắt gao với 3 điều kiện đồng thời:
  - `delta > 0` (Bản mới phải tốt hơn bản cũ).
  - `hit_rate >= 0.8` (Đảm bảo Vector DB lấy dữ liệu chính xác).
  - `agreement_rate >= 0.7` (Đảm bảo các LLM Judge đồng thuận với nhau).
- **Log lý do thất bại:** Xây dựng mảng `reasons = []` để tự động in ra các lý do khiến mô hình bị từ chối phát hành (BLOCK RELEASE).

### 1.2. Hỗ trợ Format Báo cáo JSON Metrics 

**Mô tả:** Đóng gói toàn bộ metrics phức tạp thành cấu trúc JSON tiêu chuẩn sử dụng chung cho nhóm.

- Khởi tạo khối `regression` object bao gồm thông số `score`, `hit_rate`, và `judge_agreement` để dễ dàng load lên Dashboard sau này.
- Map tự động cờ đánh giá `decision` ("APPROVE" / "BLOCK") vào file `reports/summary.json`.

### 1.3. Thống kê thay đổi mã nguồn

| File | Insertions | Deletions | Tổng thay đổi |
| :--- | :---: | :---: | :---: |
| `main.py` | +65 | -33 | Đảm nhận việc nâng cấp hàm main() |
| `analysis/reflections/reflection_nanganh.md` | +195 | 0 | File mới |
| **Tổng** | **+260** | **-33** | **293 dòng thay đổi** |

---

## 2. Technical Depth (Chiều sâu kỹ thuật)

### 2.1. Giải thích tầm quan trọng của Auto-Gate

**Auto-Gate (Release Gate)** là chốt chặn cuối cùng trong CI/CD pipeline của MLOps/LLMOps. Việc chỉ dựa vào "Loss" ban đầu không còn phản ánh đúng chất lượng của một AI Agent, mà phụ thuộc mạnh mẽ vào cách Retrieval & LLM hoạt động.
Hệ thống Auto-Gate do tôi bắt buộc thỏa mãn cùng lúc 3 rào chắn, giúp ngăn chặn rủi ro đẩy những model chạy "ngu ngốc" nhưng có điểm ảo ra Production.

### 2.2. Giải thích vị thế của MRR trong Regression

Dù Auto-Gate chỉ gài chặt `hit_rate >= 0.8`, thông số **MRR** vẫn được trích xuất ra file log. Nếu Hit Rate V1 và V2 đều là 1.0 (ai cũng xuất hiện đúng), lúc này chỉ số MRR sẽ đóng vai trò quyết định ai làm tốt hơn:
- Nếu MRR V2 cao hơn V1, điều đó chứng minh Agent V2 ranking kết quả lên đầu danh sách hiệu quả hơn.

### 2.3. Cân bằng Trade-off (Cost vs Quality) cho dự án

Để ra được một quyết định (APPROVE / BLOCK), hệ thống phải chạy đủ `run_benchmarks` và Multi-Judge. Vì quá trình đánh giá sử dụng `batch_size=5` nên rất nhanh, nhưng chi phí gọi LLM sẽ tăng tuyến tính.
Tôi đã thu thập `"total_cost": sum(r.get("cost", 0.0))` ngay từ core logic để cảnh báo: nếu giá Release 1 bản vá tốn tới $5, team có thể phải rút gọn `golden_set.jsonl` hoặc giảm bậc Judge từ GPT-4.0 xuống model nhỏ hơn để tiết kiệm chi phí mà vẫn giữ được giá trị đánh giá.

---

## 3. Problem Solving (Giải quyết vấn đề)

### Vấn đề: Trình chỉnh sửa lưu đè mã giả lập (Mocking code), gây AttributeError

**Triệu chứng:** Khi tiến hành tích hợp và test pipeline với lệnh `python main.py`, console hiển thị:
`AttributeError: 'ExpertEvaluator' object has no attribute 'calculate_hit_rate'`

**Phân tích:** Lỗi xảy ra do trong quá trình code, editor của tôi vô tình lưu lại (ghi đè) template cũ sử dụng class giả lập `ExpertEvaluator`. Class này hoàn toàn không có hàm sinh metrics của Retrieval. Trong khi đó, nhánh chính đang mong đợi class chuẩn từ `engine.retrieval_eval`.

**Giải pháp:**
Thay vì sửa code trong module của engine (điều sẽ làm hỏng chức năng của cả nhóm), tôi:
1. Đọc lại Traceback, nhận thức được file caller là `main.py` ở hàm khởi tạo Runner.
2. Nhanh chóng xóa bỏ thiết kế giả lập, tiến hành import thẳng `RetrievalEvaluator` và `LLMJudge` từ module chuẩn.
3. Patching nóng code trong Visual Studio Code, đồng thời vẫn bảo vệ được biến cấu trúc format JSON xuất báo cáo mà tôi vừa sửa. Kết quả là pipeline chạy thành công ngay sau đó.

---

## 4. Kết quả Benchmark cuối cùng (Regression Phase)

Sau khi tích hợp hoàn chỉnh và chạy Pipeline:

| Phiên bản | Average Score | Hit Rate | MRR | Agreement Rate (Kappa) |
| :--- | :---: | :---: | :---: | :---: |
| **Agent V1 (Baseline)** | 3.50 | 0.80 | 0.65 | 0.60 |
| **Agent V2 (Optimized)** | 4.42 | 1.00 | 0.83 | 0.96 |

- **Delta Score:** `+0.92` *(Đạt chuẩn > 0)*
- **Hit Rate Threshold:** `1.0 >= 0.8` *(Pass)*
- **Agreement Rate Threshold:** `0.96 >= 0.7` *(Pass)*
- **Quyết định (Release Result):** `✅ DECISION: RELEASE APPROVED`

---

## 5. Bài học rút ra

1. **Automation là tất cả trong CI/CD AI** — Không thể tin tưởng vào việc đánh giá thủ công hoặc ngẫu nhiên vài ví dụ. Phải đóng gói logic trong Auto-Gate và chặn Model ngay từ lúc deploy.
2. **Kỹ năng làm việc đa luồng (Git / Syncing)** — Cần thận trọng khi vừa sửa code, vừa pull/push branch liên tục để tránh trường hợp đè ngược lại file cũ.
3. **Mọi metrics đều quan trọng để phân tích lỗi hệ thống** — Nếu một Agent thất bại trong Release, Auto-Gate rule sẽ nhả cụ thể lý do (do giảm Score, hit_rate tồi hay giám khảo đánh nhau).

---

*Ngày hoàn thành: 21/04/2026*
*Tác giả: nanganh*
