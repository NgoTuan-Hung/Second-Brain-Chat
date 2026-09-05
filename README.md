# 🧠 Floating Desktop AI Companion for Obsidian Second Brain

Ứng dụng Desktop dạng **Floating Overlay Mini Chatbot** (luôn nổi trên màn hình, thiết kế cute, kéo thả/phóng to thu nhỏ linh hoạt, thu gọn thành linh vật / bong bóng tròn) để chat và tự động cập nhật kiến thức, công việc vào **Obsidian Second Brain** mà không cần mở Antigravity IDE hay chuyển tab.

---

## ⚡ Hỗ Trợ Đầy Đủ Antigravity CLI (`agy`) Engine

Dự án đã tích hợp trực tiếp với **`agy`** có sẵn trên máy của bạn:
- 🚀 **Không cần nhập API Key**: Tận dụng phiên đăng nhập và tài nguyên xác thực sẵn có của Antigravity CLI.
- 💎 **Hạn mức (Quota) Dồi dào**: Tận dụng tối đa quota lớn của hệ sinh thái Google Antigravity.
- 🧠 **Sức mạnh từ các Mô hình Hàng đầu**:
  - `gemini-3.8-flash-medium` *(Mặc định - Nhanh & Thông minh vượt trội thế hệ mới)*
  - `gemini-3.8-flash-high` *(Suy luận sâu nhất)*
  - `gemini-3.7-flash-medium`
  - `gemini-3.1-pro-high`
  - `claude-sonnet-4-6` / `claude-opus-4-6-thinking`
  - `gpt-oss-120b-medium`
- 🔄 **Giữ ngữ cảnh hội thoại (Continuous Session)**: Quản lý session ID và streaming token thời gian thực.
- 📁 **Tự động liên kết Vault**: Tự động đưa thư mục Obsidian Vault vào ngữ cảnh (`--add-dir`) để đọc & tạo ghi chú chính xác.

---

## ✨ Tính Năng Nổi Bật

- 🤖 **Floating Mascot & Glassmorphism UI**: Giao diện bo tròn, kính mờ tối màu sang trọng, kéo thả mượt mà, hỗ trợ thu gọn thành bong bóng linh vật (Mascot Chibi) xinh xắn.
- 💬 **Bong Bóng Chat & Trợ Lý Chủ Động (Proactive Companion)** ⭐ *MỚI*:
  - **Speech / Thought Bubble**: Bong bóng thoại mọc trực tiếp từ chú Mascot, tự động đảo chiều theo vị trí trên màn hình, chống tràn mép và có hiệu ứng kính mờ tinh tế.
  - **☀️ Morning Briefing**: Tự động quét Daily note, gom các việc chưa hoàn thành (`- [ ]`) từ hôm trước và nhắc nhở khởi động ngày mới.
  - **💡 Spaced Repetition / "On This Day"**: Khơi gợi lại các ghi chú kiến thức cũ trong Vault để ôn tập nhanh 30s qua quiz/tóm tắt từ AI.
  - **🌙 Evening Reflection**: Nhắc nhở tổng kết ngày và ghi nhanh nhật ký trước khi nghỉ ngơi.
  - **Tương tác 1-chạm**: Bấm vào nút hành động trên bong bóng để tự động mở chat và phân tích công việc tức thì.
- 📌 **Always-on-Top & Global Hotkeys**: Luôn nổi trên mọi ứng dụng với phím tắt toàn hệ thống (mặc định `<Ctrl> + <Shift> + S`).
- 📝 **Tích hợp sâu Obsidian Second Brain**:
  - Ghi nhật ký / log hoạt động vào `Daily/YYYY-MM-DD.md`.
  - Tạo ghi chú kiến thức, ý tưởng mới với YAML frontmatter và `#tags`.
  - Thêm việc cần làm (Todo checkbox `- [ ]`) vào danh sách công việc.
  - Tra cứu và trích xuất nội dung từ Second Brain theo thời gian thực.

---

## 🚀 Hướng Dẫn Chạy Ứng Dụng

Chạy trực tiếp bằng Python / `.venv`:

```bash
# Trong thư mục Second-Brain-Chat:
.venv/bin/python3 main.py
```

---

## ⚙️ Cấu Hình & Tùy Chọn

- Bấm vào biểu tượng ⚙️ (**Cài đặt**) ở thanh tiêu đề hoặc chuột phải vào Mascot.
- Bạn có thể chuyển đổi linh hoạt:
  1. **Engine Antigravity (AGY)** *(Mặc định)*: Chọn giữa các model Gemini 3.7 / Gemini 3.1 Pro / Claude.
  2. **Direct Gemini API**: Nhập `GEMINI_API_KEY` nếu muốn dùng API key riêng.
  3. **Thư mục Obsidian Vault** & **Global Hotkeys**.

---

## ⌨️ Phím Tắt & Thao Tác

| Thao tác | Mô tả |
| :--- | :--- |
| **`Ctrl + Shift + S`** | Bật / tắt hoặc focus nhanh vào cửa sổ Chat |
| **Click vào Mascot** | Mở rộng khung chat đầy đủ từ bong bóng thu nhỏ |
| **Chuột phải vào Mascot** | Mở menu nhanh (Mở chat, Ghi nhanh log, Cài đặt, Thoát) |
| **Kéo thanh tiêu đề** | Di chuyển cửa sổ đến bất kỳ vị trí nào trên màn hình |
| **Kéo góc dưới phải** | Phóng to / thu nhỏ kích thước cửa sổ |
| **Nút ➖** | Thu gọn thành Mascot tròn |
| **Nút 📌** | Bật / tắt chế độ Always on Top |
| **Enter / Shift+Enter** | Gửi tin nhắn / Xuống dòng trong ô nhập |
