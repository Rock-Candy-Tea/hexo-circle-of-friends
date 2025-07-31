//! Hexo Circle of Friends API Library
//!
//! 提供SQLite、MySQL、MongoDB三种数据库的API服务

use api_dependence::{get_version_info, mongodb::mongodbapi, mysql::mysqlapi, sqlite::sqliteapi};
use axum::{Json, Router, response::Html, routing::get};
use db::{mongo, mysql, sqlite};
use serde_json::Value;
use tower::ServiceBuilder;
use tower_http::cors::{Any, CorsLayer};
use tower_http::trace::TraceLayer;

/// 提供OpenAPI JSON文档
pub async fn get_openapi_json() -> Json<Value> {
    let openapi_content = include_str!("../swagger.json");
    let openapi_json: Value = serde_json::from_str(openapi_content).unwrap();
    Json(openapi_json)
}

/// 提供Swagger UI HTML页面
pub async fn get_swagger_ui() -> Html<String> {
    let html = r#"
<!DOCTYPE html>
<html>
<head>
  <title>API文档 - Hexo Circle of Friends</title>
  <link rel="stylesheet" type="text/css" href="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css" />
  <style>
    html {
      box-sizing: border-box;
      overflow: -moz-scrollbars-vertical;
      overflow-y: scroll;
    }
    *, *:before, *:after {
      box-sizing: inherit;
    }
    body {
      margin:0;
      background: #fafafa;
    }
  </style>
</head>
<body>
  <div id="swagger-ui"></div>
  <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js"></script>
  <script src="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-standalone-preset.js"></script>
  <script>
    window.onload = function() {
      const ui = SwaggerUIBundle({
        url: '/swagger.json',
        dom_id: '#swagger-ui',
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        plugins: [
          SwaggerUIBundle.plugins.DownloadUrl
        ],
        layout: "StandaloneLayout"
      });
    };
  </script>
</body>
</html>
"#;
    Html(html.to_string())
}

// 创建 SQLite 应用
pub async fn create_sqlite_app(db_path: &str) -> Router {
    let cors = CorsLayer::new()
        .allow_methods(Any)
        .allow_origin(Any)
        .allow_headers(Any);
    let service = ServiceBuilder::new()
        .layer(TraceLayer::new_for_http())
        .layer(cors);

    let dbpool = sqlite::connect_sqlite_dbpool(db_path).await.unwrap();
    Router::new()
        .route("/all", get(sqliteapi::get_all))
        .route("/friend", get(sqliteapi::get_friend))
        .route("/post", get(sqliteapi::get_post))
        .route("/randomfriend", get(sqliteapi::get_randomfriend))
        .route("/randompost", get(sqliteapi::get_randompost))
        .route("/summary", get(sqliteapi::get_summary))
        .route("/version", get(get_version_info))
        .route("/docs", get(get_swagger_ui))
        .route("/swagger.json", get(get_openapi_json))
        .with_state(dbpool)
        .layer(service)
}

// 创建 MySQL 应用
pub async fn create_mysql_app(conn_str: &str) -> Router {
    let cors = CorsLayer::new()
        .allow_methods(Any)
        .allow_origin(Any)
        .allow_headers(Any);
    let service = ServiceBuilder::new()
        .layer(TraceLayer::new_for_http())
        .layer(cors);

    let dbpool = mysql::connect_mysql_dbpool(conn_str).await.unwrap();
    Router::new()
        .route("/all", get(mysqlapi::get_all))
        .route("/friend", get(mysqlapi::get_friend))
        .route("/post", get(mysqlapi::get_post))
        .route("/randomfriend", get(mysqlapi::get_randomfriend))
        .route("/randompost", get(mysqlapi::get_randompost))
        .route("/summary", get(mysqlapi::get_summary))
        .route("/version", get(get_version_info))
        .route("/docs", get(get_swagger_ui))
        .route("/swagger.json", get(get_openapi_json))
        .with_state(dbpool)
        .layer(service)
}

pub async fn create_mongodb_app(mongodburi: &str) -> Router {
    let cors = CorsLayer::new()
        .allow_methods(Any)
        .allow_origin(Any)
        .allow_headers(Any);
    let service = ServiceBuilder::new()
        .layer(TraceLayer::new_for_http())
        .layer(cors);

    let clientdb = mongo::connect_mongodb_clientdb(mongodburi).await.unwrap();

    Router::new()
        .route("/all", get(mongodbapi::get_all))
        .route("/friend", get(mongodbapi::get_friend))
        .route("/post", get(mongodbapi::get_post))
        .route("/randomfriend", get(mongodbapi::get_randomfriend))
        .route("/randompost", get(mongodbapi::get_randompost))
        .route("/summary", get(mongodbapi::get_summary))
        .route("/version", get(get_version_info))
        .route("/docs", get(get_swagger_ui))
        .route("/swagger.json", get(get_openapi_json))
        .with_state(clientdb)
        .layer(service)
}

#[cfg(test)]
pub mod tests;
