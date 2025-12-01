# -*- coding:utf-8 -*-
import sys
import os
import uvicorn

# 将项目根目录添加到Python的搜索路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.utils import get_user_settings
from tools.utils import get_version
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Union

settings = get_user_settings()
if settings["DATABASE"] == "mysql" or settings["DATABASE"] == "sqlite":
    from api_dependence.sql.sqlapi import (
        query_all,
        query_friend,
        query_random_friend,
        query_random_post,
        query_post,
        query_summary,
    )
elif settings["DATABASE"] == "mongodb":
    from api_dependence.mongodb.mongodbapi import (
        query_all,
        query_friend,
        query_random_friend,
        query_random_post,
        query_post,
        query_summary,
    )
else:
    raise Exception("DATABASE not supported")

OUTDATE_CLEAN = settings["OUTDATE_CLEAN"]


# Response Models
class StatisticalData(BaseModel):
    """统计数据模型"""

    friends_num: int = Field(..., description="朋友总数", example=34)
    active_num: int = Field(..., description="活跃朋友数", example=19)
    error_num: int = Field(..., description="错误朋友数", example=15)
    article_num: int = Field(..., description="文章总数", example=31)
    last_updated_time: str = Field(
        ..., description="最后更新时间", example="2025-01-01 12:00:00"
    )


class ArticleData(BaseModel):
    """文章数据模型（用于/all接口，包含summary字段）"""

    floor: int = Field(..., description="文章楼层", example=1)
    title: str = Field(
        ..., description="文章标题", example="Wave Terminal 多功能开源终端"
    )
    created: str = Field(..., description="创建时间", example="2025-07-31")
    updated: str = Field(..., description="更新时间", example="2025-07-31")
    link: str = Field(
        ..., description="文章链接", example="https://blog.example.com/post"
    )
    author: str = Field(..., description="作者", example="张三")
    avatar: str = Field(
        ..., description="头像链接", example="https://example.com/avatar.jpg"
    )
    summary: Optional[str] = Field(
        None, description="AI生成摘要", example="这是一篇关于终端工具的文章..."
    )
    ai_model: Optional[str] = Field(None, description="AI模型", example="qwen3")
    summary_created_at: Optional[str] = Field(
        None, description="摘要创建时间", example="2025-01-01 10:00:00"
    )
    summary_updated_at: Optional[str] = Field(
        None, description="摘要更新时间", example="2025-01-01 10:00:00"
    )


class PostArticleData(BaseModel):
    """Post接口文章数据模型"""

    floor: int = Field(..., description="文章楼层", example=1)
    title: str = Field(..., description="文章标题", example="ubuntu桌面版安装字体")
    created: str = Field(..., description="创建时间", example="2025-07-12")
    updated: str = Field(..., description="更新时间", example="2025-07-12")
    link: str = Field(
        ...,
        description="文章链接",
        example="https://blog.ciraos.top/posts/ubuntu/install-fonts",
    )
    author: str = Field(..., description="作者", example="葱苓sama")
    avatar: str = Field(
        ...,
        description="头像链接",
        example="https://cdn.jsdelivr.net/gh/ciraos/ciraos-static@main/img/avatar1.webp",
    )


class RandomPostData(BaseModel):
    """RandomPost接口专用文章数据模型"""

    title: str = Field(
        ...,
        description="文章标题",
        example="利用 Webhook 实现博客自动部署到服务器并通过飞书通知",
    )
    created: str = Field(..., description="创建时间", example="2025-07-05")
    updated: str = Field(..., description="更新时间", example="2025-07-05")
    link: str = Field(
        ..., description="文章链接", example="https://xaoxuu.com/blog/20250705/"
    )
    rule: str = Field(..., description="文章规则", example="feed")
    author: str = Field(..., description="作者", example="xaoxuu")
    avatar: str = Field(
        ...,
        description="头像链接",
        example="https://bu.dusays.com/2021/09/24/2f74810ceb3d3.png",
    )
    createdAt: str = Field(..., description="创建时间", example="2025-07-31 20:09:28")


class AllResponse(BaseModel):
    """全部文章响应模型"""

    statistical_data: StatisticalData
    article_data: List[ArticleData]


class Friend(BaseModel):
    """朋友模型"""

    name: str = Field(..., description="朋友名称", example="白雾茫茫丶")
    link: str = Field(..., description="朋友链接", example="https://blog.xmwpro.com/")
    avatar: str = Field(
        ...,
        description="朋友头像",
        example="https://cyan-blog.oss-cn-shenzhen.aliyuncs.com/global/avatar.jpg",
    )
    error: bool = Field(..., description="是否存在错误", example=True)
    createdAt: str = Field(..., description="创建时间", example="2025-07-31 20:09:31")


class PostStatisticalData(BaseModel):
    """文章统计数据模型"""

    name: str = Field(..., description="朋友名称", example="葱苓sama")
    link: str = Field(..., description="朋友链接", example="https://blog.ciraos.top")
    avatar: str = Field(
        ...,
        description="朋友头像",
        example="https://cdn.jsdelivr.net/gh/ciraos/ciraos-static@main/img/avatar1.webp",
    )
    article_num: int = Field(..., description="文章数量", example=5)


class PostResponse(BaseModel):
    """文章响应模型"""

    statistical_data: PostStatisticalData
    article_data: List[PostArticleData]


class SummaryResponse(BaseModel):
    """摘要响应模型"""

    link: str = Field(..., description="文章链接", example="https://example.com/post")
    summary: str = Field(
        ..., description="AI生成摘要", example="这是一篇关于技术的文章..."
    )
    ai_model: str = Field(..., description="AI模型", example="qwen3")
    content_hash: str = Field(..., description="内容哈希", example="abc123def456")
    created_at: str = Field(..., description="创建时间", example="2025-01-01 10:00:00")
    updated_at: str = Field(..., description="更新时间", example="2025-01-01 10:00:00")


class ErrorResponse(BaseModel):
    """错误响应模型"""

    message: str = Field(
        ...,
        description="错误信息",
        example="rule error, please use 'created'/'updated'",
    )


class NotFoundResponse(BaseModel):
    """未找到响应模型"""

    message: str = Field(..., description="未找到信息", example="not found")


class VersionResponse(BaseModel):
    """版本信息响应模型"""

    version: str = Field(..., description="当前版本号", example="1.0.0")


class IndexResponse(BaseModel):
    """首页响应模型"""

    message: str = Field(..., description="服务状态消息", example="服务运行正常")
    version: str = Field(..., description="当前版本号", example="6.0.5")
    docs: str = Field(..., description="API 文档链接", example="/docs")
    database: str = Field(..., description="数据库类型", example="sqlite")


app = FastAPI(
    title="Hexo Circle of Friends API",
    description="文章和朋友管理API，支持AI生成的文章摘要功能。\n\n支持多种数据库：SQLite、MySQL、MongoDB",
    version="6.0.5",
    docs_url="/docs",
    redoc_url="/redoc",
    contact={
        "name": "Hexo Circle of Friends",
        "url": "https://github.com/Rock-Candy-Tea/hexo-circle-of-friends",
    },
    license_info={
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    },
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get(
    "/all",
    tags=["PUBLIC_API"],
    summary="返回完整统计信息",
    description="获取数据库中的统计信息和文章列表，支持分页和排序",
    response_model=Union[AllResponse, ErrorResponse],
    responses={
        200: {
            "description": "成功返回统计信息和文章列表",
            "model": AllResponse,
            "content": {
                "application/json": {
                    "example": {
                        "statistical_data": {
                            "friends_num": 34,
                            "active_num": 19,
                            "error_num": 15,
                            "article_num": 31,
                            "last_updated_time": "2025-01-01 12:00:00",
                        },
                        "article_data": [
                            {
                                "floor": 1,
                                "title": "Wave Terminal 多功能开源终端",
                                "created": "2025-07-31",
                                "updated": "2025-07-31",
                                "link": "https://blog.example.com/post",
                                "author": "张三",
                                "avatar": "https://example.com/avatar.jpg",
                                "summary": "这是一篇关于终端工具的文章...",
                                "ai_model": "qwen3",
                                "summary_created_at": "2025-01-01 10:00:00",
                                "summary_updated_at": "2025-01-01 10:00:00",
                            }
                        ],
                    }
                }
            },
        },
        400: {
            "description": "请求参数错误",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"message": "rule error, please use 'created'/'updated'"}
                }
            },
        },
        500: {
            "description": "服务器内部错误",
            "model": ErrorResponse,
            "content": {"application/json": {"example": {"message": "数据库连接失败"}}},
        },
    },
)
def all(
    start: int = Query(0, ge=0, description="起始位置，从0开始"),
    end: int = Query(-1, description="结束位置，-1表示不限制"),
    rule: str = Query(
        "updated",
        regex="^(created|updated)$",
        description="排序规则：created(创建时间) 或 updated(更新时间)",
    ),
):
    """
    ## 返回数据库统计信息和文章信息列表

    ### 参数说明
    - **start**: 文章信息列表从按rule排序后的顺序的开始位置
    - **end**: 文章信息列表从按rule排序后的顺序的结束位置
    - **rule**: 文章排序规则（创建时间created/更新时间updated）

    ### 返回数据结构
    - **statistical_data**: 包含朋友数量、活跃数量、错误数量、文章总数等统计信息
    - **article_data**: 文章列表，包含标题、作者、链接、AI摘要等信息
    """
    try:
        list_ = ["title", "created", "updated", "link", "author", "avatar"]
        result = query_all(list_, start, end, rule)

        if isinstance(result, dict) and "message" in result:
            raise HTTPException(status_code=400, detail=result["message"])

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get(
    "/friend",
    tags=["PUBLIC_API"],
    summary="返回所有友链",
    description="获取数据库中所有朋友的链接信息",
    response_model=Union[List[Friend], NotFoundResponse],
    responses={
        200: {
            "description": "成功返回友链列表",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "name": "Jerry",
                            "link": "https://butterfly.js.org/",
                            "avatar": "https://butterfly.js.org/img/avatar.png",
                        },
                        {
                            "name": "Alice",
                            "link": "https://alice.blog/",
                            "avatar": "https://alice.blog/avatar.jpg",
                        },
                    ]
                }
            },
        },
        404: {"description": "未找到友链", "model": NotFoundResponse},
        500: {"description": "服务器内部错误", "model": ErrorResponse},
    },
)
def friend():
    """
    ## 返回数据库友链列表

    获取所有已注册的朋友链接信息，包括名称、链接和头像。
    """
    try:
        result = query_friend()
        if isinstance(result, dict) and "message" in result:
            raise HTTPException(status_code=404, detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get(
    "/randomfriend",
    tags=["PUBLIC_API"],
    summary="返回随机友链",
    description="随机返回指定数量的朋友链接",
    response_model=Union[List[Friend], ErrorResponse],
    responses={
        200: {
            "description": "成功返回随机友链",
            "content": {
                "application/json": {
                    "examples": {
                        "single_friend": {
                            "summary": "返回单个朋友",
                            "value": [
                                {
                                    "name": "白雾茫茫丶",
                                    "link": "https://blog.xmwpro.com/",
                                    "avatar": "https://cyan-blog.oss-cn-shenzhen.aliyuncs.com/global/avatar.jpg",
                                    "error": True,
                                    "createdAt": "2025-07-31 20:09:31",
                                }
                            ],
                        },
                        "multiple_friends": {
                            "summary": "返回多个朋友",
                            "value": [
                                {
                                    "name": "白雾茫茫丶",
                                    "link": "https://blog.xmwpro.com/",
                                    "avatar": "https://cyan-blog.oss-cn-shenzhen.aliyuncs.com/global/avatar.jpg",
                                    "error": True,
                                    "createdAt": "2025-07-31 20:09:31",
                                },
                                {
                                    "name": "CC康纳百川",
                                    "link": "https://blog.ccknbc.cc",
                                    "avatar": "https://cdn.jsdelivr.net/gh/ccknbc-backup/cdn/logo/ccknbc.png",
                                    "error": False,
                                    "createdAt": "2025-07-30 15:30:00",
                                },
                            ],
                        },
                    }
                }
            },
        },
        400: {
            "description": "参数错误",
            "model": ErrorResponse,
            "content": {
                "application/json": {"example": {"message": "param 'num' error"}}
            },
        },
        404: {"description": "未找到友链", "model": NotFoundResponse},
    },
)
def random_friend(num: int = Query(1, ge=1, le=100, description="返回的友链数量")):
    """
    ## 随机返回num个友链信息

    ### 参数说明
    - **num**: 返回的友链数量，1-100之间的整数

    ### 返回规则
    - num=1：返回包含1个友链信息的列表
    - num>1：返回包含num个友链信息的列表
    """
    try:
        result = query_random_friend(num)
        if isinstance(result, dict) and "message" in result:
            if "param" in result["message"]:
                raise HTTPException(status_code=400, detail=result["message"])
            else:
                raise HTTPException(status_code=404, detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get(
    "/randompost",
    tags=["PUBLIC_API"],
    summary="返回随机文章",
    description="随机返回指定数量的文章信息",
    response_model=Union[List[RandomPostData], ErrorResponse],
    responses={
        200: {
            "description": "成功返回随机文章",
            "content": {
                "application/json": {
                    "examples": {
                        "single_post": {
                            "summary": "返回单篇文章",
                            "value": [
                                {
                                    "title": "利用 Webhook 实现博客自动部署到服务器并通过飞书通知",
                                    "created": "2025-07-05",
                                    "updated": "2025-07-05",
                                    "link": "https://xaoxuu.com/blog/20250705/",
                                    "rule": "feed",
                                    "author": "xaoxuu",
                                    "avatar": "https://bu.dusays.com/2021/09/24/2f74810ceb3d3.png",
                                    "createdAt": "2025-07-31 20:09:28",
                                }
                            ],
                        },
                        "multiple_posts": {
                            "summary": "返回多篇文章",
                            "value": [
                                {
                                    "title": "利用 Webhook 实现博客自动部署到服务器并通过飞书通知",
                                    "created": "2025-07-05",
                                    "updated": "2025-07-05",
                                    "link": "https://xaoxuu.com/blog/20250705/",
                                    "rule": "feed",
                                    "author": "xaoxuu",
                                    "avatar": "https://bu.dusays.com/2021/09/24/2f74810ceb3d3.png",
                                    "createdAt": "2025-07-31 20:09:28",
                                },
                                {
                                    "title": "ubuntu桌面版安装字体",
                                    "created": "2025-07-12",
                                    "updated": "2025-07-12",
                                    "link": "https://blog.ciraos.top/posts/ubuntu/install-fonts",
                                    "rule": "feed",
                                    "author": "葱苓sama",
                                    "avatar": "https://cdn.jsdelivr.net/gh/ciraos/ciraos-static@main/img/avatar1.webp",
                                    "createdAt": "2025-07-31 20:09:25",
                                },
                            ],
                        },
                    }
                }
            },
        },
        400: {"description": "参数错误", "model": ErrorResponse},
        404: {"description": "未找到文章", "model": NotFoundResponse},
    },
)
def random_post(num: int = Query(1, ge=1, le=100, description="返回的文章数量")):
    """
    ## 随机返回num篇文章信息

    ### 参数说明
    - **num**: 返回的文章数量，1-100之间的整数

    ### 返回规则
    - num=1：返回包含1篇文章信息的列表
    - num>1：返回包含num篇文章信息的列表
    """
    try:
        result = query_random_post(num)
        if isinstance(result, dict) and "message" in result:
            if "param" in result["message"]:
                raise HTTPException(status_code=400, detail=result["message"])
            else:
                raise HTTPException(status_code=404, detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get(
    "/post",
    tags=["PUBLIC_API"],
    summary="返回指定链接的所有文章",
    description="根据朋友链接获取该朋友的所有文章，支持随机朋友和指定朋友",
    response_model=Union[PostResponse, ErrorResponse],
    responses={
        200: {
            "description": "成功返回文章列表",
            "content": {
                "application/json": {
                    "example": {
                        "statistical_data": {
                            "name": "葱苓sama",
                            "link": "https://blog.ciraos.top",
                            "avatar": "https://cdn.jsdelivr.net/gh/ciraos/ciraos-static@main/img/avatar1.webp",
                            "article_num": 5,
                        },
                        "article_data": [
                            {
                                "floor": 1,
                                "title": "ubuntu桌面版安装字体",
                                "created": "2025-07-12",
                                "updated": "2025-07-12",
                                "link": "https://blog.ciraos.top/posts/ubuntu/install-fonts",
                                "author": "葱苓sama",
                                "avatar": "https://cdn.jsdelivr.net/gh/ciraos/ciraos-static@main/img/avatar1.webp",
                            }
                        ],
                    }
                }
            },
        },
        400: {
            "description": "参数错误",
            "model": ErrorResponse,
            "content": {
                "application/json": {
                    "example": {"message": "rule error, please use 'created'/'updated'"}
                }
            },
        },
        404: {"description": "未找到朋友或文章", "model": NotFoundResponse},
    },
)
def post(
    link: Optional[str] = Query(None, description="朋友链接地址，为空时随机选择"),
    num: int = Query(-1, description="返回文章数量，-1表示返回所有"),
    rule: str = Query(
        "created",
        regex="^(created|updated)$",
        description="排序规则：created(创建时间) 或 updated(更新时间)",
    ),
):
    """
    ## 返回指定链接的数据库内文章信息列表

    ### 参数说明
    - **link**: 朋友链接地址，如果为空则随机选择一个朋友
    - **num**: 返回的文章数量，-1表示返回所有文章
    - **rule**: 文章排序规则（创建时间created/更新时间updated）

    ### 返回数据结构
    - **statistical_data**: 朋友信息，包含名称、链接、头像和文章数量
    - **article_data**: 该朋友的文章列表
    """
    try:
        result = query_post(link, num, rule)
        if isinstance(result, dict) and "message" in result:
            if "rule error" in result["message"]:
                raise HTTPException(status_code=400, detail=result["message"])
            else:
                raise HTTPException(status_code=404, detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get(
    "/summary",
    tags=["PUBLIC_API"],
    summary="返回指定链接的文章摘要",
    description="根据文章链接获取AI生成的文章摘要信息",
    response_model=Union[SummaryResponse, NotFoundResponse, ErrorResponse],
    responses={
        200: {
            "description": "成功返回文章摘要",
            "content": {
                "application/json": {
                    "example": {
                        "link": "https://example.com/post",
                        "summary": "这是一篇关于技术的文章，详细介绍了某个开发工具的使用方法和最佳实践...",
                        "ai_model": "qwen3",
                        "content_hash": "abc123def456789",
                        "created_at": "2025-01-01 10:00:00",
                        "updated_at": "2025-01-01 12:00:00",
                    }
                }
            },
        },
        400: {
            "description": "参数错误",
            "model": ErrorResponse,
            "content": {
                "application/json": {"example": {"message": "链接参数不能为空"}}
            },
        },
        404: {
            "description": "未找到摘要",
            "model": NotFoundResponse,
            "content": {"application/json": {"example": {"message": "not found"}}},
        },
        422: {
            "description": "请求参数验证失败",
            "content": {
                "application/json": {
                    "example": {
                        "detail": [
                            {
                                "loc": ["query", "link"],
                                "msg": "field required",
                                "type": "value_error.missing",
                            }
                        ]
                    }
                }
            },
        },
    },
)
def summary(link: str = Query(..., description="文章链接地址（必填）")):
    """
    ## 返回指定链接的文章摘要信息

    ### 参数说明
    - **link**: 文章链接地址（必填参数）

    ### 返回数据结构
    - **link**: 原文章链接
    - **summary**: AI生成的文章摘要
    - **ai_model**: 使用的AI模型名称
    - **content_hash**: 文章内容哈希值
    - **created_at**: 摘要创建时间
    - **updated_at**: 摘要更新时间
    """
    try:
        result = query_summary(link)
        if isinstance(result, dict) and "message" in result:
            raise HTTPException(status_code=404, detail=result["message"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@app.get(
    "/",
    tags=["SYSTEM"],
    summary="服务状态",
    description="返回服务运行状态信息",
    response_model=IndexResponse,
    responses={
        200: {
            "description": "服务运行正常",
            "content": {
                "application/json": {
                    "example": {
                        "message": "服务运行正常",
                        "version": "6.0.5",
                        "docs": "/docs",
                        "database": "sqlite",
                    }
                }
            },
        }
    },
)
def index():
    """
    ## 服务状态检查

    返回服务的基本信息，用于确认后台服务是否正常运行。

    ### 返回信息包括：
    - **message**: 服务状态消息
    - **version**: 当前版本号
    - **docs**: API文档链接
    - **database**: 使用的数据库类型
    """
    return {
        "message": "服务运行正常",
        "version": get_version()["version"],
        "docs": "/docs",
        "database": settings["DATABASE"],
    }


@app.get(
    "/version",
    tags=["SYSTEM"],
    summary="获取版本信息",
    description="返回当前API服务的版本号",
    response_model=VersionResponse,
    responses={
        200: {
            "description": "成功返回版本信息",
            "content": {"application/json": {"example": {"version": "1.0.0"}}},
        }
    },
)
def get_version_info():
    """
    ## 获取版本信息

    返回当前API服务的版本号，与所有二进制组件使用统一版本。
    """
    return get_version()


if __name__ == "__main__":
    if settings["DEPLOY_TYPE"] == "docker":
        uvicorn.run("vercel:app", host="0.0.0.0")
    elif settings["DEPLOY_TYPE"] == "server":
        EXPOSE_PORT = (
            int(os.environ["EXPOSE_PORT"]) if os.environ.get("EXPOSE_PORT") else 8000
        )
        uvicorn.run("vercel:app", host="0.0.0.0", port=EXPOSE_PORT)
    else:
        uvicorn.run("vercel:app", host="0.0.0.0", reload=True)
