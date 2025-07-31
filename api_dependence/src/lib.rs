pub mod format_response;
pub mod mongodb;
pub mod mysql;
pub mod sqlite;

// 版本处理器模块 - 整合自 version_handler.rs
use axum::response::{Json, Result as AxumResult};
use data_structures::version::VersionResponse;
use tools::get_version;

/// 获取版本信息
pub async fn get_version_info() -> AxumResult<Json<VersionResponse>> {
    let version_response = get_version();
    Ok(Json(version_response))
}
