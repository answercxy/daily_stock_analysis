# feishu_doc.py
# -*- coding: utf-8 -*-
"""
飞书云文档管理器 — 使用 requests 直接调用飞书 Open API
替代 lark_oapi SDK（该 SDK 过于臃肿且有循环导入 bug）
"""
import logging
import time
from typing import Optional

import requests

from src.config import get_config

logger = logging.getLogger(__name__)

FEISHU_BASE = "https://open.feishu.cn/open-apis"


class FeishuDocManager:
    """飞书云文档管理器 (基于 requests 直接调用 API)"""

    def __init__(self):
        self.config = get_config()
        self.app_id = self.config.feishu_app_id
        self.app_secret = self.config.feishu_app_secret
        self.folder_token = self.config.feishu_folder_token
        self._token = None
        self._token_expires_at = 0

    def is_configured(self) -> bool:
        """检查配置是否完整"""
        return bool(self.app_id and self.app_secret and self.folder_token)

    def _get_token(self) -> Optional[str]:
        """获取 tenant_access_token（带缓存）"""
        now = time.time()
        if self._token and now < self._token_expires_at - 60:
            return self._token

        try:
            resp = requests.post(
                f"{FEISHU_BASE}/auth/v3/tenant_access_token/internal",
                json={"app_id": self.app_id, "app_secret": self.app_secret},
                timeout=10,
            )
            data = resp.json()
            if data.get("code") != 0:
                logger.error(f"获取飞书 token 失败: {data.get('msg', resp.text)}")
                return None
            self._token = data["tenant_access_token"]
            self._token_expires_at = now + data.get("expire", 7200)
            return self._token
        except Exception as e:
            logger.error(f"获取飞书 token 异常: {e}")
            return None

    def _headers(self) -> dict:
        token = self._get_token()
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

    def create_daily_doc(self, title: str, content_md: str) -> Optional[str]:
        """创建日报文档并写入内容"""
        if not self.is_configured():
            logger.warning("飞书文档配置缺失，跳过创建")
            return None

        token = self._get_token()
        if not token:
            return None

        try:
            # 1. 创建文档
            create_resp = requests.post(
                f"{FEISHU_BASE}/docx/v1/documents",
                headers=self._headers(),
                json={"folder_token": self.folder_token, "title": title},
                timeout=15,
            )
            create_data = create_resp.json()
            if create_data.get("code") != 0:
                logger.error(
                    f"创建飞书文档失败: {create_data.get('msg', create_resp.text)}"
                )
                return None

            doc_id = create_data["data"]["document"]["document_id"]
            doc_url = f"https://feishu.cn/docx/{doc_id}"
            logger.info(f"飞书文档创建成功: {title} (ID: {doc_id})")

            # 2. 将 Markdown 转换为 Block 并分批写入
            blocks = self._markdown_to_blocks(content_md)
            batch_size = 50

            for i in range(0, len(blocks), batch_size):
                batch = blocks[i : i + batch_size]
                add_resp = requests.post(
                    f"{FEISHU_BASE}/docx/v1/documents/{doc_id}/blocks/{doc_id}/children",
                    headers=self._headers(),
                    json={"children": batch, "index": -1},
                    timeout=15,
                )
                add_data = add_resp.json()
                if add_data.get("code") != 0:
                    logger.error(
                        f"写入文档内容失败(批次{i}): {add_data.get('msg', add_resp.text)}"
                    )

            logger.info("文档内容写入完成")
            return doc_url

        except Exception as e:
            logger.error(f"飞书文档操作异常: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    def _markdown_to_blocks(self, md_text: str) -> list:
        """将 Markdown 文本转换为飞书 Block 列表"""
        blocks = []

        # Block type 常量
        TEXT = 2
        H1 = 3
        H2 = 4
        H3 = 5
        H4 = 6
        DIVIDER = 22

        for line in md_text.split("\n"):
            stripped = line.strip()
            if not stripped:
                continue

            block_type = TEXT
            text_content = stripped

            if stripped.startswith("# "):
                block_type = H1
                text_content = stripped[2:]
            elif stripped.startswith("## "):
                block_type = H2
                text_content = stripped[3:]
            elif stripped.startswith("### "):
                block_type = H3
                text_content = stripped[4:]
            elif stripped.startswith("#### "):
                block_type = H4
                text_content = stripped[5:]
            elif stripped == "---":
                blocks.append(
                    {
                        "block_type": DIVIDER,
                        "divider": {},
                    }
                )
                continue

            # 构造 text block
            block = {
                "block_type": block_type,
            }

            text_obj = {
                "elements": [
                    {
                        "text_run": {
                            "content": text_content,
                            "text_element_style": {},
                        }
                    }
                ],
                "style": {},
            }

            if block_type == TEXT:
                block["text"] = text_obj
            elif block_type == H1:
                block["heading1"] = text_obj
            elif block_type == H2:
                block["heading2"] = text_obj
            elif block_type == H3:
                block["heading3"] = text_obj
            elif block_type == H4:
                block["heading4"] = text_obj

            blocks.append(block)

        return blocks
