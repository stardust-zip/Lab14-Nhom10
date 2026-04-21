# Báo cáo Cá nhân — Phạm Thanh Tùng

## Thông tin chung
- **Họ và tên:** Phạm Thanh Tùng
- **Nhóm:** 10
- **Module phụ trách:** Multi-Judge Consensus Engine (`engine/llm_judge.py`)
- **Vai trò:** Nhóm AI/Backend — Thiết kế và triển khai hệ thống chấm điểm đa mô hình

---

## 1. Đóng góp Kỹ thuật (Engineering Contribution) — 15 điểm

### 1.1. Tổng quan module

Tôi chịu trách nhiệm thiết kế và triển khai toàn bộ module **Multi-Judge Consensus Engine** trong file `engine/llm_judge.py`. Đây là thành phần cốt lõi của hệ thống đánh giá, đảm nhận việc chấm điểm câu trả lời của AI Agent bằng nhiều model LLM khác nhau để đảm bảo tính khách quan.

### 1.2. Các thành phần đã triển khai

#### a) Class `LLMJudge` — Hệ thống chấm điểm chính
- Khởi tạo client `AsyncOpenAI` để giao tiếp với OpenAI API.
- Thiết kế **Rubric prompt** chi tiết với thang điểm 5 bậc, mỗi bậc có mô tả rõ ràng:
  - **5 điểm:** Chính xác hoàn toàn, đầy đủ chi tiết, văn phong chuyên nghiệp.
  - **4 điểm:** Chính xác nhưng thiếu chi tiết nhỏ.
  - **3 điểm:** Trả lời được ý chính nhưng mập mờ.
  - **2 điểm:** Sai một phần quan trọng hoặc Hallucination nhẹ.
  - **1 điểm:** Hoàn toàn sai, từ chối trả lời hoặc vi phạm an toàn.

#### b) Hàm `_call_judge()` — Gọi LLM chấm điểm
- Nhận đầu vào: `model_name`, `question`, `answer`, `ground_truth`.
- Sử dụng `response_format={"type": "json_object"}` để ép LLM trả về JSON chuẩn chứa `score` và `reasoning`.
- Cài đặt `temperature=0.1` để đảm bảo chấm điểm ổn định và khách quan.
- Có xử lý lỗi (try/except) — trả về điểm mặc định 3 nếu API lỗi, tránh crash toàn pipeline.

#### c) Hàm `evaluate_multi_judge()` — Logic đồng thuận đa mô hình ⭐
Đây là phần **Expert Task** quan trọng nhất:
- **Gọi 2 model song song:** Sử dụng `asyncio.gather()` để gọi đồng thời `gpt-4o-mini` và `gpt-4o`, tiết kiệm thời gian chạy.
- **Tính Agreement Rate:** Dựa trên độ lệch điểm giữa 2 Judge:
  - Lệch 0 điểm → 100% đồng thuận (`agreement = 1.0`)
  - Lệch 1 điểm → 80% đồng thuận (`agreement = 0.8`)
  - Lệch >1 điểm → Bất đồng nặng (`agreement = 0.5`)
- **Conflict Resolution (Xử lý xung đột tự động):** Khi `diff > 1`, hệ thống tự động gọi một phiên Tie-breaker bằng model `gpt-4o` để phân xử. Điểm của Tie-breaker được lấy làm `final_score` cuối cùng.
- **Dữ liệu trả về:** Object chứa đầy đủ `final_score`, `agreement_rate`, `individual_scores` (điểm của từng Judge), và `reasoning` (lý do chấm điểm).

#### d) Test Script
- Viết 2 test cases trong khối `__main__`:
  - **Test 1:** Câu trả lời tốt → Kỳ vọng điểm cao, đồng thuận cao.
  - **Test 2:** Câu trả lời sai hoàn toàn (bịa đặt) → Kỳ vọng điểm thấp.

### 1.3. Chứng minh đóng góp
- **Hoàn thiện file `engine/llm_judge.py`**: Phát triển và mở rộng dựa trên bộ khung (template) cơ bản có sẵn, hiện thực hóa các hàm cốt lõi để hệ thống chạy thực tế.
- **Tích hợp logic nâng cao**: Trực tiếp implement và tinh chỉnh các cơ chế đánh giá đa mô hình (Dual-Judge), tính toán tỷ lệ đồng thuận (Agreement Rate) và xử lý xung đột tự động (Conflict Resolution) theo đúng tiêu chí của Lab.

---

## 2. Hiểu biết Kỹ thuật Chuyên sâu (Technical Depth) — 15 điểm

### 2.1. Agreement Rate (Tỷ lệ đồng thuận)
- **Khái niệm:** Là thước đo mức độ thống nhất giữa các Judge khi chấm cùng một câu trả lời.
- **Cách tính trong code:** Tôi sử dụng công thức rời rạc 3 bậc dựa trên `abs(score_a - score_b)`:
  - `diff = 0` → `agreement = 1.0` (hoàn toàn đồng ý)
  - `diff = 1` → `agreement = 0.8` (gần đồng ý)
  - `diff > 1` → `agreement = 0.5` (bất đồng → kích hoạt Tie-breaker)
- **Ý nghĩa thực tế:** Nếu agreement_rate trung bình trên toàn bộ dataset thấp (<0.7), cho thấy bộ câu hỏi khó hoặc rubric chấm điểm chưa rõ ràng — cần xem xét lại.

### 2.2. Position Bias trong LLM-as-Judge
- **Khái niệm:** LLM có xu hướng ưu tiên thông tin xuất hiện ở đầu hoặc cuối prompt (Primacy/Recency Bias). Nếu chỉ dùng 1 Judge, kết quả có thể bị thiên lệch.
- **Cách giảm thiểu:** Sử dụng 2 model khác nhau (`gpt-4o-mini` vs `gpt-4o`) giúp triệt tiêu bias riêng của từng model, vì mỗi model có kiến trúc và dữ liệu huấn luyện khác nhau.

### 2.3. Trade-off Chi phí vs Chất lượng
- **`gpt-4o-mini`:** Rẻ hơn (~15x), nhanh hơn, nhưng có thể thiếu sắc thái khi chấm các trường hợp ranh giới.
- **`gpt-4o`:** Đắt hơn, chính xác hơn, được dùng làm Judge chính và cũng là Tie-breaker.
- **Chiến lược:** Chạy song song cả 2 (async) để không tăng thời gian. Chỉ gọi Tie-breaker (tốn thêm 1 call GPT-4o) khi thực sự có xung đột — tối ưu chi phí cho majority case (đồng thuận).

### 2.4. MRR (Mean Reciprocal Rank)
- **Khái niệm:** Đo lường vị trí của tài liệu đúng trong kết quả tìm kiếm. MRR = 1/rank. Nếu tài liệu đúng ở vị trí 1 → MRR = 1.0, vị trí 3 → MRR = 0.33.
- **Liên hệ với Judge:** Retrieval quality ảnh hưởng trực tiếp đến Answer quality. Nếu MRR thấp → context sai → Agent trả lời sai → Judge cho điểm thấp. Do đó cần đánh giá Retrieval trước khi đánh giá Generation.

---

## 3. Giải quyết Vấn đề (Problem Solving) — 10 điểm

### Vấn đề 1: Chọn 2 model Judge nào?
- **Bối cảnh:** Rubric gợi ý dùng GPT + Claude, nhưng việc dùng 2 API provider khác nhau tăng độ phức tạp (2 SDK, 2 bộ API key, 2 format response khác nhau).
- **Giải pháp:** Dùng 2 model **cùng OpenAI** nhưng khác tier (`gpt-4o-mini` vs `gpt-4o`). Lợi ích:
  - Chỉ cần 1 API key, 1 SDK → code gọn, dễ bảo trì.
  - Vẫn đảm bảo tính đa dạng vì 2 model có khả năng suy luận khác nhau.
  - Đáp ứng tiêu chí "ít nhất 2 model Judge" trong rubric.

### Vấn đề 2: Xử lý xung đột điểm số công bằng
- **Bối cảnh:** Khi 2 Judge cho điểm chênh lệch lớn (ví dụ: 5 vs 2), lấy trung bình (3.5) không phản ánh đúng thực tế.
- **Giải pháp:** Triển khai cơ chế **Tie-breaker tự động** — gọi model `gpt-4o` lần nữa với vai trò phân xử. Điểm của Tie-breaker được lấy làm `final_score`, kèm ghi nhận `agreement = 0.5` để đánh dấu đây là case khó cần review.

### Vấn đề 3: Đảm bảo output ổn định từ LLM
- **Bối cảnh:** LLM có thể trả về text tự do thay vì JSON chuẩn, gây crash khi parse.
- **Giải pháp:**
  - Sử dụng `response_format={"type": "json_object"}` để bắt buộc output JSON.
  - Đặt `temperature=0.1` để giảm tính ngẫu nhiên.
  - Xử lý fallback: nếu parse lỗi → trả về điểm mặc định 3 (trung bình) thay vì crash.

---

## 4. Kết luận

Qua bài lab này, tôi đã:
- Hiểu được tầm quan trọng của việc **đo lường khách quan** chất lượng AI Agent — không thể chỉ "cảm thấy" Agent tốt mà phải chứng minh bằng số liệu.
- Nắm vững kiến trúc **Multi-Judge** trong thực tế production: tại sao cần nhiều Judge, cách tính đồng thuận, và xử lý xung đột.
- Rèn luyện kỹ năng **async programming** với Python (asyncio.gather) để tối ưu hiệu năng hệ thống đánh giá.
- Nhận ra trade-off giữa **chi phí API** và **độ tin cậy** của kết quả đánh giá — một bài toán thực tế trong AI Engineering.
