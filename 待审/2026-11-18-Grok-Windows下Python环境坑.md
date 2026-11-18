提交模型：Grok
来源仓库：character-image-staging（另两个图片仓库同步了这条记录）
建议归类：通用
建议新增或修改：在《检查清单》“测试”新增一条：脚本要在用户的 Windows 上也能跑，已知三个坑——`zoneinfo` 需 `pip install tzdata`；Pillow 打开的文件要用 `with Image.open(...)` 关掉再删；Python 直连部分 CDN 超时可改用系统 `curl.exe` 下载。
证据：
- 图片仓库问题记录三条（2026-11-14）：“Windows Python 缺少系统时区导致测试报错”（[b9b93f5](https://github.com/cjhkcjgk3-sys/character-image-staging/commit/b9b93f5)）、“Windows Python 下载特定 CDN 节点超时与 curl.exe 调度”与“Windows 文件系统 Pillow 惰性加载导致句柄占用（WinError 32）”（[4723c49](https://github.com/cjhkcjgk3-sys/character-image-staging/commit/4723c49)）。见 [问题与解决记录](https://github.com/cjhkcjgk3-sys/character-image-staging/blob/main/docs/%E9%97%AE%E9%A2%98%E4%B8%8E%E8%A7%A3%E5%86%B3%E8%AE%B0%E5%BD%95.md)。
