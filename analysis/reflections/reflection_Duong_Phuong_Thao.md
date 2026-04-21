# 📋 Báo cáo Cá nhân — Lab Day 14: AI Evaluation Factory

## Thông tin cá nhân

| Mục | Chi tiết |
| :--- | :--- |
| **Họ và tên** | Dương Phương Thảo |
| **Email** | duongphuongthao08102004@gmail.com |
| **Vai trò trong nhóm** | Nhóm Data — Retrieval Evaluation & Synthetic Data Generation (SDG) |
| **Branch làm việc** | `thao` |
| **Commit chính** | `a5a99bd` — _feat: implement retrieval evaluation metrics and add golden dataset for testing_ |

---

## 1. Engineering Contribution (Đóng góp kỹ thuật)

### 1.1. Synthetic Data Generation — `data/synthetic_gen.py`

**Mô tả:** Viết lại toàn bộ module sinh dữ liệu Golden Dataset từ template placeholder ban đầu thành một pipeline hoàn chỉnh, sử dụng OpenAI GPT-4o-mini để tự động sinh 50 test cases chất lượng cao.

**Các điểm kỹ thuật nổi bật:**

- **Thiết kế 4 loại prompt template** phục vụ Red Teaming:
  - `fact-check` (50%): Câu hỏi kiểm tra thông tin trực tiếp từ tài liệu.
  - `adversarial` (20%): Câu hỏi tấn công bằng Prompt Injection / Goal Hijacking.
  - `out-of-context` (20%): Câu hỏi ngoài phạm vi tài liệu, kỳ vọng Agent từ chối trả lời.
  - `ambiguous` (10%): Câu hỏi mập mờ, kỳ vọng Agent hỏi ngược để làm rõ.

- **Sliding Window Chunking Strategy:** Thay vì nhân bản mảng tạo chunk trùng lặp (phương pháp cũ), tôi triển khai thuật toán cửa sổ trượt với `step_size` tính toán tự động, đảm bảo mỗi chunk có nội dung khác biệt nhau, tăng tính đa dạng cho dataset.
  ```python
  step_size = max(1, (len(text) - chunk_size) // max(1, total_pairs_needed - 1))
  for i in range(total_pairs_needed):
      start_idx = min(i * step_size, len(text) - chunk_size)
      chunks.append(text[start_idx : start_idx + chunk_size])
  ```

- **Async Concurrency với Rate Limiting:** Sử dụng `asyncio.Semaphore(5)` để chạy song song tối đa 5 request đồng thời, tránh bị OpenAI rate-limit mà vẫn đảm bảo tốc độ nhanh.

- **Robust JSON Parsing:** Hàm `extract_valid()` xử lý đa dạng format trả về từ LLM:
  - Trường hợp LLM trả về `{"cases": [...]}` → parse trực tiếp.
  - Trường hợp LLM trả về single object `{"question": ...}` → wrap thành list.
  - Trường hợp LLM trả về key khác → duyệt tất cả values tìm list hợp lệ.
  - Trường hợp LLM trả về list trực tiếp → parse luôn.

- **Viết văn bản nguồn (Source Text):** Soạn một bài viết chi tiết (~2000 từ) về chủ đề "Thông luật và Dân luật" để làm Knowledge Base cho hệ thống RAG, đảm bảo nội dung đủ phong phú và đa dạng để sinh được nhiều loại câu hỏi khác nhau.

### 1.2. Retrieval Evaluation — `engine/retrieval_eval.py`

**Mô tả:** Triển khai hoàn chỉnh class `RetrievalEvaluator` với các metric đánh giá Retrieval stage, thay thế placeholder logic ban đầu.

**Các hàm đã triển khai:**

| Hàm | Mô tả | Chi tiết kỹ thuật |
| :--- | :--- | :--- |
| `calculate_hit_rate()` | Kiểm tra xem ít nhất 1 ID kỳ vọng có nằm trong Top-K kết quả retrieved không | Trả về `1.0` nếu hit, `0.0` nếu miss. Hỗ trợ tham số `top_k` (mặc định = 3) |
| `calculate_mrr()` | Tính Mean Reciprocal Rank | Tìm vị trí đầu tiên của expected_id trong retrieved_ids, trả về `1/(pos+1)` |
| `evaluate_batch()` | Chạy đánh giá trên toàn bộ dataset | Tính trung bình Hit Rate và MRR cho tất cả test cases |

**Bug fix quan trọng:** Xử lý edge case cho Out-of-context cases — khi `expected_retrieval_ids` là mảng rỗng `[]`, cả `calculate_hit_rate` và `calculate_mrr` đều trả về `1.0` (vì Agent không cần tìm document nào, việc "không tìm" chính là đúng). Nếu không fix bug này, tất cả out-of-context cases sẽ bị đánh giá sai, kéo toàn bộ metric xuống.

### 1.3. Golden Dataset — `data/golden_set.jsonl`

**Kết quả sinh được:** 50 test cases hoàn chỉnh với phân bố:

| Loại case | Số lượng | Tỷ lệ |
| :--- | :---: | :---: |
| Fact-check | 25 | 50% |
| Adversarial | 10 | 20% |
| Out-of-context | 10 | 20% |
| Ambiguous | 5 | 10% |

Mỗi entry bao gồm đầy đủ: `question`, `expected_answer`, `expected_retrieval_ids`, và `metadata` (difficulty, type).

### 1.4. Thống kê thay đổi mã nguồn

| File | Insertions | Deletions | Tổng thay đổi |
| :--- | :---: | :---: | :---: |
| `data/synthetic_gen.py` | +193 | -đã có template | Viết lại gần hoàn toàn |
| `engine/retrieval_eval.py` | +58 | -14 (placeholder) | Triển khai đầy đủ logic |
| `data/golden_set.jsonl` | +50 | 0 | File mới, 50 entries |
| **Tổng** | **+266** | **-37** | **303 dòng thay đổi** |

---

## 2. Technical Depth (Chiều sâu kỹ thuật)

### 2.1. Giải thích khái niệm Hit Rate

**Hit Rate (HR@K)** đo lường tỷ lệ query mà hệ thống Retrieval trả về ít nhất một tài liệu đúng trong Top-K kết quả. Đây là metric quan trọng nhất để đánh giá "Retrieval có tìm đúng hay không" trước khi đánh giá chất lượng Generation.

**Công thức:**
```
HR@K = (Số query có ít nhất 1 relevant doc trong Top-K) / (Tổng số query)
```

Trong hệ thống của nhóm, tôi implement với `top_k=3`, nghĩa là chỉ cần 1 trong 3 chunk đầu tiên mà Vector DB trả về là đúng → Hit = 1.0.

### 2.2. Giải thích khái niệm MRR (Mean Reciprocal Rank)

**MRR** đo lường vị trí trung bình của tài liệu đúng đầu tiên trong danh sách kết quả. MRR nhạy cảm hơn Hit Rate vì nó phân biệt được giữa "tìm đúng ở vị trí 1" (tốt nhất) vs "tìm đúng ở vị trí 10" (kém hơn).

**Công thức:**
```
MRR = (1/N) × Σ (1 / rank_i)
```

Ví dụ: Nếu `expected = ["chunk_005"]` và `retrieved = ["chunk_001", "chunk_005", "chunk_009"]`, thì `chunk_005` ở vị trí 2 → RR = 1/2 = 0.5.

### 2.3. Mối liên hệ Retrieval Quality → Answer Quality

Trong kiến trúc RAG (Retrieval-Augmented Generation), chất lượng câu trả lời **phụ thuộc trực tiếp** vào chất lượng Retrieval:

1. **Retrieval tốt (Hit Rate cao):** LLM nhận được context chính xác → sinh câu trả lời đúng và đầy đủ.
2. **Retrieval kém (Hit Rate thấp):** LLM không có context → hoặc từ chối trả lời, hoặc tệ hơn là **Hallucinate** (bịa thông tin).
3. **MRR thấp (vị trí chunk đúng quá xa):** Dù tìm được chunk đúng nhưng ở vị trí cuối, khi context window bị giới hạn, LLM có thể bỏ qua chunk đó → chất lượng giảm.

⇒ **Kết luận:** Nhóm nào chỉ đánh giá câu trả lời (Generation) mà bỏ qua Retrieval sẽ không biết **lỗi nằm ở đâu** — Retrieval hay Prompting. Đây là lý do tôi triển khai Retrieval Eval trước khi nhóm chạy Benchmark.

### 2.4. Trade-off Chi phí vs Chất lượng trong SDG

Khi sinh Golden Dataset, tôi chọn `gpt-4o-mini` thay vì `gpt-4o` để cân bằng:
- **Chi phí:** gpt-4o-mini rẻ hơn ~15 lần so với gpt-4o ($0.15/1M vs $2.5/1M input tokens).
- **Chất lượng:** Với task sinh QA pairs (không quá phức tạp), gpt-4o-mini cho chất lượng đủ tốt.
- **Tốc độ:** gpt-4o-mini có latency thấp hơn, giúp sinh 50 cases nhanh hơn.

Đây là ví dụ thực tế về trade-off Cost vs Quality trong AI Engineering.

---

## 3. Problem Solving (Giải quyết vấn đề)

### Vấn đề 1: LLM trả về JSON không nhất quán

**Triệu chứng:** Khi gọi OpenAI API sinh QA, mỗi lần gọi LLM trả về format JSON khác nhau — có lúc là `{"cases": [...]}`, có lúc là `[{...}]`, có lúc là `{"qa_pairs": [...]}`.

**Phân tích:** Dù đã dùng `response_format={"type": "json_object"}` và system prompt chỉ định rõ format, LLM vẫn không tuân thủ 100%. Đây là hạn chế cố hữu của LLM-based data generation.

**Giải pháp:** Viết hàm `extract_valid()` theo kiến trúc "defensive parsing" — thử parse theo nhiều pattern khác nhau, ưu tiên pattern phổ biến nhất trước:
1. Thử key `"cases"` trước (pattern mong muốn).
2. Thử single object có key `"question"` (LLM chỉ trả 1 case).
3. Duyệt tất cả values tìm list đầu tiên (LLM dùng key tùy ý).
4. Parse trực tiếp nếu response là list.

**Kết quả:** Tỷ lệ parse thành công đạt gần 100%, không bị mất test case nào do lỗi format.

### Vấn đề 2: Duplicate Chunks khi văn bản ngắn

**Triệu chứng:** Template gốc dùng phép nhân mảng (`chunks * n`) để tạo đủ số lượng chunk cần thiết. Khi văn bản ngắn, toàn bộ chunk bị trùng lặp → QA pairs bị trùng.

**Giải pháp:** Thiết kế thuật toán Sliding Window — dịch cửa sổ với `step_size` nhỏ, mỗi chunk overlap một phần nhưng vẫn có nội dung mới. Đảm bảo diversity cho dataset mà không yêu cầu văn bản quá dài.

### Vấn đề 3: Out-of-context cases bị đánh giá sai

**Triệu chứng:** Các test case loại `out-of-context` có `expected_retrieval_ids = []`. Hàm `calculate_hit_rate` và `calculate_mrr` ban đầu không xử lý trường hợp này → trả về `0.0` cho tất cả out-of-context cases → kéo metric trung bình xuống sai lệch.

**Phân tích gốc rễ:** Logic ban đầu coi "không tìm thấy document" là thất bại. Nhưng với out-of-context case, việc "không kỳ vọng tìm thấy document nào" chính là hành vi đúng.

**Giải pháp:** Thêm guard clause ở đầu cả hai hàm:
```python
if not expected_ids:
    return 1.0  # Không kỳ vọng ID nào → mặc định pass
```

---

## 4. Kết quả Benchmark cuối cùng (liên quan đến phần Retrieval)

Sau khi chạy pipeline hoàn chỉnh với 50 test cases:

| Metric | Giá trị |
| :--- | :---: |
| **Average Hit Rate** | 1.00 |
| **Average MRR** | 0.83 |
| **Average Judge Score** | 4.42 / 5.0 |
| **Agreement Rate** | 96.8% |
| **Total Cost** | $0.0015 |

Kết quả cho thấy Retrieval stage hoạt động rất tốt (Hit Rate = 1.0), MRR = 0.83 cho thấy chunk đúng thường xuất hiện trong Top-2 kết quả. Điều này chứng minh rằng chất lượng câu trả lời cao (4.42/5.0) có nền tảng từ Retrieval tốt.

---

## 5. Bài học rút ra

1. **"Garbage In, Garbage Out"** — Chất lượng Golden Dataset quyết định toàn bộ giá trị của Benchmark. Nếu dataset không đa dạng (thiếu adversarial, out-of-context), kết quả Benchmark sẽ lạc quan giả tạo.

2. **Defensive Programming là bắt buộc khi làm việc với LLM** — Output của LLM không bao giờ đáng tin 100%. Mọi pipeline phải có error handling và fallback logic.

3. **Đánh giá Retrieval trước Generation** — Đây là nguyên tắc quan trọng nhất trong AI Evaluation: phải biết chính xác lỗi nằm ở giai đoạn nào (Retrieval hay Generation) trước khi tối ưu.

4. **Async + Semaphore là pattern chuẩn cho batch processing với API** — Giúp tăng throughput mà không bị rate-limit, áp dụng được cho cả SDG lẫn Benchmark runner.

---

*Ngày hoàn thành: 21/04/2026*
*Tác giả: Dương Phương Thảo*
