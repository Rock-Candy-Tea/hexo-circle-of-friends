use axum::{
    http::header,
    response::{IntoResponse, Response},
};
use serde::{Deserialize, Serialize};
pub enum PYQError {
    QueryDataBaseError(String),
    InsertDataBaseError(String),
    QueryParamsError(String),
}

#[derive(Debug, Serialize, Deserialize)]
pub struct ErrorResponse {
    message: String,
}

impl ErrorResponse {
    pub fn new(message: &str) -> ErrorResponse {
        ErrorResponse {
            message: message.to_owned(),
        }
    }
}

impl IntoResponse for PYQError {
    fn into_response(self) -> Response {
        let body = match self {
            PYQError::QueryDataBaseError(e) => {
                serde_json::to_string(&ErrorResponse::new(&format!(
                    "查询数据库表失败,请检查: 1、请求参数是否正确? 2、数据库是否可以连接? 3、表中是否有数据? 4、字段格式是否正确?  Error: {e}"
                )))
                .unwrap()
            },
            PYQError::QueryParamsError(e)=>{
                serde_json::to_string(&ErrorResponse::new(&format!(
                    "请求参数错误. Error: {e}"
                )))
                .unwrap()
            },
            PYQError::InsertDataBaseError(e)=>{
                serde_json::to_string(&ErrorResponse::new(&format!(
                    "插入数据库错误. Error: {e}"
                )))
                .unwrap()
            }
        };
        ([(header::CONTENT_TYPE, "application/json")], body).into_response()
    }
}
