# 📬 Demo Multi-Agent Email Digest Processor

## MỤC LỤC

1. [Tổng Quan](#1-tổng-quan)
2. [Nguyên Lý Hoạt Động](#2-nguyên-lý-hoạt-động)
3. [Thư Viện Và Dịch Vụ](#3-thư-viện-và-dịch-vụ)
4. [Cấu Trúc Thư Mục](#4-cấu-trúc-thư-mục)
5. [Hướng Dẫn Chạy](#5-hướng-dẫn-chạy)
6. [Cách Sử Dụng Giao Diện](#6-cách-sử-dụng-giao-diện)
7. [Tùy Chỉnh Nâng Cao](#7-tùy-chỉnh-nâng-cao)
8. [Ví Dụ Sử Dụng](#8-ví-dụ-sử-dụng)

---

## 1. TỔNG QUAN

**Email Digest Processor** là một ứng dụng web **Streamlit** giúp bạn xử lý, tóm tắt và phân loại ưu tiên các email một cách **tự động** thông qua hệ thống **đa-agent**.

Thay vì xử lý thủ công, hệ thống này sử dụng **2 AI agents** hoạt động **song song**:

- **🔵 Summarizer Agent**: Tóm tắt nội dung email bằng tiếng Việt (2-3 câu)
- **🟡 Prioritizer Agent**: Phân loại mức độ ưu tiên (🔴 CAO / 🟡 TRUNG BÌNH / 🟢 THẤP)

Sau đó, các kết quả được **kết hợp** để tạo ra một **email digest hoàn chỉnh** với mức độ ưu tiên rõ ràng.

### ✨ Tính Năng Nổi Bật

- ✅ **Real-time streaming**: Xem từng stage hoàn tất trong real-time
- ✅ **Lập luận AI**: Hiểu tại sao mỗi email được xếp ưu tiên như vậy
- ✅ **Docker containerized**: Dễ deploy, toàn bộ services trong container
- ✅ **Tiếng Việt**: Tóm tắt và prompts 100% tiếng Việt
- ✅ **Giao diện thân thiện**: Streamlit UI đơn giản, dễ sử dụng

---

## 2. NGUYÊN LÝ HOẠT ĐỘNG

Hệ thống hoạt động theo **3 giai đoạn xử lý** (pipeline stages) chạy **tuần tự**:

### 2.1 Quy Trình 3 Stages

```
INPUT EMAILS (JSON)
    ↓
[ORCHESTRATOR] Điều phối pipeline
    ↓
[STAGE 1] SUMMARIZER AGENT  
  - Tóm tắt 2-3 câu bằng tiếng Việt
    ↓
[STAGE 2] PRIORITIZER AGENT
  - Phân loại: 🔴 CAO / 🟡 TRUNG BÌNH / 🟢 THẤP
    ↓
[STAGE 3] ORCHESTRATOR
  - Tổng hợp kết quả → JSON hoàn chỉnh
    ↓
OUTPUT: EMAIL DIGEST JSON
```

### 2.2 Chi Tiết Từng Stage

| Thành phần | Tên | Mục Đích | Output |
|-----------|-----|---------|--------|
| - | **Orchestrator** | **Điều phối toàn bộ pipeline** | - |
| 1 | Summarizer Agent | Tóm tắt emails | Summary VN |
| 2 | Prioritizer Agent | Phân loại ưu tiên | Priority + Arguments |
| 3 | Orchestrator | Tổng hợp kết quả | JSON |

### 2.3 Real-time Streaming

**Bước 1**: Người dùng **nhập emails** (JSON array)

**Bước 2**: Hệ thống **chạy 3 stages tuần tự**
- **STAGE 1**: Summarizer Agent → tóm tắt emails
- **STAGE 2**: Prioritizer Agent → phân loại ưu tiên
- **STAGE 3**: Orchestrator → tổng hợp kết quả

**Bước 3**: **Real-time display** trên Streamlit
- Hiển thị từng stage khi hoàn tất
- Hiện tên agent + action đang thực hiện
- User thấy progress trong real-time

**Bước 4**: **Xem kết quả chi tiết**
- 📊 Stats: Số emails, errors
- 📊 Priority Distribution: Biểu đồ phân bố
- 🤔 Analysis: Summary + Reasoning cho mỗi email

---

## 3. THƯ VIỆN VÀ DỊCH VỤ

### 3.1 Công Nghệ Chính

| Công Nghệ | Phiên Bản | Mục Đích |
|-----------|-----------|---------|
| Python | 3.10+ | Ngôn ngữ lập trình chính |
| FastAPI | Latest | Framework API cho orchestrator |
| Streamlit | Latest | Framework giao diện web |
| LangGraph | Latest | State machine cho pipeline |
| OpenAI API | gpt-4o | AI cho summarizer & prioritizer |
| Docker | Latest | Container orchestration |
| Requests | Latest | HTTP client giữa services |

### 3.2 Dịch Vụ Ngoài

- **🔵 OpenAI API**: Cung cấp gpt-4o cho AI agents
- **🟢 Docker**: Container cho toàn bộ services

### 3.3 File requirements.txt

```
fastapi
uvicorn
langgraph
requests
python-dotenv
openai>=1.0.0
streamlit
pandas
```

---

## 4. CẤU TRÚC THƯ MỤC

```
demo/
│
├── 🐳 docker-compose.yml
│   Cấu hình container (orchestrator, summarizer, prioritizer, streamlit)
│
├── 📦 orchestrator/
│   ├── app.py (FastAPI + LangGraph + streaming endpoint)
│   ├── orchestrator.py (LangGraph state machine)
│   ├── pipeline_stages.py (3 stage implementations)
│   ├── pipeline_utils.py (Utilities)
│   ├── digest_formatters.py (Digest formatting)
│   └── Dockerfile
│
├── 🤖 agents/
│   ├── Dockerfile (Base image cho agents)
│   ├── summarizer/
│   │   ├── app.py (FastAPI, port 8002)
│   │   ├── summarizer.py (Summarization logic)
│   │   ├── models.py
│   │   └── __init__.py
│   │
│   └── prioritizer/
│       ├── app.py (FastAPI, port 8003)
│       ├── prioritizer.py (Prioritization logic)
│       ├── models.py
│       └── __init__.py
│
├── 🔗 shared/
│   ├── base_agent.py (Base class for agents)
│   ├── config.py (Configuration)
│   ├── models.py (Pydantic models: Email, etc)
│   └── utils.py (Utilities)
│
├── 🎨 streamlit/
│   ├── app.py (Streamlit UI, port 8501)
│   └── Dockerfile
│
├── 📧 data/
│   └── sample_emails.json (5 sample Vietnamese emails)
│
├── 📁 output/
│   └── (Generated digests saved here)
│
├── .env.example (Template)
├── README.md (This file)
└── requirements.txt
```

---

## 5. HƯỚNG DẪN CHẠY

### Bước 1: Clone Repository

```bash
cd demo
```

### Bước 2: Thiết Lập API Key

```bash
cp .env.example .env
```

Mở file `.env` và điền:

```env
OPENAI_API_KEY=sk-...your-api-key...
OPENAI_MODEL=gpt-4o
```

**Cách lấy OpenAI API Key:**
1. Đi tới https://platform.openai.com/api-keys
2. Đăng nhập tài khoản OpenAI
3. Click "Create new secret key"
4. Copy và dán vào .env

### Bước 3: Khởi Động Services (Docker)

```bash
# Build + start tất cả containers
docker compose up 

# Kiểm tra status
docker compose ps

# Xem logs
docker compose logs -f
```

Services sẽ chạy ở:
- 🎨 **Streamlit UI**: http://localhost:8501
- 📦 **Orchestrator API**: http://localhost:8000/docs
- ⚙️ **Summarizer**: http://localhost:8002
- ⭐ **Prioritizer**: http://localhost:8003

---

## 6. CÁCH SỬ DỤNG GIAO DIỆN

### 6.1 Input Section

**Bước 1**: Paste emails (JSON array):

```json
[
  {
    "sender": "john@company.com",
    "subject": "Deadline dự án Q2",
    "body": "Cần nộp báo cáo trước thứ 5 EOD...",
    "timestamp": "2026-04-23T10:30:00Z"
  },
  {
    "sender": "hr@company.com",
    "subject": "Đánh giá hiệu suất",
    "body": "Lịch đánh giá đã được cập nhật...",
    "timestamp": "2026-04-23T09:15:00Z"
  }
]
```

**Bước 2**: Validate JSON (tự động)
- ✓ Valid JSON with 5 emails

**Bước 3**: (Optional) Click "👁️ Show Email Preview"

### 6.2 Processing Section

**Click button**: "🚀 Process Emails"

**Xem real-time progress** của mỗi stage

### 6.3 Results Section

Sau processing hoàn tất:

#### 📊 Processing Results
```
📧 Raw Emails: 5
✏️ Summarized: 5
⭐ Prioritized: 5
❌ Errors: 0
```

#### 📊 Priority Distribution
```
🔴 CAO: 3
🟡 TRUNG BÌNH: 1
🟢 THẤP: 1
```

#### 🤔 Email Analysis & Agent Reasoning

Click mỗi email expander:

```
🔴 Deadline dự án Q2 — CAO

📝 Summary:
> Email có từ "KHẨN" thông báo deadline 
  dự án chuyển sang thứ Năm...

─────────

Email Info:
From: john@company.com
Priority: CAO
Reason: Email thông báo thay đổi deadline...

Priority Arguments:

🔴 CAO ✓ (SELECTED)
   Email có từ "KHẨN" trong tiêu đề, 
   thông báo thay đổi deadline cần xử lý ngay...

🟡 TRUNG BÌNH
   Có thể là Trung Bình nếu bạn không 
   tham gia dự án...

🟢 THẤP
   Nội dung không quan trọng nếu bạn 
   không liên quan đến deadline này...
```

---

---

## 7. TÙY CHỈNH NÂNG CAO

### 7.1 Tùy Chỉnh Summarizer Prompt

File: `agents/summarizer/summarizer.py`

```python
system_prompt = """
Bạn là chuyên gia tóm tắt email.
Tóm tắt bằng tiếng Việt:
- 2-3 câu
- Tối đa 150 ký tự
- Giữ lại ý chính
"""
```

### 7.2 Tùy Chỉnh Prioritizer Prompt

File: `agents/prioritizer/prioritizer.py`

```python
system_prompt = """
Bạn là chuyên gia phân loại ưu tiên email.
Xếp hạng: CAO, TRUNG BÌNH, THẤP
Cung cấp: Lý do + Debate arguments
"""
```

### 7.3 Tùy Chỉnh Sample Emails

File: `data/sample_emails.json`

Thêm/xóa/sửa emails tùy ý

### 7.4 Tùy Chỉnh Model

File: `.env`

```env
OPENAI_MODEL=gpt-3.5-turbo    
```

---

## 8. VÍ DỤ SỬ DỤNG

### Kịch Bản Thực Tế

Bạn là quản lý dự án, nhận 5 emails:

1. **Deadline dự án Q2** (john@company.com) → 🔴 CAO
2. **Đánh giá hiệu suất** (hr@company.com) → 🟡 TRUNG BÌNH
3. **Code review đợi** (dev@company.com) → 🔴 CAO
4. **Phê duyệt ngân sách** (finance@company.com) → 🟡 TRUNG BÌNH
5. **Phát hành marketing** (marketing@company.com) → 🔴 CAO

### Workflow

1. **Paste** 5 emails JSON vào Streamlit
2. **Click** "🚀 Process Emails"
3. **Xem** real-time: Stage 1 → 2 → 3 → 4 hoàn tất
4. **Phân tích**: 
   - 3 CAO (xử lý ngay)
   - 2 TRUNG BÌNH
5. **Chi tiết**: Click mỗi email để xem reasoning

### Kết Quả

- 📧 Total: 5 emails
- 📊 CAO: 3, TRUNG BÌNH: 2, THẤP: 0
- 📝 Summaries bằng tiếng Việt
- 🤔 Lập luận (debate) cho mỗi priority level

---

**Cảm ơn bạn đã sử dụng Email Digest Processor!**
