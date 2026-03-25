# 动漫序列推荐网站实施计划（可部署版）

**Summary**
- 在现有模型与最小推荐服务基础上，扩展为“可用网站”，包含前端 Vue3、后端 FastAPI 完整业务、SQLite 用户系统与推荐展示、部署方案与测试验收。
- 目标：可让用户注册/登录、输入或自动记录观看历史、查看推荐列表与动漫详情，服务稳定可部署。

**Key Changes / Implementation**
1. **Backend（FastAPI）**
   - **服务结构化**：拆分为 `api/`、`services/`、`db/`、`schemas/`、`config/`，统一配置来源（env + config.yaml）。
   - **数据库层**
     - 继续使用 SQLite，新增用户与行为表：
       - `users(id, username, password_hash, created_at)`
       - `user_history(id, user_id, anime_id, watched_at)`
       - `user_favorites(id, user_id, anime_id, created_at)`
     - 动漫数据表沿用 `anime`（已存在于 `data/anime.db`）。
   - **认证与会话**
     - JWT 登录（`/auth/register`, `/auth/login`），使用 `passlib[bcrypt]` 加密密码。
     - 受保护接口需带 `Authorization: Bearer <token>`.
   - **核心 API**
     - `POST /recommend`：输入 `raw_anime_history` + `top_k`，返回推荐列表（含元数据）。
     - `GET /anime/{anime_id}`：返回动漫详情。
     - `GET /me/history`：当前用户历史。
     - `POST /me/history`：追加历史（用户看过的）。
     - `GET /me/favorites` / `POST /me/favorites` / `DELETE /me/favorites/{anime_id}`。
     - `GET /health`：模型加载状态、DB连接、版本。
   - **推理服务化**
     - 启动时加载 `model.onnx` 与映射表。
     - 推理逻辑独立模块，避免重复加载。
   - **CORS**
     - 允许前端域名（开发时 `localhost:5173`）。

2. **Frontend（Vue 3 + Vite）**
   - **页面与功能**
     - 首页：输入/选择观看历史 + 推荐按钮。
     - 推荐结果页：展示推荐卡片（名称/类型/评分/封面）。
     - 动漫详情弹窗/页面：`GET /anime/{id}`。
     - 登录/注册页。
     - 个人中心：历史记录、收藏夹。
   - **状态管理**：Pinia 保存登录状态、历史、收藏。
   - **请求层**：Axios + 统一错误处理（401 自动跳转登录）。
   - **UI 方向**：清晰卡片式布局，强调“推荐列表”可视化。

3. **Deployment（学校/实验室服务器）**
   - **默认方案：单机部署**
     - `uvicorn` 启动后端服务 + `nginx` 反向代理（如果能装）。
     - 前端构建后静态文件由 `nginx` 或 FastAPI `StaticFiles` 托管。
   - **备选方案：Docker Compose**
     - `backend`（FastAPI + uvicorn）
     - `frontend`（静态构建）
     - `nginx`（可选）
   - **配置管理**
     - `.env` 控制 DB 路径、模型路径、JWT 密钥、CORS 域名。

**Public API / Interface Changes**
- 新增认证与用户接口（`/auth/*`, `/me/*`）。
- 推荐接口输出升级：返回 `anime_id + name + genre + rating + type` 等元信息。

**Test Plan**
- **后端**
  - `POST /recommend` 基于 `sample_request.json` 回归测试。
  - 登录/注册/收藏/历史接口的正反例测试。
  - 数据库表结构与数据完整性校验。
- **前端**
  - 登录流程、推荐流程、收藏操作的页面验收。
- **部署**
  - 服务器启动后，浏览器直接访问验证全链路。

**Assumptions**
- 部署服务器可运行 Python 环境；如果允许安装 Nginx，优先 Nginx。
- SQLite 足够满足初期并发（单机小规模用户）。
- 暂不做推荐模型在线更新（模型为静态文件）。
