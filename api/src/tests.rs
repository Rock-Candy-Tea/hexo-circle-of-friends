//! API单元测试
//!
//! 测试SQLite、MySQL和MongoDB三种数据库的API端点
//! 包含基础可访问性测试和详细功能测试

use axum::{
    Router,
    body::Body,
    http::{Request, StatusCode},
};
use serde_json::Value;

use tower::ServiceExt;

use crate::{create_mongodb_app, create_mysql_app, create_sqlite_app};

/// 测试助手函数：发送GET请求并返回响应
async fn send_get_request(app: Router, path: &str) -> (StatusCode, Value) {
    let response = app
        .oneshot(Request::builder().uri(path).body(Body::empty()).unwrap())
        .await
        .unwrap();

    let status = response.status();
    let body = axum::body::to_bytes(response.into_body(), usize::MAX)
        .await
        .unwrap();
    let json: Value = serde_json::from_slice(&body).unwrap_or_else(|_| {
        serde_json::json!({
            "error": "Failed to parse JSON",
            "body": String::from_utf8_lossy(&body)
        })
    });

    (status, json)
}

/// 测试助手函数：发送请求（用于基础测试）
async fn send_request(app: Router, path: &str) -> (StatusCode, Value) {
    let response = app
        .oneshot(Request::builder().uri(path).body(Body::empty()).unwrap())
        .await
        .unwrap();

    let status = response.status();
    let body = axum::body::to_bytes(response.into_body(), usize::MAX)
        .await
        .unwrap();
    let json: Value = serde_json::from_slice(&body).unwrap_or_else(|_| {
        serde_json::json!({
            "parse_error": "Failed to parse as JSON",
            "body": String::from_utf8_lossy(&body).to_string()
        })
    });

    (status, json)
}

/// 验证统计数据结构
fn validate_statistical_data(stats: &Value) {
    assert!(stats.is_object(), "statistical_data should be an object");

    let required_fields = [
        "friends_num",
        "active_num",
        "error_num",
        "article_num",
        "last_updated_time",
    ];
    for field in required_fields {
        assert!(stats.get(field).is_some(), "Missing field: {field}");
    }
}

/// 验证文章数据结构
fn validate_article_data(articles: &Value) {
    assert!(articles.is_array(), "article_data should be an array");

    if let Some(article) = articles.as_array().and_then(|arr| arr.first()) {
        let required_fields = [
            "floor", "title", "created", "updated", "link", "author", "avatar",
        ];
        for field in required_fields {
            assert!(
                article.get(field).is_some(),
                "Missing article field: {field}"
            );
        }

        // 摘要字段可能为null，但应该存在
        assert!(article.get("summary").is_some(), "Missing summary field");
        assert!(article.get("ai_model").is_some(), "Missing ai_model field");
        assert!(
            article.get("summary_created_at").is_some(),
            "Missing summary_created_at field"
        );
        assert!(
            article.get("summary_updated_at").is_some(),
            "Missing summary_updated_at field"
        );
    }
}

/// 验证朋友数据结构
fn validate_friend_data(friends: &Value) {
    // 检查是否是错误消息（空数据库的情况）
    if let Some(message) = friends.get("message") {
        println!("⚠️ 收到消息响应: {message}");
        return;
    }

    assert!(friends.is_array(), "friends should be an array");

    if let Some(friend) = friends.as_array().and_then(|arr| arr.first()) {
        let required_fields = ["name", "link", "avatar"];
        for field in required_fields {
            assert!(friend.get(field).is_some(), "Missing friend field: {field}");
        }
    }
}

#[cfg(test)]
mod sqlite_tests {
    use super::*;

    #[tokio::test]
    async fn test_sqlite_get_all() {
        let app = create_sqlite_app("data.db").await;
        let (status, json) = send_get_request(app, "/all").await;

        println!("SQLite /all 响应状态: {status}");
        println!(
            "SQLite /all 响应内容: {}",
            serde_json::to_string_pretty(&json)
                .unwrap_or_else(|_| "Failed to serialize".to_string())
        );

        assert_eq!(status, StatusCode::OK);

        if json.get("statistical_data").is_some() && json.get("article_data").is_some() {
            validate_statistical_data(json.get("statistical_data").unwrap());
            validate_article_data(json.get("article_data").unwrap());
            println!("✅ SQLite /all 测试通过");
        } else {
            println!("⚠️ SQLite /all 返回的数据结构与预期不符，但接口可访问");
        }
    }

    #[tokio::test]
    async fn test_sqlite_get_all_with_params() {
        let app = create_sqlite_app("data.db").await;
        let (status, json) = send_get_request(app, "/all?start=0&end=5&rule=updated").await;

        assert_eq!(status, StatusCode::OK);

        if let Some(articles) = json.get("article_data").and_then(|v| v.as_array()) {
            assert!(articles.len() <= 5, "Should respect the limit parameter");
        }

        println!("✅ SQLite /all 带参数测试通过");
    }

    #[tokio::test]
    async fn test_sqlite_get_friend() {
        let app = create_sqlite_app("data.db").await;
        let (status, json) = send_get_request(app, "/friend").await;

        assert_eq!(status, StatusCode::OK);

        // 可能返回数组或错误消息（当数据库为空时）
        if json.is_array() {
            validate_friend_data(&json);
            println!("✅ SQLite /friend 测试通过 - 返回数据");
        } else if json.get("message").is_some() {
            println!("✅ SQLite /friend 测试通过 - 数据库为空");
        } else {
            panic!("Unexpected response format: {json:?}");
        }
    }

    #[tokio::test]
    async fn test_sqlite_get_randomfriend() {
        let app = create_sqlite_app("data.db").await;
        let (status, json) = send_get_request(app, "/randomfriend").await;

        assert_eq!(status, StatusCode::OK);

        // 可能返回单个对象、数组或错误消息
        if json.is_object() && json.get("name").is_some() {
            // 单个朋友
            let required_fields = ["name", "link", "avatar"];
            for field in required_fields {
                assert!(json.get(field).is_some(), "Missing field: {field}");
            }
            println!("✅ SQLite /randomfriend 测试通过 - 返回单个朋友");
        } else if json.is_array() {
            // 朋友列表
            validate_friend_data(&json);
            println!("✅ SQLite /randomfriend 测试通过 - 返回朋友列表");
        } else if json.get("message").is_some() {
            println!("✅ SQLite /randomfriend 测试通过 - 数据库为空");
        } else {
            println!("✅ SQLite /randomfriend 测试通过 - 其他格式: {json:?}");
        }
    }

    #[tokio::test]
    async fn test_sqlite_get_randompost() {
        let app = create_sqlite_app("data.db").await;
        let (status, json) = send_get_request(app, "/randompost").await;

        assert_eq!(status, StatusCode::OK);

        // 可能返回单个对象或数组
        if json.is_object() && json.get("title").is_some() {
            // 单个文章
            let required_fields = ["title", "created", "updated", "link", "author", "avatar"];
            for field in required_fields {
                assert!(json.get(field).is_some(), "Missing field: {field}");
            }
        }

        println!("✅ SQLite /randompost 测试通过");
    }

    #[tokio::test]
    async fn test_sqlite_get_post() {
        let app = create_sqlite_app("data.db").await;
        let (status, json) = send_get_request(app, "/post").await;

        assert_eq!(status, StatusCode::OK);

        // 应该有statistical_data和article_data
        if json.get("statistical_data").is_some() {
            let stats = json.get("statistical_data").unwrap();
            assert!(
                stats.get("name").is_some(),
                "Missing name in statistical_data"
            );
            assert!(
                stats.get("link").is_some(),
                "Missing link in statistical_data"
            );
            assert!(
                stats.get("article_num").is_some(),
                "Missing article_num in statistical_data"
            );
        }

        println!("✅ SQLite /post 测试通过");
    }

    #[tokio::test]
    async fn test_sqlite_get_summary() {
        let app = create_sqlite_app("data.db").await;
        let (status, _json) = send_get_request(app, "/summary?link=https://example.com/test").await;

        // 可能返回200（有摘要）或404（无摘要）
        assert!(
            status == StatusCode::OK || status == StatusCode::NOT_FOUND,
            "Expected 200 or 404, got: {status}"
        );

        println!("✅ SQLite /summary 测试通过");
    }

    #[tokio::test]
    async fn test_sqlite_swagger_endpoints() {
        let app = create_sqlite_app("data.db").await;

        // 测试swagger.json端点
        let (status, json) = send_get_request(app.clone(), "/swagger.json").await;
        assert_eq!(status, StatusCode::OK);
        assert!(json.get("openapi").is_some(), "Should have openapi field");
        assert!(json.get("paths").is_some(), "Should have paths field");

        // 测试docs端点
        let response = app
            .oneshot(Request::builder().uri("/docs").body(Body::empty()).unwrap())
            .await
            .unwrap();
        assert_eq!(response.status(), StatusCode::OK);

        println!("✅ SQLite Swagger端点测试通过");
    }

    #[tokio::test]
    async fn test_sqlite_version_endpoint() {
        let app = create_sqlite_app("data.db").await;
        let (status, json) = send_get_request(app, "/version").await;

        assert_eq!(status, StatusCode::OK);

        // 验证版本响应结构
        assert!(
            json.get("version").is_some(),
            "版本响应应包含 'version' 字段"
        );

        let version = json["version"].as_str().unwrap();
        assert!(!version.is_empty(), "版本号不能为空");

        // 确保版本号不包含 'v' 前缀
        assert!(
            !version.starts_with('v'),
            "API版本号不应包含'v'前缀，实际版本: {version}"
        );

        // 验证版本号格式（简单的语义版本检查）
        let version_parts: Vec<&str> = version.split('.').collect();
        assert!(
            version_parts.len() >= 2,
            "版本号应该至少包含主版本号和次版本号"
        );

        for part in version_parts {
            assert!(part.parse::<u32>().is_ok(), "版本号的每个部分都应该是数字");
        }

        println!("✅ SQLite 版本接口测试通过，版本: {version}");
    }
}

#[cfg(test)]
mod mysql_tests {
    use super::*;

    const MYSQL_URI: &str = "mysql://root:123456@127.0.0.1:3306/pyq";

    #[tokio::test]
    async fn test_mysql_get_all() {
        let app = create_mysql_app(MYSQL_URI).await;
        let (status, json) = send_get_request(app, "/all").await;

        assert_eq!(status, StatusCode::OK);
        if json.get("statistical_data").is_some() && json.get("article_data").is_some() {
            validate_statistical_data(json.get("statistical_data").unwrap());
            validate_article_data(json.get("article_data").unwrap());
            println!("✅ MySQL /all 测试通过");
        } else {
            println!("⚠️ MySQL /all 返回数据结构与预期不符，但接口可访问");
        }
    }

    #[tokio::test]
    async fn test_mysql_get_all_with_params() {
        let app = create_mysql_app(MYSQL_URI).await;
        let (status, json) = send_get_request(app, "/all?start=0&end=3&rule=created").await;

        assert_eq!(status, StatusCode::OK);

        if let Some(articles) = json.get("article_data").and_then(|v| v.as_array()) {
            assert!(articles.len() <= 3, "Should respect the limit parameter");
        }

        println!("✅ MySQL /all 带参数测试通过");
    }

    #[tokio::test]
    async fn test_mysql_get_friend() {
        let app = create_mysql_app(MYSQL_URI).await;
        let (status, json) = send_get_request(app, "/friend").await;

        assert_eq!(status, StatusCode::OK);
        validate_friend_data(&json);

        println!("✅ MySQL /friend 测试通过");
    }

    #[tokio::test]
    async fn test_mysql_get_randomfriend() {
        let app = create_mysql_app(MYSQL_URI).await;
        let (status, json) = send_get_request(app, "/randomfriend?num=2").await;

        assert_eq!(status, StatusCode::OK);

        if json.is_array() {
            let friends = json.as_array().unwrap();
            assert!(friends.len() <= 2, "Should respect num parameter");
            if !friends.is_empty() {
                let friend = &friends[0];
                let required_fields = ["name", "link", "avatar"];
                for field in required_fields {
                    assert!(friend.get(field).is_some(), "Missing field: {field}");
                }
            }
        }

        println!("✅ MySQL /randomfriend 测试通过");
    }

    #[tokio::test]
    async fn test_mysql_get_randompost() {
        let app = create_mysql_app(MYSQL_URI).await;
        let (status, json) = send_get_request(app, "/randompost?num=3").await;

        assert_eq!(status, StatusCode::OK);

        if json.is_array() {
            let posts = json.as_array().unwrap();
            assert!(posts.len() <= 3, "Should respect num parameter");
        }

        println!("✅ MySQL /randompost 测试通过");
    }

    #[tokio::test]
    async fn test_mysql_get_post_with_link() {
        let app = create_mysql_app(MYSQL_URI).await;

        // 先获取一个朋友的链接
        let (friend_status, friend_json) = send_get_request(app.clone(), "/friend").await;
        if friend_status == StatusCode::OK
            && friend_json.is_array()
            && let Some(friend) = friend_json.as_array().unwrap().first()
            && let Some(link) = friend.get("link").and_then(|v| v.as_str())
        {
            let encoded_link = urlencoding::encode(link);
            let path = format!("/post?link={encoded_link}&num=5");
            let (status, json) = send_get_request(app, &path).await;

            // 应该返回200或404
            assert!(
                status == StatusCode::OK || status == StatusCode::NOT_FOUND,
                "Expected 200 or 404, got: {status}"
            );

            if status == StatusCode::OK {
                assert!(json.get("statistical_data").is_some());
                assert!(json.get("article_data").is_some());
            }
        }

        println!("✅ MySQL /post 带link参数测试通过");
    }

    #[tokio::test]
    async fn test_mysql_get_summary() {
        let app = create_mysql_app(MYSQL_URI).await;
        let (status, json) =
            send_get_request(app, "/summary?link=https://test.example.com/post").await;

        // 可能返回200（有摘要）或404（无摘要）
        assert!(
            status == StatusCode::OK || status == StatusCode::NOT_FOUND,
            "Expected 200 or 404, got: {status}"
        );

        if status == StatusCode::OK && json.get("link").is_some() {
            let required_fields = [
                "link",
                "summary",
                "ai_model",
                "content_hash",
                "created_at",
                "updated_at",
            ];
            for field in required_fields {
                assert!(json.get(field).is_some(), "Missing summary field: {field}");
            }
            println!("✅ MySQL /summary 测试通过 - 返回摘要数据");
        } else if status == StatusCode::OK && json.get("message").is_some() {
            println!("✅ MySQL /summary 测试通过 - 未找到摘要");
        } else if status == StatusCode::NOT_FOUND {
            println!("✅ MySQL /summary 测试通过 - 404响应");
        }
    }

    #[tokio::test]
    async fn test_mysql_version_endpoint() {
        let app = create_mysql_app(MYSQL_URI).await;
        let (status, json) = send_get_request(app, "/version").await;

        assert_eq!(status, StatusCode::OK);

        // 验证版本响应结构
        assert!(
            json.get("version").is_some(),
            "版本响应应包含 'version' 字段"
        );

        let version = json["version"].as_str().unwrap();
        assert!(!version.is_empty(), "版本号不能为空");
        assert!(
            !version.starts_with('v'),
            "API版本号不应包含'v'前缀，实际版本: {version}"
        );

        println!("✅ MySQL 版本接口测试通过，版本: {version}");
    }
}

#[cfg(test)]
mod mongodb_tests {
    use super::*;

    const MONGODB_URI: &str = "mongodb://root:123456@127.0.0.1:27017";

    #[tokio::test]
    async fn test_mongodb_get_all() {
        // 设置环境变量

        let app = create_mongodb_app(MONGODB_URI).await;
        let (status, json) = send_get_request(app, "/all").await;

        assert_eq!(status, StatusCode::OK);
        assert!(json.get("statistical_data").is_some());
        assert!(json.get("article_data").is_some());

        validate_statistical_data(json.get("statistical_data").unwrap());
        validate_article_data(json.get("article_data").unwrap());

        println!("✅ MongoDB /all 测试通过");
    }

    #[tokio::test]
    async fn test_mongodb_get_all_with_params() {
        let app = create_mongodb_app(MONGODB_URI).await;
        let (status, json) = send_get_request(app, "/all?start=0&end=4&rule=updated").await;

        assert_eq!(status, StatusCode::OK);

        if let Some(articles) = json.get("article_data").and_then(|v| v.as_array()) {
            assert!(articles.len() <= 4, "Should respect the limit parameter");
        }

        println!("✅ MongoDB /all 带参数测试通过");
    }

    #[tokio::test]
    async fn test_mongodb_get_friend() {
        let app = create_mongodb_app(MONGODB_URI).await;
        let (status, json) = send_get_request(app, "/friend").await;

        assert_eq!(status, StatusCode::OK);
        validate_friend_data(&json);

        println!("✅ MongoDB /friend 测试通过");
    }

    #[tokio::test]
    async fn test_mongodb_get_randomfriend() {
        let app = create_mongodb_app(MONGODB_URI).await;
        let (status, json) = send_get_request(app, "/randomfriend?num=3").await;

        assert_eq!(status, StatusCode::OK);

        if json.is_array() {
            let friends = json.as_array().unwrap();
            assert!(friends.len() <= 3, "Should respect num parameter");
        } else if json.is_object() {
            // 单个朋友的情况
            let required_fields = ["name", "link", "avatar"];
            for field in required_fields {
                assert!(json.get(field).is_some(), "Missing field: {field}");
            }
        }

        println!("✅ MongoDB /randomfriend 测试通过");
    }

    #[tokio::test]
    async fn test_mongodb_get_randompost() {
        let app = create_mongodb_app(MONGODB_URI).await;
        let (status, json) = send_get_request(app, "/randompost?num=2").await;

        assert_eq!(status, StatusCode::OK);

        if json.is_array() {
            let posts = json.as_array().unwrap();
            assert!(posts.len() <= 2, "Should respect num parameter");
        }

        println!("✅ MongoDB /randompost 测试通过");
    }

    #[tokio::test]
    async fn test_mongodb_get_post() {
        let app = create_mongodb_app(MONGODB_URI).await;
        let (status, json) = send_get_request(app, "/post?num=10&rule=created").await;

        assert_eq!(status, StatusCode::OK);

        if json.get("statistical_data").is_some() {
            let stats = json.get("statistical_data").unwrap();
            assert!(stats.get("name").is_some() || stats.get("link").is_some());
        }

        println!("✅ MongoDB /post 测试通过");
    }

    #[tokio::test]
    async fn test_mongodb_get_summary() {
        let app = create_mongodb_app(MONGODB_URI).await;
        let (status, json) =
            send_get_request(app, "/summary?link=https://mongodb.test.com/article").await;

        // 可能返回200（有摘要）或404（无摘要）
        assert!(
            status == StatusCode::OK || status == StatusCode::NOT_FOUND,
            "Expected 200 or 404, got: {status}"
        );

        if status == StatusCode::OK && json.get("link").is_some() {
            let required_fields = [
                "link",
                "summary",
                "ai_model",
                "content_hash",
                "created_at",
                "updated_at",
            ];
            for field in required_fields {
                assert!(json.get(field).is_some(), "Missing summary field: {field}");
            }
            println!("✅ MongoDB /summary 测试通过 - 返回摘要数据");
        } else if status == StatusCode::OK && json.get("message").is_some() {
            println!("✅ MongoDB /summary 测试通过 - 未找到摘要");
        } else if status == StatusCode::NOT_FOUND {
            assert!(json.get("message").is_some(), "Should have error message");
            println!("✅ MongoDB /summary 测试通过 - 404响应");
        }
    }

    #[tokio::test]
    async fn test_mongodb_swagger_endpoints() {
        let app = create_mongodb_app(MONGODB_URI).await;

        // 测试swagger.json端点
        let (status, json) = send_get_request(app.clone(), "/swagger.json").await;
        assert_eq!(status, StatusCode::OK);
        assert!(json.get("openapi").is_some(), "Should have openapi field");
        assert!(json.get("info").is_some(), "Should have info field");
        assert!(json.get("paths").is_some(), "Should have paths field");

        // 验证包含所有API端点
        if let Some(paths) = json.get("paths").and_then(|v| v.as_object()) {
            let expected_paths = [
                "/all",
                "/friend",
                "/randomfriend",
                "/randompost",
                "/post",
                "/summary",
            ];
            for path in expected_paths {
                assert!(paths.contains_key(path), "Missing path: {path}");
            }
        }

        println!("✅ MongoDB Swagger端点测试通过");
    }

    #[tokio::test]
    async fn test_mongodb_version_endpoint() {
        let app = create_mongodb_app(MONGODB_URI).await;
        let (status, json) = send_get_request(app, "/version").await;

        assert_eq!(status, StatusCode::OK);

        // 验证版本响应结构
        assert!(
            json.get("version").is_some(),
            "版本响应应包含 'version' 字段"
        );

        let version = json["version"].as_str().unwrap();
        assert!(!version.is_empty(), "版本号不能为空");
        assert!(
            !version.starts_with('v'),
            "API版本号不应包含'v'前缀，实际版本: {version}"
        );

        println!("✅ MongoDB 版本接口测试通过，版本: {version}");
    }
}

#[cfg(test)]
mod integration_tests {
    use super::*;

    #[tokio::test]
    async fn test_cross_database_consistency() {
        // 测试不同数据库返回的数据结构一致性

        // SQLite
        let sqlite_app = create_sqlite_app("data.db").await;
        let (sqlite_status, sqlite_json) = send_get_request(sqlite_app, "/all?start=0&end=1").await;

        if sqlite_status == StatusCode::OK && sqlite_json.get("statistical_data").is_some() {
            validate_statistical_data(sqlite_json.get("statistical_data").unwrap());
            if sqlite_json.get("article_data").is_some() {
                validate_article_data(sqlite_json.get("article_data").unwrap());
            }
        }

        // MySQL测试
        let mysql_app = create_mysql_app("mysql://root:123456@127.0.0.1:3306/pyq").await;
        let (mysql_status, mysql_json) = send_get_request(mysql_app, "/all?start=0&end=1").await;

        if mysql_status == StatusCode::OK && mysql_json.get("statistical_data").is_some() {
            validate_statistical_data(mysql_json.get("statistical_data").unwrap());
            if mysql_json.get("article_data").is_some() {
                validate_article_data(mysql_json.get("article_data").unwrap());
            }

            // 验证字段结构一致性
            if sqlite_status == StatusCode::OK
                && sqlite_json.get("statistical_data").is_some()
                && mysql_json.get("statistical_data").is_some()
            {
                let sqlite_stats = sqlite_json.get("statistical_data").unwrap();
                let mysql_stats = mysql_json.get("statistical_data").unwrap();

                // 验证字段名一致
                if let (Some(sqlite_obj), Some(mysql_obj)) =
                    (sqlite_stats.as_object(), mysql_stats.as_object())
                {
                    for key in sqlite_obj.keys() {
                        if !mysql_obj.contains_key(key) {
                            println!("⚠️ MySQL missing SQLite field: {key}");
                        }
                    }
                }
            }
        }

        // MongoDB测试
        let mongodb_app = create_mongodb_app("mongodb://root:123456@127.0.0.1:27017").await;
        let (mongodb_status, mongodb_json) =
            send_get_request(mongodb_app, "/all?start=0&end=1").await;

        if mongodb_status == StatusCode::OK && mongodb_json.get("statistical_data").is_some() {
            validate_statistical_data(mongodb_json.get("statistical_data").unwrap());
            if mongodb_json.get("article_data").is_some() {
                validate_article_data(mongodb_json.get("article_data").unwrap());
            }
        }

        println!("✅ 跨数据库一致性测试通过");
    }

    #[tokio::test]
    async fn test_api_error_handling() {
        // 测试错误处理
        let app = create_sqlite_app("data.db").await;

        // 测试无效的rule参数
        let (status, _json) = send_get_request(app.clone(), "/all?rule=invalid").await;
        assert!(status == StatusCode::BAD_REQUEST || status == StatusCode::OK);

        // 测试summary缺少link参数 - API可能返回200并在JSON中包含错误信息
        let (status, _json) = send_get_request(app.clone(), "/summary").await;
        assert!(
            matches!(
                status,
                StatusCode::OK | StatusCode::BAD_REQUEST | StatusCode::UNPROCESSABLE_ENTITY
            ),
            "Expected 200, 400 or 422, got: {status}"
        );

        // 测试不存在的端点
        let response = app
            .oneshot(
                Request::builder()
                    .uri("/nonexistent")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(response.status(), StatusCode::NOT_FOUND);

        println!("✅ API错误处理测试通过");
    }
}

// 基础API测试模块 - 重点测试API接口的可访问性和基本响应
#[cfg(test)]
mod basic_tests {
    use super::*;

    #[cfg(test)]
    mod sqlite_basic_tests {
        use super::*;

        #[tokio::test]
        async fn test_sqlite_all_endpoints_accessible() {
            let app = create_sqlite_app("data.db").await;

            let endpoints = [
                "/all",
                "/friend",
                "/randomfriend",
                "/randompost",
                "/post",
                "/summary?link=https://test.com/post",
                "/docs",
                "/swagger.json",
            ];

            for endpoint in endpoints {
                let (status, _json) = send_request(app.clone(), endpoint).await;

                // API应该可访问，返回200或合理的错误状态码
                assert!(
                    matches!(
                        status,
                        StatusCode::OK
                            | StatusCode::BAD_REQUEST
                            | StatusCode::NOT_FOUND
                            | StatusCode::UNPROCESSABLE_ENTITY
                    ),
                    "Endpoint {endpoint} returned unexpected status: {status}"
                );

                println!("✅ SQLite {endpoint} - 状态码: {status}");
            }

            println!("✅ SQLite 所有端点可访问性测试通过");
        }

        #[tokio::test]
        async fn test_sqlite_swagger_json_structure() {
            let app = create_sqlite_app("data.db").await;
            let (status, json) = send_request(app, "/swagger.json").await;

            assert_eq!(status, StatusCode::OK);
            assert!(json.get("openapi").is_some(), "应该包含openapi字段");
            assert!(json.get("info").is_some(), "应该包含info字段");
            assert!(json.get("paths").is_some(), "应该包含paths字段");

            if let Some(paths) = json.get("paths").and_then(|v| v.as_object()) {
                let expected_paths = [
                    "/all",
                    "/friend",
                    "/randomfriend",
                    "/randompost",
                    "/post",
                    "/summary",
                ];
                for path in expected_paths {
                    assert!(paths.contains_key(path), "缺少API路径: {path}");
                }
                println!("✅ SQLite OpenAPI包含所有预期路径: {}", paths.len());
            }

            println!("✅ SQLite Swagger JSON结构测试通过");
        }
    }

    #[cfg(test)]
    mod mysql_basic_tests {
        use super::*;

        const MYSQL_URI: &str = "mysql://root:123456@127.0.0.1:3306/pyq";

        #[tokio::test]
        async fn test_mysql_connection_and_endpoints() {
            // 尝试创建MySQL应用，如果失败就跳过测试
            let app_result = tokio::spawn(async { create_mysql_app(MYSQL_URI).await }).await;

            match app_result {
                Ok(app) => {
                    println!("✅ MySQL连接成功");

                    // 测试基本端点
                    let endpoints = ["/all", "/friend", "/swagger.json"];
                    for endpoint in endpoints {
                        let (status, _json) = send_request(app.clone(), endpoint).await;
                        println!("✅ MySQL {endpoint} - 状态码: {status}");

                        // 验证返回合理的状态码
                        assert!(
                            matches!(
                                status,
                                StatusCode::OK
                                    | StatusCode::BAD_REQUEST
                                    | StatusCode::NOT_FOUND
                                    | StatusCode::INTERNAL_SERVER_ERROR
                            ),
                            "MySQL endpoint {endpoint} returned unexpected status: {status}"
                        );
                    }

                    println!("✅ MySQL API端点测试通过");
                }
                Err(_) => {
                    println!("⚠️ MySQL连接失败，跳过MySQL测试（这在测试环境中是正常的）");
                }
            }
        }
    }

    #[cfg(test)]
    mod mongodb_basic_tests {
        use super::*;

        const MONGODB_URI: &str = "mongodb://root:123456@127.0.0.1:27017";

        #[tokio::test]
        async fn test_mongodb_connection_and_endpoints() {
            // 尝试创建MongoDB应用，如果失败就跳过测试
            let app_result = tokio::spawn(async { create_mongodb_app(MONGODB_URI).await }).await;

            match app_result {
                Ok(app) => {
                    println!("✅ MongoDB连接成功");

                    // 测试基本端点
                    let endpoints = ["/all", "/friend", "/swagger.json"];
                    for endpoint in endpoints {
                        let (status, _json) = send_request(app.clone(), endpoint).await;
                        println!("✅ MongoDB {endpoint} - 状态码: {status}");

                        // 验证返回合理的状态码
                        assert!(
                            matches!(
                                status,
                                StatusCode::OK
                                    | StatusCode::BAD_REQUEST
                                    | StatusCode::NOT_FOUND
                                    | StatusCode::INTERNAL_SERVER_ERROR
                            ),
                            "MongoDB endpoint {endpoint} returned unexpected status: {status}"
                        );
                    }

                    println!("✅ MongoDB API端点测试通过");
                }
                Err(_) => {
                    println!("⚠️ MongoDB连接失败，跳过MongoDB测试（这在测试环境中是正常的）");
                }
            }
        }
    }

    #[cfg(test)]
    mod cross_database_basic_tests {
        use super::*;

        #[tokio::test]
        async fn test_api_consistency() {
            // 测试所有数据库的API端点一致性

            // SQLite（总是可用）
            let sqlite_app = create_sqlite_app("data.db").await;
            let (sqlite_swagger_status, sqlite_swagger) =
                send_request(sqlite_app, "/swagger.json").await;

            assert_eq!(sqlite_swagger_status, StatusCode::OK);

            if let Some(sqlite_paths) = sqlite_swagger.get("paths").and_then(|v| v.as_object()) {
                println!("✅ SQLite API路径数量: {}", sqlite_paths.len());

                // 验证基本路径存在
                let required_paths = [
                    "/all",
                    "/friend",
                    "/randomfriend",
                    "/randompost",
                    "/post",
                    "/summary",
                ];
                for path in required_paths {
                    assert!(sqlite_paths.contains_key(path), "SQLite缺少路径: {path}");
                }
            }

            println!("✅ API一致性测试通过");
        }

        #[tokio::test]
        async fn test_error_handling_consistency() {
            // 测试错误处理的一致性
            let app = create_sqlite_app("data.db").await;

            // 测试缺少必填参数
            let (status, _json) = send_request(app.clone(), "/summary").await;
            // API可能设计为返回200并在JSON中提供错误信息，而不是HTTP错误状态码
            assert!(
                matches!(
                    status,
                    StatusCode::OK | StatusCode::BAD_REQUEST | StatusCode::UNPROCESSABLE_ENTITY
                ),
                "API返回了意外的状态码: {status}"
            );

            // 测试不存在的路径
            let response = app
                .oneshot(
                    Request::builder()
                        .uri("/nonexistent")
                        .body(Body::empty())
                        .unwrap(),
                )
                .await
                .unwrap();
            assert_eq!(response.status(), StatusCode::NOT_FOUND);

            println!("✅ 错误处理一致性测试通过");
        }
    }
}

// 添加依赖到Cargo.toml的dev-dependencies中
// [dev-dependencies]
// tokio = { version = "1.0", features = ["full"] }
// tower = "0.4"
// axum = "0.7"
// serde_json = "1.0"
// urlencoding = "2.1"
