# Personal Reflection Report - Lab 14

**Thành viên:** nanganh (dựa trên workspace local path)
**Vai trò đảm nhận:** Regression Release Gate (Nhóm DevOps/Analyst)

---

## 1. Engineering Contribution (Đóng góp kỹ thuật)
- **Thiết kế Regression Testing & Auto-Gate:** Xây dựng logic tự động đánh giá chênh lệch (Delta Analysis) giữa phiên bản Baseline (V1) và Optimized (V2) trong `main.py`.
- **Implement Release Gate Rules:** Đặt ra các ngưỡng chất lượng gắt gao (Hit Rate >= 0.8, Agreement Rate >= 0.7 và Delta > 0) để quyết định tự động **APPROVE** hoặc **BLOCK** việc ra mắt phiên bản mới, đồng thời xuất log lý do từ chối phát hành rõ ràng.
- **Async Metrics Formatting:** Hỗ trợ tách các metrics trả về từ `BenchmarkRunner` như MRR, total_cost, agreement_rate ra file JSON tiêu chuẩn dùng chung cho báo cáo nhóm.
- **Quản lý Source Code khoa học:** Tích cực phân chia (split) nhánh (`regression-testing-auto-gate`), tách nhỏ các commits kĩ thuật số lượng lớn thành nhiều commits riêng biệt giúp team dễ dàng review.

## 2. Technical Depth (Chiều sâu kỹ thuật)
- **Hiểu biết về MRR (Mean Reciprocal Rank):** Nhận diện được MRR là chỉ số quan trọng hơn Hit Rate để đánh giá khả năng Ranking của Retriever. Việc tài liệu đúng nằm ở top 1 (rank 1) so với top 5 ảnh hưởng mạnh mẽ tới chất lượng Generation của Agent.
- **Rủi ro Position Bias & Cohen's Kappa:** Hệ thống chỉ có 1 giám khảo dễ dính "Position Bias" (ưu tiên context vị trí cụ thể) hoặc "Verbosity Bias". Đó là lý do hệ thống của chúng tôi tính toán **Agreement Rate** theo kiểu Cohen's Kappa giữa ít nhất 2 model khác biệt để hạn chế Bias xuống mức tối đa.
- **Trade-off giữa Quality & Cost:** Sử dụng kỹ thuật Async Semaphore (`batch_size=5`) tối ưu hiệu năng chạy (< 2 phút cho cases), tuy nhiên việc multi-judge đẩy `total_cost` lên cực cao. Bài toán đặt ra là trong tương lai, cần tích hợp Routing logic (Chỉ gọi model đắt khi model nhỏ mâu thuẫn).

## 3. Problem Solving (Kỹ năng giải quyết vấn đề)
- **Xử lý xung đột Class Component (Lỗi AttributeError):** Trong lúc gộp chung code, trình soạn thảo gặp xung đột khiến class giả lập `ExpertEvaluator` đè vào code chính, làm `engine/runner.py` không bắt được object tương ứng và sinh lỗi `AttributeError: 'ExpertEvaluator' object has no attribute 'calculate_hit_rate'`. 
- **Cách giải quyết:** Tôi đã không hoảng loạn thay đổi thư viện gốc (vì file gốc là chuẩn), thay vào đó đọc kỹ static Traceback và thực hiện patching nóng `main.py`, gỡ hoàn toàn các Mock class và khởi tạo lại kết nối engine thật (`RetrievalEvaluator`, `LLMJudge`) thành công mà vẫn giữ nguyên format Output JSON của code mới nhất.

---
*Báo cáo được chuẩn bị để nộp theo cấu trúc yêu cầu của Expert Mission.*
